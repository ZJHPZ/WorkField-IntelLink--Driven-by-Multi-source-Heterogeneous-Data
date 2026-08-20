"""
Agent 协作执行器
处理多 Agent 之间的协作流程
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from uuid import uuid4

from .agent_factory import get_agent_factory
from .base.agent_state import MultiAgentState, IntentType, ProcessingMode
from .base.message import AgentMessage, MessageType
from .communication.message_bus import get_message_bus
from .communication.shared_context import get_shared_context
from .constants import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Agent 协作执行器
    
    负责：
    1. 管理 Agent 间的消息传递
    2. 执行联邦式任务（独立 Agent）
    3. 执行协作式任务（依赖链）
    4. 整合多 Agent 结果
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.factory = get_agent_factory()
        self.message_bus = get_message_bus()
        self.shared_context = get_shared_context()
        
        # 执行状态
        self._execution_results: Dict[str, Dict[str, Any]] = {}
        self._active_agents: List[str] = []
        
        # 协作钩子函数
        self._collaboration_hooks: Dict[str, Callable] = {}
        
        logger.info("[AgentExecutor] Initialized")
    
    def recognize_intent(self, user_input: str) -> Dict[str, Any]:
        """
        识别用户意图
        
        Returns:
            Dict包含 intent, agent_id, confidence, matched_keyword
        """
        user_input_lower = user_input.lower()
        
        # 意图映射表（优先级从高到低）
        intent_map = [
            # 邮件发送（最高优先级）
            (["发送", "邮箱", "email", "发到", "邮件"], "email", 10),
            
            # 学习路径规划
            (["计划", "规划", "安排", "路径", "学习方案", "如何学习"], "learning_path", 8),
            
            # 学习评估
            (["评估", "水平", "诊断", "分析", "检测", "评价"], "evaluation", 8),
            
            # 题库练习
            (["练习", "出题", "做几道", "考试", "测验", "题", "做题"], "question", 7),
            
            # 文档生成
            (["文档", "大纲", "思维导图", "笔记", "整理", "总结"], "document", 7),
            
            # 多媒体
            (["图片", "图解", "示意图", "画一个"], "multimedia", 6),
            (["视频", "动画", "演示"], "multimedia", 6),
            
            # 答疑解惑
            (["疑问", "不懂", "为什么", "怎么", "解释", "讲解", "什么"], "qa", 5),
            
            # 对话学习（最低优先级）
            (["学习", "了解", "知道", "聊聊", "分享", "交流", "谈谈"], "conversation", 1),
        ]
        
        for keywords, intent, priority in intent_map:
            for keyword in keywords:
                if keyword in user_input_lower:
                    agent_id = self.factory.get_agent_id_by_intent(intent)
                    confidence = 0.7 + (priority * 0.02)
                    return {
                        "intent": intent,
                        "agent_id": agent_id,
                        "confidence": confidence,
                        "matched_keyword": keyword,
                        "priority": priority
                    }
        
        # 默认返回对话意图
        return {
            "intent": "conversation",
            "agent_id": "conversation",
            "confidence": 0.5,
            "matched_keyword": None,
            "priority": 0
        }
    
    def check_collaboration_needed(self, intent: str) -> bool:
        """检查是否需要多 Agent 协作"""
        # 协作式意图
        collaborative_intents = ["learning_path", "evaluation", "recommendation"]
        return intent in collaborative_intents
    
    def get_collaboration_chain(self, intent: str) -> List[str]:
        """获取协作链"""
        chains = {
            "learning_path": ["conversation", "learning_path"],  # 需要先了解用户
            "evaluation": ["conversation", "question", "evaluation"],  # 需要先对话和题目结果
            "recommendation": ["conversation", "evaluation", "learning_path", "recommendation"]
        }
        return chains.get(intent, [intent])
    
    def _build_extended_state(self, state: Dict[str, Any], current_input: str) -> Dict[str, Any]:
        """
        构建扩展状态，添加对话历史等上下文信息
        
        Args:
            state: 原始状态
            current_input: 当前用户输入
            
        Returns:
            扩展后的状态
        """
        extended = dict(state)
        
        # 提取对话历史
        messages = state.get("messages", [])
        messages_history = []
        
        for msg in messages:
            content = None
            role = "user"
            
            if isinstance(msg, dict):
                content = msg.get("content", "")
                role = msg.get("role", "user")
            elif hasattr(msg, "content"):
                content = msg.content
                role = getattr(msg, "type", "user")
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
            
            if content and isinstance(content, str):
                messages_history.append({"role": role, "content": content})
        
        extended["messages_history"] = messages_history
        
        # 提取用户画像
        if "user_profile" not in extended:
            extended["features"] = {
                "learning_style": "通用",
                "knowledge_level": "未知",
                "learning_goal": ""
            }
        
        return extended
    
    async def execute_federated(
        self,
        agent_id: str,
        user_input: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行联邦式任务（单个 Agent 独立处理）
        优化版：添加快速路径
        
        Args:
            agent_id: Agent ID
            user_input: 用户输入
            state: 当前状态
            
        Returns:
            执行结果
        """
        start_time = datetime.now()
        self._active_agents.append(agent_id)
        
        logger.info(f"[AgentExecutor] Executing federated task: {agent_id}")
        
        # ✅ 快速路径：简单对话直接使用 LLM 响应
        if agent_id == "conversation" and self._is_simple_conversation(user_input):
            try:
                quick_result = await self._quick_conversation_response(user_input, state)
                self._active_agents.remove(agent_id)
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "intent": "conversation",
                    "output": quick_result,
                    "metadata": {
                        "start_time": start_time.isoformat(),
                        "mode": "federated",
                        "fast_path": True
                    }
                }
            except Exception as e:
                logger.warning(f"[AgentExecutor] Fast path failed, using normal path: {e}")
                # 继续使用正常路径
        
        # 构建扩展状态
        extended_state = self._build_extended_state(state, user_input)
        
        result = {
            "success": True,
            "agent_id": agent_id,
            "intent": self._find_intent_by_agent(agent_id),
            "output": "",
            "metadata": {
                "start_time": start_time.isoformat(),
                "mode": "federated",
                "fast_path": False
            }
        }
        
        try:
            # 获取工具
            tools = self.factory.get_tools_for_agent(agent_id)
            tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
            
            # 根据 Agent 类型执行相应逻辑
            if agent_id == "conversation":
                result["output"] = await self._execute_conversation_agent(user_input, extended_state, tool_map)
            elif agent_id == "document":
                result["output"] = await self._execute_document_agent(user_input, extended_state, tool_map)
            elif agent_id == "question":
                result["output"] = await self._execute_question_agent(user_input, extended_state, tool_map)
            elif agent_id == "multimedia":
                result["output"] = await self._execute_multimedia_agent(user_input, extended_state, tool_map)
            elif agent_id == "qa":
                result["output"] = await self._execute_qa_agent(user_input, state, tool_map)
            elif agent_id == "email":
                result["output"] = await self._execute_email_agent(user_input, state, tool_map)
            else:
                result["output"] = f"[{agent_id}] 收到请求，正在处理..."
            
            result["metadata"]["end_time"] = datetime.now().isoformat()
            
        except asyncio.TimeoutError:
            # ✅ 统一处理：超时错误
            logger.warning(f"[AgentExecutor] Timeout in federated execution: {agent_id}")
            result["success"] = False
            result["error_code"] = ErrorCode.TIMEOUT_ERROR
            result["output"] = ErrorResponse.get_message(ErrorCode.TIMEOUT_ERROR)
            result["metadata"]["end_time"] = datetime.now().isoformat()
            
        except (LLMError, APIError, RateLimitError) as e:
            # ✅ 统一处理：LLM 相关错误
            logger.warning(f"[AgentExecutor] LLM error in federated execution: {e}")
            result["success"] = False
            result["error_code"] = ErrorCode.LLM_ERROR
            result["output"] = ErrorResponse.get_message(ErrorCode.LLM_ERROR)
            result["metadata"]["end_time"] = datetime.now().isoformat()
            
        except ToolExecutionError as e:
            # ✅ 统一处理：工具执行错误
            logger.warning(f"[AgentExecutor] Tool execution error: {e}")
            result["success"] = False
            result["error_code"] = ErrorCode.TOOL_EXECUTION_ERROR
            result["output"] = ErrorResponse.get_message(ErrorCode.TOOL_EXECUTION_ERROR, str(e))
            result["metadata"]["end_time"] = datetime.now().isoformat()
            
        except ValueError as e:
            # ✅ 统一处理：输入验证错误
            logger.warning(f"[AgentExecutor] Invalid input: {e}")
            result["success"] = False
            result["error_code"] = ErrorCode.INVALID_INPUT
            result["output"] = ErrorResponse.get_message(ErrorCode.INVALID_INPUT, str(e))
            result["metadata"]["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            # ✅ 统一处理：其他未知错误
            logger.error(f"[AgentExecutor] Unexpected error in federated execution: {e}")
            result["success"] = False
            result["error_code"] = ErrorCode.UNKNOWN_ERROR
            result["output"] = ErrorResponse.get_message(ErrorCode.UNKNOWN_ERROR)
            result["metadata"]["end_time"] = datetime.now().isoformat()
        
        finally:
            self._active_agents.remove(agent_id)
            self._execution_results[agent_id] = result
        
        return result
    
    async def execute_collaborative(
        self,
        intent: str,
        user_input: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行协作式任务（多 Agent 顺序协作）
        
        Args:
            intent: 意图类型
            user_input: 用户输入
            state: 当前状态
            
        Returns:
            协作执行结果
        """
        start_time = datetime.now()
        chain = self.get_collaboration_chain(intent)
        
        logger.info(f"[AgentExecutor] Executing collaborative chain: {' -> '.join(chain)}")
        
        results = {}
        context = {"user_input": user_input, "state": state}
        
        for agent_id in chain:
            logger.info(f"[AgentExecutor] Executing agent in chain: {agent_id}")
            
            try:
                agent_result = await self.execute_federated(
                    agent_id,
                    context.get("user_input", user_input),
                    context
                )
                results[agent_id] = agent_result
                
                # 将结果传递给下游 Agent
                if agent_result.get("success") and agent_result.get("output"):
                    context[f"{agent_id}_result"] = agent_result["output"]
                
            except Exception as e:
                logger.error(f"[AgentExecutor] Error in collaborative chain at {agent_id}: {e}")
                results[agent_id] = {"success": False, "error": str(e)}
        
        # 整合最终结果
        final_output = self._integrate_results(intent, results)
        
        return {
            "success": True,
            "intent": intent,
            "chain": chain,
            "agent_results": results,
            "output": final_output,
            "metadata": {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "mode": "collaborative",
                "agent_count": len(chain)
            }
        }
    
    def _integrate_results(self, intent: str, results: Dict[str, Any]) -> str:
        """整合多个 Agent 的结果"""
        if not results:
            return "处理完成"
        
        # 根据意图类型整合结果
        if intent == "learning_path":
            # 学习路径：返回最终路径结果
            if "learning_path" in results:
                return results["learning_path"].get("output", "")
            return "学习路径规划完成"
        
        elif intent == "evaluation":
            # 评估：返回评估结果
            if "evaluation" in results:
                return results["evaluation"].get("output", "")
            return "评估完成"
        
        elif intent == "recommendation":
            # 推荐：返回推荐结果
            if "recommendation" in results:
                return results["recommendation"].get("output", "")
            return "推荐完成"
        
        # 默认：返回最后一个成功的结果
        for agent_id in reversed(list(results.keys())):
            result = results[agent_id]
            if result.get("success") and result.get("output"):
                return result["output"]
        
        return "处理完成"
    
    def _find_intent_by_agent(self, agent_id: str) -> str:
        """根据 Agent ID 查找意图"""
        for intent, aid in self.factory._intent_to_agent.items():
            if aid == agent_id:
                return intent
        return agent_id
    
    def _handle_error(
        self,
        error: Exception,
        agent_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """统一错误处理"""
        from multi_agent.constants import ErrorCode, ErrorResponse, AgentError, LLMError, ToolExecutionError
        
        error_type = "unknown"
        error_code = ErrorCode.UNKNOWN_ERROR
        
        if isinstance(error, LLMError):
            error_type = "llm"
            error_code = ErrorCode.LLM_ERROR
        elif isinstance(error, ToolExecutionError):
            error_type = "tool"
            error_code = ErrorCode.TOOL_EXECUTION_ERROR
        elif isinstance(error, TimeoutError):
            error_type = "timeout"
            error_code = ErrorCode.TIMEOUT_ERROR
        elif isinstance(error, AgentError):
            error_type = "agent"
            error_code = ErrorCode.AGENT_ERROR
        
        error_message = ErrorResponse.get_message(error_code)
        
        return {
            "success": False,
            "agent_id": agent_id,
            "error_type": error_type,
            "error_code": error_code,
            "output": error_message,
            "details": str(error) if not isinstance(error, (LLMError, ToolExecutionError, TimeoutError, AgentError)) else None
        }
    
    async def _execute_conversation_agent(
        self,
        user_input: str,
        state: Dict,
        tool_map: Dict
    ) -> str:
        """执行对话 Agent - 使用完整的 System Prompt"""
        from multi_agent.system_prompts import (
            CONVERSATION_AGENT_PROMPT,
            format_response,
            get_error_response
        )
        
        try:
            from coze_coding_dev_sdk import LLMClient
            from langchain_core.messages import HumanMessage, SystemMessage
            from coze_coding_utils.runtime_ctx.context import new_context
            
            ctx = new_context(method="executor_conversation")
            client = LLMClient(ctx=ctx)
            
            # 获取用户画像
            user_id = state.get("user_id", "default_user")
            features = state.get("features", {})
            style = features.get("learning_style", "通用")
            level = features.get("knowledge_level", "未知")
            
            # 获取对话历史
            messages_history = state.get("messages_history", [])
            
            # 构建消息列表
            messages = [SystemMessage(content=CONVERSATION_AGENT_PROMPT)]
            
            # 添加画像上下文
            profile_context = f"\n\n【当前用户画像】\n- 学习风格：{style}\n- 知识水平：{level}\n"
            messages.append(HumanMessage(content=profile_context))
            
            # 添加对话历史
            if messages_history:
                history_text = "\n\n【对话历史】\n"
                for msg in messages_history[-6:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    history_text += f"{'用户' if role == 'user' else '助手'}：{content}\n"
                messages.append(HumanMessage(content=history_text))
            
            # 添加当前问题
            messages.append(HumanMessage(content=f"\n\n【当前问题】\n{user_input}"))
            
            # 调用 LLM
            response = client.invoke(messages=messages, temperature=0.7)
            
            # 保存对话
            if "save_conversation" in tool_map:
                try:
                    await asyncio.to_thread(
                        tool_map["save_conversation"].invoke,
                        {"user_id": user_id, "role": "user", "content": user_input}
                    )
                except Exception as e:
                    logger.warning(f"Failed to save conversation: {e}")
            
            # 处理响应
            content = response.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                if content and isinstance(content[0], str):
                    return " ".join(content)
                else:
                    text_parts = [item.get("text", "") for item in content 
                                  if isinstance(item, dict) and item.get("type") == "text"]
                    return " ".join(text_parts)
            return str(content)
            
        except Exception as e:
            logger.error(f"Conversation agent LLM call failed: {e}")
            # Fallback：保存对话
            if "save_conversation" in tool_map:
                try:
                    await asyncio.to_thread(
                        tool_map["save_conversation"].invoke,
                        {"user_id": state.get("user_id", "default_user"), "role": "user", "content": user_input}
                    )
                except Exception:
                    pass
            return get_error_response("llm_error")
    
    async def _execute_document_agent(
        self,
        user_input: str,
        state: Dict,
        tool_map: Dict
    ) -> str:
        """执行文档 Agent"""
        # 提取主题
        topic = self._extract_topic(user_input)
        subject = state.get("subject", "通用")
        
        if "generate_document_outline" in tool_map:
            try:
                result = await asyncio.to_thread(
                    tool_map["generate_document_outline"].invoke,
                    {"topic": topic, "subject": subject}
                )
                return f"## {topic} 文档大纲\n\n{result}"
            except Exception as e:
                logger.warning(f"Failed to generate document: {e}")
        
        return f"我将为 '{topic}' 生成文档大纲..."
    
    async def _execute_question_agent(
        self,
        user_input: str,
        state: Dict,
        tool_map: Dict
    ) -> str:
        """执行题库 Agent"""
        topic = self._extract_topic(user_input)
        question_type = self._detect_question_type(user_input)
        
        if question_type == "multiple_choice" and "generate_multiple_choice" in tool_map:
            try:
                result = await asyncio.to_thread(
                    tool_map["generate_multiple_choice"].invoke,
                    {"topic": topic, "count": 5}
                )
                return f"## {topic} 选择题练习\n\n{result}"
            except Exception as e:
                logger.warning(f"Failed to generate questions: {e}")
        
        return f"我将为 '{topic}' 生成练习题..."
    
    async def _execute_multimedia_agent(
        self,
        user_input: str,
        state: Dict,
        tool_map: Dict
    ) -> str:
        """执行多媒体 Agent - 生成架构图、流程图等概念图"""
        topic = self._extract_topic(user_input)
        
        # 从 state 中获取 subject，默认为"大数据"
        subject = state.get("subject", "大数据")
        
        # 识别图表类型
        diagram_type = self._identify_diagram_type(user_input)
        
        # 优先使用 generate_concept_diagram 生成架构图/流程图
        if "generate_concept_diagram" in tool_map:
            try:
                result = await asyncio.to_thread(
                    tool_map["generate_concept_diagram"].invoke,
                    {
                        "subject": subject,
                        "concept": topic,
                        "diagram_type": diagram_type
                    }
                )
                
                # 解析返回结果，提取图片 URL
                import json
                try:
                    result_data = json.loads(result)
                    if isinstance(result_data, dict) and result_data.get("success"):
                        image_url = result_data.get("image_url", "")
                        if image_url:
                            return f"![{topic}]({image_url})\n\n**{topic}**"
                        # 如果返回的是完整的 JSON，提取其中的图片 URL
                        if "image_urls" in result_data and result_data["image_urls"]:
                            return f"![{topic}]({result_data['image_urls'][0]})\n\n**{topic}**"
                except:
                    pass
                
                # 如果 result 本身包含 URL
                if "http" in result:
                    return f"![{topic}]({result})\n\n**{topic}**"
                
                return f"## {topic}\n\n{result}"
                
            except Exception as e:
                logger.warning(f"Failed to generate concept diagram: {e}")
        
        # 备用：使用 generate_illustration_image
        if "generate_illustration_image" in tool_map:
            try:
                result = await asyncio.to_thread(
                    tool_map["generate_illustration_image"].invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "style": "educational"
                    }
                )
                
                # 解析返回结果，提取图片 URL
                import json
                try:
                    result_data = json.loads(result)
                    if isinstance(result_data, dict) and result_data.get("success"):
                        image_url = result_data.get("image_url", "")
                        if image_url:
                            return f"![{topic}]({image_url})\n\n**{topic}**"
                        if "image_urls" in result_data and result_data["image_urls"]:
                            return f"![{topic}]({result_data['image_urls'][0]})\n\n**{topic}**"
                except:
                    pass
                
                return f"## {topic} 配图\n\n{result}"
            except Exception as e:
                logger.warning(f"Failed to generate illustration: {e}")
        
        return f"抱歉，暂时无法为 '{topic}' 生成图片。请稍后再试。"
    
    def _identify_diagram_type(self, text: str) -> str:
        """识别图表类型"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ["架构", "architecture"]):
            return "architecture"
        elif any(keyword in text_lower for keyword in ["流程", "flow", "process"]):
            return "flowchart"
        elif any(keyword in text_lower for keyword in ["关系", "relationship", "组件"]):
            return "relationship"
        elif any(keyword in text_lower for keyword in ["层次", "layer", "分层"]):
            return "hierarchy"
        else:
            return "flowchart"  # 默认使用流程图
    
    async def _execute_qa_agent(
        self,
        user_input: str,
        state: Dict,
        tool_map: Dict
    ) -> str:
        """执行答疑 Agent"""
        # 直接回答问题
        return f"关于您的问题：'{user_input}'，我来为您解答...\n\n" \
               f"如果你需要更详细的解答或有其他问题，请随时告诉我！"
    
    async def _execute_email_agent(
        self,
        user_input: str,
        state: Dict,
        tool_map: Dict
    ) -> str:
        """✅ 执行邮件 Agent - 支持从用户输入提取邮箱并发送邮件"""
        import re
        import json
        import asyncio
        
        # ✅ 从用户输入中提取邮箱地址
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, user_input)
        
        if not emails:
            # ✅ 没有邮箱，提供引导信息
            return "请提供收件人邮箱地址，例如：发送到 example@email.com"
        
        to_email = emails[0]
        
        # ✅ 根据请求内容确定邮件主题和内容
        subject = "学习助手"
        content = user_input
        
        # ✅ 尝试发送带图片的邮件
        if "send_email_with_image" in tool_map:
            try:
                tool = tool_map["send_email_with_image"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "to_addrs": [to_email],
                        "subject": subject,
                        "content": content,
                        "image_urls": []
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                if data.get("status") == "success":
                    return f"✅ 邮件已成功发送到 {to_email}"
            except Exception as e:
                logger.warning(f"[AgentExecutor] send_email_with_image failed: {e}")
        
        # ✅ 尝试发送纯文本邮件
        if "send_text_email" in tool_map:
            try:
                tool = tool_map["send_text_email"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "to_addrs": [to_email],
                        "subject": subject,
                        "content": content
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                if data.get("status") == "success":
                    return f"✅ 邮件已成功发送到 {to_email}"
            except Exception as e:
                logger.warning(f"[AgentExecutor] send_text_email failed: {e}")
        
        # ✅ 如果没有可用工具，返回提示
        return f"邮件发送功能需要配置邮件服务。请先配置邮件服务后再试。"
    
    def _extract_topic(self, text: str) -> str:
        """从文本中提取主题"""
        # 简单的关键词移除
        keywords_to_remove = [
            "帮我", "生成", "整理", "制定", "出一", "做一", "学习", "了解",
            "关于", "针对", "请", "一下", "的", "是", "什么"
        ]
        topic = text
        for kw in keywords_to_remove:
            topic = topic.replace(kw, "")
        return topic.strip() or "通用主题"
    
    def _detect_question_type(self, text: str) -> str:
        """检测题型"""
        if any(kw in text for kw in ["选择", "单选", "多选"]):
            return "multiple_choice"
        if any(kw in text for kw in ["简答", "问答"]):
            return "short_answer"
        if any(kw in text for kw in ["代码", "编程", "写"]):
            return "coding"
        return "multiple_choice"  # 默认
    
    def _is_simple_conversation(self, user_input: str) -> bool:
        """
        判断是否为简单对话（可走快速路径）
        
        简单对话的特征：
        1. 长度适中（10-100字符）
        2. 不包含特定任务关键词
        3. 不包含详细描述性词汇（"讲讲"、"介绍"、"包括"等）
        4. 是日常交流或简单问答
        """
        if not user_input or not user_input.strip():
            return False
        
        # 长度检查 - 调整为更严格的范围
        text_len = len(user_input.strip())
        if text_len < 10 or text_len > 100:
            return False
        
        # 检查是否包含详细描述性词汇（这些需要更复杂的处理）
        detail_keywords = [
            "讲讲", "介绍", "包括", "包括但不限于", "详细", "具体",
            "完整", "全面", "深入", "讲解", "解释"
        ]
        for keyword in detail_keywords:
            if keyword in user_input:
                return False
        
        # 检查是否包含特定任务关键词（这些需要走完整流程）
        task_keywords = [
            "生成", "创建", "生成文档", "生成题", "出题", "画图", "生成图片",
            "生成图表", "写邮件", "发送邮件", "制定计划", "整理成", "转换为",
            "帮我", "请帮我", "能帮我"
        ]
        for keyword in task_keywords:
            if keyword in user_input:
                return False
        
        # 检查是否包含多个技术词汇（复杂查询）
        tech_keywords = ["Hadoop", "Spark", "Hive", "Kafka", "Flink", "HDFS", "MapReduce"]
        tech_count = sum(1 for kw in tech_keywords if kw in user_input)
        if tech_count >= 2:
            return False
        
        return True
    
    async def _quick_conversation_response(
        self,
        user_input: str,
        state: Dict[str, Any]
    ) -> str:
        """
        快速对话响应（绕过工具调用）
        
        适用于简单的日常对话和问答
        """
        from coze_coding_dev_sdk import LLMClient
        from langchain_core.messages import HumanMessage, SystemMessage
        from coze_coding_utils.runtime_ctx.context import new_context
        
        ctx = new_context(method="quick_conversation")
        client = LLMClient(ctx=ctx)
        
        # 获取用户画像
        features = state.get("features", {})
        style = features.get("learning_style", "通用")
        level = features.get("knowledge_level", "未知")
        messages_history = state.get("messages_history", [])
        
        # 快速路径的系统提示（更简洁）
        quick_system_prompt = """# 角色：专业的大数据学习助手

## 核心规则
1. 直接回答用户问题，不输出问候语
2. 回答简洁、专业、易懂
3. 禁止添加客套话（如"好的，我来为你介绍"）
4. 禁止结尾说"咱们一起学习"等引导语

## 回答原则
- 如果是技术问题：先解释核心概念，再补充细节
- 如果是概念问题：先给出定义，再举例说明
- 如果需要：可以适当使用代码示例"""
        
        # 构建消息列表
        messages = [SystemMessage(content=quick_system_prompt)]
        
        # 添加画像上下文
        profile_context = f"\n\n【用户画像】学习风格：{style}，知识水平：{level}"
        messages.append(HumanMessage(content=profile_context))
        
        # 添加最近对话历史（限制为最近3轮）
        if messages_history:
            history_text = "\n\n【最近对话】\n"
            for msg in messages_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{'用户' if role == 'user' else '助手'}：{content}\n"
            messages.append(HumanMessage(content=history_text))
        
        # 添加当前问题
        messages.append(HumanMessage(content=f"\n\n【当前问题】\n{user_input}"))
        
        # 调用 LLM
        response = client.invoke(messages=messages, temperature=0.7)
        
        return response.content
    
    def reset(self):
        """重置执行器状态"""
        self._execution_results.clear()
        self._active_agents.clear()
    
    def execute_sync(
        self,
        agent_id: str,
        user_input: str,
        state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        同步执行方法，供主 Agent 调用
        
        Args:
            agent_id: Agent ID (如 "conversation", "question", "document" 等)
            user_input: 用户输入
            state: 可选的上下文状态
            
        Returns:
            执行结果字典，包含 success、output 等字段
        """
        if state is None:
            state = {}
        
        # 在同步环境中运行异步代码
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已有事件循环在运行，创建新的
                result = loop.run_until_complete(
                    self.execute_federated(agent_id, user_input, state)
                )
            else:
                result = loop.run_until_complete(
                    self.execute_federated(agent_id, user_input, state)
                )
            return result
        except RuntimeError:
            # 没有事件循环，创建一个新的
            result = asyncio.run(
                self.execute_federated(agent_id, user_input, state)
            )
            return result
        except Exception as e:
            logger.error(f"[AgentExecutor] Sync execution error: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "output": "",
                "error": str(e)
            }
    
    def execute_collaborative_sync(
        self,
        intent: str,
        user_input: str,
        state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        同步执行协作式任务
        
        Args:
            intent: 意图类型
            user_input: 用户输入
            state: 可选的上下文状态
            
        Returns:
            协作执行结果
        """
        if state is None:
            state = {}
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = loop.run_until_complete(
                    self.execute_collaborative(intent, user_input, state)
                )
            else:
                result = loop.run_until_complete(
                    self.execute_collaborative(intent, user_input, state)
                )
            return result
        except RuntimeError:
            result = asyncio.run(
                self.execute_collaborative(intent, user_input, state)
            )
            return result
        except Exception as e:
            logger.error(f"[AgentExecutor] Sync collaborative error: {e}")
            return {
                "success": False,
                "intent": intent,
                "output": "",
                "error": str(e)
            }


# 全局实例
_agent_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """获取全局 Agent 执行器实例"""
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = AgentExecutor()
    return _agent_executor
