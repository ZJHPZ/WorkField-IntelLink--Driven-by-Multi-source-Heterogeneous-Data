"""岗位 API —— 岗位列表 + 详情 + 演化时间轴。

GET  /api/positions               → 岗位列表
GET  /api/positions/{id}          → 岗位详情 + 技能雷达
GET  /api/positions/{id}/evolution → 岗位演化时间轴

数据来源：MySQL zhiyv 库。优先读 T1–T4 派生表（jd_records 二次加工）；
T 表为空或查询失败时回退 verified_skills + skill_stats 旧路径（保证测试与旧行为不破）。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.graph.repository import get_positions, get_position_detail
from app.services.jd_service import (
    classify_position_types,
    get_all_position_profiles,
    get_all_position_skills,
    get_position_evolution as get_t3_evolution,
    get_position_profile,
    get_position_skills,
    infer_tech_stack,
    salary_range,
)

router = APIRouter(prefix="/positions", tags=["岗位"])


@router.get("")
async def list_positions(type: str | None = None):
    """岗位列表。可选过滤 type=新兴|既有。优先 T1 岗位画像，空则回退。"""
    try:
        profiles = await get_all_position_profiles()
    except Exception:
        profiles = []
    if profiles:
        # T4 全量技能一次读出，按 title 分组（技能数 + 必备/加分列表）
        skills_by_title: dict[str, list[dict]] = {}
        try:
            for s in await get_all_position_skills():
                skills_by_title.setdefault(s["title"], []).append(s)
        except Exception:
            pass
        type_map = classify_position_types(profiles)
        positions = []
        for p in profiles:
            skills = sorted(
                skills_by_title.get(p["title"], []),
                key=lambda x: x["weight"], reverse=True,
            )
            positions.append({
                "position_id": p["title"],
                "name": p["title"],
                "tech_stack": infer_tech_stack(p["title"]),
                "position_type": type_map[p["title"]],
                "skill_count": len(skills),
                "city": (p["top_cities"][0]["city"] if p["top_cities"] else ""),
                "salary_range": salary_range(p),
                "jd_count": p["jd_count"],
                "top_companies": p["top_companies"],
                "top_cities": p["top_cities"],
                "required_skills": [s["skill_name"] for s in skills if s["required_type"] == "必备"][:8],
                "bonus_skills": [s["skill_name"] for s in skills if s["required_type"] != "必备"][:8],
            })
        if type:
            positions = [x for x in positions if x["position_type"] == type]
        return {"positions": positions, "total": len(positions)}

    try:
        positions = await get_positions(type)
        return {"positions": positions, "total": len(positions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@router.get("/{position_id}")
async def get_position(position_id: str):
    """岗位详情 + 关联技能 + 证据链。position_id 命中 T1.title → T1 画像 + T4 技能。"""
    try:
        profile = await get_position_profile(position_id)
    except Exception:
        profile = None
    if profile:
        try:
            skills = await get_position_skills(position_id, limit=100)
        except Exception:
            skills = []
        return {
            "position": {
                "position_id": position_id,
                "name": profile["title"],
                "tech_stack": infer_tech_stack(profile["title"]),
                "status": "confirmed",
                "jd_count": profile["jd_count"],
                "salary_range": salary_range(profile),
                "city": (profile["top_cities"][0]["city"] if profile["top_cities"] else ""),
                "top_cities": profile["top_cities"],
                "top_companies": profile["top_companies"],
            },
            "skills": [
                {
                    "skill": {
                        "skill_id": f"skill::{s['skill_name']}",
                        "name": s["skill_name"],
                        "category": infer_tech_stack(position_id),
                        "confidence": s["confidence"],
                        "status": "confirmed",
                        "emergence": 0.0,
                        "decline": 0.0,
                        "half_life": None,
                        "volatility": 0.0,
                    },
                    "rel": {
                        "required_type": s["required_type"],
                        "confidence": s["confidence"],
                    },
                    "evidences": [],
                }
                for s in skills
            ],
        }

    try:
        detail = await get_position_detail(position_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")
    if not detail:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return detail


@router.get("/{position_id:path}/evolution")
async def get_position_evolution(position_id: str):
    """岗位演化时间轴。`:path` 放行含 `/` 的岗位名（如 C/C++、法务专员/助理）。
    命中 T3.title → 按 month_key 返回月桶 timeline；否则回退快照对比。"""
    try:
        buckets = await get_t3_evolution(position_id)
    except Exception:
        buckets = []
    if buckets:
        total = sum(b["jd_count"] for b in buckets) or 1
        timeline = []
        for b in buckets:
            month = b["month_key"]
            label = f"{int(month)}月" if month != "00" else "未标注日期"
            sal = salary_range(b)
            summary = (
                f"{label} 采样窗口 JD 需求 {b['jd_count']} 条"
                f"（占 {round(b['jd_count'] / total * 100)}%），"
                + (f"月薪中位 {sal}" if sal else "无有效薪资数据")
            )
            timeline.append({
                "from": label,
                "to": label,
                "added_skills": [],
                "removed_skills": [],
                "modified_skills": [],
                "summary": summary,
            })
        return {
            "status": "ok",
            "position_id": position_id,
            "snapshot_count": len(timeline),
            "timeline": timeline,
        }

    from app.services.evolution_service import get_evolution_timeline
    result = get_evolution_timeline(position_id)
    return {"status": "ok", **result}
