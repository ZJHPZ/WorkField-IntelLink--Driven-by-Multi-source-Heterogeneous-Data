"""个人工作台服务 —— 差距分析 / 学习路径 / 半衰期提醒 / 转行可行性。

设计方案 §7.3：个人侧（面向求职者 / 在职者 / 转行者）。
"""

from __future__ import annotations

import logging

from app.services.match_service import match_skills

logger = logging.getLogger(__name__)


def career_gap_analysis(
    user_skills: list[str],
    position_skills: list[dict],
    position_name: str = "",
) -> dict:
    """差距分析：用户技能 vs 目标岗位。

    Returns:
        {match_rate, matched_skills, missing_skills, suggestion}
    """
    result = match_skills(user_skills, position_skills, position_name=position_name)
    return {
        "position_name": position_name,
        "match_rate": result.match_rate,
        "matched_skills": result.matched_skills,
        "partial_skills": result.partial_skills,
        "missing_skills": result.missing_skills,
        "suggestion": (
            f"匹配率 {result.match_rate:.0%}，"
            f"建议优先补: {result.missing_skills[0]['canonical'] if result.missing_skills else '无'}"
        ),
    }


def learning_path(user_skills: list[str], position_skills: list[dict],
                  position_name: str = "") -> dict:
    """学习路径推荐：基于差距生成分步骤学习计划。

    Returns:
        {match_rate, learning_path: [{step, skill, duration, resources}]}
    """
    result = match_skills(user_skills, position_skills, position_name=position_name)

    # 只展示前 5 项高优先级缺失技能
    high_priority = [m for m in result.missing_skills if m["priority"] == "高"][:5]
    if not high_priority:
        high_priority = [m for m in result.missing_skills if m["priority"] == "中"][:5]

    path = []
    for i, m in enumerate(high_priority, 1):
        duration = "2-3个月" if m["priority"] == "高" else "1-2个月"
        path.append({
            "step": i,
            "skill": m["canonical"],
            "priority": m["priority"],
            "duration": duration,
            "resources": [
                f"搜索 '{m['name']} 入门教程'",
                f"搜索 '{m['name']} 实战项目'",
            ],
        })

    return {
        "position_name": position_name,
        "match_rate": result.match_rate,
        "learning_path": path,
        "total_missing": len(result.missing_skills),
    }


def skill_freshness(user_skills: list[str], skill_metrics: dict) -> dict:
    """技能保鲜提醒：检查用户技能的半衰期。

    Args:
        user_skills: 用户已有技能名列表
        skill_metrics: {skill_name: {"half_life": months, "decline": rate, ...}}

    Returns:
        {alerts: [{skill, half_life, warning}], healthy: [...]}
    """
    alerts = []
    healthy = []

    for skill in user_skills:
        metrics = skill_metrics.get(skill, {})
        hl = metrics.get("half_life")
        decline = metrics.get("decline", 0)

        if hl is not None and hl < 12:
            alerts.append({
                "skill": skill,
                "half_life_months": hl,
                "decline_rate": decline,
                "warning": f"{skill} 预计 {hl} 个月后需求减半，建议关注替代技能",
            })
        elif decline > 0.3:
            alerts.append({
                "skill": skill,
                "half_life_months": hl,
                "decline_rate": decline,
                "warning": f"{skill} 衰退明显（{decline:.0%}），建议补充相关新兴技能",
            })
        else:
            healthy.append(skill)

    return {
        "alerts": alerts,
        "healthy_count": len(healthy),
        "at_risk_count": len(alerts),
        "summary": (f"{len(alerts)} 项技能有保鲜风险，{len(healthy)} 项健康"
                    if alerts else "所有技能状态健康"),
    }


def switch_feasibility(
    from_position_skills: list[str],
    to_position_skills: list[str],
    from_name: str = "",
    to_name: str = "",
) -> dict:
    """转行可行性：计算两岗位技能重叠度。

    Args:
        from_position_skills: 当前岗位的核心技能
        to_position_skills: 目标岗位的核心技能
    """
    from_set = set(s.lower() for s in from_position_skills)
    to_set = set(s.lower() for s in to_position_skills)

    overlap = from_set & to_set
    only_from = from_set - to_set
    only_to = to_set - from_set

    jaccard = len(overlap) / len(from_set | to_set) if (from_set | to_set) else 0

    if jaccard >= 0.6:
        feasibility = "高"
        advice = "技能重叠度高，转行成本较低"
    elif jaccard >= 0.3:
        feasibility = "中"
        advice = f"可复用 {len(overlap)} 项技能，需补 {len(only_to)} 项"
    else:
        feasibility = "低"
        advice = f"技能重叠度低，需学习 {len(only_to)} 项新技能"

    return {
        "from_position": from_name,
        "to_position": to_name,
        "overlap_skills": list(overlap),
        "transferable_count": len(overlap),
        "new_skills_needed": list(only_to),
        "deprecated_skills": list(only_from),
        "jaccard_similarity": round(jaccard, 2),
        "feasibility": feasibility,
        "advice": advice,
    }


def career_growth(position_skills: list[dict]) -> dict:
    """职业成长轨迹：初→中→高级技能要求差异。

    Args:
        position_skills: [{"name": ..., "required_type": ..., "level": "初级|中级|高级"}, ...]
    """
    junior = [s for s in position_skills if s.get("level") == "初级"]
    mid = [s for s in position_skills if s.get("level") == "中级"]
    senior = [s for s in position_skills if s.get("level") == "高级"]

    # 简单推断：如果没有 level 标注，按 confidence 分组
    if not junior and not mid and not senior:
        by_conf = sorted(position_skills, key=lambda x: x.get("confidence", 0))
        n = len(by_conf)
        junior = by_conf[:n//3]
        mid = by_conf[n//3:2*n//3]
        senior = by_conf[2*n//3:]

    return {
        "junior": {"skills": [s["name"] for s in junior], "count": len(junior)},
        "mid": {"skills": [s["name"] for s in mid], "count": len(mid),
                "new_vs_junior": [s["name"] for s in mid if s["name"] not in
                                  {j["name"] for j in junior}]},
        "senior": {"skills": [s["name"] for s in senior], "count": len(senior),
                   "new_vs_mid": [s["name"] for s in senior if s["name"] not in
                                  {m["name"] for m in mid}]},
    }
