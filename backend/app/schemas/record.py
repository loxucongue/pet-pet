"""记录模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RecordBase(BaseModel):
    """记录基础字段。"""

    record_date: date
    category: str
    sub_type: str
    note: str | None = None
    amount: float | None = None
    weight_value: float | None = None


class RecordCreate(RecordBase):
    """创建记录请求模型。"""

    pet_id: int


class RecordUpdate(BaseModel):
    """更新记录请求模型。"""

    record_date: date | None = None
    category: str | None = None
    sub_type: str | None = None
    note: str | None = None
    amount: float | None = None
    weight_value: float | None = None


class RecordResponse(RecordBase):
    """记录响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    created_at: datetime
    updated_at: datetime


class RecordListResponse(BaseModel):
    """记录列表响应模型。"""

    items: list[RecordResponse]
    total: int

