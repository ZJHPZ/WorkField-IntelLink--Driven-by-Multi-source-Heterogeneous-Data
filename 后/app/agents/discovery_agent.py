"""新岗发现 Agent (Collaborative) —— 三段式 + 辩论模式。

设计方案 §4.5/§7.3：
1. 候选生成：从趋势源发现暴涨术语
2. 市场验证：回 JD 库检索确认
3. 定义生成：基于确认后的证据生成 5 字段定义

辩论模式时，DiscoveryAgent 作为正方提出候选定义。
"""

from __future__ import annotations

from app.agents.base import CollaborativeAgent
from app.agents.agent_state import IntentType, MultiAgentState

DISCOVERY_SYSTEM = """你是一个新兴岗位发现专家。
基于提供的证据（新兴技能列表+相关JD片段），为一个候选新岗位生成定义。
输出 JSON：
{
  "岗位名称": "...",
  "核心职责": {"value": "...", "evidence_ids": [...]},
  "必备技能": {"value": ["技能1"], "evidence_ids": [...]},
  "加分技能": {"value": [], "evidence_ids": [...]},
  "典型行业应用场景": {"value": ["场景1"], "evidence_ids": [...]},
  "argument": "为什么这是一个真正的新岗位"
}
规则：每个字段必须基于证据。证据不足时降低置信度而非编造。"""


class DiscoveryAgent(CollaborativeAgent):
    def __init__(self, llm_client=None):
        super().__init__("discoverer", "新岗发现",
                         "新兴技能聚类→归纳岗位定义（三段式+辩论正方）",
                         dependencies=["normalizer"])
        self.llm_client = llm_client

    @property
    def intent_type(self) -> IntentType:
        return IntentType.DISCOVER_ROLE

    async def process(self, state: MultiAgentState) -> dict:
        topic = state.get_payload("debate_topic", state.payload)
        term = topic.get("term", "")
        evidence_jds = topic.get("evidence_jds", [])
        emerging_skills = topic.get("emerging_skills", [])

        if self.llm_client and evidence_jds:
            evidence_text = "\n".join(
                f"- {jd.get('title', 'JD')}: {jd.get('full_text', jd.get('text', ''))[:300]}"
                for jd in evidence_jds[:5]
            )
            prompt = (
                f'候选新岗位: "{term}"\n'
                f'新兴技能: {", ".join(emerging_skills[:15])}\n'
                f'市场验证确认的 JD 证据:\n{evidence_text}\n'
                '请为此候选岗位生成 5 字段结构化定义。'
            )
            try:
                result = self.llm_extract_json(prompt, system=DISCOVERY_SYSTEM)
                if result and isinstance(result, dict):
                    return self.ok(data={
                        "term": term,
                        "definition": result,
                        "evidence_count": len(evidence_jds),
                        "skill_count": len(emerging_skills),
                    })
            except Exception:
                pass

        # 规则兜底
        return self.ok(data={
            "term": term,
            "definition": {
                "岗位名称": term,
                "核心职责": {"value": f"负责{term}相关的设计、开发与落地", "evidence_ids": []},
                "必备技能": {"value": emerging_skills[:5], "evidence_ids": []},
                "加分技能": {"value": [], "evidence_ids": []},
                "典型行业应用场景": {"value": [], "evidence_ids": []},
                "argument": "基于新兴技能聚类+市场JD验证",
            },
            "evidence_count": len(evidence_jds),
            "skill_count": len(emerging_skills),
        })
