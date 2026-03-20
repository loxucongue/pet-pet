"""用户模块路由，提供资料、额度和反馈接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.schemas.user import UserProfileUpdate, UserQuotaSummary, UserResponse
from app.services.user_service import (
    create_feedback,
    get_user_profile,
    get_user_quota_summary,
    update_user_profile,
)
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile", response_model=UserResponse, summary="获取当前用户信息")
async def read_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """获取当前登录用户资料。"""

    user = await get_user_profile(session, current_user.id)
    return UserResponse.model_validate(user)


@router.put("/profile", response_model=UserResponse, summary="修改当前用户信息")
async def edit_user_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """修改当前用户昵称和头像。"""

    user = await update_user_profile(session, current_user.id, payload)
    return UserResponse.model_validate(user)


@router.get("/quota", response_model=UserQuotaSummary, summary="获取当前用户额度汇总")
async def read_user_quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserQuotaSummary:
    """获取当前用户额度汇总。"""

    quota_summary = await get_user_quota_summary(session, current_user.id)
    return UserQuotaSummary.model_validate(quota_summary)


@router.post("/feedback", response_model=FeedbackResponse, summary="提交用户反馈")
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FeedbackResponse:
    """提交当前用户反馈。"""

    feedback = await create_feedback(session, current_user.id, payload)
    return FeedbackResponse.model_validate(feedback)
