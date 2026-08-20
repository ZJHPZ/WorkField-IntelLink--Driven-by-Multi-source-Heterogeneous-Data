"""L2 去重模块：SimHash 近重复检测（抄袭/同源）。

设计方案 §3.1：每条 JD 算 SimHash，相似度超阈值判为同源，去重后只保留一份权重。
"""

from __future__ import annotations

from app.utils.text import SimHash


class JDDeduplicator:
    """JD 近重复检测器。

    Args:
        threshold: 相似度阈值，0.8 表示 Hamming 距离 < 13/64 ≈ 20%
    """

    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.max_distance = int(64 * (1 - threshold))
        self.simhashes: dict[str, SimHash] = {}

    def is_duplicate(self, jd_id: str, text: str) -> tuple[bool, str | None]:
        """检查是否重复。返回 (is_dup, dup_of)。"""
        h = SimHash(text)
        for existing_id, existing_hash in self.simhashes.items():
            if h.distance(existing_hash) <= self.max_distance:
                return True, existing_id
        self.simhashes[jd_id] = h
        return False, None

    def deduplicate(self, jds: list[dict]) -> tuple[list[dict], list[dict]]:
        """去重。返回 (unique_jds, duplicates)。"""
        unique, duplicates = [], []
        for jd in jds:
            jd_id = jd["jd_id"]
            text = jd.get("full_text", "") or jd.get("title", "")
            is_dup, dup_of = self.is_duplicate(jd_id, text)
            if is_dup:
                jd["dup_of"] = dup_of
                duplicates.append(jd)
            else:
                unique.append(jd)
        return unique, duplicates


def deduplicate_jds(jds: list[dict], threshold: float = 0.8) -> tuple[list[dict], dict]:
    """便捷函数：去重并返回统计。"""
    dedup = JDDeduplicator(threshold=threshold)
    unique, duplicates = dedup.deduplicate(jds)
    stats = {
        "input_count": len(jds),
        "unique_count": len(unique),
        "duplicate_count": len(duplicates),
        "dedup_rate": len(duplicates) / len(jds) if jds else 0,
        "threshold": threshold,
    }
    return unique, stats
