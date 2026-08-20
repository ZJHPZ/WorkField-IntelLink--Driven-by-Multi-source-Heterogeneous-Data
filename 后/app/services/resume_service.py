"""简历解析服务 —— 上传 PDF/Word → 抽取技能/经验/学历。

设计方案 §7.3 个人侧 + 赛题要求④：
- 支持 PDF/Word 格式
- 要素提取准确率 ≥ 90%
- 输出结构化简历（技能/经验/学历/城市）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.domain import ExtractedSkill
from app.pipeline.l1_clean import clean as l1_clean, _parse_salary, _parse_experience, _parse_education
from app.adapters.resume import ResumeAdapter

logger = logging.getLogger(__name__)


@dataclass
class ParsedResume:
    """解析后的结构化简历。"""
    resume_id: str
    raw_text: str = ""
    skills: list[dict] = field(default_factory=list)    # [{name, level, evidence}]
    experience_years: int | None = None
    education: str | None = None
    city: str | None = None
    target_positions: list[str] = field(default_factory=list)


def parse_resume(file_path: str) -> ParsedResume:
    """解析简历文件（PDF/Word）。

    Args:
        file_path: .pdf / .docx 文件路径

    Returns:
        ParsedResume（结构化提取结果）
    """
    # 1. 文本提取
    adapter = ResumeAdapter()
    docs = adapter.parse(file_path)
    if not docs:
        raise ValueError(f"无法从文件提取文本: {file_path}")

    raw_text = docs[0].raw_text
    resume_id = docs[0].doc_id

    # 2. 技能抽取（L3 规则模式，简历场景不适合调 LLM）
    from app.pipeline.l3_extract import _rule_extract
    from app.pipeline.l1_clean import CleanedJD

    # 构造一个伪 CleanedJD 供规则抽取使用
    cleaned = CleanedJD(
        jd_id=resume_id,
        title="简历",
        tech_stack="",
        posted_date="",
        candidates=[("requirement", line.strip())
                    for line in raw_text.split("\n") if line.strip()],
    )

    extracted = _rule_extract(cleaned)

    # 3. 强字段提取
    exp = _parse_experience(raw_text)
    edu = _parse_education(raw_text)

    # 4. 城市检测（简单规则）
    city = None
    import re
    city_match = re.search(r"(北京|上海|广州|深圳|杭州|成都|武汉|南京|合肥|西安)", raw_text)
    if city_match:
        city = city_match.group(1)

    skills_dict = [
        {"name": s.name, "level": "L3", "evidence": s.evidence[:100]}
        for s in extracted
    ]

    logger.info(f"简历解析完成: {len(skills_dict)} 个技能, 经验 {exp}年, 学历 {edu}")

    return ParsedResume(
        resume_id=resume_id,
        raw_text=raw_text[:5000],
        skills=skills_dict,
        experience_years=exp,
        education=edu,
        city=city,
    )


def parse_resume_text(text: str) -> ParsedResume:
    """解析纯文本简历（不上传文件时使用）。"""
    resume_id = f"resume::{hash(text) & 0xFFFFFFFF:08x}"

    from app.pipeline.l3_extract import _rule_extract
    from app.pipeline.l1_clean import CleanedJD

    cleaned = CleanedJD(
        jd_id=resume_id, title="简历", tech_stack="", posted_date="",
        candidates=[("requirement", line.strip())
                    for line in text.split("\n") if line.strip()],
    )

    extracted = _rule_extract(cleaned)
    exp = _parse_experience(text)
    edu = _parse_education(text)

    return ParsedResume(
        resume_id=resume_id,
        raw_text=text[:5000],
        skills=[{"name": s.name, "level": "L3", "evidence": s.evidence[:100]}
                for s in extracted],
        experience_years=exp,
        education=edu,
    )
