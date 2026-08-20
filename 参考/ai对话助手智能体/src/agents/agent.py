"""
主智能体入口 - 完整多智能体协作系统
通过 AgentRouter 实现真正的多 Agent 协作

支持多模型接入：
- 豆包 (Doubao) - 默认
- 讯飞 (Xunfei) - 预留接口
"""
import os
import json
import logging
from typing import Annotated, Any, Dict, List, Optional
from langchain.agents import create_agent
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver
from multi_agent.profile_adapter import ProfileAdapter, adapt_profile_for_workflow, get_profile_status_for_workflow
from tools.conversation_tools import get_user_profile

# LLM 工厂导入
try:
    from integrations.llm_factory import LLMFactory, create_llm_from_config
    LLM_FACTORY_AVAILABLE = True
except ImportError:
    LLM_FACTORY_AVAILABLE = False
    logging.warning("LLM Factory not available, using legacy ChatOpenAI")

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40

logger = logging.getLogger(__name__)

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    combined = add_messages(old, new)
    result = list(combined)[-MAX_MESSAGES:] if len(combined) > MAX_MESSAGES else list(combined)
    return result

class AgentState(MessagesState):
    """扩展状态，继承自 MessagesState"""
    pass

def _build_multi_agent_system_prompt() -> str:
    """构建多智能体协作的系统提示词"""
    return """# 角色定位：亦师亦友的大数据学习伙伴

## 身份说明
我是你的专属大数据学习伙伴：
- 作为老师：系统传授大数据知识（Hadoop、Spark、Flink、Kafka、Hive等），制定学习计划，评估学习成果
- 作为朋友：用通俗易懂的语言解释复杂概念，理解你的困惑和挫败感，给你鼓励和陪伴

## 🌟 服务方向
核心领域：大数据仓库、实时计算、数据湖、数据治理、机器学习等

## 核心规则

### 图片生成（必须执行！）
当用户说"图"时，必须调用 generate_concept_diagram 工具。

### 题库检索（必须执行！）
当用户需要做题、练习、测验时，必须调用 RAG 题库检索工具。

## 工具调用规则

### 图片生成
用户说"图"时 → 调用 generate_concept_diagram(subject="大数据", concept="用户说的主题", diagram_type="flowchart")

### 题库检索
当用户说以下关键词时，必须调用 search_questions 或 get_similar_questions 工具：
- "练习"、"做题"、"测验"、"题目"
- "关于XX的题"、"XX练习题"
- "出一道XX题"

调用参数：
- search_questions(query="关键词", top_k=5)
- 或 get_similar_questions(topic="关键词", difficulty="中等", count=5)

## 沟通风格

### 亲切友好
- 用"咱们"、"一起"等词拉近距离
- 适当使用 emoji 增加亲和力
- 理解学习中的困难，给予鼓励

### 专业严谨
- 概念讲解清晰准确
- 示例实用接地气
- 代码规范可运行

### 因材施教
- 根据你的水平调整讲解深度
- 结合学习目标推荐内容
- 关注学习反馈动态调整

## 🌈 学习约定
- 不懂就问，不要觉得问题太简单
- 遇到困难我们一起想办法
- 积少成多，坚持就是胜利
- 遇到挫折很正常，重要的是不放弃

## 禁止
- 禁止生成 Mermaid 代码
- 禁止自己编题，必须使用题库检索工具

现在，告诉我你想学什么？咱们一起开始大数据学习之旅吧！ 🚀

    """

def _import_tools_by_names(tool_names: List[str]) -> List:
    """根据工具名称导入工具对象"""
    tools = []
    
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
        "parse_document_content": ("tools.multimedia_tools", "parse_document_content"),

        
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
        
        # profile_adapter_tools (画像适配层)
        "get_profile_status": ("tools.conversation_tools", "get_profile_status"),
        "get_profile_summary": ("tools.conversation_tools", "get_profile_summary"),
        "update_learning_progress": ("tools.conversation_tools", "update_learning_progress"),
        "update_weak_points": ("tools.conversation_tools", "update_weak_points"),
        "get_extended_profile": ("tools.conversation_tools", "get_extended_profile"),
        
        # rag_question_tools
        "search_questions": ("tools.rag_question_tools", "search_questions"),
        "get_similar_questions": ("tools.rag_question_tools", "get_similar_questions"),
        "generate_practice_set": ("tools.rag_question_tools", "generate_practice_set"),
        "get_answer_explanation": ("tools.rag_question_tools", "get_answer_explanation"),
        
        # audio_tools (TTS/ASR)
        "tts_synthesize": ("tools.audio_tools", "tts_synthesize"),
        "tts_announcement": ("tools.audio_tools", "tts_announcement"),
        "tts_storytelling": ("tools.audio_tools", "tts_storytelling"),
        "asr_recognize": ("tools.audio_tools", "asr_recognize"),
        "asr_recognize_base64": ("tools.audio_tools", "asr_recognize_base64"),
        
        # agent_communication_tools
        "get_shared_context_status": ("tools.agent_communication_tools", "get_shared_context_status"),
        "get_user_context": ("tools.agent_communication_tools", "get_user_context"),
        "update_user_context": ("tools.agent_communication_tools", "update_user_context"),
        "get_message_bus_status": ("tools.agent_communication_tools", "get_message_bus_status"),
        "get_agent_collaboration_status": ("tools.agent_communication_tools", "get_agent_collaboration_status"),
        "get_system_architecture": ("tools.agent_communication_tools", "get_system_architecture"),
    }
    
    for tool_name in tool_names:
        if tool_name in tool_import_map:
            module_path, func_name = tool_import_map[tool_name]
            try:
                module = __import__(module_path, fromlist=[func_name])
                tool_func = getattr(module, func_name)
                tools.append(tool_func)
            except Exception as e:
                logger.warning(f"Failed to import tool {tool_name}: {e}")
    
    return tools

