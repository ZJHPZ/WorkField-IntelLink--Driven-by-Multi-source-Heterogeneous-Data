"""
Shared Context
共享上下文 - 跨Agent数据共享
增强版：支持上下文持久化
"""

import logging
import asyncio
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime
from uuid import uuid4
import json

logger = logging.getLogger(__name__)


class ContextPersistence:
    """
    上下文持久化管理器
    负责将共享上下文保存到数据库
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
        self._table_name = "multi_agent_context"
        self._persist_enabled = False
        self._pending_updates: List[Dict] = []
        self._batch_size = 5
        self._sync_task = None
        
        # 尝试初始化
        self._init_persistence()
    
    def _init_persistence(self):
        """初始化持久化"""
        try:
            from storage.database.supabase_client import get_supabase_client
            self._client = get_supabase_client()
            self._persist_enabled = True
            
            # 启动定期同步任务
            self._sync_task = asyncio.create_task(self._periodic_sync())
            
            logger.info("[ContextPersistence] Database persistence enabled")
        except Exception as e:
            logger.warning(f"[ContextPersistence] Failed to init persistence: {e}")
            self._persist_enabled = False
    
    async def _periodic_sync(self):
        """定期同步到数据库"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒同步一次
                if self._pending_updates:
                    await self._flush_updates()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ContextPersistence] Sync error: {e}")
    
    async def _flush_updates(self):
        """批量保存更新"""
        if not self._pending_updates or not self._persist_enabled:
            return
        
        try:
            # 合并同一 key 的更新
            merged: Dict[str, Dict] = {}
            for update in self._pending_updates:
                key = update["context_key"]
                merged[key] = update
            
            # 保存到数据库
            for key, data in merged.items():
                self._client.table(self._table_name).upsert(data).execute()
            
            self._pending_updates.clear()
            logger.debug(f"[ContextPersistence] Flushed {len(merged)} context updates")
        except Exception as e:
            logger.error(f"[ContextPersistence] Failed to flush updates: {e}")
    
    def save_context(self, category: str, key: str, value: Any) -> bool:
        """保存上下文数据"""
        if not self._persist_enabled:
            return False
        
        try:
            context_data = {
                "category": category,
                "context_key": key,
                "value": json.dumps(value, ensure_ascii=False, default=str),
                "updated_at": datetime.now().isoformat()
            }
            
            self._pending_updates.append(context_data)
            
            if len(self._pending_updates) >= self._batch_size:
                asyncio.create_task(self._flush_updates())
            
            return True
        except Exception as e:
            logger.error(f"[ContextPersistence] Failed to save context: {e}")
            return False
    
    def load_context(self, category: str, key: str) -> Optional[Dict]:
        """加载上下文数据"""
        if not self._persist_enabled or not self._client:
            return None
        
        try:
            response = self._client.table(self._table_name) \
                .select("*") \
                .eq("category", category) \
                .eq("context_key", key) \
                .maybe_single() \
                .execute()
            
            if response:
                data = response.data
                if data and "value" in data:
                    return json.loads(data["value"])
            return None
        except Exception as e:
            logger.error(f"[ContextPersistence] Failed to load context: {e}")
            return None
    
    def load_all_by_category(self, category: str) -> List[Dict]:
        """加载某个分类下的所有数据"""
        if not self._persist_enabled or not self._client:
            return []
        
        try:
            response = self._client.table(self._table_name) \
                .select("*") \
                .eq("category", category) \
                .execute()
            
            results = []
            for item in response.data:
                if "value" in item:
                    results.append({
                        "key": item["context_key"],
                        "value": json.loads(item["value"]),
                        "updated_at": item.get("updated_at")
                    })
            return results
        except Exception as e:
            logger.error(f"[ContextPersistence] Failed to load category: {e}")
            return []
    
    async def close(self):
        """关闭时同步所有数据"""
        if self._sync_task:
            self._sync_task.cancel()
        await self._flush_updates()


