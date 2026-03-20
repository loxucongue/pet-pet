"""用户模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/ping", summary="用户模块占位接口")
async def ping_user() -> dict[str, str]:
    """返回用户模块初始化状态。"""

    return {"module": "user", "status": "ready"}

