"""图谱 CRUD 仓库 —— 基于 MySQL (zhiyv 数据库)。

替代原 Neo4j Cypher 查询，提供相同的对外接口。
数据来源：skill_stats / verified_skills / skill_cooccurrence / graph_snapshots。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select, func, text

from app.persistence.database import get_session
from app.persistence.zhiyv_models import (
    SkillStat, VerifiedSkill, SkillCooccurrence, GraphSnapshot,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 查询 —— 对外接口保持不变
# ══════════════════════════════════════════════

async def get_full_graph() -> dict:
    """获取全图谱数据（AntV G6 格式）。

    优先从 graph_snapshots 表读取最新快照，失败时回退到 graph.json 文件。
    """
    # 1) 从 MySQL 读取最新快照
    try:
        async for session in get_session():
            stmt = (
                select(GraphSnapshot)
                .order_by(GraphSnapshot.timestamp.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            snap = result.scalar_one_or_none()
            if snap and snap.graph_data:
                data = json.loads(snap.graph_data) if isinstance(snap.graph_data, str) else snap.graph_data
                if data.get("nodes"):
                    return {"source": "mysql", **data}
    except Exception as e:
        logger.warning(f"MySQL 读取图谱快照失败: {e}")

    # 2) 回退到 JSON 文件
    import os
    graph_path = os.path.join(os.path.dirname(__file__), "..", "output", "graph.json")
    if os.path.exists(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"source": "json_file", **data}

    return {"nodes": [], "edges": [], "source": "empty"}


async def get_positions(position_type: str | None = None) -> list[dict]:
    """查询岗位列表。

    从 verified_skills 表提取不重复的 jd_id/jd_title 作为岗位。
    position_type 过滤基于关联技能的平均 emergence 计算。
    """
    async for session in get_session():
        # 获取所有不重复的岗位 (jd_id, jd_title)
        stmt = (
            select(
                VerifiedSkill.jd_id,
                VerifiedSkill.jd_title,
                func.group_concat(VerifiedSkill.tech_stack.distinct()).label("tech_stacks"),
            )
            .group_by(VerifiedSkill.jd_id, VerifiedSkill.jd_title)
        )
        result = await session.execute(stmt)
        rows = result.all()

        positions = []
        for row in rows:
            jd_id = row.jd_id
            jd_title = row.jd_title or jd_id
            tech_stacks = row.tech_stacks or ""

            # 获取该岗位的技能，计算平均 emergence
            skill_stmt = (
                select(VerifiedSkill.skill_name)
                .where(VerifiedSkill.jd_id == jd_id)
            )
            skill_result = await session.execute(skill_stmt)
            skill_names = [r[0] for r in skill_result.all()]

            avg_emergence = 0.0
            if skill_names:
                stats_stmt = (
                    select(func.avg(SkillStat.emergence))
                    .where(SkillStat.skill_name.in_(skill_names))
                )
                stats_result = await session.execute(stats_stmt)
                avg_emergence = stats_result.scalar() or 0.0

            # 推断岗位类型
            pos_type = "新兴" if avg_emergence > 1.0 else "既有"

            # 如果有过滤条件，不匹配则跳过
            if position_type and pos_type != position_type:
                continue

            positions.append({
                "position_id": jd_id,
                "name": jd_title,
                "tech_stack": tech_stacks.split(",")[0] if tech_stacks else "",
                "position_type": pos_type,
                "confidence": 0.8,
                "skill_count": len(skill_names),
                "avg_emergence": round(avg_emergence, 4),
            })

        return positions


async def get_position_detail(position_id: str) -> dict | None:
    """查询岗位详情 + 关联技能。

    position_id 对应 verified_skills.jd_id。
    返回格式保持与原 Neo4j 版本兼容。
    """
    async for session in get_session():
        # 查询岗位基本信息（从第一条 verified_skill 获取标题）
        pos_stmt = (
            select(VerifiedSkill)
            .where(VerifiedSkill.jd_id == position_id)
            .limit(1)
        )
        pos_result = await session.execute(pos_stmt)
        pos_row = pos_result.scalar_one_or_none()
        if not pos_row:
            return None

        # 查询该岗位的所有技能
        skills_stmt = (
            select(VerifiedSkill)
            .where(VerifiedSkill.jd_id == position_id)
        )
        skills_result = await session.execute(skills_stmt)
        verified_skills = skills_result.scalars().all()

        # 关联 skill_stats 获取指标
        skill_names = [s.skill_name for s in verified_skills]
        stats_map = {}
        if skill_names:
            stats_stmt = select(SkillStat).where(SkillStat.skill_name.in_(skill_names))
            stats_result = await session.execute(stats_stmt)
            for stat in stats_result.scalars().all():
                stats_map[stat.skill_name] = stat

        # 组装返回数据 —— 兼容原 Neo4j 格式
        position = {
            "position_id": position_id,
            "name": pos_row.jd_title or position_id,
            "tech_stack": pos_row.tech_stack or "",
            "status": "confirmed",
        }

        skills = []
        for vs in verified_skills:
            stat = stats_map.get(vs.skill_name)
            skill_data = {
                "skill": {
                    "skill_id": f"skill::{vs.skill_name}",
                    "name": vs.skill_name,
                    "category": vs.tech_stack or "",
                    "confidence": stat.confidence if stat else 0.0,
                    "status": stat.status if stat else "candidate",
                    "emergence": stat.emergence if stat else 0.0,
                    "decline": stat.decline if stat else 0.0,
                    "half_life": stat.half_life if stat else None,
                    "volatility": stat.volatility if stat else 0.0,
                },
                "rel": {
                    "required_type": vs.required_type,
                    "confidence": stat.confidence if stat else 0.0,
                },
                "evidences": [{"text": vs.evidence, "source": vs.source}] if vs.evidence else [],
            }
            skills.append(skill_data)

        return {"position": position, "skills": skills}


async def get_skill_stats(skill_name: str) -> dict | None:
    """获取单个技能的统计信息。"""
    async for session in get_session():
        stmt = select(SkillStat).where(SkillStat.skill_name == skill_name)
        result = await session.execute(stmt)
        stat = result.scalar_one_or_none()
        if not stat:
            return None
        return {
            "skill_name": stat.skill_name,
            "df": stat.df,
            "confidence": stat.confidence,
            "emergence": stat.emergence,
            "decline": stat.decline,
            "half_life": stat.half_life,
            "volatility": stat.volatility,
            "status": stat.status,
            "source_score": stat.source_score,
        }


async def get_all_skill_stats() -> list[dict]:
    """获取所有技能统计。"""
    async for session in get_session():
        stmt = select(SkillStat).order_by(SkillStat.confidence.desc())
        result = await session.execute(stmt)
        return [
            {
                "skill_name": s.skill_name,
                "df": s.df,
                "confidence": s.confidence,
                "emergence": s.emergence,
                "decline": s.decline,
                "half_life": s.half_life,
                "status": s.status,
            }
            for s in result.scalars().all()
        ]


# ══════════════════════════════════════════════
# 写入 —— 企业侧岗位标准管理
# ══════════════════════════════════════════════

async def upsert_skill(skill_name: str, confidence: float = 0.8,
                       status: str = "confirmed", tech_stack: str = "",
                       df: int = 0, required_count: int = 0, bonus_count: int = 0,
                       emergence: float = 0.0, decline: float = 0.0,
                       volatility: float = 0.0, half_life: float | None = None,
                       source_score: float = 0.0,
                       verification_status: str = "unverified") -> None:
    """创建或更新技能统计（全字段写入）。"""
    async for session in get_session():
        stmt = select(SkillStat).where(SkillStat.skill_name == skill_name)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.confidence = confidence
            existing.status = status
            existing.df = df
            existing.required_count = required_count
            existing.bonus_count = bonus_count
            existing.emergence = emergence
            existing.decline = decline
            existing.volatility = volatility
            existing.half_life = half_life
            existing.source_score = source_score
            existing.verification_status = verification_status
            if tech_stack and tech_stack not in (existing.tech_stacks or []):
                existing.tech_stacks = (existing.tech_stacks or []) + [tech_stack]
            existing.updated_at = datetime.now()
        else:
            new_stat = SkillStat(
                skill_name=skill_name,
                confidence=confidence,
                status=status,
                df=df,
                required_count=required_count,
                bonus_count=bonus_count,
                emergence=emergence,
                decline=decline,
                volatility=volatility,
                half_life=half_life,
                source_score=source_score or confidence,
                verification_status=verification_status,
                tech_stacks=[tech_stack] if tech_stack else [],
            )
            session.add(new_stat)

        await session.commit()


async def link_requires(position_id: str, skill_name: str,
                        required_type: str = "必备",
                        confidence: float = 0.8) -> None:
    """创建岗位-技能关联（写入 verified_skills）。"""
    async for session in get_session():
        # 检查是否已存在
        stmt = select(VerifiedSkill).where(
            VerifiedSkill.jd_id == position_id,
            VerifiedSkill.skill_name == skill_name,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.required_type = required_type
        else:
            new_vs = VerifiedSkill(
                jd_id=position_id,
                skill_name=skill_name,
                required_type=required_type,
                evidence="手动添加",
                source="manual",
            )
            session.add(new_vs)

        await session.commit()
