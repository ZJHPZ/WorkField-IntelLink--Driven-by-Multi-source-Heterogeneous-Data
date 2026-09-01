"""Coze 智能体「帕克」流式客户端 —— 解析上游 SSE 并翻译为内部事件字典。

对接 职域智联-接入文档.md 的 /stream_run 接口（自定义 Coze 部署，非标准 api.coze.com）。

2026-08-30 冒烟验证与文档的两处差异（已在此修正）：
- `answer` 帧 `content.answer` 是**扁平字符串**（文档 §4.3(2) 误写为嵌套 {"text": ...}），
  本模块 `_extract_answer` 两种形状都兼容；
- `message_end` 帧 `content.message_end.code` 是**字符串 "0"**（非整数），按 `str(code) != "0"` 判断。
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_payload(session_id: str, user_message: str) -> dict[str, Any]:
    """构造 /stream_run 请求体（见接入文档 §3）。"""
    return {
        "type": "query",
        "session_id": session_id,
        "content": {
            "query": {
                "prompt": [{"type": "text", "content": {"text": user_message}}],
            },
        },
    }


def _extract_answer(content: Any) -> str:
    """从 answer 帧提取文本。兼容扁平字符串与嵌套 {"text": ...} 两种形状。"""
    if not isinstance(content, dict):
        return ""
    answer = content.get("answer")
    if isinstance(answer, str):
        return answer
    if isinstance(answer, dict):
        return answer.get("text", "")
    return ""


async def stream_chat(
    user_message: str,
    session_id: str,
    *,
    token: str | None = None,
    url: str | None = None,
    timeout: httpx.Timeout | float = 120.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """调用 Coze「帕克」，把 SSE 事件翻译为内部事件并逐个 yield。

    产出事件：
      {"type": "start"}                       # message_start（端点通常已发 agent_start，可忽略）
      {"type": "content", "content": str}     # answer 文本分片
      {"type": "error", "content": str}       # 非200 / 超时 / 网络错误 / message_end code!=0 / 缺token
      {"type": "done"}                        # 正常结束（message_end code==0 或流自然结束）

    `token`/`url` 缺省时读 get_settings()；`transport` 可注入（测试用 httpx.MockTransport）。
    """
    settings = get_settings()
    token = token or settings.COZE_API_TOKEN
    url = url or settings.COZE_API_URL
    if not token:
        logger.error("未配置 COZE_API_TOKEN")
        yield {"type": "error", "content": "未配置 COZE_API_TOKEN"}
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    client_kwargs: dict[str, Any] = {"timeout": timeout}
    if transport is not None:
        client_kwargs["transport"] = transport

    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            async with client.stream(
                "POST", url, headers=headers, json=_build_payload(session_id, user_message)
            ) as resp:
                if resp.status_code != 200:
                    error_body = ""
                    async for chunk in resp.aiter_bytes():
                        error_body += chunk.decode("utf-8", errors="replace")
                        if len(error_body) > 500:
                            break
                    logger.error("Coze 上游错误 (%s): %s", resp.status_code, error_body[:300])
                    yield {"type": "error", "content": f"Coze 上游返回错误 ({resp.status_code})"}
                    return

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if not data_str or data_str == "[DONE]":
                        continue
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning("Coze SSE JSON 解析失败: %.100s", data_str)
                        continue
                    if not isinstance(data, dict):
                        continue

                    ev_type = data.get("type")
                    if ev_type == "message_start":
                        yield {"type": "start"}
                    elif ev_type == "answer":
                        text = _extract_answer(data.get("content"))
                        if text:
                            yield {"type": "content", "content": text}
                    elif ev_type == "message_end":
                        content = data.get("content")
                        end = content.get("message_end", {}) if isinstance(content, dict) else {}
                        code = str(end.get("code", -1))
                        if code != "0":
                            msg = end.get("message", "") or "未知错误"
                            logger.error("Coze 结束码异常 code=%s: %s", code, msg)
                            yield {"type": "error", "content": f"Coze 响应异常 (code={code}): {msg}"}
                        yield {"type": "done"}
                        return

                # 流自然结束（未收到 message_end）——兜底，避免前端卡死
                yield {"type": "done"}
    except httpx.TimeoutException:
        logger.error("Coze 请求超时")
        yield {"type": "error", "content": "Coze 请求超时，请稍后重试"}
    except httpx.HTTPError as e:
        logger.error("Coze 连接错误: %s", e)
        yield {"type": "error", "content": f"Coze 连接失败: {e}"}
