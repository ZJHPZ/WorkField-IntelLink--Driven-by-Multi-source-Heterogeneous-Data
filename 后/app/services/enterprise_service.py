"""企业工作台服务 —— JD 诊断 / 岗位标准 / 团队盘点 / 人才预测。

设计方案 §7.2：企业侧（面向 HR / 用人部门 / 培训）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.pipeline.l2_metrics import MetricsCalculator

logger = logging.getLogger(__name__)

_calc = MetricsCalculator()


@dataclass
class JDDiagnosis:
    """JD 质量诊断报告。"""
    jd_id: str = ""
    title: str = ""
    skill_count: int = 0
    inflation_index: float = 0.0         # 通胀指数 ∈ [0,1]
    inflated_items: list[str] = field(default_factory=list)  # 注水项清单
    soft_skill_ratio: float = 0.0        # 软技能占比
    required_ratio: float = 0.0           # 必备技能占比
    suggestions: list[str] = field(default_factory=list)     # 改进建议


def diagnose_jd(jd_id: str, title: str, skills: list[dict],
                avg_skill_count: float = 8.0) -> JDDiagnosis:
    """诊断一条 JD 的质量。

    Args:
        jd_id: JD 标识
        title: 岗位名称
        skills: 抽取出的技能列表 [{"name": ..., "required_type": "必备|加分", "source": ...}]
        avg_skill_count: 所有 JD 的平均技能数（参考值）
    """
    skill_count = len(skills)
    required_count = sum(1 for s in skills if s.get("required_type") == "必备")
    required_ratio = required_count / skill_count if skill_count > 0 else 0

    # 通胀指数
    inflation = _calc.inflation_index(skill_count, avg_skill_count, required_ratio)

    # 注水项检测
    inflated = []
    generic_patterns = ["抗压能力", "责任心", "积极主动", "学习能力", "团队合作",
                        "沟通能力", "执行力"]
    for s in skills:
        name = s.get("name", "")
        if any(gp in name for gp in generic_patterns):
            inflated.append(f"泛化软技能: {name}")

    if skill_count > avg_skill_count * 1.5:
        inflated.append(f"技能总数异常 ({skill_count} > 平均 {avg_skill_count:.0f})")

    # 改进建议
    suggestions = []
    if inflation > 0.3:
        suggestions.append("建议精简技能要求，聚焦核心必备技能")
    if required_ratio < 0.3:
        suggestions.append("必备技能占比过低，建议明确区分必备/加分")
    if inflated:
        suggestions.append(f"发现 {len(inflated)} 项疑似注水内容，建议移除泛化软技能")

    return JDDiagnosis(
        jd_id=jd_id, title=title,
        skill_count=skill_count,
        inflation_index=round(inflation, 3),
        inflated_items=inflated,
        soft_skill_ratio=round(1 - required_ratio, 2) if skill_count > 0 else 0,
        required_ratio=round(required_ratio, 2),
        suggestions=suggestions,
    )


@dataclass
class TeamGapReport:
    """团队技能盘点报告。"""
    position_name: str = ""
    total_members: int = 0
    avg_match_rate: float = 0.0
    common_gaps: list[dict] = field(default_factory=list)   # 团队共同缺失的技能
    individual_results: list[dict] = field(default_factory=list)


def team_skill_gap(match_results: list[dict], position_name: str = "") -> TeamGapReport:
    """团队技能盘点：汇总所有人的匹配结果。

    Args:
        match_results: [{"user_id": ..., "match_rate": ..., "missing_skills": [...]}, ...]
        position_name: 目标岗位
    """
    if not match_results:
        return TeamGapReport(position_name=position_name)

    total = len(match_results)
    avg_rate = sum(r.get("match_rate", 0) for r in match_results) / total

    # 统计共同缺失技能
    from collections import Counter
    gap_counter = Counter()
    for r in match_results:
        for m in r.get("missing_skills", []):
            gap_counter[m.get("canonical", m.get("name", ""))] += 1

    common_gaps = [
        {"skill": name, "missing_count": cnt, "missing_ratio": round(cnt / total, 2)}
        for name, cnt in gap_counter.most_common(10)
    ]

    return TeamGapReport(
        position_name=position_name,
        total_members=total,
        avg_match_rate=round(avg_rate, 2),
        common_gaps=common_gaps,
        individual_results=match_results,
    )


def talent_forecast(skill_metrics: dict, top_k: int = 10) -> dict:
    """人才需求预测：基于新兴度/衰退度趋势。

    Args:
        skill_metrics: {skill_name: {"emergence": float, "decline": float, ...}}
        top_k: 返回 top K
    """
    emerging = sorted(
        [(name, m.get("emergence", 0)) for name, m in skill_metrics.items()],
        key=lambda x: -x[1],
    )[:top_k]

    declining = sorted(
        [(name, m.get("decline", 0)) for name, m in skill_metrics.items()],
        key=lambda x: -x[1],
    )[:top_k]

    return {
        "hot_skills": [{"name": n, "emergence": e} for n, e in emerging],
        "cooling_skills": [{"name": n, "decline": d} for n, d in declining],
        "recommendation": (
            f"建议优先招聘/培训: {', '.join(n for n, _ in emerging[:5])}"
            if emerging else "暂无足够趋势数据"
        ),
    }
