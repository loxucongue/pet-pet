"""提醒模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import date, datetime, time

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


class ReminderBase(BaseModel):
    """提醒基础字段。"""

    reminder_type: str
    cycle_days: int
    reminder_time: time
    is_active: bool = True

    @field_validator("reminder_type")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """校验提醒类型字段。"""

        return _normalize_required_text(value)

    @field_validator("cycle_days")
    @classmethod
    def validate_cycle_days(cls, value: int) -> int:
        """校验提醒周期。"""

        if value <= 0:
            raise ValueError("周期天数必须大于 0。")
        return value


class ReminderCreate(ReminderBase):
    """创建提醒请求模型。"""

    pet_id: int
    record_id: int | None = None
    start_date: date | None = None


class ReminderUpdate(BaseModel):
    """更新提醒请求模型。"""

    record_id: int | None = None
    reminder_type: str | None = None
    cycle_days: int | None = None
    reminder_time: time | None = None
    next_reminder_date: date | None = None
    start_date: date | None = None
    is_active: bool | None = None

    @field_validator("reminder_type")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """校验可选提醒类型字段。"""

        return _normalize_optional_text(value)

    @field_validator("cycle_days")
    @classmethod
    def validate_optional_cycle_days(cls, value: int | None) -> int | None:
        """校验可选提醒周期。"""

        if value is None:
            return None
        if value <= 0:
            raise ValueError("周期天数必须大于 0。")
        return value


class ReminderResponse(ReminderBase):
    """提醒响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    record_id: int | None = None
    next_reminder_date: date
    pet_nickname: str | None = None
    created_at: datetime
    updated_at: datetime
