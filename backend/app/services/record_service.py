"""记录服务，负责宠物日常记录的 CRUD 逻辑。"""

from __future__ import annotations

from datetime import date
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pet, PetRecord, RecordImage, Reminder
from app.schemas.record import (
    ExpenseStatDetail,
    ExpenseStatsResponse,
    RecordCreate,
    RecordUpdate,
    WeightTrendPoint,
)
from app.services.pet_service import get_pet_by_id


UPDATABLE_FIELDS = {
    "record_date",
    "category",
    "sub_type",
    "note",
    "amount",
    "weight_value",
}

WEIGHT_RECORD_SUB_TYPE = "体重记录"
EXPENSE_CATEGORY = "消费"


def _get_record_query() -> select[tuple[PetRecord]]:
    """构建包含图片关系的记录查询语句。"""

    return select(PetRecord).options(
        selectinload(PetRecord.images),
    )


async def _get_record_with_pet_by_id(
    session: AsyncSession,
    record_id: int,
) -> PetRecord | None:
    """按 ID 获取记录，并预加载宠物与图片信息。"""

    result = await session.scalar(
        _get_record_query()
        .options(selectinload(PetRecord.pet))
        .where(PetRecord.id == record_id)
    )
    return result


async def _ensure_record_access(
    session: AsyncSession,
    record_id: int,
    user_id: int,
) -> PetRecord:
    """校验记录存在且属于当前用户。"""

    record = await _get_record_with_pet_by_id(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在。",
        )

    if record.pet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该记录。",
        )

    return record


async def _sync_pet_weight(
    session: AsyncSession,
    pet: Pet,
    sub_type: str,
    weight_value: float | None,
) -> None:
    """当记录为体重记录时，同步宠物当前体重。"""

    if sub_type == WEIGHT_RECORD_SUB_TYPE and weight_value is not None:
        pet.weight = weight_value
        await session.flush()


def _shift_months(base_date: date, months: int) -> date:
    """将日期按月偏移，保留可用的日字段。"""

    total_month = (base_date.year * 12 + (base_date.month - 1)) + months
    target_year = total_month // 12
    target_month = total_month % 12 + 1

    if target_month == 12:
        next_month_year = target_year + 1
        next_month = 1
    else:
        next_month_year = target_year
        next_month = target_month + 1

    month_last_day = (date(next_month_year, next_month, 1) - date.resolution).day
    target_day = min(base_date.day, month_last_day)
    return date(target_year, target_month, target_day)


def _resolve_period_start(period: str) -> date | None:
    """根据周期字符串解析起始日期。"""

    today = date.today()
    period_mapping = {
        "1m": -1,
        "3m": -3,
        "6m": -6,
        "1y": -12,
        "all": None,
    }
    months = period_mapping[period]
    if months is None:
        return None
    return _shift_months(today, months)


async def create_record(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    record_data: RecordCreate,
    image_paths: list[str],
) -> PetRecord:
    """创建记录并关联图片。"""

    pet = await get_pet_by_id(session, pet_id, user_id)

    payload = record_data.model_dump(exclude={"pet_id", "image_paths"})
    record = PetRecord(pet_id=pet.id, **payload)
    session.add(record)
    await session.flush()

    for image_path in image_paths:
        session.add(RecordImage(record_id=record.id, image_path=image_path))

    await _sync_pet_weight(session, pet, record.sub_type, record.weight_value)
    await session.commit()

    created_record = await _get_record_with_pet_by_id(session, record.id)
    assert created_record is not None
    return created_record


