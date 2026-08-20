"""
学习引擎模块
Learning Engines Module

包含三大核心引擎：
1. 学习饥饿感引擎 (HungerEngine) - 制造好奇、预测兴趣
2. 心流检测引擎 (FlowDetector) - 监控学习状态
3. 遗忘预测引擎 (ForgettingPredictor) - 主动触发复习
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class FlowState(Enum):
    """心流状态"""
    BORED = "bored"           # 无聊（太简单）
    ENGAGED = "engaged"       # 专注（适中）
    FRUSTRATED = "frustrated" # 挫败（太难）
    FLOW = "flow"             # 心流（最佳状态）
    DISTACTED = "distracted"  # 分心


class CuriositySignal(Enum):
    """好奇信号类型"""
    QUESTION = "question"           # 追问
    EXPLORATION = "exploration"     # 探索
    SURPRISE = "surprise"           # 惊讶
    INTEREST = "interest"           # 兴趣表达
    DEEP_DIVE = "deep_dive"         # 深入研究


@dataclass
class UserEngagementProfile:
    """用户参与画像"""
    user_id: str
    curiosity_score: float = 0.5      # 好奇指数 0-1
    patience_level: float = 0.5        # 耐心程度 0-1
    frustration_threshold: float = 0.7 # 挫败阈值
    boredom_threshold: float = 0.3    # 无聊阈值
    preferred_difficulty: float = 0.5  # 偏好难度 0-1
    
    # 统计
    total_sessions: int = 0
    avg_session_length: float = 0
    topics_explored: List[str] = field(default_factory=list)
    
    # 心流历史
    flow_states: List[FlowState] = field(default_factory=list)
    last_flow_time: Optional[datetime] = None
    
    def update_from_interaction(self, interaction: Dict):
        """根据交互更新画像"""
        if interaction.get("type") == "curiosity":
            self.curiosity_score = min(1.0, self.curiosity_score + 0.1)
        elif interaction.get("type") == "frustration":
            self.frustration_threshold = min(1.0, self.frustration_threshold + 0.05)
        elif interaction.get("type") == "success":
            self.curiosity_score = max(0.0, self.curiosity_score - 0.05)


@dataclass
class LearningMetrics:
    """学习指标"""
    timestamp: datetime
    topic_id: str
    engagement_score: float      # 参与度 0-1
    difficulty_appropriateness: float  # 难度合适度 0-1
    flow_state: FlowState
    completion_rate: float       # 完成率 0-1
    time_spent_minutes: float    # 花费时间（分钟）
    interaction_count: int       # 交互次数
    question_count: int          # 提问次数


class HungerEngine:
    """
    学习饥饿感引擎
    
    分析用户好奇信号，预测兴趣点，制造知识悬念
    """
    
    # 好奇信号关键词
    CURIOSITY_KEYWORDS = {
        CuriositySignal.QUESTION: ["为什么", "怎么", "如何", "什么", "?", "？", "原因"],
        CuriositySignal.EXPLORATION: ["试试", "探索", "看看", "了解", "看看还有"],
        CuriositySignal.SURPRISE: ["哇", "竟然", "居然", "没想到", "原来", "原来如此"],
        CuriositySignal.INTEREST: ["感兴趣", "想学", "想知道", "有意思", "好酷", "厉害"],
        CuriositySignal.DEEP_DIVE: ["深入", "详细", "具体", "原理", "底层", "本质"]
    }
    
    def __init__(self):
        self._user_profiles: Dict[str, UserEngagementProfile] = {}
    
    def get_profile(self, user_id: str) -> UserEngagementProfile:
        """获取用户参与画像"""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserEngagementProfile(user_id=user_id)
        return self._user_profiles[user_id]
    
    def detect_curiosity(self, user_input: str) -> Tuple[List[CuriositySignal], float]:
        """
        检测好奇信号
        
        Args:
            user_input: 用户输入
            
        Returns:
            (检测到的信号列表, 好奇强度 0-1)
        """
        signals = []
        total_weight = 0
        
        user_lower = user_input.lower()
        
        for signal_type, keywords in self.CURIOSITY_KEYWORDS.items():
            for kw in keywords:
                if kw in user_lower:
                    signals.append(signal_type)
                    total_weight += 1
                    break
        
        # 计算好奇强度
        intensity = min(1.0, total_weight / 3)  # 最多3个信号类型
        
        return signals, intensity
    
    def predict_interest_topics(
        self, 
        user_id: str, 
        conversation_history: List[Dict]
    ) -> List[str]:
        """
        预测用户可能感兴趣的主题
        
        Args:
            user_id: 用户ID
            conversation_history: 对话历史
            
        Returns:
            预测的兴趣主题ID列表
        """
        profile = self.get_profile(user_id)
        
        # 基于好奇心分数预测
        if profile.curiosity_score > 0.7:
            # 高好奇心用户，预测深入话题
            return ["原理", "底层", "深入", "源码"]
        elif profile.curiosity_score > 0.4:
            # 中等好奇心，预测扩展话题
            return ["应用", "实践", "案例"]
        else:
            # 低好奇心，预测基础巩固
            return ["复习", "练习", "巩固"]
    
    def create_anticipation(self, topic: str) -> str:
        """
        为主题创建悬念钩子
        
        Args:
            topic: 知识点名称
            
        Returns:
            悬念文本
        """
        hooks = [
            f"关于「{topic}」，有一个很多人都会踩的坑...",
            f"「{topic}」背后藏着一个有意思的设计思想，你想知道吗？",
            f"学完「{topic}」后，你会发现它和另一个知识点有神奇的联系...",
            f"「{topic}」的高阶用法，很多人都不知道...",
            f"理解了「{topic}」，很多问题就迎刃而解了..."
        ]
        import random
        return random.choice(hooks)
    
    def calculate_recommendation_score(
        self, 
        topic_difficulty: float,
        user_profile: UserEngagementProfile
    ) -> float:
        """
        计算推荐分数
        
        Args:
            topic_difficulty: 知识点难度 0-1
            user_profile: 用户画像
            
        Returns:
            推荐分数 0-1，越高越推荐
        """
        # 难度匹配度
        diff_match = 1 - abs(topic_difficulty - user_profile.preferred_difficulty)
        
        # 好奇驱动
        curiosity_boost = user_profile.curiosity_score * 0.3
        
        return (diff_match * 0.7 + curiosity_boost)


class FlowDetector:
    """
    心流检测引擎
    
    监控用户学习状态，检测是否进入心流或处于无聊/挫败状态
    """
    
    def __init__(self):
        self._metrics_history: Dict[str, List[LearningMetrics]] = defaultdict(list)
    
    def detect_state(
        self,
        user_id: str,
        current_metrics: LearningMetrics
    ) -> FlowState:
        """
        检测当前心流状态
        
        Args:
            user_id: 用户ID
            current_metrics: 当前学习指标
            
        Returns:
            心流状态
        """
        # 获取历史数据
        history = self._metrics_history[user_id]
        history.append(current_metrics)
        
        # 只保留最近10条记录
        if len(history) > 10:
            history = history[-10:]
        self._metrics_history[user_id] = history
        
        # 计算状态
        engagement = current_metrics.engagement_score
        difficulty_match = current_metrics.difficulty_appropriateness
        
        # 挫败检测
        if current_metrics.flow_state == FlowState.FRUSTRATED:
            return FlowState.FRUSTRATED
        
        # 无聊检测
        if difficulty_match < 0.3 and engagement < 0.4:
            return FlowState.BORED
        
        # 心流检测
        if (difficulty_match > 0.6 and 
            engagement > 0.7 and 
            current_metrics.completion_rate > 0.5):
            return FlowState.FLOW
        
        # 分心检测（交互减少但时间变长）
        if len(history) >= 3:
            recent_engagement = [m.engagement_score for m in history[-3:]]
            if all(recent_engagement[i] > recent_engagement[i+1] 
                   for i in range(len(recent_engagement)-1)):
                return FlowState.DISTACTED
        
        return FlowState.ENGAGED
    
    def get_state_adjustment(self, state: FlowState) -> Dict[str, Any]:
        """
        根据状态获取调整建议
        
        Returns:
            调整参数
        """
        adjustments = {
            FlowState.FLOW: {
                "action": "maintain",
                "difficulty_adjustment": 0.0,
                "encouragement": "你进入了最佳学习状态！继续保持！"
            },
            FlowState.ENGAGED: {
                "action": "slightly_increase",
                "difficulty_adjustment": 0.1,
                "encouragement": "做得不错！要不要挑战一下更难的？"
            },
            FlowState.BORED: {
                "action": "increase_difficulty",
                "difficulty_adjustment": 0.3,
                "encouragement": "这部分对你来说太简单了，来点有挑战的！"
            },
            FlowState.FRUSTRATED: {
                "action": "decrease_difficulty",
                "difficulty_adjustment": -0.3,
                "encouragement": "别着急，我们先从基础开始，一步一步来。"
            },
            FlowState.DISTACTED: {
                "action": "reengage",
                "difficulty_adjustment": -0.1,
                "encouragement": "有点走神？要不要换个方式学习？"
            }
        }
        return adjustments.get(state, adjustments[FlowState.ENGAGED])
    
    def get_flow_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户心流状态总结"""
        history = self._metrics_history.get(user_id, [])
        if not history:
            return {"total_sessions": 0, "flow_rate": 0.0}
        
        flow_count = sum(1 for m in history if m.flow_state == FlowState.FLOW)
        return {
            "total_sessions": len(history),
            "flow_count": flow_count,
            "flow_rate": flow_count / len(history),
            "avg_engagement": sum(m.engagement_score for m in history) / len(history),
            "avg_difficulty_match": sum(m.difficulty_appropriateness for m in history) / len(history)
        }


