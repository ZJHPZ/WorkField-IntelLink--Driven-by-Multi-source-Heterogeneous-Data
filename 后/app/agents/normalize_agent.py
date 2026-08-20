"""归一化 Agent (Federated) —— 技能对齐到受控词表。"""

from __future__ import annotations

from app.agents.base import FederatedAgent
from app.agents.agent_state import IntentType, MultiAgentState
from app.pipeline.l2_normalize import normalize_and_count


class NormalizeAgent(FederatedAgent):
    def __init__(self):
        super().__init__("normalizer", "技能归一化", "别名→规范名 + 频次统计 + 置信度")

    @property
    def intent_type(self) -> IntentType:
        return IntentType.NORMALIZE_SKILLS

    async def process(self, state: MultiAgentState) -> dict:
        verified_by_jd = state.get_payload("verified_by_jd", [])
        skill_stats = normalize_and_count(verified_by_jd)
        return self.ok(data={
            "skill_stats": skill_stats,
            "unique_skills": len(skill_stats),
        })
