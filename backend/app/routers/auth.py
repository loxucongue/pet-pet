"""认证模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/ping", summary="认证模块占位接口")
async def ping_auth() -> dict[str, str]:
    """返回认证模块初始化状态。"""

    return {"module": "auth", "status": "ready"}

