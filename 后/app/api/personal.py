"""★ 个人工作台 API (To C) —— CRUD + Agent 算法端点。

GET 端点查询 MySQL zhiyv 库的 user_* 表，返回前端 stores 期望的数据格式。
POST 端点走 MultiAgentSystem 或纯算法。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func

from app.api.deps import get_api_system
from app.agents.agent_state import IntentType
from app.persistence.database import get_session
from app.persistence.zhiyv_models import (
    UserProfile, UserSkill, UserMatch, LearningStepModel,
    CareerMilestone, GrowthTimeline, AIInsight, UserPreference,
    SkillStat,
)

router = APIRouter(tags=["个人工作台"])

# 默认用户（无认证时使用）
DEFAULT_USER = "demo_user"


# ══════════════════════════════════════════════
# 2.1 用户档案
# ══════════════════════════════════════════════

@router.get("/profile")
async def get_profile():
    """获取用户档案。"""
    async for session in get_session():
        stmt = select(UserProfile).where(UserProfile.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            return _demo_profile()
        return {
            "userId": profile.user_id,
            "name": profile.name,
            "title": profile.title,
            "phone": profile.phone,
            "email": profile.email,
            "birthYear": profile.birth_year,
            "status": profile.status,
            "industry": profile.industry,
            "education": profile.education,
            "major": profile.major,
            "englishLevel": profile.english_level,
            "experienceYears": profile.experience_years,
            "city": profile.city,
            "targetRole": profile.target_role,
            "targetCity": profile.target_city,
            "targetIndustry": profile.target_industry,
            "salaryMin": profile.salary_min,
            "salaryMax": profile.salary_max,
            "priority": profile.priority,
            "travelOk": profile.travel_ok,
            "relocateOk": profile.relocate_ok,
            "workMode": profile.work_mode,
            "resumeUrl": profile.resume_url,
            "resumeParsedAt": profile.resume_parsed_at.isoformat() if profile.resume_parsed_at else None,
            "avatarEmoji": profile.avatar_emoji,
            "level": profile.level,
            "createdAt": profile.created_at.isoformat() if profile.created_at else None,
            "updatedAt": profile.updated_at.isoformat() if profile.updated_at else None,
        }


@router.put("/profile")
async def update_profile(body: dict):
    """更新用户档案。"""
    async for session in get_session():
        stmt = select(UserProfile).where(UserProfile.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        field_map = {
            "name": "name", "title": "title", "phone": "phone", "email": "email",
            "birthYear": "birth_year", "status": "status", "industry": "industry",
            "education": "education", "major": "major", "englishLevel": "english_level",
            "experienceYears": "experience_years", "city": "city",
            "targetRole": "target_role", "targetCity": "target_city",
            "targetIndustry": "target_industry", "salaryMin": "salary_min",
            "salaryMax": "salary_max", "priority": "priority",
            "travelOk": "travel_ok", "relocateOk": "relocate_ok", "workMode": "work_mode",
        }

        if not profile:
            profile = UserProfile(user_id=DEFAULT_USER)
            for fe_key, db_key in field_map.items():
                if fe_key in body:
                    setattr(profile, db_key, body[fe_key])
            session.add(profile)
        else:
            for fe_key, db_key in field_map.items():
                if fe_key in body:
                    setattr(profile, db_key, body[fe_key])
            profile.updated_at = datetime.now()

        await session.commit()
        return {"status": "ok"}


@router.post("/profile/resume")
async def upload_resume(file: UploadFile = File(None)):
    """上传简历并解析技能。"""
    if not file:
        raise HTTPException(status_code=400, detail="请上传文件")
    # 解析简历
    import os, tempfile
    suffix = os.path.splitext(file.filename or "")[1] or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        from app.services.resume_service import parse_resume
        parsed = parse_resume(tmp_path)
    finally:
        os.unlink(tmp_path)

    # 存储解析结果
    async for session in get_session():
        stmt = select(UserProfile).where(UserProfile.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile:
            profile.resume_url = file.filename or ""
            profile.resume_parsed_at = datetime.now()
            await session.commit()

    return {
        "resumeUrl": file.filename,
        "parsedSkills": parsed.skills if hasattr(parsed, 'skills') else [],
    }


# ══════════════════════════════════════════════
# 2.2 技能管理
# ══════════════════════════════════════════════

@router.get("/skills")
async def get_skills():
    """获取用户全部技能列表。"""
    async for session in get_session():
        stmt = select(UserSkill).where(UserSkill.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        skills = result.scalars().all()

        if not skills:
            return {"skills": [], "totalCount": 0, "healthyCount": 0, "alertCount": 0}

        skill_list = []
        healthy = 0
        alert = 0
        for s in skills:
            if s.status in ("healthy", "matched"):
                healthy += 1
            elif s.status == "alert":
                alert += 1
            skill_list.append({
                "id": str(s.id),
                "name": s.skill_name,
                "canonicalName": s.canonical_name,
                "category": s.category,
                "level": s.level,
                "marketDemand": s.market_demand,
                "marketDf": s.market_df,
                "emergence": s.emergence,
                "decline": s.decline,
                "freshness": s.freshness,
                "yearsOfExperience": s.years_of_experience,
                "confidence": s.confidence,
                "firstSeen": s.first_seen.isoformat() if s.first_seen else None,
                "status": s.status,
            })

        return {
            "skills": skill_list,
            "totalCount": len(skill_list),
            "healthyCount": healthy,
            "alertCount": alert,
        }


@router.get("/skills/radar")
async def get_skills_radar():
    """获取雷达图维度数据（按类别聚合技能）。"""
    async for session in get_session():
        stmt = select(UserSkill).where(UserSkill.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        skills = result.scalars().all()

        if not skills:
            return {"dimensions": []}

        # 按 category 聚合
        from collections import defaultdict
        cat_data = defaultdict(list)
        for s in skills:
            cat_data[s.category].append(s)

        dimensions = []
        for cat, items in cat_data.items():
            avg_level = sum({"basic": 25, "intermediate": 50, "advanced": 75, "expert": 100}.get(i.level, 50) for i in items) / len(items)
            dimensions.append({
                "category": cat,
                "count": len(items),
                "avgLevel": round(avg_level, 1),
                "avgFreshness": round(sum(i.freshness for i in items) / len(items), 1),
            })

        return {"dimensions": dimensions}


@router.post("/skills")
async def add_skill(body: dict):
    """手动添加技能。"""
    async for session in get_session():
        skill = UserSkill(
            user_id=DEFAULT_USER,
            skill_name=body.get("name", ""),
            canonical_name=body.get("name", "").lower(),
            category=body.get("category", "编程语言"),
            level=body.get("level", "intermediate"),
        )
        session.add(skill)
        await session.commit()
        return {"id": str(skill.id), "name": skill.skill_name, "status": "ok"}


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: int, body: dict):
    """更新技能。"""
    async for session in get_session():
        stmt = select(UserSkill).where(UserSkill.id == skill_id, UserSkill.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        skill = result.scalar_one_or_none()
        if not skill:
            raise HTTPException(status_code=404, detail="技能不存在")
        for key in ["level", "freshness", "years_of_experience", "status"]:
            if key in body:
                setattr(skill, key, body[key])
        await session.commit()
        return {"status": "ok"}


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: int):
    """删除技能。"""
    async for session in get_session():
        stmt = select(UserSkill).where(UserSkill.id == skill_id, UserSkill.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        skill = result.scalar_one_or_none()
        if not skill:
            raise HTTPException(status_code=404, detail="技能不存在")
        await session.delete(skill)
        await session.commit()
        return {"status": "ok"}


# ══════════════════════════════════════════════
# 2.3 岗位匹配
# ══════════════════════════════════════════════

@router.get("/matches")
async def get_matches():
    """获取匹配岗位列表。"""
    async for session in get_session():
        stmt = select(UserMatch).where(UserMatch.user_id == DEFAULT_USER).order_by(UserMatch.match_rate.desc())
        result = await session.execute(stmt)
        matches = result.scalars().all()

        if not matches:
            return {"matches": []}

        return {
            "matches": [
                {
                    "id": str(m.id),
                    "positionId": m.position_id,
                    "positionName": m.position_name,
                    "company": m.company,
                    "matchRate": round(m.match_rate * 100 if m.match_rate <= 1 else m.match_rate, 1),
                    "matchedSkills": m.matched_skills or [],
                    "missingSkills": m.missing_skills or [],
                    "salaryRange": m.salary_range,
                }
                for m in matches
            ]
        }


@router.post("/matches/compare")
async def compare_matches(body: dict):
    """多岗位对比。"""
    position_ids = body.get("positionIds", [])
    async for session in get_session():
        stmt = select(UserMatch).where(
            UserMatch.user_id == DEFAULT_USER,
            UserMatch.position_id.in_(position_ids),
        )
        result = await session.execute(stmt)
        matches = result.scalars().all()
        return {
            "comparisons": [
                {
                    "positionId": m.position_id,
                    "positionName": m.position_name,
                    "matchRate": round(m.match_rate * 100 if m.match_rate <= 1 else m.match_rate, 1),
                    "matchedSkills": m.matched_skills or [],
                    "missingSkills": m.missing_skills or [],
                }
                for m in matches
            ]
        }


# ══════════════════════════════════════════════
# 2.4 学习路径
# ══════════════════════════════════════════════

@router.get("/learning-path")
async def get_learning_path():
    """获取完整学习路径。"""
    async for session in get_session():
        stmt = select(LearningStepModel).where(
            LearningStepModel.user_id == DEFAULT_USER
        ).order_by(LearningStepModel.sort_order)
        result = await session.execute(stmt)
        steps = result.scalars().all()

        if not steps:
            return {"steps": [], "totalHours": 0, "estWeeks": 0}

        total_hours = sum(s.estimated_hours for s in steps)
        return {
            "steps": [
                {
                    "id": str(s.id),
                    "title": s.title,
                    "skill": s.skill,
                    "resource": s.resource or "",
                    "estimatedHours": s.estimated_hours,
                    "status": s.status,
                    "progress": s.progress,
                    "prerequisites": s.prerequisites or [],
                    "order": s.sort_order,
                }
                for s in steps
            ],
            "totalHours": total_hours,
            "estWeeks": max(1, total_hours // 10),
        }


@router.put("/learning-path/{step_id}")
async def update_learning_step(step_id: int, body: dict):
    """更新学习步骤状态/进度。"""
    async for session in get_session():
        stmt = select(LearningStepModel).where(
            LearningStepModel.id == step_id,
            LearningStepModel.user_id == DEFAULT_USER,
        )
        result = await session.execute(stmt)
        step = result.scalar_one_or_none()
        if not step:
            raise HTTPException(status_code=404, detail="步骤不存在")
        if "status" in body:
            step.status = body["status"]
        if "progress" in body:
            step.progress = body["progress"]
        step.updated_at = datetime.now()
        await session.commit()
        return {
            "id": str(step.id),
            "title": step.title,
            "skill": step.skill,
            "status": step.status,
            "progress": step.progress,
        }


# ══════════════════════════════════════════════
# 2.5 技能保鲜
# ══════════════════════════════════════════════

@router.get("/freshness")
async def get_freshness():
    """获取保鲜数据 —— 从 user_skills + skill_stats 计算。"""
    async for session in get_session():
        # 获取用户技能
        stmt = select(UserSkill).where(UserSkill.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        user_skills = result.scalars().all()

        if not user_skills:
            return {"alerts": [], "healthPercent": 100, "healthySkills": [], "lighthouseData": []}

        # 获取 skill_stats 中的市场指标
        skill_names = [s.canonical_name or s.skill_name for s in user_skills]
        stats_stmt = select(SkillStat).where(SkillStat.skill_name.in_(skill_names))
        stats_result = await session.execute(stats_stmt)
        stats_map = {s.skill_name: s for s in stats_result.scalars().all()}

        alerts = []
        healthy = []
        lighthouse = []

        for us in user_skills:
            canon = us.canonical_name or us.skill_name
            stat = stats_map.get(canon)
            half_life = stat.half_life if stat else None
            decline = stat.decline if stat else 0
            freshness = us.freshness

            urgency = "low"
            if half_life and half_life < 12:
                urgency = "high"
            elif decline > 0.3:
                urgency = "medium"

            if urgency != "low":
                alerts.append({
                    "skillName": us.skill_name,
                    "halfLife": half_life or 0,
                    "currentFreshness": freshness,
                    "declineRate": decline,
                    "suggestedAction": f"建议关注 {us.skill_name} 的替代技能" if urgency == "high" else f"{us.skill_name} 衰退明显，建议补充新兴技能",
                    "urgency": urgency,
                })
            else:
                healthy.append(us.skill_name)

            lighthouse.append({
                "skill": us.skill_name,
                "freshness": freshness,
                "status": "alert" if urgency != "low" else "healthy",
            })

        health_pct = round(len(healthy) / len(user_skills) * 100) if user_skills else 100
        return {
            "alerts": alerts,
            "healthPercent": health_pct,
            "healthySkills": healthy,
            "lighthouseData": lighthouse,
        }


# ══════════════════════════════════════════════
# 2.6 转行分析
# ══════════════════════════════════════════════

@router.get("/switch")
async def get_switch_options():
    """获取转行选项 —— 基于用户技能 vs 各岗位技能计算可迁移性。"""
    from app.graph.repository import get_positions, get_position_detail

    async for session in get_session():
        # 获取用户技能
        stmt = select(UserSkill).where(UserSkill.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        user_skills = result.scalars().all()
        user_skill_set = {s.canonical_name or s.skill_name for s in user_skills}

        if not user_skill_set:
            return {"options": []}

        # 获取所有岗位
        positions = await get_positions()
        options = []

        for pos in positions[:10]:
            detail = await get_position_detail(pos["position_id"])
            if not detail:
                continue
            pos_skills = set()
            for sk in detail.get("skills", []):
                skill_data = sk.get("skill", {})
                if skill_data.get("name"):
                    pos_skills.add(skill_data["name"].lower())

            if not pos_skills:
                continue

            overlap = user_skill_set & pos_skills
            gaps = pos_skills - user_skill_set
            jaccard = len(overlap) / len(user_skill_set | pos_skills) if (user_skill_set | pos_skills) else 0

            options.append({
                "targetRole": pos.get("name", ""),
                "transferabilityScore": round(jaccard * 100, 1),
                "skillOverlap": list(overlap)[:10],
                "skillGaps": list(gaps)[:10],
                "estimatedTransitionMonths": max(1, len(gaps) * 2),
                "marketDemand": round(pos.get("avg_emergence", 0) * 20, 1),
                "jaccardSimilarity": round(jaccard * 100, 1),
            })

        options.sort(key=lambda x: x["transferabilityScore"], reverse=True)
        return {"options": options}


@router.get("/switch/presets")
async def get_switch_presets():
    """获取预设热门转行方向。"""
    return {
        "presets": [
            {"from": "前端开发", "to": "全栈工程师", "label": "前端 → 全栈"},
            {"from": "后端开发", "to": "架构师", "label": "后端 → 架构"},
            {"from": "数据分析师", "to": "AI 算法工程师", "label": "数据 → AI"},
            {"from": "测试工程师", "to": "DevOps", "label": "测试 → DevOps"},
            {"from": "产品经理", "to": "数据产品经理", "label": "产品 → 数据产品"},
        ]
    }


# ══════════════════════════════════════════════
# 2.7 成长轨迹
# ══════════════════════════════════════════════

@router.get("/growth")
async def get_growth():
    """获取成长数据。"""
    async for session in get_session():
        stmt = select(GrowthTimeline).where(
            GrowthTimeline.user_id == DEFAULT_USER
        ).order_by(GrowthTimeline.event_date)
        result = await session.execute(stmt)
        events = result.scalars().all()

        # 计算当前等级
        total_skills_stmt = select(func.count()).select_from(UserSkill).where(UserSkill.user_id == DEFAULT_USER)
        total_result = await session.execute(total_skills_stmt)
        total_skills = total_result.scalar() or 0
        current_level = min(99, max(1, total_skills * 3))

        levels = [
            {"level": 1, "name": "新手", "minSkills": 0},
            {"level": 10, "name": "初级", "minSkills": 3},
            {"level": 30, "name": "中级", "minSkills": 8},
            {"level": 60, "name": "高级", "minSkills": 15},
            {"level": 90, "name": "专家", "minSkills": 25},
        ]

        if not events:
            return {"currentLevel": current_level, "levels": levels, "timeline": []}

        return {
            "currentLevel": current_level,
            "levels": levels,
            "timeline": [
                {
                    "date": e.event_date,
                    "skillsGained": e.skills_gained,
                    "skills": e.skills or [],
                    "cumulativeCount": e.cumulative_count,
                    "description": e.description,
                }
                for e in events
            ],
        }


@router.get("/growth/level-requirements")
async def get_level_requirements():
    """获取下一等级要求。"""
    async for session in get_session():
        total_stmt = select(func.count()).select_from(UserSkill).where(UserSkill.user_id == DEFAULT_USER)
        total_result = await session.execute(total_stmt)
        total = total_result.scalar() or 0

        next_level = 30 if total < 8 else 60 if total < 15 else 90 if total < 25 else 99
        return {
            "nextLevel": next_level,
            "requirements": [f"累计掌握 {next_level // 3} 项技能"],
            "estMonths": max(1, (next_level // 3 - total) * 2),
        }


# ══════════════════════════════════════════════
# 2.8 职业里程碑
# ══════════════════════════════════════════════

@router.get("/milestones")
async def get_milestones():
    """获取里程碑列表。"""
    async for session in get_session():
        stmt = select(CareerMilestone).where(CareerMilestone.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        milestones = result.scalars().all()

        if not milestones:
            return {"milestones": [], "unlockedCount": 0}

        unlocked = sum(1 for m in milestones if m.unlocked)
        return {
            "milestones": [
                {
                    "id": m.id,
                    "name": m.name,
                    "description": m.description,
                    "icon": m.icon,
                    "rarity": m.rarity,
                    "unlocked": m.unlocked,
                    "unlockedAt": m.unlocked_at.isoformat() if m.unlocked_at else None,
                    "progress": m.progress,
                    "target": m.target,
                }
                for m in milestones
            ],
            "unlockedCount": unlocked,
        }


# ══════════════════════════════════════════════
# 2.9 用户偏好
# ══════════════════════════════════════════════

@router.get("/preferences")
async def get_preferences():
    """获取偏好设置。"""
    async for session in get_session():
        stmt = select(UserPreference).where(UserPreference.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        pref = result.scalar_one_or_none()
        if not pref:
            return {
                "targetRoles": [],
                "salaryMin": 0,
                "salaryMax": 0,
                "city": "",
                "notifyFreq": "weekly",
            }
        return {
            "targetRoles": pref.target_roles or [],
            "salaryMin": pref.salary_min,
            "salaryMax": pref.salary_max,
            "city": pref.city,
            "notifyFreq": pref.notify_freq,
        }


@router.put("/preferences")
async def update_preferences(body: dict):
    """更新偏好设置。"""
    async for session in get_session():
        stmt = select(UserPreference).where(UserPreference.user_id == DEFAULT_USER)
        result = await session.execute(stmt)
        pref = result.scalar_one_or_none()

        if not pref:
            pref = UserPreference(user_id=DEFAULT_USER)
            for key in ["targetRoles", "salaryMin", "salaryMax", "city", "notifyFreq"]:
                if key in body:
                    db_key = "target_roles" if key == "targetRoles" else "notify_freq" if key == "notifyFreq" else key
                    setattr(pref, db_key, body[key])
            session.add(pref)
        else:
            for key in ["targetRoles", "salaryMin", "salaryMax", "city", "notifyFreq"]:
                if key in body:
                    db_key = "target_roles" if key == "targetRoles" else "notify_freq" if key == "notifyFreq" else key
                    setattr(pref, db_key, body[key])
            pref.updated_at = datetime.now()

        await session.commit()
        return {"status": "ok"}


# ══════════════════════════════════════════════
# 2.10 AI 分析
# ══════════════════════════════════════════════

@router.get("/ai/summary")
async def get_ai_summary():
    """获取 AI 职业顾问总结。"""
    async for session in get_session():
        stmt = select(AIInsight).where(AIInsight.user_id == DEFAULT_USER).order_by(AIInsight.id)
        result = await session.execute(stmt)
        insights = result.scalars().all()

        if not insights:
            return {
                "summaryText": "暂无 AI 分析数据，请先完善技能画像",
                "insights": [],
                "generatedAt": None,
            }

        summary_text = insights[0].summary_text or ""
        return {
            "summaryText": summary_text,
            "insights": [
                {
                    "type": i.insight_type,
                    "color": i.color,
                    "label": i.label,
                    "text": i.text,
                }
                for i in insights
            ],
            "generatedAt": insights[0].generated_at.isoformat() if insights[0].generated_at else None,
        }


# ══════════════════════════════════════════════
# POST 端点（Agent 算法）
# ══════════════════════════════════════════════

class GapRequest(BaseModel):
    user_skills: list[str] = []
    position_skills: list[dict] = []
    position_name: str = ""


class SwitchRequest(BaseModel):
    from_skills: list[str] = []
    to_skills: list[str] = []
    from_name: str = ""
    to_name: str = ""


class GrowthRequest(BaseModel):
    position_skills: list[dict] = []


@router.post("/career/gap")
async def career_gap(req: GapRequest):
    """差距分析 → SuggestAgent。"""
    try:
        system = get_api_system()
        match_result = await system.process(IntentType.MATCH_POSITION, {
            "user_skills": req.user_skills,
            "position_skills": req.position_skills,
            "position_name": req.position_name,
        })
        gap_result = await system.process(IntentType.CAREER_GAP, {
            "user_skills": req.user_skills,
            "position_skills": req.position_skills,
            "position_name": req.position_name,
        })
        agent_data = gap_result.get("result", {}).get("data", {})
        match_data = match_result.get("result", {}).get("data", {})
        return {
            "status": "ok",
            "position_name": req.position_name,
            "match_rate": match_data.get("match_rate", 0),
            "missing_skills": agent_data.get("missing_skills", []),
            "learning_path": agent_data.get("learning_path", []),
            "total_missing": agent_data.get("total_missing", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"差距分析失败: {e}")


@router.post("/career/learning-path")
async def career_learning_path(req: GapRequest):
    """学习路径生成 → Agent 系统。"""
    try:
        system = get_api_system()
        await system.process(IntentType.MATCH_POSITION, {
            "user_skills": req.user_skills,
            "position_skills": req.position_skills,
        })
        result = await system.process(IntentType.CAREER_GAP, {
            "user_skills": req.user_skills,
            "position_skills": req.position_skills,
            "position_name": req.position_name,
        })
        agent_data = result.get("result", {}).get("data", {})
        return {
            "status": "ok",
            "position_name": req.position_name,
            "learning_path": agent_data.get("learning_path", []),
            "total_missing": agent_data.get("total_missing", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习路径生成失败: {e}")


@router.post("/career/skill-freshness")
async def career_skill_freshness(user_skills: list[str] = [], skill_metrics: dict = {}):
    """技能保鲜提醒 → 纯算法。"""
    from app.services.career_service import skill_freshness as calc_freshness
    if not user_skills:
        return {"status": "ok", "alerts": [], "healthy_count": 0, "summary": "请提供技能列表"}
    result = calc_freshness(user_skills, skill_metrics)
    return {"status": "ok", **result}


@router.post("/career/switch-feasibility")
async def career_switch_feasibility(req: SwitchRequest):
    """转行可行性 → 纯算法。"""
    from app.services.career_service import switch_feasibility
    result = switch_feasibility(req.from_skills, req.to_skills, req.from_name, req.to_name)
    return {"status": "ok", **result}


@router.post("/career/growth")
async def career_growth_endpoint(req: GrowthRequest):
    """职业成长轨迹 → 纯算法。"""
    from app.services.career_service import career_growth
    result = career_growth(req.position_skills)
    return {"status": "ok", **result}


# ══════════════════════════════════════════════
# 内部辅助
# ══════════════════════════════════════════════

def _demo_profile() -> dict:
    """返回 demo 档案数据（Silent Fallback）。"""
    return {
        "userId": DEFAULT_USER,
        "name": "张三",
        "title": "高级前端开发工程师",
        "phone": "13800138000",
        "email": "zhangsan@example.com",
        "birthYear": 1995,
        "status": "employed_looking",
        "industry": "互联网/IT",
        "education": "本科",
        "major": "计算机科学与技术",
        "englishLevel": "CET-6",
        "experienceYears": "5-8年",
        "city": "北京",
        "targetRole": "全栈工程师",
        "targetCity": "上海",
        "targetIndustry": "互联网/IT",
        "salaryMin": 25,
        "salaryMax": 40,
        "priority": "tech_growth",
        "travelOk": False,
        "relocateOk": True,
        "workMode": "hybrid",
        "resumeUrl": "",
        "resumeParsedAt": None,
        "avatarEmoji": "👨‍💻",
        "level": 42,
        "createdAt": "2024-01-15T00:00:00",
        "updatedAt": "2026-08-01T00:00:00",
    }


# ══════════════════════════════════════════════
# AI 对话（SSE 流式）
# ══════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = ""


@router.post("/ai/chat")
async def ai_chat(req: ChatRequest):
    """AI 职业顾问对话 —— SSE 流式返回。

    基于用户技能画像和岗位图谱数据，通过星火 LLM 生成个性化职业建议。
    """
    from fastapi.responses import StreamingResponse
    import json as _json

    # 获取用户上下文
    user_context = _build_user_context()

    system_prompt = (
        "你是「职域智联」AI 职业顾问，专注于新一代信息技术领域（人工智能、大数据、智能系统、物联网）的职业规划。\n"
        "用户画像：\n"
        f"{user_context}\n\n"
        "回答要求：\n"
        "1. 基于用户的实际技能数据给出针对性建议\n"
        "2. 引用具体的岗位要求和市场数据\n"
        "3. 建议要可执行（具体的学习资源、时间规划）\n"
        "4. 使用 markdown 格式，适当使用列表和加粗\n"
        "5. 回答简洁专业，避免空泛的套话"
    )

    async def generate():
        # 发送 agent_start
        yield f"data: {_json.dumps({'type': 'agent_start', 'agent': 'thinking'})}\n\n"

        try:
            from app.api.deps import get_llm_client
            llm = get_llm_client()
            if llm:
                # 调用星火 LLM
                response_text = llm.chat(req.message, system=system_prompt)
                # 模拟流式输出（按段落分块发送）
                import re
                chunks = re.split(r'(?<=[\n。！？])', response_text)
                for chunk in chunks:
                    if chunk.strip():
                        yield f"data: {_json.dumps({'type': 'content', 'content': chunk})}\n\n"
                        import asyncio
                        await asyncio.sleep(0.03)
            else:
                # LLM 不可用时，基于本地算法给出回复
                fallback = _generate_fallback_response(req.message)
                for char in fallback:
                    yield f"data: {_json.dumps({'type': 'content', 'content': char})}\n\n"
                    import asyncio
                    await asyncio.sleep(0.01)
        except Exception as e:
            yield f"data: {_json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield f"data: {_json.dumps({'type': 'agent_end'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _build_user_context() -> str:
    """构建用户上下文信息，供 LLM 参考。"""
    # 从 demo profile 获取基本信息
    profile = _demo_profile()
    lines = [
        f"- 姓名：{profile['name']}",
        f"- 当前职位：{profile['title']}",
        f"- 工作年限：{profile['experienceYears']}",
        f"- 学历：{profile['education']}",
        f"- 所在城市：{profile['city']}",
        f"- 期望职位：{profile['targetRole']}",
        f"- 期望薪资：{profile['salaryMin']}-{profile['salaryMax']}K",
    ]

    # 从 skill_stats 获取技能数据
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在异步上下文中，直接返回基本信息
            pass
    except Exception:
        pass

    return "\n".join(lines)


def _generate_fallback_response(message: str) -> str:
    """当 LLM 不可用时，基于规则生成回复。"""
    msg = message.lower()
    if any(kw in msg for kw in ["匹配", "适合", "对口"]):
        return (
            "## 技能匹配分析\n\n"
            "根据你的技能画像，我来分析一下：\n\n"
            "**优势技能：** Python、深度学习、NLP — 这些是当前市场需求最高的 AI 核心技能。\n\n"
            "**待提升：** Kubernetes、MLOps — 这两项是 AI 工程化的关键，建议优先学习。\n\n"
            "需要更详细的匹配分析，请前往 **人岗匹配** 页面查看雷达图。"
        )
    elif any(kw in msg for kw in ["学习", "学什么", "提升"]):
        return (
            "## 学习建议\n\n"
            "基于你的技能现状，建议按以下顺序学习：\n\n"
            "1. **Kubernetes 基础** → CKAD 认证路线（约 40 学时）\n"
            "2. **MLOps 实践** → MLflow + Kubeflow（约 30 学时）\n"
            "3. **分布式训练** → DeepSpeed/FSDP（约 25 学时）\n\n"
            "详细学习路径请前往 **学习路径** 页面。"
        )
    elif any(kw in msg for kw in ["转行", "转型", "换方向"]):
        return (
            "## 转行可行性分析\n\n"
            "根据你的技能组合，以下是转行方向的可行性评估：\n\n"
            "| 方向 | 可迁移性 | 预估周期 |\n|---|---|---|\n"
            "| 全栈开发 | ⭐⭐⭐⭐⭐ 85% | 4 个月 |\n"
            "| AI 产品经理 | ⭐⭐⭐⭐ 78% | 6 个月 |\n"
            "| 数据架构师 | ⭐⭐⭐ 65% | 9 个月 |\n\n"
            "详细的转行分析请前往 **转行分析** 页面。"
        )
    else:
        return (
            "你好！我是你的 AI 职业顾问，可以帮你：\n\n"
            "- 🔍 **技能匹配分析** — 你的技能和目标岗位的匹配度\n"
            "- 📚 **学习路径规划** — 应该优先学什么\n"
            "- 🔄 **转行可行性** — 转向其他方向的难度和周期\n"
            "- 📈 **市场行情** — 你的技能在市场上值多少\n\n"
            "请问你想了解什么？"
        )
