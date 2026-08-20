"""
大数据知识图谱
Big Data Knowledge Graph

包含大数据核心知识体系及其依赖关系，用于：
1. 学习路径规划
2. 知识点诊断
3. 遗忘曲线预测
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class DifficultyLevel(Enum):
    """难度等级"""
    入门 = 1
    基础 = 2
    进阶 = 3
    高级 = 4
    专家 = 5


class KnowledgeCategory(Enum):
    """知识类别"""
    基础概念 = "基础概念"
    数据存储 = "数据存储"
    数据采集 = "数据采集"
    数据处理 = "数据处理"
    数据分析 = "数据分析"
    数据挖掘 = "数据挖掘"
    架构设计 = "架构设计"
    工具平台 = "工具平台"


@dataclass
class KnowledgeNode:
    """知识点节点"""
    id: str                           # 唯一标识
    name: str                         # 名称
    description: str                  # 描述
    category: KnowledgeCategory      # 所属类别
    difficulty: DifficultyLevel      # 难度等级
    prerequisites: List[str] = field(default_factory=list)  # 前置知识点ID列表
    related_topics: List[str] = field(default_factory=list) # 相关知识点ID列表
    keywords: List[str] = field(default_factory=list)       # 关键词（用于检索）
    estimated_hours: float = 1.0      # 预估学习时长（小时）
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.name,
            "prerequisites": self.prerequisites,
            "related_topics": self.related_topics,
            "keywords": self.keywords,
            "estimated_hours": self.estimated_hours
        }


class BigDataKnowledgeGraph:
    """
    大数据知识图谱
    
    核心数据结构，包含大数据完整知识体系和依赖关系
    """
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self._build_graph()
    
    def _build_graph(self):
        """构建大数据知识图谱"""
        
        # ========== 第一层：基础概念 ==========
        base_concepts = [
            KnowledgeNode(
                id="bigdata_intro",
                name="大数据概述",
                description="大数据的定义、特征（5V特征：Volume、Velocity、Variety、Value、Veracity）、应用场景",
                category=KnowledgeCategory.基础概念,
                difficulty=DifficultyLevel.入门,
                keywords=["大数据", "5V", "Volume", "Velocity", "Variety", "特征"],
                estimated_hours=1.0
            ),
            KnowledgeNode(
                id="distributed_system",
                name="分布式系统基础",
                description="分布式架构原理、CAP定理、BASE理论、一致性模型",
                category=KnowledgeCategory.基础概念,
                difficulty=DifficultyLevel.基础,
                prerequisites=["bigdata_intro"],
                keywords=["分布式", "CAP", "BASE", "一致性", "一致性模型"],
                estimated_hours=3.0
            ),
            KnowledgeNode(
                id="linux_basics",
                name="Linux基础",
                description="Linux常用命令、Shell脚本基础、环境配置",
                category=KnowledgeCategory.基础概念,
                difficulty=DifficultyLevel.入门,
                keywords=["Linux", "Shell", "命令行", "环境配置"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="sql_basics",
                name="SQL基础",
                description="关系型数据库、SQL语句（SELECT/INSERT/UPDATE/DELETE）、表连接",
                category=KnowledgeCategory.基础概念,
                difficulty=DifficultyLevel.入门,
                keywords=["SQL", "数据库", "表", "查询"],
                estimated_hours=6.0
            ),
            KnowledgeNode(
                id="python_basics",
                name="Python基础",
                description="Python基本语法、数据类型、控制流、函数、文件操作",
                category=KnowledgeCategory.基础概念,
                difficulty=DifficultyLevel.入门,
                keywords=["Python", "编程", "语法", "函数"],
                estimated_hours=8.0
            ),
        ]
        
        # ========== 第二层：数据采集与存储 ==========
        data_collection_storage = [
            KnowledgeNode(
                id="data_collection",
                name="数据采集",
                description="数据采集工具和技术：Flume、Kafka Connect、Flink CDC等",
                category=KnowledgeCategory.数据采集,
                difficulty=DifficultyLevel.基础,
                prerequisites=["bigdata_intro", "linux_basics"],
                keywords=["数据采集", "Flume", "Kafka", "CDC", "ETL"],
                estimated_hours=3.0
            ),
            KnowledgeNode(
                id="hdfs",
                name="HDFS分布式文件系统",
                description="Hadoop Distributed File System架构、DataNode、NameNode、副本机制",
                category=KnowledgeCategory.数据存储,
                difficulty=DifficultyLevel.基础,
                prerequisites=["distributed_system", "linux_basics"],
                keywords=["HDFS", "Hadoop", "分布式存储", "NameNode", "DataNode"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="hbase",
                name="HBase NoSQL数据库",
                description="列式存储、Region、RowKey设计、Scan与Get操作",
                category=KnowledgeCategory.数据存储,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["hdfs", "sql_basics"],
                keywords=["HBase", "NoSQL", "列式存储", "Region", "RowKey"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="kafka",
                name="Kafka消息队列",
                description="发布-订阅模型、Topic、Partition、Consumer Group、幂等性",
                category=KnowledgeCategory.数据存储,
                difficulty=DifficultyLevel.基础,
                prerequisites=["distributed_system"],
                keywords=["Kafka", "消息队列", "Topic", "Partition", "发布订阅"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="data_lake",
                name="数据湖",
                description="数据湖概念、Delta Lake、Iceberg、Hudi架构对比",
                category=KnowledgeCategory.数据存储,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["hdfs", "kafka"],
                related_topics=["spark", "flink"],
                keywords=["数据湖", "Data Lake", "Delta Lake", "Iceberg", "Hudi"],
                estimated_hours=3.0
            ),
        ]
        
        # ========== 第三层：数据处理 ==========
        data_processing = [
            KnowledgeNode(
                id="mapreduce",
                name="MapReduce编程模型",
                description="Map-Shuffle-Reduce流程、Combiner、Partitioner、计数器",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.基础,
                prerequisites=["hdfs", "distributed_system"],
                keywords=["MapReduce", "Map", "Reduce", "Shuffle", "Hadoop"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="yarn",
                name="YARN资源调度",
                description="ResourceManager、NodeManager、ApplicationMaster、调度策略",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.基础,
                prerequisites=["hdfs"],
                keywords=["YARN", "资源调度", "ResourceManager", "容器"],
                estimated_hours=2.0
            ),
            KnowledgeNode(
                id="spark_core",
                name="Spark Core核心",
                description="RDD算子、DataFrame、DataSet、Spark Application、任务调度",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["mapreduce", "yarn", "python_basics"],
                keywords=["Spark", "RDD", "DataFrame", "算子", "Transformation", "Action"],
                estimated_hours=8.0
            ),
            KnowledgeNode(
                id="spark_sql",
                name="Spark SQL",
                description="DataFrame API、Spark SQL语法、UDF、窗口函数、性能优化",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["spark_core", "sql_basics"],
                keywords=["SparkSQL", "DataFrame", "窗口函数", "UDF"],
                estimated_hours=6.0
            ),
            KnowledgeNode(
                id="spark_streaming",
                name="Spark Streaming",
                description="微批次处理、DStream、Structured Streaming、检查点机制",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["spark_core", "kafka"],
                keywords=["SparkStreaming", "微批次", "DStream", "Structured"],
                estimated_hours=5.0
            ),
            KnowledgeNode(
                id="flink",
                name="Flink流处理",
                description="真正的流处理、Time语义、Window、Checkpoint、State、CEP复杂事件处理",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.高级,
                prerequisites=["kafka", "distributed_system"],
                keywords=["Flink", "流处理", "实时计算", "CEP", "Window", "Checkpoint"],
                estimated_hours=10.0
            ),
            KnowledgeNode(
                id="hive",
                name="Hive数据仓库",
                description="HiveQL、Metastore、分区表、桶表、UDF、优化策略",
                category=KnowledgeCategory.数据处理,
                difficulty=DifficultyLevel.基础,
                prerequisites=["hdfs", "sql_basics"],
                keywords=["Hive", "数据仓库", "HiveQL", "Metastore", "分区"],
                estimated_hours=5.0
            ),
        ]
        
        # ========== 第四层：数据分析与挖掘 ==========
        data_analysis_mining = [
            KnowledgeNode(
                id="statistics",
                name="统计学基础",
                description="描述性统计、概率分布、假设检验、相关性分析",
                category=KnowledgeCategory.数据分析,
                difficulty=DifficultyLevel.基础,
                prerequisites=["python_basics"],
                keywords=["统计学", "概率", "假设检验", "相关分析", "分布"],
                estimated_hours=6.0
            ),
            KnowledgeNode(
                id="ml_basics",
                name="机器学习基础",
                description="监督学习、无监督学习、模型评估、过拟合与欠拟合、特征工程",
                category=KnowledgeCategory.数据分析,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["statistics", "python_basics"],
                keywords=["机器学习", "监督学习", "无监督学习", "特征工程", "模型评估"],
                estimated_hours=10.0
            ),
            KnowledgeNode(
                id="ml_spark",
                name="Spark MLlib",
                description="MLlib API、特征提取器、分类、聚类、协同过滤、管道API",
                category=KnowledgeCategory.数据分析,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["spark_ml_basics", "spark_core"],
                keywords=["MLlib", "机器学习", "分类", "聚类", "协同过滤"],
                estimated_hours=6.0
            ),
            KnowledgeNode(
                id="spark_ml_basics",
                name="Spark机器学习基础",
                description="Spark MLlib基础、特征向量化、模型训练与评估",
                category=KnowledgeCategory.数据分析,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["ml_basics", "spark_core"],
                keywords=["MLlib", "特征向量", "模型训练"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="data_visualization",
                name="数据可视化",
                description="可视化原则、常用图表类型、ECharts、Python可视化库",
                category=KnowledgeCategory.数据分析,
                difficulty=DifficultyLevel.基础,
                prerequisites=["python_basics", "sql_basics"],
                keywords=["可视化", "图表", "ECharts", "Matplotlib", "Seaborn"],
                estimated_hours=4.0
            ),
        ]
        
        # ========== 第五层：架构与工具 ==========
        architecture_tools = [
            KnowledgeNode(
                id="hadoop_ecosystem",
                name="Hadoop生态系统",
                description="Hadoop家族组件介绍、组件协作关系、版本演进",
                category=KnowledgeCategory.架构设计,
                difficulty=DifficultyLevel.基础,
                prerequisites=["hdfs", "mapreduce", "yarn"],
                related_topics=["hive", "hbase", "spark", "flink"],
                keywords=["Hadoop", "生态系统", "Hadoop家族"],
                estimated_hours=2.0
            ),
            KnowledgeNode(
                id="lambda_architecture",
                name="Lambda架构",
                description="批处理层、速度层、服务层、Lambda架构优缺点",
                category=KnowledgeCategory.架构设计,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["spark_core", "spark_streaming"],
                keywords=["Lambda", "批处理", "实时处理", "架构"],
                estimated_hours=3.0
            ),
            KnowledgeNode(
                id="kappa_architecture",
                name="Kappa架构",
                description="纯流处理架构、Kappa vs Lambda、适用场景",
                category=KnowledgeCategory.架构设计,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["flink", "lambda_architecture"],
                keywords=["Kappa", "纯流处理", "架构"],
                estimated_hours=2.0
            ),
            KnowledgeNode(
                id="data_pipeline",
                name="数据管道设计",
                description="ETL/ELT流程、数据质量管理、数据血缘追踪",
                category=KnowledgeCategory.架构设计,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["kafka", "spark_core", "hive"],
                keywords=["ETL", "ELT", "数据管道", "数据质量", "血缘"],
                estimated_hours=4.0
            ),
            KnowledgeNode(
                id="docker_k8s",
                name="容器与编排",
                description="Docker基础、Kubernetes核心概念、在大数据中的应用",
                category=KnowledgeCategory.工具平台,
                difficulty=DifficultyLevel.进阶,
                prerequisites=["linux_basics"],
                keywords=["Docker", "Kubernetes", "K8s", "容器", "编排"],
                estimated_hours=6.0
            ),
            KnowledgeNode(
                id="scheduler",
                name="任务调度",
                description="Azkaban、Airflow、DolphinScheduler调度工具对比和使用",
                category=KnowledgeCategory.工具平台,
                difficulty=DifficultyLevel.基础,
                prerequisites=["linux_basics", "hadoop_ecosystem"],
                keywords=["调度", "Airflow", "Azkaban", "工作流"],
                estimated_hours=3.0
            ),
        ]
        
        # ========== 汇总所有知识点 ==========
        all_nodes = (
            base_concepts + 
            data_collection_storage + 
            data_processing + 
            data_analysis_mining + 
            architecture_tools
        )
        
        # 构建图谱
        for node in all_nodes:
            self.nodes[node.id] = node
        
        # 设置相关主题关联
        self._setup_related_topics()
    
    def _setup_related_topics(self):
        """设置相关主题关联"""
        related_map = {
            "spark": ["spark_core", "spark_sql", "spark_streaming", "ml_spark"],
            "flink": ["flink", "kafka"],
            "hadoop": ["hdfs", "mapreduce", "yarn", "hive", "hbase"],
        }
        
        for _, related_ids in related_map.items():
            for node_id in related_ids:
                if node_id in self.nodes:
                    self.nodes[node_id].related_topics = [
                        rid for rid in related_ids if rid != node_id
                    ]
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """获取知识点节点"""
        return self.nodes.get(node_id)
    
    def get_prerequisites(self, node_id: str) -> List[KnowledgeNode]:
        """获取前置知识点列表"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[pid] for pid in node.prerequisites if pid in self.nodes]
    
    def get_learning_path(
        self, 
        start_level: DifficultyLevel = DifficultyLevel.入门,
        target_level: DifficultyLevel = DifficultyLevel.进阶
    ) -> List[KnowledgeNode]:
        """
        获取学习路径
        
        Args:
            start_level: 起始难度
            target_level: 目标难度
            
        Returns:
            排序后的学习路径
        """
        path = []
        visited = set()
        
        def visit(node_id: str):
            if node_id in visited:
                return
            node = self.nodes.get(node_id)
            if not node:
                return
            if node.difficulty.value > target_level.value:
                return
                
            # 先访问前置节点
            for prereq_id in node.prerequisites:
                if prereq_id not in visited:
                    visit(prereq_id)
            
            visited.add(node_id)
            path.append(node)
        
        # 按难度筛选并排序
        for node in sorted(self.nodes.values(), key=lambda x: x.difficulty.value):
            if node.difficulty.value >= start_level.value:
                visit(node.id)
        
        return path
    
    def get_category_nodes(self, category: KnowledgeCategory) -> List[KnowledgeNode]:
        """获取指定类别的所有知识点"""
        return [n for n in self.nodes.values() if n.category == category]
    
    def search_by_keyword(self, keyword: str) -> List[KnowledgeNode]:
        """根据关键词搜索知识点"""
        keyword = keyword.lower()
        results = []
        for node in self.nodes.values():
            if keyword in node.name.lower():
                results.append(node)
            elif any(keyword in kw.lower() for kw in node.keywords):
                results.append(node)
            elif keyword in node.description.lower():
                results.append(node)
        return results
    
    def diagnose_gaps(
        self, 
        mastered_topics: List[str]
    ) -> Dict[str, List[KnowledgeNode]]:
        """
        诊断知识缺口
        
        Args:
            mastered_topics: 已掌握的知识点ID列表
            
        Returns:
            {
                "missing_prerequisites": [缺失的前置知识],
                "recommended_next": [推荐下一步学习],
                "weak_connections": [掌握薄弱的相关知识点]
            }
        """
        mastered = set(mastered_topics)
        missing_prereqs = []
        recommended_next = []
        
        # 分析已学知识点，找缺失的前置
        for topic_id in mastered:
            node = self.nodes.get(topic_id)
            if not node:
                continue
            for prereq_id in node.prerequisites:
                if prereq_id not in mastered:
                    prereq_node = self.nodes.get(prereq_id)
                    if prereq_node:
                        missing_prereqs.append(prereq_node)
        
        # 推荐下一步：找所有前置已学但还未学的知识点
        for node in self.nodes.values():
            if node.id in mastered:
                continue
            prereqs_met = all(p in mastered for p in node.prerequisites)
            if prereqs_met:
                recommended_next.append(node)
        
        # 按难度排序推荐
        recommended_next.sort(key=lambda x: x.difficulty.value)
        
        return {
            "missing_prerequisites": missing_prereqs,
            "recommended_next": recommended_next[:5],
            "total_known": len(mastered),
            "total_knowledge": len(self.nodes)
        }
    
    def get_dependency_tree(self, node_id: str) -> Dict:
        """
        获取知识点的依赖树
        
        Returns:
            {
                "node": {...},
                "prerequisites": [
                    {"node": {...}, "prerequisites": [...]},
                    ...
                ]
            }
        """
        def build_tree(nid: str, depth: int = 0, max_depth: int = 5) -> Optional[Dict]:
            if depth > max_depth:
                return None
            node = self.nodes.get(nid)
            if not node:
                return None
            
            tree = {"node": node.to_dict(), "prerequisites": []}
            for prereq_id in node.prerequisites:
                prereq_tree = build_tree(prereq_id, depth + 1, max_depth)
                if prereq_tree:
                    tree["prerequisites"].append(prereq_tree)
            return tree
        
        return build_tree(node_id) or {}
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "name": "大数据知识图谱",
            "version": "1.0",
            "total_nodes": len(self.nodes),
            "categories": list(set(n.category.value for n in self.nodes.values())),
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()}
        }
    
    def to_json(self) -> str:
        """导出为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# 全局单例
_knowledge_graph: Optional[BigDataKnowledgeGraph] = None


def get_knowledge_graph() -> BigDataKnowledgeGraph:
    """获取大数据知识图谱单例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = BigDataKnowledgeGraph()
    return _knowledge_graph
