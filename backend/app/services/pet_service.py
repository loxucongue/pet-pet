"""宠物服务，负责宠物档案的 CRUD 逻辑。"""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Pet
from app.models.base import utc_now
from app.schemas.pet import PetCreate, PetUpdate


UPDATABLE_FIELDS = {
    "avatar",
    "nickname",
    "species",
    "breed",
    "gender",
    "birthday",
    "approximate_age",
    "weight",
    "is_neutered",
    "fur_color",
    "adoption_date",
    "allergy_history",
    "chronic_disease",
    "current_food_brand",
}


async def create_pet(session: AsyncSession, user_id: int, pet_data: PetCreate) -> Pet:
    """创建当前用户的宠物档案。"""

    pet = Pet(user_id=user_id, **pet_data.model_dump())
    session.add(pet)
    await session.commit()
    await session.refresh(pet)
    return pet


async def get_pets_by_user(session: AsyncSession, user_id: int) -> Sequence[Pet]:
    """获取当前用户的未删除宠物列表。"""

    result = await session.scalars(
        select(Pet)
        .where(
            Pet.user_id == user_id,
            Pet.is_deleted.is_(False),
        )
        .order_by(Pet.created_at.desc(), Pet.id.desc())
    )
    return result.all()


async def get_pet_by_id(session: AsyncSession, pet_id: int, user_id: int) -> Pet:
    """按 ID 获取当前用户的宠物档案，并校验归属。"""

    pet = await session.get(Pet, pet_id)
    if pet is None or pet.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="宠物不存在。",
        )
    if pet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该宠物。",
        )
    return pet


async def update_pet(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    pet_data: PetUpdate,
) -> Pet:
    """更新当前用户的宠物档案。"""

    pet = await get_pet_by_id(session, pet_id, user_id)
    update_data = pet_data.model_dump(exclude_unset=True)
    for field in UPDATABLE_FIELDS:
        if field in update_data:
            setattr(pet, field, update_data[field])

    await session.commit()
    await session.refresh(pet)
    return pet


async def delete_pet(session: AsyncSession, pet_id: int, user_id: int) -> None:
    """软删除当前用户的宠物档案。"""

    pet = await get_pet_by_id(session, pet_id, user_id)
    pet.is_deleted = True
    pet.deleted_at = utc_now()
    await session.commit()

