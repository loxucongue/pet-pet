"""用户文章互动模型，保存收藏与点赞关系。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utc_now


class UserFavorite(Base):
    """文章收藏模型。"""

    __tablename__ = "user_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_favorites_user_article"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(back_populates="favorite_articles")
    article: Mapped["Article"] = relationship(back_populates="favorites")


class UserLike(Base):
    """文章点赞模型。"""

    __tablename__ = "user_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_likes_user_article"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(back_populates="liked_articles")
    article: Mapped["Article"] = relationship(back_populates="likes")

