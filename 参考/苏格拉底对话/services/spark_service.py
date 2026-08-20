"""讯飞星火 X2-Flash 大模型服务 — OpenAI 兼容 SSE 流式调用"""
import json
import logging
from typing import AsyncGenerator, Dict, Any
import httpx
from core.config import settings

logger = logging.getLogger(__name__)


class SparkService:
    """讯飞星火 X2-Flash — 兼容 OpenAI SDK 格式 (spark-x 模型)"""

    def __init__(self):
        self.api_url = settings.SPARK_API_URL
        self.api_password = settings.SPARK_API_PASSWORD
        self.model = settings.SPARK_MODEL

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话 — 调用讯飞星火 Agent API

        API 格式 (参考官方文档 000.md):
        - URL:   https://spark-api-open.xf-yun.com/agent/v1/chat/completions
        - Model: spark-x
        - Auth:  Bearer {APIPassword}
        - SSE:   data:{json}\n\n  → 结束 data:[DONE]
        """
        headers = {
            "Authorization": f"Bearer {self.api_password}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 800,
            "thinking": {"type": "disabled"},  # 苏格拉底反思不需要思考过程
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_body = ""
                        async for chunk in response.aiter_bytes():
                            error_body += chunk.decode("utf-8", errors="replace")
                            if len(error_body) > 500:
                                break
                        logger.error(
                            f"Spark API error ({response.status_code}): {error_body[:300]}"
                        )
                        yield {
                            "type": "error",
                            "content": f"讯飞星火返回错误 ({response.status_code})",
                        }
                        return

                    buffer = ""
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # 格式: data:{"code":0,...}  或  data:[DONE]
                        if not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()  # 去掉 "data:" 前缀

                        if data_str == "[DONE]":
                            yield {"type": "done"}
                            return

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        # 检查错误码
                        code = data.get("code", -1)
                        if code != 0:
                            err_msg = data.get("message", "未知错误")
                            logger.error(f"Spark API error code={code}: {err_msg}")
                            yield {"type": "error", "content": f"讯飞星火错误 ({code}): {err_msg}"}
                            return

                        choices = data.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})

                        # 思考过程 (reasoning_content)
                        reasoning = delta.get("reasoning_content")
                        if reasoning:
                            yield {"type": "thinking", "content": reasoning}

                        # 正文内容
                        content = delta.get("content")
                        if content:
                            yield {"type": "text", "content": content}

        except httpx.HTTPError as e:
            logger.error(f"Spark API connection error: {e}")
            yield {"type": "error", "content": f"讯飞星火连接失败: {str(e)}"}

    async def generate_socratic_reflection(
        self,
        question: str,
        topic: str = "",
        user_level: str = "初级",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """生成苏格拉底引导反思 — 调用讯飞星火 + 苏格拉底 Prompt"""
        from services.socratic_prompt import SYSTEM_PROMPT, build_user_prompt

        user_msg = build_user_prompt(question, topic, user_level)

        async for chunk in self.stream_chat(SYSTEM_PROMPT, user_msg):
            yield chunk

    async def health_check(self) -> bool:
        """检查讯飞星火服务健康状态"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {self.api_password}"}
                resp = await client.post(
                    self.api_url,
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                        "stream": False,
                    },
                )
                return resp.status_code < 500
        except Exception:
            return False


spark_service = SparkService()
