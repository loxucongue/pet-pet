"""数据库模型基类与通用 UTC 时间戳字段。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 SQLAlchemy 模型的基类。"""


def utc_now() -> datetime:
    """返回当前 UTC 时间，并以无时区格式写入 MySQL。"""

    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    """提供创建时间与更新时间字段。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
