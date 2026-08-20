"""
Multi-Agent System - 多智能体系统主入口
实现层级-协作混合模式的多智能体架构

架构说明：
1. 调度层（Orchestration Layer）：Orchestrator负责意图识别和任务分发
2. 执行层（Execution Layer）：
   - 联邦式：独立处理无依赖的任务（文档、题库、多媒体、答疑、邮件）
   - 协作式：顺序处理有依赖的任务（学习路径→评估→推荐）
3. 通信层（Communication Layer）：MessageBus负责Agent间通信
"""
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base.agent_state import MultiAgentState, IntentType, UserProfile
from .base.message import AgentMessage, MessageType
from .base.base_agent import BaseAgent
from .base.registry import AgentRegistry
from .communication.message_bus import MessageBus, get_message_bus
from .communication.shared_context import SharedContext, get_shared_context
from .knowledge.vector_store import VectorStore, get_vector_store
from .knowledge.graph_store import GraphStore, get_graph_store
from .coordinator.router import IntentRouter
from .coordinator.orchestrator import OrchestratorAgent
from .coordinator.workflow import WorkflowManager, get_workflow_manager
from .monitoring import get_multi_agent_monitor, MultiAgentMonitor

# Agent导入
from .agents.conversation_agent import ConversationAgent, get_conversation_agent
from .agents.document_agent import DocumentAgent, get_document_agent
from .agents.question_agent import QuestionAgent, get_question_agent
from .agents.multimedia_generation_agent import MultimediaAgent, get_multimedia_agent
from .agents.multimodal_understanding_agent import MultimodalUnderstandingAgent, get_multimodal_understanding_agent  # ✅ 新增
from .agents.qa_agent import QAAgent, get_qa_agent
from .agents.learning_path_agent import LearningPathAgent, get_learning_path_agent
from .agents.evaluation_agent import EvaluationAgent, get_evaluation_agent
from .agents.recommendation_agent import RecommendationAgent, get_recommendation_agent
from .agents.email_agent import EmailAgent, get_email_agent
from .agents.bigdata_learning_agent import BigDataLearningAgent, get_bigdata_learning_agent
from .agents.learning_engine_agent import LearningEngineAgent, get_learning_engine_agent
from .agents.resource_agent import ResourceAgent, get_resource_agent
from .agents.diagnosis_agent import DiagnosisAgent, get_diagnosis_agent
from .tools.resource_tools import (
    search_internet,
    search_bilibili,
    search_official_docs,
    search_github,
    search_community_posts,
)
from tools.email_tools import (  # ✅ 从 src/tools/ 导入
    send_text_email,
    send_email_with_image,
    send_learning_plan_email,
)
from tools.multimedia_tools import (  # ✅ 新增多媒体工具导入
    generate_illustration_image,
    generate_concept_diagram,
    generate_teaching_video,
)

logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """
    多智能体系统主类
    
    负责：
    1. 初始化和注册所有Agent
    2. 处理用户请求
    3. 协调Agent间的通信和协作
    4. 管理共享状态和上下文
    """
    
    def __init__(self):
        """初始化多智能体系统"""
        logger.info("[MultiAgentSystem] Initializing...")
        
        # 组件初始化
        self.message_bus = get_message_bus()
        self.shared_context = get_shared_context()
        self.vector_store = get_vector_store()
        self.graph_store = get_graph_store()
        
        # 协调器初始化
        self.router = IntentRouter()
        self.orchestrator = OrchestratorAgent()
        self.workflow_manager = get_workflow_manager()
        
        # Agent注册表
        self.registry = AgentRegistry()
        
        # ✅ 监控初始化
        self.monitor = get_multi_agent_monitor()
        self.monitor.start_monitoring()
        
        # 工具映射（用于Agent调用）
        self._tools: Dict[str, Any] = {}
        
        # ✅ 注册联网搜索工具
        self._register_resource_tools()
        
        # 初始化Agent
        self._initialize_agents()
        
        # 将工具绑定到Agent
        self._bind_tools_to_agents()
        
        # 在 MultiAgentSystem 初始化时设置全局上下文
        from .communication.shared_context import set_shared_context
        set_shared_context(self.shared_context)
        
        logger.info("[MultiAgentSystem] Initialization complete")
    
    def _initialize_agents(self):
        """初始化所有Agent"""
        # 导入新的Agent
        from .agents.audio_agent import AudioAgent
        from .agents.rag_question_agent import RagQuestionAgent

        # 创建Agent实例
        agents = {
            "conversation": get_conversation_agent(),
            "document": get_document_agent(),
            "question": get_question_agent(),
            "multimedia": get_multimedia_agent(),
            "multimodal": get_multimodal_understanding_agent(),  # ✅ 多模态理解Agent
            "qa": get_qa_agent(),
            "learning_path": get_learning_path_agent(),
            "evaluation": get_evaluation_agent(),
            "recommendation": get_recommendation_agent(),
            "email": get_email_agent(),
            "bigdata_learning": get_bigdata_learning_agent(),
            "learning_engine": get_learning_engine_agent(),
            "resource": get_resource_agent(),
            "diagnosis": get_diagnosis_agent(),
            # ✅ 新增Agent
            "audio": AudioAgent(),  # 语音处理Agent
            "rag_question": RagQuestionAgent(),  # RAG题库Agent
        }
        
        # 注册Agent
        for agent_id, agent in agents.items():
            self.registry.register(agent_id, agent)
            logger.info(f"[MultiAgentSystem] Registered agent: {agent_id}")
        
        logger.info(f"[MultiAgentSystem] Total agents registered: {len(agents)}")
    
    def _register_resource_tools(self):
        """✅ 注册联网搜索工具、邮件工具和多媒体工具到工具映射"""
        resource_tools = {
            "search_internet": search_internet,
            "search_bilibili": search_bilibili,
            "search_official_docs": search_official_docs,
            "search_github": search_github,
            "search_community_posts": search_community_posts,
        }
        # ✅ 新增邮件发送工具
        email_tools = {
            "send_text_email": send_text_email,
            "send_email_with_image": send_email_with_image,
            "send_learning_plan_email": send_learning_plan_email,
        }
        # ✅ 新增多媒体生成工具
        multimedia_tools = {
            "generate_illustration_image": generate_illustration_image,
            "generate_concept_diagram": generate_concept_diagram,
            "generate_teaching_video": generate_teaching_video,
        }
        for name, tool in {**resource_tools, **email_tools, **multimedia_tools}.items():
            self._tools[name] = tool
        logger.info(f"[MultiAgentSystem] Registered {len(resource_tools) + len(email_tools) + len(multimedia_tools)} resource tools")
    
    def _bind_tools_to_agents(self):
        """将工具绑定到Agent"""
        for agent_id, agent in self.registry.get_all_agents().items():
            # 获取该Agent相关的工具
            agent_tools = self._get_tools_for_agent(agent_id)
            if hasattr(agent, 'set_tools'):
                agent.set_tools(agent_tools)
            
            # 设置共享上下文
            if hasattr(agent, 'set_shared_context'):
                agent.set_shared_context(self.shared_context)
    
    def _get_tools_for_agent(self, agent_id: str) -> List[Any]:
        """获取Agent对应的工具"""
        # 工具映射关系
        tool_mapping = {
            "conversation": [
                "save_conversation",
                "get_user_profile",
                "update_user_profile",
                "extract_learning_features"
            ],
            "document": [
                "generate_document",
                "generate_mindmap_structure",
                "save_learning_content"
            ],
            "question": [
                "generate_multiple_choice",
                "generate_short_answer",
                "generate_coding_exercise",
                "evaluate_multiple_choice",
                "get_user_answers"
            ],
            "multimedia": [
                "generate_illustration_image",
                "generate_concept_diagram",
                "generate_video_script"
            ],
            "qa": [
                "answer_question",
                "search_related_content",
                "save_qa_record"
            ],
            "learning_path": [
                "generate_learning_path",
                "save_learning_path",
                "update_path_progress",
                "get_user_profile"
            ],
            "evaluation": [
                "evaluate_multiple_choice",
                "generate_evaluation_report",
                "save_evaluation",
                "get_user_answers"
            ],
            "recommendation": [
                "get_user_profile",
                "generate_personalized_content"
            ],
            "email": [
                "send_email",
                "send_email_with_image",
                "send_learning_plan_email"
            ],
            "resource": [
                "search_internet",
                "search_bilibili",
                "search_official_docs",
                "search_github",
                "search_community_posts"
            ]
        }
        
        tool_names = tool_mapping.get(agent_id, [])
        return [self._tools.get(name) for name in tool_names if name in self._tools]
    
    def register_tool(self, tool_name: str, tool: Any):
        """注册工具"""
        self._tools[tool_name] = tool
        logger.info(f"[MultiAgentSystem] Registered tool: {tool_name}")
    
    def register_tools(self, tools: List[Any]):
        """批量注册工具"""
        for tool in tools:
            tool_name = tool.name if hasattr(tool, 'name') else str(tool)
            self.register_tool(tool_name, tool)
        
        # 重新绑定工具到Agent
        self._bind_tools_to_agents()
    
    async def process(
        self,
        user_input: str,
        user_id: str = "default_user",
        multimodal_data: Optional[Dict[str, Any]] = None  # ✅ 新增多模态数据
    ) -> Dict[str, Any]:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            multimodal_data: ✅ 新增多模态数据
                {
                    "images": ["url1", "url2"],
                    "videos": ["url3"],
                    "audio": ["url4"],
                    "files": ["url5"]
                }

        Returns:
            处理结果
        """
        logger.info(f"[MultiAgentSystem] Processing request from user {user_id}")
        
        # ✅ 开始监控
        request_id = self.monitor.record_request_start()
        
        # 1. 初始化状态（传入多模态数据）
        state = self._create_initial_state(user_input, user_id, multimodal_data)

        # 2. 意图识别（支持多意图）
        intents = self.router.recognize_intents(user_input, multimodal_data)
        logger.info(f"[MultiAgentSystem] Recognized intents: {intents}")
        
        # ✅ 多意图处理：如果识别到多个意图，使用协作式处理
        if len(intents) > 1:
            logger.info(f"[MultiAgentSystem] Multi-intent detected, using collaborative processing")
            # 将 intents 存入 state 供后续使用
            state["intents"] = intents
            state["primary_intent"] = intents[0]
            # 使用 orchestrator 处理多意图
            orchestrator = self.orchestrator
            result = await orchestrator.process(state)
            self.monitor.record_request_end(request_id, success=result.get("success", True))
            return result
        
        # 单意图处理（保持原有逻辑）
        intent = intents[0] if intents else IntentType.CONVERSATION
        logger.info(f"[MultiAgentSystem] Recognized intent: {intent}")
        
        # 3. 确定处理模式
        agent_id = self.router.route_to_agent(intent)
        agent = self.registry.get_agent(agent_id)
        
        if not agent:
            return self._create_error_response(f"Agent {agent_id} not found")
        
        processing_mode = agent.processing_mode if hasattr(agent, 'processing_mode') else None
        
        # 4. 根据处理模式执行
        if processing_mode and processing_mode.value == "collaborative":
            # 协作式处理
            result = await self._process_collaborative(state, agent_id)
        else:
            # 联邦式处理
            result = await self._process_federated(state, agent_id)
        
        # ✅ 结束监控
        self.monitor.record_request_end(request_id, success=result.get("success", False))
        
        # 5. 返回结果
        return result
    
    async def process(self, user_input: str, user_id: str = "default_user", multimodal_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户请求 - 带监控"""
        try:
            return await self._process_internal(user_input, user_id, multimodal_data)
        except Exception as e:
            logger.error(f"[MultiAgentSystem] Error processing request: {e}")
            self.monitor.record_error("process_error", str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "处理请求时发生错误，请稍后重试"
            }
    
    async def _process_internal(self, user_input: str, user_id: str, multimodal_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """内部处理逻辑"""
        logger.info(f"[MultiAgentSystem] Processing request from user {user_id}")
        
        # 1. 初始化状态（传入多模态数据）
        state = self._create_initial_state(user_input, user_id, multimodal_data)

        # 2. 意图识别（支持多意图）
        intents = self.router.recognize_intents(user_input, multimodal_data)
        logger.info(f"[MultiAgentSystem] Recognized intents: {intents}")
        
        # ✅ 多意图处理：如果识别到多个意图，使用协作式处理
        if len(intents) > 1:
            logger.info(f"[MultiAgentSystem] Multi-intent detected, using collaborative processing")
            # 将 intents 存入 state 供后续使用
            state["intents"] = intents
            state["primary_intent"] = intents[0]
            # 使用 orchestrator 处理多意图
            orchestrator = self.orchestrator
            result = await orchestrator.process(state)
            self.monitor.record_request_end(request_id, success=result.get("success", True))
            return result
        
        # 单意图处理（保持原有逻辑）
        intent = intents[0] if intents else IntentType.CONVERSATION
        logger.info(f"[MultiAgentSystem] Recognized intent: {intent}")
        
        # ✅ 开始监控
        request_id = self.monitor.record_request_start()
        
        # 3. 确定处理模式
        agent_id = self.router.route_to_agent(intent)
        agent = self.registry.get_agent(agent_id)
        
        if not agent:
            return self._create_error_response(f"Agent {agent_id} not found")
        
        processing_mode = agent.processing_mode if hasattr(agent, 'processing_mode') else None
        
        # 4. 根据处理模式执行
        if processing_mode and processing_mode.value == "collaborative":
            # 协作式处理
            result = await self._process_collaborative(state, agent_id)
        else:
            # 联邦式处理
            result = await self._process_federated(state, agent_id)
        
        # ✅ 结束监控
        self.monitor.record_request_end(request_id, success=result.get("success", False))
        
        # 5. 返回结果
        return result
    
    async def _process_federated(self, state: MultiAgentState, agent_id: str) -> Dict[str, Any]:
        """联邦式处理（独立Agent）"""
        logger.info(f"[MultiAgentSystem] Processing federated: {agent_id}")
        
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return self._create_error_response(f"Agent {agent_id} not found")
        
        try:
            # 执行Agent处理
            if asyncio.iscoroutinefunction(agent.process):
                result = await agent.process(state)
            else:
                result = agent.process(state)
            
            # 提取自然语言文本用于返回
            if isinstance(result, dict):
                response_text = (
                    result.get("natural_language") or
                    result.get("message") or
                    result.get("response") or
                    result.get("content") or
                    result.get("learning_path") or
                    result.get("multiple_choice") or
                    result.get("recommendations") or
                    str(result)
                )
                result["response_text"] = response_text
            
            return {
                "success": True,
                "agent_id": agent_id,
                "intent": agent.intent_type.value if hasattr(agent, 'intent_type') else agent_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"[MultiAgentSystem] Error in federated processing: {e}")
            return self._create_error_response(str(e))
    
    async def _process_collaborative(self, state: MultiAgentState, agent_id: str) -> Dict[str, Any]:
        """协作式处理（多Agent协作）"""
        logger.info(f"[MultiAgentSystem] Processing collaborative: {agent_id}")
        
        # 学习路径流程
        if agent_id == "learning_path":
            return await self._process_learning_path_flow(state)
        
        # 评估流程
        elif agent_id == "evaluation":
            return await self._process_evaluation_flow(state)
        
        # 推荐流程
        elif agent_id == "recommendation":
            return await self._process_recommendation_flow(state)
        
        # 默认联邦式处理
        return await self._process_federated(state, agent_id)
    
    async def _process_learning_path_flow(self, state: MultiAgentState) -> Dict[str, Any]:
        """学习路径流程（协作式）"""
        logger.info("[MultiAgentSystem] Processing learning path flow")
        
        # 1. 获取用户画像
        user_id = state.get("user_id", "default_user")
        profile = self.shared_context.get_user_profile(user_id)
        
        # 2. 执行学习路径Agent
        path_agent = self.registry.get_agent("learning_path")
        path_result = await path_agent.process(state)
        
        # 3. 通知评估Agent
        msg1 = AgentMessage(
            sender="learning_path",
            receiver="evaluation",
            message_type=MessageType.TASK,
            content={
                "task": "setup_evaluations",
                "user_id": user_id,
                "learning_path": path_result.get("learning_path")
            },
            correlation_id=f"lr-{user_id}-{int(datetime.now().timestamp())}"
        )
        await self.message_bus.send(msg1)
        
        # 4. 通知推荐Agent
        msg2 = AgentMessage(
            sender="learning_path",
            receiver="recommendation",
            message_type=MessageType.TASK,
            content={
                "task": "plan_recommendations",
                "user_id": user_id,
                "learning_path": path_result.get("learning_path")
            },
            correlation_id=f"lr-{user_id}-{int(datetime.now().timestamp())}"
        )
        await self.message_bus.send(msg2)
        
        return {
            "success": True,
            "agent_id": "learning_path",
            "intent": "learning_path",
            "result": path_result,
            "collaborative": True
        }
    
    async def _process_evaluation_flow(self, state: MultiAgentState) -> Dict[str, Any]:
        """评估流程（协作式）"""
        logger.info("[MultiAgentSystem] Processing evaluation flow")
        
        # 1. 执行评估Agent
        eval_agent = self.registry.get_agent("evaluation")
        eval_result = await eval_agent.process(state)
        
        # 2. 通知推荐Agent
        user_id = state.get("user_id", "default_user")
        msg2 = AgentMessage(
            sender="evaluation",
            receiver="recommendation",
            message_type=MessageType.TASK,
            content={
                "task": "personalized_recommendations",
                "user_id": user_id,
                "evaluation": eval_result.get("evaluation")
            },
            correlation_id=f"eval-{user_id}-{int(datetime.now().timestamp())}"
        )
        await self.message_bus.send(msg2)
        
        return {
            "success": True,
            "agent_id": "evaluation",
            "intent": "evaluation",
            "result": eval_result,
            "collaborative": True
        }
    
    async def _process_recommendation_flow(self, state: MultiAgentState) -> Dict[str, Any]:
        """推荐流程（协作式）"""
        logger.info("[MultiAgentSystem] Processing recommendation flow")
        
        # 执行推荐Agent
        rec_agent = self.registry.get_agent("recommendation")
        rec_result = await rec_agent.process(state)
        
        return {
            "success": True,
            "agent_id": "recommendation",
            "intent": "recommendation",
            "result": rec_result,
            "collaborative": True
        }
    
    def _create_initial_state(
        self,
        user_input: str,
        user_id: str,
        multimodal_data: Optional[Dict[str, Any]] = None  # ✅ 新增
    ) -> MultiAgentState:
        """创建初始状态"""
        return MultiAgentState(
            user_id=user_id,
            messages=[{"role": "user", "content": user_input}],
            current_intent=None,
            processing_mode="federated",
            agent_results={},
            shared_context={},
            multimodal_data=multimodal_data or {}  # ✅ 新增
        )
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error,
            "result": None
        }
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent"""
        return self.registry.get_agent(agent_id)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """获取所有Agent"""
        return self.registry.get_all_agents()
    
    async def shutdown(self):
        """关闭系统"""
        logger.info("[MultiAgentSystem] Shutting down...")
        
        # 清理资源
        if hasattr(self.vector_store, 'close'):
            self.vector_store.close()
        
        if hasattr(self.graph_store, 'close'):
            self.graph_store.close()
        
        logger.info("[MultiAgentSystem] Shutdown complete")


# 全局实例
_multi_agent_system: Optional[MultiAgentSystem] = None


def get_multi_agent_system() -> MultiAgentSystem:
    """获取全局多智能体系统实例"""
    global _multi_agent_system
    if _multi_agent_system is None:
        _multi_agent_system = MultiAgentSystem()
    return _multi_agent_system


# 便捷函数
async def process_user_request(user_input: str, user_id: str = "default_user") -> Dict[str, Any]:
    """
    处理用户请求的便捷函数
    
    Args:
        user_input: 用户输入
        user_id: 用户ID
        
    Returns:
        处理结果
    """
    system = get_multi_agent_system()
    return await system.process(user_input, user_id)


# ============================================================
# 流式处理支持 (为 main.py 的 /multi_agent_stream 接口提供支持)
# ============================================================

import time
from typing import AsyncGenerator, AsyncIterable

async def stream_process(
    user_input: str,
    user_id: str = "default_user",
    session_id: Optional[str] = None,
    multimodal_data: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    多智能体系统流式处理（非语音模式）
    
    Args:
        user_input: 用户输入
        user_id: 用户ID
        session_id: 会话ID
        multimodal_data: 多模态数据
        
    Yields:
        SSE 事件字典
    """
    start_time = time.time()
    session_id = session_id or f"session_{int(start_time)}"
    
    system = get_multi_agent_system()
    
    # 1. 发送 agent_start 事件
    yield {
        "event": "agent_start",
        "type": "agent_start",
        "agent_id": "orchestrator",
        "agent_name": "调度中心",
        "content": f"开始处理用户请求..."
    }
    
    # 2. 意图识别（支持多意图）
    intents = system.router.recognize_intents(user_input, multimodal_data)
    
    # ✅ 多意图处理：使用 orchestrator 处理多意图
    if len(intents) > 1:
        yield {
            "event": "thinking",
            "type": "thinking",
            "content": f"识别到 {len(intents)} 个意图: {[i.value for i in intents]}"
        }
        
        # 创建状态并使用 orchestrator 处理
        state = system._create_initial_state(user_input, user_id, multimodal_data)
        state["intents"] = intents
        
        result = await system.orchestrator.process(state)
        
        # 提取响应文本
        response_text = ""
        if result.get("success"):
            response_text = result.get("message", str(result))
        
        # 流式发送
        for char in response_text:
            yield {"event": "message", "type": "char", "content": char}
            await asyncio.sleep(0.01)
        
        yield {"event": "agent_end", "type": "agent_end", "success": True}
        return
    
    # 单意图处理（保持原有逻辑）
    intent = intents[0] if intents else IntentType.CONVERSATION
    yield {
        "event": "thinking",
        "type": "thinking",
        "content": f"识别到意图: {intent.value if hasattr(intent, 'value') else intent}"
    }
    
    # 3. 确定处理模式
    agent_id = system.router.route_to_agent(intent)
    agent = system.registry.get_agent(agent_id)
    
    if not agent:
        yield {
            "event": "error",
            "type": "error",
            "content": f"未找到处理Agent: {agent_id}"
        }
        return
    
    # 4. 发送 agent_switch 事件
    agent_name = agent.agent_name if hasattr(agent, 'agent_name') else agent_id
    yield {
        "event": "agent_switch",
        "type": "agent_switch",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "content": f"正在使用 {agent_name} 处理..."
    }
    
    # 5. 创建初始状态
    state = system._create_initial_state(user_input, user_id, multimodal_data)
    
    # 6. 执行处理
    try:
        processing_mode = agent.processing_mode if hasattr(agent, 'processing_mode') else None
        
        if processing_mode and processing_mode.value == "collaborative":
            result = await system._process_collaborative(state, agent_id)
        else:
            result = await system._process_federated(state, agent_id)
        
        # 7. 流式返回结果
        response_text = ""
        if result.get("success"):
            agent_result = result.get("result", {})
            if isinstance(agent_result, dict):
                # 优先提取自然语言文本，然后是 message、response、content
                response_text = (
                    agent_result.get("natural_language") or
                    agent_result.get("message") or
                    agent_result.get("response") or
                    agent_result.get("content") or
                    str(agent_result)
                )
            elif isinstance(agent_result, str):
                response_text = agent_result
            else:
                response_text = str(agent_result)
        
        # 逐字符发送
        for char in response_text:
            yield {
                "event": "message",
                "type": "char",
                "content": char
            }
            await asyncio.sleep(0.01)  # 控制发送速度
        
        # 8. 发送 agent_end 事件
        duration_ms = int((time.time() - start_time) * 1000)
        yield {
            "event": "agent_end",
            "type": "agent_end",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "success": True,
            "duration_ms": duration_ms,
            "content": "处理完成"
        }
        
    except Exception as e:
        logger.error(f"[MultiAgentSystem] Stream processing error: {e}")
        yield {
            "event": "error",
            "type": "error",
            "content": f"处理出错: {str(e)}"
        }


