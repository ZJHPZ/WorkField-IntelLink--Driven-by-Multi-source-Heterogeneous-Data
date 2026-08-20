"""
Email Agent - 邮件发送Agent
功能：发送学习内容邮件、生成邮件内容
处理模式：联邦式（独立处理）
"""
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode

logger = logging.getLogger(__name__)


class EmailAgent(BaseAgent):
    """
    邮件Agent
    
    核心职责：
    1. 发送学习计划邮件
    2. 发送练习题集邮件
    3. 发送评估报告邮件
    4. 发送多媒体内容邮件
    """
    
    def __init__(self):
        super().__init__(
            agent_id="email",
            name="邮件发送Agent",
            description="负责发送学习内容邮件",
            processing_mode=ProcessingMode.FEDERATED
        )
        
        # 工具
        self._tools = None
        
        logger.info("[EmailAgent] Initialized")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.EMAIL
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[EmailAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理邮件发送请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        # ✅ 保存状态，用于跨Agent数据传递
        self._set_state(state)
        
        user_input = self._get_latest_user_input(state)
        
        self.log_info(f"Processing email request: {user_input[:50]}...")
        
        # 1. 解析邮件发送请求
        request = self._parse_email_request(user_input)
        
        # 2. 获取邮件内容
        content = await self._get_email_content(request)
        
        # 3. 发送邮件
        result = await self._send_email(request, content)
        
        # 4. 生成响应
        response = self._format_response(result)
        
        return {
            "success": result.get("success", False),
            "agent": self.agent_id,
            "request": request,
            "result": result,
            "response": response
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
    
    def _parse_email_request(self, user_input: str) -> Dict[str, Any]:
        """解析邮件发送请求"""
        request = {
            "type": "general",
            "email": None,
            "content_type": "text"
        }
        
        # 提取邮箱地址
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        if emails:
            request["email"] = emails[0]
        
        # 确定邮件类型
        if "学习计划" in user_input:
            request["type"] = "learning_plan"
            request["subject"] = "你的学习计划"
        elif "练习题" in user_input or "题目" in user_input:
            request["type"] = "questions"
            request["subject"] = "练习题集"
        elif "评估" in user_input or "报告" in user_input:
            request["type"] = "evaluation"
            request["subject"] = "学习评估报告"
        elif "思维导图" in user_input or "图" in user_input:
            request["type"] = "mindmap"
            request["subject"] = "知识思维导图"
            request["content_type"] = "image"
        else:
            request["subject"] = "学习助手内容"
        
        return request
    
    async def _get_email_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """获取邮件内容"""
        email_type = request.get("type", "general")
        content_type = request.get("content_type", "text")
        
        # ✅ 尝试从上下文中获取前置Agent的结果
        context_content = self._get_content_from_context(email_type)
        if context_content:
            return context_content
        
        if email_type == "learning_plan":
            return await self._get_learning_plan_content()
        elif email_type == "questions":
            return await self._get_questions_content()
        elif email_type == "evaluation":
            return await self._get_evaluation_content()
        elif email_type == "mindmap":
            return await self._get_mindmap_content()
        else:
            return {"text": "这是一封来自学习助手的邮件。", "images": []}
    
    def _get_content_from_context(self, email_type: str) -> Optional[Dict[str, Any]]:
        """✅ 新增：从上下文中获取前置Agent生成的内容"""
        if not hasattr(self, '_state') or not self._state:
            return None
        
        agent_results = self._state.get("agent_results", {})
        
        # 尝试获取学习计划
        if email_type == "learning_plan":
            for agent_id, result_data in agent_results.items():
                if "learning_path" in str(agent_id):
                    response = result_data.get("response", "")
                    if response:
                        return {
                            "subject": "学习计划",
                            "text": f"你的学习计划已制定完成！\n\n{response}",
                            "images": []
                        }
        
        # 尝试获取多媒体
        if email_type == "mindmap":
            for agent_id, result_data in agent_results.items():
                if "multimedia" in str(agent_id):
                    response = result_data.get("response", "")
                    if response:
                        # 尝试提取图片URL
                        import re
                        img_urls = re.findall(r'https?://[^\s\)]+\.(?:png|jpg|jpeg|gif|webp)', response)
                        return {
                            "subject": "思维导图",
                            "text": f"你的思维导图已生成！\n\n{response}",
                            "images": img_urls
                        }
        
        return None
    
    def _set_state(self, state: MultiAgentState):
        """✅ 新增：设置状态，用于跨Agent数据传递"""
        self._state = state
    
    async def _get_learning_plan_content(self) -> Dict[str, Any]:
        """获取学习计划邮件内容"""
        if self._tools and "generate_learning_path" in self._tool_map:
            try:
                tool = self._tool_map["generate_learning_path"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"subject": "Python编程", "knowledge_level": "初级", "learning_speed": "中速"}
                )
                data = json.loads(result) if isinstance(result, str) else result
                path = data.get("learning_path", {})
                
                return {
                    "subject": "Python学习计划",
                    "text": f"你的Python学习计划已制定完成！\n\n{path.get('meta', {}).get('estimated_duration', '30天')}系统学习路径，包含{path.get('meta', {}).get('total_stages', 3)}个阶段。",
                    "images": []
                }
            except Exception as e:
                self.log_error(f"Failed to generate learning plan: {e}")
        
        return {
            "subject": "Python学习计划",
            "text": "你的学习计划已制定完成，请查收！",
            "images": []
        }
    
    async def _get_questions_content(self) -> Dict[str, Any]:
        """获取练习题邮件内容"""
        if self._tools and "generate_multiple_choice" in self._tool_map:
            try:
                tool = self._tool_map["generate_multiple_choice"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"subject": "Python编程", "topic": "Python基础知识", "difficulty": "简单", "count": 5}
                )
                data = json.loads(result) if isinstance(result, str) else result
                questions = data.get("questions", [])
                
                text = f"为你准备了{len(questions)}道练习题，请查收！\n\n"
                text += "\n".join([f"- 第{q.get('id', i+1)}题：{q.get('question', '')[:50]}..." for i, q in enumerate(questions[:5])])
                
                return {
                    "subject": "练习题集",
                    "text": text,
                    "images": []
                }
            except Exception as e:
                self.log_error(f"Failed to generate questions: {e}")
        
        return {
            "subject": "练习题集",
            "text": "为你准备了练习题，请查收！",
            "images": []
        }
    
    async def _get_evaluation_content(self) -> Dict[str, Any]:
        """获取评估报告邮件内容"""
        return {
            "subject": "学习评估报告",
            "text": "你的学习评估报告已生成，请查收详细分析和建议。",
            "images": []
        }
    
    async def _get_mindmap_content(self) -> Dict[str, Any]:
        """获取思维导图邮件内容"""
        images = []
        
        if self._tools and "generate_concept_diagram" in self._tool_map:
            try:
                tool = self._tool_map["generate_concept_diagram"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"subject": "Python编程", "concept": "Python学习路径", "diagram_type": "mindmap"}
                )
                data = json.loads(result) if isinstance(result, str) else result
                if data.get("success") and data.get("image_url"):
                    images.append(data.get("image_url"))
            except Exception as e:
                self.log_error(f"Failed to generate mindmap: {e}")
        
        return {
            "subject": "知识思维导图",
            "text": "为你生成了知识思维导图，请查收！" if images else "思维导图生成中，请稍后再试。",
            "images": images
        }
    
    async def _send_email(self, request: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送邮件"""
        email = request.get("email")
        
        if not email:
            return {"success": False, "error": "未提供邮箱地址"}
        
        # 使用邮件发送工具
        if self._tools and self._tool_map:
            # ✅ 优先尝试发送带图片的邮件（如果有图片）
            images = content.get("images", [])
            if images and "send_email_with_image" in self._tool_map:
                try:
                    tool = self._tool_map["send_email_with_image"]
                    result = await asyncio.to_thread(
                        tool.invoke,
                        {
                            "to_addrs": [email],
                            "subject": content.get("subject", request.get("subject", "学习助手")),
                            "content": content.get("text", ""),
                            "image_urls": images
                        }
                    )
                    return json.loads(result) if isinstance(result, str) else result
                except Exception as e:
                    self.log_error(f"Failed to send email with image: {e}")
            
            # ✅ 尝试发送学习计划邮件
            if "send_learning_plan_email" in self._tool_map:
                try:
                    tool = self._tool_map["send_learning_plan_email"]
                    result = await asyncio.to_thread(
                        tool.invoke,
                        {
                            "to_email": email,
                            "subject": content.get("subject", "学习计划"),
                            "plan_content": content.get("text", "")
                        }
                    )
                    return json.loads(result) if isinstance(result, str) else result
                except Exception as e:
                    self.log_error(f"Failed to send learning plan email: {e}")
            
            # ✅ 尝试发送通用邮件发送（兜底方案）
            if "send_text_email" in self._tool_map:
                try:
                    tool = self._tool_map["send_text_email"]
                    result = await asyncio.to_thread(
                        tool.invoke,
                        {
                            "to_addrs": [email],
                            "subject": content.get("subject", "学习助手"),
                            "content": content.get("text", "")
                        }
                    )
                    return json.loads(result) if isinstance(result, str) else result
                except Exception as e:
                    self.log_error(f"Failed to send email: {e}")
        
        return {
            "success": False,
            "error": "邮件服务暂不可用"
        }
    
    def _format_response(self, result: Dict[str, Any]) -> str:
        """格式化响应内容"""
        # ✅ 修复：支持 "status" 和 "success" 两种返回格式
        is_success = result.get("success") or result.get("status") == "success"
        if is_success:
            return f"""✅ **邮件发送成功！**

📧 邮件已发送到：{result.get('recipient_count', result.get('recipient', 1))}个收件人
📎 包含内容：{result.get('images_count', result.get('has_images', 0))}张图片

请查收邮件，如有问题可以随时告诉我！ 😊
"""
        else:
            return f"""❌ **邮件发送失败**

原因：{result.get('error', result.get('message', '未知错误'))}

请检查邮箱地址是否正确，或稍后重试。"""

# 全局实例
_email_agent: Optional[EmailAgent] = None


def get_email_agent() -> EmailAgent:
    """✅ 获取全局EmailAgent实例（使用AgentFactory获取带工具的实例）"""
    global _email_agent
    if _email_agent is None:
        # ✅ 尝试从 AgentFactory 获取带工具的实例
        try:
            from multi_agent.agent_factory import AgentFactory
            factory = AgentFactory()
            _email_agent = factory.create_agent_instance("email")
        except Exception as e:
            logger.warning(f"[EmailAgent] Failed to get from factory, creating direct instance: {e}")
            _email_agent = EmailAgent()
    return _email_agent