class ForgettingPredictor:
    """
    遗忘预测引擎
    
    基于艾宾浩斯遗忘曲线，预测何时需要复习
    """
    
    # 遗忘曲线参数（简化模型）
    TIME_POINTS_HOURS = [0.25, 1, 8, 24, 48, 168, 336]  # 15分钟到2周
    RETENTION_RATES = [0.58, 0.44, 0.36, 0.34, 0.28, 0.25, 0.21]
    
    def __init__(self):
        # 知识点记忆记录: {user_id: {topic_id: (last_review, mastery_level)}}
        self._memory_records: Dict[str, Dict[str, Tuple[datetime, float]]] = defaultdict(dict)
    
    def record_review(
        self, 
        user_id: str, 
        topic_id: str, 
        mastery_level: float
    ):
        """记录学习/复习"""
        self._memory_records[user_id][topic_id] = (datetime.now(), mastery_level)
    
    def predict_retention(
        self, 
        user_id: str, 
        topic_id: str
    ) -> Optional[float]:
        """
        预测当前记忆保留率
        
        Args:
            user_id: 用户ID
            topic_id: 知识点ID
            
        Returns:
            保留率 0-1，如果无记录返回None
        """
        if user_id not in self._memory_records:
            return None
        
        if topic_id not in self._memory_records[user_id]:
            return None
        
        last_review, initial_mastery = self._memory_records[user_id][topic_id]
        hours_passed = (datetime.now() - last_review).total_seconds() / 3600
        
        # 找到对应的时间点
        retention = initial_mastery
        for i, time_point in enumerate(self.TIME_POINTS_HOURS):
            if hours_passed <= time_point:
                retention = initial_mastery * self.RETENTION_RATES[max(0, i-1)] / self.RETENTION_RATES[0]
                break
        else:
            # 超过最长时间点
            retention = initial_mastery * self.RETENTION_RATES[-1] / self.RETENTION_RATES[0]
        
        return max(0.0, min(1.0, retention))
    
    def get_review_schedule(
        self, 
        user_id: str, 
        topic_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取复习时间表
        
        Returns:
            {
                "current_retention": 当前保留率,
                "next_review_time": 下次最佳复习时间,
                "priority": 优先级 high/medium/low
            }
        """
        retention = self.predict_retention(user_id, topic_id)
        if retention is None:
            return None
        
        if user_id not in self._memory_records or topic_id not in self._memory_records[user_id]:
            return None
        
        last_review, _ = self._memory_records[user_id][topic_id]
        
        # 计算下次复习时间（保留率降到50%以下时）
        next_review_hours = None
        for i, time_point in enumerate(self.TIME_POINTS_HOURS):
            if time_point > (datetime.now() - last_review).total_seconds() / 3600:
                if retention < 0.5:
                    next_review_hours = time_point
                    break
        
        if next_review_hours is None:
            next_review_hours = self.TIME_POINTS_HOURS[-1]
        
        next_review_time = last_review + timedelta(hours=next_review_hours)
        
        # 优先级
        if retention < 0.3:
            priority = "high"
        elif retention < 0.5:
            priority = "medium"
        else:
            priority = "low"
        
        return {
            "current_retention": round(retention, 2),
            "last_reviewed": last_review.isoformat(),
            "next_review_time": next_review_time.isoformat(),
            "hours_until_review": round((next_review_time - datetime.now()).total_seconds() / 3600, 1),
            "priority": priority
        }
    
    def get_all_review_topics(
        self, 
        user_id: str,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        获取所有需要复习的知识点
        
        Args:
            user_id: 用户ID
            threshold: 保留率阈值，低于此值需要复习
            
        Returns:
            需要复习的知识点列表
        """
        if user_id not in self._memory_records:
            return []
        
        review_topics = []
        for topic_id in self._memory_records[user_id]:
            retention = self.predict_retention(user_id, topic_id)
            if retention is not None and retention < threshold:
                schedule = self.get_review_schedule(user_id, topic_id)
                if schedule:
                    review_topics.append({
                        "topic_id": topic_id,
                        "current_retention": retention,
                        **schedule
                    })
        
        # 按优先级和保留率排序
        review_topics.sort(key=lambda x: (
            0 if x["priority"] == "high" else 1 if x["priority"] == "medium" else 2,
            x["current_retention"]
        ))
        
        return review_topics


# 全局实例
_hunger_engine: Optional[HungerEngine] = None
_flow_detector: Optional[FlowDetector] = None
_forgetting_predictor: Optional[ForgettingPredictor] = None


def get_hunger_engine() -> HungerEngine:
    global _hunger_engine
    if _hunger_engine is None:
        _hunger_engine = HungerEngine()
    return _hunger_engine


def get_flow_detector() -> FlowDetector:
    global _flow_detector
    if _flow_detector is None:
        _flow_detector = FlowDetector()
    return _flow_detector


def get_forgetting_predictor() -> ForgettingPredictor:
    global _forgetting_predictor
    if _forgetting_predictor is None:
        _forgetting_predictor = ForgettingPredictor()
    return _forgetting_predictor
