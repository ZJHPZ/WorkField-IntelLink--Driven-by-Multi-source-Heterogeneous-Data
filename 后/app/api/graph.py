"""图谱 API —— 全图谱数据 + 快照管理 + diff。

GET /api/graph          → 全图谱（AntV G6 格式）
GET /api/graph/snapshots → 快照列表
GET /api/graph/snapshots/{id} → 快照详情
GET /api/graph/snapshots/diff  → 两快照对比

数据来源：MySQL zhiyv 库（graph_snapshots 表），回退到 graph.json 文件。
"""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException, Query

from app.graph.repository import get_full_graph

router = APIRouter(prefix="/graph", tags=["图谱"])

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "snapshots")


@router.get("")
async def get_graph():
    """返回全图谱数据（nodes + edges → AntV G6）。

    优先从 MySQL graph_snapshots 读取，失败时回退到 graph.json 文件。
    """
    try:
        data = await get_full_graph()
        if data.get("nodes"):
            return {"status": "ok", **data}
    except Exception as e:
        pass

    # 最终回退
    graph_path = os.path.join(os.path.dirname(__file__), "..", "output", "graph.json")
    if os.path.exists(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"status": "ok", "source": "json_file", **data}

    raise HTTPException(status_code=404, detail="图谱数据不存在，请先运行 pipeline")


@router.get("/snapshots")
async def list_snapshots():
    """返回快照列表。从 MySQL graph_snapshots 表读取。"""
    try:
        from app.persistence.database import get_session
        from app.persistence.zhiyv_models import GraphSnapshot
        from sqlalchemy import select

        async for session in get_session():
            stmt = select(GraphSnapshot).order_by(GraphSnapshot.timestamp.desc())
            result = await session.execute(stmt)
            snapshots = [
                {
                    "snapshot_id": s.snapshot_id,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                    "description": s.description,
                    "node_count": s.node_count,
                    "edge_count": s.edge_count,
                }
                for s in result.scalars().all()
            ]
            return {"snapshots": snapshots, "total": len(snapshots)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询快照失败: {e}")


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: str):
    """返回指定快照详情。"""
    try:
        from app.persistence.database import get_session
        from app.persistence.zhiyv_models import GraphSnapshot
        from sqlalchemy import select

        async for session in get_session():
            stmt = select(GraphSnapshot).where(GraphSnapshot.snapshot_id == snapshot_id)
            result = await session.execute(stmt)
            snap = result.scalar_one_or_none()
            if not snap:
                raise HTTPException(status_code=404, detail=f"快照 {snapshot_id} 不存在")

            graph_data = json.loads(snap.graph_data) if isinstance(snap.graph_data, str) else snap.graph_data
            return {
                "snapshot_id": snap.snapshot_id,
                "timestamp": snap.timestamp.isoformat() if snap.timestamp else None,
                "description": snap.description,
                "node_count": snap.node_count,
                "edge_count": snap.edge_count,
                "graph_data": graph_data,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@router.get("/snapshots/diff")
async def diff_snapshots(old: str = Query(...), new: str = Query(...)):
    """对比两个快照的差异（增/删/改三态）。"""
    from app.pipeline.l4_snapshot import SnapshotManager

    # 从 MySQL 加载快照数据并转为 Snapshot 对象
    from app.persistence.database import get_session
    from app.persistence.zhiyv_models import GraphSnapshot as GraphSnapshotModel
    from sqlalchemy import select

    async for session in get_session():
        old_stmt = select(GraphSnapshotModel).where(GraphSnapshotModel.snapshot_id == old)
        new_stmt = select(GraphSnapshotModel).where(GraphSnapshotModel.snapshot_id == new)

        old_result = await session.execute(old_stmt)
        new_result = await session.execute(new_stmt)

        old_snap = old_result.scalar_one_or_none()
        new_snap = new_result.scalar_one_or_none()

        if not old_snap:
            raise HTTPException(status_code=404, detail=f"旧快照 {old} 不存在")
        if not new_snap:
            raise HTTPException(status_code=404, detail=f"新快照 {new} 不存在")

        # 使用 SnapshotManager 做 diff
        mgr = SnapshotManager(storage_dir=SNAPSHOT_DIR)

        from app.pipeline.l4_snapshot import Snapshot
        old_obj = Snapshot(
            snapshot_id=old_snap.snapshot_id,
            timestamp=old_snap.timestamp,
            description=old_snap.description or "",
            graph_data=json.loads(old_snap.graph_data) if isinstance(old_snap.graph_data, str) else old_snap.graph_data,
        )
        new_obj = Snapshot(
            snapshot_id=new_snap.snapshot_id,
            timestamp=new_snap.timestamp,
            description=new_snap.description or "",
            graph_data=json.loads(new_snap.graph_data) if isinstance(new_snap.graph_data, str) else new_snap.graph_data,
        )

        diff = mgr.diff_snapshots(old_obj, new_obj)
        return {
            "snapshot_old": diff.snapshot_old,
            "snapshot_new": diff.snapshot_new,
            "timestamp_old": diff.timestamp_old,
            "timestamp_new": diff.timestamp_new,
            "added_skills": diff.added_skills,
            "removed_skills": diff.removed_skills,
            "modified_skills": diff.modified_skills,
            "added_relations": diff.added_relations,
            "removed_relations": diff.removed_relations,
            "summary": diff.summary(),
        }
