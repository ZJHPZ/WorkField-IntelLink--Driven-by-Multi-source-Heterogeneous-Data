"""讯飞星火 Spark-X2-Flash 客户端封装（OpenAI 兼容形态）。

依据官方文档 funfei.md：
- base_url = https://spark-api-open.xf-yun.com/agent/v1/
- api_key  = APIPassword（http 协议 APIPassword）
- model    = spark-x

关键约束（来自文档错误码表）：
- 10007：必须等大模型完全回复后才能发下一个请求 → 同一凭证不能高并发。
  因此本客户端内置串行限流 + 指数退避重试，供后续批量抽取 JD 安全使用。
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Optional

try:
    from openai import OpenAI
except ImportError as e:
    raise ImportError("需要安装 openai 库：pip install openai") from e


def _load_env(env_path: Optional[str] = None) -> dict:
    """极简 .env 读取（不引第三方 dotenv，避免额外依赖）。"""
    cfg = {
        "SPARK_API_PASSWORD": os.environ.get("SPARK_API_PASSWORD", ""),
        "SPARK_BASE_URL": os.environ.get(
            "SPARK_BASE_URL", "https://spark-api-open.xf-yun.com/agent/v1/"
        ),
        "SPARK_MODEL": os.environ.get("SPARK_MODEL", "spark-x"),
    }
    if env_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(here, "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


class SparkClient:
    """星火客户端。串行调用 + 重试，规避 10007 并发限制。"""

    def __init__(self, env_path: Optional[str] = None,
                 min_interval: float = 0.5, max_retries: int = 3):
        cfg = _load_env(env_path)
        if not cfg["SPARK_API_PASSWORD"] or "your_api_password" in cfg["SPARK_API_PASSWORD"]:
            raise RuntimeError("未配置 SPARK_API_PASSWORD，请检查 .env 文件")
        self.model = cfg["SPARK_MODEL"]
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._last_call = 0.0
        self._client = OpenAI(
            api_key=cfg["SPARK_API_PASSWORD"],
            base_url=cfg["SPARK_BASE_URL"],
        )

    def _throttle(self):
        """串行限流：距上次调用不足 min_interval 则等待。"""
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def chat(self, prompt: str, system: Optional[str] = None,
             temperature: float = 1.2, user: str = "kg") -> str:
        """通用对话，返回文本内容。带重试。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_err = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    user=user,
                    stream=False,
                )
                self._last_call = time.monotonic()
                return resp.choices[0].message.content or ""
            except Exception as e:
                last_err = e
                wait = (2 ** attempt) * self.min_interval
                time.sleep(wait)
                self._last_call = time.monotonic()
        raise RuntimeError(f"星火调用失败（重试 {self.max_retries} 次）：{last_err}")

    def extract_json(self, prompt: str, system: Optional[str] = None,
                     temperature: float = 0.1) -> Optional[dict | list]:
        """强制 JSON 抽取。低温 + 解析容错（剥离 ```json 代码块）。"""
        sys_prompt = (system or "") + \
            "\n严格只返回 JSON，不要任何解释性文字，不要 markdown 代码块标记。"
        raw = self.chat(prompt, system=sys_prompt, temperature=temperature)
        return _safe_parse_json(raw)


def _safe_parse_json(raw: str) -> Optional[dict | list]:
    """从模型输出里稳健地抽出 JSON。容忍代码块包裹和前后杂字。"""
    if not raw:
        return None
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        s, e = text.find(opener), text.rfind(closer)
        if 0 <= s < e:
            try:
                return json.loads(text[s:e + 1])
            except json.JSONDecodeError:
                continue
    return None
