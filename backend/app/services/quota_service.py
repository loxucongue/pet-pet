"""用户 AI 分析与对话额度管理。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HealthReport, Pet, User, UserDailyQuota


NORMAL_ANALYSIS_LIMIT = 3
VIP_MONTHLY_ANALYSIS_LIMIT = 10
NORMAL_CHAT_DAILY_LIMIT = 10
NORMAL_CHAT_PET_LIMIT = 1
VIP_CHAT_PET_LIMIT = 3


class AnalysisQuotaExceededError(Exception):
    """用户 AI 分析额度已耗尽。"""

    def __init__(self, remaining: int = 0, detail: str = "AI分析次数已用完") -> None:
        self.remaining = remaining
        self.detail = detail
        super().__init__(detail)


class ChatQuotaExceededError(Exception):
    """用户今日 AI 对话额度已耗尽。"""

    def __init__(self, remaining: int = 0, detail: str = "今日AI对话次数已用完") -> None:
        self.remaining = remaining
        self.detail = detail
        super().__init__(detail)


def is_vip_active(user: User) -> bool:
    """判断会员是否处于有效期内。"""

    if user.user_type != "vip" or user.vip_expire_time is None:
        return False

    vip_expire_time = user.vip_expire_time
    if vip_expire_time.tzinfo is not None:
        vip_expire_time = vip_expire_time.astimezone(timezone.utc).replace(tzinfo=None)

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    return vip_expire_time > now_utc


async def check_analysis_quota(session: AsyncSession, user: User) -> bool:
    """检查用户是否还有 AI 分析额度。"""

    return await get_analysis_remaining(session, user) > 0


async def consume_analysis_quota(session: AsyncSession, user: User) -> None:
    """扣减 AI 分析额度。"""

    if is_vip_active(user):
        return

    user.ai_analysis_used_count += 1
    await session.flush()


async def get_analysis_remaining(session: AsyncSession, user: User) -> int:
    """获取用户剩余 AI 分析次数。"""

    if is_vip_active(user):
        used_count = await _get_vip_monthly_completed_count(session, user.id)
        return max(VIP_MONTHLY_ANALYSIS_LIMIT - used_count, 0)

    return max(NORMAL_ANALYSIS_LIMIT - user.ai_analysis_used_count, 0)


async def ensure_analysis_quota(session: AsyncSession, user: User) -> None:
    """确保当前用户仍有 AI 分析额度。"""

    remaining = await get_analysis_remaining(session, user)
    if remaining <= 0:
        raise AnalysisQuotaExceededError(remaining=0)


async def check_chat_quota(session: AsyncSession, user: User) -> bool:
    """检查用户是否还有今日 AI 对话额度。"""

    remaining = await get_chat_remaining(session, user)
    return remaining is None or remaining > 0


async def consume_chat_quota(session: AsyncSession, user: User) -> None:
    """扣减今日 AI 对话额度。"""

    if is_vip_active(user):
        return

    quota = await _get_today_chat_quota(session, user.id)
    if quota is None:
        quota = UserDailyQuota(
            user_id=user.id,
            quota_date=_get_today_utc_date(),
            chat_count=0,
        )
        session.add(quota)
        await session.flush()

    quota.chat_count += 1
    await session.flush()


async def get_chat_remaining(session: AsyncSession, user: User) -> int | None:
    """获取今日 AI 对话剩余次数。"""

    if is_vip_active(user):
        return None

    quota = await _get_today_chat_quota(session, user.id)
    used_count = quota.chat_count if quota is not None else 0
    return max(NORMAL_CHAT_DAILY_LIMIT - used_count, 0)


async def ensure_chat_quota(session: AsyncSession, user: User) -> None:
    """确保当前用户仍有今日 AI 对话额度。"""

    remaining = await get_chat_remaining(session, user)
    if remaining is not None and remaining <= 0:
        raise ChatQuotaExceededError(remaining=0)


def get_chat_pet_limit(user: User) -> int:
    """获取用户可开启 AI 对话的宠物数量上限。"""

    return VIP_CHAT_PET_LIMIT if is_vip_active(user) else NORMAL_CHAT_PET_LIMIT


async def _get_vip_monthly_completed_count(session: AsyncSession, user_id: int) -> int:
    """获取会员用户当月已完成的分析次数。"""

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    result = await session.scalar(
        select(func.count(HealthReport.id))
        .select_from(HealthReport)
        .join(Pet, HealthReport.pet_id == Pet.id)
        .where(
            Pet.user_id == user_id,
            Pet.is_deleted.is_(False),
            HealthReport.status == "completed",
            HealthReport.updated_at >= month_start,
            HealthReport.updated_at < next_month_start,
        )
    )
    return int(result or 0)


async def _get_today_chat_quota(session: AsyncSession, user_id: int) -> UserDailyQuota | None:
    """获取用户今日对话额度记录。"""

    return await session.scalar(
        select(UserDailyQuota).where(
            UserDailyQuota.user_id == user_id,
            UserDailyQuota.quota_date == _get_today_utc_date(),
        )
    )


def _get_today_utc_date():
    """返回当前 UTC 日期。"""

    return datetime.now(timezone.utc).date()
