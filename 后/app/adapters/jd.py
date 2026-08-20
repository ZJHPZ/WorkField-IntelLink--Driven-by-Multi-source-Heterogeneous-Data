"""JD 适配器 —— 招聘数据（需求源）。

将 JobPosting 转换为统一的 SourceDocument 格式。
"""

from __future__ import annotations

from app.adapters.base import DataSource
from app.domain import SourceType, JobPosting
from app.domain.signals import SourceDocument, TextSegment


class JDAdapter(DataSource):
    """招聘 JD 适配器。"""

    def __init__(self):
        super().__init__(SourceType.JD)

    def parse(self, path_or_data: str, **kwargs) -> list[SourceDocument]:
        """从 JSONL 文件或 JobPosting 列表解析。

        Args:
            path_or_data: JSONL 文件路径（str）或 JobPosting 列表
        """
        if isinstance(path_or_data, list):
            return [self._jd_to_doc(jd) for jd in path_or_data]

        # 从 JSONL 文件加载
        import json
        docs = []
        with open(path_or_data, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                docs.append(self._dict_to_doc(d))
        return docs

    def _jd_to_doc(self, jd: JobPosting) -> SourceDocument:
        segments = [
            TextSegment(
                section_type=p.section.value if hasattr(p.section, 'value') else str(p.section),
                text=p.text,
            )
            for p in jd.paragraphs
        ]
        return self._make_doc(
            doc_id=jd.jd_id,
            title=jd.title,
            segments=segments,
            raw_text=jd.full_text(),
            timestamp=jd.posted_date,
            salary_min=jd.salary_min,
            salary_max=jd.salary_max,
            experience_years=jd.experience_years,
        )

    def _dict_to_doc(self, d: dict) -> SourceDocument:
        segments = [
            TextSegment(section_type=p.get("section", "requirement"), text=p.get("text", ""))
            for p in d.get("paragraphs", [])
        ]
        return self._make_doc(
            doc_id=d.get("jd_id", ""),
            title=d.get("title", ""),
            segments=segments,
            raw_text="\n".join(p.get("text", "") for p in d.get("paragraphs", [])),
            timestamp=d.get("posted_date", ""),
        )
