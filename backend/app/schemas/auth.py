"""认证模块的请求与响应数据模型。"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.user import UserResponse


class MockLoginRequest(BaseModel):
    """模拟登录请求模型。"""

    nickname: str
    avatar_url: str | None = None


class WxLoginRequest(BaseModel):
    """微信登录请求模型。"""

    code: str


class AuthTokenResponse(BaseModel):
    """登录响应模型。"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse

