"""企业侧人才库服务 —— 候选人列表 / 详情 / HR 标注。

候选人维度复用个人侧 user_* 表（user_profiles / user_skills / user_matches），
HR 标注独立存 talent_pool_entries（不污染个人侧档案）。
企业侧专属，天然排除 demo_user（个人侧"我自己"）。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.persistence.database import get_session
from app.persistence.zhiyv_models import (
    UserProfile,
    UserSkill,
    UserMatch,
    TalentPoolEntry,
)

DEFAULT_USER = "demo_user"

# 技能熟练度权重：用于列表 topSkills 排序
_LEVEL_WEIGHT = {"expert": 4, "advanced": 3, "intermediate": 2, "basic": 1}


def _match_rate(value: float) -> float:
    """match_rate 兼容：库里可能存 0-1 或 0-100，统一转百分制（同 personal.py）。"""
    return round(value * 100 if value <= 1 else value, 1)


def _dict_keys(v):
    """JSON 列可能是 dict 或 list，统一取可展示的键/元素列表。"""
    if isinstance(v, dict):
        return list(v.keys())
    return list(v) if v else []


def _skill_sort_key(skill: UserSkill):
    return (_LEVEL_WEIGHT.get(skill.level, 0), skill.freshness or 0)


def _top_skills(skills: list[UserSkill], n: int = 3) -> list[str]:
    return [s.skill_name for s in sorted(skills, key=_skill_sort_key, reverse=True)[:n]]


def _annotation_dict(entry: TalentPoolEntry | None) -> dict:
    if entry is None:
        return {"favorite": False, "hrStatus": "", "note": "", "updatedAt": None}
    return {
        "favorite": bool(entry.favorite),
        "hrStatus": entry.hr_status or "",
        "note": entry.note or "",
        "updatedAt": entry.updated_at.isoformat() if entry.updated_at else None,
    }


# ── 列表 ──

async def list_candidates(
    position: str | None = None,
    skill: str | None = None,
    city: str | None = None,
    favorite: bool | None = None,
    hr_status: str | None = None,
) -> list[dict]:
    """候选人列表（逻辑 JOIN：4 次索引查询 + Python 归并，避免 N:1 fan-out）。

    返回空库 → []。筛选在 Python 侧应用（候选人数据量小）。
    """
    async for session in get_session():
        profiles = (
            await session.execute(
                select(UserProfile).where(UserProfile.user_id != DEFAULT_USER)
            )
        ).scalars().all()
        if not profiles:
            return []

        ids = [p.user_id for p in profiles]

        entries = (await session.execute(select(TalentPoolEntry))).scalars().all()
        entry_map = {e.user_id: e for e in entries}

        all_skills = (
            await session.execute(select(UserSkill).where(UserSkill.user_id.in_(ids)))
        ).scalars().all()
        all_matches = (
            await session.execute(select(UserMatch).where(UserMatch.user_id.in_(ids)))
        ).scalars().all()

        skills_by_user: dict[str, list[UserSkill]] = {}
        for s in all_skills:
            skills_by_user.setdefault(s.user_id, []).append(s)

        matches_by_user: dict[str, list[UserMatch]] = {}
        for m in all_matches:
            matches_by_user.setdefault(m.user_id, []).append(m)

        candidates: list[dict] = []
        for p in profiles:
            skills = skills_by_user.get(p.user_id, [])
            matches = matches_by_user.get(p.user_id, [])
            entry = entry_map.get(p.user_id)

            best_mr = max((_match_rate(m.match_rate) for m in matches), default=0)

            row = {
                "id": p.user_id,
                "name": p.name,
                "title": p.title,
                "targetRole": p.target_role,
                "city": p.city,
                "experienceYears": p.experience_years,
                "education": p.education,
                "salaryMin": p.salary_min,
                "salaryMax": p.salary_max,
                "skillCount": len(skills),
                "topSkills": _top_skills(skills),
                "bestMatchRate": best_mr,
                "favorite": bool(entry.favorite) if entry else False,
                "hrStatus": entry.hr_status if entry else "",
                "note": entry.note if entry else "",
                "updatedAt": entry.updated_at.isoformat() if entry and entry.updated_at else None,
            }

            # 筛选
            if position and position not in (row["targetRole"] or ""):
                continue
            if city and city not in (row["city"] or ""):
                continue
            if skill and not any(
                skill in (s.skill_name or "") or skill in (s.canonical_name or "")
                for s in skills
            ):
                continue
            if favorite is not None and row["favorite"] != favorite:
                continue
            if hr_status and row["hrStatus"] != hr_status:
                continue

            candidates.append(row)

        return candidates


# ── 详情 ──

async def get_candidate_detail(user_id: str) -> dict | None:
    """候选人详情：档案 + 技能全量 + 匹配全量 + HR 标注。未知 user → None（API 转 404）。"""
    async for session in get_session():
        profile = (
            await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
        ).scalar_one_or_none()
        if profile is None:
            return None

        skills = (
            await session.execute(select(UserSkill).where(UserSkill.user_id == user_id))
        ).scalars().all()
        matches = (
            await session.execute(select(UserMatch).where(UserMatch.user_id == user_id))
        ).scalars().all()
        entry = (
            await session.execute(
                select(TalentPoolEntry).where(TalentPoolEntry.user_id == user_id)
            )
        ).scalar_one_or_none()

        return {
            "id": user_id,
            "profile": {
                "name": profile.name,
                "title": profile.title,
                "targetRole": profile.target_role,
                "targetCity": profile.target_city,
                "city": profile.city,
                "industry": profile.industry,
                "experienceYears": profile.experience_years,
                "education": profile.education,
                "major": profile.major,
                "englishLevel": profile.english_level,
                "salaryMin": profile.salary_min,
                "salaryMax": profile.salary_max,
                "workMode": profile.work_mode,
                "relocateOk": profile.relocate_ok,
                "travelOk": profile.travel_ok,
                "avatarEmoji": profile.avatar_emoji,
            },
            "skills": [
                {
                    "name": s.skill_name,
                    "category": s.category,
                    "level": s.level,
                    "freshness": s.freshness or 0,
                    "yearsOfExperience": s.years_of_experience or 0,
                    "marketDemand": s.market_demand or 0,
                    "status": s.status,
                }
                for s in sorted(skills, key=_skill_sort_key, reverse=True)
            ],
            "matches": [
                {
                    "positionId": m.position_id,
                    "positionName": m.position_name,
                    "company": m.company,
                    "matchRate": _match_rate(m.match_rate),
                    "matchedSkills": _dict_keys(m.matched_skills),
                    "missingSkills": _dict_keys(m.missing_skills),
                    "salaryRange": m.salary_range,
                }
                for m in sorted(matches, key=lambda x: _match_rate(x.match_rate), reverse=True)
            ],
            "annotation": _annotation_dict(entry),
        }


# ── HR 标注 upsert ──

async def upsert_annotation(
    user_id: str,
    favorite: bool | None = None,
    hr_status: str | None = None,
    note: str | None = None,
) -> dict | None:
    """收藏 / 状态 / 备注 upsert。候选人不存在 → None（API 转 404）。幂等（重复 PUT 不产生第二行）。"""
    async for session in get_session():
        profile = (
            await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
        ).scalar_one_or_none()
        if profile is None:
            return None

        entry = (
            await session.execute(
                select(TalentPoolEntry).where(TalentPoolEntry.user_id == user_id)
            )
        ).scalar_one_or_none()
        if entry is None:
            entry = TalentPoolEntry(user_id=user_id, favorite=False, hr_status="", note="")
            session.add(entry)

        if favorite is not None:
            entry.favorite = favorite
        if hr_status is not None:
            entry.hr_status = hr_status
        if note is not None:
            entry.note = note
        entry.updated_at = datetime.now()

        await session.commit()
        return _annotation_dict(entry)