async def stream_process_with_tts(
    user_input: str,
    user_id: str = "default_user",
    session_id: Optional[str] = None,
    voice_enabled: bool = True,
    speaker: str = "zh_female_xiaohe_uranus_bigtts",
    multimodal_data: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    多智能体系统流式处理（语音模式）
    
    Args:
        user_input: 用户输入
        user_id: 用户ID
        session_id: 会话ID
        voice_enabled: 是否启用语音
        speaker: 语音speaker
        multimodal_data: 多模态数据
        
    Yields:
        SSE 事件字典
    """
    start_time = time.time()
    session_id = session_id or f"session_{int(start_time)}"
    
    system = get_multi_agent_system()
    
    # 获取 TTS 服务
    from services.standalone_tts import get_tts_service
    tts_service = get_tts_service()
    
    # 1. 发送 agent_start 事件
    yield {
        "event": "agent_start",
        "type": "agent_start",
        "agent_id": "orchestrator",
        "agent_name": "调度中心",
        "content": f"开始处理用户请求（语音模式）..."
    }
    
    # 2. 意图识别（支持多意图）
    intents = system.router.recognize_intents(user_input, multimodal_data)
    
    # ✅ 多意图处理：使用 orchestrator 处理多意图
    if len(intents) > 1:
        yield {
            "event": "thinking",
            "type": "thinking",
            "content": f"识别到 {len(intents)} 个意图: {[i.value for i in intents]}"
        }
        
        # 创建状态并使用 orchestrator 处理
        state = system._create_initial_state(user_input, user_id, multimodal_data)
        state["intents"] = intents
        
        result = await system.orchestrator.process(state)
        
        # 提取响应文本
        response_text = ""
        if result.get("success"):
            response_text = result.get("message", str(result))
        
        # 流式发送
        for char in response_text:
            yield {"event": "message", "type": "char", "content": char}
            await asyncio.sleep(0.01)
        
        yield {"event": "agent_end", "type": "agent_end", "success": True}
        return
    
    # 单意图处理（保持原有逻辑）
    intent = intents[0] if intents else IntentType.CONVERSATION
    yield {
        "event": "thinking",
        "type": "thinking",
        "content": f"识别到意图: {intent.value if hasattr(intent, 'value') else intent}"
    }
    
    # 3. 确定处理模式
    agent_id = system.router.route_to_agent(intent)
    agent = system.registry.get_agent(agent_id)
    
    if not agent:
        yield {
            "event": "error",
            "type": "error",
            "content": f"未找到处理Agent: {agent_id}"
        }
        return
    
    # 4. 发送 agent_switch 事件
    agent_name = agent.agent_name if hasattr(agent, 'agent_name') else agent_id
    yield {
        "event": "agent_switch",
        "type": "agent_switch",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "content": f"正在使用 {agent_name} 处理..."
    }
    
    # 5. 创建初始状态
    state = system._create_initial_state(user_input, user_id, multimodal_data)
    
    # 6. 执行处理
    try:
        processing_mode = agent.processing_mode if hasattr(agent, 'processing_mode') else None
        
        if processing_mode and processing_mode.value == "collaborative":
            result = await system._process_collaborative(state, agent_id)
        else:
            result = await system._process_federated(state, agent_id)
        
        # 7. 流式返回结果 + TTS
        response_text = ""
        if result.get("success"):
            agent_result = result.get("result", {})
            if isinstance(agent_result, dict):
                response_text = agent_result.get("response", agent_result.get("content", str(agent_result)))
            elif isinstance(agent_result, str):
                response_text = agent_result
            else:
                response_text = str(agent_result)
        
        # 逐字符发送，同时进行 TTS 合成
        text_buffer = ""
        tts_chunk_size = 50  # 每50个字符合成一次
        
        for char in response_text:
            yield {
                "event": "message",
                "type": "char",
                "content": char
            }
            text_buffer += char
            
            # 达到一定长度或结束时，触发 TTS
            if len(text_buffer) >= tts_chunk_size or char == response_text[-1]:
                if text_buffer.strip() and tts_service:
                    try:
                        # 合成语音
                        audio_result = tts_service.synthesize(
                            text=text_buffer.strip(),
                            speaker=speaker
                        )
                        if audio_result and audio_result.get("audio_url"):
                            yield {
                                "event": "audio_url",
                                "type": "streaming",
                                "audio_url": audio_result["audio_url"],
                                "speaker": speaker,
                                "text": text_buffer.strip()
                            }
                    except Exception as tts_err:
                        logger.warning(f"[MultiAgentSystem] TTS error: {tts_err}")
                
                text_buffer = ""
                await asyncio.sleep(0.01)  # 控制发送速度
        
        # 8. 发送 agent_end 事件
        duration_ms = int((time.time() - start_time) * 1000)
        yield {
            "event": "agent_end",
            "type": "agent_end",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "success": True,
            "duration_ms": duration_ms,
            "content": "处理完成"
        }
        
    except Exception as e:
        logger.error(f"[MultiAgentSystem] Stream TTS processing error: {e}")
        yield {
            "event": "error",
            "type": "error",
            "content": f"处理出错: {str(e)}"
        }
