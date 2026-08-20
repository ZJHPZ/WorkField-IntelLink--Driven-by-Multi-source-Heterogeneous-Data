"""
Message Bus
消息总线 - Agent间异步通信机制
增强版：支持消息历史持久化
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from ..base.message import AgentMessage, MessageType
from ..base.agent_state import MultiAgentState

logger = logging.getLogger(__name__)


class MessagePersistence:
    """
    消息持久化管理器
    负责将消息历史保存到数据库，支持服务重启后恢复
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._client = None
        self._table_name = "multi_agent_messages"
        self._batch_size = 10
        self._pending_messages: List[Dict] = []
        self._persist_enabled = False
        
        # 尝试初始化数据库连接
        self._init_persistence()
    
    def _init_persistence(self):
        """初始化持久化"""
        try:
            from storage.database.supabase_client import get_supabase_client
            self._client = get_supabase_client()
            self._persist_enabled = True
            logger.info("[MessagePersistence] Database persistence enabled")
        except Exception as e:
            logger.warning(f"[MessagePersistence] Failed to init persistence: {e}, will use memory only")
            self._persist_enabled = False
    
    def save_message(self, message: AgentMessage) -> bool:
        """保存单条消息"""
        if not self._persist_enabled:
            return False
        
        try:
            message_dict = {
                "sender": message.sender,
                "receiver": message.receiver,
                "message_type": message.message_type,
                "content": json.dumps(message.content, ensure_ascii=False),
                "correlation_id": message.correlation_id,
                "priority": message.priority,
                "created_at": message.timestamp.isoformat()
            }
            
            # 批量保存
            self._pending_messages.append(message_dict)
            if len(self._pending_messages) >= self._batch_size:
                self._flush()
            
            return True
        except Exception as e:
            logger.error(f"[MessagePersistence] Failed to save message: {e}")
            return False
    
    def _flush(self):
        """批量保存待处理的消息"""
        if not self._pending_messages:
            return
        
        try:
            self._client.table(self._table_name).insert(self._pending_messages).execute()
            self._pending_messages.clear()
            logger.debug(f"[MessagePersistence] Flushed {self._batch_size} messages")
        except Exception as e:
            logger.error(f"[MessagePersistence] Failed to flush messages: {e}")
    
    def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """获取消息历史"""
        if not self._persist_enabled:
            return []
        
        try:
            response = self._client.table(self._table_name) \
                .select("*") \
                .eq("correlation_id", session_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .offset(offset) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"[MessagePersistence] Failed to get messages: {e}")
            return []
    
    def close(self):
        """关闭时保存剩余消息"""
        self._flush()


