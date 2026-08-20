"""L2 共现分析 —— 技能对在同一 JD 中共同出现的频率和强度。

设计方案 §3.2：共现强度用于通胀加权和技能关联分析。
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations


class CooccurrenceAnalyzer:
    """技能共现分析器。"""

    def __init__(self):
        self.skill_jd_map: dict[str, set[str]] = defaultdict(set)
        self.cooccurrences: dict[tuple[str, str], int] = defaultdict(int)
        self.jd_skills: dict[str, set[str]] = {}
        self.total_jds: int = 0

    def add_jd(self, jd_id: str, skills: list[str]):
        """添加一条 JD 的技能列表。"""
        skill_set = set(skills)
        self.jd_skills[jd_id] = skill_set
        self.total_jds += 1
        for skill in skill_set:
            self.skill_jd_map[skill].add(jd_id)
        for s1, s2 in combinations(sorted(skill_set), 2):
            self.cooccurrences[(s1, s2)] += 1

    def get_strength(self, skill_a: str, skill_b: str) -> float:
        """Jaccard 共现强度 = |A ∩ B| / |A ∪ B|。"""
        set_a = self.skill_jd_map.get(skill_a, set())
        set_b = self.skill_jd_map.get(skill_b, set())
        if not set_a and not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def get_top_cooccurring(self, skill: str, top_k: int = 10) -> list[tuple[str, float, int]]:
        """获取与某技能共现最强的 top_k 个技能。"""
        results = []
        for other in self.skill_jd_map:
            if other == skill:
                continue
            strength = self.get_strength(skill, other)
            count = self.cooccurrences.get((min(skill, other), max(skill, other)), 0)
            if strength > 0:
                results.append((other, strength, count))
        return sorted(results, key=lambda x: (-x[1], -x[2]))[:top_k]

    def get_stats(self) -> dict:
        """统计信息。"""
        return {
            "total_jds": self.total_jds,
            "total_skills": len(self.skill_jd_map),
            "total_cooccurrences": len(self.cooccurrences),
            "avg_skills_per_jd": (
                sum(len(s) for s in self.jd_skills.values()) / self.total_jds
                if self.total_jds > 0 else 0
            ),
        }


def build_cooccurrence(
    jd_skills_list: list[tuple[str, list[str]]],
) -> CooccurrenceAnalyzer:
    """便捷函数：从 [(jd_id, [skill_names]), ...] 构建共现分析器。"""
    analyzer = CooccurrenceAnalyzer()
    for jd_id, skills in jd_skills_list:
        analyzer.add_jd(jd_id, skills)
    return analyzer
