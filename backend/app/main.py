"""FastAPI 应用入口，负责注册中间件和路由。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import all_routers


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router)


@app.get("/", tags=["system"], summary="应用状态")
async def read_root() -> dict[str, str]:
    """返回后端启动状态。"""

    return {"message": "pppet backend is running"}


@app.get("/healthz", tags=["system"], summary="健康检查")
async def healthcheck() -> dict[str, str]:
    """返回服务健康检查结果。"""

    return {"status": "ok"}

