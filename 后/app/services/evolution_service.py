"""演化分析服务 —— 岗位快照时间轴。

设计方案 §5.3 + 赛题要求②：
- 查询岗位所有快照 → 依次 diff → 返回时间轴
"""

from __future__ import annotations

import logging
import os

from app.pipeline.l4_snapshot import SnapshotManager

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "snapshots")


def get_evolution_timeline(position_id: str) -> dict:
    """获取岗位的演化时间轴。

    Args:
        position_id: 岗位 ID

    Returns:
        {position_id, snapshots: [...], timeline: [...]}
    """
    mgr = SnapshotManager(storage_dir=SNAPSHOT_DIR)
    snapshots = mgr.list_snapshots()

    if len(snapshots) < 2:
        return {
            "position_id": position_id,
            "snapshot_count": len(snapshots),
            "timeline": [],
            "note": "至少需要 2 个快照才能生成演化时间轴",
        }

    timeline = []
    for i in range(1, len(snapshots)):
        old = mgr.load_snapshot(snapshots[i - 1]["snapshot_id"])
        new = mgr.load_snapshot(snapshots[i]["snapshot_id"])
        if not old or not new:
            continue

        diff = mgr.diff_snapshots(old, new)

        # 筛选与该岗位相关的变更
        relevant_added = [s for s in diff.added_skills
                          if position_id in s or "pos::" in s or not s.startswith("skill::")]
        relevant_removed = [s for s in diff.removed_skills
                            if position_id in s or "pos::" in s or not s.startswith("skill::")]

        timeline.append({
            "from": diff.timestamp_old,
            "to": diff.timestamp_new,
            "added_skills": diff.added_skills,
            "removed_skills": diff.removed_skills,
            "modified_skills": diff.modified_skills,
            "summary": diff.summary(),
        })

    return {
        "position_id": position_id,
        "snapshot_count": len(snapshots),
        "timeline": timeline,
    }
