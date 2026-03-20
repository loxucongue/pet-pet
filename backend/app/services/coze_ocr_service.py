"""Coze 工作流 OCR 服务。"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import re
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from jose import jwt

from app.config import settings


logger = logging.getLogger(__name__)

TOKEN_EXCHANGE_PATH = "/api/permission/oauth2/token"
WORKFLOW_RUN_PATH = "/v1/workflow/run"
FILE_UPLOAD_PATH = "/v1/files/upload"
JWT_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
TOKEN_REFRESH_BUFFER_SECONDS = 60
MAX_RETRY_COUNT = 2

_TOKEN_CACHE: dict[str, Any] = {
    "access_token": None,
    "expires_at": 0.0,
}
_TOKEN_LOCK = asyncio.Lock()


class CozeOCRServiceError(Exception):
    """Coze OCR 服务异常基类。"""


class CozeOCRConfigurationError(CozeOCRServiceError):
    """Coze 配置缺失或错误。"""


class CozeOAuthError(CozeOCRServiceError):
    """Coze OAuth 换取 Access Token 失败。"""


class CozeWorkflowError(CozeOCRServiceError):
    """Coze 工作流执行失败。"""


class CozeOCRInputError(CozeOCRServiceError):
    """Coze OCR 输入文件不满足调用要求。"""


class CozeOCRTimeoutError(CozeOCRServiceError):
    """Coze OCR 调用超时。"""


class CozeOCRService:
    """Coze 工作流 OCR 服务，用于识别宠物体检报告。"""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        oauth_app_id: str | None = None,
        oauth_kid: str | None = None,
        private_key_path: str | None = None,
        image_workflow_id: str | None = None,
        pdf_workflow_id: str | None = None,
        timeout: float = 30.0,
        max_retry_count: int = MAX_RETRY_COUNT,
    ) -> None:
        self.base_url = (base_url or settings.coze_base_url or "").rstrip("/")
        self.oauth_app_id = oauth_app_id or settings.coze_oauth_app_id
        self.oauth_kid = oauth_kid or settings.coze_oauth_kid
        self.private_key_path = private_key_path or settings.coze_private_key_path
        self.image_workflow_id = image_workflow_id or settings.coze_ocr_image_workflow_id
        self.pdf_workflow_id = pdf_workflow_id or settings.coze_pdf_workflow_id
        self.oauth_audience = settings.coze_oauth_audience
        self.token_duration_seconds = settings.coze_access_token_duration_seconds
        self.timeout = httpx.Timeout(timeout, connect=min(timeout, 10.0))
        self.max_attempts = max_retry_count + 1
        self._private_key_pem = self._load_private_key_pem()
        self._validate_required_settings()

    async def recognize_report(self, file_path: str, file_type: str) -> dict[str, Any]:
        """
        调用 Coze 工作流识别体检报告。

        - file_path: 本地文件路径或公网可访问 URL
        - file_type: "image" 或 "pdf"
        - 返回：{"raw_text": "...", "indicators": [...]}
        """

        workflow_id = self._resolve_workflow_id(file_type)
        workflow_input = await self._build_workflow_input(file_path)
        workflow_result = await self._run_workflow(
            workflow_id=workflow_id,
            parameters={"input": workflow_input},
        )

        output = workflow_result.get("output")
        raw_text = self._normalize_raw_text(output, file_type)
        indicators = self._extract_indicators(output, raw_text)

        return {
            "raw_text": raw_text,
            "indicators": indicators,
        }

    async def get_access_token(self) -> str:
        """获取并缓存 Coze OAuth Access Token。"""

        now = time.time()
        cached_access_token = _TOKEN_CACHE.get("access_token")
        cached_expires_at = float(_TOKEN_CACHE.get("expires_at") or 0)
        if cached_access_token and cached_expires_at - TOKEN_REFRESH_BUFFER_SECONDS > now:
            return str(cached_access_token)

        async with _TOKEN_LOCK:
            now = time.time()
            cached_access_token = _TOKEN_CACHE.get("access_token")
            cached_expires_at = float(_TOKEN_CACHE.get("expires_at") or 0)
            if cached_access_token and cached_expires_at - TOKEN_REFRESH_BUFFER_SECONDS > now:
                return str(cached_access_token)

            jwt_token = self._build_oauth_jwt()
            response = await self._request_with_retry(
                method="POST",
                path=TOKEN_EXCHANGE_PATH,
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Content-Type": "application/json",
                },
                json_body={
                    "grant_type": JWT_GRANT_TYPE,
                    "duration_seconds": self.token_duration_seconds,
                },
            )

            payload = response.json()
            if payload.get("code") not in {None, 0}:
                message = str(payload.get("msg") or "Coze OAuth 换取 access_token 失败。").strip()
                logid = self._extract_logid(payload)
                suffix = f" logid={logid}" if logid else ""
                raise CozeOAuthError(f"{message}{suffix}")

            token_payload = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            access_token = token_payload.get("access_token")
            expires_in = int(token_payload.get("expires_in") or self.token_duration_seconds)
            if not access_token:
                raise CozeOAuthError("Coze OAuth 未返回 access_token。")

            _TOKEN_CACHE["access_token"] = access_token
            _TOKEN_CACHE["expires_at"] = time.time() + expires_in
            return str(access_token)

    def _validate_required_settings(self) -> None:
        """校验必需配置。"""

        missing_fields: list[str] = []
        if not self.base_url:
            missing_fields.append("COZE_BASE_URL")
        if not self.oauth_app_id:
            missing_fields.append("COZE_OAUTH_APP_ID")
        if not self.oauth_kid:
            missing_fields.append("COZE_OAUTH_KID")
        if not self.private_key_path:
            missing_fields.append("COZE_PRIVATE_KEY_PATH")
        if not self.image_workflow_id:
            missing_fields.append("COZE_OCR_IMAGE_WORKFLOW_ID")
        if not self.pdf_workflow_id:
            missing_fields.append("COZE_PDF_WORKFLOW_ID")

        if missing_fields:
            raise CozeOCRConfigurationError(
                f"Coze OCR 配置缺失：{', '.join(missing_fields)}。"
            )

    def _load_private_key_pem(self) -> str:
        """读取 Coze OAuth 私钥。"""

        if not self.private_key_path:
            return ""

        raw_path = Path(self.private_key_path)
        if not raw_path.is_absolute():
            raw_path = (UPLOADS_DIR.parent / raw_path).resolve()

        if not raw_path.exists():
            raise CozeOCRConfigurationError(
                f"Coze 私钥文件不存在：{raw_path}"
            )

        private_key = raw_path.read_text(encoding="utf-8").strip()
        if "BEGIN PRIVATE KEY" not in private_key:
            raise CozeOCRConfigurationError("Coze 私钥文件内容无效。")

        return private_key

    def _build_oauth_jwt(self) -> str:
        """生成 Coze OAuth JWT。"""

        now = int(time.time())
        payload = {
            "iss": self.oauth_app_id,
            "aud": self.oauth_audience,
            "iat": now,
            "exp": now + 600,
            "jti": uuid4().hex,
        }
        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": self.oauth_kid,
        }

        try:
            return jwt.encode(
                payload,
                self._private_key_pem,
                algorithm="RS256",
                headers=headers,
            )
        except Exception as exc:  # noqa: BLE001
            raise CozeOAuthError("Coze OAuth JWT 生成失败，请检查私钥与 KID 配置。") from exc

    async def _run_workflow(
        self,
        *,
        workflow_id: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """执行 Coze 工作流。"""

        access_token = await self.get_access_token()
        response = await self._request_with_retry(
            method="POST",
            path=WORKFLOW_RUN_PATH,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json_body={
                "workflow_id": workflow_id,
                "parameters": parameters,
            },
        )

        payload = response.json()
        if payload.get("code") != 0:
            raise self._build_workflow_error(payload)

        raw_data = payload.get("data")
        data = self._normalize_workflow_data(raw_data)
        logger.info(
            "Coze workflow run success",
            extra={
                "workflow_id": workflow_id,
                "coze_logid": self._extract_logid(payload),
                "workflow_debug_url": payload.get("debug_url"),
            },
        )
        return data

    async def _build_workflow_input(self, file_path: str) -> str:
        """构造工作流文件类型入参。"""

        if not file_path:
            raise CozeOCRInputError("file_path 不能为空。")

        if file_path.startswith(("http://", "https://")):
            return file_path

        file_id = await self._upload_file(file_path)
        return json.dumps({"file_id": file_id}, ensure_ascii=False)

    async def _upload_file(self, file_path: str) -> str:
        """上传文件到 Coze，返回 file_id。"""

        candidate_path = Path(file_path)
        if not candidate_path.is_absolute():
            candidate_path = (UPLOADS_DIR.parent / candidate_path).resolve()

        if not candidate_path.exists() or not candidate_path.is_file():
            raise CozeOCRInputError(f"待识别文件不存在：{candidate_path}")

        access_token = await self.get_access_token()
        mime_type = mimetypes.guess_type(candidate_path.name)[0] or "application/octet-stream"

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                with candidate_path.open("rb") as file_stream:
                    response = await client.post(
                        FILE_UPLOAD_PATH,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                        },
                        files={
                            "file": (candidate_path.name, file_stream, mime_type),
                        },
                    )
        except httpx.TimeoutException as exc:
            raise CozeOCRTimeoutError("Coze 文件上传超时，请稍后重试。") from exc
        except httpx.RequestError as exc:
            raise CozeOCRServiceError("Coze 文件上传请求失败。") from exc

        if response.status_code >= 400:
            raise self._build_http_error(response)

        payload = response.json()
        if payload.get("code") not in {None, 0}:
            message = str(payload.get("msg") or "Coze 文件上传失败。").strip()
            logid = self._extract_logid(payload)
            suffix = f" logid={logid}" if logid else ""
            raise CozeOCRServiceError(f"{message}{suffix}")

        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        file_id = data.get("id") or data.get("file_id")
        if not file_id:
            raise CozeOCRServiceError("Coze 文件上传成功，但响应中未返回 file_id。")

        return str(file_id)

    async def _request_with_retry(
        self,
        *,
        method: str,
        path: str,
        headers: dict[str, str],
        json_body: dict[str, Any],
    ) -> httpx.Response:
        """请求 Coze 接口，并在网络错误时重试。"""

        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=path,
                        headers=headers,
                        json=json_body,
                    )
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(0.5 * attempt)
                    continue
                raise CozeOCRTimeoutError("Coze 接口请求超时，已达到最大重试次数。") from exc
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(0.5 * attempt)
                    continue
                raise CozeOCRServiceError("Coze 接口网络请求失败。") from exc

            if response.status_code >= 500 and attempt < self.max_attempts:
                await asyncio.sleep(0.5 * attempt)
                continue

            if response.status_code >= 400:
                raise self._build_http_error(response)

            return response

        raise CozeOCRServiceError(f"Coze 接口请求失败：{last_error}")

    def _resolve_workflow_id(self, file_type: str) -> str:
        """根据文件类型选择工作流。"""

        if file_type == "image":
            return str(self.image_workflow_id)
        if file_type == "pdf":
            return str(self.pdf_workflow_id)
        raise CozeOCRInputError("file_type 仅支持 image 或 pdf。")

    def _normalize_workflow_data(self, raw_data: Any) -> dict[str, Any]:
        """标准化 Coze workflow data 字段。"""

        if isinstance(raw_data, dict):
            return raw_data

        if isinstance(raw_data, str):
            stripped = raw_data.strip()
            if not stripped:
                return {}

            try:
                parsed_data = json.loads(stripped)
            except json.JSONDecodeError:
                return {"output": stripped}

            if isinstance(parsed_data, dict):
                return parsed_data

            return {"output": parsed_data}

        return {"output": raw_data}

    def _normalize_raw_text(self, output: Any, file_type: str) -> str:
        """将工作流输出整理为 OCR 原始文本。"""

        if file_type == "pdf" and isinstance(output, str):
            return output.strip()

        text_fragments = self._flatten_text_fragments(output)
        if text_fragments:
            return "\n".join(text_fragments).strip()

        if isinstance(output, str):
            return output.strip()

        return json.dumps(output, ensure_ascii=False, default=str)

    def _flatten_text_fragments(self, value: Any) -> list[str]:
        """从工作流输出中提取碎片化文本。"""

        fragments: list[str] = []

        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                fragments.append(stripped)
            return fragments

        if isinstance(value, dict):
            preferred_keys = ["output", "text", "content", "value", "fragment"]
            for key in preferred_keys:
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    fragments.append(candidate.strip())

            if not fragments:
                for item in value.values():
                    fragments.extend(self._flatten_text_fragments(item))
            return fragments

        if isinstance(value, list):
            for item in value:
                fragments.extend(self._flatten_text_fragments(item))
            return fragments

        return fragments

    def _extract_indicators(self, output: Any, raw_text: str) -> list[dict[str, str]]:
        """尽可能从 OCR 结果中提取结构化指标。"""

        indicators: list[dict[str, str]] = []
        seen_keys: set[tuple[str, str, str, str]] = set()

        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict) and item.get("name") and item.get("value"):
                    indicator = {
                        "name": str(item.get("name", "")).strip(),
                        "value": str(item.get("value", "")).strip(),
                        "unit": str(item.get("unit", "")).strip(),
                        "reference_range": str(item.get("reference_range", "")).strip(),
                    }
                    self._append_indicator(indicators, seen_keys, indicator)

        for line in raw_text.splitlines():
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            parsed = self._parse_indicator_line(cleaned_line)
            if parsed:
                self._append_indicator(indicators, seen_keys, parsed)

        return indicators

    def _append_indicator(
        self,
        indicators: list[dict[str, str]],
        seen_keys: set[tuple[str, str, str, str]],
        indicator: dict[str, str],
    ) -> None:
        """去重并追加指标。"""

        key = (
            indicator.get("name", ""),
            indicator.get("value", ""),
            indicator.get("unit", ""),
            indicator.get("reference_range", ""),
        )
        if not indicator.get("name") or not indicator.get("value") or key in seen_keys:
            return

        seen_keys.add(key)
        indicators.append(indicator)

    def _parse_indicator_line(self, line: str) -> dict[str, str] | None:
        """从单行文本中提取指标。"""

        normalized_line = re.sub(r"\s+", " ", line.replace("（", "(").replace("）", ")")).strip()
        pattern = re.compile(
            r"^(?P<name>[\u4e00-\u9fa5A-Za-z0-9\-/+()]+?)"
            r"(?:\s+[A-Z]{2,})?"
            r"\s*[:：]?\s*"
            r"(?P<value>-?\d+(?:\.\d+)?)"
            r"(?:\s*(?P<unit>[A-Za-z0-9/%^.\-+*μµ]+))?"
            r"(?:.*?(?:参考范围|正常范围|参考值|REF|ref)\s*[:：]?\s*(?P<reference_range>[^)\n]+))?"
            r"(?:\))?$"
        )
        match = pattern.search(normalized_line)
        if not match:
            return None

        return {
            "name": match.group("name").strip(),
            "value": match.group("value").strip(),
            "unit": (match.group("unit") or "").strip(),
            "reference_range": (match.group("reference_range") or "").strip(),
        }

    def _build_http_error(self, response: httpx.Response) -> CozeOCRServiceError:
        """将 HTTP 错误转为业务异常。"""

        message = self._extract_error_message(response)
        if response.status_code in {401, 403}:
            return CozeOAuthError(message or "Coze 认证失败，请检查 OAuth 配置。")
        return CozeOCRServiceError(
            message or f"Coze 接口调用失败，HTTP 状态码：{response.status_code}。"
        )

    def _build_workflow_error(self, payload: dict[str, Any]) -> CozeWorkflowError:
        """构造工作流异常。"""

        message = str(payload.get("msg") or "Coze 工作流执行失败。").strip()
        logid = self._extract_logid(payload)
        suffix = f" logid={logid}" if logid else ""
        return CozeWorkflowError(f"{message}{suffix}")

    def _extract_error_message(self, response: httpx.Response) -> str:
        """提取 Coze 错误消息。"""

        try:
            payload = response.json()
        except json.JSONDecodeError:
            return response.text.strip()

        if isinstance(payload, dict):
            if payload.get("code") not in {None, 0}:
                message = str(payload.get("msg") or "").strip()
                logid = self._extract_logid(payload)
                return f"{message} logid={logid}".strip()

            detail = payload.get("detail")
            if isinstance(detail, dict):
                message = str(detail.get("message") or detail.get("logid") or "").strip()
                if message:
                    return message

            if payload.get("message"):
                return str(payload["message"]).strip()

        return response.text.strip()

    def _extract_logid(self, payload: dict[str, Any]) -> str:
        """提取 Coze logid。"""

        detail = payload.get("detail")
        if isinstance(detail, dict):
            return str(detail.get("logid") or "").strip()
        return ""
