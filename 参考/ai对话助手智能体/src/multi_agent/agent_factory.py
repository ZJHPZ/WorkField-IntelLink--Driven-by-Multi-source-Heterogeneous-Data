"""
Agent 工厂 - 独立 Agent 实例化管理器
管理所有专业 Agent 的生命周期和工具绑定
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from storage.memory.memory_saver import get_memory_saver

# 导入通信模块
from .communication.message_bus import MessageBus, get_message_bus
from .communication.shared_context import SharedContext, get_shared_context

logger = logging.getLogger(__name__)

# ✅ 全局 Registry 实例（单例模式）
_GLOBAL_REGISTRY = None

def _get_global_registry():
    """获取全局 Registry 单例实例"""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        from .registry import AgentRegistry
        _GLOBAL_REGISTRY = AgentRegistry()
    return _GLOBAL_REGISTRY


class AgentFactory:
    """
    Agent 工厂类
    
    负责：
    1. 实例化所有专业 Agent
    2. 管理 Agent 生命周期
    3. 绑定工具到对应 Agent
    4. 提供 Agent 访问接口
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
        
        # Agent 实例存储
        self._agents: Dict[str, Any] = {}
        
        # Agent 元数据
        self._agent_metadata: Dict[str, Dict] = {}
        
        # 初始化共享组件
        self._shared_context: Optional[SharedContext] = None
        self._message_bus: Optional[MessageBus] = None
        
        # 工具映射
        self._tool_mapping: Dict[str, List[str]] = {
            "conversation": [
                "save_conversation", "get_user_conversations", "get_user_profile",
                "extract_features_from_conversation", "update_user_feature",
                "update_user_profile_full"
            ],
            "document": [
                "generate_document_outline", "generate_mindmap_structure",
                "generate_full_document", "save_learning_content", "get_learning_content"
            ],
            "question": [
                "generate_multiple_choice", "generate_short_answer",
                "generate_coding_exercise", "generate_practice_set",
                "get_questions", "save_question"
            ],
            "multimedia": [
                "generate_illustration_image", "generate_concept_diagram",
                "generate_teaching_video", "generate_animation_sequence",
                "generate_multimedia_package", "generate_image_batch"
            ],
            "learning_path": [
                "save_learning_path", "generate_learning_path", "get_learning_path",
                "update_path_progress", "generate_personalized_content",
                "save_push_record", "get_user_push_records"
            ],
            "qa": [
                "search_related_content", "get_faq_database", "save_qa_record",
                "get_user_qa_history", "generate_explanation_outline", "analyze_question_type"
            ],
            "evaluation": [
                "evaluate_multiple_choice", "evaluate_short_answer",
                "evaluate_coding_exercise", "generate_evaluation_report",
                "save_evaluation", "get_evaluation_history", "calculate_learning_progress"
            ],
            "email": [
                "send_text_email", "send_html_email", "send_email_with_image",
                "send_learning_plan_email", "test_email_connection"
            ],
            "recommendation": [
                "generate_personalized_content", "save_push_record"
            ],
            # 语音Agent - 处理语音输入输出
            "audio": [
                # TTS 文字转语音
                "tts_synthesize", "tts_announcement", "tts_storytelling",
                # ASR 语音转文字
                "asr_recognize", "asr_recognize_base64"
            ],
            # RAG题库Agent - 题库检索
            "rag_question": [
                "search_questions", "get_similar_questions",
                "generate_practice_set", "get_answer_explanation"
            ]
        }
        
        # 意图到 Agent 的映射
        self._intent_to_agent: Dict[str, str] = {
            "conversation": "conversation",
            "document": "document",
            "question": "question",
            "multimedia": "multimedia",
            "learning_path": "learning_path",
            "qa": "qa",
            "evaluation": "evaluation",
            "email": "email",
            "recommendation": "recommendation",
            # 语音相关意图
            "audio": "audio",
            "tts": "audio",
            "asr": "audio",
            "voice": "audio",
            "语音": "audio",
            # 题库检索意图
            "rag_question": "rag_question",
            "题库": "rag_question"
        }
        
        # Agent 配置元数据
        self._agent_metadata = {
            "conversation": {
                "name": "对话学习Agent",
                "description": "采集对话，抽取学习特征，管理用户画像",
                "processing_mode": "federated",
                "dependencies": []
            },
            "document": {
                "name": "文档生成Agent",
                "description": "生成知识点文档、大纲、思维导图",
                "processing_mode": "federated",
                "dependencies": []
            },
            "question": {
                "name": "题库练习Agent",
                "description": "出选择题、简答题、代码题",
                "processing_mode": "federated",
                "dependencies": []
            },
            "multimedia": {
                "name": "多媒体Agent",
                "description": "生成图片、概念图、视频脚本",
                "processing_mode": "federated",
                "dependencies": []
            },
            "learning_path": {
                "name": "学习路径Agent",
                "description": "规划学习路径，追踪进度",
                "processing_mode": "collaborative",
                "dependencies": ["conversation"]
            },
            "qa": {
                "name": "答疑解惑Agent",
                "description": "解答疑问，搜索相关内容",
                "processing_mode": "federated",
                "dependencies": []
            },
            "evaluation": {
                "name": "学习评估Agent",
                "description": "评估答题，分析学习效果",
                "processing_mode": "collaborative",
                "dependencies": ["question", "conversation"]
            },
            "email": {
                "name": "邮件发送Agent",
                "description": "发送学习内容到邮箱",
                "processing_mode": "federated",
                "dependencies": []
            },
            "recommendation": {
                "name": "推荐Agent",
                "description": "推荐学习资源和内容",
                "processing_mode": "collaborative",
                "dependencies": ["evaluation", "learning_path"]
            },
            # 语音Agent - 处理TTS/ASR
            "audio": {
                "name": "语音处理Agent",
                "description": "处理文字转语音(TTS)和语音转文字(ASR)",
                "processing_mode": "federated",
                "dependencies": []
            },
            # RAG题库Agent - 题库检索
            "rag_question": {
                "name": "RAG题库Agent",
                "description": "基于知识库的题库检索和练习",
                "processing_mode": "federated",
                "dependencies": []
            }
        }
        
        logger.info("[AgentFactory] Initialized")
    
    def _import_tool(self, tool_name: str):
        """根据工具名称导入工具对象"""
        tool_import_map = {
            # conversation_tools
            "save_conversation": ("tools.conversation_tools", "save_conversation"),
            "get_user_conversations": ("tools.conversation_tools", "get_user_conversations"),
            "get_user_profile": ("tools.conversation_tools", "get_user_profile"),
            "extract_features_from_conversation": ("tools.conversation_tools", "extract_features_from_conversation"),
            "update_user_feature": ("tools.conversation_tools", "update_user_feature"),
            "update_user_profile_full": ("tools.conversation_tools", "update_user_profile_full"),
            # document_tools
            "generate_document_outline": ("tools.document_tools", "generate_document_outline"),
            "generate_mindmap_structure": ("tools.document_tools", "generate_mindmap_structure"),
            "generate_full_document": ("tools.document_tools", "generate_full_document"),
            "save_learning_content": ("tools.document_tools", "save_learning_content"),
            "get_learning_content": ("tools.document_tools", "get_learning_content"),
            # question_tools
            "generate_multiple_choice": ("tools.question_tools", "generate_multiple_choice"),
            "generate_short_answer": ("tools.question_tools", "generate_short_answer"),
            "generate_coding_exercise": ("tools.question_tools", "generate_coding_exercise"),
            "generate_practice_set": ("tools.question_tools", "generate_practice_set"),
            "get_questions": ("tools.question_tools", "get_questions"),
            "save_question": ("tools.question_tools", "save_question"),
            # multimedia_tools
            "generate_illustration_image": ("tools.multimedia_tools", "generate_illustration_image"),
            "generate_concept_diagram": ("tools.multimedia_tools", "generate_concept_diagram"),
            "generate_teaching_video": ("tools.multimedia_tools", "generate_teaching_video"),
            "generate_animation_sequence": ("tools.multimedia_tools", "generate_animation_sequence"),
            "generate_multimedia_package": ("tools.multimedia_tools", "generate_multimedia_package"),
            "generate_image_batch": ("tools.multimedia_tools", "generate_image_batch"),
            # learning_path_tools
            "save_learning_path": ("tools.learning_path_tools", "save_learning_path"),
            "generate_learning_path": ("tools.learning_path_tools", "generate_learning_path"),
            "get_learning_path": ("tools.learning_path_tools", "get_learning_path"),
            "update_path_progress": ("tools.learning_path_tools", "update_path_progress"),
            "generate_personalized_content": ("tools.learning_path_tools", "generate_personalized_content"),
            "save_push_record": ("tools.learning_path_tools", "save_push_record"),
            "get_user_push_records": ("tools.learning_path_tools", "get_user_push_records"),
            # qa_tools
            "search_related_content": ("tools.qa_tools", "search_related_content"),
            "get_faq_database": ("tools.qa_tools", "get_faq_database"),
            "save_qa_record": ("tools.qa_tools", "save_qa_record"),
            "get_user_qa_history": ("tools.qa_tools", "get_user_qa_history"),
            "generate_explanation_outline": ("tools.qa_tools", "generate_explanation_outline"),
            "analyze_question_type": ("tools.qa_tools", "analyze_question_type"),
            # evaluation_tools
            "evaluate_multiple_choice": ("tools.evaluation_tools", "evaluate_multiple_choice"),
            "evaluate_short_answer": ("tools.evaluation_tools", "evaluate_short_answer"),
            "evaluate_coding_exercise": ("tools.evaluation_tools", "evaluate_coding_exercise"),
            "generate_evaluation_report": ("tools.evaluation_tools", "generate_evaluation_report"),
            "save_evaluation": ("tools.evaluation_tools", "save_evaluation"),
            "get_evaluation_history": ("tools.evaluation_tools", "get_evaluation_history"),
            "calculate_learning_progress": ("tools.evaluation_tools", "calculate_learning_progress"),
            # email_tools
            "send_text_email": ("tools.email_tools", "send_text_email"),
            "send_html_email": ("tools.email_tools", "send_html_email"),
            "send_email_with_image": ("tools.email_tools", "send_email_with_image"),
            "send_learning_plan_email": ("tools.email_tools", "send_learning_plan_email"),
            "test_email_connection": ("tools.email_tools", "test_email_connection"),
            # audio_tools - TTS/ASR
            "tts_synthesize": ("tools.audio_tools", "tts_synthesize"),
            "tts_announcement": ("tools.audio_tools", "tts_announcement"),
            "tts_storytelling": ("tools.audio_tools", "tts_storytelling"),
            "asr_recognize": ("tools.audio_tools", "asr_recognize"),
            "asr_recognize_base64": ("tools.audio_tools", "asr_recognize_base64"),
            # rag_question_tools - 题库检索
            "search_questions": ("tools.rag_question_tools", "search_questions"),
            "get_similar_questions": ("tools.rag_question_tools", "get_similar_questions"),
            "generate_practice_set": ("tools.rag_question_tools", "generate_practice_set"),
            "get_answer_explanation": ("tools.rag_question_tools", "get_answer_explanation"),
        }
        
        if tool_name in tool_import_map:
            module_path, func_name = tool_import_map[tool_name]
            try:
                module = __import__(module_path, fromlist=[func_name])
                return getattr(module, func_name)
            except Exception as e:
                logger.warning(f"Failed to import tool {tool_name}: {e}")
                return None
        return None
    
    def get_tools_for_agent(self, agent_id: str) -> List:
        """获取指定 Agent 的工具列表"""
        tool_names = self._tool_mapping.get(agent_id, [])
        tools = []
        for name in tool_names:
            tool = self._import_tool(name)
            if tool:
                tools.append(tool)
        logger.info(f"[AgentFactory] Loaded {len(tools)} tools for agent: {agent_id}")
        return tools
    
    def get_agent_id_by_intent(self, intent: str) -> Optional[str]:
        """根据意图获取对应的 Agent ID"""
        return self._intent_to_agent.get(intent.lower())
    
    def get_all_agent_ids(self) -> List[str]:
        """获取所有已配置的 Agent ID"""
        return list(self._agent_metadata.keys())
    
    def get_agent_metadata(self, agent_id: str) -> Optional[Dict]:
        """获取 Agent 元数据"""
        return self._agent_metadata.get(agent_id)
    
    def get_agent_dependencies(self, agent_id: str) -> List[str]:
        """获取 Agent 的依赖列表"""
        metadata = self._agent_metadata.get(agent_id, {})
        return metadata.get("dependencies", [])
    
    def create_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """创建 Agent 信息结构（用于 Prompt 描述）"""
        metadata = self._agent_metadata.get(agent_id, {})
        return {
            "id": agent_id,
            "name": metadata.get("name", agent_id),
            "description": metadata.get("description", ""),
            "processing_mode": metadata.get("processing_mode", "federated"),
            "dependencies": metadata.get("dependencies", []),
            "tool_count": len(self._tool_mapping.get(agent_id, []))
        }
    
    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """获取所有 Agent 的信息"""
        return [self.create_agent_info(agent_id) for agent_id in self._agent_metadata.keys()]
    
    def reset(self):
        """重置工厂状态"""
        self._agents.clear()
        logger.info("[AgentFactory] Reset")
    
    # ==================== 共享组件管理 ====================
    
    def initialize_shared_components(self) -> None:
        """初始化共享组件（MessageBus 和 SharedContext）"""
        if self._shared_context is None:
            self._shared_context = get_shared_context()
            logger.info("[AgentFactory] SharedContext initialized")
        
        if self._message_bus is None:
            self._message_bus = get_message_bus()
            logger.info("[AgentFactory] MessageBus initialized")
    
    def get_shared_context(self) -> SharedContext:
        """获取共享上下文实例"""
        if self._shared_context is None:
            self.initialize_shared_components()
        return self._shared_context
    
    def get_message_bus(self) -> MessageBus:
        """获取消息总线实例"""
        if self._message_bus is None:
            self.initialize_shared_components()
        return self._message_bus
    
    # ==================== Agent 实例管理 ====================
    
    def create_agent_instance(self, agent_id: str) -> Optional[Any]:
        """
        创建 Agent 实例
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent 实例，如果不支持则返回 None
        """
        # 确保共享组件已初始化
        self.initialize_shared_components()
        
        # 根据 agent_id 创建对应的 Agent
        agent_class_map = {
            "conversation": ("ConversationAgent", "ConversationAgent"),
            "document": ("DocumentAgent", "DocumentAgent"),
            "question": ("QuestionAgent", "QuestionAgent"),
            "multimedia": ("MultimediaAgent", "MultimediaAgent"),
            "learning_path": ("LearningPathAgent", "LearningPathAgent"),
            "qa": ("QAAgent", "QAAgent"),
            "evaluation": ("EvaluationAgent", "EvaluationAgent"),
            "email": ("EmailAgent", "EmailAgent"),
            "wechat": ("WechatAgent", "WechatAgent"),
            "rag_question": ("RagQuestionAgent", "RagQuestionAgent"),  # ✅ RAG题库Agent
            "learning_engine": ("LearningEngineAgent", "LearningEngineAgent"),  # ✅ 学习引擎Agent
            "bigdata_learning": ("BigDataLearningAgent", "BigDataLearningAgent"),  # ✅ 大数据学习Agent
            # ✅ 多模态理解Agent - 处理用户上传的图片/视频/音频
            "multimodal": ("MultimodalUnderstandingAgent", "MultimodalUnderstandingAgent"),
            # ✅ 语音处理Agent - TTS/ASR
            "audio": ("AudioAgent", "AudioAgent"),
            "recommendation": ("RecommendationAgent", "RecommendationAgent"),  # ✅ 推荐Agent - 联网搜索学习资源
        }
        
        if agent_id not in agent_class_map:
            logger.warning(f"[AgentFactory] Unknown agent_id: {agent_id}")
            return None
        
        agent_id_to_module = {
            "conversation": "conversation_agent",
            "document": "document_agent",
            "question": "question_agent",
            "multimedia": "multimedia_generation_agent",
            "learning_path": "learning_path_agent",
            "qa": "qa_agent",
            "evaluation": "evaluation_agent",
            "email": "email_agent",
            "wechat": "wechat_agent",
            "rag_question": "rag_question_agent",  # ✅ RAG题库Agent
            "learning_engine": "learning_engine_agent",  # ✅ 学习引擎Agent
            "bigdata_learning": "bigdata_learning_agent",  # ✅ 大数据学习Agent
            # ✅ 多模态理解Agent
            "multimodal": "multimodal_understanding_agent",
            # ✅ 语音处理Agent
            "audio": "audio_agent",
            # ✅ 推荐Agent - 联网搜索学习资源
            "recommendation": "recommendation_agent",
        }
        
        class_name, _ = agent_class_map[agent_id]
        module_name = agent_id_to_module.get(agent_id, f"{agent_id}_agent")
        
        try:
            # 动态导入 Agent 类
            module = __import__(
                f"multi_agent.agents.{module_name}",
                fromlist=[class_name]
            )
            agent_class = getattr(module, class_name)
            
            # 创建实例
            agent = agent_class()
            
            # 绑定工具
            tools = self.get_tools_for_agent(agent_id)
            if hasattr(agent, 'set_tools'):
                agent.set_tools(tools)
            
            # 绑定共享组件
            if hasattr(agent, 'shared_context'):
                agent.shared_context = self._shared_context
            if hasattr(agent, 'message_bus'):
                agent.message_bus = self._message_bus
            
            # 初始化 LLM 客户端（如果 Agent 有这个方法）
            if hasattr(agent, '_init_llm_client'):
                try:
                    agent._init_llm_client()
                except Exception as llm_err:
                    logger.warning(f"[AgentFactory] Failed to init LLM for {agent_id}: {llm_err}")
            
            # 缓存实例
            self._agents[agent_id] = agent
            
            # ✅ 注册到全局 Registry（使 Orchestrator 能够获取 Agent）
            try:
                registry = _get_global_registry()
                registry.register(agent)
                logger.info(f"[AgentFactory] Registered agent to global registry: {agent_id}")
            except Exception as reg_err:
                logger.warning(f"[AgentFactory] Failed to register agent to global registry: {reg_err}")
            
            logger.info(f"[AgentFactory] Created agent instance: {agent_id}")
            return agent
            
        except Exception as e:
            logger.error(f"[AgentFactory] Failed to create agent {agent_id}: {e}")
            return None
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        获取 Agent 实例（如果不存在则创建）
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent 实例
        """
        if agent_id not in self._agents:
            return self.create_agent_instance(agent_id)
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """获取所有已创建的 Agent 实例"""
        return dict(self._agents)


# 全局实例
_agent_factory: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """获取全局 Agent 工厂实例"""
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
        # 初始化共享组件
        _agent_factory.initialize_shared_components()
    return _agent_factory
