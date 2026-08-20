"""
Vector Store
向量存储 - 基于ChromaDB的知识检索增强
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict], ids: List[str]) -> None:
        """添加向量"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """删除向量"""
        pass


class InMemoryVectorStore(BaseVectorStore):
    """
    内存向量存储（当ChromaDB不可用时的fallback实现）
    
    使用简单的余弦相似度计算进行向量检索。
    """
    
    def __init__(self):
        self._vectors: List[Dict[str, Any]] = []
        self._initialized = True
        logger.info("[VectorStore] Using InMemoryVectorStore")
    
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict], ids: List[str]) -> None:
        """添加向量到内存存储"""
        for i, (text, embedding, metadata, vector_id) in enumerate(zip(texts, embeddings, metadatas, ids)):
            self._vectors.append({
                "id": vector_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.now().isoformat()
            })
        logger.info(f"[VectorStore] Added {len(ids)} vectors (in-memory)")
    
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """搜索相似向量"""
        results = []
        
        for vector in self._vectors:
            # 应用过滤
            if filter_dict:
                match = all(
                    vector["metadata"].get(k) == v
                    for k, v in filter_dict.items()
                )
                if not match:
                    continue
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_embedding, vector["embedding"])
            results.append({
                "id": vector["id"],
                "text": vector["text"],
                "metadata": vector["metadata"],
                "similarity": similarity
            })
        
        # 排序并返回top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(a * a for a in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def delete(self, ids: List[str]) -> None:
        """删除向量"""
        self._vectors = [v for v in self._vectors if v["id"] not in ids]
        logger.info(f"[VectorStore] Deleted {len(ids)} vectors (in-memory)")
    
    def count(self) -> int:
        """获取向量数量"""
        return len(self._vectors)
    
    def clear(self) -> None:
        """清空所有向量"""
        self._vectors.clear()
        logger.info("[VectorStore] Cleared all vectors (in-memory)")


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB向量存储
    
    当ChromaDB可用时使用的高性能向量存储。
    """
    
    def __init__(self, collection_name: str = "learning_content"):
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.Client(Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ))
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Learning content vector store"}
            )
            self._initialized = True
            logger.info(f"[VectorStore] ChromaDB initialized, collection: {collection_name}")
            
        except ImportError:
            logger.warning("[VectorStore] ChromaDB not available, falling back to InMemoryVectorStore")
            self._initialized = False
            self._fallback = InMemoryVectorStore()
    
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict], ids: List[str]) -> None:
        """添加向量到ChromaDB"""
        if not self._initialized:
            return self._fallback.add(texts, embeddings, metadatas, ids)
        
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"[VectorStore] Added {len(ids)} vectors to ChromaDB")
    
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """搜索相似向量"""
        if not self._initialized:
            return self._fallback.search(query_embedding, top_k, filter_dict)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict
        )
        
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, vector_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": vector_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "similarity": 1.0 - (results["distances"][0][i] if results["distances"] else 0)
                })
        
        return formatted_results
    
    def delete(self, ids: List[str]) -> None:
        """删除向量"""
        if not self._initialized:
            return self._fallback.delete(ids)
        
        self.collection.delete(ids=ids)
        logger.info(f"[VectorStore] Deleted {len(ids)} vectors from ChromaDB")


