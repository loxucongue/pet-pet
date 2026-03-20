"""AI 对话模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/ping", summary="对话模块占位接口")
async def ping_chat() -> dict[str, str]:
    """返回对话模块初始化状态。"""

    return {"module": "chat", "status": "ready"}

