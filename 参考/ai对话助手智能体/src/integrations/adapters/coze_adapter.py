"""
Coze 平台适配器

封装 Coze 平台 API 调用，支持对话和工具调用能力。
作为讯飞大模型的补充，处理需要工具调用的场景。
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Iterator, Union

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class CozeAdapter(BaseLLMAdapter):
    """
    Coze 平台适配器

    封装 Coze 平台的 API 调用，提供:
    - 对话能力 (chat)
    - 流式对话 (stream_chat)
    - 工具调用 (通过 Coze Agent)

    用于与讯飞大模型配合，处理需要工具调用的场景。
    """

    # Coze API 配置
    BASE_URL = "https://api.coze.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Coze 适配器

        Args:
            api_key: Coze API Key (从环境变量 COZE_WORKLOAD_IDENTITY_API_KEY 获取)
            base_url: API 基础 URL
            conversation_id: 会话 ID (用于多轮对话)
        """
        self.api_key = api_key or os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        self.base_url = base_url or self.BASE_URL
        self.conversation_id = conversation_id

        if not self.api_key:
            logger.warning("Coze API Key 未配置，某些功能可能不可用")

        super().__init__(model="coze-agent", **kwargs)

    @property
    def provider_name(self) -> str:
        return "coze"

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        发送对话请求 (非流式)

        Args:
            messages: 对话消息列表
            **kwargs: 其他参数

        Returns:
            助手的回复文本
        """
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "messages": messages,
                "stream": False
            }

            # 添加可选参数
            if self.conversation_id:
                payload["conversation_id"] = self.conversation_id

            response = requests.post(
                f"{self.base_url}/chat",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 60)
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [{}])[-1].get("content", "")
            else:
                logger.error(f"Coze API 错误: {response.status_code} - {response.text}")
                return f"Coze API 调用失败: {response.status_code}"

        except ImportError:
            return "Coze 适配器需要 requests 库支持"
        except Exception as e:
            logger.error(f"Coze chat 错误: {e}")
            return f"Coze chat 调用失败: {str(e)}"

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Iterator[str]:
        """
        发送流式对话请求

        Args:
            messages: 对话消息列表
            **kwargs: 其他参数

        Yields:
            增量文本片段
        """
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "messages": messages,
                "stream": True
            }

            if self.conversation_id:
                payload["conversation_id"] = self.conversation_id

            response = requests.post(
                f"{self.base_url}/chat",
                headers=headers,
                json=payload,
                stream=True,
                timeout=kwargs.get("timeout", 60)
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "message":
                                content = data.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
            else:
                logger.error(f"Coze API 错误: {response.status_code}")
                yield f"Coze API 调用失败: {response.status_code}"

        except ImportError:
            yield "Coze 适配器需要 requests 库支持"
        except Exception as e:
            logger.error(f"Coze stream_chat 错误: {e}")
            yield f"Coze stream_chat 调用失败: {str(e)}"

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送带工具调用的对话请求

        这是 Coze 适配器的核心功能，用于处理需要工具调用的场景。

        Args:
            messages: 对话消息列表
            tools: 可用工具列表
            **kwargs: 其他参数

        Returns:
            包含响应和工具调用信息的字典
        """
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "messages": messages,
                "stream": False
            }

            if tools:
                payload["tools"] = tools

            if self.conversation_id:
                payload["conversation_id"] = self.conversation_id

            response = requests.post(
                f"{self.base_url}/chat",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 120)
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Coze API 错误: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API 调用失败: {response.status_code}",
                    "content": ""
                }

        except ImportError:
            return {
                "success": False,
                "error": "需要 requests 库支持",
                "content": ""
            }
        except Exception as e:
            logger.error(f"Coze chat_with_tools 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }

    def invoke_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 Coze 工作流

        Args:
            workflow_id: 工作流 ID
            input_data: 输入数据
            **kwargs: 其他参数

        Returns:
            工作流执行结果
        """
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "workflow_id": workflow_id,
                "input": input_data
            }

            response = requests.post(
                f"{self.base_url}/workflows/run",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 300)
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Coze Workflow API 错误: {response.status_code}")
                return {
                    "success": False,
                    "error": f"工作流调用失败: {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Coze invoke_workflow 错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def set_conversation_id(self, conversation_id: str) -> None:
        """设置会话 ID"""
        self.conversation_id = conversation_id

    def get_conversation_id(self) -> Optional[str]:
        """获取会话 ID"""
        return self.conversation_id

    def reset_conversation(self) -> None:
        """重置会话"""
        self.conversation_id = None

    @staticmethod
    def get_capabilities() -> Dict[str, bool]:
        """
        获取 Coze 适配器的能力

        Returns:
            能力字典
        """
        return {
            "chat": True,
            "stream_chat": True,
            "chat_with_tools": True,
            "invoke_workflow": True,
            "multi_modal": True,
            "vision": True,
            "function_calling": True,
        }
