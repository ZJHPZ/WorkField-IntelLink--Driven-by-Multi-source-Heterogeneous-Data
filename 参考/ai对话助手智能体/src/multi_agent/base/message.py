"""
Agent Message Definitions
Agent消息定义
"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举"""
    TASK = "task"              # 任务分配
    REQUEST = "request"        # 数据请求
    RESPONSE = "response"      # 响应结果
    NOTIFICATION = "notification"  # 状态通知
    ERROR = "error"            # 错误信息


class Priority(int, Enum):
    """消息优先级"""
    LOW = 5
    NORMAL = 3
    HIGH = 1
    CRITICAL = 0


class AgentMessage(BaseModel):
    """
    Agent间通信消息
    
    属性:
        sender: 发送者ID
        receiver: 接收者ID
        message_type: 消息类型
        content: 消息内容
        timestamp: 时间戳
        correlation_id: 关联ID (用于追踪)
        priority: 优先级
    """
    sender: str = Field(..., description="发送者Agent ID")
    receiver: str = Field(..., description="接收者Agent ID")
    message_type: MessageType = Field(..., description="消息类型")
    content: Dict[str, Any] = Field(default_factory=dict, description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    correlation_id: str = Field(..., description="关联ID，用于追踪请求")
    priority: Priority = Field(default=Priority.NORMAL, description="优先级")
    reply_to: Optional[str] = Field(None, description="回复目标消息ID")

    class Config:
        use_enum_values = True


class TaskMessage(AgentMessage):
    """任务分配消息"""
    
    @classmethod
    def create_task(
        cls,
        sender: str,
        receiver: str,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any],
        correlation_id: str
    ) -> "TaskMessage":
        """创建任务消息"""
        return cls(
            sender=sender,
            receiver=receiver,
            message_type=MessageType.TASK,
            content={
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data
            },
            correlation_id=correlation_id,
            priority=Priority.HIGH
        )


class ResponseMessage(AgentMessage):
    """响应消息"""
    
    @classmethod
    def create_response(
        cls,
        sender: str,
        receiver: str,
        result: Any,
        correlation_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> "ResponseMessage":
        """创建响应消息"""
        return cls(
            sender=sender,
            receiver=receiver,
            message_type=MessageType.RESPONSE,
            content={
                "success": success,
                "result": result,
                "error": error
            },
            correlation_id=correlation_id,
            priority=Priority.NORMAL
        )


class RequestMessage(AgentMessage):
    """数据请求消息"""
    
    @classmethod
    def create_request(
        cls,
        sender: str,
        receiver: str,
        data_type: str,
        query: Dict[str, Any],
        correlation_id: str
    ) -> "RequestMessage":
        """创建请求消息"""
        return cls(
            sender=sender,
            receiver=receiver,
            message_type=MessageType.REQUEST,
            content={
                "data_type": data_type,
                "query": query
            },
            correlation_id=correlation_id,
            priority=Priority.NORMAL
        )


class NotificationMessage(AgentMessage):
    """状态通知消息"""
    
    @classmethod
    def create_notification(
        cls,
        sender: str,
        receivers: list[str],
        notification_type: str,
        data: Dict[str, Any],
        correlation_id: str
    ) -> list["NotificationMessage"]:
        """创建通知消息（可发送给多个接收者）"""
        return [
            cls(
                sender=sender,
                receiver=receiver,
                message_type=MessageType.NOTIFICATION,
                content={
                    "notification_type": notification_type,
                    "data": data
                },
                correlation_id=correlation_id,
                priority=Priority.LOW
            )
            for receiver in receivers
        ]
