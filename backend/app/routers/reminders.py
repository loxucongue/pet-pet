"""提醒模块路由，提供提醒 CRUD 与即将到期接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.reminder import ReminderCreate, ReminderResponse, ReminderUpdate
from app.services.reminder_service import (
    complete_reminder,
    create_reminder,
    delete_reminder,
    get_reminders,
    get_upcoming_reminders,
    update_reminder,
)
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED, summary="创建提醒")
async def create_reminder_route(
    payload: ReminderCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ReminderResponse:
    """创建当前用户指定宠物的提醒。"""

    reminder = await create_reminder(
        session=session,
        pet_id=payload.pet_id,
        user_id=current_user.id,
        reminder_data=payload,
    )
    return ReminderResponse.model_validate(reminder)


@router.get("", response_model=list[ReminderResponse], summary="查询提醒列表")
async def list_reminders_route(
    pet_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ReminderResponse]:
    """查询当前用户的提醒列表，可按宠物筛选。"""

    reminders = await get_reminders(session, current_user.id, pet_id)
    return [ReminderResponse.model_validate(item) for item in reminders]


@router.get("/upcoming", response_model=list[ReminderResponse], summary="获取即将到期提醒")
async def get_upcoming_reminders_route(
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ReminderResponse]:
    """获取今天到未来指定天数内的活跃提醒。"""

    reminders = await get_upcoming_reminders(session, current_user.id, days)
    return [ReminderResponse.model_validate(item) for item in reminders]


@router.post("/{reminder_id}/complete", response_model=ReminderResponse, summary="完成提醒")
async def complete_reminder_route(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ReminderResponse:
    """标记提醒完成并推进到下一周期。"""

    reminder = await complete_reminder(session, reminder_id, current_user.id)
    return ReminderResponse.model_validate(reminder)


@router.put("/{reminder_id}", response_model=ReminderResponse, summary="编辑提醒")
async def update_reminder_route(
    reminder_id: int,
    payload: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ReminderResponse:
    """编辑当前提醒。"""

    reminder = await update_reminder(session, reminder_id, current_user.id, payload)
    return ReminderResponse.model_validate(reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除提醒")
async def delete_reminder_route(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """删除当前提醒。"""

    await delete_reminder(session, reminder_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
