"""统一导出所有路由模块。"""

from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.community import router as community_router
from app.routers.health import router as health_router
from app.routers.pets import router as pets_router
from app.routers.records import router as records_router
from app.routers.reminders import router as reminders_router
from app.routers.upload import router as upload_router
from app.routers.user import router as user_router


all_routers = (
    auth_router,
    pets_router,
    upload_router,
    records_router,
    reminders_router,
    health_router,
    chat_router,
    community_router,
    admin_router,
    user_router,
)

__all__ = ["all_routers"]
