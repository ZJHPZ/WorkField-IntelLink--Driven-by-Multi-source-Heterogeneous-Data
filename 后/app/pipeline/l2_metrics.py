"""L2 动态演化指标 —— 六大指标完整实现。

设计方案 §3.5：
- 技能新兴度：频次上升斜率 × 近期集中度
- 技能衰退度：频次下滑速率
- 技能波动率：需求在时间上的变异系数
- 岗位演化速度：技能集变化量
- 技能半衰期：从峰值到需求减半的时间
- 通胀指数：JD 注水程度
"""

from __future__ import annotations

import math

from app.domain import DynamicMetrics


class MetricsCalculator:
    """动态指标计算器。"""

    @staticmethod
    def emergence(monthly_counts: list[int]) -> float:
        """新兴度 = 增长率(后半段/前半段) × 近期集中度。"""
        n = len(monthly_counts)
        if n < 3:
            return 0.0
        half = n // 2
        first = monthly_counts[:half]
        second = monthly_counts[half:]
        mean_first = sum(first) / len(first) if first else 1
        mean_second = sum(second) / len(second) if second else 0
        total = sum(monthly_counts)
        growth = mean_second / mean_first if mean_first > 0 else 0
        concentration = sum(second) / total if total > 0 else 0
        return round(growth * concentration, 4)

    @staticmethod
    def decline(monthly_counts: list[int]) -> float:
        """衰退度 = 前半段均值高于后半段的降幅比例。"""
        n = len(monthly_counts)
        if n < 3:
            return 0.0
        half = n // 2
        mean_first = sum(monthly_counts[:half]) / half if half else 1
        mean_second = sum(monthly_counts[half:]) / (n - half) if (n - half) else 0
        if mean_first == 0:
            return 0.0
        return round(max(0, (mean_first - mean_second) / mean_first), 4)

    @staticmethod
    def volatility(monthly_counts: list[int]) -> float:
        """波动率 = 变异系数 CV = std / mean。"""
        n = len(monthly_counts)
        if n < 2:
            return 0.0
        mean = sum(monthly_counts) / n
        if mean == 0:
            return 0.0
        variance = sum((x - mean) ** 2 for x in monthly_counts) / n
        return round(math.sqrt(variance) / mean, 4)

    @staticmethod
    def half_life(monthly_counts: dict[str, int]) -> tuple[float | None, str]:
        """半衰期估算。

        主路径（经验估计）：找峰值月 → 找首个跌破 50% 峰值的月 → 差值。
        升级路径（≥6 数据点）：指数衰减拟合 f(t)=A·e^(-t/τ)。
        回退：数据不足/仍上升期 → 标"暂不可估"。
        """
        if len(monthly_counts) < 3:
            return None, "insufficient"
        months = sorted(monthly_counts.keys())
        counts = [monthly_counts[m] for m in months]
        peak_idx = counts.index(max(counts))
        peak_val = counts[peak_idx]
        threshold = peak_val * 0.5
        for i in range(peak_idx + 1, len(counts)):
            if counts[i] < threshold:
                return i - peak_idx, "peak"
        if peak_idx == len(counts) - 1:
            return None, "rising"

        # 曲线拟合（≥6 点）
        if len(monthly_counts) >= 6:
            try:
                import numpy as np
                from scipy.optimize import curve_fit
                t = np.arange(len(counts))
                y = np.array(counts, dtype=float)

                def exp_decay(t, A, tau, C):
                    return A * np.exp(-t / max(tau, 1e-6)) + C

                p0 = [max(counts), len(counts) / 2, min(counts)]
                popt, _ = curve_fit(exp_decay, t, y, p0=p0, maxfev=1000)
                tau = popt[1]
                if tau > 0:
                    return round(tau * math.log(2), 1), "curve_fit"
            except (ImportError, RuntimeError, ValueError):
                pass

        return None, "insufficient"

    @staticmethod
    def evolution_speed(old_skills: set[str], new_skills: set[str]) -> float:
        """演化速度 = 技能集变化量 / 总技能数。"""
        union = old_skills | new_skills
        if not union:
            return 0.0
        changed = len(old_skills.symmetric_difference(new_skills))
        return round(changed / len(union), 4)

    @staticmethod
    def inflation_index(
        skill_count: int,
        avg_skill_count: float,
        required_ratio: float = 0.5,
    ) -> float:
        """通胀指数 ∈ [0,1]。值越大注水越严重。"""
        score = 0.0
        if avg_skill_count > 0:
            ratio = skill_count / avg_skill_count
            if ratio > 1.5:
                score += min(0.4, (ratio - 1.5) * 0.4)
        if required_ratio < 0.3:
            score += 0.3
        elif required_ratio < 0.5:
            score += 0.1
        return round(min(1.0, score), 4)

    def compute_all(
        self,
        monthly_counts: dict[str, int],
        old_skills: set[str] | None = None,
        new_skills: set[str] | None = None,
        skill_count: int = 0,
        avg_skill_count: float = 0,
        required_ratio: float = 0.5,
    ) -> DynamicMetrics:
        """计算所有六大指标。"""
        counts_list = [monthly_counts[m] for m in sorted(monthly_counts.keys())]

        hl, hl_method = self.half_life(monthly_counts)
        evo_speed = 0.0
        if old_skills is not None and new_skills is not None:
            evo_speed = self.evolution_speed(old_skills, new_skills)

        return DynamicMetrics(
            emergence=self.emergence(counts_list),
            decline=self.decline(counts_list),
            volatility=self.volatility(counts_list),
            half_life=hl,
            half_life_method=hl_method,
            evolution_speed=evo_speed,
            inflation_index=self.inflation_index(skill_count, avg_skill_count, required_ratio),
        )
