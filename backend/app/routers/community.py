"""社区模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("/ping", summary="社区模块占位接口")
async def ping_community() -> dict[str, str]:
    """返回社区模块初始化状态。"""

    return {"module": "community", "status": "ready"}

