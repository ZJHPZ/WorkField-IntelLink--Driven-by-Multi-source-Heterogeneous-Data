"""
学习引擎协调Agent
LearningEngineAgent

协调三大引擎（饥饿感+心流+遗忘预测）的工作
实现：制造好奇 → 维持心流 → 适时复习 → 强化记忆 → 激发新好奇 的闭环
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from multi_agent.base.base_agent import BaseAgent
from multi_agent.base.agent_state import MultiAgentState, IntentType
from multi_agent.base.message import AgentMessage, MessageType
from multi_agent.knowledge.learning_engines import (
    get_hunger_engine,
    get_flow_detector,
    get_forgetting_predictor,
    HungerEngine,
    FlowDetector,
    ForgettingPredictor,
    FlowState,
    LearningMetrics,
    CuriositySignal
)


class LearningEngineAgent(BaseAgent):
    """
    学习引擎协调Agent
    
    负责：
    1. 饥饿感引擎：检测用户好奇信号，制造悬念
    2. 心流检测：监控学习状态，动态调整难度
    3. 遗忘预测：管理复习计划，主动触发复习
    
    协作模式：
    - 接收来自其他Agent的学习事件
    - 分析用户状态并生成优化建议
    - 触发相应的学习干预
    """
    
    def __init__(self):
        super().__init__(
            agent_id="learning_engine",
            name="学习引擎协调Agent",
            description="协调饥饿感、心流检测、遗忘预测三大引擎"
        )
        
        self.hunger_engine = get_hunger_engine()
        self.flow_detector = get_flow_detector()
        self.forgetting_predictor = get_forgetting_predictor()
        
        # 心流状态
        self._current_flow_state: Dict[str, FlowState] = {}
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.LEARNING_PATH  # 使用学习路径意图类型
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理学习引擎请求
        
        输入：
        - state.messages[-1].content: 用户消息
        - state.context.get("event"): 学习事件类型
        
        支持的事件类型：
        - "learning_interaction": 用户学习交互
        - "check_flow": 检查心流状态
        - "check_review": 检查复习需求
        - "detect_curiosity": 检测好奇信号
        - "get_recommendation": 获取推荐（综合三大引擎）
        """
        # MultiAgentState 是 TypedDict，支持 dict 访问方式
        user_id = state.get('user_id', 'anonymous')
        messages = state.get('messages', [])
        context = state.get('context', {})
        
        user_input = messages[-1].content if messages else ""
        event = context.get("event")
        
        # 根据事件类型处理
        if event == "check_flow":
            return await self._check_flow_state(state)
        elif event == "check_review":
            return await self._check_review_needs(state)
        elif event == "detect_curiosity":
            return await self._detect_curiosity(state)
        elif event == "learning_interaction":
            return await self._process_learning_interaction(state)
        else:
            # 综合分析
            return await self._comprehensive_analysis(state)
    
    async def _comprehensive_analysis(self, state: MultiAgentState) -> Dict[str, Any]:
        """综合分析用户学习状态"""
        user_id = state.get('user_id', 'anonymous')
        messages = state.get('messages', [])
        user_input = messages[-1].content if messages else ""
        
        # 1. 好奇信号检测
        signals, intensity = self.hunger_engine.detect_curiosity(user_input)
        
        # 2. 心流状态检测
        current_flow = self._current_flow_state.get(user_id, FlowState.ENGAGED)
        flow_adjustment = self.flow_detector.get_state_adjustment(current_flow)
        
        # 3. 检查遗忘预测
        review_topics = self.forgetting_predictor.get_all_review_topics(user_id)
        urgent_reviews = [t for t in review_topics if t["priority"] == "high"]
        
        # 构建综合分析结果
        result = {
            "success": True,
            "analysis": {
                "curiosity": {
                    "detected": len(signals) > 0,
                    "signals": [s.value for s in signals],
                    "intensity": intensity,
                    "profile": {
                        "curiosity_score": self.hunger_engine.get_profile(user_id).curiosity_score
                    }
                },
                "flow": {
                    "current_state": current_flow.value,
                    "adjustment": flow_adjustment
                },
                "forgetting": {
                    "topics_to_review": len(review_topics),
                    "urgent_count": len(urgent_reviews),
                    "urgent_topics": urgent_reviews[:3] if urgent_reviews else []
                }
            },
            "suggestions": self._generate_suggestions(
                signals, current_flow, urgent_reviews
            ),
            "message": self._generate_response_message(
                signals, current_flow, urgent_reviews, user_id
            )
        }
        
        return result
    
    async def _detect_curiosity(self, state: MultiAgentState) -> Dict[str, Any]:
        """检测好奇信号"""
        user_id = state.get('user_id', 'anonymous')
        messages = state.get('messages', [])
        user_input = messages[-1].content if messages else ""
        
        signals, intensity = self.hunger_engine.detect_curiosity(user_input)
        profile = self.hunger_engine.get_profile(user_id)
        
        # 如果检测到好奇，更新画像
        if intensity > 0:
            profile.update_from_interaction({"type": "curiosity"})
        
        # 生成悬念
        interest_topics = self.hunger_engine.predict_interest_topics(
            user_id, [m.content if hasattr(m, 'content') else str(m) for m in messages]
        )
        
        anticipation = None
        if intensity > 0.3:
            anticipation = self.hunger_engine.create_anticipation(
                interest_topics[0] if interest_topics else "这个知识点"
            )
        
        return {
            "success": True,
            "curiosity_detected": len(signals) > 0,
            "signals": [s.value for s in signals],
            "intensity": intensity,
            "curiosity_score": profile.curiosity_score,
            "anticipation": anticipation,
            "recommended_topics": interest_topics,
            "message": self._generate_curiosity_message(signals, intensity)
        }
    
    async def _check_flow_state(self, state: MultiAgentState) -> Dict[str, Any]:
        """检查心流状态"""
        user_id = state.get('user_id', 'anonymous')
        
        current_flow = self._current_flow_state.get(user_id, FlowState.ENGAGED)
        flow_summary = self.flow_detector.get_flow_summary(user_id)
        adjustment = self.flow_detector.get_state_adjustment(current_flow)
        
        return {
            "success": True,
            "current_state": current_flow.value,
            "flow_summary": flow_summary,
            "adjustment": adjustment,
            "encouragement": adjustment.get("encouragement", ""),
            "message": self._generate_flow_message(current_flow, adjustment)
        }
    
    async def _check_review_needs(self, state: MultiAgentState) -> Dict[str, Any]:
        """检查复习需求"""
        user_id = state.get('user_id', 'anonymous')
        
        review_topics = self.forgetting_predictor.get_all_review_topics(user_id)
        
        if not review_topics:
            return {
                "success": True,
                "has_reviews": False,
                "message": "🎉 你的知识掌握得很扎实，暂无需要复习的内容！"
            }
        
        # 分类
        high_priority = [t for t in review_topics if t["priority"] == "high"]
        medium_priority = [t for t in review_topics if t["priority"] == "medium"]
        
        return {
            "success": True,
            "has_reviews": True,
            "total_count": len(review_topics),
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "next_review": review_topics[0] if review_topics else None,
            "message": self._generate_review_message(review_topics),
            "suggestion": self._generate_review_suggestion(review_topics)
        }
    
    async def _process_learning_interaction(self, state: MultiAgentState) -> Dict[str, Any]:
        """处理学习交互事件"""
        user_id = state.get('user_id', 'anonymous')
        
        # 从context获取交互数据
        context = state.get('context', {}) or {}
        topic_id = context.get("topic_id", "unknown")
        mastery_level = context.get("mastery_level", 0.5)
        engagement_score = context.get("engagement_score", 0.5)
        difficulty_match = context.get("difficulty_match", 0.5)
        
        # 1. 记录遗忘曲线
        self.forgetting_predictor.record_review(user_id, topic_id, mastery_level)
        
        # 2. 检测心流状态
        metrics = LearningMetrics(
            timestamp=datetime.now(),
            topic_id=topic_id,
            engagement_score=engagement_score,
            difficulty_appropriateness=difficulty_match,
            flow_state=self._current_flow_state.get(user_id, FlowState.ENGAGED),
            completion_rate=context.get("completion_rate", 0.5),
            time_spent_minutes=context.get("time_spent", 5),
            interaction_count=context.get("interaction_count", 1),
            question_count=context.get("question_count", 0)
        )
        
        new_state = self.flow_detector.detect_state(user_id, metrics)
        self._current_flow_state[user_id] = new_state
        
        # 3. 获取调整建议
        adjustment = self.flow_detector.get_state_adjustment(new_state)
        
        # 4. 检查复习需求
        review_schedule = self.forgetting_predictor.get_review_schedule(user_id, topic_id)
        
        return {
            "success": True,
            "topic_id": topic_id,
            "flow_state": new_state.value,
            "adjustment": adjustment,
            "review_schedule": review_schedule,
            "message": self._generate_interaction_message(
                topic_id, new_state, adjustment, review_schedule
            )
        }
    
    def _generate_suggestions(
        self,
        curiosity_signals: List[CuriositySignal],
        flow_state: FlowState,
        urgent_reviews: List[Dict]
    ) -> List[str]:
        """生成建议列表"""
        suggestions = []
        
        # 好奇建议
        if curiosity_signals:
            suggestions.append("继续保持你的好奇心！")
        
        # 心流建议
        if flow_state == FlowState.BORED:
            suggestions.append("增加学习难度，挑战更有趣的内容")
        elif flow_state == FlowState.FRUSTRATED:
            suggestions.append("适当降低难度，打好基础")
        elif flow_state == FlowState.FLOW:
            suggestions.append("你已经进入最佳状态！")
        
        # 复习建议
        if urgent_reviews:
            suggestions.append(f"有 {len(urgent_reviews)} 个知识点需要及时复习")
        
        return suggestions
    
    def _generate_response_message(
        self,
        curiosity_signals: List[CuriositySignal],
        flow_state: FlowState,
        urgent_reviews: List[Dict],
        user_id: str
    ) -> str:
        """生成综合响应消息"""
        parts = []
        
        # 心流部分
        flow_adjustment = self.flow_detector.get_state_adjustment(flow_state)
        if flow_state == FlowState.FLOW:
            parts.append("🌊 你正在最佳学习状态！继续保持这种节奏。")
        elif flow_state == FlowState.ENGAGED:
            parts.append("📚 你的学习状态不错。")
        elif flow_state == FlowState.BORED:
            parts.append("😴 感觉有点无聊？来点更有挑战的吧！")
        elif flow_state == FlowState.FRUSTRATED:
            parts.append("💪 别着急，我们慢一点。")
        
        # 好奇部分
        if curiosity_signals:
            profile = self.hunger_engine.get_profile(user_id)
            if profile.curiosity_score > 0.7:
                parts.append("✨ 你的好奇心很强！这种探索精神很棒。")
        
        # 复习部分
        if urgent_reviews:
            parts.append(f"📝 有 {len(urgent_reviews)} 个知识点该复习了，我来帮你安排。")
        
        return " ".join(parts) if parts else "让我分析一下你的学习状态..."
    
    def _generate_curiosity_message(
        self, 
        signals: List[CuriositySignal], 
        intensity: float
    ) -> str:
        """生成好奇响应消息"""
        if not signals:
            return "我感受到你正在认真思考..."
        
        signal_names = {
            CuriositySignal.QUESTION: "深入提问",
            CuriositySignal.EXPLORATION: "积极探索",
            CuriositySignal.SURPRISE: "发现惊喜",
            CuriositySignal.INTEREST: "浓厚兴趣",
            CuriositySignal.DEEP_DIVE: "追求深度"
        }
        
        detected = [signal_names.get(s, s.value) for s in signals]
        return f"🔍 我检测到你展现了：{', '.join(detected)}。这种好奇心会让学习效果加倍！"
    
    def _generate_flow_message(self, state: FlowState, adjustment: Dict) -> str:
        """生成心流响应消息"""
        return adjustment.get("encouragement", "继续学习...")
    
    def _generate_review_message(self, review_topics: List[Dict]) -> str:
        """生成复习响应消息"""
        high_count = sum(1 for t in review_topics if t["priority"] == "high")
        
        if high_count > 0:
            return f"⚠️ 你有 {high_count} 个知识点接近遗忘临界点，建议立即复习。"
        else:
            return f"📚 你有 {len(review_topics)} 个知识点可以巩固一下。"
    
    def _generate_review_suggestion(self, review_topics: List[Dict]) -> str:
        """生成复习建议"""
        if not review_topics:
            return ""
        
        next_topic = review_topics[0]
        return f"建议从「{next_topic['topic_id']}」开始复习，当前保留率仅 {next_topic['current_retention']*100:.0f}%"
    
    def _generate_interaction_message(
        self,
        topic_id: str,
        flow_state: FlowState,
        adjustment: Dict,
        review_schedule: Optional[Dict]
    ) -> str:
        """生成交互响应消息"""
        parts = [f"已记录你对「{topic_id}」的学习。"]
        
        if flow_state == FlowState.FLOW:
            parts.append("🌟 你进入了心流状态！")
        elif flow_state == FlowState.FRUSTRATED:
            parts.append(adjustment.get("encouragement", ""))
        
        if review_schedule and review_schedule["priority"] in ["high", "medium"]:
            parts.append(f"\n📅 {review_schedule['hours_until_review']}小时后需要复习这个知识点。")
        
        return " ".join(parts)
    
    def _extract_topic_from_message(self, message: str) -> Optional[str]:
        """从消息中提取知识点名称"""
        # 简化实现
        topics = ["HDFS", "MapReduce", "Spark", "Hive", "Kafka", "Flink", 
                  "Hadoop", "数据仓库", "机器学习", "大数据"]
        
        for topic in topics:
            if topic in message:
                return topic
        
        return None


# 全局实例
_learning_engine_agent: Optional[LearningEngineAgent] = None


def get_learning_engine_agent() -> LearningEngineAgent:
    global _learning_engine_agent
    if _learning_engine_agent is None:
        _learning_engine_agent = LearningEngineAgent()
    return _learning_engine_agent
