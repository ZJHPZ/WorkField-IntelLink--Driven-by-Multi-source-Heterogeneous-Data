"""
Agent Registry - Agent注册表
管理所有Agent的注册和获取
"""
import logging
from typing import Dict, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent注册表
    
    负责：
    1. 注册Agent实例
    2. 获取Agent实例
    3. 列出所有Agent
    4. 检查Agent是否存在
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        logger.info("[AgentRegistry] Initialized")
    
    def register(self, agent_id: str, agent: BaseAgent) -> bool:
        """
        注册Agent
        
        Args:
            agent_id: Agent唯一标识
            agent: Agent实例
            
        Returns:
            是否注册成功
        """
        if agent_id in self._agents:
            logger.warning(f"[AgentRegistry] Agent {agent_id} already registered, overwriting")
        
        self._agents[agent_id] = agent
        logger.info(f"[AgentRegistry] Registered agent: {agent_id}")
        return True
    
    def unregister(self, agent_id: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            是否注销成功
        """
        if agent_id not in self._agents:
            logger.warning(f"[AgentRegistry] Agent {agent_id} not found")
            return False
        
        del self._agents[agent_id]
        logger.info(f"[AgentRegistry] Unregistered agent: {agent_id}")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        获取Agent实例
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            Agent实例，如果不存在返回None
        """
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning(f"[AgentRegistry] Agent {agent_id} not found")
        return agent
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """
        获取所有Agent
        
        Returns:
            所有Agent的字典
        """
        return self._agents.copy()
    
    def list_agent_ids(self) -> List[str]:
        """
        列出所有Agent ID
        
        Returns:
            Agent ID列表
        """
        return list(self._agents.keys())
    
    def has_agent(self, agent_id: str) -> bool:
        """
        检查Agent是否存在
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            是否存在
        """
        return agent_id in self._agents
    
    def get_agent_count(self) -> int:
        """
        获取Agent数量
        
        Returns:
            Agent数量
        """
        return len(self._agents)
    
    def clear(self):
        """清空所有Agent"""
        self._agents.clear()
        logger.info("[AgentRegistry] Cleared all agents")


# 全局实例
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """获取全局Agent注册表"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
