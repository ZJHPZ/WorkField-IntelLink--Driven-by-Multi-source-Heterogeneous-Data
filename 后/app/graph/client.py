"""Neo4j 异步驱动封装。

设计方案 §5：图数据库选型 Neo4j 5.x，存储岗位-技能-证据关系。
使用官方 neo4j 5.x 异步驱动。
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncManagedTransaction

from app.config import Settings

logger = logging.getLogger(__name__)

_driver = None


async def init_neo4j(settings: Settings) -> None:
    """初始化 Neo4j 驱动（全局单例）。"""
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=3600,
        max_connection_pool_size=50,
    )
    # 连接验证
    await _driver.verify_connectivity()
    logger.info(f"Neo4j 已连接: {settings.NEO4J_URI}")
    # 初始化约束和索引
    await _init_constraints()


async def close_neo4j() -> None:
    """关闭 Neo4j 驱动。"""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j 已关闭")


def get_driver():
    """获取当前驱动实例。"""
    if _driver is None:
        raise RuntimeError("Neo4j 驱动未初始化，请先调用 init_neo4j()")
    return _driver


async def get_session():
    """获取异步 session（上下文管理器）。"""
    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        yield session


async def run_cypher(query: str, **params) -> list[dict]:
    """执行一条 Cypher 查询，返回记录列表。"""
    driver = get_driver()
    records, _, _ = await driver.execute_query(query, **params)
    return [record.data() for record in records]


async def _init_constraints() -> None:
    """创建唯一性约束和索引。"""
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Position) REQUIRE p.position_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TechStack) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Snapshot) REQUIRE s.snapshot_id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (p:Position) ON (p.position_type)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.status)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.category)",
    ]
    for q in queries:
        try:
            await run_cypher(q)
        except Exception as e:
            logger.warning(f"约束创建失败（可能已存在）: {e}")
