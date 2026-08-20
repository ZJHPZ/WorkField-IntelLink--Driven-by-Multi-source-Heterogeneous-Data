"""岗位 API —— 岗位列表 + 详情 + 演化时间轴。

GET  /api/positions               → 岗位列表
GET  /api/positions/{id}          → 岗位详情 + 技能雷达
GET  /api/positions/{id}/evolution → 岗位演化时间轴

数据来源：MySQL zhiyv 库（verified_skills + skill_stats + graph_snapshots）。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.graph.repository import get_positions, get_position_detail

router = APIRouter(prefix="/positions", tags=["岗位"])


@router.get("")
async def list_positions(type: str | None = None):
    """岗位列表。可选过滤 type=新兴|既有。"""
    try:
        positions = await get_positions(type)
        return {"positions": positions, "total": len(positions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@router.get("/{position_id}")
async def get_position(position_id: str):
    """岗位详情 + 关联技能 + 证据链。"""
    try:
        detail = await get_position_detail(position_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")
    if not detail:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return detail


@router.get("/{position_id}/evolution")
async def get_position_evolution(position_id: str):
    """岗位演化时间轴 —— 各快照的技能变化。"""
    from app.services.evolution_service import get_evolution_timeline
    result = get_evolution_timeline(position_id)
    return {"status": "ok", **result}
