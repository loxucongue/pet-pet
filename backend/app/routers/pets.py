"""宠物模块占位路由。"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/pets", tags=["pets"])


@router.get("/ping", summary="宠物模块占位接口")
async def ping_pets() -> dict[str, str]:
    """返回宠物模块初始化状态。"""

    return {"module": "pets", "status": "ready"}

