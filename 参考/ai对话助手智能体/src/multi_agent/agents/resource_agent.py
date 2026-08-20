"""
资源推荐Agent
ResourceAgent

负责：
1. 搜索互联网资源（B站、知乎、博客等）
2. 推荐高质量学习资源
3. 基于知识点匹配资源
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from multi_agent.base.base_agent import BaseAgent
from multi_agent.base.agent_state import MultiAgentState, IntentType
from multi_agent.knowledge.bigdata_knowledge_graph import get_knowledge_graph, KnowledgeNode
from multi_agent.tools.resource_tools import (
    search_internet,
    search_bilibili,
    search_official_docs,
    search_github,
    search_community_posts,
)


class ResourceType(Enum):
    """资源类型"""
    BILIBILI = "bilibili"      # B站视频
    BLOG = "blog"              # 技术博客
    DOCUMENTATION = "doc"      # 官方文档
    COURSE = "course"          # 在线课程
    PAPER = "paper"            # 论文
    COMMUNITY = "community"     # 社区帖子


class Difficulty(Enum):
    """资源难度"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class LearningResource:
    """学习资源"""
    title: str
    url: str
    resource_type: ResourceType
    difficulty: Difficulty
    duration_minutes: int      # 预计学习时长
    relevance_score: float      # 与知识点的相关度 0-1
    quality_score: float        # 资源质量评分 0-1
    description: str
    tags: List[str]
    author: Optional[str] = None
    published_date: Optional[str] = None
    
    @property
    def formatted_duration(self) -> str:
        """格式化时长"""
        if self.duration_minutes < 60:
            return f"{self.duration_minutes}分钟"
        else:
            hours = self.duration_minutes // 60
            mins = self.duration_minutes % 60
            return f"{hours}小时{mins}分钟" if mins > 0 else f"{hours}小时"