class SupabaseVectorStore(BaseVectorStore):
    """
    Supabase向量存储（持久化）
    
    使用Supabase作为后端存储，支持向量数据的持久化保存。
    适用于生产环境，确保服务重启后数据不丢失。
    """
    
    def __init__(self, table_name: str = "vector_store"):
        self._table_name = table_name
        self._initialized = False
        self._supabase = None
        self._embedding_cache: Dict[str, List[float]] = {}  # 内存缓存embedding
        
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                self._supabase = create_client(supabase_url, supabase_key)
                self._initialized = True
                logger.info(f"[VectorStore] Supabase initialized, table: {table_name}")
            else:
                logger.warning("[VectorStore] Supabase credentials not found, using InMemory fallback")
                self._fallback = InMemoryVectorStore()
                
        except ImportError:
            logger.warning("[VectorStore] Supabase not available, using InMemory fallback")
            self._fallback = InMemoryVectorStore()
        except Exception as e:
            logger.warning(f"[VectorStore] Supabase init failed: {e}, using InMemory fallback")
            self._fallback = InMemoryVectorStore()
    
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict], ids: List[str]) -> None:
        """添加向量到Supabase"""
        if not self._initialized:
            return self._fallback.add(texts, embeddings, metadatas, ids)
        
        try:
            # 存储到数据库
            records = []
            for i, vector_id in enumerate(ids):
                records.append({
                    "content_id": vector_id,
                    "text": texts[i],
                    "embedding": embeddings[i],  # Supabase支持JSONB存储列表
                    "metadata": metadatas[i]
                })
            
            self._supabase.table(self._table_name).upsert(records).execute()
            
            # 缓存到内存
            for i, vector_id in enumerate(ids):
                self._embedding_cache[vector_id] = embeddings[i]
            
            logger.info(f"[VectorStore] Added {len(ids)} vectors to Supabase")
        except Exception as e:
            logger.error(f"[VectorStore] Failed to add vectors to Supabase: {e}")
            self._fallback.add(texts, embeddings, metadatas, ids)
    
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """搜索相似向量"""
        if not self._initialized:
            return self._fallback.search(query_embedding, top_k, filter_dict)
        
        try:
            # 从数据库获取所有向量（简单实现，生产环境可用pgvector扩展）
            query = self._supabase.table(self._table_name).select("*")
            
            if filter_dict:
                for key, value in filter_dict.items():
                    query = query.eq(f"metadata->>'{key}'", value)
            
            response = query.execute()
            
            # 计算余弦相似度
            results = []
            for record in response.data:
                stored_embedding = record.get("embedding", [])
                if len(stored_embedding) == len(query_embedding):
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    results.append({
                        "id": record["content_id"],
                        "text": record["text"],
                        "metadata": record.get("metadata", {}),
                        "similarity": similarity
                    })
            
            # 排序并返回top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"[VectorStore] Search failed: {e}")
            return self._fallback.search(query_embedding, top_k, filter_dict)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0
    
    def delete(self, ids: List[str]) -> None:
        """删除向量"""
        if not self._initialized:
            return self._fallback.delete(ids)
        
        try:
            for vector_id in ids:
                self._supabase.table(self._table_name).delete().eq("content_id", vector_id).execute()
                self._embedding_cache.pop(vector_id, None)
            logger.info(f"[VectorStore] Deleted {len(ids)} vectors from Supabase")
        except Exception as e:
            logger.error(f"[VectorStore] Failed to delete vectors: {e}")
            self._fallback.delete(ids)
    
    def count(self) -> int:
        """获取向量数量"""
        if not self._initialized:
            return self._fallback.count()
        
        try:
            response = self._supabase.table(self._table_name).select("id", count="exact").execute()
            return len(response.data)
        except:
            return self._fallback.count()
    
    def clear(self) -> None:
        """清空所有向量"""
        if not self._initialized:
            return self._fallback.clear()
        
        try:
            self._supabase.table(self._table_name).delete().neq("id", 0).execute()
            self._embedding_cache.clear()
            logger.info("[VectorStore] Cleared all vectors from Supabase")
        except Exception as e:
            logger.error(f"[VectorStore] Failed to clear vectors: {e}")
            self._fallback.clear()


class VectorStore:
    """
    向量存储统一接口
    
    根据环境自动选择合适的存储实现：
    - ChromaDB: 高性能向量存储（优先）
    - InMemory: 内存存储（fallback）
    """
    
    _instance = None
    
    def __new__(cls, collection_name: str = "learning_content"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._init_store(collection_name)
        return cls._instance
    
    def _init_store(self, collection_name: str) -> None:
        """初始化存储"""
        # 优先尝试使用Supabase持久化存储
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                self._store = SupabaseVectorStore(collection_name)
                if self._store._initialized:
                    self._initialized = True
                    logger.info("[VectorStore] Initialized with Supabase persistence")
                    return
                    
        except ImportError:
            logger.debug("[VectorStore] Supabase not available")
        except Exception as e:
            logger.debug(f"[VectorStore] Supabase init failed: {e}")
        
        # 回退到ChromaDB
        try:
            import chromadb
            self._store = ChromaVectorStore(collection_name)
            self._initialized = True
            logger.info("[VectorStore] Initialized with ChromaDB")
        except ImportError:
            # 最终回退到内存存储
            self._store = InMemoryVectorStore()
            self._initialized = True
            logger.info("[VectorStore] Initialized with InMemory fallback")
    
    def add_learning_content(
        self,
        content_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """添加学习内容"""
        self._store.add(
            texts=[text],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[content_id]
        )
    
    def add_batch(
        self,
        contents: List[Dict[str, Any]]
    ) -> None:
        """批量添加学习内容"""
        texts = [c["text"] for c in contents]
        embeddings = [c["embedding"] for c in contents]
        metadatas = [c["metadata"] for c in contents]
        ids = [c["id"] for c in contents]
        
        self._store.add(texts, embeddings, metadatas, ids)
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似内容"""
        filter_dict = {}
        if subject:
            filter_dict["subject"] = subject
        if topic:
            filter_dict["topic"] = topic
        
        return self._store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_dict=filter_dict if filter_dict else None
        )
    
    def search_by_text(
        self,
        query_text: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        通过文本搜索（需要先生成embedding）
        
        注意：这个方法需要调用方提供embedding模型来生成查询向量。
        """
        # 这里需要embedding服务，实际使用时由调用方提供
        logger.warning("[VectorStore] search_by_text requires external embedding service")
        return []
    
    def delete_content(self, content_id: str) -> None:
        """删除内容"""
        self._store.delete(ids=[content_id])
    
    def get_count(self) -> int:
        """获取内容数量"""
        return self._store.count()
    
    def clear(self) -> None:
        """清空所有内容"""
        self._store.clear()
    
    def reset(self) -> None:
        """重置向量存储"""
        VectorStore._instance = None


def get_vector_store(collection_name: str = "learning_content") -> VectorStore:
    """获取向量存储实例"""
    return VectorStore(collection_name)
