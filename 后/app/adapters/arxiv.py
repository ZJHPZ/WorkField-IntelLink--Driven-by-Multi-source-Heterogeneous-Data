"""arXiv 适配器 —— 学术论文（趋势源，轻量信号）。

设计方案 §2.1：趋势源只取技术术语的时间频次，不做深度 NLP。
"""

from __future__ import annotations

from datetime import datetime

from app.adapters.base import DataSource
from app.domain import SourceType
from app.domain.signals import SourceDocument, TextSegment


class ArxivAdapter(DataSource):
    """arXiv 适配器 —— 学术趋势源。"""

    def __init__(self):
        super().__init__(SourceType.ARXIV)

    def parse(self, path_or_data: str, **kwargs) -> list[SourceDocument]:
        """从 HTTP 响应 JSON 或本地文件解析。

        Args:
            path_or_data: arXiv API 响应 JSON 或文件路径
        """
        import json

        if path_or_data.startswith("{"):
            data = json.loads(path_or_data)
        else:
            with open(path_or_data, encoding="utf-8") as f:
                data = json.load(f)

        docs = []
        papers = data if isinstance(data, list) else data.get("papers", [])
        for paper in papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", paper.get("summary", ""))
            categories = paper.get("categories", [])

            segments = [
                TextSegment(section_type="title", text=title),
                TextSegment(section_type="abstract", text=abstract),
                TextSegment(section_type="categories",
                            text=", ".join(categories) if isinstance(categories, list) else str(categories)),
            ]

            docs.append(self._make_doc(
                doc_id=f"arxiv::{paper.get('id', '')}",
                title=title,
                segments=segments,
                raw_text=f"{title} {abstract}",
                timestamp=paper.get("published", datetime.now().isoformat()),
                authors=paper.get("authors", []),
            ))

        return docs
