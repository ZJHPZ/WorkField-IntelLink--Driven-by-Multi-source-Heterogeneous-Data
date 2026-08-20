"""
Conversation Agent - 对话学习Agent
功能：对话采集、特征抽取、用户画像管理
处理模式：联邦式（独立处理）
"""
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..base.message import AgentMessage, MessageType
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context
from ..system_prompts import (
    CONVERSATION_AGENT_PROMPT,
    format_response,
    get_error_response
)

logger = logging.getLogger(__name__)


class ConversationAgent(BaseAgent):
    """
    对话学习Agent
    
    核心职责：
    1. 采集用户对话内容
    2. 抽取用户学习特征（6维特征）
    3. 管理用户画像
    4. 识别学习意图和偏好
    """
    
    def __init__(self):
        super().__init__(
            agent_id="conversation",
            name="对话学习Agent",
            description="负责对话采集、特征抽取和用户画像管理",
            processing_mode=ProcessingMode.FEDERATED
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具（将在初始化时绑定）
        self._tools = None
        
        logger.info("[ConversationAgent] Initialized")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.CONVERSATION
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        # 构建工具映射
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[ConversationAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理对话请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing conversation: {user_input[:50]}...")
        
        results = {}
        
        # 1. 保存用户对话
        conversation_result = await self._save_conversation(user_id, "user", user_input)
        results["conversation_saved"] = conversation_result
        
        # 2. 抽取学习特征
        features = await self._extract_features(user_input)
        results["extracted_features"] = features
        
        # 3. 更新用户画像
        if features:
            profile_update = await self._update_profile(user_id, features)
            results["profile_updated"] = profile_update
        
        # 4. 更新共享上下文
        await self._update_shared_context(user_id, features)
        
        # 5. 获取对话历史
        conversation_history = self._get_conversation_history(state)
        
        # 6. 生成响应
        response = await self._generate_response(user_input, features, conversation_history)
        results["response"] = response
        
        # 7. 保存助手回复
        await self._save_conversation(user_id, "assistant", response)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "conversation_saved": True,
            "features_extracted": bool(features),
            "profile_updated": bool(features),
            "response": response,
            "features": features
        }
    
    def _get_latest_user_input(self, state: MultiAgentState) -> str:
        """获取最新用户输入"""
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
    
    def _get_conversation_history(self, state: MultiAgentState) -> List[Dict]:
        """获取对话历史"""
        messages = state.get("messages", [])
        history = []
        
        for msg in messages:
            content = None
            role = "user"
            
            if isinstance(msg, dict):
                content = msg.get("content", "")
                role = msg.get("role", "user")
            elif hasattr(msg, "content"):
                content = msg.content
                role = getattr(msg, "type", "user")
                # 转换 type 到 role
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
            
            if content and isinstance(content, str):
                history.append({"role": role, "content": content})
        
        return history
    
    async def _save_conversation(
        self,
        user_id: str,
        role: str,
        content: str
    ) -> Dict[str, Any]:
        """保存对话记录"""
        if self._tools and "save_conversation" in self._tool_map:
            try:
                tool = self._tool_map["save_conversation"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"user_id": user_id, "role": role, "content": content}
                )
                self.log_info(f"Conversation saved: {result[:100]}...")
                return {"success": True, "result": result}
            except Exception as e:
                self.log_error(f"Failed to save conversation: {e}")
                return {"success": False, "error": str(e)}
        else:
            # 模拟保存
            self.log_info(f"Simulated save: user={user_id}, role={role}, content_len={len(content)}")
            return {"success": True, "simulated": True}
    
    async def _extract_features(self, user_input: str) -> Dict[str, Any]:
        """
        抽取学习特征
        
        基于用户输入分析6维特征：
        - learning_style: 学习风格
        - knowledge_level: 知识水平
        - learning_goal: 学习目标
        - learning_speed: 学习速度
        - learning_preference: 学习偏好
        - learning_progress: 学习进度
        """
        # 简单的关键词匹配进行特征抽取
        features = {}
        
        # 学习风格识别
        style_keywords = {
            "视觉": ["图片", "图", "可视化", "图表", "颜色", "视觉"],
            "听觉": ["听", "音频", "视频", "讲解", "声音", "播放"],
            "阅读": ["文字", "文档", "阅读", "文章", "看书", "资料"],
            "动觉": ["实践", "动手", "练习", "做", "操作", "实验"]
        }
        
        for style, keywords in style_keywords.items():
            if any(kw in user_input for kw in keywords):
                features["learning_style"] = style
                break
        
        # 知识水平识别
        level_keywords = {
            "入门": ["零基础", "初学", "入门", "刚开始", "不了解"],
            "初级": ["基础", "简单", "初级", "基本概念"],
            "中级": ["进阶", "深入", "中级", "提高", "熟练"],
            "高级": ["高级", "专家", "精通", "深度", "复杂"]
        }
        
        for level, keywords in level_keywords.items():
            if any(kw in user_input for kw in keywords):
                features["knowledge_level"] = level
                break
        
        # 学习目标识别
        goal_keywords = ["想学", "目标是", "目的是", "希望", "为了", "考试", "工作", "兴趣"]
        if any(kw in user_input for kw in goal_keywords):
            features["learning_goal"] = user_input
        
        return features
    
    async def _update_profile(
        self,
        user_id: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新用户画像"""
        if self._tools and "update_user_feature" in self._tool_map:
            try:
                for feature_type, feature_value in features.items():
                    tool = self._tool_map["update_user_feature"]
                    result = await asyncio.to_thread(
                        tool.invoke,
                        {
                            "user_id": user_id,
                            "feature_type": feature_type,
                            "feature_value": json.dumps(feature_value)
                        }
                    )
                return {"success": True, "features_updated": len(features)}
            except Exception as e:
                self.log_error(f"Failed to update profile: {e}")
                return {"success": False, "error": str(e)}
        else:
            self.log_info(f"Simulated profile update: {features}")
            return {"success": True, "simulated": True}
    
    async def _update_shared_context(
        self,
        user_id: str,
        features: Dict[str, Any]
    ) -> None:
        """更新共享上下文"""
        try:
            # 更新用户画像
            profile = self.shared_context.get_user_profile(user_id)
            if profile:
                profile.update(features)
                self.shared_context.update_user_profile(user_id, profile)
            else:
                self.shared_context.update_user_profile(user_id, features)
            
            self.log_info(f"Updated shared context for user {user_id}")
        except Exception as e:
            self.log_error(f"Failed to update shared context: {e}")
    
    async def _generate_response(
        self,
        user_input: str,
        features: Dict[str, Any],
        conversation_history: List[Dict] = None
    ) -> str:
        """生成响应内容 - 使用真正的 AI 模型和完整的 System Prompt"""
        try:
            from coze_coding_dev_sdk import LLMClient
            from langchain_core.messages import HumanMessage, SystemMessage
            from coze_coding_utils.runtime_ctx.context import new_context
            
            # 获取 Context
            ctx = new_context(method="conversation_response")
            
            # 创建 LLM 客户端
            client = LLMClient(ctx=ctx)
            
            # 构建消息列表
            messages = []
            
            # 1. 添加 System Prompt（完整的角色定义）
            messages.append(SystemMessage(content=CONVERSATION_AGENT_PROMPT))
            
            # 2. 添加用户画像上下文
            style = features.get("learning_style", "通用")
            level = features.get("knowledge_level", "未知")
            profile_context = f"\n\n【当前用户画像】\n- 学习风格：{style}\n- 知识水平：{level}\n"
            messages.append(HumanMessage(content=profile_context))
            
            # 3. 添加对话历史（如果有）
            if conversation_history:
                history_text = "\n\n【对话历史】\n"
                for msg in conversation_history[-6:]:  # 限制最近3轮对话
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    history_text += f"{'用户' if role == 'user' else '助手'}：{content}\n"
                messages.append(HumanMessage(content=history_text))
            
            # 4. 添加当前用户输入
            messages.append(HumanMessage(content=f"\n\n【当前问题】\n{user_input}"))
            
            # 调用 LLM
            response = client.invoke(
                messages=messages,
                temperature=0.7
            )
            
            # 处理响应内容
            content = response.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                if content and isinstance(content[0], str):
                    return " ".join(content)
                else:
                    text_parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
                    return " ".join(text_parts)
            return str(content)
            
        except Exception as e:
            self.log_error(f"LLM call failed: {e}")
            return await self._fallback_response(user_input, features)
    
    async def _fallback_response(
        self,
        user_input: str,
        features: Dict[str, Any]
    ) -> str:
        """备用响应 - 当 LLM 不可用时使用"""
        style = features.get("learning_style", "通用")
        level = features.get("knowledge_level", "未知")
        
        # 检查是否有明确的学习请求
        if any(kw in user_input for kw in ["学习", "了解", "知道", "什么"]):
            return f"好的！我来帮你学习。根据你的{style}学习风格和{level}水平，我会为你定制合适的学习内容。"
        
        # 一般对话
        return "收到，我会记住你的学习偏好。有什么学习需求随时告诉我！"
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """获取用户历史对话"""
        if self._tools and "get_user_conversations" in self._tool_map:
            try:
                tool = self._tool_map["get_user_conversations"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"user_id": user_id, "limit": limit}
                )
                return json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                self.log_error(f"Failed to get conversations: {e}")
                return {"error": str(e)}
        
        return {"conversations": [], "total": 0}
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        if self._tools and "get_user_profile" in self._tool_map:
            try:
                tool = self._tool_map["get_user_profile"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"user_id": user_id}
                )
                return json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                self.log_error(f"Failed to get profile: {e}")
                return {"error": str(e)}
        
        return {"user_id": user_id, "exists": False}


# 全局实例
_conversation_agent: Optional[ConversationAgent] = None


def get_conversation_agent() -> ConversationAgent:
    """获取全局ConversationAgent实例"""
    global _conversation_agent
    if _conversation_agent is None:
        _conversation_agent = ConversationAgent()
    return _conversation_agent
