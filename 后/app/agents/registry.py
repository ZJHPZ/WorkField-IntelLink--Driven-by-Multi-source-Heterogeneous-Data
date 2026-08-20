"""Agent 注册表 —— 单例，管理所有 Agent 实例。

核心职责：
- 意图 → Agent 映射
- 依赖关系图
- can_execute(agent_id, completed) 判定
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.agent_state import IntentType, ProcessingMode
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent 注册表（单例）。"""

    _instance: "AgentRegistry | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Agent 实例存储
        self._agents: dict[str, BaseAgent] = {}

        # 意图 → Agent ID 映射
        self._intent_map: dict[IntentType, str] = {}

        # 依赖图: agent_id → [依赖的 agent_id...]
        self._dependency_graph: dict[str, list[str]] = {}

        logger.info("[Registry] 初始化完成")

    # ── 注册 / 注销 ──

    def register(self, agent: BaseAgent) -> None:
        if agent.agent_id in self._agents:
            logger.warning(f"[Registry] {agent.agent_id} 已注册，覆盖")
        self._agents[agent.agent_id] = agent
        self._intent_map[agent.intent_type] = agent.agent_id
        if agent.dependencies:
            self._dependency_graph[agent.agent_id] = agent.dependencies
        logger.info(f"[Registry] 注册: {agent.agent_id} → {agent.intent_type.value}")

    def unregister(self, agent_id: str) -> bool:
        agent = self._agents.pop(agent_id, None)
        if agent:
            self._intent_map.pop(agent.intent_type, None)
            self._dependency_graph.pop(agent_id, None)
            return True
        return False

    # ── 查询 ──

    def get(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def get_by_intent(self, intent: IntentType) -> BaseAgent | None:
        agent_id = self._intent_map.get(intent)
        return self._agents.get(agent_id) if agent_id else None

    def get_all(self) -> dict[str, BaseAgent]:
        return dict(self._agents)

    def get_federated(self) -> list[BaseAgent]:
        return [a for a in self._agents.values()
                if a.processing_mode == ProcessingMode.FEDERATED]

    def get_collaborative(self) -> list[BaseAgent]:
        return [a for a in self._agents.values()
                if a.processing_mode == ProcessingMode.COLLABORATIVE]

    # ── 依赖管理 ──

    def get_dependencies(self, agent_id: str) -> list[str]:
        return self._dependency_graph.get(agent_id, [])

    def can_execute(self, agent_id: str, completed: list[str]) -> bool:
        deps = self.get_dependencies(agent_id)
        return all(d in completed for d in deps)

    def get_executable(self, pending: list[str], completed: list[str]) -> list[str]:
        return [aid for aid in pending if self.can_execute(aid, completed)]

    # ── 意图映射 ──

    def get_intent_map(self) -> dict[str, str]:
        return {intent.value: aid for intent, aid in self._intent_map.items()}

    def reset(self):
        self._agents.clear()
        self._intent_map.clear()
        self._dependency_graph.clear()
        logger.info("[Registry] 已重置")


# 全局单例
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
