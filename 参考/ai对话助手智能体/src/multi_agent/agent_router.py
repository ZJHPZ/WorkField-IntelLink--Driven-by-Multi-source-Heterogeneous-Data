"""
同步路由层 - 桥接主 Agent 和子 Agent
将工具调用路由到对应的子 Agent 执行
"""
import json
import logging
from typing import Any, Dict, Optional
from langchain.tools import tool

from multi_agent.agent_executor import get_agent_executor

logger = logging.getLogger(__name__)


# 全局执行器实例（延迟初始化）
_executor = None


def _get_executor():
    """获取执行器实例"""
    global _executor
    if _executor is None:
        _executor = get_agent_executor()
    return _executor


def _build_state_from_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """从工具参数构建状态"""
    state = {}
    
    # 提取通用参数
    if "user_id" in kwargs:
        state["user_id"] = kwargs["user_id"]
    if "subject" in kwargs:
        state["subject"] = kwargs["subject"]
    if "topic" in kwargs:
        state["topic"] = kwargs["topic"]
    if "knowledge_level" in kwargs:
        state["knowledge_level"] = kwargs["knowledge_level"]
    if "learning_speed" in kwargs:
        state["learning_speed"] = kwargs["learning_speed"]
    
    # 保存原始参数供后续使用
    state["_raw_kwargs"] = kwargs
    
    return state


# ============== 对话 Agent 路由工具 ==============

@tool
def route_conversation_agent(user_input: str, **kwargs) -> str:
    """
    路由到对话学习 Agent 处理对话类任务
    
    Args:
        user_input: 用户输入的内容
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        
        result = executor.execute_sync(
            agent_id="conversation",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "处理完成")
        else:
            return f"处理失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_conversation_agent error: {e}")
        return f"对话处理异常: {str(e)}"


# ============== 文档 Agent 路由工具 ==============

@tool
def route_document_agent(topic: str, subject: str = "通用", **kwargs) -> str:
    """
    路由到文档生成 Agent 处理文档类任务
    
    Args:
        topic: 文档主题
        subject: 学科/科目
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["topic"] = topic
        state["subject"] = subject
        
        user_input = f"生成关于 {subject} 的 {topic} 文档"
        
        result = executor.execute_sync(
            agent_id="document",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "文档生成完成")
        else:
            return f"文档生成失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_document_agent error: {e}")
        return f"文档处理异常: {str(e)}"


# ============== 题库 Agent 路由工具 ==============

@tool
def route_question_agent(topic: str, question_type: str = "multiple_choice", 
                         difficulty: str = "中等", count: int = 5, **kwargs) -> str:
    """
    路由到题库 Agent 处理题目生成任务
    
    Args:
        topic: 题目主题
        question_type: 题目类型 (multiple_choice/short_answer/coding)
        difficulty: 难度等级
        count: 题目数量
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["topic"] = topic
        state["question_type"] = question_type
        state["difficulty"] = difficulty
        
        type_names = {
            "multiple_choice": "选择题",
            "short_answer": "简答题",
            "coding": "编程题"
        }
        type_name = type_names.get(question_type, "练习题")
        
        user_input = f"生成 {count} 道关于 {topic} 的{type_name}"
        
        result = executor.execute_sync(
            agent_id="question",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "题目生成完成")
        else:
            return f"题目生成失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_question_agent error: {e}")
        return f"题目处理异常: {str(e)}"


# ============== 多媒体 Agent 路由工具 ==============

@tool
def route_multimedia_agent(topic: str, media_type: str = "image", **kwargs) -> str:
    """
    路由到多媒体 Agent 处理多媒体生成任务
    
    Args:
        topic: 内容主题
        media_type: 媒体类型 (image/video/animation)
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["topic"] = topic
        state["media_type"] = media_type
        
        user_input = f"为 {topic} 生成{media_type}内容"
        
        result = executor.execute_sync(
            agent_id="multimedia",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "多媒体生成完成")
        else:
            return f"多媒体生成失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_multimedia_agent error: {e}")
        return f"多媒体处理异常: {str(e)}"


