"""AI 对话服务，负责会话管理、消息历史与流式回复。"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Sequence
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ChatMessage, ChatSession, HealthReport, Pet, User
from app.models.base import utc_now
from app.services.deepseek_service import DeepSeekService, DeepSeekServiceError
from app.services.pet_service import get_pet_by_id, get_pets_by_user
from app.services.quota_service import (
    ChatQuotaExceededError,
    consume_chat_quota,
    ensure_chat_quota,
    get_chat_pet_limit,
    get_chat_remaining,
    is_vip_active,
)


SESSION_TITLE_MAX_LENGTH = 20
SESSION_SUMMARY_MAX_LENGTH = 60
CONTEXT_MESSAGE_LIMIT = 10
HEALTH_REPORT_SUMMARY_LIMIT = 3
HEALTH_INTERPRETATION_SUMMARY_LENGTH = 200


async def create_session(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
) -> ChatSession:
    """创建 AI 对话会话。"""

    await get_pet_by_id(session, pet_id, user_id)
    if not await check_pet_chat_permission(session, pet_id, user_id):
        user = await _get_user_by_id(session, user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_build_pet_permission_denied_detail(user),
        )

    chat_session = ChatSession(
        pet_id=pet_id,
        user_id=user_id,
        title=None,
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return chat_session


async def get_sessions(
    session: AsyncSession,
    user_id: int,
    pet_id: int | None = None,
) -> list[dict[str, Any]]:
    """获取当前用户的会话列表。"""

    if pet_id is not None:
        await get_pet_by_id(session, pet_id, user_id)

    message_count_subquery = (
        select(func.count(ChatMessage.id))
        .where(ChatMessage.session_id == ChatSession.id)
        .correlate(ChatSession)
        .scalar_subquery()
    )
    last_message_subquery = (
        select(ChatMessage.content)
        .where(ChatMessage.session_id == ChatSession.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(1)
        .correlate(ChatSession)
        .scalar_subquery()
    )

    statement = (
        select(
            ChatSession,
            Pet.nickname.label("pet_nickname"),
            message_count_subquery.label("message_count"),
            last_message_subquery.label("last_message_summary"),
        )
        .join(Pet, ChatSession.pet_id == Pet.id)
        .where(
            ChatSession.user_id == user_id,
            Pet.is_deleted.is_(False),
        )
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
    )
    if pet_id is not None:
        statement = statement.where(ChatSession.pet_id == pet_id)

    rows = (await session.execute(statement)).all()
    items: list[dict[str, Any]] = []
    for chat_session, pet_nickname, message_count, last_message_summary in rows:
        items.append(
            {
                "id": chat_session.id,
                "pet_id": chat_session.pet_id,
                "user_id": chat_session.user_id,
                "title": chat_session.title,
                "pet_nickname": pet_nickname,
                "last_message_summary": _build_message_summary(last_message_summary),
                "message_count": int(message_count or 0),
                "created_at": chat_session.created_at,
                "updated_at": chat_session.updated_at,
            }
        )
    return items


async def get_session_messages(
    session: AsyncSession,
    session_id: int,
    user_id: int,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """分页获取会话消息历史。"""

    await _ensure_session_access(session, session_id, user_id)

    total = await session.scalar(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
    )
    offset = (page - 1) * page_size
    messages = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
            .offset(offset)
            .limit(page_size)
        )
    ).all()
    return {
        "total": int(total or 0),
        "items": list(messages),
    }


async def delete_session(
    session: AsyncSession,
    session_id: int,
    user_id: int,
) -> None:
    """删除会话及关联消息。"""

    chat_session = await _ensure_session_access(session, session_id, user_id)
    await session.delete(chat_session)
    await session.commit()


async def send_message(
    session: AsyncSession,
    session_id: int,
    user_id: int,
    content: str,
    *,
    deepseek_service: DeepSeekService | Any | None = None,
) -> AsyncGenerator[dict[str, str], None]:
    """发送消息并流式返回 AI 回复。"""

    normalized_content = content.strip()
    if not normalized_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="消息内容不能为空。",
        )

    chat_session = await _ensure_session_access(session, session_id, user_id)
    user = await _get_user_by_id(session, user_id)
    await ensure_chat_quota(session, user)

    existing_message_count = int(
        await session.scalar(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
        )
        or 0
    )

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=normalized_content,
    )
    session.add(user_message)
    if existing_message_count == 0 and not chat_session.title:
        chat_session.title = normalized_content[:SESSION_TITLE_MAX_LENGTH]
    chat_session.updated_at = utc_now()
    await session.commit()
    await session.refresh(user_message)

    context_messages = await _load_context_messages(session, session_id, CONTEXT_MESSAGE_LIMIT)
    pet_context = await _build_pet_context(session, chat_session.pet)
    ai_service = deepseek_service or DeepSeekService()

    async def event_stream() -> AsyncGenerator[dict[str, str], None]:
        assistant_chunks: list[str] = []
        try:
            yield _build_sse_event(
                "start",
                {
                    "session_id": chat_session.id,
                    "title": chat_session.title,
                    "user_message_id": user_message.id,
                },
            )

            async for token in ai_service.chat_stream(
                [{"role": item.role, "content": item.content} for item in context_messages],
                pet_context,
            ):
                assistant_chunks.append(token)
                yield _build_sse_event("message", token)

            assistant_content = "".join(assistant_chunks).strip()
            if not assistant_content:
                raise DeepSeekServiceError("AI 未返回有效回复。")

            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
            )
            session.add(assistant_message)
            chat_session.updated_at = utc_now()
            await consume_chat_quota(session, user)
            await session.commit()
            await session.refresh(assistant_message)

            remaining = await get_chat_remaining(session, user)
            yield _build_sse_event(
                "done",
                {
                    "session_id": chat_session.id,
                    "assistant_message_id": assistant_message.id,
                    "remaining": remaining,
                },
            )
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            yield _build_sse_event(
                "error",
                {"detail": _build_stream_error_message(exc)},
            )

    return event_stream()


async def check_pet_chat_permission(
    session: AsyncSession,
    pet_id: int,
    user_id: int,
) -> bool:
    """检查该宠物是否允许开启 AI 对话。"""

    await get_pet_by_id(session, pet_id, user_id)
    user = await _get_user_by_id(session, user_id)
    enabled_pet_ids = await _get_enabled_chat_pet_ids(session, user_id)

    if pet_id in enabled_pet_ids:
        return True

    return len(enabled_pet_ids) < get_chat_pet_limit(user)


async def get_chat_permissions(session: AsyncSession, user_id: int) -> dict[str, Any]:
    """获取当前用户全部宠物的对话权限状态。"""

    user = await _get_user_by_id(session, user_id)
    pets = await get_pets_by_user(session, user_id)
    enabled_pet_ids = await _get_enabled_chat_pet_ids(session, user_id)
    max_chat_pets = get_chat_pet_limit(user)
    used_chat_pets = len(enabled_pet_ids)

    items: list[dict[str, Any]] = []
    for pet in pets:
        has_session = pet.id in enabled_pet_ids
        is_locked = not has_session and used_chat_pets >= max_chat_pets
        items.append(
            {
                "pet_id": pet.id,
                "pet_nickname": pet.nickname,
                "pet_avatar": pet.avatar,
                "species": pet.species,
                "breed": pet.breed,
                "is_locked": is_locked,
                "has_session": has_session,
                "lock_reason": _build_pet_permission_denied_detail(user) if is_locked else None,
            }
        )

    return {
        "items": items,
        "max_chat_pets": max_chat_pets,
        "used_chat_pets": used_chat_pets,
    }


async def _ensure_session_access(
    session: AsyncSession,
    session_id: int,
    user_id: int,
) -> ChatSession:
    """校验会话归属权。"""

    chat_session = await session.scalar(
        select(ChatSession)
        .options(selectinload(ChatSession.pet))
        .where(ChatSession.id == session_id)
    )
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在。",
        )

    if chat_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该会话。",
        )

    if chat_session.pet is None or chat_session.pet.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在。",
        )

    return chat_session


async def _get_user_by_id(session: AsyncSession, user_id: int) -> User:
    """按 ID 获取用户。"""

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在。",
        )
    return user


async def _get_enabled_chat_pet_ids(session: AsyncSession, user_id: int) -> set[int]:
    """获取当前用户已开启 AI 对话的宠物集合。"""

    pet_ids = (
        await session.scalars(
            select(ChatSession.pet_id)
            .where(ChatSession.user_id == user_id)
            .distinct()
        )
    ).all()
    return {int(pet_id) for pet_id in pet_ids}


async def _load_context_messages(
    session: AsyncSession,
    session_id: int,
    limit: int,
) -> Sequence[ChatMessage]:
    """加载会话最近上下文消息。"""

    recent_messages = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
    ).all()
    return list(reversed(recent_messages))


async def _build_pet_context(session: AsyncSession, pet: Pet) -> dict[str, Any]:
    """构造注入 system prompt 的宠物完整档案与健康摘要。"""

    recent_reports = (
        await session.scalars(
            select(HealthReport)
            .where(
                HealthReport.pet_id == pet.id,
                HealthReport.status == "completed",
            )
            .order_by(HealthReport.updated_at.desc(), HealthReport.id.desc())
            .limit(HEALTH_REPORT_SUMMARY_LIMIT)
        )
    ).all()

    return {
        "nickname": pet.nickname,
        "species": pet.species,
        "breed": pet.breed,
        "gender": pet.gender,
        "birthday": str(pet.birthday) if pet.birthday else None,
        "approximate_age": pet.approximate_age,
        "weight": pet.weight,
        "is_neutered": pet.is_neutered,
        "fur_color": pet.fur_color,
        "adoption_date": str(pet.adoption_date) if pet.adoption_date else None,
        "allergy_history": pet.allergy_history,
        "chronic_disease": pet.chronic_disease,
        "current_food_brand": pet.current_food_brand,
        "recent_health_reports": [
            {
                "report_id": report.id,
                "date": report.updated_at.isoformat(),
                "indicators": _safe_parse_json(report.parsed_indicators_json),
                "interpretation_summary": _build_message_summary(
                    report.ai_interpretation,
                    HEALTH_INTERPRETATION_SUMMARY_LENGTH,
                ),
            }
            for report in recent_reports
        ],
    }


def _build_pet_permission_denied_detail(user: User) -> str:
    """构造宠物对话权限不足提示。"""

    if is_vip_active(user):
        return "当前账号最多支持 3 只宠物开启 AI 对话。"
    return "普通用户仅支持 1 只宠物开启 AI 对话。"


def _build_message_summary(content: str | None, limit: int = SESSION_SUMMARY_MAX_LENGTH) -> str | None:
    """裁剪消息摘要。"""

    if not content:
        return None

    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _safe_parse_json(value: str | None) -> Any:
    """安全解析 JSON 字符串。"""

    if not value:
        return None

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _build_sse_event(event: str, data: Any) -> dict[str, str]:
    """构造 SSE 事件。"""

    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, default=str)
    return {
        "event": event,
        "data": payload,
    }


def _build_stream_error_message(exc: Exception) -> str:
    """构造流式对话错误信息。"""

    if isinstance(exc, HTTPException):
        return str(exc.detail)

    if isinstance(exc, ChatQuotaExceededError):
        return exc.detail

    if isinstance(exc, DeepSeekServiceError):
        return f"AI 对话失败：{exc}"

    return "AI 对话暂时不可用，请稍后重试。"