class MessageBus:
    """
    消息总线
    
    负责Agent间的消息传递，采用发布-订阅模式。
    支持：
    - 点对点消息
    - 广播消息
    - 消息订阅/退订
    - 消息追踪
    - 消息持久化（✅ 新增）
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
        
        # 消息队列
        self._queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        
        # 订阅者映射
        self._subscribers: Dict[str, List[str]] = defaultdict(list)
        
        # 消息历史
        self._history: List[AgentMessage] = []
        self._max_history = 1000
        
        # 等待回复的Future
        self._pending_replies: Dict[str, asyncio.Future] = {}
        
        # 消息回调
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # 统计信息
        self._stats = {
            "sent": 0,
            "received": 0,
            "broadcast": 0
        }
        
        # ✅ 持久化管理器
        self._persistence = MessagePersistence()
        
        logger.info("[MessageBus] Initialized with persistence support")
    
    async def send(self, message: AgentMessage) -> bool:
        """
        发送消息
        
        Args:
            message: 消息对象
            
        Returns:
            是否发送成功
        """
        try:
            # 放入接收者队列
            queue = self._queues[message.receiver]
            await queue.put(message)
            
            # 更新历史
            self._history.append(message)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            # ✅ 持久化消息
            self._persistence.save_message(message)
            
            # 更新统计
            self._stats["sent"] += 1
            
            # 触发回调
            await self._trigger_callbacks(message)
            
            logger.debug(
                f"[MessageBus] Message sent: {message.sender} -> {message.receiver}, "
                f"type={message.message_type}, id={message.correlation_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[MessageBus] Failed to send message: {e}")
            return False
    
    async def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        接收消息
        
        Args:
            agent_id: Agent ID
            timeout: 超时时间（秒）
            
        Returns:
            消息对象，超时返回None
        """
        try:
            queue = self._queues[agent_id]
            
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()
            
            # 更新统计
            self._stats["received"] += 1
            
            logger.debug(
                f"[MessageBus] Message received: {message.sender} -> {agent_id}, "
                f"type={message.message_type}"
            )
            
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"[MessageBus] Failed to receive message: {e}")
            return None
    
    async def broadcast(self, message: AgentMessage, target_agents: List[str]) -> int:
        """
        广播消息给多个Agent
        
        Args:
            message: 消息对象
            target_agents: 目标Agent列表
            
        Returns:
            成功发送数量
        """
        success_count = 0
        for agent_id in target_agents:
            msg = AgentMessage(
                sender=message.sender,
                receiver=agent_id,
                message_type=message.message_type,
                content=message.content.copy(),
                timestamp=datetime.now(),
                correlation_id=f"{message.correlation_id}-broadcast-{uuid4().hex[:4]}",
                priority=message.priority
            )
            if await self.send(msg):
                success_count += 1
        
        self._stats["broadcast"] += success_count
        logger.info(
            f"[MessageBus] Broadcast: {message.sender} -> {target_agents}, "
            f"success={success_count}/{len(target_agents)}"
        )
        
        return success_count
    
    def subscribe(self, agent_id: str, event_type: Optional[str] = None) -> None:
        """
        订阅消息
        
        Args:
            agent_id: Agent ID
            event_type: 事件类型，None表示接收所有消息
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if agent_id not in self._subscribers[event_type]:
            self._subscribers[event_type].append(agent_id)
            logger.debug(f"[MessageBus] Agent {agent_id} subscribed to {event_type or 'all'}")
    
    def unsubscribe(self, agent_id: str, event_type: Optional[str] = None) -> None:
        """退订消息"""
        if event_type in self._subscribers and agent_id in self._subscribers[event_type]:
            self._subscribers[event_type].remove(agent_id)
            logger.debug(f"[MessageBus] Agent {agent_id} unsubscribed from {event_type or 'all'}")
    
    async def request_reply(
        self,
        message: AgentMessage,
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """
        发送请求并等待回复
        
        Args:
            message: 消息对象
            timeout: 超时时间
            
        Returns:
            回复消息
        """
        correlation_id = message.correlation_id
        
        # 创建Future等待回复
        future = asyncio.Future()
        self._pending_replies[correlation_id] = future
        
        try:
            # 发送消息
            await self.send(message)
            
            # 等待回复
            reply = await asyncio.wait_for(future, timeout=timeout)
            return reply
            
        except asyncio.TimeoutError:
            logger.warning(f"[MessageBus] Request timeout: {correlation_id}")
            return None
        finally:
            self._pending_replies.pop(correlation_id, None)
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """添加消息回调"""
        self._callbacks[event_type].append(callback)
    
    async def _trigger_callbacks(self, message: AgentMessage) -> None:
        """触发消息回调"""
        # 触发特定类型回调
        if message.message_type in self._callbacks:
            for callback in self._callbacks[message.message_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"[MessageBus] Callback error: {e}")
        
        # 触发全局回调
        if None in self._callbacks:
            for callback in self._callbacks[None]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"[MessageBus] Global callback error: {e}")
    
    def get_history(
        self,
        sender: Optional[str] = None,
        receiver: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100
    ) -> List[AgentMessage]:
        """获取消息历史"""
        results = self._history
        
        if sender:
            results = [m for m in results if m.sender == sender]
        if receiver:
            results = [m for m in results if m.receiver == receiver]
        if message_type:
            results = [m for m in results if m.message_type == message_type]
        
        return results[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return dict(self._stats)
    
    def get_all_subscribers(self) -> List[str]:
        """获取所有订阅者"""
        return list(self._subscribers.keys())
    
    def clear_history(self) -> None:
        """清空消息历史"""
        self._history.clear()
        logger.info("[MessageBus] History cleared")
    
    def reset(self) -> None:
        """重置消息总线"""
        self._queues.clear()
        self._subscribers.clear()
        self._history.clear()
        self._pending_replies.clear()
        self._callbacks.clear()
        self._stats = {"sent": 0, "received": 0, "broadcast": 0}
        logger.info("[MessageBus] Reset")
    
    async def _checkpoint(self) -> bool:
        """
        持久化当前状态（调用 MessagePersistence）
        
        Returns:
            是否持久化成功
        """
        try:
            # 将当前内存中的消息保存到数据库
            for msg in self._history:
                self._persistence.save_message(msg)
            
            # 刷新待处理消息
            self._persistence._flush()
            
            logger.info(f"[MessageBus] Checkpoint completed, {len(self._history)} messages saved")
            return True
        except Exception as e:
            logger.error(f"[MessageBus] Checkpoint failed: {e}")
            return False
    
    async def _restore(self, session_id: Optional[str] = None) -> bool:
        """
        从持久化中恢复状态
        
        Args:
            session_id: 会话 ID，如果为 None 则恢复所有消息
            
        Returns:
            是否恢复成功
        """
        try:
            messages = self._persistence.get_messages(session_id or "default", limit=self._max_history)
            
            # 恢复消息历史
            for msg_data in reversed(messages):
                msg = AgentMessage(
                    sender=msg_data["sender"],
                    receiver=msg_data["receiver"],
                    message_type=MessageType(msg_data["message_type"]),
                    content=json.loads(msg_data["content"]),
                    correlation_id=msg_data["correlation_id"]
                )
                self._history.append(msg)
            
            logger.info(f"[MessageBus] Restore completed, {len(messages)} messages restored")
            return True
        except Exception as e:
            logger.error(f"[MessageBus] Restore failed: {e}")
            return False


# 全局实例
_global_message_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """获取全局消息总线实例"""
    global _global_message_bus
    if _global_message_bus is None:
        _global_message_bus = MessageBus()
    return _global_message_bus
