"""裁决 Agent (Federated) —— 辩论最终判定。

综合正方论点(pro_argument)和反方质疑(con_argument)，做最终裁决：
- Confirmed: 支撑JD≥10条, 技能≥3项, 反方无high级质疑
- Pending: 支撑JD 5-9条
- Rejected: 支撑JD<5条 或 ≥2个high级质疑
"""

from __future__ import annotations

from app.agents.base import FederatedAgent
from app.agents.agent_state import IntentType, MultiAgentState

JUDGE_SYSTEM = """你是一个公正的岗位审核裁判。
判定标准：
- Confirmed: 支撑JD≥10条, 技能≥3项可区分, 反方无high级质疑
- Pending: JD 5-9条, 或存在medium级质疑需补充证据
- Rejected: JD<5条, 或≥2个high级质疑
输出 JSON: {"verdict": "Confirmed|Pending|Rejected", "reason": "...", "next_steps": [...]}"""


class JudgeAgent(FederatedAgent):
    def __init__(self, llm_client=None):
        super().__init__("judge", "辩论裁决", "综合正反双方论点做最终判定")
        self.llm_client = llm_client

    @property
    def intent_type(self) -> IntentType:
        return IntentType.DISCOVER_ROLE

    async def process(self, state: MultiAgentState) -> dict:
        pro = state.get_payload("pro_argument", {})
        con = state.get_payload("con_argument", {})
        topic = state.get_payload("debate_topic", {})

        term = pro.get("term", topic.get("term", ""))
        evidence_count = pro.get("evidence_count", 0)
        skill_count = pro.get("skill_count", 0)
        concerns = con.get("concerns", [])

        high_count = sum(1 for c in concerns if c.get("level") == "high")

        # 规则判定
        if high_count >= 2:
            verdict, reason = "Rejected", f"{high_count}个高优先级问题，证据不足"
        elif evidence_count < 5:
            verdict, reason = "Rejected", f"仅{evidence_count}条JD，不满足最低要求"
        elif evidence_count < 10 or high_count >= 1:
            verdict, reason = "Pending", f"JD {evidence_count}条，建议补充{(10-evidence_count)}条以上"
        elif evidence_count >= 10 and high_count == 0 and skill_count >= 3:
            verdict, reason = "Confirmed", f"{evidence_count}条JD+{skill_count}项技能，通过验证"
        else:
            verdict, reason = "Pending", "需进一步审查"

        # LLM 增强
        if self.llm_client and evidence_count > 0:
            try:
                prompt = (
                    f'候选岗位: "{term}"\n'
                    f'正方: JD {evidence_count}条, 技能 {skill_count}项\n'
                    f'规则预判: {verdict} - {reason}\n请做最终裁决。'
                )
                result = self.llm_extract_json(prompt, system=JUDGE_SYSTEM)
                if result and isinstance(result, dict):
                    verdict = result.get("verdict", verdict)
                    reason = result.get("reason", reason)
            except Exception:
                pass

        return self.ok(data={
            "term": term, "verdict": verdict, "reason": reason,
            "evidence_count": evidence_count, "skill_count": skill_count,
            "high_concerns": high_count,
            "next_steps": (
                ["列入候选库", "持续收集JD"] if verdict in ("Confirmed", "Pending")
                else ["标记不成立", "3个月后重评"]
            ),
        })
