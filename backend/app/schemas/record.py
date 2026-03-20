"""记录模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_required_text(value: str) -> str:
    """标准化必填文本字段并校验非空。"""

    normalized = value.strip()
    if not normalized:
        raise ValueError("字段不能为空字符串。")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    """标准化可选文本字段。"""

    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise ValueError("字段不能为空字符串。")
    return normalized


class RecordBase(BaseModel):
    """记录基础字段。"""

    record_date: date
    category: str
    sub_type: str
    note: str | None = None
    amount: float | None = None
    weight_value: float | None = None

    @field_validator("category", "sub_type")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """校验必填文本字段。"""

        return _normalize_required_text(value)

    @field_validator("note")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """校验可选文本字段。"""

        return _normalize_optional_text(value)


class RecordImageResponse(BaseModel):
    """记录图片响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    created_at: datetime


class RecordCreate(RecordBase):
    """创建记录请求模型。"""

    pet_id: int
    image_paths: list[str] = Field(default_factory=list)

    @field_validator("image_paths")
    @classmethod
    def validate_image_paths(cls, value: list[str]) -> list[str]:
        """校验图片路径数组。"""

        normalized_paths: list[str] = []
        for item in value:
            normalized_paths.append(_normalize_required_text(item))
        return normalized_paths


class RecordUpdate(BaseModel):
    """更新记录请求模型。"""

    record_date: date | None = None
    category: str | None = None
    sub_type: str | None = None
    note: str | None = None
    amount: float | None = None
    weight_value: float | None = None
    image_paths: list[str] | None = None

    @field_validator("category", "sub_type", "note")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """校验可选文本字段。"""

        return _normalize_optional_text(value)

    @field_validator("image_paths")
    @classmethod
    def validate_update_image_paths(cls, value: list[str] | None) -> list[str] | None:
        """校验更新时的图片路径数组。"""

        if value is None:
            return None

        normalized_paths: list[str] = []
        for item in value:
            normalized_paths.append(_normalize_required_text(item))
        return normalized_paths


class RecordResponse(RecordBase):
    """记录响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    images: list[RecordImageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RecordListResponse(BaseModel):
    """记录列表响应模型。"""

    items: list[RecordResponse]
    total: int
