"""
Learning Path Agent - 学习路径规划Agent
功能：制定学习计划、追踪进度、管理推送
处理模式：协作式（依赖用户画像）
"""
import json
import logging
import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from ..base.base_agent import BaseAgent, CollaborativeAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context
from integrations.llm_factory import LLMFactory
from config.bigdata_knowledge import SUBJECTS, KNOWLEDGE_TREE

logger = logging.getLogger(__name__)


class LearningPathAgent(CollaborativeAgent):
    """
    学习路径Agent（协作式Agent）
    
    核心职责：
    1. 根据用户画像制定学习路径
    2. 追踪学习进度
    3. 管理学习里程碑
    4. 协调评估和推荐Agent
    
    依赖关系：
    - 输入：依赖ConversationAgent采集的用户画像
    - 输出：供给EvaluationAgent和RecommendationAgent使用
    """
    
    def __init__(self):
        super().__init__(
            agent_id="learning_path",
            name="学习路径Agent",
            description="负责制定学习计划和追踪学习进度"
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具
        self._tools = None
        
        # 注册协作回调
        self.register_callback("evaluation", self.on_evaluation_complete)
        self.register_callback("recommendation", self.on_recommendation_feedback)
        
        # LLM 客户端
        self._llm_client = None
        self._llm_initialized = False
        
        logger.info("[LearningPathAgent] Initialized")
    
    def _init_llm_client(self):
        """初始化 LLM 客户端 - 使用讯飞大模型"""
        if not self._llm_initialized:
            try:
                # 读取讯飞配置
                workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
                config_path = os.path.join(workspace_path, "config/agent_llm_config.json")
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                llm_config = {
                    "api_key": config.get("api_key") or config.get("config", {}).get("api_key"),
                    "api_secret": config.get("api_secret") or config.get("config", {}).get("api_secret"),
                    "app_id": config.get("app_id") or config.get("config", {}).get("app_id"),
                    "version": config.get("version") or config.get("config", {}).get("version", "x2"),
                    "temperature": config.get("temperature") or config.get("config", {}).get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens") or config.get("config", {}).get("max_tokens", 4096),
                }
                
                self._llm_client = LLMFactory.create("xunfei", llm_config)
                self._llm_initialized = True
                logger.info("[LearningPathAgent] LLM client (Xunfei) initialized")
            except Exception as e:
                logger.warning(f"[LearningPathAgent] Failed to initialize LLM client: {e}")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.LEARNING_PATH
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[LearningPathAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理学习路径规划请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing learning path request: {user_input[:50]}...")
        
        # 1. 获取用户画像
        user_profile = await self._get_user_profile(user_id)
        
        # 2. 解析学习目标
        goal = self._parse_learning_goal(user_input, user_profile)
        
        # 3. 生成学习路径
        learning_path = await self._generate_path(user_profile, goal, user_id)
        
        # 4. 保存学习路径
        save_result = await self._save_path(user_id, learning_path)
        
        # 5. 设置里程碑
        milestones = await self._setup_milestones(learning_path)
        
        # 6. 更新共享上下文
        await self._update_shared_context(user_id, learning_path)
        
        # 7. 通知下游Agent（协作）
        await self._notify_downstream_agents(user_id, learning_path)
        
        # 8. 生成友好响应
        response = self._format_response(user_profile, learning_path, milestones)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "user_profile": user_profile,
            "learning_path": learning_path,
            "milestones": milestones,
            "saved": save_result.get("success", False),
            "response": response
        }
    
    def _get_latest_user_input(self, state: MultiAgentState) -> str:
        """获取最新用户输入"""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            content = None
            if isinstance(msg, dict):
                content = msg.get("content", "")
            elif hasattr(msg, "content"):
                content = msg.content
            
            if content and isinstance(content, str):
                return content
        return ""
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        # 从共享上下文获取
        profile = self.shared_context.get_user_profile(user_id)
        
        if profile:
            return profile
        
        # 如果没有，从工具获取
        if self._tools and "get_user_profile" in self._tool_map:
            try:
                tool = self._tool_map["get_user_profile"]
                result = await asyncio.to_thread(tool.invoke, {"user_id": user_id})
                profile_data = json.loads(result) if isinstance(result, str) else result
                if profile_data.get("exists"):
                    return profile_data.get("profile", {})
            except Exception as e:
                self.log_error(f"Failed to get user profile: {e}")
        
        # 返回默认画像
        return self._get_default_profile()
    
    def _get_default_profile(self) -> Dict[str, Any]:
        """获取默认用户画像"""
        return {
            "user_id": "default_user",
            "learning_style": "视觉型",
            "knowledge_level": "初级",
            "learning_goal": "提升技能",
            "learning_speed": "中速",
            "learning_preference": {
                "study_time": "晚上",
                "content_type": ["图文", "视频"],
                "avoid_content": "大段文字",
                "focus_duration": 40
            }
        }
    
    def _parse_learning_goal(self, user_input: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """解析学习目标"""
        goal = {
            "subject": "通用",
            "target": "基础掌握",
            "duration_days": 30,
            "daily_hours": 2
        }
        
        # 识别科目 - 使用 RAG 数据中的知识点配置（大小写不敏感）
        try:
            from config.bigdata_knowledge import SUBJECTS, SUBJECT_KEYWORDS, TOPIC_KEYWORDS
            
            subjects = {}
            for subj in SUBJECTS:
                # 添加科目本身
                subjects[subj] = (subj, 45)
                # 添加科目关键词
                for keyword, keyword_subj in SUBJECT_KEYWORDS.items():
                    if keyword_subj == subj:
                        subjects[keyword] = (subj, 45)
            
            # 添加Topic关键词作为别名
            for keyword, topic_subj in TOPIC_KEYWORDS.items():
                if topic_subj not in subjects:
                    subjects[keyword] = (topic_subj, 45)
                    
        except ImportError:
            # 兜底：使用内置列表
            subjects = {
                "Python": ("Python编程", 30),
                "Java": ("Java编程", 30),
                "Hadoop": ("Hadoop大数据", 45),
                "Spark": ("Spark大数据", 30),
                "Flink": ("Flink实时计算", 45),
                "Kafka": ("Kafka消息队列", 30),
                "Hive": ("Hive数据仓库", 30),
                "大数据": ("大数据技术", 45),
                "数据仓库": ("数据仓库", 30),
            }
        
        # 大小写不敏感匹配
        user_input_lower = user_input.lower()
        for key, (subject, days) in subjects.items():
            if key.lower() in user_input_lower:
                goal["subject"] = subject
                goal["duration_days"] = days
                break
        
        # 识别目标级别
        if "精通" in user_input or "深入" in user_input:
            goal["target"] = "深入精通"
            goal["duration_days"] = int(goal["duration_days"] * 1.5)
        elif "入门" in user_input or "基础" in user_input:
            goal["target"] = "入门掌握"
            goal["duration_days"] = int(goal["duration_days"] * 0.5)
        
        # 识别时间
        if "周" in user_input:
            import re
            week_match = re.search(r'(\d+)\s*周', user_input)
            if week_match:
                goal["duration_days"] = int(week_match.group(1)) * 7
        elif "月" in user_input:
            import re
            month_match = re.search(r'(\d+)\s*个月', user_input)
            if month_match:
                goal["duration_days"] = int(month_match.group(1)) * 30
        
        return goal
    
    async def _generate_path(self, user_profile: Dict[str, Any], goal: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        """生成学习路径"""
        subject = goal.get("subject", "通用")
        knowledge_level = user_profile.get("knowledge_level", "初级")
        learning_speed = user_profile.get("learning_speed", "中速")
        
        # 初始化 LLM 客户端
        self._init_llm_client()
        
        # 尝试使用 LLM 生成真实学习路径
        if self._llm_client:
            try:
                llm_result = await self._generate_path_with_llm(subject, knowledge_level, learning_speed)
                if llm_result:
                    return llm_result
            except Exception as e:
                self.log_error(f"LLM generation failed: {e}")
        
        # 如果 LLM 不可用或失败，尝试使用工具
        if self._tools and "generate_learning_path" in self._tool_map:
            try:
                tool = self._tool_map["generate_learning_path"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "user_id": user_id,
                        "subject": subject,
                        "knowledge_level": knowledge_level,
                        "learning_speed": learning_speed
                    }
                )
                path_data = json.loads(result) if isinstance(result, str) else result
                return path_data.get("learning_path", {})
            except Exception as e:
                self.log_error(f"Failed to generate learning path: {e}")
        
        # 生成默认学习路径
        return self._create_default_path(user_profile, goal)
    
    async def _generate_path_with_llm(self, subject: str, knowledge_level: str, learning_speed: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成学习路径"""
        if not self._llm_client:
            return None
        
        # 获取科目的知识点
        topics_data = KNOWLEDGE_TREE.get(subject, {})
        base_topics = topics_data.get("topics", [])
        
        # 获取科目说明
        topic_desc = ""
        if base_topics:
            topic_desc = "，" .join(base_topics[:10])  # 最多10个核心知识点
        
        prompt = f"""请为"{subject}"科目制定一个专业的学习计划。

科目说明：{topic_desc if topic_desc else "大数据相关技术"}

学习者信息：
- 知识水平：{knowledge_level}
- 学习速度：{learning_speed}

要求：
1. 生成一个完整的Markdown格式学习计划
2. 包含3-5个学习阶段，每个阶段有明确的主题和具体知识点
3. 每个阶段需要包含：标题、主题说明、学习活动、里程碑
4. 内容要专业、具体，体现{subject}的核心知识点和实际应用
5. 结合学习者的水平和速度调整内容深度

请直接输出学习计划内容，不要有其他解释说明。"""

        messages = [{'role': 'user', 'content': prompt}]
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._llm_client.chat(messages)
            )
            
            if result and len(result) > 50:
                return {
                    "generated_by": "llm",
                    "subject": subject,
                    "knowledge_level": knowledge_level,
                    "learning_speed": learning_speed,
                    "raw_content": result,
                    "created_at": datetime.now().isoformat()
                }
        except Exception as e:
            self.log_error(f"LLM chat failed: {e}")
        
        return None
    
    def _create_default_path(self, user_profile: Dict[str, Any], goal: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认学习路径 - 根据科目生成有意义的学习阶段"""
        subject = goal.get("subject", "通用")
        duration = goal.get("duration_days", 30)
        level = user_profile.get("knowledge_level", "初级")
        
        # 根据时长计算阶段数
        if duration <= 14:
            num_stages = 2
        elif duration <= 30:
            num_stages = 3
        elif duration <= 60:
            num_stages = 4
        else:
            num_stages = 5
        
        days_per_stage = duration // num_stages
        
        # 根据科目定义学习阶段和主题
        learning_path_templates = {
            "Python编程": {
                2: [
                    {"title": "基础入门", "topics": ["Python环境搭建", "变量与数据类型", "基本语法"], "milestone": "完成基础语法测试"},
                    {"title": "进阶应用", "topics": ["函数与模块", "面向对象基础", "文件操作"], "milestone": "完成简单项目"}
                ],
                3: [
                    {"title": "基础入门", "topics": ["Python环境搭建", "变量与数据类型", "条件与循环", "函数基础"], "milestone": "完成基础语法测试"},
                    {"title": "核心技能", "topics": ["函数进阶", "面向对象编程", "异常处理", "模块与包"], "milestone": "完成核心技能测试"},
                    {"title": "实战应用", "topics": ["文件操作", "网络编程基础", "数据库操作", "项目实战"], "milestone": "完成实战项目"}
                ],
                4: [
                    {"title": "基础入门", "topics": ["环境搭建", "变量与数据类型", "控制流", "函数基础"], "milestone": "完成基础测试"},
                    {"title": "核心进阶", "topics": ["函数高级特性", "面向对象", "异常处理", "模块管理"], "milestone": "完成进阶测试"},
                    {"title": "实用技术", "topics": ["文件与IO", "网络编程", "数据库", "多线程"], "milestone": "完成实用技术项目"},
                    {"title": "项目实战", "topics": ["Web开发基础", "数据分析入门", "自动化脚本", "综合项目"], "milestone": "完成毕业项目"}
                ],
                5: [
                    {"title": "环境与基础", "topics": ["环境搭建", "数据类型", "控制流"], "milestone": "完成环境测试"},
                    {"title": "函数与模块", "topics": ["函数编程", "模块管理", "包与发布"], "milestone": "完成函数测试"},
                    {"title": "面向对象", "topics": ["类与对象", "继承多态", "设计模式"], "milestone": "完成OOP测试"},
                    {"title": "高级特性", "topics": ["装饰器", "生成器", "并发编程"], "milestone": "完成高级测试"},
                    {"title": "项目实战", "topics": ["Web开发", "数据分析", "自动化", "毕业项目"], "milestone": "完成毕业项目"}
                ]
            },
            "网络安全": {
                3: [
                    {"title": "安全基础", "topics": ["网络安全概述", "常见攻击类型", "安全原则"], "milestone": "完成安全基础测试"},
                    {"title": "攻防技术", "topics": ["SQL注入防护", "XSS攻击防御", "CSRF防护"], "milestone": "完成攻防测试"},
                    {"title": "实战提升", "topics": ["渗透测试入门", "漏洞扫描", "安全工具使用"], "milestone": "完成实战项目"}
                ]
            },
            "Java编程": {
                3: [
                    {"title": "Java基础", "topics": ["环境配置", "语法基础", "面向对象"], "milestone": "完成Java基础测试"},
                    {"title": "核心特性", "topics": ["集合框架", "异常处理", "IO流", "多线程"], "milestone": "完成核心特性测试"},
                    {"title": "Web开发", "topics": ["Servlet/JSP", "数据库连接", "框架入门"], "milestone": "完成Web项目"}
                ]
            },
            # ✅ 大数据技术学习模板
            "Hadoop大数据": {
                3: [
                    {"title": "Hadoop基础", "topics": ["Hadoop概述", "HDFS分布式文件系统", "NameNode与DataNode", "环境搭建"], "milestone": "完成Hadoop基础测试"},
                    {"title": "MapReduce核心", "topics": ["MapReduce编程模型", "WordCount实战", "Combiner与Partitioner", "YARN资源调度"], "milestone": "完成MapReduce实战"},
                    {"title": "Hadoop生态", "topics": ["Hive数据仓库", "HBase NoSQL", "Sqoop数据迁移", "企业实战项目"], "milestone": "完成大数据项目"}
                ],
                4: [
                    {"title": "Hadoop基础与HDFS", "topics": ["Hadoop概述与架构", "HDFS原理", "HDFS Java API", "环境集群搭建"], "milestone": "完成HDFS实战"},
                    {"title": "MapReduce编程", "topics": ["MapReduce核心流程", "Combiner与Partitioner", "多Job串联", "性能优化"], "milestone": "完成MapReduce项目"},
                    {"title": "YARN与资源管理", "topics": ["YARN架构", "资源调度策略", "容量调度器", "公平调度器"], "milestone": "完成YARN配置"},
                    {"title": "Hadoop生态实战", "topics": ["Hive数仓", "HBase数据库", "Kafka消息队列", "综合项目"], "milestone": "完成生态项目"}
                ]
            },
            "Spark大数据": {
                3: [
                    {"title": "Spark基础", "topics": ["Spark概述与架构", "RDD编程模型", "SparkConf与SparkContext", "环境搭建"], "milestone": "完成Spark基础测试"},
                    {"title": "Spark Core进阶", "topics": ["Transformation与Action", "累加器与广播变量", "数据倾斜处理", "Shuffle机制"], "milestone": "完成Spark Core实战"},
                    {"title": "Spark生态应用", "topics": ["Spark SQL结构化数据", "Spark Streaming实时处理", "MLlib机器学习", "企业项目实战"], "milestone": "完成Spark综合项目"}
                ],
                4: [
                    {"title": "Spark环境与基础", "topics": ["Spark架构原理", "RDD设计与特性", "SparkSession", "开发环境搭建"], "milestone": "完成Spark入门"},
                    {"title": "Spark Core核心", "topics": ["RDD算子详解", "依赖与stage划分", "Shuffle优化", "内存管理"], "milestone": "完成Core进阶"},
                    {"title": "Spark SQL实战", "topics": ["DataFrame与Dataset", "Spark SQL执行流程", "UDF与开窗函数", "性能调优"], "milestone": "完成SQL项目"},
                    {"title": "Spark高级应用", "topics": ["Structured Streaming", "MLlib机器学习", "Spark综合项目", "生产环境部署"], "milestone": "完成高级项目"}
                ]
            },
            "Flink实时计算": {
                3: [
                    {"title": "Flink基础", "topics": ["Flink概述", "流处理基本概念", "DataStream API", "环境搭建"], "milestone": "完成Flink基础测试"},
                    {"title": "Flink核心", "topics": ["Time与Window", "State状态管理", "Checkpoint与Savepoint", "容错机制"], "milestone": "完成Flink核心实战"},
                    {"title": "Flink实战", "topics": ["Table API与SQL", "CEP复杂事件处理", "Kafka集成", "实时项目"], "milestone": "完成Flink项目"}
                ]
            },
            "机器学习": {
                3: [
                    {"title": "机器学习基础", "topics": ["机器学习概述", "监督学习基础", "线性回归与逻辑回归", "评估指标"], "milestone": "完成ML基础测试"},
                    {"title": "经典算法", "topics": ["决策树与随机森林", "SVM支持向量机", "朴素贝叶斯", "聚类算法"], "milestone": "完成算法实战"},
                    {"title": "项目实战", "topics": ["特征工程", "模型调参与集成", "Spark MLlib实战", "项目综合"], "milestone": "完成项目实战"}
                ]
            }
        }
        
        # 获取对应科目的模板
        stage_templates = learning_path_templates.get(subject, {}).get(num_stages)
        
        if stage_templates is None:
            # 使用通用模板
            stage_names = {
                2: ["基础阶段", "进阶阶段"],
                3: ["基础阶段", "提升阶段", "实战阶段"],
                4: ["入门阶段", "基础阶段", "进阶阶段", "实战阶段"],
                5: ["入门阶段", "基础阶段", "提升阶段", "进阶阶段", "实战阶段"]
            }
            # ✅ 改进通用模板：为每个科目生成有意义的默认 topics
            generic_topic_templates = {
                "通用": ["核心概念入门", "基础技能掌握", "实践应用提升"],
                "Hadoop大数据": ["Hadoop概述与HDFS", "MapReduce编程", "YARN资源管理", "Hive数据仓库"],
                "Spark大数据": ["Spark概述与RDD", "DataFrame与Spark SQL", "Spark Streaming实时处理", "MLlib机器学习"],
                "Flink实时计算": ["Flink流处理基础", "Time与Window", "State与Checkpoint", "Table API与CEP"],
                "机器学习": ["机器学习基础概念", "监督学习算法", "无监督学习", "模型评估与调优"],
                "深度学习": ["神经网络基础", "卷积神经网络CNN", "循环神经网络RNN", "Transformer与注意力机制"],
                "大数据技术": ["Hadoop生态概述", "HDFS分布式存储", "MapReduce批处理", "Kafka+Flink实时处理"],
                "数据仓库": ["数仓架构设计", "HiveQL与ETL", "数据建模与分层", "OLAP与BI分析"],
            }
            default_topics = generic_topic_templates.get(subject, [f"{subject}核心概念", f"{subject}基础技能", f"{subject}实践应用"])
            stage_templates = [
                {
                    "title": stage_names.get(num_stages, ["阶段"])[i] if i < len(stage_names.get(num_stages, [])) else f"阶段{i+1}",
                    "topics": default_topics[i % len(default_topics)] if i < len(default_topics) else [f"{subject}核心概念", f"{subject}基础技能", f"{subject}实践应用"],
                    "milestone": f"完成{stage_names.get(num_stages, ['阶段'])[i]}测试"
                }
                for i in range(num_stages)
            ]
        
        stages = []
        for i in range(num_stages):
            template = stage_templates[i] if i < len(stage_templates) else stage_templates[-1]
            stages.append({
                "stage_id": i + 1,
                "title": template["title"],
                "topics": template["topics"],
                "activities": ["视频学习", "文档阅读", "练习题", "项目实践"],
                "milestone": template["milestone"],
                "prerequisites": [stages[i-1]["title"]] if i > 0 else [],
                "duration_days": days_per_stage
            })
        
        return {
            "meta": {
                "user_id": user_profile.get("user_id", "default_user"),
                "subject": subject,
                "knowledge_level": level,
                "learning_speed": user_profile.get("learning_speed", "中速"),
                "content_difficulty": "初级" if level == "初级" else "中级",
                "total_stages": num_stages,
                "estimated_duration": f"{duration}天"
            },
            "stages": stages
        }
    
    async def _save_path(self, user_id: str, learning_path: Dict[str, Any]) -> Dict[str, Any]:
        """保存学习路径"""
        if self._tools and "save_learning_path" in self._tool_map:
            try:
                tool = self._tool_map["save_learning_path"]
                # 从 learning_path 中提取 subject
                subject = learning_path.get("subject", learning_path.get("title", "未知科目"))
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "user_id": user_id,
                        "subject": subject,
                        "path_data": json.dumps(learning_path)
                    }
                )
                save_result = json.loads(result) if isinstance(result, str) else result
                return save_result
            except Exception as e:
                self.log_error(f"Failed to save learning path: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": True, "simulated": True}
    
    async def _setup_milestones(self, learning_path: Dict[str, Any]) -> List[Dict[str, Any]]:
        """设置学习里程碑"""
        stages = learning_path.get("stages", [])
        
        milestones = []
        for stage in stages:
            milestones.append({
                "stage_id": stage.get("stage_id"),
                "title": stage.get("title"),
                "milestone": stage.get("milestone"),
                "status": "pending"
            })
        
        return milestones
    
    async def _update_shared_context(self, user_id: str, learning_path: Dict[str, Any]):
        """更新共享上下文"""
        subject = learning_path.get("meta", {}).get("subject", "通用")
        self.shared_context.update_learning_progress(
            user_id,
            {"current_topic": subject, "progress": 0.0}
        )
    
    async def _notify_downstream_agents(self, user_id: str, learning_path: Dict[str, Any]):
        """通知下游Agent（协作流程）"""
        # 向EvaluationAgent发送任务
        await self.send_to_agent(
            "evaluation",
            {
                "task": "setup_evaluations",
                "user_id": user_id,
                "learning_path": learning_path
            }
        )
        
        # 向RecommendationAgent发送任务
        await self.send_to_agent(
            "recommendation",
            {
                "task": "plan_recommendations",
                "user_id": user_id,
                "learning_path": learning_path
            }
        )
    
    async def on_evaluation_complete(self, data: Dict[str, Any]):
        """评估完成回调"""
        user_id = data.get("user_id")
        evaluation_results = data.get("results", {})
        
        # 根据评估结果调整学习路径
        self.log_info(f"Received evaluation results for user {user_id}")
        
        # 更新学习进度
        if evaluation_results.get("overall_score"):
            self.shared_context.update_learning_progress(
                user_id,
                {"current_subject": evaluation_results.get("progress", 0)}
            )
    
    async def on_recommendation_feedback(self, data: Dict[str, Any]):
        """推荐反馈回调"""
        user_id = data.get("user_id")
        feedback = data.get("feedback", {})
        
        self.log_info(f"Received recommendation feedback for user {user_id}")
        
        # 根据反馈调整推荐策略
        # ...
    
    def _format_response(
        self,
        user_profile: Dict[str, Any],
        learning_path: Dict[str, Any],
        milestones: List[Dict[str, Any]]
    ) -> str:
        """格式化响应内容 - 返回完整的 LLM 生成内容"""
        # 如果 LLM 生成了完整内容，直接返回
        raw_content = learning_path.get("raw_content", "")
        if raw_content and len(raw_content) > 100:
            return raw_content
        
        # 兜底：生成摘要
        meta = learning_path.get("meta", {})
        stages = learning_path.get("stages", [])
        subject = meta.get("subject", "该科目")
        duration = meta.get("estimated_duration", "30天")
        
        response = f"""太棒了！🚀 给你制定了一个 **{subject}** 学习计划

**📊 学习者特征**
- 学习风格：{user_profile.get('learning_style', '视觉型')}
- 知识水平：{user_profile.get('knowledge_level', '初级')}
- 学习速度：{user_profile.get('learning_speed', '中速')}

**📅 计划总览**
- 总时长：{duration}
- 阶段数：{len(stages)}个阶段
- 预计完成：{meta.get('estimated_duration', '30天')}

"""
        
        for stage in stages[:3]:
            response += f"""**阶段{stage.get('stage_id')}：{stage.get('title')}**
- 主题：{', '.join(stage.get('topics', [])[:2])}
- 活动：{'、'.join(stage.get('activities', [])[:2])}
- 里程碑：{stage.get('milestone')}

"""
        
        response += """---
加油！💪 遇到困难咱们一起想办法，坚持就是胜利！

有不懂的地方随时问我，我会一直陪着你~"""
        
        return response


# 全局实例
_learning_path_agent: Optional[LearningPathAgent] = None


def get_learning_path_agent() -> LearningPathAgent:
    """获取全局LearningPathAgent实例"""
    global _learning_path_agent
    if _learning_path_agent is None:
        _learning_path_agent = LearningPathAgent()
    return _learning_path_agent
