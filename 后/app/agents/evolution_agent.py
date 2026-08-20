"""演化分析 Agent (Federated) —— 对比岗位历史快照 → 增/删/改。"""

from __future__ import annotations

from datetime import datetime

from app.agents.base import FederatedAgent
from app.agents.agent_state import IntentType, MultiAgentState


class EvolutionAgent(FederatedAgent):
    def __init__(self):
        super().__init__("evolver", "演化分析", "对比岗位历史快照→增/删/改三态标注")

    @property
    def intent_type(self) -> IntentType:
        return IntentType.EVOLUTION_ANALYSIS

    async def process(self, state: MultiAgentState) -> dict:
        snapshots = state.get_payload("snapshots", [])
        if len(snapshots) < 2:
            return self.ok(data={
                "note": "至少需要2个快照才能生成演化分析",
                "snapshot_count": len(snapshots),
            })

        old = snapshots[-2]
        new = snapshots[-1]
        old_skills = set(old.get("skills", {}).keys())
        new_skills = set(new.get("skills", {}).keys())

        added = list(new_skills - old_skills)
        removed = list(old_skills - new_skills)
        modified = []
        for name in old_skills & new_skills:
            old_conf = old.get("skills", {}).get(name, {}).get("confidence", 0)
            new_conf = new.get("skills", {}).get(name, {}).get("confidence", 0)
            if abs(old_conf - new_conf) > 0.1:
                modified.append({
                    "name": name,
                    "old_confidence": old_conf,
                    "new_confidence": new_conf,
                })

        return self.ok(data={
            "snapshot_old": old.get("snapshot_id", ""),
            "snapshot_new": new.get("snapshot_id", ""),
            "added_skills": added,
            "removed_skills": removed,
            "modified_skills": modified,
            "summary": f"新增{len(added)}/删除{len(removed)}/修改{len(modified)}",
            "timestamp": datetime.now().isoformat(),
        })
