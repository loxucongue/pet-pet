"""宠物模块路由，提供宠物档案 CRUD 接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.pet import PetCreate, PetListResponse, PetResponse, PetUpdate
from app.services.pet_service import (
    create_pet,
    delete_pet,
    get_pet_by_id,
    get_pets_by_user,
    update_pet,
)
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/pets", tags=["pets"])


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED, summary="创建宠物")
async def create_pet_route(
    payload: PetCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PetResponse:
    """创建当前用户的宠物档案。"""

    pet = await create_pet(session, current_user.id, payload)
    return PetResponse.model_validate(pet)


@router.get("", response_model=PetListResponse, summary="获取当前用户宠物列表")
async def list_pets_route(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PetListResponse:
    """获取当前用户所有未删除宠物。"""

    pets = await get_pets_by_user(session, current_user.id)
    return PetListResponse(
        items=[PetResponse.model_validate(pet) for pet in pets],
        total=len(pets),
    )


@router.get("/{pet_id}", response_model=PetResponse, summary="获取宠物详情")
async def get_pet_route(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PetResponse:
    """获取当前用户的单只宠物详情。"""

    pet = await get_pet_by_id(session, pet_id, current_user.id)
    return PetResponse.model_validate(pet)


@router.put("/{pet_id}", response_model=PetResponse, summary="更新宠物信息")
async def update_pet_route(
    pet_id: int,
    payload: PetUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PetResponse:
    """更新当前用户的宠物档案。"""

    pet = await update_pet(session, pet_id, current_user.id, payload)
    return PetResponse.model_validate(pet)


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT, summary="软删除宠物")
async def delete_pet_route(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """软删除当前用户的宠物档案。"""

    await delete_pet(session, pet_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
