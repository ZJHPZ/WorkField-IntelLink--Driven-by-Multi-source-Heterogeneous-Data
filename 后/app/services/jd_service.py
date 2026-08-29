"""JD 派生表读服务 —— 供 API 层做形状映射的六个读函数。

数据源：T1–T6 派生表（由 build_jd_derived.py 从 zhiyv.jd_records 二次加工生成）。
计划 §6：仓储层单一职责，API 层只做形状映射。
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.persistence.database import get_session
from app.persistence.zhiyv_models import (
    JDQualityDiagnosis,
    JDPositionCitySalary,
    JDPositionEvolution,
    JDPositionProfile,
    JDPositionSkill,
    JDSkillSignal,
)

logger = logging.getLogger(__name__)


async def get_position_profile(title: str) -> dict | None:
    """T1 岗位画像：按 title 取一行。"""
    async for session in get_session():
        row = (
            await session.execute(
                select(JDPositionProfile).where(JDPositionProfile.title == title)
            )
        ).scalar_one_or_none()
        if not row:
            return None
        return {
            "title": row.title,
            "jd_count": row.jd_count,
            "salary_unit": row.salary_unit,
            "salary_min_p25": row.salary_min_p25,
            "salary_min_p50": row.salary_min_p50,
            "salary_min_p75": row.salary_min_p75,
            "salary_max_p25": row.salary_max_p25,
            "salary_max_p50": row.salary_max_p50,
            "salary_max_p75": row.salary_max_p75,
            "salary_cover_rate": row.salary_cover_rate,
            "top_cities": row.top_cities or [],
            "top_companies": row.top_companies or [],
            "industry_dist": row.industry_dist or [],
            "size_dist": row.size_dist or [],
            "type_dist": row.type_dist or [],
            "latest_posted": row.latest_posted.isoformat() if row.latest_posted else None,
        }


async def get_all_position_profiles() -> list[dict]:
    """T1 全量岗位画像（按 jd_count 降序）。"""
    async for session in get_session():
        rows = (
            await session.execute(
                select(JDPositionProfile).order_by(JDPositionProfile.jd_count.desc())
            )
        ).scalars().all()
        return [
            {
                "title": r.title,
                "jd_count": r.jd_count,
                "salary_unit": r.salary_unit,
                "salary_min_p25": r.salary_min_p25,
                "salary_min_p50": r.salary_min_p50,
                "salary_min_p75": r.salary_min_p75,
                "salary_max_p25": r.salary_max_p25,
                "salary_max_p50": r.salary_max_p50,
                "salary_max_p75": r.salary_max_p75,
                "salary_cover_rate": r.salary_cover_rate,
                "top_cities": r.top_cities or [],
                "top_companies": r.top_companies or [],
                "industry_dist": r.industry_dist or [],
                "size_dist": r.size_dist or [],
                "type_dist": r.type_dist or [],
                "latest_posted": r.latest_posted.isoformat() if r.latest_posted else None,
            }
            for r in rows
        ]


async def get_position_city_salary(title: str) -> list[dict]:
    """T2 岗位×城市薪资。"""
    async for session in get_session():
        rows = (
            await session.execute(
                select(JDPositionCitySalary)
                .where(JDPositionCitySalary.title == title)
                .order_by(JDPositionCitySalary.jd_count.desc())
            )
        ).scalars().all()
        return [
            {
                "title": r.title,
                "city": r.city,
                "jd_count": r.jd_count,
                "salary_min_median": r.salary_min_median,
                "salary_max_median": r.salary_max_median,
                "salary_unit": r.salary_unit,
            }
            for r in rows
        ]


async def get_position_evolution(title: str) -> list[dict]:
    """T3 岗位演化月桶（按 month_key 排序）。"""
    async for session in get_session():
        rows = (
            await session.execute(
                select(JDPositionEvolution)
                .where(JDPositionEvolution.title == title)
                .order_by(JDPositionEvolution.month_key)
            )
        ).scalars().all()
        return [
            {
                "title": r.title,
                "month_key": r.month_key,
                "jd_count": r.jd_count,
                "salary_min_median": r.salary_min_median,
                "salary_max_median": r.salary_max_median,
                "salary_unit": r.salary_unit,
            }
            for r in rows
        ]


async def get_position_skills(title: str, limit: int = 100) -> list[dict]:
    """T4 岗位×技能权重（按 weight 降序）。"""
    async for session in get_session():
        rows = (
            await session.execute(
                select(JDPositionSkill)
                .where(JDPositionSkill.title == title)
                .order_by(JDPositionSkill.weight.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            {
                "title": r.title,
                "skill_name": r.skill_name,
                "jd_count": r.jd_count,
                "weight": r.weight,
                "required_type": r.required_type,
                "level": r.level,
                "confidence": r.confidence,
            }
            for r in rows
        ]


async def get_all_position_skills() -> list[dict]:
    """T4 全量岗位×技能（一次读出，API 层按 title 分组）。"""
    async for session in get_session():
        rows = (
            await session.execute(select(JDPositionSkill))
        ).scalars().all()
        return [
            {
                "title": r.title,
                "skill_name": r.skill_name,
                "jd_count": r.jd_count,
                "weight": r.weight,
                "required_type": r.required_type,
                "level": r.level,
                "confidence": r.confidence,
            }
            for r in rows
        ]


async def get_skill_signals() -> list[dict]:
    """T5 技能信号（jd 源，按 jd_frequency 降序）。"""
    async for session in get_session():
        rows = (
            await session.execute(
                select(JDSkillSignal).order_by(JDSkillSignal.jd_frequency.desc())
            )
        ).scalars().all()
        return [
            {
                "skill_name": r.skill_name,
                "category": r.category,
                "jd_frequency": r.jd_frequency,
                "jd_confidence": r.jd_confidence,
                "jd_examples": r.jd_examples or [],
                "verification_status": r.verification_status,
            }
            for r in rows
        ]


async def get_quality_diagnoses(limit: int = 50) -> list[dict]:
    """T6 JD 质量诊断（默认前 limit 条）。"""
    async for session in get_session():
        rows = (
            await session.execute(
                select(JDQualityDiagnosis).limit(limit)
            )
        ).scalars().all()
        return [
            {
                "jd_id": r.jd_id,
                "title": r.title,
                "skill_count": r.skill_count,
                "inflation_index": r.inflation_index,
                "inflated_items": r.inflated_items or [],
                "soft_skill_ratio": r.soft_skill_ratio,
                "required_ratio": r.required_ratio,
                "suggestions": r.suggestions or [],
                "overall_score": r.overall_score,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]


# ══════════════════════════════════════════════
# 展示形状辅助 —— JD 派生表读结果的展示化（API 层复用）
# ══════════════════════════════════════════════

def salary_range(p: dict) -> str:
    """月薪范围文案 '14-26K'；兼容 T1（salary_*_p50）与 T2/T3（salary_*_median）。"""
    lo = p.get("salary_min_p50") or p.get("salary_min_median")
    hi = p.get("salary_max_p50") or p.get("salary_max_median")
    if not lo or not hi:
        return ""
    return f"{int(lo) // 1000}-{int(hi) // 1000}K"


def infer_tech_stack(title: str) -> str:
    """岗位名 → 技术栈粗分类（仅展示用，与 ExploreView 筛选桶对齐，不做硬决策）。"""
    t = title or ""
    if any(k in t for k in ("算法", "AI", "人工智能", "机器学习", "NLP", "大模型", "数据科学", "深度学习", "自然语言")):
        return "人工智能"
    if any(k in t for k in ("前端", "Web", "H5", "小程序", "Vue", "React")):
        return "前端"
    if any(k in t for k in ("Java", "后端", "服务端", "Golang", "Go", "Python", ".NET", "C++", "C#", "PHP", "全栈", "测试")):
        return "后端"
    if any(k in t for k in ("大数据", "数据", "ETL", "数仓", "BI", "分析")):
        return "大数据"
    if any(k in t for k in ("运维", "DevOps", "SRE", "QA", "安全", "实施")):
        return "DevOps"
    if any(k in t for k in ("物联网", "嵌入式", "硬件", "芯片")):
        return "物联网"
    return "智能系统"


def classify_position_types(profiles: list[dict]) -> dict[str, str]:
    """按 jd_count 中位数划分：≥中位 → 既有，<中位 → 新兴。
    （采样窗口内需求小的岗位更可能为新/边缘岗位；D3 无时间序列指标，故不用 emergence。）"""
    if not profiles:
        return {}
    counts = sorted(p["jd_count"] for p in profiles)
    median = counts[len(counts) // 2]
    return {
        p["title"]: ("既有" if p["jd_count"] >= median else "新兴")
        for p in profiles
    }
