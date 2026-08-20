"""
大数据学习知识点配置
整合 RAG 知识库中的知识点，为各 Agent 提供统一的知识体系支持
"""

# 一级分类（学科领域）
SUBJECTS = [
    "Hadoop",
    "Spark",
    "Flink",
    "Hive",
    "Kafka",
    "HBase",
    "数据仓库",
    "离线计算",
    "实时计算",
    "数据湖",
    "大数据",
]

# 二级分类（技术领域）
TECH_DOMAINS = [
    "大数据采集",
    "大数据存储",
    "大数据计算",
    "大数据仓库",
    "大数据可视化",
    "大数据预处理",
    "大数据协同工具",
]

# 三级分类（具体技术）
TECHNOLOGIES = [
    "Hadoop",
    "HDFS",
    "MapReduce",
    "YARN",
    "Spark",
    "Spark SQL",
    "Spark Streaming",
    "Flink",
    "Hive",
    "HiveQL",
    "Kafka",
    "HBase",
    "ZooKeeper",
    "数据湖",
    "离线计算",
    "实时计算",
    "流处理",
    "批处理",
]

# 完整知识点树（从 RAG 知识库 bigdata_question_bank 提取）
KNOWLEDGE_TREE = {
    "大数据存储": {
        "HDFS": {
            "HDFS 存储机制": [],
            "Hadoop 环境部署": [],
        },
        "HBase": {
            "HBase 环境部署": [],
            "HBase 逻辑与物理视图": [],
            "HBase 批量处理操作": [],
            "HBase 与 Hive 集成": [],
        },
    },
    "大数据计算": {
        "Spark 综合": {
            "Spark 综合应用": [],
        },
        "Spark SQL": {
            "Spark DataFrame 运算 API": [],
        },
        "MapReduce": {},
    },
    "大数据仓库": {
        "Hive 基础": {
            "Hive 数据存储": [],
            "Hive 工作原理": [],
            "Hive 数据定义语言": [],
        },
        "Hive 进阶": {
            "Hive 安全管理": [],
        },
        "Spark SQL": {},
    },
    "大数据采集": {
        "Kafka": {},
        "Flink": {},
    },
    "大数据可视化": {},
    "大数据预处理": {},
    "大数据协同工具": {
        "ZooKeeper": {},
    },
}

# 知识点关键词映射（用于识别用户输入中的知识点）
KNOWLEDGE_KEYWORDS = {
    # Hadoop 生态
    "hadoop": "Hadoop",
    "hdfs": "HDFS",
    "mapreduce": "MapReduce",
    "yarn": "YARN",
    "zookeeper": "ZooKeeper",
    # Spark
    "spark": "Spark",
    "spark sql": "Spark SQL",
    "spark streaming": "Spark Streaming",
    "rdd": "Spark",
    "dataframe": "Spark",
    "dataset": "Spark",
    # Hive
    "hive": "Hive",
    "hiveql": "HiveQL",
    "hivesql": "HiveQL",
    # 实时计算
    "flink": "Flink",
    "kafka": "Kafka",
    # 存储
    "hbase": "HBase",
    # 数据仓库
    "数据仓库": "数据仓库",
    "离线计算": "离线计算",
    "实时计算": "实时计算",
    "流处理": "流处理",
    "批处理": "批处理",
    "数据湖": "数据湖",
    # 大数据整体
    "大数据": "大数据",
}

# 科目识别列表（包含大小写变体）
SUBJECT_ALIASES = {
    # Hadoop 生态
    "Hadoop": ["hadoop", "Hadoop", "HADOOP"],
    "HDFS": ["hdfs", "HDFS", "Hdfs"],
    "MapReduce": ["mapreduce", "MapReduce", "MAPREDUCE"],
    "YARN": ["yarn", "YARN", "Yarn"],
    "ZooKeeper": ["zookeeper", "ZooKeeper", "ZOOKEEPER"],
    # Spark
    "Spark": ["spark", "Spark", "SPARK"],
    "SparkSQL": ["spark sql", "spark-sql", "Spark SQL", "SparkSQL", "SPARK SQL"],
    "SparkStreaming": ["spark streaming", "Spark Streaming", "SPARK STREAMING"],
    # Hive
    "Hive": ["hive", "Hive", "HIVE"],
    "HiveQL": ["hiveql", "HiveQL", "HIVEQL", "hivesql"],
    # 实时计算
    "Flink": ["flink", "Flink", "FLINK"],
    "Kafka": ["kafka", "Kafka", "KAFKA"],
    # 存储
    "HBase": ["hbase", "HBase", "HBASE"],
    # 数据仓库
    "数据仓库": ["数据仓库", "数仓"],
    "离线计算": ["离线计算", "离线批处理", "批处理"],
    "实时计算": ["实时计算", "实时处理", "流处理"],
    "数据湖": ["数据湖", "data lake"],
    # 大数据整体
    "大数据": ["大数据", "bigdata", "BigData"],
}

# 学习路径科目列表（用于学习计划生成）
LEARNING_PATH_SUBJECTS = [
    "Hadoop",
    "Spark",
    "Flink",
    "Hive",
    "Kafka",
    "HBase",
    "数据仓库",
    "离线计算",
    "实时计算",
    "数据湖",
    "大数据",
]

# 文档生成科目列表
DOCUMENT_SUBJECTS = [
    "Hadoop",
    "Spark",
    "Flink",
    "Hive",
    "Kafka",
    "HBase",
    "数据仓库",
    "离线计算",
    "实时计算",
    "数据湖",
    "大数据",
    # 编程语言
    "Python",
    "Java",
    "Scala",
    "SQL",
    # 机器学习
    "机器学习",
    "深度学习",
    # 云计算
    "云原生",
    "Kubernetes",
    "Docker",
]

# 多媒体生成科目列表
MULTIMEDIA_SUBJECTS = [
    "Hadoop",
    "HDFS",
    "MapReduce",
    "YARN",
    "Spark",
    "Spark SQL",
    "Spark Streaming",
    "Flink",
    "Hive",
    "Kafka",
    "HBase",
    "数据仓库",
    "实时计算",
    "离线计算",
    "数据湖",
    "大数据",
]


def get_all_knowledge_points() -> list:
    """获取所有知识点列表"""
    points = []
    for domain, technologies in KNOWLEDGE_TREE.items():
        for tech, details in technologies.items():
            points.append(tech)
            if isinstance(details, dict):
                for detail in details.keys():
                    points.append(detail)
    return points


def match_subject(user_input: str) -> tuple:
    """
    匹配用户输入中的科目

    Returns:
        tuple: (科目, 知识点) 或 (None, None)
    """
    user_input_lower = user_input.lower()

    # 先匹配知识点
    for keyword, subject in KNOWLEDGE_KEYWORDS.items():
        if keyword.lower() in user_input_lower:
            # 检查是否有更具体的知识点
            for domain, technologies in KNOWLEDGE_TREE.items():
                if subject in technologies:
                    for tech, details in technologies.items():
                        if tech.lower() in user_input_lower:
                            return subject, tech
                        if isinstance(details, dict):
                            for detail in details.keys():
                                if detail.lower() in user_input_lower:
                                    return subject, detail
            return subject, None

    return None, None


def get_subject_aliases(subject: str) -> list:
    """获取科目的所有别名"""
    return SUBJECT_ALIASES.get(subject, [subject.lower()])
