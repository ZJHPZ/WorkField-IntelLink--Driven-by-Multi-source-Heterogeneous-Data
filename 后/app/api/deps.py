"""API 共享依赖 —— 单例 Agent 系统，确保全 API 走 LLM 路径。"""
from app.agents.system import MultiAgentSystem, get_system
from app.utils.spark import SparkClient

_llm_client = None
_system = None


def get_llm_client():
    """延迟初始化星火客户端（单例）。"""
    global _llm_client
    if _llm_client is None:
        try:
            _llm_client = SparkClient()
        except Exception:
            _llm_client = False  # 标记失败，不回退重试
    return _llm_client if _llm_client is not False else None


def get_api_system() -> MultiAgentSystem:
    """获取已初始化 LLM 的 Agent 系统（单例）。"""
    global _system
    if _system is None:
        client = get_llm_client()
        _system = get_system().initialize(llm_client=client)
    return _system
