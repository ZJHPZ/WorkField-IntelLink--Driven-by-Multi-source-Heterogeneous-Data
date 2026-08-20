"""职业建议 Agent (Collaborative) —— 差距分析 + 学习路径。

依赖 Matcher 的结果（match_rate, missing_skills）。
"""

from __future__ import annotations

from app.agents.base import CollaborativeAgent
from app.agents.agent_state import IntentType, MultiAgentState

SUGGEST_SYSTEM = """你是职业规划专家。基于用户技能与目标岗位的差距，生成学习路径。
输出 JSON: {"match_rate":0.0-1.0,"matched_skills":[],"missing_skills":[{"name":"","priority":"高|中|低"}],"learning_path":[{"step":1,"skill":"","duration":"X-Y个月","resources":[]}]}"""


class SuggestAgent(CollaborativeAgent):
    def __init__(self, llm_client=None):
        super().__init__("suggester", "职业建议",
                         "差距分析→学习路径推荐",
                         dependencies=["matcher"])
        self.llm_client = llm_client

    @property
    def intent_type(self) -> IntentType:
        return IntentType.CAREER_GAP

    async def process(self, state: MultiAgentState) -> dict:
        # 从 payload 或 matcher 结果获取
        user_skills = state.get_payload("user_skills", [])
        position_skills = state.get_payload("position_skills", [])
        match_result = state.get_agent_result("matcher") or {}

        missing = (match_result.get("data", {}).get("missing_skills", [])
                   if isinstance(match_result, dict) else [])

        # 如果没有 matcher 结果，自己计算
        if not missing and user_skills and position_skills:
            from app.services.match_service import match_skills
            detail = match_skills(user_skills, position_skills)
            missing = detail.missing_skills

        # 生成学习路径
        learning_path = []
        if self.llm_client and missing:
            try:
                prompt = (f'缺失技能: {[m["name"] if isinstance(m,dict) else m for m in missing[:10]]}\n请生成学习路径。')
                result = self.llm_extract_json(prompt, system=SUGGEST_SYSTEM)
                if isinstance(result, dict) and "learning_path" in result:
                    learning_path = result["learning_path"]
            except Exception:
                pass

        if not learning_path:
            for i, m in enumerate(missing[:5], 1):
                name = m.get("name", m.get("canonical", str(m)))
                priority = m.get("priority", "中") if isinstance(m, dict) else "中"
                duration = {"高": "3-4个月", "中": "2-3个月", "低": "1-2个月"}.get(priority, "2-3个月")
                learning_path.append({
                    "step": i, "skill": name,
                    "duration": duration,
                    "resources": [f"搜索 '{name} 教程'"],
                })

        return self.ok(data={
            "missing_skills": missing,
            "learning_path": learning_path,
            "total_missing": len(missing),
        })
