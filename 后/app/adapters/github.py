"""GitHub 适配器 —— GitHub Trending API（趋势源，轻量信号）。

设计方案 §2.1：趋势源只取技术术语的时间频次，不做深度 NLP。
"""

from __future__ import annotations

from datetime import datetime

from app.adapters.base import DataSource
from app.domain import SourceType
from app.domain.signals import SourceDocument, TextSegment


class GitHubAdapter(DataSource):
    """GitHub Trending 适配器 —— 趋势源。"""

    def __init__(self):
        super().__init__(SourceType.GITHUB)

    def parse(self, path_or_data: str, **kwargs) -> list[SourceDocument]:
        """从 HTTP 响应 JSON 或本地文件解析。

        Args:
            path_or_data: GitHub API 响应 JSON 字符串或文件路径
        """
        import json

        if path_or_data.startswith("{"):
            data = json.loads(path_or_data)
        else:
            with open(path_or_data, encoding="utf-8") as f:
                data = json.load(f)

        docs = []
        repos = data if isinstance(data, list) else data.get("items", [])
        for repo in repos:
            name = repo.get("full_name", repo.get("name", ""))
            desc = repo.get("description", "")
            topics = repo.get("topics", [])
            lang = repo.get("language", "")

            segments = [
                TextSegment(section_type="description", text=desc),
                TextSegment(section_type="topics", text=", ".join(topics)),
                TextSegment(section_type="language", text=lang),
            ]

            docs.append(self._make_doc(
                doc_id=f"github::{name}",
                title=name,
                segments=segments,
                raw_text=f"{desc} {' '.join(topics)} {lang}",
                timestamp=datetime.now().isoformat(),
                stars=repo.get("stargazers_count", 0),
                forks=repo.get("forks_count", 0),
            ))

        return docs
