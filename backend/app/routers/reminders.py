"""提醒模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("/ping", summary="提醒模块占位接口")
async def ping_reminders() -> dict[str, str]:
    """返回提醒模块初始化状态。"""

    return {"module": "reminders", "status": "ready"}

