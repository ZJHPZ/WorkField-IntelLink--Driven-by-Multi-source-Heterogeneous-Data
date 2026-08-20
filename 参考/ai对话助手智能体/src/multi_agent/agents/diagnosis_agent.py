"""
诊断Agent
DiagnosisAgent

实现 Level 2/3 诊断能力：
- Level 2: 学习路径个性化（已通过知识图谱实现）
- Level 3: 诊断学生哪里没学会、为什么没学会

核心功能：
1. 错误归因分析
2. 根因追溯
3. 知识薄弱点检测
4. 学习建议生成
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from multi_agent.base.base_agent import BaseAgent
from multi_agent.base.agent_state import MultiAgentState, IntentType
from multi_agent.knowledge.bigdata_knowledge_graph import get_knowledge_graph, KnowledgeNode, DifficultyLevel


class ErrorType(Enum):
    """错误类型"""
    CONCEPTUAL = "conceptual"           # 概念理解错误
    PROCEDURAL = "procedural"          # 步骤/流程错误
    CALCULATION = "calculation"         # 计算错误
    MISREADING = "misreading"          # 审题错误
    FOUNDATION = "foundation"          # 基础不牢
    APPLICATION = "application"        # 应用不当
    FORGETTING = "forgetting"          # 遗忘


class MasteryLevel(Enum):
    """掌握程度"""
    MASTERED = "mastered"               # 完全掌握
    PROFICIENT = "proficient"          # 熟练
    FAMILIAR = "familiar"             # 熟悉
    UNDERSTANDING = "understanding"   # 理解中
    UNFAMILIAR = "unfamiliar"          # 不熟悉
    UNKNOWN = "unknown"                # 完全未知


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: ErrorType
    description: str
    root_cause: str
    related_topics: List[str]
    suggested_fix: str
    confidence: float  # 分析置信度 0-1


class DiagnosisAgent(BaseAgent):
    """
    诊断Agent
    
    核心功能：
    1. 评估知识点掌握程度
    2. 错误归因分析
    3. 根因追溯
    4. 生成补救学习建议
    """
    
    def __init__(self):
        super().__init__(
            agent_id="diagnosis",
            name="诊断Agent",
            description="诊断学习薄弱点，分析错误原因"
        )
        self.knowledge_graph = get_knowledge_graph()
        
        # 用户学习记录
        self._user_mastery: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._user_errors: Dict[str, List[Tuple[str, ErrorType, str]]] = defaultdict(list)
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.EVALUATION
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """处理诊断请求"""
        user_id = state.get('user_id', 'anonymous')
        messages = state.get('messages', [])
        context = state.get('context', {}) or {}
        
        user_input = messages[-1].content if messages else ""
        action = context.get('action') or self._determine_action(user_input)
        
        if action == "assess":
            return await self._assess_mastery(context.get('topic_id'), user_id)
        elif action == "diagnose_error":
            return await self._diagnose_error(context, user_id)
        elif action == "find_gaps":
            return await self._find_gaps(user_id)
        elif action == "trace_root":
            return await self._trace_root(context.get('topic_id'), user_id)
        elif action == "generate_plan":
            return await self._generate_remediation_plan(context.get('topic_id'), user_id)
        else:
            return await self._comprehensive_diagnosis(context.get('topic_id'), user_id)
    
    def _determine_action(self, user_input: str) -> str:
        if any(kw in user_input for kw in ["评估", "掌握", "水平"]):
            return "assess"
        elif any(kw in user_input for kw in ["错", "不会", "不懂"]):
            return "diagnose_error"
        elif any(kw in user_input for kw in ["薄弱", "gap", "差距"]):
            return "find_gaps"
        elif any(kw in user_input for kw in ["根本", "原因"]):
            return "trace_root"
        elif any(kw in user_input for kw in ["计划", "补救"]):
            return "generate_plan"
        return "comprehensive"
    
    async def _assess_mastery(self, topic_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """评估知识点掌握程度"""
        if not topic_id:
            return {"success": False, "message": "请提供要评估的知识点ID"}
        
        node = self.knowledge_graph.nodes.get(topic_id)
        if not node:
            return {"success": False, "message": f"未找到知识点: {topic_id}"}
        
        mastery_score = self._user_mastery.get(user_id, {}).get(topic_id, 0.0)
        
        if node.prerequisites:
            prereq_scores = [
                self._user_mastery.get(user_id, {}).get(prereq, 0.0)
                for prereq in node.prerequisites
            ]
            if prereq_scores:
                avg_prereq = sum(prereq_scores) / len(prereq_scores)
                mastery_score = min(mastery_score, avg_prereq * 0.8 + mastery_score * 0.2)
        
        mastery_level = self._score_to_level(mastery_score)
        
        return {
            "success": True,
            "topic_id": topic_id,
            "topic_name": node.name,
            "mastery_score": round(mastery_score * 100, 1),
            "mastery_level": mastery_level.value,
            "difficulty": node.difficulty.value,
            "estimated_hours": node.estimated_hours,
            "message": f"「{node.name}」掌握程度: {mastery_level.value} ({mastery_score*100:.0f}%)"
        }
    
    async def _diagnose_error(self, context: Dict, user_id: str) -> Dict[str, Any]:
        """诊断错误原因"""
        topic_id = context.get('topic_id')
        user_answer = context.get('user_answer', '')
        
        if not topic_id:
            return {"success": False, "message": "请提供相关知识点"}
        
        node = self.knowledge_graph.nodes.get(topic_id)
        if not node:
            return {"success": False, "message": f"未找到知识点: {topic_id}"}
        
        error_analysis = self._analyze_error(topic_id, user_answer)
        
        if error_analysis:
            self._user_errors[user_id].append((topic_id, error_analysis.error_type, error_analysis.description))
        
        current_mastery = self._user_mastery.get(user_id, {}).get(topic_id, 0.5)
        self._user_mastery[user_id][topic_id] = current_mastery * 0.7
        
        root_cause = self._trace_topic_root_cause(topic_id, user_id)
        
        return {
            "success": True,
            "topic_id": topic_id,
            "topic_name": node.name,
            "error_type": error_analysis.error_type.value if error_analysis else "unknown",
            "description": error_analysis.description if error_analysis else "未知错误",
            "root_cause": error_analysis.root_cause if error_analysis else root_cause,
            "suggested_fix": error_analysis.suggested_fix if error_analysis else "建议复习相关内容",
            "message": self._generate_error_message(error_analysis, root_cause)
        }
    
    async def _find_gaps(self, user_id: str) -> Dict[str, Any]:
        """查找知识薄弱点"""
        gaps = []
        
        for topic_id, node in self.knowledge_graph.nodes.items():
            mastery_score = self._user_mastery.get(user_id, {}).get(topic_id, 0.0)
            
            if mastery_score < 0.6:
                missing_prereqs = []
                for prereq in node.prerequisites:
                    prereq_score = self._user_mastery.get(user_id, {}).get(prereq, 0.0)
                    if prereq_score < 0.5:
                        prereq_node = self.knowledge_graph.nodes.get(prereq)
                        if prereq_node:
                            missing_prereqs.append(prereq_node.name)
                
                gaps.append({
                    "topic_id": topic_id,
                    "topic_name": node.name,
                    "mastery_score": round(mastery_score * 100, 1),
                    "difficulty": node.difficulty.value,
                    "missing_prerequisites": missing_prereqs,
                    "priority": self._calculate_gap_priority(node, mastery_score)
                })
        
        gaps.sort(key=lambda x: (0 if x["priority"] == "high" else 1, x["mastery_score"]))
        
        high_priority = [g for g in gaps if g["priority"] == "high"]
        
        return {
            "success": True,
            "total_gaps": len(gaps),
            "high_priority_gaps": high_priority[:5],
            "summary": {"total": len(gaps), "high": len(high_priority)},
            "message": f"发现 {len(gaps)} 个知识薄弱点，其中 {len(high_priority)} 个需要优先补救"
        }
    
    async def _trace_root(self, topic_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """追溯根本原因"""
        if not topic_id:
            return {"success": False, "message": "请提供要分析的知识点"}
        
        root_cause = self._trace_topic_root_cause(topic_id, user_id)
        node = self.knowledge_graph.nodes.get(topic_id)
        
        return {
            "success": True,
            "target_topic": node.name if node else topic_id,
            "root_cause": root_cause,
            "message": f"「{node.name if node else topic_id}」的根本原因：{root_cause}"
        }
    
    async def _generate_remediation_plan(self, topic_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """生成补救学习计划"""
        if not topic_id:
            return {"success": False, "message": "请提供需要补救的知识点"}
        
        node = self.knowledge_graph.nodes.get(topic_id)
        if not node:
            return {"success": False, "message": f"未找到知识点: {topic_id}"}
        
        plan = self._create_remediation_plan(topic_id, user_id)
        total_time = sum(step.get('estimated_minutes', 30) for step in plan)
        
        return {
            "success": True,
            "target_topic": node.name,
            "plan": plan,
            "estimated_time": total_time,
            "message": f"「{node.name}」补救计划：{len(plan)}个步骤，预计{total_time}分钟"
        }
    
    async def _comprehensive_diagnosis(self, topic_id: Optional[str], user_id: str) -> Dict[str, Any]:
        """综合诊断"""
        assessment = await self._assess_mastery(topic_id, user_id)
        gaps = await self._find_gaps(user_id)
        
        return {
            "success": True,
            "target_topic": assessment.get("topic_name") if topic_id else None,
            "current_mastery": assessment.get("mastery_score", 0),
            "mastery_level": assessment.get("mastery_level", "unknown"),
            "total_gaps": gaps.get("total_gaps", 0),
            "summary": gaps.get("summary", {}),
            "message": f"综合诊断完成。「{assessment.get('topic_name', '整体') if topic_id else '整体'}」掌握程度{assessment.get('mastery_score', 0)}%，发现{gaps.get('total_gaps', 0)}个薄弱点"
        }
    
    def _analyze_error(self, topic_id: str, user_answer: str) -> Optional[ErrorAnalysis]:
        """分析错误类型"""
        if not user_answer or user_answer.strip() == "":
            return ErrorAnalysis(
                error_type=ErrorType.FORGETTING,
                description="未能作答，可能已遗忘相关知识",
                root_cause="知识点长时间未复习导致遗忘",
                related_topics=[topic_id],
                suggested_fix="重新学习该知识点，并设置复习提醒",
                confidence=0.8
            )
        return ErrorAnalysis(
            error_type=ErrorType.APPLICATION,
            description="对知识点的应用不够灵活",
            root_cause="理论与实践结合不足",
            related_topics=[topic_id],
            suggested_fix="多做练习，加深理解",
            confidence=0.6
        )
    
    def _trace_topic_root_cause(self, topic_id: str, user_id: str) -> Optional[str]:
        """追溯根因"""
        node = self.knowledge_graph.nodes.get(topic_id)
        if not node:
            return None
        
        weak_prereqs = []
        for prereq in node.prerequisites:
            prereq_score = self._user_mastery.get(user_id, {}).get(prereq, 0.0)
            if prereq_score < 0.5:
                prereq_node = self.knowledge_graph.nodes.get(prereq)
                if prereq_node:
                    weak_prereqs.append(prereq_node.name)
        
        if weak_prereqs:
            return f"前置知识掌握不牢：{', '.join(weak_prereqs)}"
        return "知识点理解不够深入，需要加强基础"
    
    def _create_remediation_plan(self, topic_id: str, user_id: str) -> List[Dict[str, Any]]:
        """创建补救计划"""
        node = self.knowledge_graph.nodes.get(topic_id)
        if not node:
            return []
        
        plan = []
        
        for prereq in node.prerequisites:
            prereq_node = self.knowledge_graph.nodes.get(prereq)
            if prereq_node:
                prereq_score = self._user_mastery.get(user_id, {}).get(prereq, 0.0)
                if prereq_score < 0.7:
                    plan.append({
                        "step": len(plan) + 1,
                        "type": "review_prerequisite",
                        "topic_name": prereq_node.name,
                        "action": f"复习「{prereq_node.name}」",
                        "estimated_minutes": 20,
                        "priority": "high" if prereq_score < 0.5 else "medium"
                    })
        
        plan.append({
            "step": len(plan) + 1,
            "type": "relearn",
            "topic_name": node.name,
            "action": f"重新学习「{node.name}」",
            "estimated_minutes": int(node.estimated_hours * 30),
            "priority": "high"
        })
        
        plan.append({
            "step": len(plan) + 1,
            "type": "practice",
            "topic_name": node.name,
            "action": f"完成「{node.name}」相关练习",
            "estimated_minutes": 30,
            "priority": "high"
        })
        
        return plan
    
    def _score_to_level(self, score: float) -> MasteryLevel:
        if score >= 0.9:
            return MasteryLevel.MASTERED
        elif score >= 0.7:
            return MasteryLevel.PROFICIENT
        elif score >= 0.5:
            return MasteryLevel.FAMILIAR
        elif score >= 0.3:
            return MasteryLevel.UNDERSTANDING
        elif score >= 0.1:
            return MasteryLevel.UNFAMILIAR
        return MasteryLevel.UNKNOWN
    
    def _calculate_gap_priority(self, node: KnowledgeNode, mastery_score: float) -> str:
        if node.difficulty == DifficultyLevel.高级 and mastery_score < 0.3:
            return "high"
        if node.difficulty == DifficultyLevel.进阶 and mastery_score < 0.4:
            return "high"
        if mastery_score < 0.2:
            return "high"
        if mastery_score < 0.4:
            return "medium"
        return "low"
    
    def _generate_error_message(self, error: Optional[ErrorAnalysis], root: Optional[str]) -> str:
        if not error:
            return "分析完成，请根据建议进行复习"
        return f"错误类型：{error.error_type.value}。原因：{error.root_cause}。建议：{error.suggested_fix}"


_diagnosis_agent: Optional['DiagnosisAgent'] = None


def get_diagnosis_agent() -> 'DiagnosisAgent':
    global _diagnosis_agent
    if _diagnosis_agent is None:
        _diagnosis_agent = DiagnosisAgent()
    return _diagnosis_agent
