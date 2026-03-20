"""用户模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    """用户基础字段。"""

    openid: str | None = None
    nickname: str
    avatar_url: str | None = None
    user_type: str = "normal"
    vip_expire_time: datetime | None = None
    ai_analysis_used_count: int = 0


class UserCreate(UserBase):
    """创建用户请求模型。"""


class UserUpdate(BaseModel):
    """更新用户请求模型。"""

    nickname: str | None = None
    avatar_url: str | None = None


class UserProfileUpdate(UserUpdate):
    """用户资料更新请求模型。"""


class UserResponse(UserBase):
    """用户响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserQuotaSummary(BaseModel):
    """用户额度汇总响应模型。"""

    ai_analysis_remaining: int
    chat_daily_remaining: int | None
    user_type: str
    vip_expire_time: datetime | None = None
