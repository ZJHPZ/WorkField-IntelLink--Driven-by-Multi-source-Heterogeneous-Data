"""多智能体系统状态定义。

定义 Agent 协作所需的所有状态类型：意图、任务、处理模式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    """意图类型 —— 对应 API 端点，非 NLP 识别。"""
    # Pipeline 批量处理
    EXTRACT_SKILLS = "extract_skills"          # 技能抽取
    VERIFY_SKILLS = "verify_skills"            # 幻觉校验
    NORMALIZE_SKILLS = "normalize_skills"      # 技能归一化
    BUILD_GRAPH = "build_graph"                # 图谱构建

    # To B 企业侧
    DIAGNOSE_JD = "diagnose_jd"               # JD 质量诊断
    DISCOVER_ROLE = "discover_role"            # 新岗位发现
    TEAM_GAP = "team_gap"                     # 团队技能盘点
    TALENT_FORECAST = "talent_forecast"        # 人才需求预测

    # To C 个人侧
    PARSE_RESUME = "parse_resume"              # 简历解析
    MATCH_POSITION = "match_position"          # 人岗匹配
    CAREER_GAP = "career_gap"                 # 差距分析
    LEARNING_PATH = "learning_path"            # 学习路径
    SKILL_FRESHNESS = "skill_freshness"        # 技能保鲜
    SWITCH_FEASIBILITY = "switch_feasibility"  # 转行可行性

    # 通用
    EVOLUTION_ANALYSIS = "evolution_analysis"  # 演化分析
    PIPELINE = "pipeline"                     # 全链路 pipeline
    UNKNOWN = "unknown"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingMode(str, Enum):
    FEDERATED = "federated"          # 独立并行执行
    COLLABORATIVE = "collaborative"  # 依赖其他 Agent 结果


@dataclass
class TaskInfo:
    """单个任务信息。"""
    task_id: str
    intent_type: IntentType
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str = ""
    result: Any = None
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""


@dataclass
class MultiAgentState:
    """多智能体系统共享状态。

    Agent 之间通过此状态传递数据，替代旧系统的裸 dict。
    """
    # 用户/会话标识
    user_id: str = "default"
    session_id: str = ""

    # 当前意图
    current_intent: IntentType = IntentType.UNKNOWN
    intents: list[IntentType] = field(default_factory=list)

    # 任务跟踪
    tasks: dict[str, TaskInfo] = field(default_factory=dict)

    # 数据载荷（各 Agent 的输入/输出）
    payload: dict[str, Any] = field(default_factory=dict)

    # Agent 执行结果
    agent_results: dict[str, Any] = field(default_factory=dict)

    # 共享上下文（跨 Agent 通信）
    shared_context: dict[str, Any] = field(default_factory=dict)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_mode: str = ProcessingMode.FEDERATED.value

    def set_payload(self, key: str, value: Any) -> None:
        self.payload[key] = value

    def get_payload(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)

    def set_agent_result(self, agent_id: str, result: Any) -> None:
        self.agent_results[agent_id] = result

    def get_agent_result(self, agent_id: str) -> Any:
        return self.agent_results.get(agent_id)
