"""管理后台模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/ping", summary="后台模块占位接口")
async def ping_admin() -> dict[str, str]:
    """返回后台模块初始化状态。"""

    return {"module": "admin", "status": "ready"}