# ============== 学习路径 Agent 路由工具 ==============

@tool
def route_learning_path_agent(subject: str, knowledge_level: str = "初级",
                               learning_speed: str = "中速", **kwargs) -> str:
    """
    路由到学习路径 Agent 处理学习规划任务
    
    Args:
        subject: 学习科目
        knowledge_level: 知识水平
        learning_speed: 学习速度
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["subject"] = subject
        state["knowledge_level"] = knowledge_level
        state["learning_speed"] = learning_speed
        
        user_input = f"制定一个 {subject} 学习计划，难度 {knowledge_level}，学习速度 {learning_speed}"
        
        result = executor.execute_sync(
            agent_id="learning_path",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "学习路径规划完成")
        else:
            return f"学习路径规划失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_learning_path_agent error: {e}")
        return f"学习路径处理异常: {str(e)}"


# ============== 答疑 Agent 路由工具 ==============

@tool
def route_qa_agent(question: str, **kwargs) -> str:
    """
    路由到答疑 Agent 处理问答任务
    
    Args:
        question: 用户的问题
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        
        result = executor.execute_sync(
            agent_id="qa",
            user_input=question,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "答疑完成")
        else:
            return f"答疑失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_qa_agent error: {e}")
        return f"答疑处理异常: {str(e)}"


# ============== 评估 Agent 路由工具 ==============

@tool
def route_evaluation_agent(subject: str, topic: str = "", **kwargs) -> str:
    """
    路由到评估 Agent 处理学习评估任务
    
    Args:
        subject: 评估科目
        topic: 评估主题（可选）
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["subject"] = subject
        state["topic"] = topic
        
        user_input = f"评估我对 {subject} 的学习水平"
        if topic:
            user_input += f"，重点关注 {topic}"
        
        result = executor.execute_sync(
            agent_id="evaluation",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "评估完成")
        else:
            return f"评估失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_evaluation_agent error: {e}")
        return f"评估处理异常: {str(e)}"


# ============== 协作式路由工具 ==============

@tool
def route_collaborative_learning_path(subject: str, knowledge_level: str = "初级",
                                       learning_speed: str = "中速", **kwargs) -> str:
    """
    协作式学习路径规划（需要多个 Agent 协作）
    
    协作链: conversation -> learning_path
    
    Args:
        subject: 学习科目
        knowledge_level: 知识水平
        learning_speed: 学习速度
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["subject"] = subject
        state["knowledge_level"] = knowledge_level
        state["learning_speed"] = learning_speed
        
        user_input = f"制定一个 {subject} 学习计划"
        
        result = executor.execute_collaborative_sync(
            intent="learning_path",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "学习路径规划完成")
        else:
            return f"学习路径规划失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_collaborative_learning_path error: {e}")
        return f"协作处理异常: {str(e)}"


@tool
def route_collaborative_evaluation(subject: str, **kwargs) -> str:
    """
    协作式学习评估（需要多个 Agent 协作）
    
    协作链: conversation -> question -> evaluation
    
    Args:
        subject: 评估科目
        
    Returns:
        处理结果
    """
    try:
        executor = _get_executor()
        state = _build_state_from_kwargs(kwargs)
        state["subject"] = subject
        
        user_input = f"评估我对 {subject} 的学习水平"
        
        result = executor.execute_collaborative_sync(
            intent="evaluation",
            user_input=user_input,
            state=state
        )
        
        if result.get("success"):
            return result.get("output", "评估完成")
        else:
            return f"评估失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error(f"[Router] route_collaborative_evaluation error: {e}")
        return f"协作处理异常: {str(e)}"


# ============== 获取所有路由工具 ==============

def get_all_router_tools():
    """获取所有路由工具"""
    return [
        # 单 Agent 路由
        route_conversation_agent,
        route_document_agent,
        route_question_agent,
        route_multimedia_agent,
        route_learning_path_agent,
        route_qa_agent,
        route_evaluation_agent,
        # 协作式路由
        route_collaborative_learning_path,
        route_collaborative_evaluation,
    ]
