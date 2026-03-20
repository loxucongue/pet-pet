"""AI 对话模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatSessionCreate(BaseModel):
    """创建会话请求模型。"""

    pet_id: int
    user_id: int
    title: str | None = None


class ChatSessionResponse(BaseModel):
    """会话响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    user_id: int
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    """会话列表响应模型。"""

    items: list[ChatSessionResponse]
    total: int


class ChatMessageCreate(BaseModel):
    """创建消息请求模型。"""

    session_id: int
    role: str
    content: str


class ChatMessageResponse(BaseModel):
    """消息响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