async def get_records(
    session: AsyncSession,
    user_id: int,
    pet_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
) -> Sequence[PetRecord]:
    """按条件查询当前用户的记录列表。"""

    query = (
        _get_record_query()
        .join(PetRecord.pet)
        .where(
            Pet.user_id == user_id,
            Pet.is_deleted.is_(False),
        )
        .order_by(PetRecord.record_date.desc(), PetRecord.id.desc())
    )

    if pet_id is not None:
        await get_pet_by_id(session, pet_id, user_id)
        query = query.where(PetRecord.pet_id == pet_id)

    if date_from is not None:
        query = query.where(PetRecord.record_date >= date_from)

    if date_to is not None:
        query = query.where(PetRecord.record_date <= date_to)

    if category is not None:
        query = query.where(PetRecord.category == category.strip())

    result = await session.scalars(query)
    return result.all()


async def get_record_by_id(
    session: AsyncSession,
    record_id: int,
    user_id: int,
) -> PetRecord:
    """获取单条记录详情。"""

    return await _ensure_record_access(session, record_id, user_id)


async def get_weight_trend(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    period: str,
) -> list[WeightTrendPoint]:
    """获取指定周期内的体重趋势数据。"""

    await get_pet_by_id(session, pet_id, user_id)

    query = (
        select(PetRecord.record_date, PetRecord.weight_value)
        .where(
            PetRecord.pet_id == pet_id,
            PetRecord.sub_type == WEIGHT_RECORD_SUB_TYPE,
            PetRecord.weight_value.is_not(None),
        )
        .order_by(PetRecord.record_date.asc(), PetRecord.id.asc())
    )

    start_date = _resolve_period_start(period)
    if start_date is not None:
        query = query.where(PetRecord.record_date >= start_date)

    rows = (await session.execute(query)).all()
    return [
        WeightTrendPoint(date=row.record_date, weight=row.weight_value)
        for row in rows
    ]


async def get_expense_stats(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
    year: int,
    month: int | None = None,
) -> ExpenseStatsResponse:
    """获取月度或年度消费统计。"""

    await get_pet_by_id(session, pet_id, user_id)

    query = (
        select(
            PetRecord.sub_type,
            func.coalesce(func.sum(PetRecord.amount), 0.0).label("amount"),
        )
        .where(
            PetRecord.pet_id == pet_id,
            PetRecord.category == EXPENSE_CATEGORY,
            PetRecord.amount.is_not(None),
            func.extract("year", PetRecord.record_date) == year,
        )
        .group_by(PetRecord.sub_type)
        .order_by(func.coalesce(func.sum(PetRecord.amount), 0.0).desc(), PetRecord.sub_type.asc())
    )

    if month is not None:
        query = query.where(func.extract("month", PetRecord.record_date) == month)

    rows = (await session.execute(query)).all()
    details = [
        ExpenseStatDetail(sub_type=row.sub_type, amount=float(row.amount or 0.0))
        for row in rows
    ]
    total = float(sum(item.amount for item in details))
    return ExpenseStatsResponse(total=total, details=details)


async def update_record(
    session: AsyncSession,
    record_id: int,
    user_id: int,
    record_data: RecordUpdate,
) -> PetRecord:
    """更新记录，并在需要时替换图片列表。"""

    record = await _ensure_record_access(session, record_id, user_id)
    update_data = record_data.model_dump(exclude_unset=True)
    image_paths = update_data.pop("image_paths", None)

    for field in UPDATABLE_FIELDS:
        if field in update_data:
            setattr(record, field, update_data[field])

    if image_paths is not None:
        record.images.clear()
        await session.flush()
        for image_path in image_paths:
            record.images.append(RecordImage(image_path=image_path))

    await _sync_pet_weight(session, record.pet, record.sub_type, record.weight_value)
    await session.commit()

    updated_record = await _get_record_with_pet_by_id(session, record.id)
    assert updated_record is not None
    return updated_record


async def delete_record(
    session: AsyncSession,
    record_id: int,
    user_id: int,
) -> None:
    """删除记录及其关联图片和提醒。"""

    record = await _ensure_record_access(session, record_id, user_id)

    await session.execute(
        delete(Reminder).where(Reminder.record_id == record.id)
    )
    await session.delete(record)
    await session.commit()
