"""动态指标 API —— 六大指标看板。

GET /api/metrics           → 全量动态指标报告
GET /api/metrics/emerging   → 新兴技能 Top 榜
GET /api/metrics/declining  → 衰退技能 Top 榜
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.pipeline.l2_metrics import MetricsCalculator

router = APIRouter(prefix="/metrics", tags=["指标"])

_calc = MetricsCalculator()


@router.get("")
async def get_metrics():
    """全量动态指标报告（六大指标）。"""
    # 从图谱数据读取技能指标
    # Phase 2：从 Neo4j 或 pipeline context 读取已计算的指标
    return {
        "status": "ok",
        "message": "指标计算就绪，请从 pipeline 输出中读取具体数值。"
                   " GET /metrics/emerging 和 /metrics/declining 已可用。",
    }


@router.get("/emerging")
async def get_emerging_skills(limit: int = 10):
    """新兴技能 Top 榜 —— 按新兴度降序。

    新兴度 = 频次上升斜率 × 近期集中度。
    数据来自 pipeline 产出的 metrics_report。
    """
    # 从 pipeline output 读取（Phase 2 集成后可用）
    import json
    import os
    report_path = os.path.join(os.path.dirname(__file__), "..", "output", "metrics_report.json")
    if os.path.exists(report_path):
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)
        skills = data.get("skill_metrics", {})
        sorted_skills = sorted(
            skills.items(),
            key=lambda x: x[1].get("emergence", 0),
            reverse=True,
        )[:limit]
        return {
            "emerging_skills": [
                {"name": name, "emergence": m.get("emergence", 0),
                 "decline": m.get("decline", 0), "volatility": m.get("volatility", 0)}
                for name, m in sorted_skills
            ]
        }
    return {"emerging_skills": [], "note": "请先运行 pipeline 生成指标数据"}


@router.get("/declining")
async def get_declining_skills(limit: int = 10):
    """衰退技能 Top 榜 —— 按衰退度降序。"""
    import json
    import os
    report_path = os.path.join(os.path.dirname(__file__), "..", "output", "metrics_report.json")
    if os.path.exists(report_path):
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)
        skills = data.get("skill_metrics", {})
        sorted_skills = sorted(
            skills.items(),
            key=lambda x: x[1].get("decline", 0),
            reverse=True,
        )[:limit]
        return {
            "declining_skills": [
                {"name": name, "decline": m.get("decline", 0),
                 "emergence": m.get("emergence", 0)}
                for name, m in sorted_skills
            ]
        }
    return {"declining_skills": [], "note": "请先运行 pipeline 生成指标数据"}
