"""JD 派生数据 API —— 市场对比 / 信号光谱 / 质量诊断。

数据源：T4/T5/T6 派生表（jd_records 二次加工）。API 层只做形状映射，读取交给 jd_service。

GET  /api/jd/market?title=X   → 岗位市场技能（T4）MarketSkill[]
GET  /api/jd/signals          → 技能信号光谱（T5·jd 源）SignalDetail[]
GET  /api/jd/quality?limit=N  → JD 质量诊断（T6）JDDiagnosis[]
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.jd_service import (
    get_position_skills,
    get_quality_diagnoses,
    get_skill_signals,
)

router = APIRouter(tags=["JD 数据"])


@router.get("/market")
async def jd_market(title: str):
    """岗位市场技能（T4）→ MarketSkill[]。PositionDiffView 市场侧对比用（D6）。"""
    try:
        skills = await get_position_skills(title, limit=100)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")
    return {
        "skills": [
            {
                "name": s["skill_name"],
                "weight": s["weight"],
                "level": s["level"],
                "freshness": round(100 * s["confidence"]),
            }
            for s in skills
        ]
    }


@router.get("/signals")
async def jd_signals():
    """技能信号光谱（T5·jd 源）→ SignalDetail[]。github/arxiv/standard 源保持 demo（D5）。"""
    try:
        signals = await get_skill_signals()
    except Exception:
        signals = []
    return {
        "signals": [
            {
                "skillName": s["skill_name"],
                "category": s["category"],
                "totalConfidence": round(s["jd_confidence"], 3),
                "verificationStatus": s["verification_status"],
                "sources": [
                    {
                        "source": "jd",
                        "frequency": s["jd_frequency"],
                        "confidence": round(s["jd_confidence"], 3),
                        "examples": s["jd_examples"],
                    }
                ],
            }
            for s in signals
        ]
    }


@router.get("/quality")
async def jd_quality(limit: int = 50):
    """JD 质量诊断（T6）→ JDDiagnosis[]（与 /api/enterprise/diagnose 同形状）。"""
    try:
        rows = await get_quality_diagnoses(limit=limit)
    except Exception:
        rows = []
    return {
        "diagnoses": [
            {
                "id": r["jd_id"],
                "positionName": r["title"],
                "jdTitle": r["title"],
                "submittedAt": r.get("created_at") or "",
                "inflationIndex": r["inflation_index"],
                "missingKeywords": [],
                "redundantKeywords": r.get("inflated_items") or [],
                "overallScore": r["overall_score"],
                "status": r["status"],
            }
            for r in rows
        ]
    }
