"""
答疑智能体工具模块
功能：为用户提供学习过程中的问题解答服务
"""
import json
from typing import Optional, List
from langchain.tools import tool
from storage.database.supabase_client import get_supabase_client
from postgrest.exceptions import APIError
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def search_related_content(subject: str, topic: str, keywords: Optional[str] = None) -> str:
    """
    搜索相关的学习内容。
    
    Args:
        subject: 学习科目
        topic: 知识点
        keywords: 关键词（可选）
    
    Returns:
        相关内容列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="search_related_content")
    
    try:
        client = get_supabase_client()
        
        # 构建查询
        query = client.table("learning_contents") \
            .select("*") \
            .eq("subject", subject) \
            .eq("topic", topic)
        
        response = query.execute()
        
        return json.dumps({
            "subject": subject,
            "topic": topic,
            "keywords": keywords,
            "count": len(response.data),
            "related_content": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"搜索相关内容失败: {e.message}")


@tool
def get_faq_database(subject: str) -> str:
    """
    获取科目的常见问题库。
    
    Args:
        subject: 学习科目
    
    Returns:
        常见问题列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_faq_database")
    
    # 预定义一些常见问题模板
    faq_templates = {
        "Python": [
            {"question": "什么是Python？", "answer": "Python是一门高级编程语言..."},
            {"question": "如何安装Python？", "answer": "可以从官网下载安装包..."},
            {"question": "Python的基本数据类型有哪些？", "answer": "包括int, float, str, bool, list, dict等..."}
        ],
        "JavaScript": [
            {"question": "什么是JavaScript？", "answer": "JavaScript是一门脚本语言..."},
            {"question": "如何定义变量？", "answer": "可以使用var, let, const..."}
        ]
    }
    
    default_faqs = [
        {"question": "这个概念是什么意思？", "answer": "请详细描述您不理解的部分，我将为您解答。"},
        {"question": "如何应用这个知识点？", "answer": "这个知识点可以应用在..."},
        {"question": "有什么注意事项？", "answer": "使用时需要注意以下几点..."}
    ]
    
    faqs = faq_templates.get(subject, default_faqs)
    
    return json.dumps({
        "subject": subject,
        "faqs": faqs,
        "message": "常见问题列表"
    }, ensure_ascii=False, indent=2)


@tool
def save_qa_record(user_id: str, subject: str, question: str, answer: str) -> str:
    """
    保存问答记录。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
        question: 问题
        answer: 回答
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_qa_record")
    
    try:
        client = get_supabase_client()
        
        # 保存对话记录
        conversation_data = [
            {"role": "user", "content": question, "user_id": user_id, "subject": subject},
            {"role": "assistant", "content": answer, "user_id": user_id, "subject": subject}
        ]
        
        for conv in conversation_data:
            client.table("conversations").insert(conv).execute()
        
        return json.dumps({
            "success": True,
            "message": "问答记录已保存",
            "user_id": user_id,
            "subject": subject
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"保存问答记录失败: {e.message}")


@tool
def get_user_qa_history(user_id: str, subject: Optional[str] = None, limit: int = 20) -> str:
    """
    获取用户的问答历史。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目（可选）
        limit: 返回数量限制
    
    Returns:
        问答历史列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_user_qa_history")
    
    try:
        client = get_supabase_client()
        
        query = client.table("conversations") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit)
        
        if subject:
            query = query.eq("subject", subject)
        
        response = query.execute()
        
        # 整理成问答对
        qa_pairs = []
        temp_q = None
        for conv in response.data if response.data else []:
            if isinstance(conv, dict):
                if conv.get("role") == "user":
                    temp_q = conv
                elif conv.get("role") == "assistant" and temp_q:
                    qa_pairs.append({
                        "question": temp_q.get("content"),
                        "answer": conv.get("content"),
                        "timestamp": str(conv.get("created_at"))
                    })
                    temp_q = None
        
        return json.dumps({
            "user_id": user_id,
            "subject": subject,
            "count": len(qa_pairs),
            "qa_history": qa_pairs
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取问答历史失败: {e.message}")


@tool
def generate_explanation_outline(subject: str, topic: str) -> str:
    """
    生成知识点的讲解大纲。
    
    Args:
        subject: 学习科目
        topic: 知识点
    
    Returns:
        讲解大纲（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_explanation_outline")
    
    outline = {
        "subject": subject,
        "topic": topic,
        "sections": [
            {
                "title": "基础概念",
                "subsections": [
                    "定义",
                    "背景",
                    "核心术语"
                ]
            },
            {
                "title": "核心原理",
                "subsections": [
                    "工作原理",
                    "关键机制",
                    "重要特性"
                ]
            },
            {
                "title": "实践应用",
                "subsections": [
                    "使用场景",
                    "实际案例",
                    "注意事项"
                ]
            },
            {
                "title": "常见问题",
                "subsections": [
                    "FAQ 1",
                    "FAQ 2",
                    "FAQ 3"
                ]
            }
        ]
    }
    
    return json.dumps({
        "outline": outline,
        "message": "已生成讲解大纲，可用于结构化解答"
    }, ensure_ascii=False, indent=2)


@tool
def analyze_question_type(question: str) -> str:
    """
    分析问题类型和难度。
    
    Args:
        question: 用户问题
    
    Returns:
        问题分析结果（JSON格式）
    """
    ctx = request_context.get() or new_context(method="analyze_question_type")
    
    # 简单分析问题类型
    question_lower = question.lower()
    
    # 判断问题类型
    if any(kw in question_lower for kw in ["什么是", "定义", "概念", "是什么"]):
        q_type = "概念理解"
    elif any(kw in question_lower for kw in ["如何", "怎么", "步骤", "方法"]):
        q_type = "方法应用"
    elif any(kw in question_lower for kw in ["为什么", "原因", "原理", "为什么"]):
        q_type = "原理分析"
    elif any(kw in question_lower for kw in ["比较", "区别", "不同", "差异"]):
        q_type = "对比分析"
    elif any(kw in question_lower for kw in ["代码", "程序", "实现", "编程"]):
        q_type = "编程实践"
    else:
        q_type = "综合问题"
    
    # 判断问题难度
    if len(question) < 30:
        difficulty = "简单"
    elif len(question) < 100:
        difficulty = "中等"
    else:
        difficulty = "复杂"
    
    return json.dumps({
        "question": question,
        "type": q_type,
        "difficulty": difficulty,
        "message": f"问题类型: {q_type}, 难度: {difficulty}"
    }, ensure_ascii=False, indent=2)
