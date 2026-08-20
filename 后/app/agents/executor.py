"""AgentExecutor —— 联邦式 + 协作式执行引擎。

联邦式：独立 Agent 直接执行
协作式：按依赖链顺序执行，上游结果通过 state 传递
Pipeline：批量数据 → Agent 链 (MapReduce 模式)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from app.agents.base import BaseAgent
from app.agents.agent_state import (
    IntentType, TaskStatus, MultiAgentState, ProcessingMode,
)
from app.agents.router import get_intent_router
from app.agents.registry import get_registry
from app.agents.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Agent 执行引擎（单例）。"""

    _instance: "AgentExecutor | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.registry = get_registry()
        self.router = get_intent_router()
        self.context = get_shared_context()
        logger.info("[Executor] 初始化完成")

    # ── 公共入口 ──

    async def execute(self, intent: IntentType, payload: dict,
                      user_id: str = "default") -> dict[str, Any]:
        """执行单个意图。

        Args:
            intent: 意图类型
            payload: 请求数据
            user_id: 用户标识

        Returns:
            执行结果
        """
        agent_id = self.router.route(intent)
        agent = self.registry.get(agent_id)
        if not agent:
            return {"success": False, "error": f"未找到处理 Agent: {agent_id}"}

        state = MultiAgentState(
            user_id=user_id,
            current_intent=intent,
            payload=payload,
            processing_mode=agent.processing_mode.value,
        )

        if agent.processing_mode == ProcessingMode.COLLABORATIVE:
            return await self._execute_collaborative(state, agent_id)
        return await self._execute_federated(state, agent_id)

    async def execute_pipeline(self, intent: IntentType, items: list[dict],
                               agent_ids: list[str]) -> list[dict]:
        """批量 pipeline 执行（MapReduce 模式）。

        每个 Agent 处理完所有 items → 结果传给下一个 Agent。

        Args:
            intent: 顶层意图
            items: 待处理的数据项列表
            agent_ids: 按顺序执行的 Agent ID 列表

        Returns:
            处理后的 items 列表
        """
        results = items
        for aid in agent_ids:
            agent = self.registry.get(aid)
            if not agent:
                logger.warning(f"[Executor] Agent {aid} 未注册，跳过")
                continue
            batch_state = MultiAgentState(
                current_intent=intent,
                payload={"items": results, "agent_chain": agent_ids},
                processing_mode="pipeline",
            )
            self.log(f"Pipeline → {aid} ({len(results)} items)")
            result = await agent.process(batch_state)
            if isinstance(result, dict) and "items" in result:
                results = result["items"]
            else:
                # Agent 返回的不是批量结果，存为中间产物
                batch_state.set_agent_result(aid, result)

        return results

    # ── 联邦式 ──

    async def _execute_federated(self, state: MultiAgentState,
                                 agent_id: str) -> dict[str, Any]:
        """联邦式执行（独立 Agent）。"""
        agent = self.registry.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent {agent_id} 未注册"}

        self.log(f"联邦式 → {agent_id}")
        try:
            result = await agent.process(state)
            state.set_agent_result(agent_id, result)
            return {"success": True, "agent_id": agent_id, "result": result}
        except Exception as e:
            self.log(f"失败: {e}")
            return {"success": False, "agent_id": agent_id, "error": str(e)}

    # ── 协作式 ──

    async def _execute_collaborative(self, state: MultiAgentState,
                                     agent_id: str) -> dict[str, Any]:
        """协作式执行（按依赖链顺序）。

        宽松模式：只检查在当前链内的依赖，链外的上游行为视为数据已由 payload 提供。
        """
        chain = self.router.get_chain(agent_id)
        full_chain = chain + [agent_id]
        completed = set()

        for aid in full_chain:
            agent = self.registry.get(aid)
            if not agent:
                continue

            # 只检查在当前链内的依赖
            deps = [d for d in self.registry.get_dependencies(aid) if d in full_chain]
            if not all(d in completed for d in deps):
                self.log(f"等待依赖: {[d for d in deps if d not in completed]}")
                continue

            self.log(f"协作式 → {aid}")
            try:
                result = await agent.process(state)
                state.set_agent_result(aid, result)
                completed.add(aid)
            except Exception as e:
                return {"success": False, "agent_id": aid, "error": str(e)}

        final = state.get_agent_result(agent_id)
        return {"success": True, "agent_id": agent_id, "result": final,
                "chain": full_chain, "completed": list(completed)}

    def log(self, msg: str):
        logger.info(f"[Executor] {msg}")


# 全局单例
_executor: AgentExecutor | None = None


def get_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
    return _executor
