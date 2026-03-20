"""宠物模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


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


class PetBase(BaseModel):
    """宠物基础字段。"""

    avatar: str | None = None
    nickname: str
    species: str
    breed: str
    gender: str | None = None
    birthday: date | None = None
    approximate_age: str | None = None
    weight: float | None = None
    is_neutered: bool | None = None
    fur_color: str | None = None
    adoption_date: date | None = None
    allergy_history: str | None = None
    chronic_disease: str | None = None
    current_food_brand: str | None = None

    @field_validator("nickname", "species", "breed")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """校验创建时必填文本字段。"""

        return _normalize_required_text(value)


class PetCreate(PetBase):
    """创建宠物请求模型。"""


class PetUpdate(BaseModel):
    """更新宠物请求模型。"""

    avatar: str | None = None
    nickname: str | None = None
    species: str | None = None
    breed: str | None = None
    gender: str | None = None
    birthday: date | None = None
    approximate_age: str | None = None
    weight: float | None = None
    is_neutered: bool | None = None
    fur_color: str | None = None
    adoption_date: date | None = None
    allergy_history: str | None = None
    chronic_disease: str | None = None
    current_food_brand: str | None = None
    is_deleted: bool | None = None
    deleted_at: datetime | None = None

    @field_validator(
        "avatar",
        "nickname",
        "species",
        "breed",
        "gender",
        "approximate_age",
        "fur_color",
        "allergy_history",
        "chronic_disease",
        "current_food_brand",
    )
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """校验更新时文本字段。"""

        return _normalize_optional_text(value)


class PetResponse(PetBase):
    """宠物响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_deleted: bool
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PetListResponse(BaseModel):
    """宠物列表响应模型。"""

    items: list[PetResponse]
    total: int
