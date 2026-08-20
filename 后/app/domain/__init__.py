"""领域模型 —— 纯数据 dataclass，不依赖任何外部基础设施。

对应设计方案 v2 §2-§5 的核心数据结构：
- JobPosting: 一条 JD 的统一格式
- ExtractedSkill: 抽取后的技能信号
- SkillStat: 归一化后的技能统计
- Position: 岗位节点
- Evidence: 证据节点
- DynamicMetrics: 六大动态指标
- EvolutionDiff: 演化差异
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ══════════════════════════════════════════════
# 枚举
# ══════════════════════════════════════════════

class SourceType(str, Enum):
    """数据来源类型。"""
    JD = "jd"
    RESUME = "resume"
    GITHUB = "github"
    ARXIV = "arxiv"
    STANDARD = "standard"


class SectionType(str, Enum):
    """JD 段落类型 —— 分级归类降噪的关键信号。"""
    RESPONSIBILITY = "responsibility"
    REQUIREMENT = "requirement"
    BONUS = "bonus"
    WELFARE = "welfare"
    COMPANY = "company"
    OTHER = "other"


class TechStack(str, Enum):
    """新一代信息技术领域 —— 赛题限定四大领域。"""
    AI = "人工智能"
    BIG_DATA = "大数据"
    INTELLIGENT_SYSTEM = "智能系统"
    IOT = "物联网"


class SkillLevel(str, Enum):
    """技能分级（L0-L3），设计方案 §2.3。"""
    L0_NOISE = "L0"        # 纯噪声（五险一金、弹性工作）
    L1_GENERIC = "L1"      # 泛化软技能（抗压能力、责任心）
    L2_CONTEXTUAL = "L2"   # 岗位相关软技能（善沟通对售前）
    L3_HARD = "L3"         # 硬技能（Kubernetes、PyTorch）


class VerificationStatus(str, Enum):
    """验证状态。"""
    UNVERIFIED = "unverified"    # 无来源
    CANDIDATE = "candidate"      # 单一来源
    CONFIRMED = "confirmed"      # 多源佐证


class PositionType(str, Enum):
    """岗位类型。"""
    EMERGING = "新兴"     # 新涌现的岗位
    EXISTING = "既有"     # 已存在的岗位


# ══════════════════════════════════════════════
# L1: JD 数据
# ══════════════════════════════════════════════

@dataclass
class Paragraph:
    """JD 的一个段落，带类型标记。"""
    section: SectionType
    text: str


@dataclass
class JobPosting:
    """一条 JD 的统一格式 —— 所有数据源的落地格式。"""
    jd_id: str
    source: SourceType
    tech_stack: TechStack
    title: str
    posted_date: str                          # YYYY-MM-DD
    paragraphs: list[Paragraph] = field(default_factory=list)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None
    city: Optional[str] = None
    meta: dict = field(default_factory=dict)  # 扩展元数据

    def full_text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs)


@dataclass
class CleanedJD:
    """L1 清洗后的中间格式。"""
    jd_id: str
    title: str
    tech_stack: str
    posted_date: str
    # 候选短语：[(section_type, phrase), ...]
    candidates: list[tuple[str, str]] = field(default_factory=list)
    # 分级后的技能词条（带级别）
    graded_items: list[dict] = field(default_factory=list)


# ══════════════════════════════════════════════
# L3: 技能抽取
# ══════════════════════════════════════════════

@dataclass
class ExtractedSkill:
    """抽取 Agent 产出的一个技能信号。"""
    name: str                          # 原始技能名（未归一化）
    required_type: str = "必备"         # 必备 / 加分
    evidence: str = ""                 # 原文证据片段
    source: str = "rule"              # spark / rule
    section: str = ""                 # 来自哪个段落
    confidence: float = 1.0           # 抽取置信度


@dataclass
class VerifyVerdict:
    """幻觉闸门对单个技能的验证结果。"""
    skill: ExtractedSkill
    passed: bool
    reason: str = ""


@dataclass
class GateResult:
    """幻觉闸门整体结果。"""
    jd_id: str
    total: int
    passed: list[ExtractedSkill] = field(default_factory=list)
    rejected: list[VerifyVerdict] = field(default_factory=list)

    @property
    def intercept_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return len(self.rejected) / self.total


# ══════════════════════════════════════════════
# L2: 归一化 + 统计
# ══════════════════════════════════════════════

@dataclass
class SkillStat:
    """归一化后的技能统计。"""
    name: str                          # 规范名
    df: int = 0                        # 文档频率（独立 JD 数）
    required_count: int = 0            # 标记为"必备"的次数
    bonus_count: int = 0               # 标记为"加分"的次数
    confidence: float = 0.0            # 融合置信度 ∈ [0,1]
    source_score: float = 0.0          # 信源加权得分
    verification_status: str = "unverified"  # confirmed / candidate / unverified
    tech_stacks: list[str] = field(default_factory=list)


# ══════════════════════════════════════════════
# L2: 动态指标
# ══════════════════════════════════════════════

@dataclass
class DynamicMetrics:
    """六大动态指标体系。"""
    emergence: float = 0.0             # 新兴度（上升斜率 × 近期集中度）
    decline: float = 0.0               # 衰退度（频次下滑速率）
    volatility: float = 0.0            # 波动率（时间方差）
    evolution_speed: float = 0.0       # 演化速度
    half_life: Optional[float] = None  # 半衰期（月）
    half_life_method: str = ""         # 估算方法
    inflation_index: float = 0.0       # 通胀指数


# ══════════════════════════════════════════════
# L4: 图谱节点
# ══════════════════════════════════════════════

@dataclass
class Position:
    """岗位节点。"""
    position_id: str
    name: str
    tech_stack: str
    position_type: PositionType = PositionType.EXISTING
    confidence: float = 0.8
    first_seen: str = ""
    description: str = ""


@dataclass
class SkillNode:
    """技能节点。"""
    skill_id: str
    name: str                          # 规范名
    category: str = "hard"             # hard / tool / framework / soft
    level: SkillLevel = SkillLevel.L3_HARD
    confidence: float = 0.0
    status: str = "candidate"          # confirmed / candidate / pending
    metrics: Optional[DynamicMetrics] = None


@dataclass
class EvidenceNode:
    """证据节点 —— 幻觉防控地基。"""
    evidence_id: str
    jd_id: str
    text: str                          # 原文片段（截断前 200 字符）
    source: str = ""
    timestamp: str = ""
    skill_name: str = ""               # 关联的规范技能名


@dataclass
class EvolutionDiff:
    """两个快照的差异。"""
    snapshot_old: str
    snapshot_new: str
    timestamp_old: str
    timestamp_new: str
    added_skills: list[str] = field(default_factory=list)
    removed_skills: list[str] = field(default_factory=list)
    modified_skills: list[dict] = field(default_factory=list)
    added_relations: list[dict] = field(default_factory=list)
    removed_relations: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"新增 {len(self.added_skills)} 项技能，"
            f"删除 {len(self.removed_skills)} 项，"
            f"修改 {len(self.modified_skills)} 项"
        )


# ══════════════════════════════════════════════
# 匹配 + 职业
# ══════════════════════════════════════════════

@dataclass
class MatchResult:
    """人岗匹配结果。"""
    position_id: str
    position_name: str
    match_rate: float                  # 0-1
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[dict] = field(default_factory=list)   # [{name, priority, reason}]
    learning_path: list[dict] = field(default_factory=list)    # [{step, skill, duration, resources}]
