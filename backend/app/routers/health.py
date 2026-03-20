"""健康分析模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/ping", summary="健康模块占位接口")
async def ping_health() -> dict[str, str]:
    """返回健康模块初始化状态。"""

    return {"module": "health", "status": "ready"}

