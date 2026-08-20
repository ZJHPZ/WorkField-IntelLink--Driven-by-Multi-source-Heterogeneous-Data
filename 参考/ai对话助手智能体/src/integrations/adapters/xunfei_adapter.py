"""
讯飞大模型适配器

支持 Spark X2, X1.5, 3.5, 3.1, 1.1 版本
使用 WebSocket 协议进行实时对话
"""

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime as dt
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import urlparse, urlencode

import websocket

from .base_adapter import BaseLLMAdapter


class XunfeiAdapter(BaseLLMAdapter):
    """
    讯飞大模型适配器

    支持:
    - Spark X2 (最新深度推理模型)
    - Spark X1.5 (深度推理模型)
    - Spark 4.0 Ultra
    - Spark 3.5
    - Spark 3.1
    - Spark 1.1

    使用 WebSocket 协议进行实时对话
    """

    # API 版本配置
    API_VERSIONS = {
        # X2/X1.5 使用 WebSocket 接口
        "x2": {
            "url": "wss://spark-api.xf-yun.com/x2",
            "domain": "spark-x",
            "model": "SPARKX2",
            "protocol": "websocket",
        },
        "x1.5": {
            "url": "wss://spark-api.xf-yun.com/v1/x1",
            "domain": "spark-x",
            "model": "SPARKX15",
            "protocol": "websocket",
        },
        # 旧版本使用 WebSocket
        "4.0": {
            "url": "wss://spark-api.xf-yun.com/v4.0/chat",
            "domain": "generalv4",
            "model": "SPARK4.0",
            "protocol": "websocket",
        },
        "3.5": {
            "url": "wss://spark-api.xf-yun.com/v3.1/chat",
            "domain": "generalv3.5",
            "model": "SPARK3.5",
            "protocol": "websocket",
        },
        "3.1": {
            "url": "wss://spark-api.xf-yun.com/v2.1/chat",
            "domain": "generalv2.1",
            "model": "SPARK3.1",
            "protocol": "websocket",
        },
        "1.1": {
            "url": "wss://spark-api.xf-yun.com/v1.1/chat",
            "domain": "general",
            "model": "SPARK1.1",
            "protocol": "websocket",
        },
    }

    def __init__(self, config: Dict[str, Any]):
        """
        初始化讯飞适配器

        Args:
            config: 配置字典，需要包含以下必填字段:
                - api_key: API密钥 (必填)
                - api_secret: API密钥 (必填)
                - version: API版本 (默认 x2)
                - model: 模型名称 (可选，默认使用版本对应的模型)
                - temperature: 温度参数
                - top_p: top_p 参数
                - max_tokens: 最大token数
        """
        super().__init__(config)

        # 讯飞凭证 (必填)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.app_id = config.get("app_id", config.get("appid"))

        if not all([self.api_key, self.api_secret]):
            raise ValueError(
                "讯飞适配器需要配置 api_key, api_secret\n"
                "请在 config/agent_llm_config.json 中配置讯飞凭证"
            )

        # API 版本
        self.version = config.get("version", "x2")
        if self.version not in self.API_VERSIONS:
            self.version = "x2"  # 默认使用 X2

        version_config = self.API_VERSIONS[self.version]
        self.api_url = version_config["url"]
        self.domain = version_config["domain"]
        self.protocol = version_config.get("protocol", "websocket")  # 默认为 WebSocket

        # 模型名称
        self.model = config.get("model") or version_config["model"]

        # 调整配置参数以适配讯飞
        self.temperature = config.get("temperature", 0.5)
        self.top_k = config.get("top_k", 5)
        self.max_tokens = config.get("max_tokens", 4096)

    def _generate_auth_url(self) -> str:
        """
        生成鉴权 URL (通用 WebSocket 鉴权)

        基于 HMAC-SHA256 签名
        """
        from urllib.parse import urlparse, urlencode
        from datetime import datetime, timezone

        # RFC1123 格式的时间戳 (使用 timezone-aware datetime)
        now = datetime.now(timezone.utc)
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # HTTP 接口使用不同的签名方式 (POST request-line)
        if self.protocol == "http":
            # HTTP 接口签名 - 使用 POST request-line 格式
            signature_origin = f"host: {urlparse(self.api_url).netloc}\ndate: {date}\nPOST {urlparse(self.api_url).path} HTTP/1.1"
            signature_sha = hmac.new(
                self.api_secret.encode("utf-8"),
                signature_origin.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            signature_base64 = base64.b64encode(signature_sha).decode("utf-8")

            authorization_origin = (
                f'api_key="{self.api_key}", algorithm="hmac-sha256", '
                f'headers="host date request-line", signature="{signature_base64}"'
            )
        else:
            # WebSocket 接口签名
            signature_origin = f"host: {urlparse(self.api_url).netloc}\ndate: {date}\nGET {urlparse(self.api_url).path} HTTP/1.1"
            signature_sha = hmac.new(
                self.api_secret.encode("utf-8"),
                signature_origin.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            signature_base64 = base64.b64encode(signature_sha).decode("utf-8")

            authorization_origin = (
                f'api_key="{self.api_key}", algorithm="hmac-sha256", '
                f'headers="host date request-line", signature="{signature_base64}"'
            )

        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

        # 拼接 URL - 使用与讯飞官方一致的编码方式
        from urllib.parse import quote
        # WSS URL
        host = urlparse(self.api_url).netloc
        path = urlparse(self.api_url).path
        return f"wss://{host}{path}?authorization={quote(authorization)}&date={quote(date)}&host={quote(host)}"

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        格式化消息为讯飞格式

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]

        Returns:
            格式化后的消息列表
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            # 映射角色
            if role == "system":
                role = "system"
            elif role == "assistant":
                role = "assistant"
            else:
                role = "user"

            content = msg.get("content", "")
            formatted.append({
                "role": role,
                "content": content,
            })

        return formatted

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        对话 (流式)

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            助手回复文本
        """
        # 收集所有流式输出
        full_response = []
        reasoning_content = []

        for chunk in self.stream_chat(messages, **kwargs):
            if isinstance(chunk, dict):
                # X2 版本返回结构化数据
                if "reasoning_content" in chunk:
                    reasoning_content.append(chunk["reasoning_content"])
                if "content" in chunk:
                    full_response.append(chunk["content"])
            else:
                full_response.append(chunk)

        return "".join(full_response)

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[Any]:
        """
        流式对话

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            逐步输出的文本片段或字典
        """
        # 根据协议选择不同的流式方法
        if self.protocol == "http":
            # HTTP 接口使用 SSE
            yield from self._stream_http(messages, **kwargs)
        else:
            # WebSocket 接口
            auth_url = self._generate_auth_url()
            if self.version in ("x2", "x1.5"):
                yield from self._stream_x2_websocket(auth_url, messages, **kwargs)
            else:
                yield from self._stream_legacy(auth_url, messages, **kwargs)

    def _stream_http(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[Any]:
        """
        HTTP SSE 流式对话 (X2/X1.5)
        """
        import requests
        from datetime import datetime as dt

        now = dt.now()
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # 生成 authorization - 讯飞 HTTP 接口使用标准 HMAC 签名
        from urllib.parse import urlparse
        import base64

        # 签名内容 (按讯飞 HTTP 接口规范)
        signature_origin = f"host: {urlparse(self.api_url).netloc}\ndate: {date}\nPOST {urlparse(self.api_url).path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_base64 = base64.b64encode(signature_sha).decode("utf-8")

        # Authorization header
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Date": date,  # HTTP header 使用大写 Date
            "Authorization": authorization,
        }

        payload = {
            "header": {
                "app_id": self.app_id or "",
                "uid": str(uuid.uuid4()),
            },
            "payload": {
                "message": {
                    "text": self._format_messages(messages)
                }
            },
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature),
                    "top_k": kwargs.get("top_k", self.top_k),
                    "presence_penalty": kwargs.get("presence_penalty", 1.0),
                    "frequency_penalty": kwargs.get("frequency_penalty", 0.02),
                    "chat_id": str(uuid.uuid4()),
                }
            },
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60,
        )

        if response.status_code != 200:
            error_msg = response.text
            raise Exception(f"HTTP {response.status_code}: {error_msg}")

        # 解析 SSE 流
        reasoning_text = []
        response_text = []

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8")
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    header = data.get("header", {})
                    code = header.get("code", 0)

                    if code != 0:
                        raise Exception(f"API error: {header.get('message', 'Unknown error')}")

                    payload_data = data.get("payload", {})
                    choices = payload_data.get("choices", {})
                    status = choices.get("status", 0)

                    # X2 版本返回格式
                    text_list = choices.get("text", [])
                    for item in text_list:
                        # 思考内容
                        reasoning = item.get("reasoning_content", "")
                        if reasoning:
                            reasoning_text.append(reasoning)
                            yield {"reasoning_content": reasoning}

                        # 实际回答内容
                        content = item.get("content", "")
                        if content:
                            response_text.append(content)
                            yield {"content": content}

                    if status == 2:
                        break

                except json.JSONDecodeError:
                    continue

    def _stream_x2_websocket(self, auth_url: str, messages: List[Dict[str, str]], **kwargs) -> Iterator[Any]:
        """
        X2/X1.5 版本流式对话

        使用新的请求格式
        """
        import queue
        import threading

        response_queue: queue.Queue = queue.Queue()
        complete = threading.Event()
        error = [None]  # 使用列表以便在闭包中修改

        def on_message(ws, message):
            try:
                data = json.loads(message)
                header = data.get("header", {})
                code = header.get("code", 0)

                if code != 0:
                    error[0] = f"API error: {header.get('message', 'Unknown error')}"
                    complete.set()
                    return

                payload = data.get("payload", {})
                choices = payload.get("choices", {})
                status = choices.get("status", 0)

                # X2 版本返回格式
                text_list = choices.get("text", [])
                for item in text_list:
                    # 思考内容 (reasoning_content)
                    reasoning = item.get("reasoning_content", "")
                    if reasoning:
                        response_queue.put({"reasoning_content": reasoning})

                    # 实际回答内容
                    content = item.get("content", "")
                    if content:
                        response_queue.put({"content": content})

                # 完成状态
                if status == 2:
                    complete.set()

            except Exception as e:
                error[0] = str(e)
                complete.set()

        def on_error(ws, err):
            error[0] = str(err)
            complete.set()

        def on_close(ws, code, reason):
            complete.set()

        def on_open(ws):
            # 构建 X2 版本请求体
            payload = {
                "header": {
                    "uid": str(uuid.uuid4()),
                    "app_id": self.app_id or "",
                },
                "payload": {
                    "message": {
                        "text": self._format_messages(messages)
                    }
                },
                "parameter": {
                    "chat": {
                        "domain": self.domain,
                        "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                        "temperature": kwargs.get("temperature", self.temperature),
                        "top_k": kwargs.get("top_k", self.top_k),
                        "presence_penalty": kwargs.get("presence_penalty", 1.0),
                        "frequency_penalty": kwargs.get("frequency_penalty", 0.02),
                        "chat_id": str(uuid.uuid4()),
                        "stream": True,
                        "thinking": {"type": "disabled"},  # 关闭深度思考
                    }
                },
            }

            ws.send(json.dumps(payload))

        # 创建 WebSocket 连接
        ws = websocket.WebSocketApp(
            auth_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        # 运行连接
        thread = threading.Thread(target=ws.run_forever, daemon=True)
        thread.start()

        # 从队列中获取结果
        while not complete.is_set() or not response_queue.empty():
            try:
                item = response_queue.get(timeout=0.1)
                yield item
            except queue.Empty:
                continue

        if error[0]:
            raise Exception(f"讯飞 API 错误: {error[0]}")

    def _stream_legacy(self, auth_url: str, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """
        旧版本 (3.5/3.1/1.1) 流式对话
        """
        response_text = []
        complete = False
        error = None

        class StreamHandler:
            def on_message(self, ws, message):
                nonlocal complete
                try:
                    data = json.loads(message)
                    payload = data.get("payload", {})
                    choices = payload.get("choices", {})
                    status = choices.get("status", 0)

                    # 文本内容
                    text = choices.get("text", [])
                    for content in text:
                        content_text = content.get("content", "")
                        response_text.append(content_text)
                        yield content_text

                    # 完成状态
                    if status == 2:
                        complete = True

                except Exception as e:
                    nonlocal error
                    error = str(e)

            def on_error(self, ws, err):
                nonlocal error
                error = str(err)

            def on_close(self, ws, code, reason):
                pass

            def on_open(self, ws):
                # 构建请求体 (旧版本格式)
                payload = {
                    "header": {
                        "app_id": self.app_id or "",
                        "uid": str(uuid.uuid4()),
                    },
                    "parameter": {
                        "chat": {
                            "domain": self.domain,
                            "temperature": kwargs.get("temperature", self.temperature),
                            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                            "top_k": kwargs.get("top_k", self.top_k),
                            "chat_id": str(uuid.uuid4()),
                            "stream": True,
                        }
                    },
                    "payload": {
                        "message": {
                            "text": self._format_messages(messages)
                        }
                    },
                }

                ws.send(json.dumps(payload))

        # 创建处理器
        handler = StreamHandler()

        # 创建 WebSocket 连接
        ws = websocket.WebSocketApp(
            auth_url,
            on_message=handler.on_message,
            on_error=handler.on_error,
            on_close=handler.on_close,
        )

        # 添加 on_open 回调
        ws.on_open = handler.on_open

        # 运行连接
        import threading

        thread = threading.Thread(target=ws.run_forever, daemon=True)
        thread.start()

        # 等待完成
        while not complete and error is None:
            import time
            time.sleep(0.1)

        if error:
            raise Exception(f"讯飞 API 错误: {error}")

    def supports_function_calling(self) -> bool:
        """讯飞 X2 版本支持函数调用"""
        return self.version in ("x2", "x1.5")

    def supports_vision(self) -> bool:
        """讯飞不支持视觉"""
        return False

    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model
