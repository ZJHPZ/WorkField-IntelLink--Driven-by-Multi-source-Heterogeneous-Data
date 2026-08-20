"""
对话采集与特征抽取工具模块
功能：采集用户对话内容，抽取6维特征，支持动态更新
"""
import json
from typing import Optional
from langchain.tools import tool
from storage.database.supabase_client import get_supabase_client
from storage.database import DatabaseManager
from postgrest.exceptions import APIError
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def save_conversation(user_id: str, role: str, content: str, metadata: Optional[dict] = None) -> str:
    """
    保存用户对话记录到数据库。
    
    Args:
        user_id: 用户唯一标识
        role: 角色类型 (user/assistant/system)
        content: 对话内容
        metadata: 附加元数据
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_conversation")
    
    try:
        client = get_supabase_client()
        
        conversation_data = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "extra_data": metadata
        }
        
        response = client.table("conversations").insert(conversation_data).execute()
        
        return f"对话已保存，用户ID: {user_id}, 角色: {role}, 内容长度: {len(content)}字符"
    
    except APIError as e:
        raise Exception(f"保存对话失败: {e.message}")


@tool
def get_user_conversations(user_id: str, limit: int = 50) -> str:
    """
    获取用户的历史对话记录。
    
    Args:
        user_id: 用户唯一标识
        limit: 返回记录数量限制
    
    Returns:
        用户对话记录列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_user_conversations")
    
    try:
        client = get_supabase_client()
        
        response = client.table("conversations") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        conversations = response.data
        
        return json.dumps({
            "user_id": user_id,
            "total": len(conversations),
            "conversations": conversations
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取对话记录失败: {e.message}")


@tool
def get_user_profile(user_id: str) -> str:
    """
    获取用户画像信息（6维特征）。
    
    Args:
        user_id: 用户唯一标识
    
    Returns:
        用户画像信息（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_user_profile")
    
    try:
        client = get_supabase_client()
        
        response = client.table("user_profiles") \
            .select("*") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        
        if response is None:
            return json.dumps({
                "user_id": user_id,
                "exists": False,
                "message": "用户画像不存在"
            }, ensure_ascii=False)
        
        return json.dumps({
            "user_id": user_id,
            "exists": True,
            "profile": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取用户画像失败: {e.message}")


@tool
def update_user_feature(user_id: str, feature_type: str, feature_value: str) -> str:
    """
    更新用户画像的单一特征维度。
    
    Args:
        user_id: 用户唯一标识
        feature_type: 特征类型
            - learning_style: 学习风格
            - knowledge_level: 知识水平
            - learning_goal: 学习目标
            - learning_speed: 学习速度
            - learning_preference: 学习偏好
            - learning_progress: 学习进度
        feature_value: 特征值（JSON格式字符串）
    
    Returns:
        更新结果信息
    """
    ctx = request_context.get() or new_context(method="update_user_feature")
    
    try:
        client = get_supabase_client()
        
        # 检查用户是否存在
        existing = client.table("user_profiles") \
            .select("id") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        
        update_data = {feature_type: feature_value}
        
        if existing is None:
            # 创建新用户画像
            profile_data = {
                "user_id": user_id,
                feature_type: feature_value
            }
            client.table("user_profiles").insert(profile_data).execute()
            return f"已创建用户画像并设置 {feature_type} = {feature_value}"
        else:
            # 更新现有画像
            client.table("user_profiles") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()
            return f"已更新用户 {user_id} 的特征 {feature_type} = {feature_value}"
    
    except APIError as e:
        raise Exception(f"更新用户特征失败: {e.message}")


@tool
def update_user_profile_full(user_id: str, learning_style: Optional[str] = None,
                              knowledge_level: Optional[str] = None,
                              learning_goal: Optional[str] = None,
                              learning_speed: Optional[str] = None,
                              learning_preference: Optional[str] = None,
                              learning_progress: Optional[str] = None) -> str:
    """
    批量更新用户画像的所有6维特征。
    
    Args:
        user_id: 用户唯一标识
        learning_style: 学习风格 (视觉型/听觉型/阅读型/动觉型)
        knowledge_level: 知识水平 (入门/初级/中级/高级)
        learning_goal: 学习目标
        learning_speed: 学习速度 (慢速/中速/快速)
        learning_preference: 学习偏好配置 (JSON格式字符串)
        learning_progress: 学习进度记录 (JSON格式字符串)
    
    Returns:
        更新结果信息
    """
    ctx = request_context.get() or new_context(method="update_user_profile_full")
    
    try:
        client = get_supabase_client()
        
        # 构建更新数据
        update_data = {}
        if learning_style is not None:
            update_data["learning_style"] = learning_style
        if knowledge_level is not None:
            update_data["knowledge_level"] = knowledge_level
        if learning_goal is not None:
            update_data["learning_goal"] = learning_goal
        if learning_speed is not None:
            update_data["learning_speed"] = learning_speed
        if learning_preference is not None:
            try:
                update_data["learning_preference"] = json.loads(learning_preference)
            except json.JSONDecodeError:
                update_data["learning_preference"] = learning_preference
        if learning_progress is not None:
            try:
                update_data["learning_progress"] = json.loads(learning_progress)
            except json.JSONDecodeError:
                update_data["learning_progress"] = learning_progress
        
        # 检查用户是否存在
        existing = client.table("user_profiles") \
            .select("id") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        
        if existing is None:
            # 创建新用户画像
            profile_data = {"user_id": user_id}
            profile_data.update(update_data)
            client.table("user_profiles").insert(profile_data).execute()
            return f"已创建用户 {user_id} 的完整画像"
        else:
            # 更新现有画像
            if update_data:
                client.table("user_profiles") \
                    .update(update_data) \
                    .eq("user_id", user_id) \
                    .execute()
            return f"已更新用户 {user_id} 的画像特征"
    
    except APIError as e:
        raise Exception(f"更新用户画像失败: {e.message}")


@tool
def extract_features_from_conversation(user_id: str) -> str:
    """
    从用户历史对话中抽取并更新6维特征。
    该工具会分析用户最近的对话内容，自动推断学习风格、知识水平等特征。
    
    Args:
        user_id: 用户唯一标识
    
    Returns:
        抽取分析结果和建议
    """
    ctx = request_context.get() or new_context(method="extract_features_from_conversation")
    
    try:
        client = get_supabase_client()
        
        # 获取用户最近的对话记录
        response = client.table("conversations") \
            .select("content, role") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
        
        conversations = list(response.data)
        
        if not conversations:
            return json.dumps({
                "user_id": user_id,
                "message": "没有找到足够的对话记录进行分析",
                "suggestions": ["建议先进行一些学习对话后再尝试特征抽取"]
            }, ensure_ascii=False, indent=2)
        
        # 汇总对话内容用于分析
        user_messages = []
        for c in conversations:
            if isinstance(c, dict) and c.get("role") == "user":
                user_messages.append(str(c.get("content", "")))
        total_content = "\n".join(user_messages)
        
        return json.dumps({
            "user_id": user_id,
            "conversation_count": len(conversations),
            "content_length": len(total_content),
            "message": "已获取对话记录，请根据对话内容分析并调用 update_user_feature 或 update_user_profile_full 更新用户特征",
            "analysis_prompt": f"请分析以下对话内容，提取用户的6维学习特征：\n\n{total_content[:2000]}"
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"抽取特征失败: {e.message}")


@tool
def update_learning_progress(user_id: str, progress_data: dict) -> str:
    """
    更新用户学习进度

    Args:
        user_id: 用户ID
        progress_data: 学习进度数据，格式为:
            {
                "current_topic": str,     # 当前学习主题
                "completed_topics": [],   # 已完成的主题列表
                "weak_points": [],        # 薄弱点列表
                "progress_percentage": int  # 进度百分比
            }

    Returns:
        JSON格式的更新结果
    """
    try:
        from storage.database import DatabaseManager
        db = DatabaseManager()

        # 获取当前进度
        profile = db.get_user_profile(user_id)
        if not profile:
            return json.dumps({"success": False, "message": "用户不存在"}, ensure_ascii=False)

        current_progress = profile.get("learning_progress", {}) or {}

        # 更新进度
        if "current_topic" in progress_data:
            current_progress["current_topic"] = progress_data["current_topic"]
        if "completed_topics" in progress_data:
            current_progress["completed_topics"] = progress_data["completed_topics"]
        if "weak_points" in progress_data:
            current_progress["weak_points"] = progress_data["weak_points"]
        if "progress_percentage" in progress_data:
            current_progress["progress_percentage"] = progress_data["progress_percentage"]

        # 保存更新
        db.update_user_profile(
            user_id=user_id,
            profile_data={"learning_progress": current_progress}
        )

        return json.dumps({
            "success": True,
            "message": "学习进度已更新",
            "learning_progress": current_progress
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"更新学习进度失败: {str(e)}"
        }, ensure_ascii=False)


@tool
def update_weak_points(user_id: str, weak_points: list) -> str:
    """
    更新用户薄弱点

    Args:
        user_id: 用户ID
        weak_points: 薄弱点列表

    Returns:
        JSON格式的更新结果
    """
    try:
        from storage.database import DatabaseManager
        db = DatabaseManager()

        # 获取当前进度
        profile = db.get_user_profile(user_id)
        if not profile:
            return json.dumps({"success": False, "message": "用户不存在"}, ensure_ascii=False)

        current_progress = profile.get("learning_progress", {}) or {}
        current_progress["weak_points"] = weak_points

        # 保存更新
        db.update_user_profile(
            user_id=user_id,
            profile_data={"learning_progress": current_progress}
        )

        return json.dumps({
            "success": True,
            "message": "薄弱点已更新",
            "weak_points": weak_points
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"更新薄弱点失败: {str(e)}"
        }, ensure_ascii=False)


@tool
def get_extended_profile(user_id: str) -> str:
    """
    获取扩展的用户画像（包含工作流期望的所有字段）

    返回完整画像结构，包括:
    - 6个基础维度
    - 扩展的学习偏好
    - 沟通风格偏好

    Args:
        user_id: 用户ID

    Returns:
        JSON格式的扩展画像
    """
    try:
        from storage.database import DatabaseManager
        db = DatabaseManager()

        profile = db.get_user_profile(user_id)
        if not profile:
            return json.dumps({
                "success": False,
                "message": "用户不存在",
                "profile": None
            }, ensure_ascii=False)

        # 构建扩展画像
        extended_profile = {
            # 基础维度
            "learning_style": profile.get("learning_style", ""),
            "knowledge_level": profile.get("knowledge_level", ""),
            "learning_goal": profile.get("learning_goal", ""),
            "learning_speed": profile.get("learning_speed", ""),

            # 学习偏好
            "learning_preference": profile.get("learning_preference", {}),

            # 学习进度
            "learning_progress": profile.get("learning_progress", {}),

            # 扩展字段（工作流特有）
            "interests": _extract_interests(profile),
            "communication_preferences": _extract_communication_preferences(profile),
            "avoid_patterns": _extract_avoid_patterns(profile),
            "explanation_style": _infer_explanation_style(profile),
            "feedback_style": _infer_feedback_style(profile),
            "strengths": _extract_strengths(profile),
            "weaknesses": _extract_weaknesses(profile),

            # 元数据
            "profile_version": "2.0",
            "last_updated": profile.get("updated_at", "")
        }

        return json.dumps({
            "success": True,
            "profile": extended_profile
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"获取扩展画像失败: {str(e)}"
        }, ensure_ascii=False)


def _extract_interests(profile: dict) -> list:
    """从学习目标中提取兴趣领域"""
    learning_goal = profile.get("learning_goal", "")
    # 简单的关键词提取
    interests = []
    keywords = ["Python", "大数据", "Hadoop", "Spark", "机器学习", "人工智能", "数据分析"]
    for keyword in keywords:
        if keyword in learning_goal:
            interests.append(keyword)
    return interests if interests else ["编程基础"]


def _extract_communication_preferences(profile: dict) -> dict:
    """从学习偏好中提取沟通偏好"""
    learning_pref = profile.get("learning_preference", {}) or {}

    content_types = learning_pref.get("content_type", ["图文"])

    # 根据内容类型推断沟通偏好
    explanation_styles = {
        "图文": "visual_with_examples",
        "短视频": "concise_with_visual",
        "音频": "narrative_style",
        "代码": "code_first"
    }

    explanation_style = explanation_styles.get(content_types[0], "balanced")

    return {
        "explanation_style": explanation_style,
        "feedback_style": "encouraging_specific",
        "response_length": "medium"
    }


def _extract_avoid_patterns(profile: dict) -> list:
    """提取应避免的模式"""
    avoid_patterns = []

    learning_pref = profile.get("learning_preference", {}) or {}

    # 从偏好中推断避免模式
    avoid_content = learning_pref.get("avoid_content", "")
    if "大段文字" in avoid_content or "长文本" in avoid_content:
        avoid_patterns.append("过度理论讲解")
        avoid_patterns.append("长篇纯文字解释")

    # 根据学习风格推断
    learning_style = profile.get("learning_style", "")
    if learning_style == "视觉型":
        avoid_patterns.append("纯文字解释")
        avoid_patterns.append("缺乏图示")
    elif learning_style == "听觉型":
        avoid_patterns.append("仅文字沟通")

    return avoid_patterns if avoid_patterns else ["过度批评"]


def _infer_explanation_style(profile: dict) -> str:
    """根据学习风格推断解释风格"""
    learning_style = profile.get("learning_style", "")
    knowledge_level = profile.get("knowledge_level", "")

    if knowledge_level == "入门":
        return "simple_with_examples"
    elif knowledge_level == "初级":
        return "structured_with_exercises"
    elif knowledge_level == "中级":
        return "advanced_with_challenges"
    elif knowledge_level == "高级":
        return "concise_technical"

    if learning_style == "视觉型":
        return "visual_with_diagrams"
    elif learning_style == "听觉型":
        return "narrative_examples"

    return "balanced_multimodal"


def _infer_feedback_style(profile: dict) -> str:
    """根据学习风格推断反馈风格"""
    learning_style = profile.get("learning_style", "")

    if learning_style == "视觉型":
        return "encouraging_with_visual"
    elif learning_style == "听觉型":
        return "encouraging_narrative"

    return "encouraging_specific"


def _extract_strengths(profile: dict) -> list:
    """提取用户优势"""
    progress = profile.get("learning_progress", {}) or {}
    completed = progress.get("completed_topics", [])

    # 根据已完成的主题推断优势
    strengths = []
    topic_mapping = {
        "Python基础": "编程基础",
        "数据结构": "逻辑思维",
        "算法": "问题解决",
        "数据库": "数据管理"
    }

    for topic in completed:
        if topic in topic_mapping:
            strengths.append(topic_mapping[topic])

    return strengths if strengths else ["学习能力"]


def _extract_weaknesses(profile: dict) -> list:
    """提取用户劣势"""
    progress = profile.get("learning_progress", {}) or {}
    weak_points = progress.get("weak_points", [])

    return weak_points if weak_points else []
