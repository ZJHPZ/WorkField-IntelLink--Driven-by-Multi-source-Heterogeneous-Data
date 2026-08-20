"""L4 快照机制 —— 图谱版本管理与时序演化。

设计方案 §5.3：
- 快照：每批数据生成带时间戳的 snapshot
- diff：两快照对比自动产出 新增/删除/修改 三态
- 生命周期：关系带 valid_from/valid_to
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SkillVersion:
    """技能版本（带生命周期）。"""
    name: str
    confidence: float = 0.0
    status: str = "candidate"
    df: int = 0
    valid_from: str = ""

    def is_valid_at(self, timestamp: str) -> bool:
        return not self.valid_from or timestamp >= self.valid_from


@dataclass
class Snapshot:
    """图谱快照。"""
    snapshot_id: str
    timestamp: str
    description: str = ""
    skills: dict[str, SkillVersion] = field(default_factory=dict)
    relations: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "description": self.description,
            "skills": {name: {"name": sv.name, "confidence": sv.confidence,
                              "status": sv.status, "df": sv.df}
                       for name, sv in self.skills.items()},
            "relations": self.relations,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        snap = cls(
            snapshot_id=data["snapshot_id"],
            timestamp=data["timestamp"],
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )
        for name, sv in data.get("skills", {}).items():
            snap.skills[name] = SkillVersion(**sv)
        snap.relations = data.get("relations", [])
        return snap


@dataclass
class SnapshotDiff:
    """快照差异（增/删/改三态）。"""
    snapshot_old: str
    snapshot_new: str
    timestamp_old: str = ""
    timestamp_new: str = ""
    added_skills: list[str] = field(default_factory=list)
    removed_skills: list[str] = field(default_factory=list)
    modified_skills: list[dict] = field(default_factory=list)
    added_relations: list[dict] = field(default_factory=list)
    removed_relations: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        return (f"新增 {len(self.added_skills)} 项技能，"
                f"删除 {len(self.removed_skills)} 项，"
                f"修改 {len(self.modified_skills)} 项")


class SnapshotManager:
    """快照管理器。"""

    def __init__(self, storage_dir: str | None = None):
        self.storage_dir = storage_dir
        self.snapshots: dict[str, Snapshot] = {}
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)

    def create_snapshot(
        self, graph_data: dict, timestamp: str | None = None,
        description: str = "", snapshot_id: str | None = None,
    ) -> Snapshot:
        """从图谱数据创建快照。"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        if snapshot_id is None:
            snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        snap = Snapshot(snapshot_id=snapshot_id, timestamp=timestamp,
                        description=description)

        for node in graph_data.get("nodes", []):
            nd = node.get("data", {})
            if nd.get("nodeType") == "Skill":
                name = nd.get("label", "")
                snap.skills[name] = SkillVersion(
                    name=name,
                    confidence=nd.get("confidence", 0),
                    status=nd.get("status", "candidate"),
                    df=nd.get("df", 0),
                    valid_from=timestamp,
                )

        snap.relations = graph_data.get("edges", [])
        snap.metadata = {"skill_count": len(snap.skills),
                         "relation_count": len(snap.relations)}

        self.snapshots[snapshot_id] = snap
        if self.storage_dir:
            path = os.path.join(self.storage_dir, f"{snapshot_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(snap.to_dict(), f, ensure_ascii=False, indent=2)

        return snap

    def diff_snapshots(self, old: Snapshot, new: Snapshot) -> SnapshotDiff:
        """对比两个快照的差异。"""
        diff = SnapshotDiff(
            snapshot_old=old.snapshot_id, snapshot_new=new.snapshot_id,
            timestamp_old=old.timestamp, timestamp_new=new.timestamp,
        )
        old_skills = set(old.skills.keys())
        new_skills = set(new.skills.keys())
        diff.added_skills = list(new_skills - old_skills)
        diff.removed_skills = list(old_skills - new_skills)

        for name in old_skills & new_skills:
            old_conf = old.skills[name].confidence
            new_conf = new.skills[name].confidence
            if abs(old_conf - new_conf) > 0.1:
                diff.modified_skills.append({
                    "name": name,
                    "old_confidence": old_conf,
                    "new_confidence": new_conf,
                })

        old_rels = {(r.get("source",""), r.get("target",""), r.get("data",{}).get("rel",""))
                     for r in old.relations}
        new_rels = {(r.get("source",""), r.get("target",""), r.get("data",{}).get("rel",""))
                     for r in new.relations}
        diff.added_relations = [{"source": s, "target": t, "rel_type": r}
                                for s, t, r in (new_rels - old_rels)]
        diff.removed_relations = [{"source": s, "target": t, "rel_type": r}
                                  for s, t, r in (old_rels - new_rels)]
        return diff

    def list_snapshots(self) -> list[dict]:
        return [{"snapshot_id": s.snapshot_id, "timestamp": s.timestamp,
                 "description": s.description,
                 "skill_count": len(s.skills)}
                for s in sorted(self.snapshots.values(), key=lambda x: x.timestamp)]

    def load_snapshot(self, snapshot_id: str) -> Snapshot | None:
        if snapshot_id in self.snapshots:
            return self.snapshots[snapshot_id]
        if self.storage_dir:
            path = os.path.join(self.storage_dir, f"{snapshot_id}.json")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    snap = Snapshot.from_dict(json.load(f))
                self.snapshots[snapshot_id] = snap
                return snap
        return None
