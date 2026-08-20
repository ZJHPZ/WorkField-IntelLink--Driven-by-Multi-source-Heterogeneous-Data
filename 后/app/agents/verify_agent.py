"""幻觉校验 Agent (Federated) —— 三道闸核验。"""

from __future__ import annotations

from app.agents.base import FederatedAgent
from app.agents.agent_state import IntentType, MultiAgentState
from app.pipeline.l3_verify import verify


class VerifyAgent(FederatedAgent):
    def __init__(self):
        super().__init__("verifier", "幻觉校验", "三道闸核验：强制引证→证据核验→内容核验")

    @property
    def intent_type(self) -> IntentType:
        return IntentType.VERIFY_SKILLS

    async def process(self, state: MultiAgentState) -> dict:
        extracted_by_jd = state.get_payload("extracted_by_jd", [])
        jd_fulltext_map = state.get_payload("jd_fulltext_map", {})

        verified, gate_total, gate_rejected = [], 0, 0
        reject_log = []

        for jd_id, tech_stack, skills in extracted_by_jd:
            gate = verify(jd_id, jd_fulltext_map.get(jd_id, ""), skills)
            gate_total += gate.total
            gate_rejected += len(gate.rejected)
            for v in gate.rejected:
                reject_log.append({"jd_id": jd_id, "skill": v.skill.name,
                                   "reason": v.reason})
            verified.append((jd_id, tech_stack, gate.passed))

        rate = gate_rejected / gate_total if gate_total else 0.0
        return self.ok(data={
            "verified_by_jd": verified,
            "gate_total": gate_total,
            "gate_rejected": gate_rejected,
            "intercept_rate": round(rate, 4),
            "reject_log": reject_log,
        })
