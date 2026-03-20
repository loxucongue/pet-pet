"""用户服务，负责资料、额度和反馈的业务逻辑。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feedback, User, UserDailyQuota
from app.schemas.feedback import FeedbackCreate
from app.schemas.user import UserProfileUpdate
from app.services.quota_service import get_analysis_remaining, is_vip_active


NORMAL_CHAT_DAILY_LIMIT = 10


async def get_user_profile(session: AsyncSession, user_id: int) -> User:
    """获取用户资料。"""

    user = await session.get(User, user_id)
    if user is None:
        raise ValueError("用户不存在。")
    return user


async def update_user_profile(
    session: AsyncSession,
    user_id: int,
    data: UserProfileUpdate,
) -> User:
    """更新用户资料。"""

    user = await get_user_profile(session, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


async def get_user_quota_summary(session: AsyncSession, user_id: int) -> dict[str, object]:
    """获取用户额度汇总。"""

    user = await get_user_profile(session, user_id)
    now_utc = datetime.now(timezone.utc)
    vip_active = is_vip_active(user)

    effective_user_type = "vip" if vip_active else "normal"
    ai_analysis_remaining = await get_analysis_remaining(session, user)

    if vip_active:
        chat_daily_remaining: int | None = None
    else:
        quota = await session.scalar(
            select(UserDailyQuota).where(
                UserDailyQuota.user_id == user_id,
                UserDailyQuota.quota_date == now_utc.date(),
            )
        )
        chat_used = quota.chat_count if quota is not None else 0
        chat_daily_remaining = max(NORMAL_CHAT_DAILY_LIMIT - chat_used, 0)

    return {
        "ai_analysis_remaining": ai_analysis_remaining,
        "chat_daily_remaining": chat_daily_remaining,
        "user_type": effective_user_type,
        "vip_expire_time": user.vip_expire_time,
    }


async def create_feedback(
    session: AsyncSession,
    user_id: int,
    feedback_data: FeedbackCreate,
) -> Feedback:
    """创建用户反馈。"""

    await get_user_profile(session, user_id)

    feedback = Feedback(
        user_id=user_id,
        type=feedback_data.type,
        content=feedback_data.content,
        contact=feedback_data.contact,
    )
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)
    return feedback
