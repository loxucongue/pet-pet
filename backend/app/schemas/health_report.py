"""健康报告模块的请求与响应数据模型。"""

from __future__ import annotations

import json
from typing import Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IndicatorItem(BaseModel):
    """结构化指标条目。"""

    name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    status: str | None = None


class HealthAnalyzeRequest(BaseModel):
    """体检报告分析请求。"""

    pet_id: int
    file_path: str
    file_type: str

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, value: str) -> str:
        """校验文件类型。"""

        normalized = value.strip().lower()
        if normalized not in {"image", "pdf"}:
            raise ValueError("file_type 仅支持 image 或 pdf。")
        return normalized


class HealthReportIndicatorsUpdate(BaseModel):
    """更新结构化指标请求。"""

    indicators: list[IndicatorItem] = Field(default_factory=list)


class HealthReportBase(BaseModel):
    """健康报告基础字段。"""

    original_file_path: str
    file_type: str
    ocr_result_json: str | None = None
    parsed_indicators_json: str | None = None
    ai_interpretation: str | None = None
    status: str = "pending"


class HealthReportCreate(HealthReportBase):
    """创建健康报告请求模型。"""

    pet_id: int


class HealthReportResponse(HealthReportBase):
    """健康报告响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    ocr_result_json: dict[str, Any] | list[Any] | str | None = None
    parsed_indicators_json: list[IndicatorItem] | dict[str, Any] | str | None = None
    id: int
    pet_id: int
    created_at: datetime
    updated_at: datetime

    @field_validator("ocr_result_json", mode="before")
    @classmethod
    def parse_ocr_result_json(
        cls,
        value: dict[str, Any] | list[Any] | str | None,
    ) -> dict[str, Any] | list[Any] | str | None:
        """解析 OCR JSON 字符串。"""

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return stripped
        return value

    @field_validator("parsed_indicators_json", mode="before")
    @classmethod
    def parse_indicators_json(
        cls,
        value: list[dict[str, Any]] | dict[str, Any] | str | None,
    ) -> list[dict[str, Any]] | dict[str, Any] | str | None:
        """解析指标 JSON 字符串。"""

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return stripped
        return value


class HealthReportListResponse(BaseModel):
    """健康报告列表响应模型。"""

    items: list[HealthReportResponse]
    total: int


class HealthQuotaResponse(BaseModel):
    """健康分析额度响应。"""

    remaining: int
