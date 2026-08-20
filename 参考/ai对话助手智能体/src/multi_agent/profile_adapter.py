"""
画像适配层模块

将多智能体系统的6维用户画像转换为工作流期望的结构：
- 我的系统：learning_style, knowledge_level, learning_goal, learning_speed, learning_preference, learning_progress
- 工作流期望：learning_style, knowledge_level, interests, communication_preferences, avoid_patterns, strengths, weaknesses, explanation_style, feedback_style
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProfileAdapter:
    """画像适配器：转换画像结构以适配工作流"""

    # 学习风格映射
    LEARNING_STYLE_MAPPING = {
        "视觉型": "visual",
        "听觉型": "auditory",
        "阅读型": "reading",
        "动觉型": "kinesthetic",
        "visual": "visual",
        "auditory": "auditory",
        "reading": "reading",
        "kinesthetic": "kinesthetic",
    }

    # 知识水平映射
    KNOWLEDGE_LEVEL_MAPPING = {
        "入门": "beginner",
        "初级": "beginner",
        "中级": "intermediate",
        "高级": "advanced",
        "beginner": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
    }

    # 学习速度映射
    LEARNING_SPEED_MAPPING = {
        "慢速": "slow",
        "中速": "moderate",
        "快速": "fast",
        "slow": "slow",
        "moderate": "moderate",
        "fast": "fast",
    }

    def __init__(self, profile_data: Optional[Dict[str, Any]] = None):
        """
        初始化画像适配器

        Args:
            profile_data: 原始的用户画像数据（6维结构）
        """
        self.profile_data = profile_data or {}

    def get_profile_status(self) -> Dict[str, Any]:
        """
        获取画像状态

        Returns:
            {
                "is_ready": bool,           # 画像是否可用
                "fallback_used": bool,      # 是否使用降级策略
                "message": str,              # 状态消息
                "profile_fields": list       # 可用的画像字段
            }
        """
        is_ready = self.profile_data is not None and self.profile_data.get("user_id") is not None
        available_fields = []

        if is_ready:
            if self.profile_data.get("learning_style"):
                available_fields.append("learning_style")
            if self.profile_data.get("knowledge_level"):
                available_fields.append("knowledge_level")
            if self.profile_data.get("learning_goal"):
                available_fields.append("interests")
            if self.profile_data.get("learning_preference"):
                available_fields.append("communication_preferences")

        return {
            "is_ready": is_ready,
            "fallback_used": not is_ready,
            "message": "画像可用" if is_ready else "画像不可用，将使用通用配置",
            "profile_fields": available_fields
        }

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        获取画像摘要 - 转换为工作流期望的结构

        Returns:
            工作流期望的画像结构：
            {
                "learning_style": str,
                "knowledge_level": str,
                "interests": list[str],
                "communication_preferences": {
                    "explanation_style": str,
                    "feedback_style": str,
                    "study_time": str,
                    "content_types": list[str]
                },
                "avoid_patterns": list[str],
                "strengths": list[str],
                "weaknesses": list[str],
                "explanation_style": str,
                "feedback_style": str
            }
        """
        if not self.profile_data or not self.profile_data.get("user_id"):
            return self._get_default_profile()

        return {
            # 基础维度（直接映射）
            "learning_style": self._map_learning_style(),
            "knowledge_level": self._map_knowledge_level(),

            # 兴趣领域（从learning_goal转换）
            "interests": self._extract_interests(),

            # 沟通偏好（从learning_preference转换）
            "communication_preferences": self._extract_communication_preferences(),

            # 避免模式（从learning_preference和learning_progress推断）
            "avoid_patterns": self._extract_avoid_patterns(),

            # 优势（从learning_progress转换）
            "strengths": self._extract_strengths(),

            # 劣势（从learning_progress转换）
            "weaknesses": self._extract_weaknesses(),

            # 解释风格（基于学习风格推断）
            "explanation_style": self._infer_explanation_style(),

            # 反馈风格（基于知识水平推断）
            "feedback_style": self._infer_feedback_style()
        }

    def _map_learning_style(self) -> str:
        """映射学习风格"""
        style = self.profile_data.get("learning_style", "")
        return self.LEARNING_STYLE_MAPPING.get(style, "visual")

    def _map_knowledge_level(self) -> str:
        """映射知识水平"""
        level = self.profile_data.get("knowledge_level", "")
        return self.KNOWLEDGE_LEVEL_MAPPING.get(level, "beginner")

    def _extract_interests(self) -> list:
        """从learning_goal提取兴趣领域"""
        goal = self.profile_data.get("learning_goal", "")
        if not goal:
            return []

        # 如果是字符串，尝试解析
        if isinstance(goal, str):
            # 尝试解析JSON格式
            if goal.startswith('"') or goal.startswith('['):
                try:
                    goal = json.loads(goal)
                except json.JSONDecodeError:
                    pass

            # 简单的关键词提取
            interests = []
            keywords = ["Python", "Java", "大数据", "机器学习", "深度学习",
                       "Hadoop", "Spark", "Flink", "Hive", "数据分析",
                       "网络安全", "云计算", "Web开发", "移动开发"]

            for keyword in keywords:
                if keyword in goal:
                    interests.append(keyword)

            return interests if interests else [goal[:50]]

        return []

    def _extract_communication_preferences(self) -> Dict[str, Any]:
        """从learning_preference提取沟通偏好"""
        pref = self.profile_data.get("learning_preference", {})

        if isinstance(pref, str):
            try:
                pref = json.loads(pref) if pref else {}
            except json.JSONDecodeError:
                pref = {}

        # 推断学习风格对应的沟通偏好
        learning_style = self._map_learning_style()
        study_time = pref.get("study_time", "晚上8点后")
        content_types = pref.get("content_type", ["图文", "短视频"])

        # 根据学习风格推断解释风格偏好
        explanation_styles = {
            "visual": "visual_with_examples",
            "auditory": "verbal_explanation",
            "reading": "text_based",
            "kinesthetic": "hands_on_examples"
        }

        return {
            "explanation_style": explanation_styles.get(learning_style, "visual_with_examples"),
            "feedback_style": "encouraging_specific",
            "study_time": study_time,
            "content_types": content_types
        }

    def _extract_avoid_patterns(self) -> list:
        """提取需要避免的模式"""
        avoid_patterns = []

        # 从learning_preference推断
        pref = self.profile_data.get("learning_preference", {})
        if isinstance(pref, dict):
            if pref.get("avoid_content"):
                avoid_content = pref.get("avoid_content")
                if isinstance(avoid_content, list):
                    avoid_patterns.extend(avoid_content)
                else:
                    avoid_patterns.append(str(avoid_content))

        # 基于学习速度推断
        speed = self.profile_data.get("learning_speed", "")
        if speed in ["慢速", "slow"]:
            avoid_patterns.extend(["过快讲解", "跳跃式教学"])
        elif speed in ["快速", "fast"]:
            avoid_patterns.extend(["过慢讲解", "重复性内容"])

        # 默认避免模式
        default_avoid = ["过度批评", "纯理论讲解", "大段文字"]
        for pattern in default_avoid:
            if pattern not in avoid_patterns:
                avoid_patterns.append(pattern)

        return avoid_patterns

    def _extract_strengths(self) -> list:
        """提取学习优势"""
        strengths = []

        # 从learning_progress提取
        progress = self.profile_data.get("learning_progress", {})
        if isinstance(progress, str):
            try:
                progress = json.loads(progress) if progress else {}
            except json.JSONDecodeError:
                progress = {}

        # 知识水平对应的通用优势
        level = self._map_knowledge_level()
        if level == "intermediate":
            strengths.extend(["编程基础", "逻辑思维"])
        elif level == "advanced":
            strengths.extend(["编程基础", "逻辑思维", "系统设计", "问题解决"])

        return strengths

    def _extract_weaknesses(self) -> list:
        """提取学习薄弱点"""
        weak_points = []

        # 从learning_progress.weak_points提取
        progress = self.profile_data.get("learning_progress", {})
        if isinstance(progress, str):
            try:
                progress = json.loads(progress) if progress else {}
            except json.JSONDecodeError:
                progress = {}

        if isinstance(progress, dict):
            weak_points.extend(progress.get("weak_points", []))

        # 知识水平对应的通用薄弱点
        level = self._map_knowledge_level()
        if level == "beginner":
            weak_points.extend(["基础概念", "语法细节"])

        # 去重
        seen = set()
        unique_weak_points = []
        for wp in weak_points:
            if wp not in seen:
                seen.add(wp)
                unique_weak_points.append(wp)

        return unique_weak_points[:5]  # 最多返回5个

    def _infer_explanation_style(self) -> str:
        """基于学习风格推断解释风格"""
        style = self._map_learning_style()

        style_mapping = {
            "visual": "visual_with_examples",           # 视觉型：图表+示例
            "auditory": "verbal_with_discussion",       # 听觉型：讲解+讨论
            "reading": "text_based_with_notes",         # 阅读型：文字+笔记
            "kinesthetic": "hands_on_with_practice"    # 动觉型：实践+操作
        }

        return style_mapping.get(style, "visual_with_examples")

    def _infer_feedback_style(self) -> str:
        """基于知识水平推断反馈风格"""
        level = self._map_knowledge_level()

        style_mapping = {
            "beginner": "encouraging_gentle",           # 入门：鼓励为主
            "intermediate": "encouraging_specific",     # 中级：具体鼓励
            "advanced": "constructive_direct"           # 高级：建设性直接
        }

        return style_mapping.get(level, "encouraging_specific")

    def _get_default_profile(self) -> Dict[str, Any]:
        """获取默认画像（当用户画像不可用时）"""
        return {
            "learning_style": "visual",
            "knowledge_level": "beginner",
            "interests": ["大数据", "Python"],
            "communication_preferences": {
                "explanation_style": "visual_with_examples",
                "feedback_style": "encouraging_specific",
                "study_time": "晚上8点后",
                "content_types": ["图文", "短视频"]
            },
            "avoid_patterns": ["过度批评", "纯理论讲解", "大段文字"],
            "strengths": ["学习意愿强"],
            "weaknesses": ["需要更多实践"],
            "explanation_style": "visual_with_examples",
            "feedback_style": "encouraging_specific"
        }


