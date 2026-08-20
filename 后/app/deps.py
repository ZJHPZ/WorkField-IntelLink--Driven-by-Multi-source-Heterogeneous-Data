"""依赖注入 —— FastAPI Depends() 使用的工厂函数。"""

from __future__ import annotations

from app.config import Settings, get_settings


def get_settings_dep() -> Settings:
    """注入 Settings（单例）。"""
    return get_settings()
