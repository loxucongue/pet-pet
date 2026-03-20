"""宠物模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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

