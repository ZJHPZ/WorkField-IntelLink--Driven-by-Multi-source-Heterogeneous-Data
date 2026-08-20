"""苏格拉底引导反思 API — POST /generate (SSE 流式)"""
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from services.spark_service import spark_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/socratic", tags=["socratic"])


class SocraticRequest(BaseModel):
    question: str = Field(..., description="用户的原始问题")
    topic: str = Field(default="", description="知识点/主题（可选）")
    user_level: str = Field(default="初级", description="用户水平：初级/中级/高级")
    user_id: str = Field(default="", description="用户ID")


@router.post("/generate")
async def generate_socratic_reflection(req: SocraticRequest, request: Request):
    """生成苏格拉底引导反思 — SSE流式响应"""

    async def event_stream():
        full_text = ""
        current_section = ""

        async for chunk in spark_service.generate_socratic_reflection(
            question=req.question,
            topic=req.topic,
            user_level=req.user_level,
        ):
            if chunk["type"] == "text":
                text = chunk["content"]
                full_text += text

                # 检测段落标记（倒序检查，最新标记优先匹配）
                section = current_section
                if "【一句话反思】" in full_text:
                    section = "reflection"
                    current_section = "reflection"
                elif "【关键假设检验】" in full_text:
                    section = "assumptions"
                    current_section = "assumptions"
                elif "【引导性问题】" in full_text:
                    section = "questions"
                    current_section = "questions"

                # SSE 事件: 带 section 标记
                line = f"data: {_sse_data('text', text, section)}\n\n"
                yield line

            elif chunk["type"] == "done":
                yield f"data: {_sse_data('done', '', current_section)}\n\n"

            elif chunk["type"] == "error":
                yield f"data: {_sse_data('error', chunk['content'], '')}\n\n"

        yield f"data: {_sse_data('done', '', full_text)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/health")
async def health():
    ok = await spark_service.health_check()
    return {"status": "ok" if ok else "degraded", "model": spark_service.model}


def _sse_data(typ: str, content: str, section: str) -> str:
    import json
    return json.dumps({"type": typ, "content": content, "section": section}, ensure_ascii=False)


# ── 通用生成端点（自定义 system prompt，不做苏格拉底格式约束） ──

class SimpleGenerateRequest(BaseModel):
    system_prompt: str = Field(..., description="系统提示词")
    user_message: str = Field(..., description="用户消息")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=800, ge=1, le=4096)


@router.post("/generate-simple")
async def generate_simple(req: SimpleGenerateRequest):
    """直接调用星火 API，使用自定义 system prompt — SSE 流式响应"""

    async def event_stream():
        async for chunk in spark_service.stream_chat(
            system_prompt=req.system_prompt,
            user_message=req.user_message,
        ):
            if chunk["type"] == "text":
                yield f"data: {_sse_data('text', chunk['content'], '')}\n\n"
            elif chunk["type"] == "done":
                yield f"data: {_sse_data('done', '', '')}\n\n"
            elif chunk["type"] == "error":
                yield f"data: {_sse_data('error', chunk['content'], '')}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
