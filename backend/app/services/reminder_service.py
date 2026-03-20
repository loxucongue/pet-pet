"""提醒服务，负责提醒的 CRUD 与到期逻辑。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pet, PetRecord, Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.services.pet_service import get_pet_by_id


UPDATABLE_FIELDS = {
    "record_id",
    "reminder_type",
    "cycle_days",
    "reminder_time",
    "next_reminder_date",
    "is_active",
}


def _get_reminder_query() -> select[tuple[Reminder]]:
    """构建包含宠物关系的提醒查询语句。"""

    return select(Reminder).options(
        selectinload(Reminder.pet),
    )


async def _get_record_for_reminder(
    session: AsyncSession,
    record_id: int,
    pet_id: int,
    user_id: int,
) -> PetRecord:
    """校验提醒关联记录存在且归属当前用户。"""

    record = await session.scalar(
        select(PetRecord)
        .join(PetRecord.pet)
        .where(
            PetRecord.id == record_id,
            PetRecord.pet_id == pet_id,
            Pet.user_id == user_id,
            Pet.is_deleted.is_(False),
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联记录不存在。",
        )
    return record


def _calculate_next_reminder_date(
    start_date: date,
    cycle_days: int,
) -> date:
    """根据起始日期和周期计算下次提醒日期。"""

    return start_date + timedelta(days=cycle_days)


async def _resolve_start_date(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    record_id: int | None,
    explicit_start_date: date | None,
) -> tuple[date, PetRecord | None]:
    """解析提醒起始日期，优先使用显式传入值。"""

    linked_record: PetRecord | None = None
    if record_id is not None:
        linked_record = await _get_record_for_reminder(session, record_id, pet_id, user_id)

    if explicit_start_date is not None:
        return explicit_start_date, linked_record

    if linked_record is not None:
        return linked_record.record_date, linked_record

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="创建提醒需要提供 start_date 或有效的 record_id。",
    )


async def _ensure_reminder_access(
    session: AsyncSession,
    reminder_id: int,
    user_id: int,
) -> Reminder:
    """校验提醒存在且属于当前用户。"""

    reminder = await session.scalar(
        _get_reminder_query()
        .where(Reminder.id == reminder_id)
    )
    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在。",
        )

    if reminder.pet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该提醒。",
        )

    return reminder


def _attach_pet_nickname(reminder: Reminder) -> Reminder:
    """为提醒对象附加宠物昵称，便于序列化返回。"""

    reminder.pet_nickname = reminder.pet.nickname
    return reminder


async def create_reminder(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    reminder_data: ReminderCreate,
) -> Reminder:
    """创建提醒并自动计算下次提醒日期。"""

    pet = await get_pet_by_id(session, pet_id, user_id)
    start_date, _ = await _resolve_start_date(
        session=session,
        pet_id=pet.id,
        user_id=user_id,
        record_id=reminder_data.record_id,
        explicit_start_date=reminder_data.start_date,
    )

    reminder = Reminder(
        pet_id=pet.id,
        record_id=reminder_data.record_id,
        reminder_type=reminder_data.reminder_type,
        cycle_days=reminder_data.cycle_days,
        reminder_time=reminder_data.reminder_time,
        next_reminder_date=_calculate_next_reminder_date(start_date, reminder_data.cycle_days),
        is_active=reminder_data.is_active,
    )
    session.add(reminder)
    await session.commit()

    created_reminder = await _ensure_reminder_access(session, reminder.id, user_id)
    return _attach_pet_nickname(created_reminder)


async def get_reminders(
    session: AsyncSession,
    user_id: int,
    pet_id: int | None = None,
) -> Sequence[Reminder]:
    """查询当前用户的提醒列表。"""

    query = (
        _get_reminder_query()
        .join(Reminder.pet)
        .where(
            Pet.user_id == user_id,
            Pet.is_deleted.is_(False),
        )
        .order_by(Reminder.next_reminder_date.asc(), Reminder.id.asc())
    )

    if pet_id is not None:
        await get_pet_by_id(session, pet_id, user_id)
        query = query.where(Reminder.pet_id == pet_id)

    reminders = (await session.scalars(query)).all()
    return [_attach_pet_nickname(item) for item in reminders]


async def get_upcoming_reminders(
    session: AsyncSession,
    user_id: int,
    days: int = 7,
) -> Sequence[Reminder]:
    """获取今天到未来指定天数内的活跃提醒。"""

    today = date.today()
    end_date = today + timedelta(days=max(days, 0))

    reminders = (
        await session.scalars(
            _get_reminder_query()
            .join(Reminder.pet)
            .where(
                Pet.user_id == user_id,
                Pet.is_deleted.is_(False),
                Reminder.is_active.is_(True),
                Reminder.next_reminder_date >= today,
                Reminder.next_reminder_date <= end_date,
            )
            .order_by(Reminder.next_reminder_date.asc(), Reminder.id.asc())
        )
    ).all()

    return [_attach_pet_nickname(item) for item in reminders]


async def complete_reminder(
    session: AsyncSession,
    reminder_id: int,
    user_id: int,
) -> Reminder:
    """标记提醒完成，并推进到下一周期。"""

    reminder = await _ensure_reminder_access(session, reminder_id, user_id)
    reminder.next_reminder_date = reminder.next_reminder_date + timedelta(days=reminder.cycle_days)
    await session.commit()

    completed_reminder = await _ensure_reminder_access(session, reminder_id, user_id)
    return _attach_pet_nickname(completed_reminder)


async def update_reminder(
    session: AsyncSession,
    reminder_id: int,
    user_id: int,
    data: ReminderUpdate,
) -> Reminder:
    """更新提醒信息。"""

    reminder = await _ensure_reminder_access(session, reminder_id, user_id)
    update_data = data.model_dump(exclude_unset=True)
    start_date = update_data.pop("start_date", None)

    if "record_id" in update_data and update_data["record_id"] is not None:
        await _get_record_for_reminder(
            session=session,
            record_id=update_data["record_id"],
            pet_id=reminder.pet_id,
            user_id=user_id,
        )

    for field in UPDATABLE_FIELDS:
        if field in update_data:
            setattr(reminder, field, update_data[field])

    if start_date is not None:
        reminder.next_reminder_date = _calculate_next_reminder_date(
            start_date,
            reminder.cycle_days,
        )
    elif "record_id" in update_data and update_data["record_id"] is not None and "next_reminder_date" not in update_data:
        linked_record = await _get_record_for_reminder(
            session=session,
            record_id=update_data["record_id"],
            pet_id=reminder.pet_id,
            user_id=user_id,
        )
        reminder.next_reminder_date = _calculate_next_reminder_date(
            linked_record.record_date,
            reminder.cycle_days,
        )

    await session.commit()

    updated_reminder = await _ensure_reminder_access(session, reminder_id, user_id)
    return _attach_pet_nickname(updated_reminder)


async def delete_reminder(
    session: AsyncSession,
    reminder_id: int,
    user_id: int,
) -> None:
    """删除提醒。"""

    reminder = await _ensure_reminder_access(session, reminder_id, user_id)
    await session.delete(reminder)
    await session.commit()
