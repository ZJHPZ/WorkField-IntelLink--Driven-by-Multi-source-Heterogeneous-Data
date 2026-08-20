"""人岗匹配 Agent (Collaborative) —— 依赖抽取+归一化结果。

封装 match_service 逻辑，通过 Agent 系统调用。
"""

from __future__ import annotations

from app.agents.base import CollaborativeAgent
from app.agents.agent_state import IntentType, MultiAgentState
from app.services.match_service import match_skills


class MatchAgent(CollaborativeAgent):
    def __init__(self, llm_client=None):
        super().__init__("matcher", "人岗匹配",
                         "技能Jaccard匹配+必备/加分加权→匹配率+差距清单",
                         dependencies=["extractor", "normalizer"])
        self.llm_client = llm_client

    @property
    def intent_type(self) -> IntentType:
        return IntentType.MATCH_POSITION

    async def process(self, state: MultiAgentState) -> dict:
        user_skills = state.get_payload("user_skills", [])
        position_skills = state.get_payload("position_skills", [])
        position_name = state.get_payload("position_name", "")

        if not position_skills:
            # 从 normalizer 结果获取技能统计
            norm_result = state.get_agent_result("normalizer") or {}
            norm_data = norm_result.get("data", {})
            skill_stats = norm_data.get("skill_stats", {})
            if skill_stats:
                position_skills = [
                    {"name": name, "required_type": "必备" if stat.required_count > stat.bonus_count else "加分",
                     "confidence": stat.confidence}
                    for name, stat in skill_stats.items()
                ]

        result = match_skills(user_skills, position_skills,
                              position_name=position_name)

        return self.ok(data={
            "match_rate": result.match_rate,
            "matched_skills": result.matched_skills,
            "partial_skills": result.partial_skills,
            "missing_skills": result.missing_skills,
            "learning_path": result.learning_path,
            "skill_coverage": result.skill_coverage,
        })
