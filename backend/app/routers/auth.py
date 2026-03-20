"""认证模块路由，提供模拟登录与微信登录占位实现。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.auth import AuthTokenResponse, MockLoginRequest, WxLoginRequest
from app.schemas.user import UserResponse
from app.services.auth_service import create_access_token


router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _get_or_create_user_by_nickname(
    session: AsyncSession,
    nickname: str,
    avatar_url: str | None = None,
) -> User:
    """按昵称获取或创建模拟用户。"""

    user = await session.scalar(
        select(User).where(User.nickname == nickname)
    )
    if user is None:
        user = User(
            nickname=nickname,
            avatar_url=avatar_url,
            user_type="normal",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    if avatar_url and user.avatar_url != avatar_url:
        user.avatar_url = avatar_url
        await session.commit()
        await session.refresh(user)

    return user


@router.post("/mock-login", response_model=AuthTokenResponse, summary="模拟登录")
async def mock_login(
    payload: MockLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthTokenResponse:
    """本地开发环境使用昵称完成模拟登录。"""

    user = await _get_or_create_user_by_nickname(
        session=session,
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
    )
    access_token = create_access_token(user.id)
    return AuthTokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/wx-login", response_model=AuthTokenResponse, summary="微信登录占位接口")
async def wx_login(
    payload: WxLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthTokenResponse:
    """使用 code 模拟微信 openid 登录。"""

    openid = payload.code.strip()
    if not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code 不能为空。",
        )

    user = await session.scalar(
        select(User).where(User.openid == openid)
    )
    if user is None:
        user = User(
            openid=openid,
            nickname=f"微信用户_{openid[-6:]}",
            user_type="normal",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # 后续在这里替换成真实微信 code2Session 逻辑。
    access_token = create_access_token(user.id)
    return AuthTokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
