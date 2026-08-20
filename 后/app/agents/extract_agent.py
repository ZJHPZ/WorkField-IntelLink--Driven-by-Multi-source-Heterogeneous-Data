"""抽取 Agent (Federated) —— 从清洗后的 JD 抽取技能。"""

from __future__ import annotations

from app.agents.base import FederatedAgent
from app.agents.agent_state import IntentType, MultiAgentState
from app.pipeline.l3_extract import extract as l3_extract


class ExtractAgent(FederatedAgent):
    def __init__(self, llm_client=None):
        super().__init__("extractor", "技能抽取", "从JD抽取技能（LLM优先+规则兜底）")
        self.llm_client = llm_client

    @property
    def intent_type(self) -> IntentType:
        return IntentType.EXTRACT_SKILLS

    async def process(self, state: MultiAgentState) -> dict:
        cleaned = state.get_payload("cleaned_jd")
        if cleaned:
            skills = l3_extract(cleaned, self.llm_client)
            return self.ok(data={"skills": skills, "count": len(skills)})

        # 批量模式
        cleaned_jds = state.get_payload("cleaned_jds", [])
        extracted = []
        for item in cleaned_jds:
            skills = l3_extract(item["cleaned"], self.llm_client)
            extracted.append((item["jd_id"], item.get("tech_stack", ""), skills))

        return self.ok(data={
            "extracted_by_jd": extracted,
            "total_jds": len(extracted),
            "spark_hits": sum(1 for _, _, skills in extracted
                            for s in skills if s.source == "spark"),
            "rule_hits": sum(1 for _, _, skills in extracted
                           for s in skills if s.source == "rule"),
        })
