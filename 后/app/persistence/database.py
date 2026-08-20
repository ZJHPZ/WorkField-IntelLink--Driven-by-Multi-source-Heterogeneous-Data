"""MySQL 异步引擎 + session 工厂（aiomysql 驱动）。

对接 zhiyv 数据库，存储图谱数据（skill_stats / verified_skills / graph_snapshots 等）。
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import Settings

logger = logging.getLogger(__name__)

_engine = None
_session_factory: async_sessionmaker | None = None


class Base(DeclarativeBase):
    """SQLAlchemy ORM 基类。"""
    pass


# 确保 zhiyv 模型被注册到 Base.metadata
import app.persistence.zhiyv_models  # noqa: F401, E402


async def init_db(settings: Settings) -> None:
    """初始化 MySQL 异步引擎和 session 工厂。"""
    global _engine, _session_factory
    _engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=10,
        max_overflow=5,
        pool_recycle=3600,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    # 建表
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"MySQL 已连接: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")


async def close_db() -> None:
    """关闭数据库连接。"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("MySQL 已关闭")


async def get_session() -> AsyncSession:
    """获取异步 session（FastAPI Depends 使用）。"""
    if _session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    async with _session_factory() as session:
        yield session
