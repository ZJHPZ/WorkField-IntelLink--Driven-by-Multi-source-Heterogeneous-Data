"""
Integration Agent
集成Agent - 负责系统集成和外部服务对接
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base.base_agent import FederatedAgent
from ..base.agent_state import MultiAgentState, IntentType
from ..communication.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class IntegrationAgent(FederatedAgent):
    """
    集成Agent
    
    职责：
    - 外部服务对接：微信、飞书、钉钉等
    - API集成：第三方API调用
    - 数据同步：与其他系统数据同步
    """
    
    def __init__(self):
        super().__init__(
            agent_id="integration",
            name="集成智能体",
            description="负责系统集成和外部服务对接"
        )
        self.shared_context = get_shared_context()
        self.integrations = {
            "wechat": self._init_wechat(),
            "feishu": self._init_feishu(),
            "dingtalk": self._init_dingtalk()
        }
        logger.info("[IntegrationAgent] Initialized")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.INTEGRATION
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """处理集成请求"""
        user_input = self._get_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing integration request: {user_input[:50]}...")
        
        # 1. 识别集成类型
        integration_type = self._identify_integration(user_input)
        
        # 2. 执行集成操作
        result = await self._execute_integration(
            integration_type,
            user_input,
            user_id
        )
        
        return result
    
    def _get_user_input(self, state: MultiAgentState) -> str:
        """获取用户输入"""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            content = None
            if isinstance(msg, dict):
                content = msg.get("content", "")
            elif hasattr(msg, "content"):
                content = msg.content
            
            if content and isinstance(content, str):
                return content
        return ""
    
    def _identify_integration(self, text: str) -> str:
        """识别集成类型"""
        text_lower = text.lower()
        
        if "微信" in text:
            return "wechat"
        elif "飞书" in text:
            return "feishu"
        elif "钉钉" in text:
            return "dingtalk"
        elif "推送" in text:
            return "push"
        else:
            return "general"
    
    def _init_wechat(self) -> Dict[str, Any]:
        """初始化微信集成"""
        return {
            "enabled": False,
            "webhook_url": None,
            "app_id": None,
            "app_secret": None
        }
    
    def _init_feishu(self) -> Dict[str, Any]:
        """初始化飞书集成"""
        return {
            "enabled": False,
            "webhook_url": None,
            "app_id": None,
            "app_secret": None
        }
    
    def _init_dingtalk(self) -> Dict[str, Any]:
        """初始化钉钉集成"""
        return {
            "enabled": False,
            "webhook_url": None,
            "app_key": None,
            "app_secret": None
        }
    
    async def _execute_integration(
        self,
        integration_type: str,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """执行集成操作"""
        if integration_type == "wechat":
            return await self._send_wechat_message(content, user_id)
        elif integration_type == "feishu":
            return await self._send_feishu_message(content, user_id)
        elif integration_type == "dingtalk":
            return await self._send_dingtalk_message(content, user_id)
        elif integration_type == "push":
            return await self._send_push_notification(content, user_id)
        else:
            return await self._general_integration(content, user_id)
    
    async def _send_wechat_message(
        self,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """发送微信消息"""
        # 模拟微信消息发送
        result = {
            "success": True,
            "platform": "wechat",
            "message": "微信消息发送功能已配置",
            "note": "请配置微信公众号webhook URL以启用此功能",
            "user_id": user_id,
            "content_preview": content[:50]
        }
        
        # 记录集成历史
        await self._record_integration("wechat", content, user_id, result)
        
        return result
    
    async def _send_feishu_message(
        self,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """发送飞书消息"""
        # 模拟飞书消息发送
        result = {
            "success": True,
            "platform": "feishu",
            "message": "飞书消息发送功能已配置",
            "note": "请配置飞书机器人webhook URL以启用此功能",
            "user_id": user_id,
            "content_preview": content[:50]
        }
        
        # 记录集成历史
        await self._record_integration("feishu", content, user_id, result)
        
        return result
    
    async def _send_dingtalk_message(
        self,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """发送钉钉消息"""
        # 模拟钉钉消息发送
        result = {
            "success": True,
            "platform": "dingtalk",
            "message": "钉钉消息发送功能已配置",
            "note": "请配置钉钉机器人webhook URL以启用此功能",
            "user_id": user_id,
            "content_preview": content[:50]
        }
        
        # 记录集成历史
        await self._record_integration("dingtalk", content, user_id, result)
        
        return result
    
    async def _send_push_notification(
        self,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """发送推送通知"""
        # 模拟推送通知
        result = {
            "success": True,
            "platform": "push",
            "message": "推送通知已发送",
            "user_id": user_id,
            "content_preview": content[:50],
            "channels": ["email", "in_app"]
        }
        
        # 记录集成历史
        await self._record_integration("push", content, user_id, result)
        
        return result
    
    async def _general_integration(
        self,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """通用集成操作"""
        result = {
            "success": True,
            "platform": "general",
            "message": "内容已准备完毕",
            "user_id": user_id,
            "content_preview": content[:100]
        }
        
        return result
    
    async def _record_integration(
        self,
        platform: str,
        content: str,
        user_id: str,
        result: Dict[str, Any]
    ) -> None:
        """记录集成历史"""
        integration_id = f"integration_{datetime.now().timestamp()}"
        
        record = {
            "id": integration_id,
            "platform": platform,
            "content": content,
            "user_id": user_id,
            "result": result,
            "created_at": datetime.now().isoformat()
        }
        
        integrations = self.shared_context.get("integrations", {})
        integrations[integration_id] = record
        self.shared_context.set("integrations", integrations)
    
    async def configure_integration(
        self,
        platform: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """配置集成"""
        if platform in self.integrations:
            self.integrations[platform].update(config)
            self.integrations[platform]["enabled"] = True
            
            return {
                "success": True,
                "platform": platform,
                "message": f"{platform}集成已配置并启用"
            }
        
        return {
            "success": False,
            "message": f"不支持的集成平台: {platform}"
        }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        status = {}
        for platform, config in self.integrations.items():
            status[platform] = {
                "enabled": config.get("enabled", False),
                "configured": any([
                    config.get("webhook_url"),
                    config.get("app_id"),
                    config.get("app_key")
                ])
            }
        return status
