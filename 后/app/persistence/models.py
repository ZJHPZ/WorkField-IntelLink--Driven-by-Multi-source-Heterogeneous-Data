"""SQLAlchemy ORM 模型 —— PostgreSQL 表结构。

设计方案 §9 存储职责：
- JD 原文与证据 → jd_documents / evidence_log
- 演化更新说明 → evolution_changelog
- 评测结果 → eval_results
- 快照元数据（内容在 Neo4j）→ snapshots_meta
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.database import Base


class JDDocument(Base):
    """JD 原文存储（L1 清洗后的全文 + 元信息）。"""
    __tablename__ = "jd_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jd_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    source: Mapped[str] = mapped_column(String(32))
    tech_stack: Mapped[str] = mapped_column(String(64))
    posted_date: Mapped[str] = mapped_column(String(16))
    full_text: Mapped[str] = mapped_column(Text)
    structured_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class EvidenceLog(Base):
    """证据日志 —— 每条抽取技能的溯源记录。"""
    __tablename__ = "evidence_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jd_id: Mapped[str] = mapped_column(String(64), index=True)
    skill_name: Mapped[str] = mapped_column(String(128), index=True)
    skill_canonical: Mapped[str] = mapped_column(String(128))
    evidence_text: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32))
    required_type: Mapped[str] = mapped_column(String(16))
    extraction_method: Mapped[str] = mapped_column(String(16))  # spark / rule
    gate_verdict: Mapped[str] = mapped_column(String(16))        # passed / rejected
    gate_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class EvolutionChangelog(Base):
    """岗位演化变更日志 —— 设计方案要求②的"变更说明+数据源"。"""
    __tablename__ = "evolution_changelog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[str] = mapped_column(String(64), index=True)
    position_name: Mapped[str] = mapped_column(String(256))
    snapshot_old: Mapped[str] = mapped_column(String(64))
    snapshot_new: Mapped[str] = mapped_column(String(64))
    change_type: Mapped[str] = mapped_column(String(16))  # added / removed / modified
    skill_name: Mapped[str] = mapped_column(String(128))
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    data_source: Mapped[str] = mapped_column(String(256))  # 数据来源
    manual_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class EvalResult(Base):
    """评测结果记录 —— 三个 90% 指标的历次跑分。"""
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(64))  # jd_accuracy / resume_accuracy / match_accuracy
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    f1: Mapped[float] = mapped_column(Float)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
