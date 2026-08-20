"""意图路由器 —— 静态映射，非 NLP。

与参考系统不同：我们的 "意图" 由 API 端点决定，不需要关键词匹配。
Router 退化为一个静态映射表 + 依赖链查询。
"""

from __future__ import annotations

import logging

from app.agents.agent_state import IntentType

logger = logging.getLogger(__name__)


# ── 意图 → Agent ID 静态映射 ──

INTENT_TO_AGENT: dict[IntentType, str] = {
    # Pipeline
    IntentType.EXTRACT_SKILLS: "extractor",
    IntentType.VERIFY_SKILLS: "verifier",
    IntentType.NORMALIZE_SKILLS: "normalizer",
    IntentType.BUILD_GRAPH: "graph_builder",

    # To B
    IntentType.DIAGNOSE_JD: "jd_diagnoser",
    IntentType.DISCOVER_ROLE: "discoverer",
    IntentType.TEAM_GAP: "team_analyzer",
    IntentType.TALENT_FORECAST: "forecaster",

    # To C
    IntentType.PARSE_RESUME: "resume_parser",
    IntentType.MATCH_POSITION: "matcher",
    IntentType.CAREER_GAP: "suggester",
    IntentType.LEARNING_PATH: "path_planner",
    IntentType.SKILL_FRESHNESS: "freshness_checker",
    IntentType.SWITCH_FEASIBILITY: "switch_analyzer",

    # 通用
    IntentType.EVOLUTION_ANALYSIS: "evolver",
    IntentType.PIPELINE: "pipeline_runner",
    IntentType.UNKNOWN: "extractor",
}

# ── 依赖链：协作式 Agent 需要的前置 Agent ──

COLLABORATION_CHAINS: dict[str, list[str]] = {
    "matcher": ["extractor", "normalizer"],         # 匹配依赖抽取+归一化
    "discoverer": ["normalizer"],                    # 新岗发现依赖归一化后的技能
    "suggester": ["matcher"],                        # 职业建议依赖匹配结果
    "path_planner": ["matcher", "suggester"],        # 学习路径依赖匹配+建议
    "switch_analyzer": ["matcher"],                  # 转行分析依赖匹配
    "team_analyzer": ["matcher"],                    # 团队盘点依赖匹配
    "forecaster": ["normalizer"],                    # 人才预测依赖归一化数据
}


class IntentRouter:
    """意图路由器 —— 静态映射版。"""

    def __init__(self):
        self._intent_map: dict[IntentType, str] = dict(INTENT_TO_AGENT)
        self._chains: dict[str, list[str]] = dict(COLLABORATION_CHAINS)

    def route(self, intent: IntentType) -> str:
        """意图 → Agent ID。"""
        return self._intent_map.get(intent, "extractor")

    def get_chain(self, agent_id: str) -> list[str]:
        """获取 Agent 的前置依赖链。"""
        return self._chains.get(agent_id, [])

    def get_agent_mapping(self) -> dict[str, str]:
        return {intent.value: aid for intent, aid in self._intent_map.items()}

    def add_mapping(self, intent: IntentType, agent_id: str):
        self._intent_map[intent] = agent_id


# 全局单例
_router: IntentRouter | None = None


def get_intent_router() -> IntentRouter:
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router
