"""动态指标模型 —— 设计方案 §3.5 六大指标。

独立模块，避免循环导入。供 L2 指标计算和 API schema 共同引用。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkillMetricItem:
    """单个技能的动态指标。"""
    skill_name: str
    emergence: float = 0.0            # 新兴度
    decline: float = 0.0              # 衰退度
    volatility: float = 0.0           # 波动率
    half_life: float | None = None    # 半衰期（月）
    half_life_method: str = ""        # 估算方法
    inflation_index: float = 0.0      # 通胀指数
    evolution_speed: float = 0.0      # 演化速度


@dataclass
class MetricsReport:
    """动态指标报告。"""
    skills: list[SkillMetricItem] = field(default_factory=list)
    top_emerging: list[str] = field(default_factory=list)
    top_declining: list[str] = field(default_factory=list)
    most_volatile: list[str] = field(default_factory=list)
    generated_at: str = ""
