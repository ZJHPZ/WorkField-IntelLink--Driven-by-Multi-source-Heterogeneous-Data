"""多源适配层基类 —— DataSource / BaseExtractor 抽象。

设计方案 §2.1：四类信源（需求源/权威源/趋势源/参照源）统一接入。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.domain import SourceType
from app.domain.signals import SourceDocument, TextSegment


# 信源可信度基数（设计方案 §3.4）
BASE_CREDIBILITY: dict[SourceType, float] = {
    SourceType.STANDARD: 0.95,   # 权威源
    SourceType.GITHUB:   0.80,   # 趋势源
    SourceType.JD:       0.70,   # 需求源（有噪声）
    SourceType.ARXIV:    0.50,   # 学术源（偏理论）
    SourceType.RESUME:   0.55,   # 简历（可能注水）
}


class DataSource(ABC):
    """数据源适配器基类。"""

    def __init__(self, source_type: SourceType):
        self.source_type = source_type

    @abstractmethod
    def parse(self, path_or_data: str, **kwargs) -> list[SourceDocument]:
        """解析数据源，返回统一的 SourceDocument 列表。"""
        ...

    def _make_doc(self, doc_id: str, title: str,
                  segments: list[TextSegment],
                  raw_text: str = "", timestamp: str = "",
                  **meta) -> SourceDocument:
        """构造 SourceDocument 的便捷方法。"""
        return SourceDocument(
            doc_id=doc_id,
            source_type=self.source_type,
            title=title,
            segments=segments,
            raw_text=raw_text,
            timestamp=timestamp or datetime.now().isoformat(),
            credibility=BASE_CREDIBILITY.get(self.source_type, 0.5),
            metadata=meta,
        )
