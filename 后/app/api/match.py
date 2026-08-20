"""匹配引擎 API —— 简历解析 + 人岗匹配。所有端点走 MultiAgentSystem。"""

from __future__ import annotations

import os, tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.api.deps import get_api_system
from app.agents.agent_state import IntentType

router = APIRouter(tags=["匹配"])


class MatchRequest(BaseModel):
    position_id: str = ""
    position_name: str = ""
    position_skills: list[dict] = []
    user_skills: list[str] = []


class BatchMatchRequest(BaseModel):
    position_name: str = ""
    position_skills: list[dict] = []
    user_skills_list: list[list[str]] = []


@router.post("/resume/parse")
async def parse_resume_endpoint(file: UploadFile = File(None), text: str = Form(None)):
    """上传简历（PDF/Word）或纯文本 → Agent 系统抽取技能。"""
    try:
        if file:
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
        elif text:
            from app.services.resume_service import parse_resume_text
            parsed = parse_resume_text(text)
        else:
            raise HTTPException(status_code=400, detail="请上传文件或提供文本")

        # ★ 过 Agent 系统做抽取+校验
        system = get_api_system()
        result = await system.process(IntentType.EXTRACT_SKILLS, {
            "resume_text": parsed.raw_text,
            "resume_id": parsed.resume_id,
        })

        agent_data = result.get("result", {}).get("data", {})
        return {
            "status": "ok",
            "resume_id": parsed.resume_id,
            "skills": parsed.skills,
            "experience_years": parsed.experience_years,
            "education": parsed.education,
            "city": parsed.city,
            "skill_count": len(parsed.skills),
            "agent_processed": result.get("success", False),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历解析失败: {e}")


@router.post("/match")
async def match_endpoint(req: MatchRequest):
    """★ 人岗匹配 → Agent 系统 (extractor→normalizer→matcher 链)。"""
    try:
        system = get_api_system()
        result = await system.process(IntentType.MATCH_POSITION, {
            "user_skills": req.user_skills,
            "position_skills": req.position_skills,
            "position_name": req.position_name,
            "position_id": req.position_id,
        })

        agent_data = result.get("result", {}).get("data", {})
        return {
            "status": "ok",
            "position_name": req.position_name,
            "match_rate": agent_data.get("match_rate", 0),
            "skill_coverage": agent_data.get("skill_coverage", 0),
            "matched_skills": agent_data.get("matched_skills", []),
            "partial_skills": agent_data.get("partial_skills", []),
            "missing_skills": agent_data.get("missing_skills", []),
            "learning_path": agent_data.get("learning_path", []),
            "agent_id": result.get("agent_id", "matcher"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {e}")


@router.post("/match/batch")
async def batch_match_endpoint(req: BatchMatchRequest):
    """批量匹配 → Agent 系统。"""
    try:
        results = []
        system = get_api_system()
        for skills in req.user_skills_list:
            result = await system.process(IntentType.MATCH_POSITION, {
                "user_skills": skills,
                "position_skills": req.position_skills,
                "position_name": req.position_name,
            })
            agent_data = result.get("result", {}).get("data", {})
            results.append({
                "match_rate": agent_data.get("match_rate", 0),
                "matched_count": len(agent_data.get("matched_skills", [])),
                "missing_count": len(agent_data.get("missing_skills", [])),
            })

        return {
            "status": "ok",
            "total": len(results),
            "avg_match_rate": sum(r["match_rate"] for r in results) / len(results) if results else 0,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量匹配失败: {e}")
