"""
Graph Store
图存储 - 基于Neo4j的知识图谱
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """图节点"""
    id: str
    label: str
    properties: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class GraphEdge:
    """图边"""
    id: str
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BaseGraphStore(ABC):
    """图存储抽象基类"""
    
    @abstractmethod
    def add_node(self, node: GraphNode) -> None:
        """添加节点"""
        pass
    
    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None:
        """添加边"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str, relationship: Optional[str] = None) -> List[GraphNode]:
        """获取邻居节点"""
        pass
    
    @abstractmethod
    def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> List[str]:
        """查找路径"""
        pass


class InMemoryGraphStore(BaseGraphStore):
    """
    内存图存储（当Neo4j不可用时的fallback实现）
    
    使用邻接表实现简单的图操作。
    """
    
    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._adjacency: Dict[str, Dict[str, List[str]]] = {}  # node_id -> {relationship -> [target_ids]}
        self._reverse_adjacency: Dict[str, Dict[str, List[str]]] = {}  # target_id -> {relationship -> [source_ids]}
        self._initialized = True
        logger.info("[GraphStore] Using InMemoryGraphStore")
    
    def add_node(self, node: GraphNode) -> None:
        """添加节点"""
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = {}
            self._reverse_adjacency[node.id] = {}
        logger.debug(f"[GraphStore] Added node: {node.id}")
    
    def add_edge(self, edge: GraphEdge) -> None:
        """添加边"""
        # 确保节点存在
        if edge.source not in self._nodes:
            self.add_node(GraphNode(id=edge.source, label="Unknown", properties={}))
        if edge.target not in self._nodes:
            self.add_node(GraphNode(id=edge.target, label="Unknown", properties={}))
        
        # 添加边
        self._edges[edge.id] = edge
        
        # 更新邻接表
        if edge.relationship not in self._adjacency[edge.source]:
            self._adjacency[edge.source][edge.relationship] = []
        if edge.target not in self._adjacency[edge.source][edge.relationship]:
            self._adjacency[edge.source][edge.relationship].append(edge.target)
        
        # 更新反向邻接表
        if edge.relationship not in self._reverse_adjacency[edge.target]:
            self._reverse_adjacency[edge.target][edge.relationship] = []
        if edge.source not in self._reverse_adjacency[edge.target][edge.relationship]:
            self._reverse_adjacency[edge.target][edge.relationship].append(edge.source)
        
        logger.debug(f"[GraphStore] Added edge: {edge.source} -[{edge.relationship}]-> {edge.target}")
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        return self._nodes.get(node_id)
    
    def get_neighbors(
        self,
        node_id: str,
        relationship: Optional[str] = None
    ) -> List[GraphNode]:
        """获取邻居节点"""
        if node_id not in self._adjacency:
            return []
        
        neighbor_ids = []
        if relationship:
            neighbor_ids = self._adjacency[node_id].get(relationship, [])
        else:
            # 获取所有关系的邻居
            for neighbors in self._adjacency[node_id].values():
                neighbor_ids.extend(neighbors)
        
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]
    
    def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> List[str]:
        """使用BFS查找路径"""
        from collections import deque
        
        queue = deque([(start_id, [start_id])])
        visited = {start_id}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end_id:
                return path
            
            if len(path) >= max_depth:
                continue
            
            if current not in self._adjacency:
                continue
            
            for neighbors in self._adjacency[current].values():
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def query(
        self,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[GraphNode]:
        """查询节点"""
        results = []
        
        for node in self._nodes.values():
            # 标签过滤
            if label and node.label != label:
                continue
            
            # 属性过滤
            if properties:
                match = all(
                    node.properties.get(k) == v
                    for k, v in properties.items()
                )
                if not match:
                    continue
            
            results.append(node)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_edges_from(self, node_id: str) -> List[GraphEdge]:
        """获取从指定节点出发的所有边"""
        return [
            edge for edge in self._edges.values()
            if edge.source == node_id
        ]
    
    def get_edges_to(self, node_id: str) -> List[GraphEdge]:
        """获取指向指定节点的所有边"""
        return [
            edge for edge in self._edges.values()
            if edge.target == node_id
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "labels": list(set(n.label for n in self._nodes.values())),
            "relationship_types": list(set(e.relationship for e in self._edges.values()))
        }
    
    def delete_node(self, node_id: str) -> None:
        """删除节点及其相关边"""
        # 删除相关边
        edges_to_delete = [
            eid for eid, edge in self._edges.items()
            if edge.source == node_id or edge.target == node_id
        ]
        for eid in edges_to_delete:
            del self._edges[eid]
        
        # 删除节点
        if node_id in self._nodes:
            del self._nodes[node_id]
        if node_id in self._adjacency:
            del self._adjacency[node_id]
        if node_id in self._reverse_adjacency:
            del self._reverse_adjacency[node_id]
        
        logger.info(f"[GraphStore] Deleted node: {node_id}")
    
    def clear(self) -> None:
        """清空所有数据"""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()
        logger.info("[GraphStore] Cleared all data")


class GraphStore:
    """
    图存储统一接口
    
    根据环境自动选择合适的存储实现：
    - Neo4j: 工业级图数据库（优先）
    - InMemory: 内存存储（fallback）
    """
    
    _instance = None
    
    def __new__(cls, uri: str = "bolt://localhost:7687"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._init_store(uri)
        return cls._instance
    
    def _init_store(self, uri: str) -> None:
        """初始化存储"""
        # 尝试使用Neo4j
        try:
            from neo4j import GraphDatabase
            
            self._driver = GraphDatabase.driver(uri)
            # 测试连接
            with self._driver.session() as session:
                session.run("RETURN 1")
            
            self._store = None  # 使用driver直接操作
            self._initialized = True
            self._use_neo4j = True
            logger.info(f"[GraphStore] Neo4j connected: {uri}")
            
        except (ImportError, Exception) as e:
            # 回退到内存存储
            self._store = InMemoryGraphStore()
            self._driver = None
            self._initialized = True
            self._use_neo4j = False
            logger.warning(f"[GraphStore] Neo4j not available, falling back to InMemory: {e}")
    
    def add_knowledge_node(
        self,
        node_id: str,
        label: str,
        properties: Dict[str, Any]
    ) -> None:
        """添加知识节点"""
        node = GraphNode(id=node_id, label=label, properties=properties)
        
        if self._use_neo4j:
            self._add_node_neo4j(node)
        else:
            self._store.add_node(node)
    
    def _add_node_neo4j(self, node: GraphNode) -> None:
        """通过Neo4j添加节点"""
        query = f"""
        MERGE (n:{node.label} {{id: $id}})
        SET n += $properties,
            n.created_at = $created_at
        """
        with self._driver.session() as session:
            session.run(query, id=node.id, properties=node.properties, created_at=node.created_at.isoformat())
    
    def add_knowledge_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加知识关系"""
        from uuid import uuid4
        edge = GraphEdge(
            id=str(uuid4()),
            source=source_id,
            target=target_id,
            relationship=relation_type,
            properties=properties or {}
        )
        
        if self._use_neo4j:
            self._add_edge_neo4j(edge)
        else:
            self._store.add_edge(edge)
    
    def _add_edge_neo4j(self, edge: GraphEdge) -> None:
        """通过Neo4j添加边"""
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $source AND b.id = $target
        MERGE (a)-[r:{edge.relationship} {{id: $id}}]->(b)
        SET r += $properties
        """
        with self._driver.session() as session:
            session.run(query, **edge.__dict__)
    
    def get_topic_neighbors(
        self,
        topic_id: str,
        relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取主题的邻居（前置/后继知识点）"""
        if self._use_neo4j:
            return self._get_neighbors_neo4j(topic_id, relation_type)
        else:
            neighbors = self._store.get_neighbors(topic_id, relation_type)
            return [
                {
                    "id": n.id,
                    "label": n.label,
                    "properties": n.properties
                }
                for n in neighbors
            ]
    
    def _get_neighbors_neo4j(self, topic_id: str, relation_type: Optional[str] = None) -> List[Dict]:
        """通过Neo4j获取邻居"""
        if relation_type:
            query = f"""
            MATCH (a)-[r:{relation_type}]->(b)
            WHERE a.id = $id
            RETURN b
            """
        else:
            query = """
            MATCH (a)-[r]->(b)
            WHERE a.id = $id
            RETURN b, type(r) as relationship
            """
        
        with self._driver.session() as session:
            results = session.run(query, id=topic_id)
            return [dict(record) for record in results]
    
    def find_learning_path(
        self,
        current_topic: str,
        target_topic: str
    ) -> List[str]:
        """查找学习路径"""
        if self._use_neo4j:
            return self._find_path_neo4j(current_topic, target_topic)
        else:
            return self._store.find_path(current_topic, target_topic)
    
    def _find_path_neo4j(self, start_id: str, end_id: str) -> List[str]:
        """通过Neo4j查找路径"""
        query = """
        MATCH path = shortestPath((a)-[:PREREQUISITE*..10]->(b))
        WHERE a.id = $start AND b.id = $end
        RETURN [node IN nodes(path) | node.id] as path
        """
        with self._driver.session() as session:
            results = session.run(query, start=start_id, end=end_id)
            records = list(results)
            if records:
                return records[0]["path"]
        return []
    
    def recommend_next_topics(
        self,
        current_topic: str,
        max_count: int = 3
    ) -> List[Dict[str, Any]]:
        """推荐下一个学习主题"""
        if self._use_neo4j:
            return self._recommend_next_neo4j(current_topic, max_count)
        else:
            neighbors = self._store.get_neighbors(current_topic, "NEXT")
            return [
                {
                    "id": n.id,
                    "label": n.label,
                    "properties": n.properties
                }
                for n in neighbors[:max_count]
            ]
    
    def _recommend_next_neo4j(self, topic_id: str, max_count: int) -> List[Dict]:
        """通过Neo4j推荐下一个主题"""
        query = """
        MATCH (current)-[:NEXT]->(next)
        WHERE current.id = $id
        RETURN next
        LIMIT $limit
        """
        with self._driver.session() as session:
            results = session.run(query, id=topic_id, limit=max_count)
            return [dict(record["next"]) for record in results]
    
    def build_topic_graph(
        self,
        topics: List[Dict[str, Any]],
        relations: List[Dict[str, str]]
    ) -> None:
        """批量构建主题图"""
        # 添加节点
        for topic in topics:
            self.add_knowledge_node(
                node_id=topic["id"],
                label="Topic",
                properties={
                    "name": topic.get("name", ""),
                    "subject": topic.get("subject", ""),
                    "difficulty": topic.get("difficulty", "medium")
                }
            )
        
        # 添加关系
        for relation in relations:
            self.add_knowledge_relation(
                source_id=relation["source"],
                target_id=relation["target"],
                relation_type=relation.get("type", "PREREQUISITE")
            )
        
        logger.info(f"[GraphStore] Built topic graph: {len(topics)} nodes, {len(relations)} edges")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self._use_neo4j:
            query = """
            MATCH (n)
            RETURN count(DISTINCT n) as node_count,
                   size([(n)-[r]->() | r]) as edge_count,
                   labels(n) as labels
            """
            with self._driver.session() as session:
                result = session.run(query)
                record = result.single()
                return {
                    "node_count": record["node_count"] if record else 0,
                    "edge_count": record["edge_count"] if record else 0
                }
        else:
            return self._store.get_statistics()
    
    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
            logger.info("[GraphStore] Neo4j connection closed")
    
    def reset(self) -> None:
        """重置图存储"""
        if not self._use_neo4j:
            self._store.clear()
        else:
            # 清空Neo4j数据
            with self._driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        logger.info("[GraphStore] Reset")
        GraphStore._instance = None


def get_graph_store(uri: str = "bolt://localhost:7687") -> GraphStore:
    """获取图存储实例"""
    return GraphStore(uri)
