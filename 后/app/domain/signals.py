"""多源信号模型 —— 适配层统一数据格式。

设计方案 §3.4 + §3.5：
- SkillSignal：从单份文档中抽取的原始技能信号
- FusedSkill：多源融合后的可信技能
- SourceDocument：适配器统一输出格式
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain import SourceType


@dataclass
class TextSegment:
    """一段带语义标签的文本片段。"""
    section_type: str
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SourceDocument:
    """适配器统一输出 —— 一份来自任意数据源的文档。"""
    doc_id: str
    source_type: SourceType
    title: str
    segments: list[TextSegment] = field(default_factory=list)
    raw_text: str = ""
    timestamp: str = ""
    credibility: float = 0.0          # 该文档的可信度
    metadata: dict = field(default_factory=dict)

    def full_text(self) -> str:
        if self.segments:
            return "\n".join(seg.text for seg in self.segments)
        return self.raw_text


@dataclass
class SkillSignal:
    """从某份文档中抽取的原始技能信号（未融合）。"""
    name: str
    required_type: str = "提及"
    evidence: str = ""
    source_doc_id: str = ""
    source_type: SourceType = SourceType.JD
    section_type: str = ""
    credibility: float = 0.0
    extraction_confidence: float = 1.0
    timestamp: str = ""


@dataclass
class FusedSkill:
    """多源融合后的可信技能 —— 置信度融合引擎输出。"""
    name: str
    confidence: float = 0.0
    required_type: str = "提及"
    source_count: int = 0
    source_types: list[str] = field(default_factory=list)
    evidences: list[dict] = field(default_factory=list)
    verification_status: str = "unverified"    # confirmed / candidate / unverified
