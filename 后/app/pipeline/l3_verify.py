"""L3 幻觉防控闸门 —— 三道闸核验。

设计方案 §4.2：
闸1：强制引证 —— evidence 非空
闸2：证据核验 —— 片段关键内容来自 JD 原文（模糊匹配，容忍 LLM 轻微改写）
闸3：内容核验 —— 片段必须含该技能名

任何一闸不过即拦截，输出拦截率作为可量化创新指标。
"""

from __future__ import annotations

import re

from app.domain import ExtractedSkill, GateResult, VerifyVerdict


def _norm(text: str) -> str:
    """核验用宽松归一：去空格、大小写、标点符号，只留可比字符。"""
    return re.sub(r"[\s/\-_·、,，。.（）()]+", "", text).lower()


def _skill_in_evidence(skill_name: str, evidence: str) -> bool:
    """技能名字面/模糊是否被证据片段包含。"""
    if not evidence:
        return False
    return _norm(skill_name) in _norm(evidence)


def _evidence_in_jd(evidence: str, jd_fulltext_norm: str) -> bool:
    """检查证据是否来自 JD 原文（模糊匹配）。

    策略：将证据按标点拆成关键短语，只要 60% 以上的短语在 JD 原文中出现即通过。
    这样可以容忍 LLM 对原文的轻微改写（换标点、加连接词等）。
    """
    ev_norm = _norm(evidence)
    if not ev_norm:
        return False

    # 优先精确匹配
    if ev_norm in jd_fulltext_norm:
        return True

    # 模糊匹配：按常见分隔符拆成关键片段
    chunks = re.split(r"[，。；、,;.]", ev_norm)
    chunks = [c.strip() for c in chunks if len(c.strip()) >= 2]
    if not chunks:
        # 不可拆分时，取前 10 字符做子串匹配
        return ev_norm[:10] in jd_fulltext_norm

    hits = sum(1 for c in chunks if c in jd_fulltext_norm)
    return hits / len(chunks) >= 0.6


def verify_one(skill: ExtractedSkill, jd_fulltext_norm: str) -> VerifyVerdict:
    """核验单条技能（三道闸）。

    Args:
        skill: 抽取出的技能
        jd_fulltext_norm: 该 JD 全文的归一化串（调用方预处理一次）

    Returns:
        VerifyVerdict（passed=True 通过 / False 拦截）
    """
    ev = skill.evidence.strip()

    # 闸1：强制引证
    if not ev:
        return VerifyVerdict(skill, False, "无证据：evidence 为空")

    # 闸2：证据核验（关键内容必须来自 JD 原文，容忍 LLM 轻微改写）
    if not _evidence_in_jd(ev, jd_fulltext_norm):
        return VerifyVerdict(skill, False,
                             f"伪造证据：片段不在该JD原文中「{ev[:30]}」")

    # 闸3：内容核验（证据必须含该技能名）
    if not _skill_in_evidence(skill.name, ev):
        return VerifyVerdict(skill, False,
                             f"证据不支撑：片段中找不到技能「{skill.name}」")

    return VerifyVerdict(skill, True, "证据接地：原文可溯源")


def verify(jd_id: str, jd_fulltext: str, skills: list[ExtractedSkill]) -> GateResult:
    """对一条 JD 的抽取结果整体过闸。

    Args:
        jd_id: JD 唯一标识
        jd_fulltext: JD 全文
        skills: 抽取结果

    Returns:
        GateResult（含 passed/rejected 分立列表 + 拦截率）
    """
    jd_norm = _norm(jd_fulltext)
    passed: list[ExtractedSkill] = []
    rejected: list[VerifyVerdict] = []

    for sk in skills:
        v = verify_one(sk, jd_norm)
        if v.passed:
            passed.append(sk)
        else:
            rejected.append(v)

    return GateResult(jd_id=jd_id, total=len(skills), passed=passed, rejected=rejected)
