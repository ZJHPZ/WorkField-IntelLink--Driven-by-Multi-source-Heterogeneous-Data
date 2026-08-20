"""L2 归一化 + 频次统计 + 置信度计算。

设计方案 §4.3 / §3.2 / §3.4：
- 归一化：种子映射表 + 大小写统一（K8s→Kubernetes）
- 频次统计：跨 JD 统计每个技能的 DF（文档频率）
- 置信度：融合 DF、信源权重、位置权重、时间新鲜度、通胀惩罚
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from app.domain import SkillStat
from app.utils.text import sigmoid

# ══════════════════════════════════════════════
# 种子别名映射表（设计方案 §4.3）
# ══════════════════════════════════════════════

SKILL_ALIASES: dict[str, str] = {
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "容器编排": "Kubernetes",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "大模型微调": "大模型微调",
    "模型微调": "大模型微调",
    "rag": "RAG",
    "检索增强": "RAG",
    "transformer": "Transformer",
    "cuda": "CUDA",
    "hugging face": "HuggingFace",
    "huggingface": "HuggingFace",
    "spark": "Spark",
    "flink": "Flink",
    "hadoop": "Hadoop",
    "kafka": "Kafka",
    "golang": "Go",
    "go语言": "Go",
    "c语言": "C语言",
    "sql": "SQL",
    "etl": "ETL",
    "clickhouse": "ClickHouse",
    "doris": "Doris",
    "airflow": "Airflow",
    "olap": "OLAP",
    "vllm": "vLLM",
    "rtos": "RTOS",
    "freertos": "FreeRTOS",
    "深度学习": "深度学习",
    "向量检索": "向量数据库",
    "向量数据库": "向量数据库",
    "微服务": "微服务",
    "docker": "Docker",
    "mqtt": "MQTT",
    "边缘计算": "边缘计算",
    "嵌入式开发": "嵌入式开发",
    "嵌入式": "嵌入式开发",
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "react": "React",
    "vue": "Vue",
    "redis": "Redis",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "nginx": "Nginx",
    "elasticsearch": "Elasticsearch",
    "es": "Elasticsearch",
    "git": "Git",
    "linux": "Linux",
}

# 信号词前缀剥离正则
_SIGNAL_PREFIX = re.compile(
    r"^(熟悉|掌握|精通|了解|熟练掌握|熟练|会|具备|使用|能|善于)"
)


def normalize_name(raw: str) -> str:
    """把技能原始名归一化到规范名。

    步骤：剥信号词前缀 → 去尾部标点 → 英文/中文空格压缩 → 查别名表 →
    命中即规范名，否则返回清洗后的原文。
    """
    s = raw.strip()
    # 剥信号词前缀（"熟悉Kubernetes" → "Kubernetes"）
    prev = None
    while prev != s:
        prev = s
        s = _SIGNAL_PREFIX.sub("", s).strip()
    s = s.strip("，。、；;,. 　")
    # 英文与中文之间空格压缩
    s = re.sub(r"([A-Za-z0-9])\s+([一-鿿])", r"\1\2", s)
    s = re.sub(r"([一-鿿])\s+([A-Za-z0-9])", r"\1\2", s)
    key = s.lower()
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    return s


# ══════════════════════════════════════════════
# 信源权重（设计方案 §3.4）
# ══════════════════════════════════════════════

SOURCE_WEIGHTS = {
    "authority": 1.0,   # 权威源（官方文档/白皮书/职业大典）
    "trend": 0.9,       # 趋势源（GitHub/arXiv）
    "demand": 0.6,      # 需求源（招聘 JD）
    "reference": 0.3,   # 参照源（技术栈词表）
    "unknown": 0.4,
}

# 抽取方式乘数（LLM 有语义理解能力，权重更高）
EXTRACTION_MULTIPLIER = {
    "spark": 1.0,       # 星火 LLM 抽取
    "rule": 0.5,        # 规则引擎（信号词模式匹配）
    "manual": 0.8,      # 人工添加
}


def classify_source(source_id: str) -> str:
    """根据来源 ID 推断信源类型。"""
    if not source_id:
        return "unknown"
    sid = source_id.lower()
    if "github" in sid or "arxiv" in sid:
        return "trend"
    authority_kw = ["职业大典", "白皮书", "行业标准", "国家标准", "官方"]
    if any(kw in sid for kw in authority_kw):
        return "authority"
    jd_kw = ["jd", "job", "招聘", "职位", "岗位", "syn-", "real-", "demo-"]
    if any(kw in sid for kw in jd_kw):
        return "demand"
    ref_kw = ["词表", "词库", "ontology", "wiki"]
    if any(kw in sid for kw in ref_kw):
        return "reference"
    return "unknown"


# ══════════════════════════════════════════════
# 置信度计算（设计方案 §3.4）
# ══════════════════════════════════════════════

# 公式权重（初值，用金标准集网格搜索调优）
DEFAULT_CONFIDENCE_WEIGHTS = {
    "w1": 0.4,  # DF 权重
    "w2": 0.3,  # 信源权重
    "w3": 0.1,  # 位置权重
    "w4": 0.2,  # 时间新鲜度
    "w5": 0.2,  # 通胀惩罚
}


def compute_confidence(
    df: int,
    source_count: int = 1,
    is_required: bool = True,
    months_ago: int = 0,
    inflation_score: float = 0.0,
    weights: dict | None = None,
    source_weight: float = 0.6,
    extraction_mult: float = 1.0,
) -> float:
    """计算技能置信度。

    confidence = sigmoid(
        w1·log(1+DF) + w2·Σ(信源权重 × 抽取方式乘数) + w3·位置权重
        + w4·时间新鲜度 - w5·通胀惩罚
    )

    Args:
        df: 文档频率
        source_count: 来源数
        is_required: 是否必备技能
        months_ago: 首次出现距今月数
        inflation_score: 通胀惩罚分
        weights: 自定义公式权重
        source_weight: 信源类型权重 (authority/trend/demand/reference/unknown)
        extraction_mult: 抽取方式乘数 (spark=1.0, rule=0.5, manual=0.8)
    """
    w = weights or DEFAULT_CONFIDENCE_WEIGHTS
    if df == 0:
        return 0.1
    df_term = w["w1"] * math.log(1 + df)
    source_term = w["w2"] * source_count * source_weight * extraction_mult
    pos_term = w["w3"] * (1.0 if is_required else 0.3)
    decay_rate = 0.1
    freshness_term = w["w4"] * math.exp(-decay_rate * months_ago)
    inflation_term = w["w5"] * inflation_score
    score = df_term + source_term + pos_term + freshness_term - inflation_term
    return round(sigmoid(score), 3)


# ══════════════════════════════════════════════
# 归一化 + 统计（主函数）
# ══════════════════════════════════════════════

def normalize_and_count(
    extracted_by_jd: list[tuple[str, str, list]],
    inflation_scores: dict[str, float] | None = None,
) -> dict[str, SkillStat]:
    """输入 [(jd_id, tech_stack, [ExtractedSkill,...]), ...]，输出 {规范名: SkillStat}。

    信源权重：五档（authority 1.0 > trend 0.9 > demand 0.6 > unknown 0.4 > reference 0.3）
    抽取方式乘数：spark(LLM) 1.0 > manual 0.8 > rule 0.5
    过滤规则：归一化后长度 < 2 的技能名直接丢弃

    Args:
        extracted_by_jd: 抽取结果列表
        inflation_scores: {jd_id: 通胀评分}，可选

    Returns:
        {规范名: SkillStat}
    """
    stats: dict[str, SkillStat] = {}
    total_jd = len(extracted_by_jd)
    filtered_count = 0

    for jd_id, tech_stack, skills in extracted_by_jd:
        seen_in_this_jd: set[str] = set()
        inflation = inflation_scores.get(jd_id, 0.0) if inflation_scores else 0.0
        source_type = classify_source(jd_id)

        for sk in skills:
            # 兼容 dict 和 ExtractedSkill
            name = getattr(sk, "name", None)
            if name is None:
                name = sk.get("name", "") if isinstance(sk, dict) else ""
            canon = normalize_name(name)

            # 过滤：归一化后长度 < 2 的技能名（A, B, C, 3D 等噪声）
            if len(canon) < 2:
                filtered_count += 1
                continue

            if canon not in stats:
                stats[canon] = SkillStat(name=canon)
            st = stats[canon]
            st.tech_stacks.append(tech_stack)

            rtype = getattr(sk, "required_type", None)
            if rtype is None:
                rtype = sk.get("required_type", "必备") if isinstance(sk, dict) else "必备"
            if rtype == "必备":
                st.required_count += 1
            else:
                st.bonus_count += 1

            # 记录抽取方式（取最高权重的方式）
            extraction_src = getattr(sk, "source", None) or (sk.get("source", "rule") if isinstance(sk, dict) else "rule")
            if not hasattr(st, '_extraction_sources'):
                st._extraction_sources = []
            st._extraction_sources.append(extraction_src)

            # DF 按 JD 去重
            if canon not in seen_in_this_jd:
                st.df += 1
                seen_in_this_jd.add(canon)

    if filtered_count:
        import logging
        logging.getLogger(__name__).info(f"归一化过滤：丢弃 {filtered_count} 个长度<2的技能名")

    # 计算置信度（融合信源类型 × 抽取方式）
    for st in stats.values():
        total = st.required_count + st.bonus_count
        is_required = (st.required_count / total > 0.5) if total > 0 else False

        # 孤证判断（设计方案 §3.4）
        if st.df <= 1:
            st.verification_status = "candidate" if st.df == 1 else "unverified"
        elif st.df >= 2:
            st.verification_status = "confirmed"

        # 信源权重
        src_weight = SOURCE_WEIGHTS.get(source_type, 0.4)

        # 抽取方式乘数（取所有来源中最高的）
        sources = getattr(st, '_extraction_sources', ['rule'])
        extraction_mult = max(EXTRACTION_MULTIPLIER.get(s, 0.5) for s in sources)

        st.confidence = compute_confidence(
            df=st.df,
            source_count=min(st.df, 3),
            is_required=is_required,
            source_weight=src_weight,
            extraction_mult=extraction_mult,
        )

        # 清理临时属性
        if hasattr(st, '_extraction_sources'):
            delattr(st, '_extraction_sources')

    return stats
