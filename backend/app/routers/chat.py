"""AI 对话模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db_session
from app.models import User
from app.schemas.chat import (
    ChatMessageListResponse,
    ChatMessageResponse,
    ChatPermissionsResponse,
    ChatQuotaResponse,
    ChatSendRequest,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
)
from app.services.chat_service import (
    create_session,
    delete_session,
    get_chat_permissions,
    get_session_messages,
    get_sessions,
    send_message,
)
from app.services.pet_service import get_pet_by_id
from app.services.quota_service import ChatQuotaExceededError, get_chat_remaining
from app.utils.deps import get_current_user


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse, summary="创建 AI 对话会话")
async def create_chat_session_route(
    payload: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ChatSessionResponse:
    """创建 AI 对话会话。"""

    chat_session = await create_session(session, payload.pet_id, current_user.id)
    pet = await get_pet_by_id(session, payload.pet_id, current_user.id)
    return ChatSessionResponse.model_validate(
        {
            "id": chat_session.id,
            "pet_id": chat_session.pet_id,
            "user_id": chat_session.user_id,
            "title": chat_session.title,
            "pet_nickname": pet.nickname,
            "last_message_summary": None,
            "message_count": 0,
            "created_at": chat_session.created_at,
            "updated_at": chat_session.updated_at,
        }
    )


@router.get("/sessions", response_model=ChatSessionListResponse, summary="获取 AI 对话会话列表")
async def list_chat_sessions_route(
    pet_id: int | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ChatSessionListResponse:
    """获取当前用户的 AI 对话会话列表。"""

    sessions = await get_sessions(session, current_user.id, pet_id)
    return ChatSessionListResponse(
        items=[ChatSessionResponse.model_validate(item) for item in sessions],
        total=len(sessions),
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageListResponse,
    summary="获取会话消息历史",
)
async def list_chat_session_messages_route(
    session_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ChatMessageListResponse:
    """分页获取会话消息历史。"""

    payload = await get_session_messages(session, session_id, current_user.id, page, page_size)
    return ChatMessageListResponse(
        total=payload["total"],
        items=[ChatMessageResponse.model_validate(item) for item in payload["items"]],
    )


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_chat_session_route(
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """删除会话及其关联消息。"""

    await delete_session(session, session_id, current_user.id)
    return {"status": "deleted"}


@router.post(
    "/sessions/{session_id}/send",
    summary="发送消息并流式获取 AI 回复",
    response_model=None,
)
async def send_chat_message_route(
    session_id: int,
    payload: ChatSendRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> EventSourceResponse | JSONResponse:
    """发送消息并以 SSE 流式返回 AI 回复。"""

    try:
        event_stream = await send_message(
            session,
            session_id,
            current_user.id,
            payload.content,
        )
    except ChatQuotaExceededError as exc:
        return JSONResponse(
            status_code=403,
            content={"detail": exc.detail, "remaining": exc.remaining},
        )

    return EventSourceResponse(event_stream)


@router.get("/quota", response_model=ChatQuotaResponse, summary="查询今日对话剩余次数")
async def get_chat_quota_route(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ChatQuotaResponse:
    """查询当前用户今日剩余对话次数。"""

    remaining = await get_chat_remaining(session, current_user)
    return ChatQuotaResponse(remaining=remaining)


@router.get("/permissions", response_model=ChatPermissionsResponse, summary="查询宠物对话权限")
async def get_chat_permissions_route(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ChatPermissionsResponse:
    """查询当前用户全部宠物的对话权限状态。"""

    permissions = await get_chat_permissions(session, current_user.id)
    return ChatPermissionsResponse.model_validate(permissions)
