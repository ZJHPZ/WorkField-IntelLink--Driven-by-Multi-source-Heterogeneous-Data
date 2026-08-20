"""Agent 消息定义 —— 轻量版。

与参考系统不同，我们的 Agent 主要通过 SharedContext 通信。
Message 仅用于辩论模式中的正反方结构化交互。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    TASK = "task"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Agent 间通信消息。"""
    sender: str
    receiver: str
    message_type: MessageType = MessageType.TASK
    content: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def create_task(cls, sender: str, receiver: str, task_type: str,
                    task_data: dict, correlation_id: str = "") -> "AgentMessage":
        return cls(
            sender=sender, receiver=receiver,
            message_type=MessageType.TASK,
            content={"task_type": task_type, "task_data": task_data},
            correlation_id=correlation_id,
        )

    @classmethod
    def create_response(cls, sender: str, receiver: str, result: Any,
                        correlation_id: str, success: bool = True) -> "AgentMessage":
        return cls(
            sender=sender, receiver=receiver,
            message_type=MessageType.RESPONSE,
            content={"success": success, "result": result},
            correlation_id=correlation_id,
        )
