"""L2 置信度融合引擎 —— 多源信号交叉验证。

设计方案 §3.4：
- 信源分层加权（权威 > 趋势 > 需求 > 参照）
- 孤证不入正式图谱（单一来源 → candidate）
- 多源佐证 + 置信度 > 阈值 → confirmed
"""

from __future__ import annotations

from app.pipeline.l2_normalize import (
    classify_source,
    compute_confidence,
    SOURCE_WEIGHTS,
)

# ══════════════════════════════════════════════
# 信源证据 + 评分
# ══════════════════════════════════════════════

def calculate_source_score(source_ids: list[str]) -> tuple[float, dict]:
    """计算多源交叉验证分数。

    Args:
        source_ids: 来源标识列表（如 jd_id）

    Returns:
        (综合分数, 详情字典)
    """
    if not source_ids:
        return 0.0, {"source_count": 0, "weighted_sum": 0}

    # 按来源类型分组
    groups: dict[str, int] = {}
    for sid in source_ids:
        st = classify_source(sid)
        groups[st] = groups.get(st, 0) + 1

    # 加权求和 + 多样性加成
    weighted_sum = sum(SOURCE_WEIGHTS.get(st, 0.4) * count
                       for st, count in groups.items())
    unique_count = len(groups)
    diversity_bonus = min(1.0, unique_count * 0.2)
    has_authority = "authority" in groups
    authority_bonus = 0.15 if has_authority else 0.0
    final_score = min(1.0, weighted_sum * (1 + diversity_bonus) + authority_bonus)

    return round(final_score, 4), {
        "source_count": unique_count,
        "weighted_sum": round(weighted_sum, 4),
        "diversity_bonus": round(diversity_bonus, 4),
        "has_authority": has_authority,
    }


def get_verification_status(source_ids: list[str]) -> str:
    """根据来源数量判定验证状态。

    Returns:
        "confirmed" (≥2 源) | "candidate" (1 源) | "unverified" (0 源)
    """
    if not source_ids:
        return "unverified"
    unique = len(set(classify_source(sid) for sid in source_ids))
    if unique >= 2:
        return "confirmed"
    return "candidate"
