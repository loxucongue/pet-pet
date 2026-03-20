"""提醒模型，保存基于记录或宠物的周期提醒。"""

from __future__ import annotations

from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Reminder(TimestampMixin, Base):
    """宠物提醒模型。"""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int | None] = mapped_column(
        ForeignKey("pet_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type: Mapped[str] = mapped_column(String(100), nullable=False)
    cycle_days: Mapped[int] = mapped_column(Integer, nullable=False)
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    next_reminder_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    record: Mapped["PetRecord | None"] = relationship(back_populates="reminders")
    pet: Mapped["Pet"] = relationship(back_populates="reminders")

