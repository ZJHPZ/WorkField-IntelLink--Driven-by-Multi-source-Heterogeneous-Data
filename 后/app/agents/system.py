"""MultiAgentSystem —— 多智能体系统主入口。

初始化所有 Agent → 注册到 Registry → 提供统一的 process() 接口。
业务代码通过此入口调用 Agent 系统，不直接依赖具体 Agent。
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.agent_state import IntentType, MultiAgentState
from app.agents.registry import get_registry
from app.agents.router import get_intent_router
from app.agents.executor import get_executor, AgentExecutor
from app.agents.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """多智能体系统主入口。

    用法:
        system = MultiAgentSystem()
        system.initialize(client=spark_client)

        # 单次执行
        result = await system.process(IntentType.MATCH_POSITION, {
            "user_skills": ["Python", "SQL"],
            "position_skills": [{"name": "Python", "required_type": "必备"}, ...],
        })

        # Pipeline 批量执行
        results = await system.process_pipeline(items, [
            "extractor", "verifier", "normalizer"
        ])
    """

    def __init__(self):
        self.registry = get_registry()
        self.router = get_intent_router()
        self.executor: AgentExecutor = get_executor()
        self.context = get_shared_context()
        self._initialized = False

    def initialize(self, llm_client: Any = None) -> "MultiAgentSystem":
        """初始化所有 Agent 并注册。"""
        if self._initialized:
            return self

        from app.agents.extract_agent import ExtractAgent
        from app.agents.verify_agent import VerifyAgent
        from app.agents.normalize_agent import NormalizeAgent
        from app.agents.match_agent import MatchAgent
        from app.agents.discovery_agent import DiscoveryAgent
        from app.agents.judge_agent import JudgeAgent
        from app.agents.evolution_agent import EvolutionAgent
        from app.agents.suggest_agent import SuggestAgent
        from app.agents.orchestrator import get_orchestrator

        agents = [
            ExtractAgent(llm_client=llm_client),
            VerifyAgent(),
            NormalizeAgent(),
            MatchAgent(llm_client=llm_client),
            DiscoveryAgent(llm_client=llm_client),
            JudgeAgent(llm_client=llm_client),
            EvolutionAgent(),
            SuggestAgent(llm_client=llm_client),
            get_orchestrator(),
        ]

        for agent in agents:
            self.registry.register(agent)

        self._initialized = True
        logger.info(f"[MultiAgentSystem] 初始化完成，已注册 {len(agents)} 个 Agent")
        return self

    async def process(self, intent: IntentType, payload: dict,
                      user_id: str = "default") -> dict[str, Any]:
        """处理单个意图。

        Args:
            intent: 意图类型
            payload: 请求数据
            user_id: 用户标识

        Returns:
            执行结果
        """
        if not self._initialized:
            return {"success": False, "error": "Agent 系统未初始化，请先调用 initialize()"}
        return await self.executor.execute(intent, payload, user_id)

    async def process_pipeline(self, items: list[dict],
                               agent_ids: list[str] | None = None) -> list[dict]:
        """批量 pipeline 执行。

        Args:
            items: 待处理数据项
            agent_ids: Agent ID 列表，None 则用默认链

        Returns:
            处理后的 items
        """
        if not self._initialized:
            return items
        if agent_ids is None:
            agent_ids = ["extractor", "verifier", "normalizer"]
        return await self.executor.execute_pipeline(
            IntentType.PIPELINE, items, agent_ids,
        )

    def is_initialized(self) -> bool:
        return self._initialized


# 全局单例
_system: MultiAgentSystem | None = None


def get_system() -> MultiAgentSystem:
    global _system
    if _system is None:
        _system = MultiAgentSystem()
    return _system
