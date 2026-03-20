"""文章模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    """文章基础字段。"""

    title: str
    cover_image: str | None = None
    category: str
    content: str
    author: str
    view_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    is_published: bool = True


class ArticleCreate(ArticleBase):
    """创建文章请求模型。"""


class ArticleUpdate(BaseModel):
    """更新文章请求模型。"""

    title: str | None = None
    cover_image: str | None = None
    category: str | None = None
    content: str | None = None
    author: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    favorite_count: int | None = None
    is_published: bool | None = None


class ArticleResponse(ArticleBase):
    """文章响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    """文章列表响应模型。"""

    items: list[ArticleResponse]
    total: int

