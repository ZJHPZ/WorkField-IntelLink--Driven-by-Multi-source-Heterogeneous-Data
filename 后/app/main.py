"""FastAPI 应用入口 —— 工厂模式 + 生命周期管理。

数据库：仅 MySQL (zhiyv)，不再依赖 Neo4j。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    """应用生命周期：启动时初始化 MySQL 连接，关闭时清理。"""
    settings = get_settings()
    from app.persistence.database import init_db, close_db

    await init_db(settings)
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 根路径重定向到 API 文档
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # 注册路由
    from app.api.router import api_router
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
