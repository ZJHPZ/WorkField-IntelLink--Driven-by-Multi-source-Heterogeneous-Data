"""
豆包 (Doubao) 模型适配器

基于火山引擎大模型服务平台
"""

import os
import json
import logging
from typing import Any, Dict, Iterator, List, Optional

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class DoubaoAdapter(BaseLLMAdapter):
    """
    豆包模型适配器

    使用 ChatOpenAI 封装火山引擎 API
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化豆包适配器

        Args:
            config: 模型配置
                - model: 模型名称 (如 doubao-seed-2-0-lite-260215)
                - api_key: API密钥 (从环境变量 COZE_WORKLOAD_IDENTITY_API_KEY 获取)
                - base_url: API地址 (从环境变量 COZE_INTEGRATION_MODEL_BASE_URL 获取)
                - temperature: 温度参数
                - top_p: top_p 参数
                - max_tokens: 最大token数
                - timeout: 超时时间
                - thinking: 是否启用思考模式
        """
        super().__init__(config)

        # 判断是否使用火山方舟
        # use_ark=True: 使用火山方舟 API（仅 MultimodalUnderstandingAgent 使用）
        # use_ark=False: 使用 Coze 内部大模型（QA Agent 等使用）
        self.use_ark = config.get("use_ark", False)

        if self.use_ark:
            # 火山方舟 API 配置
            self.api_key = config.get("api_key") or os.getenv("ARK_API_KEY")
            
            # 如果没有专门的火山方舟 Key，从火山方舟集成获取
            if not self.api_key:
                try:
                    from coze_workload_identity import Client
                    client = Client()
                    credential = client.get_integration_credential("integration-volcano-ark")
                    data = json.loads(credential)
                    self.api_key = data.get("ark_api_key", "")
                    logger.info("[DoubaoAdapter] Using Ark API Key from integration")
                except Exception as e:
                    logger.warning(f"[DoubaoAdapter] Failed to get Ark API Key: {e}")
            
            # 火山方舟端点
            self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
            logger.info("[DoubaoAdapter] Using Volcano Ark endpoint for vision")
        else:
            # Coze 内部大模型配置（默认）
            self.api_key = config.get("api_key") or os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
            self.base_url = config.get("base_url") or os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
            logger.info("[DoubaoAdapter] Using Coze internal LLM")

        if not self.api_key:
            logger.warning("API密钥未配置，将使用环境变量 COZE_WORKLOAD_IDENTITY_API_KEY")
        if not self.base_url:
            logger.warning("API地址未配置，将使用环境变量 COZE_INTEGRATION_MODEL_BASE_URL")

        # 豆包特有配置
        self.thinking = config.get("thinking", "disabled")

        # 初始化 ChatOpenAI
        self._llm = self._init_llm()

    def _init_llm(self):
        """
        初始化 ChatOpenAI 实例
        """
        try:
            from langchain_openai import ChatOpenAI
            from coze_coding_utils.runtime_ctx.context import default_headers
        except ImportError as e:
            logger.error(f"缺少依赖包: {e}")
            raise ImportError("请安装 langchain-openai 和 coze-coding-utils")

        extra_body = {
            "thinking": {
                "type": self.thinking
            }
        }

        # 如果配置了 ctx，可以传入 default_headers
        ctx = self.config.get("ctx")
        headers = default_headers(ctx) if ctx else {}

        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            max_completion_tokens=self.max_tokens,
            streaming=self.streaming,
            timeout=self.timeout,
            default_headers=headers,
            extra_body=extra_body,
        )

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        同步对话

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            助手回复文本
        """
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        # 转换消息格式
        langchain_messages = self._convert_messages(messages)

        # 调用模型
        response = self._llm.invoke(langchain_messages)

        return response.content if hasattr(response, "content") else str(response)

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式对话

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            逐步输出的文本片段
        """
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        # 转换消息格式
        langchain_messages = self._convert_messages(messages)

        # 流式调用
        for chunk in self._llm.stream(langchain_messages):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                yield content

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """
        将消息格式转换为 LangChain 格式
        """
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

        result = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            elif role == "tool":
                result.append(ToolMessage(content=content, tool_call_id=msg.get("tool_call_id", "")))
            else:
                # 默认作为用户消息处理
                result.append(HumanMessage(content=content))

        return result

    def get_model_name(self) -> str:
        """
        获取模型名称
        """
        return self.model

    def invoke_with_state(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """
        使用 LangChain 的 with_config 调用

        适用于需要传递额外配置的复杂场景

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            LangChain 响应对象
        """
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        langchain_messages = self._convert_messages(messages)

        # 如果传入了 config
        config = kwargs.pop("config", None)
        if config:
            return self._llm.invoke(langchain_messages, config=config)

        return self._llm.invoke(langchain_messages)

    def __repr__(self) -> str:
        return f"<DoubaoAdapter model={self.model} base_url={self.base_url}>"

    @classmethod
    def get_capabilities(cls) -> Dict[str, bool]:
        """
        获取豆包模型的能力列表

        Returns:
            能力字典
        """
        return {
            "chat": True,
            "streaming": True,
            "function_calling": True,  # 支持 Tool Calling
            "vision": True,  # 支持图片理解
            "audio": False,  # 豆包本身不支持，需要 Audio 技能
        }
