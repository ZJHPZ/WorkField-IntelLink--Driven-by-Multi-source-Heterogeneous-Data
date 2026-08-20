"""
大数据学习Agent
BigData Learning Agent

基于大数据知识图谱，提供：
1. 学习路径规划
2. 知识点诊断
3. 遗忘曲线预测
4. 学习进度追踪
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType
from ..base.message import AgentMessage, MessageType
from ..knowledge.bigdata_knowledge_graph import (
    BigDataKnowledgeGraph, 
    KnowledgeNode, 
    DifficultyLevel,
    KnowledgeCategory,
    get_knowledge_graph
)

logger = logging.getLogger(__name__)


@dataclass
class LearningRecord:
    """学习记录"""
    topic_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    mastery_level: float = 0.0  # 0.0-1.0 掌握程度
    review_count: int = 0       # 复习次数
    last_review: Optional[datetime] = None
    wrong_attempts: List[Dict] = field(default_factory=list)  # 错误尝试记录


@dataclass
class ForgettingCurve:
    """遗忘曲线模型（基于艾宾浩斯遗忘曲线）"""
    # 遗忘时间点（小时）
    TIME_POINTS = [0.25, 1, 8, 24, 48, 168, 336]  # 15分钟、1小时、8小时、1天、2天、1周、2周
    # 对应记忆保留率（简化模型）
    RETENTION_RATES = [0.58, 0.44, 0.36, 0.34, 0.28, 0.25, 0.21]


class BigDataLearningAgent(BaseAgent):
    """
    大数据学习Agent
    
    核心能力：
    1. 基于知识图谱的学习路径规划
    2. 智能知识点诊断
    3. 遗忘曲线预测复习时间
    4. 学习进度追踪
    """
    
    def __init__(self):
        super().__init__(
            agent_id="bigdata_learning",
            name="大数据学习Agent",
            description="基于知识图谱的大数据学习路径规划和诊断"
        )
        
        self.processing_mode = "collaborative"
        
        # 初始化知识图谱
        self.knowledge_graph = get_knowledge_graph()
        
        # 用户学习记录存储（内存）
        self._learning_records: Dict[str, Dict[str, LearningRecord]] = defaultdict(dict)
        
        # 遗忘曲线模型
        self._forgetting_model = ForgettingCurve()
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.LEARNING_PATH
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理学习请求
        """
        user_id = state.get("user_id", "default_user")
        messages = state.get("messages", [])
        user_input = self._get_latest_input(messages)
        
        self.log_info(f"Processing bigdata learning request: {user_input}")
        
        # 分析用户意图
        intent_analysis = self._analyze_intent(user_input)
        
        if intent_analysis["type"] == "path_planning":
            return await self._plan_learning_path(user_id, user_input, intent_analysis)
        elif intent_analysis["type"] == "diagnosis":
            return await self._diagnose_knowledge_gaps(user_id, intent_analysis)
        elif intent_analysis["type"] == "review":
            return await self._generate_review_plan(user_id)
        elif intent_analysis["type"] == "progress":
            return self._get_learning_progress(user_id)
        else:
            return await self._answer_question(user_input)
    
    def _analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """分析用户学习意图"""
        user_input_lower = user_input.lower()
        
        # 诊断意图关键词
        diagnosis_keywords = ["诊断", "哪里不会", "薄弱", "不会", "卡住", "不懂"]
        if any(kw in user_input_lower for kw in diagnosis_keywords):
            return {
                "type": "diagnosis",
                "level": self._detect_level(user_input)
            }
        
        # 复习意图关键词
        review_keywords = ["复习", "回顾", "忘记", "巩固", "还记得"]
        if any(kw in user_input_lower for kw in review_keywords):
            return {"type": "review"}
        
        # 进度查询关键词
        progress_keywords = ["进度", "学到哪", "完成了多少", "学了什么"]
        if any(kw in user_input_lower for kw in progress_keywords):
            return {"type": "progress"}
        
        # 学习路径规划关键词
        path_keywords = ["学习", "计划", "路径", "怎么学", "入门", "开始", "课程"]
        if any(kw in user_input_lower for kw in path_keywords):
            return {
                "type": "path_planning",
                "level": self._detect_level(user_input)
            }
        
        # 默认按问题回答
        return {"type": "question"}
    
    def _detect_level(self, user_input: str) -> DifficultyLevel:
        """检测用户学习水平"""
        user_input_lower = user_input.lower()
        
        if any(kw in user_input_lower for kw in ["入门", "零基础", "小白", "初学", "开始"]):
            return DifficultyLevel.入门
        elif any(kw in user_input_lower for kw in ["高级", "深入", "精通", "专家"]):
            return DifficultyLevel.高级
        elif any(kw in user_input_lower for kw in ["进阶", "深入", "提升"]):
            return DifficultyLevel.进阶
        else:
            return DifficultyLevel.基础  # 默认基础级
    
    async def _plan_learning_path(
        self, 
        user_id: str, 
        user_input: str,
        intent_analysis: Dict
    ) -> Dict[str, Any]:
        """规划学习路径"""
        level = intent_analysis.get("level", DifficultyLevel.入门)
        
        # 获取学习路径
        path = self.knowledge_graph.get_learning_path(
            start_level=DifficultyLevel.入门,
            target_level=level
        )
        
        # 过滤用户已学过的
        user_records = self._learning_records.get(user_id, {})
        unlearned_path = [
            node for node in path 
            if node.id not in user_records
        ]
        
        # 生成学习计划
        plan_sections = []
        current_category = None
        section = None
        
        for node in unlearned_path:
            if node.category != current_category:
                if section:
                    plan_sections.append(section)
                current_category = node.category
                section = {
                    "category": node.category.value,
                    "topics": [],
                    "total_hours": 0
                }
            if section:
                section["topics"].append({
                    "id": node.id,
                    "name": node.name,
                    "description": node.description[:50] + "...",
                    "hours": node.estimated_hours,
                    "difficulty": node.difficulty.name,
                    "prerequisites": node.prerequisites
                })
                section["total_hours"] += node.estimated_hours
        
        if section:
            plan_sections.append(section)
        
        # 存储学习计划
        self._store_learning_plan(user_id, unlearned_path)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "intent": "learning_path",
            "level": level.name,
            "total_topics": len(unlearned_path),
            "total_hours": sum(n.estimated_hours for n in unlearned_path),
            "learning_plan": plan_sections,
            "first_topic": unlearned_path[0].to_dict() if unlearned_path else None,
            "message": f"为你规划了 {len(unlearned_path)} 个学习模块，预计 {sum(n.estimated_hours for n in unlearned_path):.1f} 小时完成"
        }
    
    async def _diagnose_knowledge_gaps(
        self, 
        user_id: str,
        intent_analysis: Dict
    ) -> Dict[str, Any]:
        """诊断知识缺口"""
        # 获取用户已掌握的知识点
        user_records = self._learning_records.get(user_id, {})
        mastered_topics = [
            rid for rid, record in user_records.items() 
            if record.mastery_level >= 0.7
        ]
        
        # 执行诊断
        diagnosis = self.knowledge_graph.diagnose_gaps(mastered_topics)
        
        # 格式化输出
        missing_prereqs = [
            {
                "id": n.id,
                "name": n.name,
                "difficulty": n.difficulty.name,
                "description": n.description[:80]
            }
            for n in diagnosis["missing_prerequisites"]
        ]
        
        recommended = [
            {
                "id": n.id,
                "name": n.name,
                "difficulty": n.difficulty.name,
                "estimated_hours": n.estimated_hours
            }
            for n in diagnosis["recommended_next"]
        ]
        
        return {
            "success": True,
            "agent": self.agent_id,
            "intent": "diagnosis",
            "mastery_summary": {
                "known": diagnosis["total_known"],
                "total": diagnosis["total_knowledge"],
                "mastery_rate": f"{diagnosis['total_known']/max(diagnosis['total_known'], diagnosis['total_knowledge'])*100:.1f}%"
            },
            "missing_prerequisites": missing_prereqs[:5],
            "recommended_next": recommended,
            "message": f"你的知识体系已完成 {diagnosis['total_known']}/{diagnosis['total_knowledge']}，"
                      f"建议从「{recommended[0]['name'] if recommended else '基础概念'}」开始补充"
        }
    
    async def _generate_review_plan(self, user_id: str) -> Dict[str, Any]:
        """生成复习计划"""
        user_records = self._learning_records.get(user_id, {})
        review_topics = []
        
        now = datetime.now()
        
        for topic_id, record in user_records.items():
            # 计算遗忘程度
            if record.last_review:
                hours_since = (now - record.last_review).total_seconds() / 3600
                retention = self._forgetting_model.predict_retention(
                    record.mastery_level,
                    hours_since
                )
                
                if retention < 0.5:  # 遗忘超过50%需要复习
                    topic = self.knowledge_graph.get_node(topic_id)
                    if topic:
                        review_topics.append({
                            "id": topic_id,
                            "name": topic.name,
                            "retention": f"{retention*100:.0f}%",
                            "priority": "high" if retention < 0.3 else "medium",
                            "last_reviewed": record.last_review.strftime("%Y-%m-%d %H:%M"),
                            "review_count": record.review_count
                        })
        
        # 按优先级排序
        review_topics.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "intent": "review_plan",
            "topics_to_review": len(review_topics),
            "high_priority": len([t for t in review_topics if t["priority"] == "high"]),
            "review_topics": review_topics[:10],
            "message": f"根据遗忘曲线，你有 {len(review_topics)} 个知识点需要复习，"
                      f"其中 {len([t for t in review_topics if t['priority'] == 'high'])} 个是高优先级"
        }
    
    def _get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """获取学习进度"""
        user_records = self._learning_records.get(user_id, {})
        
        # 分类统计
        by_category = defaultdict(list)
        for topic_id, record in user_records.items():
            node = self.knowledge_graph.get_node(topic_id)
            if node:
                by_category[node.category.value].append({
                    "id": topic_id,
                    "name": node.name,
                    "mastery": f"{record.mastery_level*100:.0f}%",
                    "status": "completed" if record.mastery_level >= 0.9 else 
                             "in_progress" if record.mastery_level >= 0.3 else "started"
                })
        
        # 总体统计
        total_mastered = sum(1 for r in user_records.values() if r.mastery_level >= 0.9)
        total_learning = sum(1 for r in user_records.values() if 0.3 <= r.mastery_level < 0.9)
        total_started = sum(1 for r in user_records.values() if r.mastery_level < 0.3)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "intent": "progress",
            "overview": {
                "total_learned": len(user_records),
                "mastered": total_mastered,
                "in_progress": total_learning,
                "just_started": total_started,
                "completion_rate": f"{len(user_records)/len(self.knowledge_graph.nodes)*100:.1f}%"
            },
            "by_category": dict(by_category),
            "message": f"你已经学习了 {len(user_records)} 个大数据知识点，"
                      f"其中 {total_mastered} 个已完全掌握"
        }
    
    async def _answer_question(self, user_input: str) -> Dict[str, Any]:
        """回答关于大数据的问题"""
        # 搜索相关知识点
        results = self.knowledge_graph.search_by_keyword(user_input)
        
        if results:
            topic = results[0]
            # 获取依赖树
            dependency_tree = self.knowledge_graph.get_dependency_tree(topic.id)
            
            return {
                "success": True,
                "agent": self.agent_id,
                "intent": "explanation",
                "topic": topic.to_dict(),
                "dependency_tree": dependency_tree,
                "message": f"关于「{topic.name}」：\n\n{topic.description}"
            }
        
        return {
            "success": True,
            "agent": self.agent_id,
            "intent": "general_response",
            "message": "我对这个问题还不够了解。让我为你规划一个学习路径来系统掌握这个知识点。"
        }
    
    def _get_latest_input(self, messages: List[Any]) -> str:
        """获取最新用户输入"""
        for msg in reversed(messages):
            content = None
            if isinstance(msg, dict):
                content = msg.get("content", "")
            elif hasattr(msg, "content"):
                content = msg.content
            
            if content and isinstance(content, str):
                return content
        return ""
    
    def _store_learning_plan(self, user_id: str, path: List[KnowledgeNode]):
        """存储学习计划到记录"""
        if user_id not in self._learning_records:
            self._learning_records[user_id] = {}
        
        for node in path:
            if node.id not in self._learning_records[user_id]:
                self._learning_records[user_id][node.id] = LearningRecord(
                    topic_id=node.id,
                    user_id=user_id,
                    start_time=datetime.now(),
                    mastery_level=0.0
                )
    
    def update_mastery(
        self, 
        user_id: str, 
        topic_id: str, 
        mastery_level: float,
        wrong_attempts: Optional[List[Dict]] = None
    ):
        """更新知识点掌握程度"""
        if user_id not in self._learning_records:
            self._learning_records[user_id] = {}
        
        if topic_id in self._learning_records[user_id]:
            record = self._learning_records[user_id][topic_id]
            record.mastery_level = mastery_level
            record.last_review = datetime.now()
            if wrong_attempts:
                record.wrong_attempts.extend(wrong_attempts)
        else:
            node = self.knowledge_graph.get_node(topic_id)
            self._learning_records[user_id][topic_id] = LearningRecord(
                topic_id=topic_id,
                user_id=user_id,
                start_time=datetime.now(),
                mastery_level=mastery_level,
                last_review=datetime.now()
            )


def get_bigdata_learning_agent() -> BigDataLearningAgent:
    """获取大数据学习Agent单例"""
    return BigDataLearningAgent()


# 扩展遗忘曲线模型
ForgettingCurve.predict_retention = lambda self, initial_mastery, hours_since: (
    initial_mastery * self.RETENTION_RATES[
        min(len(self.TIME_POINTS) - 1, 
            next((i for i, t in enumerate(self.TIME_POINTS) if hours_since <= t), 
                 len(self.TIME_POINTS) - 1))
    ] / self.RETENTION_RATES[0]
)
