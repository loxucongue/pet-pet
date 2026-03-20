"""用户每日额度模型，保存每日 AI 对话次数。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utc_now


class UserDailyQuota(Base):
    """用户每日额度模型。"""

    __tablename__ = "user_daily_quota"
    __table_args__ = (
        UniqueConstraint("user_id", "quota_date", name="uq_user_daily_quota_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quota_date: Mapped[date] = mapped_column(Date, nullable=False)
    chat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(back_populates="daily_quotas")

