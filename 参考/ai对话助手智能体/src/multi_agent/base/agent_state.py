"""
Multi-Agent State Definitions
多智能体系统状态定义
"""

from typing import TypedDict, Annotated, Optional, Any, Dict, List
from datetime import datetime
from enum import Enum
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingMode(str, Enum):
    """处理模式枚举"""
    FEDERATED = "federated"      # 联邦式 - 独立并行
    COLLABORATIVE = "collaborative"  # 协作式 - 依赖处理


class IntentType(str, Enum):
    """意图类型枚举"""
    CONVERSATION = "conversation"      # 对话学习
    DOCUMENT = "document"              # 文档生成
    QUESTION = "question"               # 题库练习
    MULTIMEDIA = "multimedia"           # 多媒体生成（文生图、文生视频）
    MULTIMODAL = "multimodal"           # ✅ 多模态理解（理解用户上传的图片/视频/音频）
    QA = "qa"                          # 答疑解惑
    LEARNING_PATH = "learning_path"     # 学习路径
    EVALUATION = "evaluation"           # 学习评估
    RECOMMENDATION = "recommendation"   # 个性化推荐
    EMAIL = "email"                    # 邮件发送
    AUDIO = "audio"                    # 语音处理（TTS/ASR）
    RAG_QUESTION = "rag_question"       # RAG题库检索
    UNKNOWN = "unknown"                 # 未知


class TaskInfo(TypedDict):
    """任务信息"""
    task_id: str
    task_type: IntentType
    description: str
    status: TaskStatus
    assigned_agent: Optional[str]
    result: Optional[Any]
    created_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


class UserProfile(TypedDict):
    """用户画像"""
    user_id: str
    learning_style: str  # visual, auditory, reading, kinesthetic
    knowledge_level: str  # beginner, elementary, intermediate, advanced
    learning_goal: str
    learning_speed: str  # slow, medium, fast
    learning_preference: Dict[str, Any]
    weak_points: List[str]
    strong_points: List[str]
    updated_at: datetime


class LearningProgress(TypedDict):
    """学习进度"""
    user_id: str
    subject: str
    overall_progress: float  # 0.0 - 1.0
    topic_progress: Dict[str, Dict[str, Any]]
    total_study_time: int  # 分钟
    exercise_count: int
    assessment_history: List[Dict[str, Any]]
    updated_at: datetime


class AgentMessageInfo(TypedDict):
    """Agent消息信息"""
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime


def _reduce_messages(old: list, new: list) -> list:
    """消息 reducer - 滑动窗口保留最近100条"""
    combined = old + new
    return combined[-100:] if len(combined) > 100 else combined


def _reduce_tasks(old: dict, new: dict) -> dict:
    """任务 reducer - 合并任务状态"""
    result = dict(old)
    result.update(new)
    return result


def _reduce_profiles(old: dict, new: dict) -> dict:
    """用户画像 reducer - 合并用户画像"""
    result = dict(old)
    result.update(new)
    return result


class MultiAgentState(TypedDict):
    """
    多智能体系统状态
    
    包含:
    - messages: 对话消息历史
    - current_intent: 当前识别的意图
    - tasks: 任务列表
    - user_profile: 用户画像
    - learning_progress: 学习进度
    - shared_context: 共享上下文
    - agent_messages: Agent间消息
    - results: 处理结果
    """
    # 对话消息历史
    messages: Annotated[list[AnyMessage], add_messages]
    
    # 当前状态
    current_intent: Annotated[IntentType, lambda old, new: new if new else old]
    
    # 任务管理
    tasks: Annotated[dict[str, TaskInfo], _reduce_tasks]
    
    # 用户画像
    user_profile: Annotated[Optional[UserProfile], lambda old, new: new or old]
    
    # 学习进度
    learning_progress: Annotated[Optional[LearningProgress], lambda old, new: new or old]
    
    # 共享上下文
    shared_context: Annotated[dict[str, Any], _reduce_tasks]
    
    # Agent间消息
    agent_messages: Annotated[list[AgentMessageInfo], _reduce_messages]
    
    # 处理结果
    results: Annotated[dict[str, Any], _reduce_tasks]

    # ✅ 新增：多模态数据（用户上传的图片/视频/音频/文件）
    multimodal_data: Annotated[Optional[Dict[str, Any]], lambda old, new: new or old]

    # 元信息
    user_id: str
    session_id: str


class TaskDecomposition(TypedDict):
    """任务分解结果"""
    tasks: List[TaskInfo]
    parallel_groups: List[List[str]]  # 可并行执行的任务组
    sequential_chains: List[List[str]]  # 需顺序执行的任务链
