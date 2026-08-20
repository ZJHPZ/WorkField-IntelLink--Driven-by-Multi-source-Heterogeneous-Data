"""
Integrations 模块

支持多模型接入的适配器架构：
- 豆包模型 (Doubao)
- 讯飞大模型 (Xunfei)
"""

from .llm_factory import LLMFactory, get_llm_factory

__all__ = ["LLMFactory", "get_llm_factory"]
