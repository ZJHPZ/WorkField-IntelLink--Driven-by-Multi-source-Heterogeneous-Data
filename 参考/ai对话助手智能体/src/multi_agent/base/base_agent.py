"""
Base Agent Class
Agent基类 - 所有Agent的抽象基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type
from datetime import datetime
from uuid import uuid4

from .agent_state import MultiAgentState, IntentType, TaskStatus, ProcessingMode
from .message import AgentMessage, MessageType, TaskMessage, ResponseMessage

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Agent基类
    
    所有具体的Agent都应该继承此类并实现process方法。
    提供了基础的Agent功能：
    - 消息发送/接收
    - 任务状态管理
    - 日志记录
    - 上下文访问
    """
    
    # 类级别的Agent注册表
    _registry: Dict[str, Type["BaseAgent"]] = {}
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        processing_mode: ProcessingMode = ProcessingMode.FEDERATED
    ):
        """
        初始化Agent
        
        Args:
            agent_id: Agent唯一标识
            name: Agent名称
            description: Agent描述
            processing_mode: 处理模式（联邦式/协作式）
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.processing_mode = processing_mode
        
        # 工具列表
        self.tools: List[Any] = []
        
        # 依赖的Agent
        self.dependencies: List[str] = []
        
        # 初始化时间
        self.created_at = datetime.now()
        
        # 注册到全局表
        self._register()
        
        logger.info(f"[{self.agent_id}] Agent '{self.name}' initialized")
    
    def _register(self):
        """注册Agent到类级别注册表"""
        if self.agent_id in self._registry:
            logger.warning(f"[{self.agent_id}] Agent ID already registered, overwriting")
        self._registry[self.agent_id] = self.__class__
    
    @classmethod
    def get_registered_agents(cls) -> Dict[str, Type["BaseAgent"]]:
        """获取所有注册的Agent"""
        return dict(cls._registry)
    
    @property
    @abstractmethod
    def intent_type(self) -> IntentType:
        """返回该Agent处理的意图类型"""
        pass
    
    @abstractmethod
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理任务的抽象方法
        
        Args:
            state: 当前系统状态
            
        Returns:
            更新状态的字典
        """
        pass
    
    def get_tools(self) -> List[Any]:
        """获取Agent可用的工具列表"""
        return self.tools
    
    def add_tool(self, tool: Any):
        """添加工具到Agent"""
        self.tools.append(tool)
        logger.debug(f"[{self.agent_id}] Added tool: {tool}")
    
    def set_dependencies(self, dependencies: List[str]):
        """设置依赖的Agent列表"""
        self.dependencies = dependencies
        logger.debug(f"[{self.agent_id}] Set dependencies: {dependencies}")
    
    def can_process(self, intent: IntentType) -> bool:
        """检查Agent是否能处理指定意图"""
        return self.intent_type == intent
    
    def create_task_id(self) -> str:
        """生成唯一任务ID"""
        return f"{self.agent_id}-{uuid4().hex[:8]}"
    
    def prepare_result(
        self,
        success: bool = True,
        data: Any = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """准备标准格式的返回结果"""
        return {
            "success": success,
            "agent_id": self.agent_id,
            "data": data,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        logger.info(f"[{self.agent_id}] {message}", extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """记录错误日志"""
        logger.error(f"[{self.agent_id}] {message}", extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        logger.debug(f"[{self.agent_id}] {message}", extra=kwargs)
    
    async def send_to_agent(
        self,
        target_agent_id: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送消息给其他Agent（协作式Agent使用）
        
        Args:
            target_agent_id: 目标Agent ID
            message: 消息内容
            data: 附加数据
            
        Returns:
            发送结果
        """
        # 这个方法会在MultiAgentSystem中被调用
        # 协作式Agent使用此方法与其他Agent通信
        self.log_info(f"Sending message to {target_agent_id}: {message}")
        return {
            "success": True,
            "target": target_agent_id,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.agent_id}', name='{self.name}')>"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.agent_id})"


class FederatedAgent(BaseAgent):
    """
    联邦式Agent基类
    
    适用于独立执行任务的Agent，不需要等待其他Agent完成。
    """
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            processing_mode=ProcessingMode.FEDERATED
        )


class CollaborativeAgent(BaseAgent):
    """
    协作式Agent基类
    
    适用于需要依赖其他Agent结果的Agent。
    """
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            processing_mode=ProcessingMode.COLLABORATIVE
        )
        
        # 协作回调函数映射
        self._callbacks: Dict[str, Callable] = {}
    
    def register_callback(self, agent_id: str, callback: Callable) -> None:
        """注册协作回调函数"""
        self._callbacks[agent_id] = callback
        logger.debug(f"[{self.agent_id}] Registered callback for {agent_id}")
    
    def get_callback(self, agent_id: str) -> Optional[Callable]:
        """获取指定Agent的回调函数"""
        return self._callbacks.get(agent_id)
    
    def requires_results_from(self, agent_ids: List[str]) -> bool:
        """检查是否需要等待某些Agent的结果"""
        return bool(set(self.dependencies) & set(agent_ids))
