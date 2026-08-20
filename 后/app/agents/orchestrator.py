"""OrchestratorAgent —— 意图识别 → 任务分解 → 调度 → 结果整合。

Orchestrator 本身也是一个 Agent，处理 PIPELINE / DISCOVER_ROLE 等复杂意图。
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from app.agents.base import BaseAgent, CollaborativeAgent
from app.agents.agent_state import (
    IntentType, TaskStatus, TaskInfo, MultiAgentState, ProcessingMode,
)
from app.agents.router import get_intent_router
from app.agents.registry import get_registry

logger = logging.getLogger(__name__)


class OrchestratorAgent(CollaborativeAgent):
    """调度 Agent —— 负责复杂任务分解和调度。

    处理意图：PIPELINE、DISCOVER_ROLE、MATCH_POSITION
    """

    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            name="调度中心",
            description="意图识别、任务分解、调度协调、结果整合",
        )
        self.router = get_intent_router()
        self.registry = get_registry()

    @property
    def intent_type(self) -> IntentType:
        return IntentType.PIPELINE

    async def process(self, state: MultiAgentState) -> dict[str, Any]:
        """处理复杂任务。"""
        intent = state.current_intent
        payload = state.payload

        self.log(f"处理意图: {intent.value}")

        # Step 1: 任务分解
        tasks = self._decompose(intent, payload)
        state.tasks = {t.task_id: t for t in tasks}
        self.log(f"分解为 {len(tasks)} 个任务")

        # Step 2: 执行任务（支持联邦式并行 + 协作式顺序）
        results = await self._execute_all(tasks, state)

        # Step 3: 整合结果
        integrated = self._integrate(intent, results)

        return self.ok(data=integrated)

    def _decompose(self, intent: IntentType, payload: dict) -> list[TaskInfo]:
        """根据意图分解为子任务链。"""
        agent_id = self.router.route(intent)

        # 单 Agent 任务
        chain_ids = self.router.get_chain(agent_id)
        if not chain_ids:
            return [TaskInfo(
                task_id=f"task-{uuid4().hex[:8]}",
                intent_type=intent,
                description=intent.value,
                status=TaskStatus.PENDING,
                assigned_agent=agent_id,
            )]

        # 多 Agent 协作链
        tasks = []
        for i, aid in enumerate(chain_ids):
            tasks.append(TaskInfo(
                task_id=f"task-{uuid4().hex[:8]}",
                intent_type=intent if i == len(chain_ids) - 1 else IntentType.UNKNOWN,
                description=f"chain step {i+1}: {aid}",
                status=TaskStatus.PENDING,
                assigned_agent=aid,
            ))
        return tasks

    async def _execute_all(self, tasks: list[TaskInfo],
                           state: MultiAgentState) -> list[dict]:
        """按依赖顺序执行所有任务。"""
        results = []
        completed = set()

        for task in tasks:
            agent = self.registry.get(task.assigned_agent)
            if not agent:
                results.append({"task_id": task.task_id, "success": False,
                                "error": f"Agent {task.assigned_agent} 未注册"})
                continue

            task.status = TaskStatus.RUNNING
            try:
                result = await agent.process(state)
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now().isoformat()
                completed.add(task.assigned_agent)

                # 将结果写入 state 供后续 Agent 使用
                state.set_agent_result(task.assigned_agent, result)
                results.append({"task_id": task.task_id, "agent": task.assigned_agent,
                                "success": True, "result": result})
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                results.append({"task_id": task.task_id, "agent": task.assigned_agent,
                                "success": False, "error": str(e)})

        return results

    def _integrate(self, intent: IntentType, results: list[dict]) -> dict:
        """整合多 Agent 结果。"""
        if not results:
            return {"message": "无结果"}

        if len(results) == 1:
            r = results[0]
            return r.get("result", {}) if r.get("success") else {"error": r.get("error")}

        # 多结果整合
        return {
            "task_count": len(results),
            "success_count": sum(1 for r in results if r.get("success")),
            "agent_results": {
                r["agent"]: r.get("result", {}) if r.get("success") else {"error": r.get("error")}
                for r in results
            },
        }


# 全局单例
_orchestrator: OrchestratorAgent | None = None


def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
