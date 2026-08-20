"""Agent 基类 —— FederatedAgent / CollaborativeAgent。

与旧系统关键区别：
- 每个 Agent 声明 intent_type（不需要 Orchestrator 手动编排）
- 联邦式 Agent 独立执行，协作式 Agent 声明依赖
- process(state) → dict 是统一入口（替代旧的 execute(context)）
- 工具列表和 LLM 客户端内置于 Agent
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.agents.agent_state import IntentType, ProcessingMode, MultiAgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 抽象基类。

    每个 Agent 必须声明：
    - agent_id: 唯一标识
    - intent_type: 处理的意图类型
    - processing_mode: 联邦式(FEDERATED) 或 协作式(COLLABORATIVE)
    """

    # 类级别注册表
    _registry: dict[str, type["BaseAgent"]] = {}

    def __init__(
        self,
        agent_id: str,
        name: str = "",
        description: str = "",
        processing_mode: ProcessingMode = ProcessingMode.FEDERATED,
        dependencies: list[str] | None = None,
    ):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.description = description
        self.processing_mode = processing_mode
        self.dependencies = dependencies or []

        # 工具列表
        self.tools: list[Any] = []

        # LLM 客户端（可选）
        self.llm_client: Any = None

        # 创建时间
        self.created_at = datetime.now().isoformat()

        # 自动注册
        self._register()

    def _register(self):
        if self.agent_id in self._registry:
            logger.warning(f"[{self.agent_id}] 已注册，覆盖")
        self._registry[self.agent_id] = self.__class__

    @classmethod
    def get_registry(cls) -> dict[str, type["BaseAgent"]]:
        return dict(cls._registry)

    # ── 子类必须实现 ──

    @property
    @abstractmethod
    def intent_type(self) -> IntentType:
        """返回该 Agent 处理的意图类型。"""
        ...

    @abstractmethod
    async def process(self, state: MultiAgentState) -> dict[str, Any]:
        """处理任务的核心方法。

        Args:
            state: 当前系统共享状态

        Returns:
            处理结果 dict，至少包含 {"success": bool, ...}
        """
        ...

    # ── 工具管理 ──

    def add_tool(self, tool: Any):
        self.tools.append(tool)

    def get_tools(self) -> list[Any]:
        return self.tools

    # ── 结果辅助 ──

    def ok(self, data: Any = None, **kwargs) -> dict[str, Any]:
        return {"success": True, "agent_id": self.agent_id, "data": data, **kwargs}

    def fail(self, error: str, **kwargs) -> dict[str, Any]:
        logger.error(f"[{self.agent_id}] {error}")
        return {"success": False, "agent_id": self.agent_id, "error": error, **kwargs}

    # ── LLM 推理 ──

    def llm_reason(self, prompt: str, system: str = "") -> str:
        if not self.llm_client:
            raise RuntimeError(f"[{self.agent_id}] 未配置 LLM 客户端")
        try:
            return self.llm_client.chat(prompt, system=system)
        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM 推理失败: {e}")
            raise

    def llm_extract_json(self, prompt: str, system: str = "") -> dict | list | None:
        if not self.llm_client:
            return None
        try:
            return self.llm_client.extract_json(prompt, system=system)
        except Exception as e:
            logger.warning(f"[{self.agent_id}] JSON 抽取失败: {e}")
            return None

    def log(self, msg: str):
        logger.info(f"[{self.agent_id}] {msg}")

    def __repr__(self):
        return f"<{self.__class__.__name__}(id='{self.agent_id}')>"


class FederatedAgent(BaseAgent):
    """联邦式 Agent —— 独立并行执行，不依赖其他 Agent。

    用于：抽取、校验、归一化、演化分析、JD诊断。
    """

    def __init__(self, agent_id: str, name: str = "", description: str = ""):
        super().__init__(
            agent_id=agent_id, name=name, description=description,
            processing_mode=ProcessingMode.FEDERATED,
        )


class CollaborativeAgent(BaseAgent):
    """协作式 Agent —— 依赖其他 Agent 的结果，顺序执行。

    用于：人岗匹配（依赖抽取+归一化）、新岗发现（依赖趋势分析）、职业建议（依赖匹配）。
    """

    def __init__(self, agent_id: str, name: str = "", description: str = "",
                 dependencies: list[str] | None = None):
        super().__init__(
            agent_id=agent_id, name=name, description=description,
            processing_mode=ProcessingMode.COLLABORATIVE,
            dependencies=dependencies or [],
        )
