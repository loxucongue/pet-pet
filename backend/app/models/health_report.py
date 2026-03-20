"""AI 体检分析模型，保存原始报告与解读结果。"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class HealthReport(TimestampMixin, Base):
    """宠物健康报告模型。"""

    __tablename__ = "health_reports"
    __table_args__ = (
        CheckConstraint("file_type IN ('image', 'pdf')", name="ck_health_reports_file_type"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_health_reports_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True)
    original_file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    ocr_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_indicators_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")

    pet: Mapped["Pet"] = relationship(back_populates="health_reports")

