"""记录模块路由，提供宠物记录 CRUD 接口。"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.record import RecordCreate, RecordListResponse, RecordResponse, RecordUpdate
from app.services.record_service import (
    create_record,
    delete_record,
    get_record_by_id,
    get_records,
    update_record,
)
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/records", tags=["records"])


@router.post("", response_model=RecordResponse, status_code=status.HTTP_201_CREATED, summary="创建记录")
async def create_record_route(
    payload: RecordCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> RecordResponse:
    """创建当前用户指定宠物的记录。"""

    record = await create_record(
        session=session,
        pet_id=payload.pet_id,
        user_id=current_user.id,
        record_data=payload,
        image_paths=payload.image_paths,
    )
    return RecordResponse.model_validate(record)


@router.get("", response_model=RecordListResponse, summary="查询记录列表")
async def list_records_route(
    pet_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> RecordListResponse:
    """按宠物、日期区间和分类查询当前用户的记录列表。"""

    records = await get_records(
        session=session,
        user_id=current_user.id,
        pet_id=pet_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
    )
    return RecordListResponse(
        items=[RecordResponse.model_validate(record) for record in records],
        total=len(records),
    )


@router.get("/{record_id}", response_model=RecordResponse, summary="获取记录详情")
async def get_record_route(
    record_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> RecordResponse:
    """获取单条记录详情。"""

    record = await get_record_by_id(session, record_id, current_user.id)
    return RecordResponse.model_validate(record)


@router.put("/{record_id}", response_model=RecordResponse, summary="更新记录")
async def update_record_route(
    record_id: int,
    payload: RecordUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> RecordResponse:
    """更新单条记录。"""

    record = await update_record(session, record_id, current_user.id, payload)
    return RecordResponse.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除记录")
async def delete_record_route(
    record_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """删除单条记录及其关联图片与提醒。"""

    await delete_record(session, record_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
