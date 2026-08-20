"""L4 图谱构建 —— 将 pipeline 产物写入 MySQL。

设计方案 §5：
- 节点：Position / Skill / TechStack / Evidence
- 关系：REQUIRES / BELONGS_TO / CO_OCCURS / SUPPORTED_BY / IN_STACK
- 存储：MySQL zhiyv 库（graph_snapshots + skill_stats + verified_skills + skill_cooccurrence）
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from app.domain import (
    SkillStat,
)

logger = logging.getLogger(__name__)


async def build_graph(
    positions: list[dict],
    skill_stats: dict[str, SkillStat],
    evidences: list[dict],
    cooccurrence: dict | None = None,
    skill_metrics: dict | None = None,
) -> dict:
    """将 pipeline 产物写入 MySQL（skill_stats + verified_skills + skill_cooccurrence + graph_snapshots）。

    Args:
        positions: [{jd_id, title, tech_stack, skills: [ExtractedSkill]}]
        skill_stats: {规范名: SkillStat}
        evidences: [{evidence_id, jd_id, text, skill_name}]
        cooccurrence: {(skill_a, skill_b): strength}
        skill_metrics: {规范名: DynamicMetrics}

    Returns:
        构建统计 {nodes, edges}
    """
    from app.graph.repository import upsert_skill, link_requires

    node_count = 0
    edge_count = 0

    # ── 1. 写入技能统计（全字段） ──
    for name, stat in skill_stats.items():
        metrics = skill_metrics.get(name) if skill_metrics else None
        status = "confirmed" if stat.confidence >= 0.55 else "candidate"
        tech_stack = stat.tech_stacks[0] if stat.tech_stacks else ""

        await upsert_skill(
            skill_name=name,
            confidence=stat.confidence,
            status=status,
            tech_stack=tech_stack,
            df=stat.df,
            required_count=stat.required_count,
            bonus_count=stat.bonus_count,
            emergence=metrics.emergence if metrics else 0.0,
            decline=metrics.decline if metrics else 0.0,
            volatility=metrics.volatility if metrics else 0.0,
            half_life=metrics.half_life if metrics else None,
            source_score=stat.source_score if hasattr(stat, 'source_score') else stat.confidence,
            verification_status=stat.verification_status,
        )
        node_count += 1

    # ── 2. 写入岗位-技能关联 ──
    for p in positions:
        pid = p["jd_id"]
        for sk in p["skills"]:
            sk_name = sk.name if hasattr(sk, 'name') else sk.get("name", "")
            req_type = sk.required_type if hasattr(sk, 'required_type') else sk.get("required_type", "必备")
            conf = skill_stats.get(sk_name, SkillStat(name=sk_name)).confidence if skill_stats else 0.0

            await link_requires(
                position_id=pid,
                skill_name=sk_name,
                required_type=req_type,
                confidence=conf,
            )
            edge_count += 1

    # ── 3. 写入共现关系 ──
    if cooccurrence:
        await _save_cooccurrence(cooccurrence)
        edge_count += len(cooccurrence)

    # ── 4. 生成并保存图谱快照到 MySQL ──
    graph_json = build_graph_json(positions, skill_stats, evidences,
                                  cooccurrence=cooccurrence,
                                  skill_metrics=skill_metrics)
    await _save_graph_snapshot(graph_json, description=f"Pipeline: {len(positions)} positions")
    node_count += len(graph_json["nodes"])

    logger.info(f"图谱构建完成：{node_count} 节点, {edge_count} 关系")
    return {"nodes": node_count, "edges": edge_count}


async def _save_cooccurrence(cooccurrence: dict) -> None:
    """保存技能共现关系到 MySQL。"""
    from app.persistence.database import get_session
    from app.persistence.zhiyv_models import SkillCooccurrence
    from sqlalchemy import select

    async for session in get_session():
        for (sk_a, sk_b), strength in cooccurrence.items():
            if sk_a == sk_b:
                continue
            # 检查是否已存在
            stmt = select(SkillCooccurrence).where(
                SkillCooccurrence.skill_a == sk_a,
                SkillCooccurrence.skill_b == sk_b,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.count += 1
                existing.strength = strength
            else:
                session.add(SkillCooccurrence(
                    skill_a=sk_a,
                    skill_b=sk_b,
                    count=1,
                    strength=strength,
                ))

        await session.commit()


async def _save_graph_snapshot(graph_data: dict, description: str = "") -> None:
    """保存图谱快照到 MySQL graph_snapshots 表。"""
    from app.persistence.database import get_session
    from app.persistence.zhiyv_models import GraphSnapshot
    import uuid

    snap_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    async for session in get_session():
        snap = GraphSnapshot(
            snapshot_id=snap_id,
            timestamp=datetime.now(),
            description=description,
            node_count=len(graph_data.get("nodes", [])),
            edge_count=len(graph_data.get("edges", [])),
            graph_data=json.dumps(graph_data, ensure_ascii=False),
        )
        session.add(snap)
        await session.commit()
        logger.info(f"图谱快照已保存: {snap_id}")


def build_graph_json(
    positions: list[dict],
    skill_stats: dict[str, SkillStat],
    evidences: list[dict],
    cooccurrence: dict | None = None,
    skill_metrics: dict | None = None,
) -> dict:
    """构建图谱并输出为 AntV G6 JSON 格式。"""
    now = datetime.now().isoformat()
    nodes: list[dict] = []
    edges: list[dict] = []
    edge_id = 0

    # TechStack 节点
    for ts in {p["tech_stack"] for p in positions}:
        nodes.append({"id": f"stack::{ts}", "data": {"nodeType": "TechStack", "label": ts}})

    # Skill 节点
    for name, stat in skill_stats.items():
        sid = f"skill::{name}"
        if stat.verification_status == "unverified":
            status = "pending"
        elif stat.verification_status == "candidate":
            status = "candidate"
        elif stat.confidence >= 0.55:
            status = "confirmed"
        else:
            status = "candidate"

        metrics = skill_metrics.get(name) if skill_metrics else None
        nodes.append({"id": sid, "data": {
            "nodeType": "Skill", "label": name,
            "df": stat.df, "confidence": stat.confidence,
            "required_count": stat.required_count, "bonus_count": stat.bonus_count,
            "verification_status": stat.verification_status, "status": status,
            "emergence": metrics.emergence if metrics else 0,
            "decline": metrics.decline if metrics else 0,
            "half_life": metrics.half_life if metrics else None,
            "volatility": metrics.volatility if metrics else 0,
            "valid_from": now,
        }})
        for ts in stat.tech_stacks:
            edges.append({"id": f"e{edge_id}", "source": sid, "target": f"stack::{ts}",
                          "data": {"rel": "BELONGS_TO"}})
            edge_id += 1

    # CO_OCCURS 关系
    if cooccurrence:
        for (sk_a, sk_b), strength in cooccurrence.items():
            edges.append({"id": f"e{edge_id}", "source": f"skill::{sk_a}",
                          "target": f"skill::{sk_b}",
                          "data": {"rel": "CO_OCCURS", "strength": strength, "valid_from": now}})
            edge_id += 1

    # Evidence 节点 + SUPPORTED_BY
    for ev in evidences:
        eid = f"ev::{ev.get('eid', ev.get('evidence_id'))}"
        nodes.append({"id": eid, "data": {
            "nodeType": "Evidence", "label": (ev.get("text", "") or "")[:30],
            "jd_id": ev.get("jd_id", ""), "text": ev.get("text", ""),
            "source": ev.get("source", "jd"), "timestamp": ev.get("timestamp", now),
        }})
        canon = ev.get("skill", ev.get("skill_name", ""))
        if canon:
            edges.append({"id": f"e{edge_id}", "source": f"skill::{canon}", "target": eid,
                          "data": {"rel": "SUPPORTED_BY", "valid_from": now}})
            edge_id += 1

    # Position 节点 + REQUIRES + IN_STACK
    for p in positions:
        pid = f"pos::{p['jd_id']}"
        title_lower = p["title"].lower()
        is_emerging = any(kw in title_lower for kw in ["ai", "智能", "大模型", "rag", "新"])
        nodes.append({"id": pid, "data": {
            "nodeType": "Position", "label": p["title"],
            "tech_stack": p["tech_stack"],
            "position_type": "新兴" if is_emerging else "既有",
            "confidence": 0.8, "first_seen": now,
        }})
        edges.append({"id": f"e{edge_id}", "source": pid,
                      "target": f"stack::{p['tech_stack']}", "data": {"rel": "IN_STACK"}})
        edge_id += 1
        for sk in p["skills"]:
            name = sk.name if hasattr(sk, 'name') else sk.get("name", "")
            sid = f"skill::{name}"
            edges.append({"id": f"e{edge_id}", "source": pid, "target": sid, "data": {
                "rel": "REQUIRES",
                "required_type": sk.required_type if hasattr(sk, 'required_type') else sk.get("required_type", "必备"),
                "valid_from": now,
            }})
            edge_id += 1

    logger.info(f"图谱JSON构建：{len(nodes)} 节点, {len(edges)} 关系")
    return {"nodes": nodes, "edges": edges}
