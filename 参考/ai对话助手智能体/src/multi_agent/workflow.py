"""
Workflow - 工作流编排模块
定义和执行复杂的多Agent协作工作流
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from datetime import datetime

from .base.agent_state import MultiAgentState
from .communication.message_bus import get_message_bus

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """工作流类型"""
    LEARNING_PATH = "learning_path"
    EVALUATION = "evaluation"
    RECOMMENDATION = "recommendation"
    FULL_LEARNING_CYCLE = "full_learning_cycle"


class WorkflowStep:
    """工作流步骤"""
    
    def __init__(
        self,
        step_id: str,
        agent_id: str,
        action: str,
        inputs: Dict[str, Any],
        outputs: List[str],
        depends_on: Optional[List[str]] = None
    ):
        self.step_id = step_id
        self.agent_id = agent_id
        self.action = action
        self.inputs = inputs
        self.outputs = outputs
        self.depends_on = depends_on or []
        self.status = "pending"
        self.result = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }


class Workflow:
    """工作流"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        workflow_type: WorkflowType,
        steps: List[WorkflowStep]
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.workflow_type = workflow_type
        self.steps = {step.step_id: step for step in steps}
        self.status = "created"
        self.start_time = None
        self.end_time = None
        self.results = {}
    
    def get_executable_steps(self) -> List[WorkflowStep]:
        """获取可执行的步骤（依赖已完成的）"""
        executable = []
        for step in self.steps.values():
            if step.status != "pending":
                continue
            
            # 检查依赖
            deps_completed = True
            for dep_id in step.depends_on:
                dep_step = self.steps.get(dep_id)
                if not dep_step or dep_step.status != "completed":
                    deps_completed = False
                    break
            
            if deps_completed:
                executable.append(step)
        
        return executable
    
    def is_complete(self) -> bool:
        """检查工作流是否完成"""
        return all(step.status == "completed" for step in self.steps.values())
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return any(step.status == "failed" for step in self.steps.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "type": self.workflow_type.value,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps.values()],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self):
        self.message_bus = get_message_bus()
        self._agent_executor: Optional[Callable] = None
    
    def set_agent_executor(self, executor: Callable):
        """设置Agent执行器"""
        self._agent_executor = executor
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow: 工作流定义
            initial_context: 初始上下文
            
        Returns:
            执行结果
        """
        logger.info(f"[WorkflowExecutor] Starting workflow: {workflow.workflow_id}")
        
        workflow.status = "running"
        workflow.start_time = datetime.now()
        
        context = initial_context or {}
        max_iterations = len(workflow.steps) * 2  # 防止无限循环
        iteration = 0
        
        try:
            while not workflow.is_complete() and iteration < max_iterations:
                # 获取可执行的步骤
                executable = workflow.get_executable_steps()
                
                if not executable:
                    logger.warning(f"[WorkflowExecutor] No executable steps, workflow may be stuck")
                    break
                
                # 执行步骤
                for step in executable:
                    await self._execute_step(workflow, step, context)
                    
                    # 如果失败，记录但继续
                    if step.status == "failed":
                        logger.warning(f"[WorkflowExecutor] Step {step.step_id} failed: {step.error}")
                
                iteration += 1
            
            # 确定最终状态
            if workflow.is_complete():
                workflow.status = "completed"
            elif workflow.has_errors():
                workflow.status = "completed_with_errors"
            else:
                workflow.status = "partial"
            
        except Exception as e:
            logger.error(f"[WorkflowExecutor] Workflow execution error: {e}")
            workflow.status = "failed"
            raise
        
        finally:
            workflow.end_time = datetime.now()
        
        return {
            "success": workflow.status in ["completed", "completed_with_errors"],
            "workflow": workflow.to_dict(),
            "results": workflow.results
        }
    
    async def _execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: Dict[str, Any]
    ):
        """执行单个步骤"""
        logger.info(f"[WorkflowExecutor] Executing step: {step.step_id}")
        
        step.status = "running"
        
        try:
            # 准备输入
            inputs = self._prepare_inputs(step, context, workflow.results)
            
            # 执行Agent
            if self._agent_executor:
                result = await self._agent_executor(step.agent_id, step.action, inputs)
            else:
                # 模拟执行
                result = await self._mock_execute(step, inputs)
            
            step.result = result
            step.status = "completed"
            
            # 更新上下文
            for output_key in step.outputs:
                context[output_key] = result.get(output_key)
            
            # 保存结果
            workflow.results[step.step_id] = result
            
        except Exception as e:
            logger.error(f"[WorkflowExecutor] Step execution error: {e}")
            step.status = "failed"
            step.error = str(e)
    
    def _prepare_inputs(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备输入参数"""
        inputs = {}
        
        for key, value in step.inputs.items():
            # 如果是引用，替换为实际值
            if isinstance(value, str) and value.startswith("$"):
                ref = value[1:]
                
                # 从上下文获取
                if ref in context:
                    inputs[key] = context[ref]
                # 从结果获取
                elif ref in results:
                    inputs[key] = results[ref]
                else:
                    inputs[key] = None
            else:
                inputs[key] = value
        
        return inputs
    
    async def _mock_execute(self, step: WorkflowStep, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """模拟执行（当没有Agent执行器时）"""
        return {
            "step_id": step.step_id,
            "agent_id": step.agent_id,
            "action": step.action,
            "status": "completed",
            "data": inputs
        }


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.executor = WorkflowExecutor()
        self._agent_executor: Optional[Callable] = None
    
    def set_agent_executor(self, executor: Callable):
        """设置Agent执行器"""
        self._agent_executor = executor
        self.executor.set_agent_executor(executor)
    
    def create_learning_path_workflow(
        self,
        user_id: str,
        subject: str,
        knowledge_level: str = "初级"
    ) -> Workflow:
        """
        创建学习路径工作流
        
        流程：
        1. ConversationAgent - 采集用户信息
        2. LearningPathAgent - 生成学习路径
        3. EvaluationAgent - 设置评估节点
        4. RecommendationAgent - 配置推送
        """
        steps = [
            WorkflowStep(
                step_id="step_1_conversation",
                agent_id="conversation",
                action="extract_profile",
                inputs={
                    "user_id": user_id
                },
                outputs=["user_profile"]
            ),
            WorkflowStep(
                step_id="step_2_learning_path",
                agent_id="learning_path",
                action="generate_path",
                inputs={
                    "user_id": user_id,
                    "subject": subject,
                    "knowledge_level": knowledge_level
                },
                outputs=["learning_path"],
                depends_on=["step_1_conversation"]
            ),
            WorkflowStep(
                step_id="step_3_evaluation",
                agent_id="evaluation",
                action="setup_milestones",
                inputs={
                    "user_id": user_id,
                    "learning_path": "$learning_path"
                },
                outputs=["evaluations"],
                depends_on=["step_2_learning_path"]
            ),
            WorkflowStep(
                step_id="step_4_recommendation",
                agent_id="recommendation",
                action="plan_push",
                inputs={
                    "user_id": user_id,
                    "learning_path": "$learning_path"
                },
                outputs=["recommendations"],
                depends_on=["step_2_learning_path"]
            )
        ]
        
        workflow = Workflow(
            workflow_id=f"lp_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=f"学习路径工作流 - {subject}",
            workflow_type=WorkflowType.LEARNING_PATH,
            steps=steps
        )
        
        self.workflows[workflow.workflow_id] = workflow
        return workflow
    
    def create_evaluation_workflow(
        self,
        user_id: str,
        subject: str,
        topic: str
    ) -> Workflow:
        """
        创建评估工作流
        
        流程：
        1. QuestionAgent - 生成题目
        2. EvaluationAgent - 评估答案
        3. RecommendationAgent - 生成建议
        """
        steps = [
            WorkflowStep(
                step_id="step_1_questions",
                agent_id="question",
                action="generate_questions",
                inputs={
                    "subject": subject,
                    "topic": topic,
                    "count": 5
                },
                outputs=["questions"]
            ),
            WorkflowStep(
                step_id="step_2_evaluation",
                agent_id="evaluation",
                action="evaluate",
                inputs={
                    "user_id": user_id,
                    "questions": "$questions"
                },
                outputs=["evaluation_result"],
                depends_on=["step_1_questions"]
            ),
            WorkflowStep(
                step_id="step_3_recommendation",
                agent_id="recommendation",
                action="generate_recommendations",
                inputs={
                    "user_id": user_id,
                    "evaluation": "$evaluation_result"
                },
                outputs=["recommendations"],
                depends_on=["step_2_evaluation"]
            )
        ]
        
        workflow = Workflow(
            workflow_id=f"eval_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=f"评估工作流 - {topic}",
            workflow_type=WorkflowType.EVALUATION,
            steps=steps
        )
        
        self.workflows[workflow.workflow_id] = workflow
        return workflow
    
    def create_full_learning_cycle_workflow(
        self,
        user_id: str,
        subject: str,
        topic: str
    ) -> Workflow:
        """
        创建完整学习周期工作流
        
        流程：
        1. ConversationAgent - 采集对话
        2. DocumentAgent - 生成文档
        3. QuestionAgent - 生成题目
        4. MultimediaAgent - 生成多媒体
        5. LearningPathAgent - 生成路径
        6. EvaluationAgent - 评估
        7. RecommendationAgent - 推荐
        """
        steps = [
            WorkflowStep(
                step_id="step_1_conversation",
                agent_id="conversation",
                action="extract_features",
                inputs={"user_id": user_id, "topic": topic},
                outputs=["user_features"]
            ),
            WorkflowStep(
                step_id="step_2_document",
                agent_id="document",
                action="generate_document",
                inputs={"topic": topic},
                outputs=["document"]
            ),
            WorkflowStep(
                step_id="step_3_questions",
                agent_id="question",
                action="generate_practice",
                inputs={"subject": subject, "topic": topic, "count": 3},
                outputs=["questions"]
            ),
            WorkflowStep(
                step_id="step_4_multimedia",
                agent_id="multimedia",
                action="generate_visuals",
                inputs={"topic": topic},
                outputs=["multimedia"]
            ),
            WorkflowStep(
                step_id="step_5_learning_path",
                agent_id="learning_path",
                action="generate_path",
                inputs={"user_id": user_id, "subject": subject, "knowledge_level": "初级"},
                outputs=["learning_path"],
                depends_on=["step_1_conversation"]
            ),
            WorkflowStep(
                step_id="step_6_evaluation",
                agent_id="evaluation",
                action="evaluate",
                inputs={"user_id": user_id, "learning_path": "$learning_path"},
                outputs=["evaluation"],
                depends_on=["step_5_learning_path"]
            ),
            WorkflowStep(
                step_id="step_7_recommendation",
                agent_id="recommendation",
                action="personalized_recommendations",
                inputs={"user_id": user_id, "evaluation": "$evaluation"},
                outputs=["recommendations"],
                depends_on=["step_6_evaluation"]
            )
        ]
        
        workflow = Workflow(
            workflow_id=f"full_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=f"完整学习周期 - {topic}",
            workflow_type=WorkflowType.FULL_LEARNING_CYCLE,
            steps=steps
        )
        
        self.workflows[workflow.workflow_id] = workflow
        return workflow
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        return await self.executor.execute_workflow(workflow, initial_context)
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        return [wf.to_dict() for wf in self.workflows.values()]


# 全局实例
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """获取全局工作流管理器"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager
