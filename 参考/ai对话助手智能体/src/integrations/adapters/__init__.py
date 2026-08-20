"""
LLM 适配器模块

所有模型适配器需继承自 BaseLLMAdapter
"""

from .base_adapter import BaseLLMAdapter

# 动态导入子适配器
try:
    from .doubao_adapter import DoubaoAdapter
except ImportError:
    DoubaoAdapter = None

try:
    from .xunfei_adapter import XunfeiAdapter
except ImportError:
    XunfeiAdapter = None

try:
    from .coze_adapter import CozeAdapter
except ImportError:
    CozeAdapter = None

__all__ = [
    "BaseLLMAdapter",
    "DoubaoAdapter",
    "XunfeiAdapter",
    "CozeAdapter",
]
