"""测试配置 —— MySQL（真实连接）+ Agent fixtures"""
import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def event_loop():
    """整个测试会话共享一个 event loop"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_initialized():
    """初始化 MySQL 连接（整个 session 一次）。"""
    from app.config import get_settings
    from app.persistence.database import init_db, close_db
    settings = get_settings()
    try:
        await init_db(settings)
        yield True
    finally:
        await close_db()


@pytest.fixture(scope="session")
def system():
    """初始化 MultiAgentSystem（不调 LLM）。"""
    from app.agents.system import get_system
    return get_system().initialize(llm_client=None)


@pytest.fixture(scope="session")
def registry(system):
    from app.agents.registry import get_registry
    return get_registry()


@pytest.fixture(scope="session")
def router():
    from app.agents.router import get_intent_router
    return get_intent_router()