def adapt_profile_for_workflow(profile_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：将6维画像适配为工作流格式

    Args:
        profile_data: 原始的6维用户画像

    Returns:
        工作流期望的画像结构
    """
    adapter = ProfileAdapter(profile_data)
    return adapter.get_profile_summary()


def get_profile_status_for_workflow(profile_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：获取画像状态

    Args:
        profile_data: 原始的用户画像

    Returns:
        画像状态信息
    """
    adapter = ProfileAdapter(profile_data)
    return adapter.get_profile_status()


def get_extended_profile(profile_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    获取扩展的用户画像（包含原始数据和工作流格式）

    Args:
        profile_data: 原始的6维用户画像

    Returns:
        包含原始数据和扩展信息的完整画像
    """
    adapter = ProfileAdapter(profile_data)

    # 获取画像摘要
    summary = adapter.get_profile_summary()

    # 获取画像状态
    status = adapter.get_profile_status()

    return {
        "profile": profile_data or {},
        "adapted_profile": summary,
        "status": status,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "adapter_version": "1.0"
        }
    }


def transform_to_workflow_format(profile_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    将用户画像转换为工作流期望的格式

    Args:
        profile_data: 原始的6维用户画像

    Returns:
        工作流期望的画像结构
    """
    return adapt_profile_for_workflow(profile_data)


def profile_to_star_chart(profile_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    将用户画像转换为星图可视化格式

    星图格式包含：
    - center: 中心节点（通常是"学习者"）
    - rays: 射线节点，每个节点包含 label、value、level/type

    Args:
        profile_data: 用户画像数据

    Returns:
        星图格式的画像数据
    """
    if not profile_data:
        return {
            "center": "学习者",
            "rays": [],
            "metadata": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat()
            }
        }

    # 基础结构
    center = profile_data.get("user_id", "学习者")
    rays = []

    # 1. 好奇心指数 (curiosity_index)
    curiosity = profile_data.get("curiosity_index", 50)
    rays.append({
        "label": "好奇心",
        "value": curiosity,
        "level": min(5, max(1, curiosity // 20)),
        "type": "numeric"
    })

    # 2. 知识水平 (knowledge_level)
    knowledge = profile_data.get("knowledge_level", "未知")
    knowledge_value = {
        "零基础": 20,
        "入门": 35,
        "初级": 50,
        "中级": 65,
        "高级": 80,
        "专家": 95
    }.get(str(knowledge), 50)
    rays.append({
        "label": "知识水平",
        "value": knowledge_value,
        "level": min(5, max(1, knowledge_value // 20)),
        "type": "text",
        "raw_value": str(knowledge)
    })

    # 3. 学习风格 (learning_style)
    style = profile_data.get("learning_style", "待分析")
    rays.append({
        "label": "学习风格",
        "value": str(style),
        "type": "text",
        "raw_value": str(style)
    })

    # 4. 学习速度 (learning_speed)
    speed = profile_data.get("learning_speed", "待分析")
    speed_value = {
        "较慢": 30,
        "中等": 50,
        "较快": 70,
        "快速": 90
    }.get(str(speed), 50)
    rays.append({
        "label": "学习速度",
        "value": speed_value,
        "level": min(5, max(1, speed_value // 20)),
        "type": "text",
        "raw_value": str(speed)
    })

    # 5. 兴趣领域 (interests)
    interests = profile_data.get("interests", [])
    if isinstance(interests, list):
        interest_value = ", ".join(interests[:5]) if interests else "待发现"
    else:
        interest_value = str(interests)
    rays.append({
        "label": "兴趣领域",
        "value": interest_value,
        "type": "array",
        "raw_value": interests if isinstance(interests, list) else [interests]
    })

    # 6. 学习进度 (learning_progress)
    progress = profile_data.get("learning_progress", {})
    if isinstance(progress, dict):
        completed = progress.get("completed_topics", [])
        progress_value = min(100, len(completed) * 10 + 10)
    else:
        progress_value = 10
    rays.append({
        "label": "学习进度",
        "value": progress_value,
        "level": min(5, max(1, progress_value // 20)),
        "type": "numeric",
        "unit": "%"
    })

    # 7. 参与度分数 (engagement_score)
    engagement = profile_data.get("engagement_score", 50)
    rays.append({
        "label": "参与度",
        "value": engagement,
        "level": min(5, max(1, engagement // 20)),
        "type": "numeric"
    })

    # 8. 近期提问数 (recent_questions)
    recent_q = profile_data.get("recent_questions", 0)
    rays.append({
        "label": "活跃度",
        "value": recent_q,
        "level": min(5, max(1, (recent_q // 5) + 1)) if recent_q > 0 else 1,
        "type": "numeric",
        "unit": "次"
    })

    return {
        "center": center,
        "rays": rays,
        "metadata": {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_dimensions": len(rays)
        }
    }


def enhance_message_with_profile(
    user_message: str,
    profile_data: Optional[Dict[str, Any]],
    include_context: bool = True
) -> str:
    """
    画像增强中间件：将用户消息与画像信息结合，生成增强的提示词

    Args:
        user_message: 用户原始输入消息
        profile_data: 用户画像数据（6维结构）
        include_context: 是否包含详细上下文

    Returns:
        增强后的用户消息

    Example:
        >>> profile = {"learning_style": "视觉型", "knowledge_level": "中级"}
        >>> enhanced = enhance_message_with_profile("讲解Spark", profile)
        >>> print(enhanced)
        【用户画像】
        - 学习风格：视觉型
        - 知识水平：中级
        - 解释风格：图表+示例

        用户问题：讲解Spark
    """
    # 获取画像适配器
    adapter = ProfileAdapter(profile_data)
    profile_summary = adapter.get_profile_summary()
    profile_status = adapter.get_profile_status()

    # 构建画像提示词
    profile_prompt = _build_profile_prompt(profile_summary, profile_status, include_context)

    # 组合增强消息
    enhanced_message = f"""{profile_prompt}

用户问题：{user_message}"""

    return enhanced_message


def _build_profile_prompt(
    profile_summary: Dict[str, Any],
    profile_status: Dict[str, Any],
    include_context: bool
) -> str:
    """
    构建画像提示词

    Args:
        profile_summary: 画像摘要
        profile_status: 画像状态
        include_context: 是否包含详细上下文

    Returns:
        格式化的画像提示词
    """
    # 检查是否使用降级策略
    if profile_status.get("fallback_used", True):
        return "【用户画像】无历史画像，使用通用配置"

    prompt_parts = ["【用户画像】"]

    # 基础维度
    if profile_summary.get("learning_style"):
        prompt_parts.append(f"- 学习风格：{profile_summary['learning_style']}")
    if profile_summary.get("knowledge_level"):
        prompt_parts.append(f"- 知识水平：{profile_summary['knowledge_level']}")

    # 兴趣领域
    interests = profile_summary.get("interests", [])
    if interests:
        interests_str = "、".join(interests) if isinstance(interests, list) else str(interests)
        prompt_parts.append(f"- 兴趣领域：{interests_str}")

    # 解释风格（详细上下文时包含）
    if include_context:
        if profile_summary.get("explanation_style"):
            prompt_parts.append(f"- 解释风格：{profile_summary['explanation_style']}")
        if profile_summary.get("feedback_style"):
            prompt_parts.append(f"- 反馈风格：{profile_summary['feedback_style']}")

    # 避免模式（详细上下文时包含）
    avoid_patterns = profile_summary.get("avoid_patterns", [])
    if include_context and avoid_patterns:
        avoid_str = "、".join(avoid_patterns) if isinstance(avoid_patterns, list) else str(avoid_patterns)
        prompt_parts.append(f"- 避免模式：{avoid_str}")

    # 优势（详细上下文时包含）
    strengths = profile_summary.get("strengths", [])
    if include_context and strengths:
        strengths_str = "、".join(strengths) if isinstance(strengths, list) else str(strengths)
        prompt_parts.append(f"- 学习优势：{strengths_str}")

    # 劣势（详细上下文时包含）
    weaknesses = profile_summary.get("weaknesses", [])
    if include_context and weaknesses:
        weaknesses_str = "、".join(weaknesses) if isinstance(weaknesses, list) else str(weaknesses)
        prompt_parts.append(f"- 薄弱环节：{weaknesses_str}")

    # 沟通偏好（详细上下文时包含）
    comm_prefs = profile_summary.get("communication_preferences", {})
    if include_context and comm_prefs:
        if comm_prefs.get("content_types"):
            content_types = comm_prefs["content_types"]
            types_str = "、".join(content_types) if isinstance(content_types, list) else str(content_types)
            prompt_parts.append(f"- 内容类型偏好：{types_str}")

    return "\n".join(prompt_parts)


def enhance_message_simple(user_message: str, profile_data: Optional[Dict[str, Any]]) -> str:
    """
    简化版画像增强：只包含核心维度（用于简短对话）

    Args:
        user_message: 用户原始输入消息
        profile_data: 用户画像数据

    Returns:
        增强后的用户消息
    """
    return enhance_message_with_profile(user_message, profile_data, include_context=False)
