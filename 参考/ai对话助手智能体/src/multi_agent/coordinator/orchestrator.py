"""
Orchestrator Agent
调度Agent - 负责任务分解、调度和结果整合
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from ..base.base_agent import BaseAgent, CollaborativeAgent
from ..base.agent_state import (
    MultiAgentState, IntentType, TaskStatus, ProcessingMode, 
    TaskInfo, TaskDecomposition
)
from ..base.message import AgentMessage, MessageType
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context
from .router import IntentRouter, get_intent_router
from ..registry import get_registry

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    调度Agent
    
    核心职责：
    1. 意图识别 - 识别用户意图
    2. 任务分解 - 将复杂任务分解为子任务
    3. 任务调度 - 分配任务给合适的Agent
    4. 结果整合 - 整合各Agent的返回结果
    """
    
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            name="调度中心",
            description="负责意图识别、任务分解和调度协调",
            processing_mode=ProcessingMode.COLLABORATIVE
        )
        
        # 路由器
        self.router: IntentRouter = get_intent_router()
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 注册表
        self.registry = get_registry()
        
        # 当前会话的任务列表
        self.current_tasks: Dict[str, List[TaskInfo]] = {}
        
        logger.info("[Orchestrator] Initialized")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.UNKNOWN  # Orchestrator处理所有意图
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理用户请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            更新状态的字典
        """
        user_input = self._get_latest_user_input(state)
        multimodal_data = state.get("multimodal_data")
        user_id = state.get("user_id", "default_user")
        session_id = state.get("session_id", str(uuid4()))
        
        self.log_info(f"Processing request: {user_input[:50]}...")
        
        # Step 1: 意图识别（支持多意图）
        intents, confidence, patterns = self.router.recognize_multi(user_input, multimodal_data)
        self.log_info(f"Recognized intents: {[i.value for i in intents]} (confidence: {confidence:.2f})")
        
        # Step 2: 任务分解（支持多意图）
        tasks = await self._decompose_tasks(user_input, intents, patterns)
        self.log_info(f"Decomposed {len(tasks)} tasks")
        
        # Step 3: 执行任务
        results = await self._execute_tasks(tasks, state)
        
        # Step 4: 整合结果
        final_result = self._integrate_results(results, intents)
        
        return {
            "current_intents": intents,
            "results": final_result,
            "tasks": {t["task_id"]: t for t in tasks}
        }
    
    def _get_latest_user_input(self, state: MultiAgentState) -> str:
        """获取最新用户输入"""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            # 检查消息内容
            content = None
            if isinstance(msg, dict):
                content = msg.get("content", "")
            elif hasattr(msg, "content"):
                content = msg.content
            
            if content and isinstance(content, str):
                return content
        return ""
    
    async def _decompose_tasks(
        self,
        user_input: str,
        intents: List[IntentType],
        patterns: List
    ) -> List[Dict[str, Any]]:
        """
        ✅ 重构：任务分解（支持多意图）
        
        将复杂任务分解为可执行的子任务，每个意图对应一个任务。
        """
        tasks = []
        agent_mapping = self.router.get_agent_mapping()
        
        # ✅ 为每个意图创建一个任务
        for intent in intents:
            if intent == IntentType.UNKNOWN or intent == IntentType.CONVERSATION:
                # 对话意图不需要专门任务
                continue
                
            task = TaskInfo(
                task_id=f"task-{uuid4().hex[:8]}",
                task_type=intent,
                description=user_input,
                status=TaskStatus.PENDING,
                assigned_agent=agent_mapping.get(intent),
                result=None,
                created_at=datetime.now(),
                completed_at=None,
                error=None
            )
            tasks.append(task)
            
            # ✅ 检查是否需要添加关联任务
            if intent == IntentType.LEARNING_PATH:
                # 生成学习计划后，添加推荐任务
                tasks.append(TaskInfo(
                    task_id=f"task-{uuid4().hex[:8]}",
                    task_type=IntentType.RECOMMENDATION,
                    description="根据学习路径生成推荐内容",
                    status=TaskStatus.PENDING,
                    assigned_agent="recommendation",
                    result=None,
                    created_at=datetime.now(),
                    completed_at=None,
                    error=None
                ))
            
            elif intent == IntentType.QUESTION:
                # 生成练习后，添加评估准备
                tasks.append(TaskInfo(
                    task_id=f"task-{uuid4().hex[:8]}",
                    task_type=IntentType.EVALUATION,
                    description="评估练习结果",
                    status=TaskStatus.PENDING,
                    assigned_agent="evaluation",
                    result=None,
                    created_at=datetime.now(),
                    completed_at=None,
                    error=None
                ))
        
        return tasks
    
    async def _decompose_task(
        self,
        user_input: str,
        intent: IntentType,
        patterns: List
    ) -> List[Dict[str, Any]]:
        """
        任务分解（兼容旧接口 - 单意图）
        """
        return await self._decompose_tasks(user_input, [intent], patterns)
    
    async def _execute_tasks(
        self,
        tasks: List[Dict[str, Any]],
        state: MultiAgentState
    ) -> List[Dict[str, Any]]:
        """
        执行任务
        
        根据任务类型和依赖关系执行任务。
        """
        results = []
        completed_agents = []
        
        for task in tasks:
            task_id = task["task_id"]
            task_type = task["task_type"]
            assigned_agent = task["assigned_agent"]
            
            self.log_info(f"Executing task {task_id}: {task_type.value} -> {assigned_agent}")
            
            # 更新任务状态
            task["status"] = TaskStatus.RUNNING
            
            try:
                # 获取Agent
                agent = self.registry.get(assigned_agent)
                
                if agent:
                    # 联邦式任务 - 并行执行
                    if agent.processing_mode == ProcessingMode.FEDERATED:
                        result = await agent.process(state)
                        task["result"] = result
                        task["status"] = TaskStatus.COMPLETED
                        task["completed_at"] = datetime.now()
                        completed_agents.append(assigned_agent)
                        results.append({
                            "task_id": task_id,
                            "agent": assigned_agent,
                            "success": True,
                            "result": result
                        })
                    
                    # 协作式任务 - 检查依赖
                    else:
                        dependencies = self.registry.get_dependencies(assigned_agent)
                        if all(dep in completed_agents for dep in dependencies):
                            result = await agent.process(state)
                            task["result"] = result
                            task["status"] = TaskStatus.COMPLETED
                            task["completed_at"] = datetime.now()
                            completed_agents.append(assigned_agent)
                            results.append({
                                "task_id": task_id,
                                "agent": assigned_agent,
                                "success": True,
                                "result": result
                            })
                        else:
                            # 等待依赖
                            missing = [d for d in dependencies if d not in completed_agents]
                            self.log_info(f"Waiting for dependencies: {missing}")
                            # 这里应该加入等待逻辑，暂时跳过
                            task["status"] = TaskStatus.PENDING
                else:
                    # Agent不存在，使用默认处理
                    result = await self._default_handler(task_type, state)
                    task["result"] = result
                    task["status"] = TaskStatus.COMPLETED
                    task["completed_at"] = datetime.now()
                    results.append({
                        "task_id": task_id,
                        "agent": "default",
                        "success": True,
                        "result": result
                    })
                    
            except Exception as e:
                self.log_error(f"Task {task_id} failed: {str(e)}")
                task["status"] = TaskStatus.FAILED
                task["error"] = str(e)
                results.append({
                    "task_id": task_id,
                    "agent": assigned_agent,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _default_handler(
        self,
        intent: IntentType,
        state: MultiAgentState
    ) -> Dict[str, Any]:
        """
        默认处理器
        
        当对应Agent不存在时使用。
        """
        self.log_info(f"Using default handler for {intent.value}")
        
        # 这里可以集成LLM来处理通用请求
        # 暂时返回简单的响应
        return {
            "success": True,
            "message": f"Handled {intent.value} request",
            "intent": intent.value
        }
    
    def _integrate_results(
        self,
        results: List[Dict[str, Any]],
        intents: List[IntentType]
    ) -> Dict[str, Any]:
        """
        ✅ 重构：整合结果（支持多意图）
        
        将多个Agent的结果整合为最终响应。
        """
        if not results:
            return {
                "success": False,
                "message": "No results to integrate"
            }
        
        # ✅ 收集所有消息
        messages = []
        agent_results = {}
        all_success = True
        
        for result in results:
            agent = result.get("agent", "unknown")
            agent_result = result.get("result", {})
            
            # ✅ 提取消息内容
            if isinstance(agent_result, dict):
                message = agent_result.get("message", "")
                if message:
                    messages.append({"agent": agent, "message": message})
                agent_results[agent] = agent_result
            elif isinstance(agent_result, str):
                messages.append({"agent": agent, "message": agent_result})
                agent_results[agent] = {"message": agent_result}
            
            if not result.get("success", True):
                all_success = False
        
        # ✅ 单结果直接返回
        if len(results) == 1:
            return {
                "success": all_success,
                "message": messages[0]["message"] if messages else "处理完成",
                "agent_results": agent_results
            }
        
        # ✅ 多结果整合 - 按意图优先级排序消息
        # 邮件意图放在最后，因为通常需要等待前置任务完成
        ordered_messages = []
        for msg in messages:
            if "email" not in msg["agent"].lower():
                ordered_messages.append(msg)
        for msg in messages:
            if "email" in msg["agent"].lower():
                ordered_messages.append(msg)
        
        # 构建最终消息
        final_message = ""
        for idx, msg in enumerate(ordered_messages):
            if idx > 0:
                final_message += "\n\n---\n\n"
            final_message += f"**[{msg['agent']}]**\n\n{msg['message']}"
        
        return {
            "success": all_success,
            "message": final_message,
            "primary_intents": [i.value for i in intents],
            "task_count": len(results),
            "agent_results": agent_results
        }
    
    async def route_to_agent(
        self,
        agent_id: str,
        task_data: Dict[str, Any],
        correlation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        路由任务到指定Agent
        
        Args:
            agent_id: Agent ID
            task_data: 任务数据
            correlation_id: 关联ID
            
        Returns:
            Agent执行结果
        """
        agent = self.registry.get(agent_id)
        
        if not agent:
            self.log_error(f"Agent not found: {agent_id}")
            return None
        
        # 发送任务消息
        message = AgentMessage(
            sender=self.agent_id,
            receiver=agent_id,
            message_type=MessageType.TASK,
            content=task_data,
            correlation_id=correlation_id
        )
        
        await self.message_bus.send(message)
        
        # 等待响应
        response = await self.message_bus.request_reply(message, timeout=60.0)
        
        if response:
            return response.content.get("result")
        
        return None
    
    def get_task_summary(self, tasks: List[Dict[str, Any]]) -> str:
        """获取任务摘要"""
        completed = sum(1 for t in tasks if t["status"] == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t["status"] == TaskStatus.FAILED)
        pending = sum(1 for t in tasks if t["status"] == TaskStatus.PENDING)
        
        return f"任务摘要: 完成{completed}/{len(tasks)}, 失败{failed}, 等待{pending}"


# 全局Orchestrator实例
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """获取全局Orchestrator实例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