class SharedContext:
    """
    共享上下文
    
    提供跨Agent的数据共享能力：
    - 用户画像
    - 学习进度
    - 任务状态
    - 缓存数据
    - 持久化支持（✅ 新增）
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
        
        # 存储结构
        self._data: Dict[str, Dict[str, Any]] = {
            "user_profiles": {},      # 用户画像
            "learning_progress": {},  # 学习进度
            "task_states": {},         # 任务状态
            "cache": {},              # 缓存数据
            "session_data": {}        # 会话数据
        }
        
        # 变更历史
        self._history: List[Dict[str, Any]] = []
        self._max_history = 500
        
        # ✅ 持久化管理器
        self._persistence = ContextPersistence()
        
        # ✅ 注册持久化钩子
        self._register_persistence_hooks()
        
        logger.info("[SharedContext] Initialized with persistence support")
    
    def _register_persistence_hooks(self):
        """注册持久化钩子，自动同步关键数据"""
        # 这个方法会在数据更新时自动持久化
        pass
    
    def _persist_update(self, category: str, key: str, value: Any):
        """持久化数据更新"""
        try:
            self._persistence.save_context(category, key, value)
        except Exception as e:
            logger.warning(f"[SharedContext] Persistence failed: {e}")
    
    def _record_change(self, category: str, key: str, action: str, old_value: Any = None) -> None:
        """记录变更历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "key": key,
            "action": action,
            "old_value": old_value
        }
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    # ==================== 用户画像 ====================
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        return self._data["user_profiles"].get(user_id)
    
    def set_user_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        """设置用户画像"""
        old = self._data["user_profiles"].get(user_id)
        self._data["user_profiles"][user_id] = {
            **profile,
            "updated_at": datetime.now().isoformat()
        }
        self._record_change("user_profiles", user_id, "set", old)
        self._persist_update("user_profiles", user_id, self._data["user_profiles"][user_id])
        logger.debug(f"[SharedContext] User profile updated: {user_id}")
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> None:
        """更新用户画像"""
        old = self._data["user_profiles"].get(user_id)
        if user_id not in self._data["user_profiles"]:
            self._data["user_profiles"][user_id] = {
                "user_id": user_id,
                "updated_at": datetime.now().isoformat()
            }
        self._data["user_profiles"][user_id].update(updates)
        self._data["user_profiles"][user_id]["updated_at"] = datetime.now().isoformat()
        self._record_change("user_profiles", user_id, "update", old)
        self._persist_update("user_profiles", user_id, self._data["user_profiles"][user_id])
    
    def get_all_user_ids(self) -> List[str]:
        """获取所有用户ID"""
        return list(self._data["user_profiles"].keys())
    
    # ==================== 学习进度 ====================
    
    def get_learning_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取学习进度"""
        return self._data["learning_progress"].get(user_id)
    
    def set_learning_progress(self, user_id: str, progress: Dict[str, Any]) -> None:
        """设置学习进度"""
        old = self._data["learning_progress"].get(user_id)
        self._data["learning_progress"][user_id] = {
            **progress,
            "updated_at": datetime.now().isoformat()
        }
        self._record_change("learning_progress", user_id, "set", old)
    
    def update_learning_progress(self, user_id: str, updates: Dict[str, Any]) -> None:
        """更新学习进度"""
        old = self._data["learning_progress"].get(user_id)
        if user_id not in self._data["learning_progress"]:
            self._data["learning_progress"][user_id] = {
                "user_id": user_id,
                "overall_progress": 0.0,
                "topic_progress": {},
                "updated_at": datetime.now().isoformat()
            }
        self._data["learning_progress"][user_id].update(updates)
        self._data["learning_progress"][user_id]["updated_at"] = datetime.now().isoformat()
        self._record_change("learning_progress", user_id, "update", old)
        self._persist_update("learning_progress", user_id, self._data["learning_progress"][user_id])
    
    def update_context(self, user_id: str, key: str, value: Any) -> None:
        """通用上下文更新"""
        if user_id not in self._data["learning_progress"]:
            self._data["learning_progress"][user_id] = {
                "user_id": user_id,
                "updated_at": datetime.now().isoformat()
            }
        if "context_data" not in self._data["learning_progress"][user_id]:
            self._data["learning_progress"][user_id]["context_data"] = {}
        self._data["learning_progress"][user_id]["context_data"][key] = value
        self._data["learning_progress"][user_id]["updated_at"] = datetime.now().isoformat()
    
    def get_topic_progress(self, user_id: str, topic: str) -> Optional[Dict[str, Any]]:
        """获取特定主题进度"""
        progress = self._data["learning_progress"].get(user_id, {})
        return progress.get("topic_progress", {}).get(topic)
    
    def update_topic_progress(self, user_id: str, topic: str, topic_data: Dict[str, Any]) -> None:
        """更新特定主题进度"""
        if user_id not in self._data["learning_progress"]:
            self._data["learning_progress"][user_id] = {
                "user_id": user_id,
                "topic_progress": {},
                "updated_at": datetime.now().isoformat()
            }
        if "topic_progress" not in self._data["learning_progress"][user_id]:
            self._data["learning_progress"][user_id]["topic_progress"] = {}
        
        self._data["learning_progress"][user_id]["topic_progress"][topic] = topic_data
        self._data["learning_progress"][user_id]["updated_at"] = datetime.now().isoformat()
    
    # ==================== 任务状态 ====================
    
    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self._data["task_states"].get(task_id)
    
    def set_task_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """设置任务状态"""
        self._data["task_states"][task_id] = {
            **state,
            "updated_at": datetime.now().isoformat()
        }
        self._record_change("task_states", task_id, "set")
    
    def update_task_state(self, task_id: str, updates: Dict[str, Any]) -> None:
        """更新任务状态"""
        if task_id not in self._data["task_states"]:
            self._data["task_states"][task_id] = {}
        self._data["task_states"][task_id].update(updates)
        self._data["task_states"][task_id]["updated_at"] = datetime.now().isoformat()
        self._record_change("task_states", task_id, "update")
    
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态获取任务列表"""
        return [
            task for task in self._data["task_states"].values()
            if task.get("status") == status
        ]
    
    # ==================== 缓存 ====================
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示永不过期
        """
        cache_entry = {
            "value": value,
            "created_at": datetime.now().isoformat(),
            "ttl": ttl
        }
        self._data["cache"][key] = cache_entry
        self._record_change("cache", key, "set")
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        entry = self._data["cache"].get(key)
        if entry is None:
            return None
        
        # 检查TTL
        if entry.get("ttl"):
            created = datetime.fromisoformat(entry["created_at"])
            if (datetime.now() - created).total_seconds() > entry["ttl"]:
                del self._data["cache"][key]
                return None
        
        return entry["value"]
    
    def delete_cache(self, key: str) -> bool:
        """删除缓存"""
        if key in self._data["cache"]:
            del self._data["cache"][key]
            self._record_change("cache", key, "delete")
            return True
        return False
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._data["cache"].clear()
        logger.info("[SharedContext] Cache cleared")
    
    # ==================== 会话数据 ====================
    
    def set_session_data(self, session_id: str, key: str, value: Any) -> None:
        """设置会话数据"""
        if session_id not in self._data["session_data"]:
            self._data["session_data"][session_id] = {}
        self._data["session_data"][session_id][key] = value
        self._record_change("session_data", f"{session_id}.{key}", "set")
    
    def get_session_data(self, session_id: str, key: str) -> Optional[Any]:
        """获取会话数据"""
        return self._data["session_data"].get(session_id, {}).get(key)
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取整个会话数据"""
        return self._data["session_data"].get(session_id, {})
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._data["session_data"]:
            del self._data["session_data"][session_id]
            return True
        return False
    
    # ==================== 工具方法 ====================
    
    def get(self, category: str, key: str) -> Optional[Any]:
        """通用获取方法"""
        return self._data.get(category, {}).get(key)
    
    def set(self, category: str, key: str, value: Any) -> None:
        """通用设置方法"""
        if category not in self._data:
            self._data[category] = {}
        old = self._data[category].get(key)
        self._data[category][key] = value
        self._record_change(category, key, "set", old)
    
    def get_history(self, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取变更历史"""
        history = self._history
        if category:
            history = [h for h in history if h["category"] == category]
        return history[-limit:]
    
    def export(self) -> Dict[str, Any]:
        """导出所有数据"""
        return {
            "timestamp": datetime.now().isoformat(),
            "data": self._data.copy()
        }
    
    def import_data(self, data: Dict[str, Any]) -> None:
        """导入数据"""
        if "data" in data:
            self._data = data["data"].copy()
            logger.info("[SharedContext] Data imported")
    
    def clear(self, category: Optional[str] = None) -> None:
        """清空数据"""
        if category:
            self._data[category].clear()
            logger.info(f"[SharedContext] Category '{category}' cleared")
        else:
            for key in self._data:
                self._data[key].clear()
            logger.info("[SharedContext] All data cleared")
    
    async def _checkpoint(self, user_id: Optional[str] = None) -> bool:
        """
        持久化当前状态到数据库
        
        Args:
            user_id: 可选的用户 ID，仅持久化该用户的数据
            
        Returns:
            是否持久化成功
        """
        try:
            from storage.database.supabase_client import get_supabase_client
            
            client = get_supabase_client()
            table_name = "context_checkpoints"
            
            # 准备持久化数据
            checkpoint_data = {
                "user_id": user_id or "global",
                "checkpoint_data": json.dumps(self._data, ensure_ascii=False),
                "created_at": datetime.now().isoformat()
            }
            
            # 保存到数据库
            client.table(table_name).insert(checkpoint_data).execute()
            
            logger.info(f"[SharedContext] Checkpoint saved for user: {user_id or 'global'}")
            return True
            
        except ImportError:
            logger.warning("[SharedContext] Storage module not available, skipping checkpoint")
            return False
        except Exception as e:
            logger.error(f"[SharedContext] Checkpoint failed: {e}")
            return False
    
    async def _restore(self, user_id: Optional[str] = None) -> bool:
        """
        从数据库恢复状态
        
        Args:
            user_id: 可选的用户 ID，恢复该用户的数据
            
        Returns:
            是否恢复成功
        """
        try:
            from storage.database.supabase_client import get_supabase_client
            
            client = get_supabase_client()
            table_name = "context_checkpoints"
            
            # 查询最新的检查点
            response = client.table(table_name) \
                .select("*") \
                .eq("user_id", user_id or "global") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if response.data:
                checkpoint = response.data[0]
                self._data = json.loads(checkpoint["checkpoint_data"])
                logger.info(f"[SharedContext] State restored for user: {user_id or 'global'}")
                return True
            else:
                logger.info(f"[SharedContext] No checkpoint found for user: {user_id or 'global'}")
                return False
            
        except ImportError:
            logger.warning("[SharedContext] Storage module not available, skipping restore")
            return False
        except Exception as e:
            logger.error(f"[SharedContext] Restore failed: {e}")
            return False
    
    def reset(self) -> None:
        """重置共享上下文"""
        self._data = {
            "user_profiles": {},
            "learning_progress": {},
            "task_states": {},
            "cache": {},
            "session_data": {}
        }
        self._history.clear()
        logger.info("[SharedContext] Reset")


# 全局实例
_global_context: Optional[SharedContext] = None


def get_shared_context() -> SharedContext:
    """获取全局共享上下文实例"""
    global _global_context
    if _global_context is None:
        _global_context = SharedContext()
    return _global_context


def set_shared_context(context: SharedContext) -> None:
    """设置全局共享上下文实例"""
    global _global_context
    _global_context = context
