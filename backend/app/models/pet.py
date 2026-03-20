"""宠物模型，保存宠物档案与软删除信息。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Pet(TimestampMixin, Base):
    """宠物档案模型。"""

    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str] = mapped_column(String(20), nullable=False)
    breed: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    approximate_age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_neutered: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fur_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adoption_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    allergy_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    chronic_disease: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_food_brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    user: Mapped["User"] = relationship(back_populates="pets")
    records: Mapped[list["PetRecord"]] = relationship(
        back_populates="pet",
        cascade="save-update, merge",
    )
    health_reports: Mapped[list["HealthReport"]] = relationship(
        back_populates="pet",
        cascade="save-update, merge",
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="pet",
        cascade="save-update, merge",
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="pet",
        cascade="save-update, merge",
    )
