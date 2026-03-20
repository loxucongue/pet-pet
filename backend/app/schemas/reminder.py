"""提醒模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class ReminderBase(BaseModel):
    """提醒基础字段。"""

    reminder_type: str
    cycle_days: int
    reminder_time: time
    next_reminder_date: date
    is_active: bool = True


class ReminderCreate(ReminderBase):
    """创建提醒请求模型。"""

    pet_id: int
    record_id: int | None = None


class ReminderUpdate(BaseModel):
    """更新提醒请求模型。"""

    record_id: int | None = None
    reminder_type: str | None = None
    cycle_days: int | None = None
    reminder_time: time | None = None
    next_reminder_date: date | None = None
    is_active: bool | None = None


class ReminderResponse(ReminderBase):
    """提醒响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    record_id: int | None = None
    created_at: datetime
    updated_at: datetime
