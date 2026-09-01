"""Coze 帕克流式服务单元测试 —— httpx.MockTransport 模拟上游 SSE（不打网络）。

用 asyncio.run() 同步驱动（不依赖 pytest-asyncio 插件，避免与 conftest 的
session event_loop fixture 相互干扰）。
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch
from httpx import MockTransport, Request, Response

from app.services.coze_service import stream_chat


def _sse(*frames: str) -> str:
    """拼出标准 SSE 帧：event: message + data: <json> + 空行。"""
    return "".join(f"event: message\ndata: {f}\n\n" for f in frames)


def _ok_handler(body: str):
    def handler(request: Request) -> Response:
        return Response(200, content=body, headers={"Content-Type": "text/event-stream"})
    return handler


def _collect(**kwargs):
    return asyncio.run(
        _collect_gen(**kwargs)
    )


async def _collect_gen(**kwargs):
    return [ev async for ev in stream_chat("hi", "s1", token="t", url="https://x", **kwargs)]


def test_answer_concatenation_flat_string():
    """真实接口形状（2026-08-30 冒烟验证）：content.answer 是扁平字符串；code 是字符串 "0"。"""
    body = _sse(
        '{"type":"message_start","content":{"message_start":{"session_id":"s1"}}}',
        '{"type":"answer","content":{"answer":"雷达扫描完成，"}}',
        '{"type":"answer","content":{"answer":"张明机长。"}}',
        '{"type":"message_end","content":{"message_end":{"code":"0","message":"success"}}}',
    )
    evs = _collect(transport=MockTransport(_ok_handler(body)))
    assert evs[0] == {"type": "start"}
    assert evs[1] == {"type": "content", "content": "雷达扫描完成，"}
    assert evs[2] == {"type": "content", "content": "张明机长。"}
    assert evs[-1] == {"type": "done"}


def test_answer_nested_text_shape():
    """兼容接入文档 §4.3(2) 的嵌套 {"text": ...} 形状；code 为整数 0 也判成功。"""
    body = _sse(
        '{"type":"answer","content":{"answer":{"text":"嵌套文本"}}}',
        '{"type":"message_end","content":{"message_end":{"code":0,"message":"success"}}}',
    )
    evs = _collect(transport=MockTransport(_ok_handler(body)))
    assert evs[0] == {"type": "content", "content": "嵌套文本"}
    assert evs[-1] == {"type": "done"}


def test_message_end_error_code():
    body = _sse('{"type":"message_end","content":{"message_end":{"code":"1","message":"boom"}}}')
    evs = _collect(transport=MockTransport(_ok_handler(body)))
    assert evs[0]["type"] == "error" and "boom" in evs[0]["content"]
    assert evs[1] == {"type": "done"}


def test_stream_end_without_message_end():
    """流自然结束（无 message_end）→ 兜底 done，防前端卡死。"""
    body = _sse('{"type":"answer","content":{"answer":"只有这一句"}}')
    evs = _collect(transport=MockTransport(_ok_handler(body)))
    assert evs[0] == {"type": "content", "content": "只有这一句"}
    assert evs[-1] == {"type": "done"}


def test_non_200():
    def handler(request: Request) -> Response:
        return Response(401, text="unauthorized")
    evs = _collect(transport=MockTransport(handler))
    assert evs[0]["type"] == "error" and "401" in evs[0]["content"]


def test_missing_token():
    """token 为空（且 settings 也空）→ error，不打网络。"""
    fake = SimpleNamespace(COZE_API_TOKEN="", COZE_API_URL="https://x")
    with patch("app.services.coze_service.get_settings", return_value=fake):
        evs = asyncio.run(
            _collect_gen_no_token()
        )
    assert evs[0]["type"] == "error"


async def _collect_gen_no_token():
    return [ev async for ev in stream_chat("hi", "s1", token=None, url=None)]
