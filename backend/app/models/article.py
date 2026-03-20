"""社区文章模型，保存文章内容与互动计数。"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Article(TimestampMixin, Base):
    """社区文章模型。"""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    favorite_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )
    favorites: Mapped[list["UserFavorite"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )
    likes: Mapped[list["UserLike"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )

