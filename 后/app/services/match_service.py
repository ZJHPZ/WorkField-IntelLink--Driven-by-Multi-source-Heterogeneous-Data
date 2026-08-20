"""人岗匹配引擎 —— 加权多维匹配。

设计方案 §7.2/§7.3：
- 技能 Jaccard 匹配 + 必备/加分权重 + 置信度加权
- 输出匹配率 + 差距清单 + 学习路径
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.domain import MatchResult, SkillStat
from app.pipeline.l2_normalize import normalize_name

logger = logging.getLogger(__name__)


@dataclass
class MatchDetail:
    """单次匹配详情。"""
    position_id: str
    position_name: str
    match_rate: float                           # 0-1
    skill_coverage: float                        # 用户技能覆盖岗位要求的比例
    matched_skills: list[str] = field(default_factory=list)
    partial_skills: list[str] = field(default_factory=list)   # 有相似但不完全匹配
    missing_skills: list[dict] = field(default_factory=list)  # [{name, priority, required_type}]
    learning_path: list[dict] = field(default_factory=list)


def match_skills(
    user_skills: list[str],
    position_skills: list[dict],
    position_id: str = "",
    position_name: str = "",
) -> MatchDetail:
    """个人技能 vs 岗位技能 → 匹配分析。

    Args:
        user_skills: 用户已有技能列表（原始名）
        position_skills: [{"name": "Python", "required_type": "必备", "confidence": 0.9}, ...]
        position_id: 岗位 ID
        position_name: 岗位名称

    Returns:
        MatchDetail
    """
    if not position_skills:
        return MatchDetail(
            position_id=position_id, position_name=position_name,
            match_rate=0.0, skill_coverage=0.0,
        )

    # 归一化用户技能
    user_norm = {normalize_name(s): s for s in user_skills}
    user_set = set(user_norm.keys())

    matched = []
    partial = []
    missing = []

    for req in position_skills:
        req_name = normalize_name(req["name"])
        req_type = req.get("required_type", "必备")
        confidence = req.get("confidence", 0.5)

        if req_name in user_set:
            matched.append(req_name)
        else:
            # 检查模糊匹配（子串包含）
            found = False
            for us in user_set:
                if req_name.lower() in us.lower() or us.lower() in req_name.lower():
                    partial.append(req_name)
                    found = True
                    break
            if not found:
                priority = "高" if req_type == "必备" and confidence > 0.6 else (
                    "中" if req_type == "必备" else "低"
                )
                missing.append({
                    "name": req["name"],
                    "canonical": req_name,
                    "priority": priority,
                    "required_type": req_type,
                    "confidence": confidence,
                })

    # 计算匹配率
    total_required = len(position_skills)
    effective_matched = len(matched) + len(partial) * 0.5
    skill_coverage = effective_matched / total_required if total_required > 0 else 0

    # 必备技能权重更高
    required_count = sum(1 for r in position_skills if r.get("required_type") == "必备")
    required_matched = sum(
        1 for m in matched
        if any(r["name"] == m and r.get("required_type") == "必备" for r in position_skills)
    ) + sum(
        0.5 for p in partial
        if any(r["name"] == p and r.get("required_type") == "必备" for r in position_skills)
    )

    required_rate = required_matched / required_count if required_count > 0 else 1.0
    match_rate = round(skill_coverage * 0.4 + required_rate * 0.6, 2)

    # 生成学习路径
    learning_path = _build_learning_path(missing)

    return MatchDetail(
        position_id=position_id,
        position_name=position_name,
        match_rate=match_rate,
        skill_coverage=round(skill_coverage, 2),
        matched_skills=matched,
        partial_skills=partial,
        missing_skills=sorted(missing, key=lambda x: (
            0 if x["priority"] == "高" else 1 if x["priority"] == "中" else 2
        )),
        learning_path=learning_path,
    )


def _build_learning_path(missing: list[dict]) -> list[dict]:
    """根据缺失技能生成学习路径。"""
    if not missing:
        return []
    path = []
    for i, m in enumerate(missing[:5], 1):
        duration = ("1-2个月" if m["priority"] == "低"
                    else "2-3个月" if m["priority"] == "中"
                    else "3-4个月")
        path.append({
            "step": i,
            "skill": m["canonical"],
            "priority": m["priority"],
            "duration": duration,
            "resources": [f"搜索 '{m['name']} 教程'"],
        })
    return path


def batch_match(
    user_skills_list: list[list[str]],
    position_skills: list[dict],
    position_name: str = "",
) -> list[MatchDetail]:
    """批量匹配（企业端团队盘点用）。"""
    results = []
    for i, skills in enumerate(user_skills_list):
        result = match_skills(
            skills, position_skills,
            position_id=f"batch_{i}",
            position_name=position_name,
        )
        results.append(result)
    return results
