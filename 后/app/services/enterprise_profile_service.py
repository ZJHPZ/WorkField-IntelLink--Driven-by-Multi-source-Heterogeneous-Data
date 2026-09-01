"""企业侧当前登录企业档案服务 —— 单行档案 读取 / 编辑（GET + PUT upsert）。

系统无登录体系，企业侧是单一 demo 工作台；「当前登录的企业」固定为
DEFAULT_ENTERPRISE = "demo_ent"（enterprise_profiles 单行，enterprise_id 唯一）。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.persistence.database import get_session
from app.persistence.zhiyv_models import EnterpriseProfile

DEFAULT_ENTERPRISE = "demo_ent"


def _profile_dict(p: EnterpriseProfile) -> dict:
    """单行档案 → camelCase dict（对齐前端 store / API 响应）。"""
    return {
        "enterpriseId": p.enterprise_id,
        "name": p.name,
        "shortName": p.short_name,
        "logoEmoji": p.logo_emoji,
        "uscc": p.uscc,
        "nature": p.nature,
        "industry": p.industry,
        "foundedYear": p.founded_year,
        "headcount": p.headcount,
        "financing": p.financing,
        "city": p.city,
        "address": p.address,
        "website": p.website,
        "description": p.description,
        "tags": p.tags or [],
        "techStack": p.tech_stack or [],
        "hiringChannels": p.hiring_channels or [],
        "hrName": p.hr_name,
        "hrTitle": p.hr_title,
        "hrPhone": p.hr_phone,
        "hrEmail": p.hr_email,
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


async def get_profile() -> dict | None:
    """当前登录企业档案。无行 → None（API 返回 {"profile": null}，前端 demo 兜底）。"""
    async for session in get_session():
        p = (
            await session.execute(
                select(EnterpriseProfile).where(EnterpriseProfile.enterprise_id == DEFAULT_ENTERPRISE)
            )
        ).scalar_one_or_none()
        return _profile_dict(p) if p else None


async def upsert_profile(body: dict) -> dict | None:
    """档案 upsert（partial 更新，body 为 camelCase）。单行幂等（重复 PUT 不产生第二行）。
    返回更新后的档案 dict；理论上不存在"目标企业未知"（固定单行）。"""
    field_map = {
        "name": "name",
        "shortName": "short_name",
        "logoEmoji": "logo_emoji",
        "uscc": "uscc",
        "nature": "nature",
        "industry": "industry",
        "foundedYear": "founded_year",
        "headcount": "headcount",
        "financing": "financing",
        "city": "city",
        "address": "address",
        "website": "website",
        "description": "description",
        "tags": "tags",
        "techStack": "tech_stack",
        "hiringChannels": "hiring_channels",
        "hrName": "hr_name",
        "hrTitle": "hr_title",
        "hrPhone": "hr_phone",
        "hrEmail": "hr_email",
    }

    async for session in get_session():
        p = (
            await session.execute(
                select(EnterpriseProfile).where(EnterpriseProfile.enterprise_id == DEFAULT_ENTERPRISE)
            )
        ).scalar_one_or_none()
        if p is None:
            p = EnterpriseProfile(enterprise_id=DEFAULT_ENTERPRISE)
            session.add(p)

        for fe_key, db_key in field_map.items():
            if fe_key in body and body[fe_key] is not None:
                setattr(p, db_key, body[fe_key])
        p.updated_at = datetime.now()

        await session.commit()
        return _profile_dict(p)