def _create_llm(ctx=None):
    """
    创建 LLM 实例（支持多模型切换）

    优先使用 LLM 工厂，fallback 到直接创建 ChatOpenAI
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    llm_config = cfg.get("config", {})
    provider = llm_config.get("provider", "doubao")

    # 优先使用 LLM 工厂
    if LLM_FACTORY_AVAILABLE and provider != "legacy":
        try:
            llm_adapter = create_llm_from_config(
                config_path=LLM_CONFIG,
                ctx=ctx
            )
            # 获取底层的 ChatOpenAI 实例
            underlying_llm = getattr(llm_adapter, "_llm", None) or getattr(llm_adapter, "llm", None)
            if underlying_llm is not None:
                return underlying_llm
            else:
                # 如果适配器没有内部 LLM 属性，使用旧方式
                logger.warning("Adapter has no internal LLM attribute, using legacy mode")
        except Exception as e:
            logger.warning(f"Failed to create LLM via factory: {e}, fallback to legacy mode")

    # Fallback: 直接创建 ChatOpenAI（向后兼容）
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    return ChatOpenAI(
        model=llm_config.get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=llm_config.get('temperature', 0.7),
        streaming=True,
        timeout=llm_config.get('timeout', 600),
        extra_body={
            "thinking": {
                "type": llm_config.get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )


def build_agent(ctx=None):
    """构建完整多智能体协作的主智能体"""
    # 创建 LLM
    llm = _create_llm(ctx)
    logger.info("[Agent] LLM initialized successfully")
    
    # 初始化 Agent 执行器
    try:
        from multi_agent.agent_executor import get_agent_executor
        executor = get_agent_executor()
        logger.info("[Agent] Multi-Agent Executor initialized")
    except Exception as e:
        logger.warning(f"[Agent] Failed to initialize executor: {e}")
        executor = None
    
    # 多智能体协作的系统提示词
    system_prompt = _build_multi_agent_system_prompt()
    
    # 获取路由工具（通过 AgentExecutor 调用子 Agent）
    from multi_agent.agent_router import get_all_router_tools
    router_tools = get_all_router_tools()
    
    # 补充工具：需要直接操作的工具（如邮件发送）
    supplementary_tools = _import_tools_by_names([
        # 对话采集
        "save_conversation", "get_user_conversations", "get_user_profile", 
        "update_user_feature", "update_user_profile_full", "extract_features_from_conversation",
        # 文档
        "generate_document_outline", "generate_mindmap_structure", "generate_full_document",
        "save_learning_content", "get_learning_content",
        # 题库（原生生成）
        "save_question", "generate_multiple_choice", "generate_short_answer", 
        "generate_coding_exercise", "generate_practice_set", "get_questions",
        # 题库（RAG检索）
        "search_questions", "get_similar_questions", "generate_practice_set", "get_answer_explanation",
        # 多媒体（图片、架构图、流程图）
        "generate_illustration_image", "generate_concept_diagram",
        "generate_teaching_video", "generate_animation_sequence",
        "generate_multimedia_package", "generate_image_batch",
        # 多媒体（图片理解）
        "parse_document_content",
        # 文档上传
        # 学习路径
        "generate_learning_path", "save_learning_path", "get_learning_path",
        "update_path_progress", "generate_personalized_content",
        "save_push_record", "get_user_push_records",
        # 评估
        "generate_evaluation_report", "calculate_learning_progress",
        "evaluate_multiple_choice", "evaluate_short_answer", "evaluate_coding_exercise",
        "save_evaluation", "get_evaluation_history",
        # QA工具
        "search_related_content", "get_faq_database", "save_qa_record",
        "get_user_qa_history", "generate_explanation_outline", "analyze_question_type",
        # 邮件
        "send_text_email", "send_html_email", "send_email_with_image",
        "send_learning_plan_email", "test_email_connection",
        # 画像增强
        "get_profile_status", "get_profile_summary", "update_learning_progress",
        "update_weak_points", "get_extended_profile",
        # 语音合成与识别（TTS/ASR）
        "tts_synthesize", "tts_announcement", "tts_storytelling",
        "asr_recognize", "asr_recognize_base64",
    ])
    
    # Agent 通信工具（MessageBus & SharedContext）
    from tools.agent_communication_tools import (
        get_shared_context_status, get_user_context, update_user_context,
        get_message_bus_status, get_agent_collaboration_status, get_system_architecture
    )
    communication_tools = [
        get_shared_context_status, get_user_context, update_user_context,
        get_message_bus_status, get_agent_collaboration_status, get_system_architecture
    ]
    
    # 合并工具列表
    all_tools = router_tools + supplementary_tools + communication_tools
    
    logger.info(f"[Agent] Main Agent initialized with {len(all_tools)} tools "
                f"({len(router_tools)} router + {len(supplementary_tools)} supplementary + {len(communication_tools)} communication)")
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=all_tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