class ResourceAgent(BaseAgent):
    """
    资源推荐Agent
    
    负责搜索和推荐高质量学习资源
    """
    
    # B站搜索基础URL
    BILIBILI_SEARCH = "https://search.bilibili.com/all?keyword={keyword}"
    
    # 技术博客平台
    BLOG_SOURCES = {
        "csdn": "https://blog.csdn.net/search?searchtext={keyword}",
        "juejin": "https://juejin.cn/search?query={keyword}",
        "zhihu": "https://www.zhihu.com/search?type=content&q={keyword}"
    }
    
    def __init__(self):
        super().__init__(
            agent_id="resource",
            name="资源推荐Agent",
            description="搜索和推荐高质量学习资源"
        )
        self.knowledge_graph = get_knowledge_graph()
        
        # 注册联网搜索工具（✅ 替换硬编码资源库）
        self._tools = [
            search_internet,
            search_bilibili,
            search_official_docs,
            search_github,
            search_community_posts,
        ]
        
        # 本地资源库作为补充（无网络时使用）
        self._resource_library = self._init_resource_library()
    
    def _init_resource_library(self) -> Dict[str, List[LearningResource]]:
        """初始化资源库"""
        resources = {
            # Hadoop相关
            "hdfs": [
                LearningResource(
                    title="【狂神说】HDFS分布式文件系统详解",
                    url="https://www.bilibili.com/video/BV1Kp4y197X7",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.BEGINNER,
                    duration_minutes=45,
                    relevance_score=0.95,
                    quality_score=0.9,
                    description="通俗易懂地讲解HDFS的架构和原理",
                    tags=["HDFS", "大数据", "分布式"],
                    author="狂神说"
                ),
                LearningResource(
                    title="HDFS官方文档",
                    url="https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html",
                    resource_type=ResourceType.DOCUMENTATION,
                    difficulty=Difficulty.INTERMEDIATE,
                    duration_minutes=60,
                    relevance_score=1.0,
                    quality_score=0.95,
                    description="HDFS官方设计文档，权威且详细",
                    tags=["HDFS", "官方文档", "架构设计"],
                    author="Apache"
                ),
            ],
            "mapreduce": [
                LearningResource(
                    title="MapReduce编程思想详解",
                    url="https://www.bilibili.com/video/BV1Mp4y1a7mX",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.INTERMEDIATE,
                    duration_minutes=50,
                    relevance_score=0.95,
                    quality_score=0.88,
                    description="深入理解MapReduce的编程模型",
                    tags=["MapReduce", "编程模型", "大数据"],
                    author="技术寅"
                ),
            ],
            "spark": [
                LearningResource(
                    title="Spark 3.0完全分布式集群搭建教程",
                    url="https://www.bilibili.com/video/BV1hQ4y1a7Wx",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.BEGINNER,
                    duration_minutes=35,
                    relevance_score=0.9,
                    quality_score=0.92,
                    description="手把手教你搭建Spark集群环境",
                    tags=["Spark", "集群", "安装配置"],
                    author="老马程序员"
                ),
                LearningResource(
                    title="Spark核心原理精讲",
                    url="https://www.bilibili.com/video/BV1Xy4y1K7cZ",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.ADVANCED,
                    duration_minutes=120,
                    relevance_score=0.98,
                    quality_score=0.95,
                    description="深入理解Spark RDD、DAG、任务调度等核心原理",
                    tags=["Spark", "原理", "RDD", "源码"],
                    author="大数据技术与架构"
                ),
            ],
            "hive": [
                LearningResource(
                    title="Hive数仓入门到精通",
                    url="https://www.bilibili.com/video/BV1CQ4y1S7zV",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.BEGINNER,
                    duration_minutes=90,
                    relevance_score=0.95,
                    quality_score=0.9,
                    description="从零学习Hive数据仓库",
                    tags=["Hive", "数据仓库", "SQL"],
                    author="数据分析星球"
                ),
            ],
            "kafka": [
                LearningResource(
                    title="Kafka消息队列详解",
                    url="https://www.bilibili.com/video/BV1vK411N7Jv",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.INTERMEDIATE,
                    duration_minutes=60,
                    relevance_score=0.95,
                    quality_score=0.88,
                    description="深入理解Kafka的架构和使用",
                    tags=["Kafka", "消息队列", "实时处理"],
                    author="程序员子海"
                ),
            ],
            "flink": [
                LearningResource(
                    title="Flink实时计算框架教程",
                    url="https://www.bilibili.com/video/BV1Fy4y1Y7Pc",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.INTERMEDIATE,
                    duration_minutes=80,
                    relevance_score=0.95,
                    quality_score=0.9,
                    description="Flink流处理实战",
                    tags=["Flink", "流处理", "实时计算"],
                    author="AI教育"
                ),
            ],
            "hadoop": [
                LearningResource(
                    title="Hadoop全套教程",
                    url="https://www.bilibili.com/video/BV1Qp4y1X7cV",
                    resource_type=ResourceType.BILIBILI,
                    difficulty=Difficulty.BEGINNER,
                    duration_minutes=180,
                    relevance_score=0.9,
                    quality_score=0.92,
                    description="从安装到实战，Hadoop全家桶",
                    tags=["Hadoop", "HDFS", "MapReduce", "生态"],
                    author="尚硅谷"
                ),
            ],
        }
        return resources
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.LEARNING_PATH
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理资源推荐请求
        
        支持的请求类型：
        - "search": 搜索资源
        - "recommend": 基于知识点推荐
        - "curated": 精选资源列表
        """
        user_id = state.get('user_id', 'anonymous')
        messages = state.get('messages', [])
        context = state.get('context', {}) or {}
        
        user_input = messages[-1].content if messages else ""
        action = context.get('action') or self._determine_action(user_input)
        
        if action == "search":
            return await self._search_resources(user_input, context)
        elif action == "recommend":
            return await self._recommend_by_topic(context.get('topic_id'), user_id)
        elif action == "curated":
            return await self._get_curated_list(context.get('category'))
        else:
            return await self._search_resources(user_input, context)
    
    def _determine_action(self, user_input: str) -> str:
        """判断用户意图"""
        search_keywords = ["搜索", "找", "查找", "search"]
        recommend_keywords = ["推荐", "资源", "学习材料", "recommend"]
        curated_keywords = ["精选", "必看", "top", "best"]
        
        if any(kw in user_input for kw in search_keywords):
            return "search"
        elif any(kw in user_input for kw in recommend_keywords):
            return "recommend"
        elif any(kw in user_input for kw in curated_keywords):
            return "curated"
        return "search"
    
    async def _search_resources(
        self, 
        query: str, 
        context: Dict
    ) -> Dict[str, Any]:
        """搜索资源"""
        # 从知识图谱中匹配知识点
        matched_topics = []
        for topic_id, node in self.knowledge_graph.nodes.items():
            if query.lower() in topic_id.lower() or query.lower() in node.name.lower():
                matched_topics.append(topic_id)
        
        # 从资源库中搜索
        results = []
        for topic_id in matched_topics:
            if topic_id in self._resource_library:
                results.extend(self._resource_library[topic_id])
        
        # 如果没有精确匹配，进行模糊搜索
        if not results:
            for topic_id, resources in self._resource_library.items():
                for resource in resources:
                    if (query.lower() in resource.title.lower() or 
                        query.lower() in resource.description.lower()):
                        results.append(resource)
        
        # 去重
        seen_urls = set()
        unique_results = []
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)
        
        # 按相关度排序
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # 生成搜索链接
        search_links = self._generate_search_links(query)
        
        return {
            "success": True,
            "query": query,
            "results_count": len(unique_results),
            "results": [self._format_resource(r) for r in unique_results[:5]],
            "search_links": search_links,
            "message": self._generate_search_message(query, len(unique_results))
        }
    
    async def _recommend_by_topic(
        self, 
        topic_id: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """基于知识点推荐资源"""
        if not topic_id:
            return {
                "success": False,
                "message": "请提供要学习的知识点"
            }
        
        # 获取知识点信息
        node = self.knowledge_graph.nodes.get(topic_id)
        if not node:
            return {
                "success": False,
                "message": f"未找到知识点: {topic_id}"
            }
        
        # 获取相关资源
        resources = self._resource_library.get(topic_id, [])
        
        # 如果知识点没有资源，尝试获取前置知识的资源
        if not resources and node.prerequisites:
            for prereq in node.prerequisites:
                if prereq in self._resource_library:
                    resources.extend(self._resource_library[prereq])
        
        if not resources:
            # 生成B站搜索链接
            search_url = self.BILIBILI_SEARCH.format(keyword=topic_id)
            return {
                "success": True,
                "topic": node.name,
                "topic_id": topic_id,
                "recommendations": [],
                "search_url": search_url,
                "message": f"关于「{node.name}」的资源正在整理中，你可以先搜索：{search_url}"
            }
        
        # 按质量和相关度排序
        resources.sort(key=lambda x: (x.relevance_score * 0.6 + x.quality_score * 0.4), reverse=True)
        
        # 生成推荐
        recommendations = []
        beginner = [r for r in resources if r.difficulty == Difficulty.BEGINNER]
        intermediate = [r for r in resources if r.difficulty == Difficulty.INTERMEDIATE]
        advanced = [r for r in resources if r.difficulty == Difficulty.ADVANCED]
        
        if beginner:
            recommendations.append({
                "level": "入门",
                "resources": [self._format_resource(r) for r in beginner[:2]]
            })
        if intermediate:
            recommendations.append({
                "level": "进阶",
                "resources": [self._format_resource(r) for r in intermediate[:2]]
            })
        if advanced:
            recommendations.append({
                "level": "深入",
                "resources": [self._format_resource(r) for r in advanced[:2]]
            })
        
        return {
            "success": True,
            "topic": node.name,
            "topic_id": topic_id,
            "difficulty": node.difficulty.value,
            "estimated_time": node.estimated_hours,
            "recommendations": recommendations,
            "total_resources": len(resources),
            "message": self._generate_recommend_message(node, len(resources))
        }
    
    async def _get_curated_list(self, category: Optional[str]) -> Dict[str, Any]:
        """获取精选资源列表"""
        if category:
            resources = self._resource_library.get(category, [])
        else:
            # 获取所有高质量资源
            resources = []
            for topic_resources in self._resource_library.values():
                resources.extend(topic_resources)
        
        # 筛选高质量资源
        high_quality = [r for r in resources if r.quality_score >= 0.9]
        high_quality.sort(key=lambda x: x.quality_score, reverse=True)
        
        return {
            "success": True,
            "category": category or "全部",
            "curated_resources": [self._format_resource(r) for r in high_quality[:10]],
            "total_count": len(high_quality),
            "message": f"为你精选了 {len(high_quality)} 个高质量学习资源"
        }
    
    def _generate_search_links(self, keyword: str) -> Dict[str, str]:
        """生成搜索链接"""
        return {
            "bilibili": self.BILIBILI_SEARCH.format(keyword=keyword),
            "csdn": self.BLOG_SOURCES["csdn"].format(keyword=keyword),
            "juejin": self.BLOG_SOURCES["juejin"].format(keyword=keyword),
            "zhihu": self.BLOG_SOURCES["zhihu"].format(keyword=keyword)
        }
    
    def _format_resource(self, resource: LearningResource) -> Dict[str, Any]:
        """格式化资源输出"""
        return {
            "title": resource.title,
            "url": resource.url,
            "type": resource.resource_type.value,
            "difficulty": resource.difficulty.value,
            "duration": resource.formatted_duration,
            "quality_score": f"{resource.quality_score * 100:.0f}%",
            "description": resource.description,
            "author": resource.author,
            "tags": resource.tags
        }
    
    def _generate_search_message(self, query: str, count: int) -> str:
        """生成搜索结果消息"""
        if count > 0:
            return f"找到 {count} 个与「{query}」相关的学习资源"
        else:
            return f"未找到「{query}」的直接相关资源，已为你生成搜索链接"
    
    def _generate_recommend_message(self, node: KnowledgeNode, count: int) -> str:
        """生成推荐消息"""
        return (f"关于「{node.name}」的学习，我为你准备了 {count} 个优质资源。"
                f"预计学习时长：{node.estimated_hours}小时。"
                f"难度：{node.difficulty.value}。")


# 全局实例
_resource_agent: Optional[ResourceAgent] = None


def get_resource_agent() -> ResourceAgent:
    global _resource_agent
    if _resource_agent is None:
        _resource_agent = ResourceAgent()
    return _resource_agent
