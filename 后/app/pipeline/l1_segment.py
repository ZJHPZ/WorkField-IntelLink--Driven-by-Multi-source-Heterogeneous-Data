"""L1 段落定位 —— 按 JD 文本内容推断段落类型。

设计方案 §2.2："段落定位即强信号"。
对于段落标注不完整的 JD（如纯文本导入），用启发式规则推断各段类型。
"""

from __future__ import annotations

import re

from app.domain import SectionType, Paragraph


# 段落定位规则
_SECTION_PATTERNS: list[tuple[SectionType, list[str]]] = [
    (SectionType.RESPONSIBILITY, [
        r"岗位职责", r"工作职责", r"职位描述", r"工作内容", r"岗位描述",
        r"负责", r"职责描述",
    ]),
    (SectionType.REQUIREMENT, [
        r"任职要求", r"岗位要求", r"职位要求", r"能力要求", r"技术要求",
        r"技能要求", r"资格要求", r"我们希望你",
    ]),
    (SectionType.BONUS, [
        r"加分项", r"优先条件", r"优先考虑", r"有以下经验者优先",
        r"有以下能力者优先",
    ]),
    (SectionType.WELFARE, [
        r"福利", r"薪酬", r"薪资", r"待遇", r"五险一金",
    ]),
    (SectionType.COMPANY, [
        r"公司介绍", r"关于我们", r"企业简介", r"公司简介",
    ]),
]


def classify_section(text: str) -> SectionType:
    """根据文本内容推断段落类型。"""
    for sec_type, patterns in _SECTION_PATTERNS:
        for pat in patterns:
            if re.search(pat, text):
                return sec_type
    return SectionType.OTHER


def segment_text(full_text: str) -> list[Paragraph]:
    """将纯文本 JD 按空行/换行分段，并推断各段类型。

    Args:
        full_text: JD 全文

    Returns:
        带 SectionType 标注的段落列表
    """
    # 按双换行或明显的标题行分割
    lines = full_text.strip().split("\n")
    paragraphs: list[Paragraph] = []
    current_lines: list[str] = []
    current_section = SectionType.OTHER

    for line in lines:
        line = line.strip()
        if not line:
            if current_lines:
                text = " ".join(current_lines)
                paragraphs.append(Paragraph(section=current_section, text=text))
                current_lines = []
            continue

        # 检测是否为段落标题（长度短 或 含冒号标题）
        inferred = classify_section(line)
        is_header = (inferred != SectionType.OTHER and len(line) < 50) or \
                    (inferred != SectionType.OTHER and ('：' in line or ':' in line))

        if is_header:
            # 保存上一段
            if current_lines:
                text = " ".join(current_lines)
                paragraphs.append(Paragraph(section=current_section, text=text))
                current_lines = []
            current_section = inferred
            # 如果标题行后面还有内容（如 "任职要求：熟悉Python"），把冒号后的内容提取出来
            for sep in ('：', ':'):
                if sep in line:
                    _, content = line.split(sep, 1)
                    content = content.strip()
                    if content:
                        current_lines.append(content)
                    break
        else:
            current_lines.append(line)

    # 最后一段
    if current_lines:
        text = " ".join(current_lines)
        paragraphs.append(Paragraph(section=current_section, text=text))

    return paragraphs
