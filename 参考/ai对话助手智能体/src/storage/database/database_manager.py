"""
数据库管理器 - 提供用户画像相关的数据库操作
"""
import json
import logging
from typing import Optional, Dict, Any, List
from storage.database.db import get_session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.session = get_session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        try:
            result = self.session.execute(
                text("SELECT * FROM user_profiles WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                # 将 datetime 转换为字符串
                data = dict(row._mapping)
                for key, value in data.items():
                    if hasattr(value, 'isoformat'):
                        data[key] = value.isoformat()
                return data
            return None
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """更新用户画像"""
        try:
            updates = []
            params = {"user_id": user_id}
            
            for key, value in profile_data.items():
                updates.append(f"{key} = :{key}")
                if isinstance(value, (dict, list)):
                    params[key] = json.dumps(value)
                else:
                    params[key] = value
            
            if updates:
                sql = f"""
                    UPDATE user_profiles 
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE user_id = :user_id
                """
                self.session.execute(text(sql), params)
                self.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"更新用户画像失败: {e}")
            self.session.rollback()
            return False
    
    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """创建用户画像"""
        try:
            columns = ["user_id"]
            values = [":user_id"]
            params = {"user_id": user_id}
            
            for key, value in profile_data.items():
                columns.append(key)
                values.append(f":{key}")
                if isinstance(value, (dict, list)):
                    params[key] = json.dumps(value)
                else:
                    params[key] = value
            
            sql = f"""
                INSERT INTO user_profiles ({', '.join(columns)})
                VALUES ({', '.join(values)})
            """
            self.session.execute(text(sql), params)
            self.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"创建用户画像失败: {e}")
            self.session.rollback()
            return False
    
    def save_conversation(self, user_id: str, user_message: str, agent_response: str,
                         agent_id: str = "conversation", metadata: Optional[Dict] = None) -> Optional[int]:
        """保存对话记录"""
        try:
            sql = """
                INSERT INTO conversation_records 
                (user_id, user_message, agent_response, agent_id, metadata, created_at)
                VALUES (:user_id, :user_message, :agent_response, :agent_id, :metadata, NOW())
                RETURNING id
            """
            result = self.session.execute(
                text(sql),
                {
                    "user_id": user_id,
                    "user_message": user_message,
                    "agent_response": agent_response,
                    "agent_id": agent_id,
                    "metadata": json.dumps(metadata) if metadata else None
                }
            )
            self.session.commit()
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"保存对话记录失败: {e}")
            self.session.rollback()
            return None
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户对话记录"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM conversation_records 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"获取对话记录失败: {e}")
            return []
    
    def get_learning_path(self, user_id: str, subject: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取学习路径"""
        try:
            if subject:
                result = self.session.execute(
                    text("""
                        SELECT * FROM learning_paths 
                        WHERE user_id = :user_id AND subject = :subject
                        ORDER BY created_at DESC LIMIT 1
                    """),
                    {"user_id": user_id, "subject": subject}
                )
            else:
                result = self.session.execute(
                    text("""
                        SELECT * FROM learning_paths 
                        WHERE user_id = :user_id 
                        ORDER BY created_at DESC LIMIT 1
                    """),
                    {"user_id": user_id}
                )
            
            row = result.fetchone()
            if row:
                path_data = dict(row._mapping)
                if path_data.get("path_data"):
                    path_data["path_data"] = json.loads(path_data["path_data"])
                return path_data
            return None
        except Exception as e:
            logger.error(f"获取学习路径失败: {e}")
            return None
    
    def save_learning_path(self, user_id: str, subject: str, path_data: Dict[str, Any]) -> Optional[int]:
        """保存学习路径"""
        try:
            sql = """
                INSERT INTO learning_paths 
                (user_id, subject, path_data, created_at, updated_at)
                VALUES (:user_id, :subject, :path_data, NOW(), NOW())
                RETURNING id
            """
            result = self.session.execute(
                text(sql),
                {
                    "user_id": user_id,
                    "subject": subject,
                    "path_data": json.dumps(path_data)
                }
            )
            self.session.commit()
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"保存学习路径失败: {e}")
            self.session.rollback()
            return None
    
    def update_learning_path_progress(self, path_id: int, current_stage: int, 
                                      completed_stages: List[int]) -> bool:
        """更新学习路径进度"""
        try:
            sql = """
                UPDATE learning_paths 
                SET current_stage = :current_stage,
                    completed_stages = :completed_stages,
                    updated_at = NOW()
                WHERE id = :path_id
            """
            self.session.execute(
                text(sql),
                {
                    "path_id": path_id,
                    "current_stage": current_stage,
                    "completed_stages": json.dumps(completed_stages)
                }
            )
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"更新学习路径进度失败: {e}")
            self.session.rollback()
            return False
    
    def save_push_record(self, user_id: str, content: str, push_type: str,
                        content_id: Optional[int] = None) -> Optional[int]:
        """保存推送记录"""
        try:
            sql = """
                INSERT INTO push_records 
                (user_id, content, push_type, content_id, created_at)
                VALUES (:user_id, :content, :push_type, :content_id, NOW())
                RETURNING id
            """
            result = self.session.execute(
                text(sql),
                {
                    "user_id": user_id,
                    "content": content,
                    "push_type": push_type,
                    "content_id": content_id
                }
            )
            self.session.commit()
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"保存推送记录失败: {e}")
            self.session.rollback()
            return None
    
    def get_push_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取推送记录"""
        try:
            result = self.session.execute(
                text("""
                    SELECT * FROM push_records 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"获取推送记录失败: {e}")
            return []


__all__ = ["DatabaseManager"]
