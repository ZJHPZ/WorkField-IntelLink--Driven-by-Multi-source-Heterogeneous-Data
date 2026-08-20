"""
Communication Module
通信模块 - Agent间通信机制
"""

from .message_bus import MessageBus, get_message_bus
from .shared_context import SharedContext, get_shared_context

__all__ = [
    "MessageBus",
    "get_message_bus",
    "SharedContext",
    "get_shared_context",
]
