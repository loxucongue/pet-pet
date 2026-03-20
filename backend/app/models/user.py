"""用户模型，保存账号基础信息与会员状态。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    """应用用户模型。"""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("user_type IN ('normal', 'vip')", name="ck_users_user_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str | None] = mapped_column(String(128), unique=True, index=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_type: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", server_default="normal")
    vip_expire_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    ai_analysis_used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    pets: Mapped[list["Pet"]] = relationship(
        back_populates="user",
        cascade="save-update, merge",
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user",
        cascade="save-update, merge",
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    favorite_articles: Mapped[list["UserFavorite"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    liked_articles: Mapped[list["UserLike"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    daily_quotas: Mapped[list["UserDailyQuota"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    payment_records: Mapped[list["PaymentRecord"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    feedback_entries: Mapped[list["Feedback"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

