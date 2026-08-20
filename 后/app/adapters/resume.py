"""简历适配器 —— PDF/Word 解析（个人供给侧）。

设计方案 §7.3 个人侧：上传简历 → 抽取技能/经验/学历。
"""

from __future__ import annotations

from app.adapters.base import DataSource
from app.domain import SourceType
from app.domain.signals import SourceDocument, TextSegment


class ResumeAdapter(DataSource):
    """简历适配器 —— PDF/Word 文本提取。"""

    def __init__(self):
        super().__init__(SourceType.RESUME)

    def parse(self, path_or_data: str, **kwargs) -> list[SourceDocument]:
        """解析简历文件。

        Args:
            path_or_data: .pdf / .docx 文件路径，或纯文本字符串
        """
        text = ""
        if path_or_data.endswith(".pdf"):
            text = self._parse_pdf(path_or_data)
        elif path_or_data.endswith(".docx"):
            text = self._parse_docx(path_or_data)
        else:
            text = path_or_data

        segments = [
            TextSegment(section_type="full", text=text),
        ]

        return [self._make_doc(
            doc_id=f"resume::{hash(text) & 0xFFFFFFFF:08x}",
            title="简历",
            segments=segments,
            raw_text=text,
        )]

    def _parse_pdf(self, path: str) -> str:
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
        except ImportError:
            raise ImportError("需要安装 pdfplumber：pip install pdfplumber")

    def _parse_docx(self, path: str) -> str:
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise ImportError("需要安装 python-docx：pip install python-docx")
