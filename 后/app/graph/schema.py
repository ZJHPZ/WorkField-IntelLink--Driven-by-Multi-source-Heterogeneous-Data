"""图谱 Schema 定义 —— 节点类型 + 关系类型常量。

设计方案 §5.1/5.2：
- 节点：Position / Skill / TechStack / Evidence / Snapshot / Level / Industry
- 关系：REQUIRES / BELONGS_TO / CO_OCCURS / SUPPORTED_BY / IN_STACK / IN_INDUSTRY / EVOLVED_FROM / CONTAINS
"""

from __future__ import annotations

from enum import Enum


class NodeLabel(str, Enum):
    POSITION = "Position"
    SKILL = "Skill"
    TECH_STACK = "TechStack"
    EVIDENCE = "Evidence"
    SNAPSHOT = "Snapshot"
    LEVEL = "Level"
    INDUSTRY = "Industry"


class RelType(str, Enum):
    REQUIRES = "REQUIRES"        # Position → Skill
    BELONGS_TO = "BELONGS_TO"   # Skill → TechStack
    CO_OCCURS = "CO_OCCURS"     # Skill ↔ Skill
    SUPPORTED_BY = "SUPPORTED_BY"  # Skill → Evidence
    IN_STACK = "IN_STACK"       # Position → TechStack
    IN_INDUSTRY = "IN_INDUSTRY"  # Position → Industry
    EVOLVED_FROM = "EVOLVED_FROM"  # Position → Position
    CONTAINS = "CONTAINS"       # Snapshot → Position/Skill


# ID 前缀
ID_PREFIX = {
    "Position": "pos",
    "Skill": "skill",
    "TechStack": "stack",
    "Evidence": "ev",
    "Snapshot": "snap",
    "Level": "lvl",
    "Industry": "ind",
}


def make_id(label: NodeLabel, key: str) -> str:
    """生成统一格式的节点 ID: pos::xxx, skill::xxx 等。"""
    prefix = ID_PREFIX.get(label.value, "node")
    return f"{prefix}::{key}"
