"""DeepSeek API 调用服务，兼容 OpenAI 接口格式。"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from app.config import settings


DEFAULT_MODEL = "deepseek-chat"
CHAT_COMPLETIONS_PATH = "/chat/completions"


class DeepSeekServiceError(Exception):
    """DeepSeek 服务调用异常基类。"""


class DeepSeekConfigurationError(DeepSeekServiceError):
    """DeepSeek 配置缺失或无效。"""


class DeepSeekTimeoutError(DeepSeekServiceError):
    """DeepSeek 请求超时。"""


class DeepSeekAuthenticationError(DeepSeekServiceError):
    """DeepSeek 认证失败。"""


class DeepSeekRateLimitError(DeepSeekServiceError):
    """DeepSeek 触发速率限制。"""


class DeepSeekQuotaExceededError(DeepSeekServiceError):
    """DeepSeek 额度不足或已耗尽。"""


class DeepSeekResponseError(DeepSeekServiceError):
    """DeepSeek 响应内容异常。"""


class DeepSeekService:
    """DeepSeek API 调用服务，兼容 OpenAI 接口格式。"""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = (base_url or settings.deepseek_base_url or "").rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout, connect=min(timeout, 10.0))

        if not self.api_key:
            raise DeepSeekConfigurationError("DEEPSEEK_API_KEY 未配置，无法调用 DeepSeek 服务。")

        if not self.base_url:
            raise DeepSeekConfigurationError("DEEPSEEK_BASE_URL 未配置，无法调用 DeepSeek 服务。")

    async def interpret_health_report(self, ocr_data: str, pet_info: dict[str, Any]) -> str:
        """
        体检报告解读。

        - ocr_data: OCR 识别出的文本数据
        - pet_info: 宠物档案信息（品种、年龄、体重等）
        - 返回通俗化解读文本
        """

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._build_health_report_prompt(pet_info),
                },
                {
                    "role": "user",
                    "content": f"请解读以下宠物体检报告 OCR 文本，并按要求输出通俗化结论：\n\n{ocr_data}",
                },
            ],
            "temperature": 0.3,
            "stream": False,
        }

        response_data = await self._post_json(CHAT_COMPLETIONS_PATH, payload)
        choices = response_data.get("choices") or []
        content = (
            choices[0].get("message", {}).get("content")
            if choices and isinstance(choices[0], dict)
            else None
        )
        if not content:
            raise DeepSeekResponseError("DeepSeek 未返回有效的体检解读内容。")
        return content.strip()

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        pet_info: dict[str, Any],
    ) -> AsyncIterator[str]:
        """
        对话问答，流式输出。

        - messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
        - pet_info: 当前宠物档案信息
        - yield 每个 token 文本片段
        """

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._build_chat_prompt(pet_info),
                },
                *messages,
            ],
            "temperature": 0.5,
            "stream": True,
        }

        headers = self._build_headers()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    CHAT_COMPLETIONS_PATH,
                    headers=headers,
                    json=payload,
                ) as response:
                    await self._raise_for_status(response)
                    async for raw_line in response.aiter_lines():
                        if not raw_line:
                            continue

                        line = raw_line.strip()
                        if not line or line.startswith(":") or not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError as exc:
                            raise DeepSeekResponseError("DeepSeek 流式响应解析失败。") from exc

                        delta = ((data.get("choices") or [{}])[0].get("delta") or {})
                        token = delta.get("content") or ""
                        if token:
                            yield token
        except httpx.TimeoutException as exc:
            raise DeepSeekTimeoutError("DeepSeek 流式对话请求超时，请稍后重试。") from exc
        except httpx.HTTPError as exc:
            raise DeepSeekServiceError(f"DeepSeek 流式对话请求失败：{exc}") from exc

    def _build_headers(self) -> dict[str, str]:
        """构造请求头。"""

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_health_report_prompt(self, pet_info: dict[str, Any]) -> str:
        """构造体检解读 system prompt。"""

        return (
            "你是一位专业的宠物健康顾问，请用通俗易懂的语言解读以下体检报告数据。"
            "对每项指标说明：指标含义、当前数值是否正常、可能的影响、建议。"
            "最后给出整体健康评估和注意事项。"
            "请明确说明这不是替代兽医诊断的最终结论，如有急症或明显异常，建议尽快就医。\n\n"
            f"宠物信息：{self._format_pet_info(pet_info)}"
        )

    def _build_chat_prompt(self, pet_info: dict[str, Any]) -> str:
        """构造对话问答 system prompt。"""

        pet_name = pet_info.get("nickname") or pet_info.get("pet_name") or "这只宠物"
        species = pet_info.get("species") or "未知物种"
        breed = pet_info.get("breed") or "未知品种"
        age = (
            pet_info.get("approximate_age")
            or pet_info.get("birthday")
            or pet_info.get("age")
            or "年龄未知"
        )

        return (
            f"你是{pet_name}（{species}/{breed}/{age}）的专属健康顾问。"
            "基于以下健康档案信息回答问题，回答要通俗易懂，不夸大、不制造恐慌。"
            "如果用户描述的是呼吸困难、持续抽搐、昏迷、大量出血等紧急情况，要明确建议立刻就医。"
            "你可以提供观察建议和护理建议，但不要冒充正式诊断。\n\n"
            f"宠物档案信息：{self._format_pet_info(pet_info)}"
        )

    def _format_pet_info(self, pet_info: dict[str, Any]) -> str:
        """将宠物档案信息转为稳定文本。"""

        if not pet_info:
            return "暂无宠物档案信息。"
        return json.dumps(pet_info, ensure_ascii=False, indent=2, default=str)

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """发送普通 JSON 请求。"""

        headers = self._build_headers()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(path, headers=headers, json=payload)
            await self._raise_for_status(response)
            return response.json()
        except httpx.TimeoutException as exc:
            raise DeepSeekTimeoutError("DeepSeek 请求超时，请稍后重试。") from exc
        except httpx.HTTPError as exc:
            raise DeepSeekServiceError(f"DeepSeek 请求失败：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise DeepSeekResponseError("DeepSeek 返回了无法解析的 JSON 响应。") from exc

    async def _raise_for_status(self, response: httpx.Response) -> None:
        """根据响应状态抛出更具体的异常。"""

        if response.is_success:
            return

        message = await self._extract_error_message(response)
        status_code = response.status_code
        normalized_message = message.lower()

        if status_code in {401, 403}:
            raise DeepSeekAuthenticationError(message or "DeepSeek API Key 无效或没有访问权限。")

        if status_code == 429:
            raise DeepSeekRateLimitError(message or "DeepSeek 请求过于频繁，请稍后再试。")

        if status_code == 402 or "insufficient" in normalized_message or "quota" in normalized_message:
            raise DeepSeekQuotaExceededError(message or "DeepSeek 额度不足或账户余额不足。")

        raise DeepSeekServiceError(
            message or f"DeepSeek 接口调用失败，HTTP 状态码：{status_code}。"
        )

    async def _extract_error_message(self, response: httpx.Response) -> str:
        """提取 DeepSeek 错误信息。"""

        try:
            payload = response.json()
        except httpx.ResponseNotRead:
            raw_content = await response.aread()
            response_text = raw_content.decode("utf-8", errors="ignore").strip()
            try:
                payload = json.loads(response_text)
            except json.JSONDecodeError:
                return response_text
        except json.JSONDecodeError:
            return response.text.strip()

        error = payload.get("error")
        if isinstance(error, dict):
            return (
                str(error.get("message") or error.get("code") or "").strip()
                or response.text.strip()
            )

        if isinstance(error, str):
            return error.strip()

        return response.text.strip()
