"""AI 对话模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatSessionCreate(BaseModel):
    """创建会话请求模型。"""

    pet_id: int


class ChatSendRequest(BaseModel):
    """发送消息请求模型。"""

    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """校验并清洗消息内容。"""

        content = value.strip()
        if not content:
            raise ValueError("消息内容不能为空。")
        return content


class ChatSessionResponse(BaseModel):
    """会话响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    user_id: int
    title: str | None = None
    pet_nickname: str | None = None
    last_message_summary: str | None = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    """会话列表响应模型。"""

    items: list[ChatSessionResponse]
    total: int


class ChatMessageResponse(BaseModel):
    """消息响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime


class ChatMessageListResponse(BaseModel):
    """消息分页响应模型。"""

    total: int
    items: list[ChatMessageResponse]


class ChatQuotaResponse(BaseModel):
    """今日对话剩余额度响应。"""

    remaining: int | None


class ChatPermissionItem(BaseModel):
    """宠物对话权限项。"""

    pet_id: int
    pet_nickname: str
    pet_avatar: str | None = None
    species: str
    breed: str
    is_locked: bool
    has_session: bool
    lock_reason: str | None = None


class ChatPermissionsResponse(BaseModel):
    """宠物对话权限列表响应。"""

    items: list[ChatPermissionItem]
    max_chat_pets: int
    used_chat_pets: int
