"""用户 AI 分析额度管理。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HealthReport, Pet, User


NORMAL_ANALYSIS_LIMIT = 3
VIP_MONTHLY_ANALYSIS_LIMIT = 10


class AnalysisQuotaExceededError(Exception):
    """用户 AI 分析额度已耗尽。"""

    def __init__(self, remaining: int = 0, detail: str = "AI分析次数已用完") -> None:
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
