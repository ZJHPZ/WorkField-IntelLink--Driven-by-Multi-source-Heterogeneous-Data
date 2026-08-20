"""
Multi-Agent Registry
多智能体注册表 - 管理所有Agent实例
"""

import logging
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

from .base.base_agent import BaseAgent, FederatedAgent, CollaborativeAgent
from .base.agent_state import IntentType, MultiAgentState, ProcessingMode

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent注册表
    
    负责：
    - 注册和获取Agent实例
    - Agent实例的生命周期管理
    - Agent间关系维护
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Agent实例存储
        self._agents: Dict[str, BaseAgent] = {}
        
        # 意图类型到Agent的映射
        self._intent_map: Dict[IntentType, str] = {}
        
        # Agent依赖关系图
        self._dependency_graph: Dict[str, List[str]] = {}
        
        logger.info("[Registry] AgentRegistry initialized")
    
    def register(self, agent: BaseAgent) -> None:
        """
        注册Agent实例
        
        Args:
            agent: Agent实例
        """
        if agent.agent_id in self._agents:
            logger.warning(f"[Registry] Agent {agent.agent_id} already registered")
            return
        
        self._agents[agent.agent_id] = agent
        self._intent_map[agent.intent_type] = agent.agent_id
        
        logger.info(f"[Registry] Registered agent: {agent.agent_id} ({agent.name})")
    
    def unregister(self, agent_id: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功注销
        """
        if agent_id not in self._agents:
            return False
        
        agent = self._agents.pop(agent_id)
        self._intent_map.pop(agent.intent_type, None)
        logger.info(f"[Registry] Unregistered agent: {agent_id}")
        return True
    
    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent实例"""
        return self._agents.get(agent_id)
    
    def get_by_intent(self, intent: IntentType) -> Optional[BaseAgent]:
        """根据意图类型获取Agent"""
        agent_id = self._intent_map.get(intent)
        return self._agents.get(agent_id) if agent_id else None
    
    def get_all(self) -> Dict[str, BaseAgent]:
        """获取所有Agent"""
        return dict(self._agents)
    
    def get_federated_agents(self) -> List[BaseAgent]:
        """获取所有联邦式Agent"""
        return [
            agent for agent in self._agents.values()
            if agent.processing_mode == ProcessingMode.FEDERATED
        ]
    
    def get_collaborative_agents(self) -> List[BaseAgent]:
        """获取所有协作式Agent"""
        return [
            agent for agent in self._agents.values()
            if agent.processing_mode == ProcessingMode.COLLABORATIVE
        ]
    
    def get_dependencies(self, agent_id: str) -> List[str]:
        """获取Agent的依赖列表"""
        return self._dependency_graph.get(agent_id, [])
    
    def set_dependencies(self, agent_id: str, dependencies: List[str]) -> None:
        """设置Agent的依赖关系"""
        self._dependency_graph[agent_id] = dependencies
        agent = self.get(agent_id)
        if agent:
            agent.set_dependencies(dependencies)
        logger.debug(f"[Registry] Set dependencies for {agent_id}: {dependencies}")
    
    def add_dependency(self, agent_id: str, dependency: str) -> None:
        """添加单个依赖关系"""
        if agent_id not in self._dependency_graph:
            self._dependency_graph[agent_id] = []
        if dependency not in self._dependency_graph[agent_id]:
            self._dependency_graph[agent_id].append(dependency)
    
    def get_dependents(self, agent_id: str) -> List[str]:
        """获取依赖指定Agent的所有Agent"""
        return [
            aid for aid, deps in self._dependency_graph.items()
            if agent_id in deps
        ]
    
    def can_execute(self, agent_id: str, completed_agents: List[str]) -> bool:
        """
        检查Agent是否可以执行
        
        Args:
            agent_id: Agent ID
            completed_agents: 已完成的Agent列表
            
        Returns:
            是否可以执行
        """
        dependencies = self.get_dependencies(agent_id)
        return all(dep in completed_agents for dep in dependencies)
    
    def get_executable_agents(
        self,
        pending_agents: List[str],
        completed_agents: List[str]
    ) -> List[str]:
        """
        获取可执行的Agent列表
        
        Args:
            pending_agents: 待执行的Agent列表
            completed_agents: 已完成的Agent列表
            
        Returns:
            可执行的Agent列表
        """
        return [
            agent_id for agent_id in pending_agents
            if self.can_execute(agent_id, completed_agents)
        ]
    
    def get_intent_to_agent_map(self) -> Dict[str, str]:
        """获取意图到Agent的映射（用于日志）"""
        return {
            intent.value: agent_id
            for intent, agent_id in self._intent_map.items()
        }
    
    def reset(self) -> None:
        """重置注册表"""
        self._agents.clear()
        self._intent_map.clear()
        self._dependency_graph.clear()
        logger.info("[Registry] Registry reset")


# 全局实例
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """获取全局Agent注册表实例"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(agent: BaseAgent) -> None:
    """快捷函数：注册Agent"""
    get_registry().register(agent)


def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """快捷函数：获取Agent"""
    return get_registry().get(agent_id)


def get_agents_by_intent(intent: IntentType) -> Optional[BaseAgent]:
    """快捷函数：根据意图获取Agent"""
    return get_registry().get_by_intent(intent)
