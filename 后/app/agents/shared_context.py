"""共享上下文 —— 跨 Agent 数据共享。

轻量版：用 dict + 命名空间管理跨 Agent 状态。
不需要参考系统的 Supabase 持久化——我们的数据已在 Neo4j/PostgreSQL。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SharedContext:
    """共享上下文（单例）。

    命名空间：
    - user_profiles: 用户画像（To C 用）
    - pipeline_cache: 批量 pipeline 中间结果
    - task_states: 任务状态跟踪
    - session_data: 会话临时数据
    """

    _instance: "SharedContext | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._data: dict[str, dict[str, Any]] = {
            "user_profiles": {},
            "pipeline_cache": {},
            "task_states": {},
            "session_data": {},
        }
        logger.info("[SharedContext] 初始化完成")

    # ── 通用 ──

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        return self._data.get(namespace, {}).get(key, default)

    def set(self, namespace: str, key: str, value: Any) -> None:
        if namespace not in self._data:
            self._data[namespace] = {}
        self._data[namespace][key] = value

    def delete(self, namespace: str, key: str) -> bool:
        if namespace in self._data and key in self._data[namespace]:
            del self._data[namespace][key]
            return True
        return False

    # ── Pipeline 缓存（批量处理的中间结果） ──

    def cache_pipeline(self, key: str, value: Any) -> None:
        self.set("pipeline_cache", key, {
            "value": value,
            "cached_at": datetime.now().isoformat(),
        })

    def get_pipeline_cache(self, key: str) -> Any:
        entry = self.get("pipeline_cache", key)
        return entry["value"] if entry else None

    # ── 任务状态 ──

    def set_task_state(self, task_id: str, state: dict) -> None:
        self.set("task_states", task_id, {
            **state,
            "updated_at": datetime.now().isoformat(),
        })

    def get_task_state(self, task_id: str) -> dict | None:
        return self.get("task_states", task_id)

    # ── 会话 ──

    def set_session(self, session_id: str, key: str, value: Any) -> None:
        self.set("session_data", f"{session_id}.{key}", value)

    def get_session(self, session_id: str, key: str) -> Any:
        return self.get("session_data", f"{session_id}.{key}")

    def clear_session(self, session_id: str) -> None:
        prefix = f"{session_id}."
        keys = [k for k in self._data["session_data"] if k.startswith(prefix)]
        for k in keys:
            del self._data["session_data"][k]

    def reset(self):
        for ns in self._data:
            self._data[ns].clear()
        logger.info("[SharedContext] 已重置")


# 全局单例
_context: SharedContext | None = None


def get_shared_context() -> SharedContext:
    global _context
    if _context is None:
        _context = SharedContext()
    return _context
