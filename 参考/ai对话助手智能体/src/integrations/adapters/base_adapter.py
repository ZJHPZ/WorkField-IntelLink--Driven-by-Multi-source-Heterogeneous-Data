"""
LLM 适配器基类

所有模型适配器必须继承此类并实现抽象方法
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Iterator
import logging

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """
    LLM 适配器基类

    所有模型适配器必须继承此类并实现以下抽象方法:
    - chat() - 同步对话
    - stream_chat() - 流式对话
    - get_model_name() - 获取模型名称

    可选实现:
    - chat_completions_format() - OpenAI兼容格式
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器

        Args:
            config: 模型配置，包含:
                - model: 模型名称
                - temperature: 温度参数
                - top_p: top_p 参数
                - max_tokens: 最大token数
                - timeout: 超时时间
                等...
        """
        self.config = config
        self.model = config.get("model", "unknown")
        self.temperature = config.get("temperature", 0.7)
        self.top_p = config.get("top_p", 0.9)
        self.max_tokens = config.get("max_completion_tokens", 4096)
        self.timeout = config.get("timeout", 600)
        self.streaming = config.get("streaming", True)

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        同步对话

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数

        Returns:
            助手回复文本
        """
        pass

    @abstractmethod
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式对话

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            逐步输出的文本片段
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        获取模型名称

        Returns:
            模型名称字符串
        """
        pass

    def chat_completions_format(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI Chat Completions 兼容格式转换

        Args:
            messages: 消息列表
            model: 模型名称 (可选)
            stream: 是否流式
            **kwargs: 其他参数

        Returns:
            OpenAI兼容格式的请求字典
        """
        return {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """
        验证消息格式

        Args:
            messages: 消息列表

        Returns:
            是否有效
        """
        if not messages:
            return False

        valid_roles = {"system", "user", "assistant", "function", "tool"}
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in valid_roles:
                return False

        return True

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置字典
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "streaming": self.streaming,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model}>"


class AsyncBaseLLMAdapter(BaseLLMAdapter):
    """
    异步 LLM 适配器基类

    如果底层模型支持异步操作，可继承此类
    """

    @abstractmethod
    async def async_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        异步对话

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            助手回复文本
        """
        pass

    @abstractmethod
    async def async_stream_chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncIterator[str]:
        """
        异步流式对话

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            逐步输出的文本片段
        """
        pass
