"""
LLM 工厂

支持多模型接入，通过配置切换不同模型
"""

import logging
from typing import Any, Dict, Optional, Type

from .adapters.base_adapter import BaseLLMAdapter
from .adapters.doubao_adapter import DoubaoAdapter
from .adapters.xunfei_adapter import XunfeiAdapter

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    LLM 工厂类

    根据配置创建对应的 LLM 适配器
    """

    # 支持的适配器注册表
    ADAPTERS = {
        "doubao": DoubaoAdapter,
        "xunfei": XunfeiAdapter,
    }

    # 别名映射
    ALIASES = {
        "spark": "xunfei",
        "volcengine": "doubao",
        "火山": "doubao",
        "讯飞": "xunfei",
        "豆包": "doubao",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工厂

        Args:
            config: 工厂配置
        """
        self.config = config or {}
        self._adapter_cache: Dict[str, BaseLLMAdapter] = {}

    @classmethod
    def create(
        cls,
        provider: str,
        model_config: Dict[str, Any],
        ctx: Optional[Any] = None
    ) -> BaseLLMAdapter:
        """
        创建 LLM 适配器

        Args:
            provider: 提供商名称 (doubao, xunfei)
            model_config: 模型配置
            ctx: 请求上下文 (可选)

        Returns:
            LLM 适配器实例
        """
        # 解析别名
        provider = cls.ALIASES.get(provider, provider)

        # 获取适配器类
        adapter_class = cls.ADAPTERS.get(provider)
        if not adapter_class:
            raise ValueError(
                f"不支持的 LLM 提供商: {provider}\n"
                f"支持的提供商: {list(cls.ADAPTERS.keys())}"
            )

        # 添加 ctx 到配置
        if ctx:
            model_config["ctx"] = ctx

        # 创建适配器
        try:
            adapter = adapter_class(model_config)
            logger.info(f"成功创建 LLM 适配器: {provider} ({adapter.get_model_name()})")
            return adapter
        except Exception as e:
            logger.error(f"创建 LLM 适配器失败: {provider}, 错误: {e}")
            raise

    @classmethod
    def create_from_config(
        cls,
        config_path: str = "config/agent_llm_config.json",
        ctx: Optional[Any] = None
    ) -> BaseLLMAdapter:
        """
        从配置文件创建 LLM 适配器

        Args:
            config_path: 配置文件路径
            ctx: 请求上下文 (可选)

        Returns:
            LLM 适配器实例
        """
        import json
        import os

        # 读取配置
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        full_path = os.path.join(workspace_path, config_path)

        with open(full_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 获取 provider
        llm_config = config.get("config", {})
        provider = llm_config.get("provider", "doubao")

        # 创建适配器
        return cls.create(provider, llm_config, ctx=ctx)

    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[BaseLLMAdapter]):
        """
        注册新的适配器

        Args:
            name: 适配器名称
            adapter_class: 适配器类
        """
        if not issubclass(adapter_class, BaseLLMAdapter):
            raise ValueError("适配器必须继承自 BaseLLMAdapter")

        cls.ADAPTERS[name] = adapter_class
        logger.info(f"已注册 LLM 适配器: {name}")

    @classmethod
    def list_adapters(cls) -> list:
        """
        列出所有已注册的适配器

        Returns:
            适配器名称列表
        """
        return list(cls.ADAPTERS.keys())

    @classmethod
    def is_available(cls, provider: str) -> bool:
        """
        检查适配器是否可用

        Args:
            provider: 提供商名称

        Returns:
            是否可用
        """
        provider = cls.ALIASES.get(provider, provider)
        return provider in cls.ADAPTERS


# 全局工厂实例
_factory_instance: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """
    获取全局 LLM 工厂实例

    Returns:
        LLMFactory 实例
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = LLMFactory()
    return _factory_instance


def create_llm(
    provider: str = "doubao",
    config: Optional[Dict[str, Any]] = None,
    ctx: Optional[Any] = None
) -> BaseLLMAdapter:
    """
    快捷函数：创建 LLM 适配器

    Args:
        provider: 提供商名称
        config: 模型配置
        ctx: 请求上下文

    Returns:
        LLM 适配器实例
    """
    return LLMFactory.create(provider, config or {}, ctx=ctx)


def create_llm_from_config(
    config_path: str = "config/agent_llm_config.json",
    ctx: Optional[Any] = None
) -> BaseLLMAdapter:
    """
    快捷函数：从配置文件创建 LLM 适配器

    Args:
        config_path: 配置文件路径
        ctx: 请求上下文

    Returns:
        LLM 适配器实例
    """
    return LLMFactory.create_from_config(config_path, ctx=ctx)


# ==================== 讯飞 + Coze 智能路由 ====================

def create_hybrid_llm(config: Optional[Dict[str, Any]] = None) -> Any:
    """
    创建混合 LLM 实例（讯飞 + Coze）

    讯飞用于纯对话，Coze 用于工具调用

    Args:
        config: 配置信息
            - xunfei: 讯飞配置
            - coze: Coze 配置

    Returns:
        SmartRouter 实例
    """
    from .smart_router import SmartRouter

    return SmartRouter(config)


def create_from_provider(
    provider: str,
    config: Optional[Dict[str, Any]] = None,
    ctx: Optional[Any] = None
) -> BaseLLMAdapter:
    """
    根据 provider 创建对应的适配器

    支持的 provider:
    - doubao: 豆包模型
    - xunfei: 讯飞大模型
    - coze: Coze 平台

    Args:
        provider: 提供商名称
        config: 配置信息
        ctx: 请求上下文

    Returns:
        LLM 适配器实例
    """
    from .adapters.coze_adapter import CozeAdapter

    # 注册 Coze 适配器
    if "coze" not in LLMFactory.ADAPTERS:
        LLMFactory.register_adapter("coze", CozeAdapter)

    return LLMFactory.create(provider, config or {}, ctx=ctx)
