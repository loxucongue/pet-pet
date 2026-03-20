"""健康报告模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IndicatorItem(BaseModel):
    """结构化指标条目。"""

    name: str
    value: str
    reference_range: str | None = None
    status: str


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

    id: int
    pet_id: int
    created_at: datetime
    updated_at: datetime


class HealthReportListResponse(BaseModel):
    """健康报告列表响应模型。"""

    items: list[HealthReportResponse]
    total: int

