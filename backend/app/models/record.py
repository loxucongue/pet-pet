"""记录模型，保存宠物的日常、健康与医疗记录。"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PetRecord(TimestampMixin, Base):
    """宠物记录模型。"""

    __tablename__ = "pet_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_type: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    pet: Mapped["Pet"] = relationship(back_populates="records")
    images: Mapped[list["RecordImage"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="record",
        cascade="save-update, merge",
    )

