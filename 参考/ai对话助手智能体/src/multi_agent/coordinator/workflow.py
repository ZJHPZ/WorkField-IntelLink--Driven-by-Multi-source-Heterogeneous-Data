"""
Workflow Manager
工作流管理器 - 管理多Agent协作工作流
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field

from ..base.agent_state import IntentType, TaskStatus, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context
from ..registry import get_registry

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """工作流类型"""
    LEARNING_PATH = "learning_path"        # 学习路径规划流程
    EVALUATION = "evaluation"              # 学习评估流程
    CONTENT_GENERATION = "content_generation"  # 内容生成流程
    CUSTOM = "custom"                     # 自定义流程


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    agent_id: str
    step_name: str
    input_from: List[str]  # 依赖的前置步骤ID
    output_to: List[str]   # 输出给哪些步骤
    timeout: int = 60      # 超时时间（秒）


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    workflow_type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: Optional[datetime] = None


@dataclass
class WorkflowExecution:
    """工作流执行"""
    execution_id: str
    workflow_id: str
    status: str  # pending, running, completed, failed
    current_step: Optional[str]
    step_results: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


class WorkflowManager:
    """
    工作流管理器
    
    管理多Agent协作工作流的定义和执行。
    支持：
    - 预定义工作流（学习路径、评估等）
    - 自定义工作流
    - 工作流执行跟踪
    """
    
    def __init__(self):
        self.message_bus = get_message_bus()
        self.shared_context = get_shared_context()
        self.registry = get_registry()
        
        # 工作流定义
        self.workflows: Dict[str, WorkflowDefinition] = {}
        
        # 工作流执行记录
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # 初始化预定义工作流
        self._init_preset_workflows()
        
        logger.info("[WorkflowManager] Initialized")
    
    def _init_preset_workflows(self) -> None:
        """初始化预定义工作流"""
        
        # 学习路径规划工作流
        learning_path_workflow = WorkflowDefinition(
            workflow_id="learning_path_flow",
            workflow_type=WorkflowType.LEARNING_PATH,
            name="学习路径规划流程",
            description="用户画像采集 → 路径规划 → 内容推荐",
            steps=[
                WorkflowStep(
                    step_id="step_1",
                    agent_id="conversation",
                    step_name="采集用户信息",
                    input_from=[],
                    output_to=["step_2"]
                ),
                WorkflowStep(
                    step_id="step_2",
                    agent_id="learning_path",
                    step_name="生成学习路径",
                    input_from=["step_1"],
                    output_to=["step_3"]
                ),
                WorkflowStep(
                    step_id="step_3",
                    agent_id="recommendation",
                    step_name="生成推荐内容",
                    input_from=["step_2"],
                    output_to=[]
                ),
            ]
        )
        self.workflows["learning_path_flow"] = learning_path_workflow
        
        # 学习评估工作流
        evaluation_workflow = WorkflowDefinition(
            workflow_id="evaluation_flow",
            workflow_type=WorkflowType.EVALUATION,
            name="学习评估流程",
            description="练习测试 → 结果评估 → 反馈建议",
            steps=[
                WorkflowStep(
                    step_id="eval_step_1",
                    agent_id="question",
                    step_name="生成测试题",
                    input_from=[],
                    output_to=["eval_step_2"]
                ),
                WorkflowStep(
                    step_id="eval_step_2",
                    agent_id="evaluation",
                    step_name="评估学习成果",
                    input_from=["eval_step_1"],
                    output_to=["eval_step_3"]
                ),
                WorkflowStep(
                    step_id="eval_step_3",
                    agent_id="recommendation",
                    step_name="生成改进建议",
                    input_from=["eval_step_2"],
                    output_to=[]
                ),
            ]
        )
        self.workflows["evaluation_flow"] = evaluation_workflow
        
        # 内容生成工作流
        content_workflow = WorkflowDefinition(
            workflow_id="content_flow",
            workflow_type=WorkflowType.CONTENT_GENERATION,
            name="内容生成流程",
            description="文档生成 → 多媒体补充 → 发送邮件",
            steps=[
                WorkflowStep(
                    step_id="content_step_1",
                    agent_id="document",
                    step_name="生成文档",
                    input_from=[],
                    output_to=["content_step_2"]
                ),
                WorkflowStep(
                    step_id="content_step_2",
                    agent_id="multimedia",
                    step_name="生成多媒体内容",
                    input_from=["content_step_1"],
                    output_to=[]
                ),
            ]
        )
        self.workflows["content_flow"] = content_workflow
        
        logger.info(f"[WorkflowManager] Initialized {len(self.workflows)} preset workflows")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """注册自定义工作流"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"[WorkflowManager] Registered workflow: {workflow.workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self.workflows.get(workflow_id)
    
    def get_workflows_by_type(self, workflow_type: WorkflowType) -> List[WorkflowDefinition]:
        """按类型获取工作流"""
        return [
            wf for wf in self.workflows.values()
            if wf.workflow_type == workflow_type
        ]
    
    async def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any],
        callback: Optional[Callable] = None
    ) -> WorkflowExecution:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            context: 执行上下文
            callback: 步骤完成回调
            
        Returns:
            工作流执行结果
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        execution_id = f"exec-{uuid4().hex[:8]}"
        
        # 创建执行记录
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="running",
            current_step=None,
            step_results={},
            started_at=datetime.now(),
            completed_at=None,
            error=None
        )
        self.executions[execution_id] = execution
        
        logger.info(f"[WorkflowManager] Starting workflow: {workflow_id}, execution: {execution_id}")
        
        try:
            # 构建步骤依赖图
            step_map = {step.step_id: step for step in workflow.steps}
            completed_steps = set()
            pending_steps = set(step.step_id for step in workflow.steps)
            
            # 执行直到所有步骤完成
            while pending_steps:
                # 找到可执行的步骤
                ready_steps = [
                    step_id for step_id in pending_steps
                    if all(dep in completed_steps for dep in step_map[step_id].input_from)
                ]
                
                if not ready_steps:
                    # 检查是否有循环依赖
                    if pending_steps:
                        raise RuntimeError(f"Circular dependency detected in workflow: {pending_steps}")
                    break
                
                # 执行就绪的步骤
                for step_id in ready_steps:
                    step = step_map[step_id]
                    execution.current_step = step_id
                    
                    self.log_info(f"Executing step: {step.step_name} ({step_id})")
                    
                    # 获取Agent
                    agent = self.registry.get(step.agent_id)
                    
                    if agent:
                        # 准备输入数据
                        input_data = self._prepare_step_input(step, execution.step_results, context)
                        
                        # 执行Agent
                        try:
                            result = await agent.process(input_data)
                            execution.step_results[step_id] = result
                            self.log_info(f"Step {step_id} completed")
                            
                            # 触发回调
                            if callback:
                                await callback(step_id, result)
                                
                        except Exception as e:
                            self.log_error(f"Step {step_id} failed: {str(e)}")
                            execution.error = f"Step {step_id} failed: {str(e)}"
                            execution.status = "failed"
                            raise
                    
                    completed_steps.add(step_id)
                    pending_steps.remove(step_id)
            
            # 工作流完成
            execution.status = "completed"
            execution.current_step = None
            execution.completed_at = datetime.now()
            
            logger.info(f"[WorkflowManager] Workflow completed: {execution_id}")
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            logger.error(f"[WorkflowManager] Workflow failed: {execution_id}, error: {str(e)}")
        
        return execution
    
    def _prepare_step_input(
        self,
        step: WorkflowStep,
        previous_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备步骤输入数据"""
        input_data = context.copy()
        
        # 添加前置步骤的结果
        for dep_step_id in step.input_from:
            if dep_step_id in previous_results:
                input_data[f"from_{dep_step_id}"] = previous_results[dep_step_id]
        
        return input_data
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行记录"""
        return self.executions.get(execution_id)
    
    def get_running_executions(self) -> List[WorkflowExecution]:
        """获取正在运行的执行"""
        return [
            exec for exec in self.executions.values()
            if exec.status == "running"
        ]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == "running":
            execution.status = "failed"
            execution.error = "Cancelled by user"
            execution.completed_at = datetime.now()
            return True
        return False
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """获取工作流统计"""
        total = len(self.executions)
        completed = sum(1 for e in self.executions.values() if e.status == "completed")
        failed = sum(1 for e in self.executions.values() if e.status == "failed")
        running = sum(1 for e in self.executions.values() if e.status == "running")
        
        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": completed / total if total > 0 else 0,
            "workflow_count": len(self.workflows)
        }


from dataclasses import dataclass

# 全局实例
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """获取全局工作流管理器实例"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager
