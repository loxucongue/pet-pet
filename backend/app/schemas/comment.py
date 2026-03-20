"""评论模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentBase(BaseModel):
    """评论基础字段。"""

    content: str


class CommentCreate(CommentBase):
    """创建评论请求模型。"""

    article_id: int
    user_id: int


class CommentResponse(CommentBase):
    """评论响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    user_id: int
    created_at: datetime


class CommentListResponse(BaseModel):
    """评论列表响应模型。"""

    items: list[CommentResponse]
    total: int

