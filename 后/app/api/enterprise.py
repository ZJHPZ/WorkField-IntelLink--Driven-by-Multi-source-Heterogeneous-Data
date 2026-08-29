"""★ 企业工作台 API (To B) —— GET 端点查 MySQL，POST 端点走 Agent。

数据来源：MySQL zhiyv 库，不再依赖 Neo4j。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import get_api_system
from app.agents.agent_state import IntentType
from app.persistence.database import get_session
from app.persistence.zhiyv_models import (
    VerifiedSkill, SkillStat, NewRole, EvolutionRecord,
)
from app.services.jd_service import (
    classify_position_types,
    get_all_position_profiles,
    get_all_position_skills,
    get_position_evolution as get_t3_evolution,
    get_position_skills,
    get_quality_diagnoses,
    infer_tech_stack,
    salary_range,
)

router = APIRouter(tags=["企业工作台"])


class JDDiagnoseRequest(BaseModel):
    jd_id: str = ""
    title: str = ""
    skills: list[dict] = []
    avg_skill_count: float = 8.0


class TeamGapRequest(BaseModel):
    position_name: str = ""
    position_skills: list[dict] = []
    user_skills_list: list[list[str]] = []


class ValidatePositionRequest(BaseModel):
    term: str
    evidence_jds: list[dict] = []
    emerging_skills: list[str] = []


class StandardUpdateRequest(BaseModel):
    skills: list[dict] = []
    description: str = ""


@router.post("/jd/diagnose")
async def diagnose_jd_endpoint(req: JDDiagnoseRequest):
    """★ JD 质量诊断 → 纯算法（确定性计算，不需 Agent）。"""
    from app.services.enterprise_service import diagnose_jd
    result = diagnose_jd(req.jd_id, req.title, req.skills, req.avg_skill_count)
    return {"status": "ok", "diagnosis": result.__dict__}


@router.get("/positions/{position_id}/standard")
async def get_position_standard(position_id: str):
    """获取岗位标准定义。命中 T4 → T4 技能作为标准；否则回退 verified_skills + skill_stats。"""
    try:
        skills = await get_position_skills(position_id, limit=100)
    except Exception:
        skills = []
    if skills:
        return {
            "status": "ok",
            "position": {"name": position_id},
            "skills": [
                {
                    "name": s["skill_name"],
                    "confidence": s["confidence"],
                    "required_type": s["required_type"],
                    "status": "confirmed",
                }
                for s in skills
            ],
        }

    try:
        from app.graph.repository import get_position_detail
        detail = await get_position_detail(position_id)
        if not detail:
            raise HTTPException(status_code=404, detail="岗位不存在")

        # 已经是新格式，直接组装返回
        skills = []
        for item in detail.get("skills", []):
            sk = item.get("skill", {})
            rel = item.get("rel", {})
            skills.append({
                "name": sk.get("name", ""),
                "confidence": sk.get("confidence", 0),
                "required_type": rel.get("required_type", "必备"),
                "status": sk.get("status", "candidate"),
            })
        return {"status": "ok", "position": detail.get("position", {}), "skills": skills}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@router.put("/positions/{position_id}/standard")
async def update_position_standard(position_id: str, req: StandardUpdateRequest):
    """人工更新岗位标准 → 写入 MySQL verified_skills + skill_stats。"""
    from app.graph.repository import upsert_skill, link_requires

    for s in req.skills:
        skill_name = s["name"]
        await upsert_skill(
            skill_name=skill_name,
            confidence=s.get("confidence", 0.8),
            status="confirmed",
        )
        await link_requires(
            position_id=position_id,
            skill_name=skill_name,
            required_type=s.get("required_type", "必备"),
            confidence=s.get("confidence", 0.8),
        )

    return {"status": "ok", "position_id": position_id,
            "message": f"已更新 {len(req.skills)} 项技能标准", "manual_optimized": True}


@router.post("/positions/validate")
async def validate_new_position(req: ValidatePositionRequest):
    """★ 验证候选新岗位 → Agent 辩论系统 (DiscoveryAgent → JudgeAgent)。"""
    system = get_api_system()
    from app.agents.agent_state import MultiAgentState
    state = MultiAgentState(
        current_intent=IntentType.DISCOVER_ROLE,
        payload={"debate_topic": {
            "term": req.term,
            "emerging_skills": req.emerging_skills,
            "evidence_jds": req.evidence_jds,
        }},
    )
    for aid in ["discoverer", "judge"]:
        agent = system.registry.get(aid)
        if agent:
            result = await agent.process(state)
            state.set_agent_result(aid, result)

    verdict = state.get_agent_result("judge") or {}
    return {"status": "ok", "term": req.term,
            "verdict": verdict.get("data", verdict)}


@router.post("/team/gap")
async def team_skill_gap_endpoint(req: TeamGapRequest):
    """★ 团队技能盘点 → Agent 系统批量匹配。"""
    from app.services.enterprise_service import team_skill_gap

    system = get_api_system()
    results = []
    for skills in req.user_skills_list:
        result = await system.process(IntentType.MATCH_POSITION, {
            "user_skills": skills,
            "position_skills": req.position_skills,
            "position_name": req.position_name,
        })
        agent_data = result.get("result", {}).get("data", {})
        results.append({
            "match_rate": agent_data.get("match_rate", 0),
            "matched_skills": agent_data.get("matched_skills", []),
            "missing_skills": agent_data.get("missing_skills", []),
        })

    report = team_skill_gap(results, req.position_name)
    return {"status": "ok", "report": report.__dict__}


@router.get("/talent/forecast")
async def talent_forecast_endpoint(tech_stack: str | None = None):
    """人才需求预测 → 从 MySQL skill_stats 读取指标数据。"""
    from app.graph.repository import get_all_skill_stats
    from app.services.enterprise_service import talent_forecast

    all_stats = await get_all_skill_stats()
    skill_metrics = {
        s["skill_name"]: {
            "emergence": s["emergence"],
            "decline": s["decline"],
        }
        for s in all_stats
    }
    result = talent_forecast(skill_metrics)
    return {"status": "ok", **result}


# ══════════════════════════════════════════════
# GET 端点 —— 前端 stores 调用
# ══════════════════════════════════════════════

@router.get("/positions")
async def list_enterprise_positions():
    """获取岗位标准列表。优先 T1 画像 + T4 技能；空则回退 verified_skills。前端 GET /api/enterprise/positions。"""
    try:
        profiles = await get_all_position_profiles()
    except Exception:
        profiles = []
    if profiles:
        max_jd = max(p["jd_count"] for p in profiles) or 1
        # T4 全量技能一次读出，按 title 分组
        skills_by_title: dict[str, list[dict]] = {}
        try:
            for s in await get_all_position_skills():
                skills_by_title.setdefault(s["title"], []).append(s)
        except Exception:
            pass

        type_map = classify_position_types(profiles)
        result = []
        for p in profiles:
            skills = skills_by_title.get(p["title"], [])[:20]
            result.append({
                "id": p["title"],
                "name": p["title"],
                "department": infer_tech_stack(p["title"]),
                "level": "P5",
                "skills": [
                    {
                        "name": s["skill_name"],
                        "level": s["level"],
                        "weight": s["weight"],
                        "trend": "stable",  # D3：无时间序列，不伪造趋势
                        "freshness": round(100 * s["confidence"]),
                    }
                    for s in skills
                ],
                "status": "confirmed" if type_map[p["title"]] == "既有" else "emerging",
                "lastUpdated": p["latest_posted"] or "",
                "marketDemand": min(100, round(p["jd_count"] / max_jd * 100)),
                "matchRate": 0,
            })
        return {"positions": result}

    from app.graph.repository import get_positions, get_position_detail

    positions = await get_positions()
    result = []
    for pos in positions:
        detail = await get_position_detail(pos["position_id"])
        skills = []
        if detail:
            for sk in detail.get("skills", []):
                skill_data = sk.get("skill", {})
                rel = sk.get("rel", {})
                skills.append({
                    "name": skill_data.get("name", ""),
                    "level": _level_from_confidence(skill_data.get("confidence", 0)),
                    "weight": rel.get("confidence", 0.5),
                    "trend": _trend_from_emergence(skill_data.get("emergence", 0)),
                    "freshness": max(0, 100 - int(skill_data.get("decline", 0) * 100)),
                })

        result.append({
            "id": pos["position_id"],
            "name": pos.get("name", ""),
            "department": pos.get("tech_stack", ""),
            "level": "P5",
            "skills": skills,
            "status": "confirmed" if pos.get("position_type") == "既有" else "emerging",
            "lastUpdated": "",
            "marketDemand": min(100, int(pos.get("avg_emergence", 0) * 20)),
            "matchRate": 0,
        })

    return {"positions": result}


@router.get("/discovery")
async def list_discovery():
    """获取新岗位发现列表。前端 GET /api/enterprise/discovery。"""
    async for session in get_session():
        stmt = select(NewRole).order_by(NewRole.created_at.desc()).limit(20)
        result = await session.execute(stmt)
        roles = result.scalars().all()

        if not roles:
            return {"candidates": []}

        return {
            "candidates": [
                {
                    "id": str(r.id),
                    "title": r.role_name,
                    "source": r.source or "pipeline",
                    "discoveredAt": r.created_at.isoformat() if r.created_at else None,
                    "confidence": r.required_skills_confidence or 0.5,
                    "status": r.status or "pending_review",
                    "debatePoints": {"pro": [], "con": []},
                    "skillOverlap": 0,
                }
                for r in roles
            ]
        }


@router.get("/diagnose")
async def list_diagnoses():
    """获取 JD 诊断历史。优先 T6（前 50 条）；空则返回空列表（前端 Silent Fallback 用 demo）。"""
    try:
        rows = await get_quality_diagnoses(limit=50)
    except Exception:
        rows = []
    if not rows:
        return {"diagnoses": []}

    # T6 → 前端 JDDiagnosis[] 形状（inflated_items→redundantKeywords 近似，missingKeywords 暂空）
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


@router.get("/team/gaps")
async def list_team_gaps():
    """获取团队技能缺口。前端 GET /api/enterprise/team/gaps。"""
    # 从 skill_stats 中取 Top 缺口技能
    async for session in get_session():
        stmt = select(SkillStat).order_by(SkillStat.emergence.desc()).limit(10)
        result = await session.execute(stmt)
        stats = result.scalars().all()

        return {
            "gaps": [
                {
                    "skillName": s.skill_name,
                    "requiredLevel": "advanced",
                    "currentAvg": max(0, 100 - int(s.emergence * 10)),
                    "gap": int(s.emergence * 10),
                    "affectedPositions": s.required_count,
                    "priority": "high" if s.emergence > 2 else "medium" if s.emergence > 1 else "low",
                }
                for s in stats
            ]
        }


@router.get("/positions/{position_id:path}/evolution")
async def get_position_evolution(position_id: str):
    """获取岗位演化时间轴。`:path` 放行含 `/` 的岗位名（如 C/C++、法务专员/助理）。
    命中 T3 → 月桶时间线（薪资/需求/技能）；否则回退 EvolutionRecord。
    前端 GET /api/enterprise/positions/:id/evolution。"""
    try:
        buckets = await get_t3_evolution(position_id)
    except Exception:
        buckets = []
    if buckets:
        max_count = max(b["jd_count"] for b in buckets) or 1
        total = sum(b["jd_count"] for b in buckets) or 1
        # T4 技能快照（title 级，月桶间一致）
        skills_snapshot = []
        try:
            for s in await get_position_skills(position_id, limit=12):
                skills_snapshot.append({
                    "name": s["skill_name"],
                    "level": s["level"],
                    "weight": s["weight"],
                    "freshness": round(100 * s["confidence"]),
                    "change": "unchanged",
                })
        except Exception:
            pass
        tools = [s["name"] for s in skills_snapshot[:5]]

        timeline = []
        for b in buckets:
            month = b["month_key"]
            label = f"{int(month)}月" if month != "00" else "未标注日期"
            sal = salary_range(b)
            demand = min(100, round(b["jd_count"] / max_count * 100))
            timeline.append({
                "date": month if month != "00" else "00",
                "label": label,
                "marketDemand": demand,
                "matchRate": 0,
                "salaryRange": sal,
                "adoptionRate": demand,
                "tools": tools,
                "marketContext": (
                    f"采样窗口内 {label} 该岗位 JD 需求 {b['jd_count']} 条"
                    f"（占采样 {round(b['jd_count'] / total * 100)}%），月薪中位 {sal}。"
                ),
                "industryEvents": [],
                "typicalProjects": [],
                "skills": skills_snapshot,
                "dataSources": [f"JD采样×{b['jd_count']}"],
                "summary": f"采样窗口 {label}：JD 需求 {b['jd_count']} 条 · 月薪中位 {sal}",
            })

        return {
            "positionId": position_id,
            "positionName": position_id,
            "timeline": timeline,
        }

    async for session in get_session():
        stmt = select(EvolutionRecord).where(
            EvolutionRecord.position_id == position_id
        ).order_by(EvolutionRecord.created_at)
        result = await session.execute(stmt)
        records = result.scalars().all()

        if not records:
            return {
                "positionId": position_id,
                "positionName": position_id,
                "timeline": [],
            }

        timeline = []
        for r in records:
            timeline.append({
                "date": r.created_at.strftime("%YQ") + str((r.created_at.month - 1) // 3 + 1) if r.created_at else "",
                "label": f"{r.change_type}: {r.skill_name}",
                "marketDemand": 0,
                "matchRate": 0,
                "salaryRange": "",
                "adoptionRate": 0,
                "tools": [],
                "marketContext": r.summary if hasattr(r, 'summary') and r.summary else "",
                "industryEvents": [],
                "typicalProjects": [],
                "skills": [{"name": r.skill_name, "change": r.change_type, "changeReason": ""}],
                "dataSources": [],
                "summary": r.summary if hasattr(r, 'summary') and r.summary else f"{r.change_type} {r.skill_name}",
            })

        return {
            "positionId": position_id,
            "positionName": position_id,
            "timeline": timeline,
        }


# ══════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════

def _level_from_confidence(conf: float) -> str:
    if conf >= 0.8:
        return "expert"
    elif conf >= 0.6:
        return "advanced"
    elif conf >= 0.4:
        return "intermediate"
    return "basic"


def _trend_from_emergence(em: float) -> str:
    if em > 1.5:
        return "rising"
    elif em < 0:
        return "declining"
    return "stable"
