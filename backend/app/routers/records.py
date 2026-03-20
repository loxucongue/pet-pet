"""记录模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("/ping", summary="记录模块占位接口")
async def ping_records() -> dict[str, str]:
    """返回记录模块初始化状态。"""

    return {"module": "records", "status": "ready"}

