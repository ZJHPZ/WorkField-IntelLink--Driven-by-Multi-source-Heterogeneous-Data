"""SQLAlchemy ORM 模型 —— zhiyv 数据库表结构。

包含图谱 pipeline 数据表 + 用户侧业务表。
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Float, Integer, String, Text, DateTime, Date, JSON, BigInteger, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.database import Base


class SkillStat(Base):
    """技能统计表 —— pipeline 产出的技能指标。对应 zhiyv.skill_stats。"""
    __tablename__ = "skill_stats"

    skill_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    df: Mapped[int] = mapped_column(Integer, default=0)
    jd_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_count: Mapped[int] = mapped_column(Integer, default=0)
    bonus_count: Mapped[int] = mapped_column(Integer, default=0)
    tech_stacks: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_evidences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    first_seen_months_ago: Mapped[int] = mapped_column(Integer, default=0)
    avg_inflation: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    source_score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default="candidate")
    verification_status: Mapped[str] = mapped_column(String(16), default="unverified")
    emergence: Mapped[float] = mapped_column(Float, default=0)
    decline: Mapped[float] = mapped_column(Float, default=0)
    volatility: Mapped[float] = mapped_column(Float, default=0)
    half_life: Mapped[float | None] = mapped_column(Float, nullable=True)
    half_life_method: Mapped[str] = mapped_column(String(32), default="")
    evolution_speed: Mapped[float] = mapped_column(Float, default=0)
    inflation_index: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class VerifiedSkill(Base):
    """已验证技能表 —— JD 中抽取并验证的技能。对应 zhiyv.verified_skills。"""
    __tablename__ = "verified_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    jd_id: Mapped[str] = mapped_column(String(64), index=True)
    jd_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    skill_name: Mapped[str] = mapped_column(String(128), index=True)
    tech_stack: Mapped[str | None] = mapped_column(String(64), nullable=True)
    required_type: Mapped[str] = mapped_column(String(16))
    evidence: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(16))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class SkillCooccurrence(Base):
    """技能共现表 —— 技能间的共现频率和强度。对应 zhiyv.skill_cooccurrence。"""
    __tablename__ = "skill_cooccurrence"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    skill_a: Mapped[str] = mapped_column(String(128), index=True)
    skill_b: Mapped[str] = mapped_column(String(128), index=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    strength: Mapped[float] = mapped_column(Float, default=0)


class GraphSnapshot(Base):
    """图谱快照表 —— 完整图谱 JSON 数据。对应 zhiyv.graph_snapshots。"""
    __tablename__ = "graph_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, default=0)
    graph_data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class NewRole(Base):
    """新发现岗位表。对应 zhiyv.new_roles。"""
    __tablename__ = "new_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(128))
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities_confidence: Mapped[float] = mapped_column(Float, default=0)
    responsibilities_evidence_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    responsibilities_source: Mapped[str] = mapped_column(String(16), default="rule")
    required_skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_skills_evidence_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_skills_confidence: Mapped[float] = mapped_column(Float, default=0)
    bonus_skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bonus_skills_evidence_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bonus_skills_confidence: Mapped[float] = mapped_column(Float, default=0)
    industries: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    industries_confidence: Mapped[float] = mapped_column(Float, default=0)
    industries_evidence_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    industries_source: Mapped[str] = mapped_column(String(16), default="rule")
    market_jd_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="pending_review")
    source: Mapped[str] = mapped_column(String(16), default="rule")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class EvolutionRecord(Base):
    """演化记录表。对应 zhiyv.evolution_records。"""
    __tablename__ = "evolution_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    position_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_old: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snapshot_new: Mapped[str | None] = mapped_column(String(64), nullable=True)
    change_type: Mapped[str] = mapped_column(String(16))
    skill_name: Mapped[str] = mapped_column(String(128))
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


# ══════════════════════════════════════════════
# 用户侧业务表
# ══════════════════════════════════════════════


class UserProfile(Base):
    """用户职业档案。对应 zhiyv.user_profiles。"""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(128), default="")
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="employed_looking")
    industry: Mapped[str] = mapped_column(String(64), default="")
    education: Mapped[str] = mapped_column(String(16), default="本科")
    major: Mapped[str] = mapped_column(String(128), default="")
    english_level: Mapped[str] = mapped_column(String(32), default="")
    experience_years: Mapped[str] = mapped_column(String(16), default="")
    city: Mapped[str] = mapped_column(String(64), default="")
    target_role: Mapped[str] = mapped_column(String(128), default="")
    target_city: Mapped[str] = mapped_column(String(64), default="")
    target_industry: Mapped[str] = mapped_column(String(64), default="")
    salary_min: Mapped[int] = mapped_column(Integer, default=0)
    salary_max: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String(32), default="tech_growth")
    travel_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    relocate_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    work_mode: Mapped[str] = mapped_column(String(16), default="any")
    resume_url: Mapped[str] = mapped_column(String(512), default="")
    resume_parsed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    avatar_emoji: Mapped[str] = mapped_column(String(16), default="👨‍💻")
    level: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class UserSkill(Base):
    """用户技能。对应 zhiyv.user_skills。"""
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    skill_name: Mapped[str] = mapped_column(String(128))
    canonical_name: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(32), default="编程语言")
    level: Mapped[str] = mapped_column(String(16), default="intermediate")
    market_demand: Mapped[int] = mapped_column(Integer, default=0)
    market_df: Mapped[int] = mapped_column(Integer, default=0)
    emergence: Mapped[float] = mapped_column(Float, default=0)
    decline: Mapped[float] = mapped_column(Float, default=0)
    freshness: Mapped[int] = mapped_column(Integer, default=100)
    years_of_experience: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)
    status: Mapped[str] = mapped_column(String(20), default="healthy")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class UserMatch(Base):
    """岗位匹配记录。对应 zhiyv.user_matches。"""
    __tablename__ = "user_matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    position_id: Mapped[str] = mapped_column(String(64), index=True)
    position_name: Mapped[str] = mapped_column(String(256), default="")
    company: Mapped[str] = mapped_column(String(128), default="")
    match_rate: Mapped[float] = mapped_column(Float, default=0)
    matched_skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    salary_range: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class LearningStepModel(Base):
    """学习路径步骤。对应 zhiyv.learning_steps。"""
    __tablename__ = "learning_steps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    match_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    skill: Mapped[str] = mapped_column(String(128), default="")
    resource: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="locked")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    prerequisites: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class CareerMilestone(Base):
    """职业里程碑。对应 zhiyv.career_milestones。"""
    __tablename__ = "career_milestones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512), default="")
    icon: Mapped[str] = mapped_column(String(16), default="🏆")
    rarity: Mapped[str] = mapped_column(String(16), default="COMMON")
    unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    target: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class GrowthTimeline(Base):
    """成长时间轴事件。对应 zhiyv.growth_timeline。"""
    __tablename__ = "growth_timeline"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    event_date: Mapped[str] = mapped_column(String(16), default="")
    skills_gained: Mapped[int] = mapped_column(Integer, default=0)
    skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cumulative_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class AIInsight(Base):
    """AI 分析洞察。对应 zhiyv.ai_insights。"""
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    insight_type: Mapped[str] = mapped_column(String(16))
    color: Mapped[str] = mapped_column(String(16), default="#6366f1")
    label: Mapped[str] = mapped_column(String(32), default="")
    text: Mapped[str] = mapped_column(Text)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class UserPreference(Base):
    """用户偏好设置。对应 zhiyv.user_preferences。"""
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    target_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    salary_min: Mapped[int] = mapped_column(Integer, default=0)
    salary_max: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[str] = mapped_column(String(64), default="")
    notify_freq: Mapped[str] = mapped_column(String(16), default="weekly")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class JDRecord(Base):
    """智联招聘 JD 原始记录表 —— 12 列完整采样数据（按岗位编码去重）。对应 zhiyv.jd_records。"""
    __tablename__ = "jd_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    jd_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), index=True)
    location: Mapped[str] = mapped_column(String(128), default="")
    city: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    district: Mapped[str | None] = mapped_column(String(64), nullable=True)
    salary_raw: Mapped[str] = mapped_column(String(64), default="")
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_unit: Mapped[str] = mapped_column(String(8), default="")
    company_name: Mapped[str] = mapped_column(String(256), default="")
    industry: Mapped[str] = mapped_column(String(512), default="")
    company_size: Mapped[str] = mapped_column(String(64), default="")
    company_type: Mapped[str] = mapped_column(String(64), default="")
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_date_raw: Mapped[str] = mapped_column(String(32), default="")
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    company_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(512), default="")
    source: Mapped[str] = mapped_column(String(16), default="zhaopin")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


# ══════════════════════════════════════════════
# JD 数据二次加工派生表（T1–T6，按《JD数据二次加工与展示对接实施计划》P0 建表）
# 数据源：zhiyv.jd_records；岗位身份 = jd_records.title（D1）
# ══════════════════════════════════════════════


class JDPositionProfile(Base):
    """T1 岗位画像表 —— 按岗位名(title)聚合的薪资/城市/公司/行业分布。对应 zhiyv.jd_position_profile。"""
    __tablename__ = "jd_position_profile"

    title: Mapped[str] = mapped_column(String(256), primary_key=True)
    jd_count: Mapped[int] = mapped_column(Integer, default=0)
    salary_unit: Mapped[str] = mapped_column(String(8), default="")
    salary_min_p25: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_min_p50: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_min_p75: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max_p25: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max_p50: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max_p75: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_cover_rate: Mapped[float] = mapped_column(Float, default=0)
    top_cities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    top_companies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    industry_dist: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    size_dist: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    type_dist: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latest_posted: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class JDPositionCitySalary(Base):
    """T2 岗位×城市薪资表。对应 zhiyv.jd_position_city_salary。"""
    __tablename__ = "jd_position_city_salary"

    title: Mapped[str] = mapped_column(String(256), primary_key=True)
    city: Mapped[str] = mapped_column(String(64), primary_key=True)
    jd_count: Mapped[int] = mapped_column(Integer, default=0)
    salary_min_median: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max_median: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_unit: Mapped[str] = mapped_column(String(8), default="")


class JDPositionEvolution(Base):
    """T3 岗位演化月桶表 —— 按岗位名×月份桶聚合 JD 需求与薪资中位数。对应 zhiyv.jd_position_evolution。"""
    __tablename__ = "jd_position_evolution"

    title: Mapped[str] = mapped_column(String(256), primary_key=True)
    month_key: Mapped[str] = mapped_column(String(16), primary_key=True)
    jd_count: Mapped[int] = mapped_column(Integer, default=0)
    salary_min_median: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max_median: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_unit: Mapped[str] = mapped_column(String(8), default="")


class JDPositionSkill(Base):
    """T4 岗位×技能权重表 —— 从 jd_text 管线抽取聚合。对应 zhiyv.jd_position_skills。"""
    __tablename__ = "jd_position_skills"

    title: Mapped[str] = mapped_column(String(256), primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    jd_count: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[float] = mapped_column(Float, default=0)
    required_type: Mapped[str] = mapped_column(String(16), default="")
    level: Mapped[str] = mapped_column(String(16), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0)


class JDSkillSignal(Base):
    """T5 技能信号统计表（jd 源）。对应 zhiyv.jd_skill_signal。"""
    __tablename__ = "jd_skill_signal"

    skill_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    category: Mapped[str] = mapped_column(String(32), default="")
    jd_frequency: Mapped[int] = mapped_column(Integer, default=0)
    jd_confidence: Mapped[float] = mapped_column(Float, default=0)
    jd_examples: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(16), default="unverified")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)


class JDQualityDiagnosis(Base):
    """T6 JD 质量诊断表 —— 复用 diagnose_jd 批量落库。对应 zhiyv.jd_quality_diagnosis。"""
    __tablename__ = "jd_quality_diagnosis"

    jd_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    skill_count: Mapped[int] = mapped_column(Integer, default=0)
    inflation_index: Mapped[float] = mapped_column(Float, default=0)
    inflated_items: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    soft_skill_ratio: Mapped[float] = mapped_column(Float, default=0)
    required_ratio: Mapped[float] = mapped_column(Float, default=0)
    suggestions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now)
