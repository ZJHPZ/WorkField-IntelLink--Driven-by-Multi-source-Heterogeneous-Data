"""
Evaluation Agent - 学习评估Agent
功能：评估学习成果、生成评估报告、提供改进建议
处理模式：协作式（依赖QuestionAgent和LearningPathAgent）
"""
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base.base_agent import BaseAgent, CollaborativeAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class EvaluationAgent(CollaborativeAgent):
    """
    评估Agent（协作式Agent）
    
    核心职责：
    1. 评估学习成果和掌握程度
    2. 生成评估报告
    3. 提供改进建议
    4. 协调QuestionAgent和LearningPathAgent
    
    依赖关系：
    - 输入：依赖QuestionAgent的答题结果、LearningPathAgent的学习路径
    - 输出：供给RecommendationAgent使用
    """
    
    def __init__(self):
        super().__init__(
            agent_id="evaluation",
            name="学习评估Agent",
            description="负责评估学习成果和生成评估报告"
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具
        self._tools = None
        
        # 注册协作回调
        self.register_callback("question", self.on_question_complete)
        self.register_callback("learning_path", self.on_path_update)
        
        logger.info("[EvaluationAgent] Initialized")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.EVALUATION
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[EvaluationAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理评估请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing evaluation request: {user_input[:50]}...")
        
        # 1. 获取用户答题记录
        answers = self._extract_answers(state)
        
        # 2. 评估答题结果
        evaluation = await self._evaluate_answers(answers)
        
        # 3. 生成评估报告
        report = await self._generate_report(user_id, evaluation)
        
        # 4. 保存评估结果
        save_result = await self._save_evaluation(user_id, report)
        
        # 5. 生成改进建议
        suggestions = await self._generate_suggestions(evaluation)
        
        # 6. 更新共享上下文
        await self._update_progress(user_id, evaluation)
        
        # 7. 通知下游Agent
        await self._notify_recommendation_agent(user_id, evaluation)
        
        # 8. 生成友好响应
        response = self._format_response(evaluation, report, suggestions)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "evaluation": evaluation,
            "report": report,
            "suggestions": suggestions,
            "saved": save_result.get("success", False),
            "response": response
        }
    
    def _get_latest_user_input(self, state: MultiAgentState) -> str:
        """获取最新用户输入"""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            content = None
            if isinstance(msg, dict):
                content = msg.get("content", "")
            elif hasattr(msg, "content"):
                content = msg.content
            
            if content and isinstance(content, str):
                return content
        return ""
    
    def _extract_answers(self, state: MultiAgentState) -> List[Dict[str, Any]]:
        """提取用户答题记录"""
        answers = state.get("answers", [])
        
        if not answers and self._tools and "get_user_answers" in self._tool_map:
            try:
                user_id = state.get("user_id", "default_user")
                tool = self._tool_map["get_user_answers"]
                result = asyncio.to_thread(
                    tool.invoke,
                    {"user_id": user_id, "limit": 20}
                )
                answers = json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                self.log_error(f"Failed to get answers: {e}")
        
        return answers
    
    async def _evaluate_answers(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估答题结果"""
        if not answers:
            return self._create_empty_evaluation()
        
        # 使用评估工具
        if self._tools and "evaluate_multiple_choice" in self._tool_map:
            try:
                tool = self._tool_map["evaluate_multiple_choice"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"answers_data": json.dumps(answers)}
                )
                evaluation = json.loads(result) if isinstance(result, str) else result
                return evaluation
            except Exception as e:
                self.log_error(f"Failed to evaluate: {e}")
        
        # 生成默认评估
        return self._create_default_evaluation(answers)
    
    def _create_empty_evaluation(self) -> Dict[str, Any]:
        """创建空评估"""
        return {
            "total_questions": 0,
            "correct_count": 0,
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "overall_level": "无数据"
        }
    
    def _create_default_evaluation(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建默认评估"""
        total = len(answers)
        correct = sum(1 for a in answers if a.get("is_correct", False))
        score = int((correct / total * 100) if total > 0 else 0)
        
        # 分析强弱项
        topics = {}
        for answer in answers:
            topic = answer.get("topic", "未知")
            if topic not in topics:
                topics[topic] = {"correct": 0, "total": 0}
            topics[topic]["total"] += 1
            if answer.get("is_correct", False):
                topics[topic]["correct"] += 1
        
        strengths = []
        weaknesses = []
        for topic, stats in topics.items():
            rate = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if rate >= 0.8:
                strengths.append(topic)
            elif rate < 0.5:
                weaknesses.append(topic)
        
        # 判断整体水平
        if score >= 90:
            level = "优秀"
        elif score >= 75:
            level = "良好"
        elif score >= 60:
            level = "及格"
        else:
            level = "需加强"
        
        return {
            "total_questions": total,
            "correct_count": correct,
            "score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "overall_level": level,
            "topic_analysis": topics
        }
    
    async def _generate_report(self, user_id: str, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """生成评估报告"""
        if self._tools and "generate_evaluation_report" in self._tool_map:
            try:
                tool = self._tool_map["generate_evaluation_report"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "user_id": user_id,
                        "evaluation_data": json.dumps(evaluation)
                    }
                )
                report = json.loads(result) if isinstance(result, str) else result
                return report
            except Exception as e:
                self.log_error(f"Failed to generate report: {e}")
        
        # 生成默认报告
        return {
            "user_id": user_id,
            "date": datetime.now().isoformat(),
            "summary": f"本次评估得分{evaluation.get('score', 0)}分，整体水平{evaluation.get('overall_level', '一般')}",
            "details": {
                "total": evaluation.get("total_questions", 0),
                "correct": evaluation.get("correct_count", 0),
                "score": evaluation.get("score", 0)
            }
        }
    
    async def _save_evaluation(self, user_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
        """保存评估结果"""
        if self._tools and "save_evaluation" in self._tool_map:
            try:
                tool = self._tool_map["save_evaluation"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "user_id": user_id,
                        "report_data": json.dumps(report)
                    }
                )
                save_result = json.loads(result) if isinstance(result, str) else result
                return save_result
            except Exception as e:
                self.log_error(f"Failed to save evaluation: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": True, "simulated": True}
    
    async def _generate_suggestions(self, evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []
        
        # 基于评估结果生成建议
        score = evaluation.get("score", 0)
        weaknesses = evaluation.get("weaknesses", [])
        
        if score < 60:
            suggestions.append({
                "priority": "high",
                "title": "基础需要加强",
                "content": "建议重新学习基础知识，配合练习题巩固"
            })
        
        if weaknesses:
            suggestions.append({
                "priority": "medium",
                "title": "薄弱环节需要强化",
                "content": f"建议针对{', '.join(weaknesses[:2])}进行专项练习"
            })
        
        if score >= 60 and score < 80:
            suggestions.append({
                "priority": "medium",
                "title": "巩固提升",
                "content": "建议多做综合练习，提升解题能力"
            })
        
        if score >= 80:
            suggestions.append({
                "priority": "low",
                "title": "保持状态",
                "content": "学习效果良好，建议继续深入学习"
            })
        
        suggestions.append({
            "priority": "general",
            "title": "学习建议",
            "content": "坚持每天学习，及时复习，形成知识体系"
        })
        
        return suggestions
    
    async def _update_progress(self, user_id: str, evaluation: Dict[str, Any]):
        """更新学习进度"""
        score = evaluation.get("score", 0) / 100
        self.shared_context.update_learning_progress(user_id, {
            "current_subject": evaluation.get("subject", ""),
            "current_score": score,
            "weak_points": evaluation.get("weak_points", [])
        })
    
    async def _notify_recommendation_agent(self, user_id: str, evaluation: Dict[str, Any]):
        """通知推荐Agent"""
        await self.send_to_agent(
            "recommendation",
            {
                "task": "personalized_recommendations",
                "user_id": user_id,
                "evaluation": evaluation
            }
        )
    
    async def on_question_complete(self, data: Dict[str, Any]):
        """题目完成回调"""
        user_id = data.get("user_id")
        answers = data.get("answers", [])
        
        self.log_info(f"Received {len(answers)} answers from user {user_id}")
        
        # 评估答题结果
        evaluation = await self._evaluate_answers(answers)
        
        # 生成建议
        suggestions = await self._generate_suggestions(evaluation)
        
        # 更新进度
        await self._update_progress(user_id, evaluation)
    
    async def on_path_update(self, data: Dict[str, Any]):
        """学习路径更新回调"""
        user_id = data.get("user_id")
        learning_path = data.get("learning_path", {})
        
        self.log_info(f"Learning path updated for user {user_id}")
        
        # 设置评估节点
        stages = learning_path.get("stages", [])
        evaluation_points = []
        
        for stage in stages:
            evaluation_points.append({
                "stage_id": stage.get("stage_id"),
                "milestone": stage.get("milestone")
            })
        
        return {"evaluation_points": evaluation_points}
    
    def _format_response(
        self,
        evaluation: Dict[str, Any],
        report: Dict[str, Any],
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """格式化响应内容"""
        score = evaluation.get("score", 0)
        level = evaluation.get("overall_level", "一般")
        strengths = evaluation.get("strengths", [])
        weaknesses = evaluation.get("weaknesses", [])
        
        response = f"""📊 **学习评估报告**

**总体得分：{score}分（{level}）**

"""
        
        if strengths:
            response += f"""**💪 强项**
- {', '.join(strengths)}

"""
        
        if weaknesses:
            response += f"""**📚 薄弱环节**
- {', '.join(weaknesses)}

"""
        
        response += """**📋 详细分析**
"""
        response += f"""
- 总题数：{evaluation.get('total_questions', 0)}
- 正确数：{evaluation.get('correct_count', 0)}
- 正确率：{int(evaluation.get('correct_count', 0) / evaluation.get('total_questions', 1) * 100) if evaluation.get('total_questions', 0) > 0 else 0}%

"""
        
        if suggestions:
            response += """**💡 改进建议**

"""
            for i, s in enumerate(suggestions[:3], 1):
                response += f"{i}. **{s['title']}**：{s['content']}\n"
        
        response += """

继续加油！有问题随时问我！ 🌟
"""
        
        return response


# 全局实例
_evaluation_agent: Optional[EvaluationAgent] = None


def get_evaluation_agent() -> EvaluationAgent:
    """获取全局EvaluationAgent实例"""
    global _evaluation_agent
    if _evaluation_agent is None:
        _evaluation_agent = EvaluationAgent()
    return _evaluation_agent
