"""通用仓库 —— PostgreSQL CRUD 操作。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import (
    JDDocument,
    EvidenceLog,
    EvolutionChangelog,
    EvalResult,
)


async def upsert_jd(session: AsyncSession, jd_id: str, title: str,
                    source: str, tech_stack: str, posted_date: str,
                    full_text: str, structured_fields: dict | None = None,
                    meta: dict | None = None) -> JDDocument:
    """插入或更新 JD 文档。"""
    result = await session.execute(
        select(JDDocument).where(JDDocument.jd_id == jd_id)
    )
    doc = result.scalar_one_or_none()
    if doc:
        doc.title = title
        doc.full_text = full_text
        doc.structured_fields = structured_fields
    else:
        doc = JDDocument(
            jd_id=jd_id, title=title, source=source,
            tech_stack=tech_stack, posted_date=posted_date,
            full_text=full_text, structured_fields=structured_fields, meta=meta,
        )
        session.add(doc)
    await session.commit()
    return doc


async def save_evidence_logs(session: AsyncSession, logs: list[dict]) -> None:
    """批量保存证据日志。"""
    for log in logs:
        session.add(EvidenceLog(
            jd_id=log["jd_id"],
            skill_name=log["skill_name"],
            skill_canonical=log.get("skill_canonical", log["skill_name"]),
            evidence_text=log.get("evidence_text", ""),
            source_type=log.get("source_type", "jd"),
            required_type=log.get("required_type", "必备"),
            extraction_method=log.get("extraction_method", "rule"),
            gate_verdict=log.get("gate_verdict", "passed"),
            gate_reason=log.get("gate_reason"),
        ))
    await session.commit()


async def save_changelog(session: AsyncSession, entries: list[dict]) -> None:
    """批量保存演化变更日志。"""
    for entry in entries:
        session.add(EvolutionChangelog(
            position_id=entry["position_id"],
            position_name=entry["position_name"],
            snapshot_old=entry["snapshot_old"],
            snapshot_new=entry["snapshot_new"],
            change_type=entry["change_type"],
            skill_name=entry["skill_name"],
            detail=entry.get("detail"),
            data_source=entry.get("data_source", ""),
            manual_optimized=entry.get("manual_optimized", False),
        ))
    await session.commit()


async def save_eval_result(session: AsyncSession, metric_name: str,
                           precision: float, recall: float, f1: float,
                           detail: dict | None = None) -> None:
    """保存一次评测结果。"""
    session.add(EvalResult(
        metric_name=metric_name,
        precision=precision, recall=recall, f1=f1, detail=detail,
    ))
    await session.commit()


async def count_jd(session: AsyncSession) -> int:
    """统计 JD 数量。"""
    result = await session.execute(select(func.count()).select_from(JDDocument))
    return result.scalar() or 0
