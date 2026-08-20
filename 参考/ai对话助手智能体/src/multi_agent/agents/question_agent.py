"""
Question Agent - 题库与练习Agent
功能：生成练习题、评估答案、管理题库
处理模式：联邦式（独立处理）
"""
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class QuestionAgent(BaseAgent):
    """
    题库Agent
    
    核心职责：
    1. 生成各类练习题（选择、简答、编程）
    2. 管理题库数据
    3. 评估用户答案
    4. 提供练习反馈
    """
    
    def __init__(self):
        super().__init__(
            agent_id="question",
            name="题库练习Agent",
            description="负责生成练习题和管理题库",
            processing_mode=ProcessingMode.FEDERATED
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具（将在初始化时绑定）
        self._tools = None
        
        # LLM 客户端（讯飞大模型）
        self._llm_client = None
        
        # 初始化 LLM 客户端
        self._init_llm_client()
        
        logger.info("[QuestionAgent] Initialized")
    
    def _init_llm_client(self):
        """初始化讯飞大模型客户端"""
        try:
            from integrations.llm_factory import create_llm_from_config
            self._llm_client = create_llm_from_config()
            logger.info("[QuestionAgent] LLM client initialized (XunfeiAdapter)")
        except Exception as e:
            logger.warning(f"[QuestionAgent] Failed to initialize LLM client: {e}")
            self._llm_client = None
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.QUESTION
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[QuestionAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理练习题生成请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing question request: {user_input[:50]}...")
        
        # 解析用户请求
        params = self._parse_request(user_input)
        subject = params.get("subject", "通用")
        topic = params.get("topic", "基础")
        difficulty = params.get("difficulty", "中等")
        count = params.get("count", 5)
        
        results = {}
        
        # 1. 生成选择题
        mc_result = await self._generate_multiple_choice(subject, topic, difficulty, count)
        results["multiple_choice"] = mc_result
        
        # 2. 生成简答题
        sa_result = await self._generate_short_answer(subject, topic, difficulty, count // 2)
        results["short_answer"] = sa_result
        
        # 3. 生成编程题（如果有）
        if params.get("include_code", False):
            code_result = await self._generate_coding(subject, topic, difficulty, count // 3)
            results["coding"] = code_result
        
        # 4. 保存题目
        save_result = await self._save_questions(
            user_id, subject, topic, difficulty, mc_result, sa_result
        )
        results["saved"] = save_result
        
        # 5. 生成友好响应
        response = self._format_response(subject, topic, mc_result, sa_result)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "multiple_choice": mc_result,
            "short_answer": sa_result,
            "saved": save_result.get("success", False),
            "response": response,
            # 标准格式：包装在 answer 字段中
            "answer": {
                "type": "question",
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "multiple_choice": mc_result,
                "short_answer": sa_result,
                "count": len(mc_result) + len(sa_result),
                "content": response
            }
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
    
    def _parse_request(self, user_input: str) -> Dict[str, Any]:
        """解析用户请求"""
        params = {
            "subject": "通用",
            "topic": "基础知识",
            "difficulty": "中等",
            "count": 5,
            "include_code": False
        }
        
        # 识别科目
        subjects = {
            # 编程语言
            "Python": "Python",
            "Java": "Java",
            "JavaScript": "JavaScript",
            "Go": "Go",
            "C++": "C++",
            "C语言": "C语言",
            # 技术领域
            "网络安全": "网络安全",
            "数据结构": "数据结构",
            "算法": "算法",
            # 大数据技术
            "hadoop": "Hadoop",
            "spark": "Spark",
            "flink": "Flink",
            "kafka": "Kafka",
            "hive": "Hive",
            "hbase": "HBase",
            "zookeeper": "Zookeeper",
            "大数据": "大数据",
            # 运维技术
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "linux": "Linux",
            "git": "Git",
            # 数据库
            "mysql": "MySQL",
            "redis": "Redis",
            "mongodb": "MongoDB",
            "数据库": "数据库",
        }
        user_input_lower = user_input.lower()
        for key, value in subjects.items():
            if key.lower() in user_input_lower:
                params["subject"] = value
                params["topic"] = value
                break
        
        # 识别难度
        if any(kw in user_input for kw in ["简单", "基础", "入门"]):
            params["difficulty"] = "简单"
        elif any(kw in user_input for kw in ["困难", "高级", "复杂"]):
            params["difficulty"] = "困难"
        
        # 识别数量
        import re
        count_match = re.search(r'(\d+)\s*道', user_input)
        if count_match:
            params["count"] = int(count_match.group(1))
        
        # 识别是否包含编程题
        if "编程" in user_input or "代码" in user_input:
            params["include_code"] = True
        
        return params
    
    async def _generate_multiple_choice(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        count: int
    ) -> Dict[str, Any]:
        """生成选择题"""
        if self._tools and "generate_multiple_choice" in self._tool_map:
            try:
                tool = self._tool_map["generate_multiple_choice"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "difficulty": difficulty,
                        "count": count
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to generate multiple choice: {e}")
        
        # 生成默认选择题
        return await self._create_default_multiple_choice(subject, topic, difficulty, count)
    
    async def _create_default_multiple_choice(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        count: int
    ) -> Dict[str, Any]:
        """创建默认选择题 - 根据科目和主题生成有意义的题目"""
        questions = []
        
        # 根据不同科目和主题定义题目模板
        question_templates = {
            "Python": {
                "基础语法": [
                    {
                        "question": "以下哪个是Python中定义函数的关键字？",
                        "options": [
                            {"key": "A", "text": "def"},
                            {"key": "B", "text": "function"},
                            {"key": "C", "text": "func"},
                            {"key": "D", "text": "define"}
                        ],
                        "answer": "A",
                        "explanation": "Python使用def关键字来定义函数。"
                    },
                    {
                        "question": "Python中以下哪种数据类型是不可变的？",
                        "options": [
                            {"key": "A", "text": "列表（list）"},
                            {"key": "B", "text": "字典（dict）"},
                            {"key": "C", "text": "元组（tuple）"},
                            {"key": "D", "text": "集合（set）"}
                        ],
                        "answer": "C",
                        "explanation": "元组（tuple）是Python中的不可变数据类型，一旦创建就不能修改。"
                    },
                    {
                        "question": "以下哪个是Python的缩进单位？",
                        "options": [
                            {"key": "A", "text": "2个空格"},
                            {"key": "B", "text": "4个空格"},
                            {"key": "C", "text": "Tab键或4个空格均可"},
                            {"key": "D", "text": "必须使用Tab键"}
                        ],
                        "answer": "C",
                        "explanation": "PEP 8推荐使用4个空格，但Tab键也可以，只要保持一致即可。"
                    },
                    {
                        "question": "执行print(type([]))会输出什么？",
                        "options": [
                            {"key": "A", "text": "<class 'list'>"},
                            {"key": "B", "text": "<class 'tuple'>"},
                            {"key": "C", "text": "<class 'dict'>"},
                            {"key": "D", "text": "<class 'array'>"}
                        ],
                        "answer": "A",
                        "explanation": "[]表示空列表，所以type([])返回<class 'list'>。"
                    },
                    {
                        "question": "Python中如何表示单行注释？",
                        "options": [
                            {"key": "A", "text": "使用<!-- -->"},
                            {"key": "B", "text": "使用#"},
                            {"key": "C", "text": "使用//"},
                            {"key": "D", "text": "使用/** */"}
                        ],
                        "answer": "B",
                        "explanation": "Python使用#符号表示单行注释。"
                    }
                ],
                "面向对象": [
                    {
                        "question": "Python中以下哪个关键字用于定义类？",
                        "options": [
                            {"key": "A", "text": "class"},
                            {"key": "B", "text": "def"},
                            {"key": "C", "text": "object"},
                            {"key": "D", "text": "struct"}
                        ],
                        "answer": "A",
                        "explanation": "Python使用class关键字来定义类。"
                    },
                    {
                        "question": "Python类的构造函数是以下哪个方法？",
                        "options": [
                            {"key": "A", "text": "__init__()"},
                            {"key": "B", "text": "__construct()"},
                            {"key": "C", "text": "constructor()"},
                            {"key": "D", "text": "new()"}
                        ],
                        "answer": "A",
                        "explanation": "Python使用__init__()作为类的构造函数。"
                    },
                    {
                        "question": "以下哪个是Python中私有属性的命名约定？",
                        "options": [
                            {"key": "A", "text": "private_attr"},
                            {"key": "B", "text": "_private_attr"},
                            {"key": "C", "text": "__private_attr__"},
                            {"key": "D", "text": "#private_attr"}
                        ],
                        "answer": "B",
                        "explanation": "Python中以单下划线_开头的属性表示受保护的，以双下划线__开头但不以双下划线结尾的表示私有属性。"
                    },
                    {
                        "question": "Python中如何实现继承？",
                        "options": [
                            {"key": "A", "text": "class Child(Parent):"},
                            {"key": "B", "text": "class Child extends Parent:"},
                            {"key": "C", "text": "class Child inherits Parent:"},
                            {"key": "D", "text": "class Child: Parent"}
                        ],
                        "answer": "A",
                        "explanation": "Python使用class Child(Parent):语法来实现继承。"
                    },
                    {
                        "question": "Python中的多态是如何实现的？",
                        "options": [
                            {"key": "A", "text": "通过方法重写"},
                            {"key": "B", "text": "通过接口实现"},
                            {"key": "C", "text": "通过抽象类"},
                            {"key": "D", "text": "通过类型注解"}
                        ],
                        "answer": "A",
                        "explanation": "Python通过方法重写（override）来实现多态，子类可以重写父类的方法。"
                    }
                ],
                "默认": [
                    {
                        "question": f"以下关于{topic}的说法正确的是？",
                        "options": [
                            {"key": "A", "text": f"{topic}是最常用的技术之一"},
                            {"key": "B", "text": f"{topic}已经完全被淘汰"},
                            {"key": "C", "text": f"{topic}只适用于特定场景"},
                            {"key": "D", "text": f"{topic}没有任何实际应用"}
                        ],
                        "answer": "A",
                        "explanation": f"{topic}是重要的技术基础，在实际应用中被广泛使用。"
                    },
                    {
                        "question": f"{topic}的核心概念是什么？",
                        "options": [
                            {"key": "A", "text": "基础理论知识"},
                            {"key": "B", "text": "实践应用技能"},
                            {"key": "C", "text": "理论加实践"},
                            {"key": "D", "text": "纯理论研究"}
                        ],
                        "answer": "C",
                        "explanation": f"学习{topic}需要理论与实践相结合。"
                    },
                    {
                        "question": f"以下哪项不是{topic}的特点？",
                        "options": [
                            {"key": "A", "text": "实用性"},
                            {"key": "B", "text": "系统性"},
                            {"key": "C", "text": "局限性"},
                            {"key": "D", "text": "发展性"}
                        ],
                        "answer": "C",
                        "explanation": f"{topic}具有实用性、系统性和发展性。"
                    },
                    {
                        "question": f"学习{topic}的最佳方式是什么？",
                        "options": [
                            {"key": "A", "text": "只看理论不动手"},
                            {"key": "B", "text": "多动手实践"},
                            {"key": "C", "text": "死记硬背"},
                            {"key": "D", "text": "只看别人的代码"}
                        ],
                        "answer": "B",
                        "explanation": f"学习{topic}需要多动手实践，理论结合实际。"
                    },
                    {
                        "question": f"{topic}在现代技术中的地位如何？",
                        "options": [
                            {"key": "A", "text": "已经过时"},
                            {"key": "B", "text": "非常重要"},
                            {"key": "C", "text": "可有可无"},
                            {"key": "D", "text": "无人关注"}
                        ],
                        "answer": "B",
                        "explanation": f"{topic}在现代技术中仍然占有重要地位。"
                    }
                ]
            },
            "网络安全": {
                "默认": [
                    {
                        "question": "以下哪个是SQL注入攻击的防御方法？",
                        "options": [
                            {"key": "A", "text": "使用参数化查询"},
                            {"key": "B", "text": "直接拼接SQL语句"},
                            {"key": "C", "text": "使用字符串拼接用户输入"},
                            {"key": "D", "text": "禁用数据库"}
                        ],
                        "answer": "A",
                        "explanation": "使用参数化查询可以有效防止SQL注入攻击。"
                    },
                    {
                        "question": "XSS攻击的中文名称是什么？",
                        "options": [
                            {"key": "A", "text": "跨站脚本攻击"},
                            {"key": "B", "text": "跨站请求伪造"},
                            {"key": "C", "text": "SQL注入攻击"},
                            {"key": "D", "text": "文件上传漏洞"}
                        ],
                        "answer": "A",
                        "explanation": "XSS是Cross-Site Scripting的缩写，中文名称是跨站脚本攻击。"
                    },
                    {
                        "question": "HTTPS相比HTTP增加了什么安全机制？",
                        "options": [
                            {"key": "A", "text": "SSL/TLS加密"},
                            {"key": "B", "text": "更快的传输速度"},
                            {"key": "C", "text": "更大的数据包"},
                            {"key": "D", "text": "更多的端口"}
                        ],
                        "answer": "A",
                        "explanation": "HTTPS通过SSL/TLS协议对通信进行加密，保护数据安全。"
                    }
                ]
            }
        }
        
        # 根据科目和主题选择题目模板
        subject_templates = question_templates.get(subject, None)
        if subject_templates:
            templates = subject_templates.get(topic, subject_templates.get("默认", []))
        else:
            # 科目不在模板中，尝试使用 LLM 生成
            self.log_info(f"科目 {subject} 不在模板中，尝试使用 LLM 生成")
            llm_result = await self._generate_questions_with_llm(subject, topic, difficulty, count, "选择题")
            if llm_result:
                return llm_result
            templates = []
        
        # 如果模板为空，尝试使用 LLM 生成
        if not templates:
            self.log_info(f"模板未找到 {subject}-{topic}，尝试使用 LLM 生成")
            llm_result = await self._generate_questions_with_llm(subject, topic, difficulty, count, "选择题")
            if llm_result:
                return llm_result
            templates = []
        
        # 生成指定数量的题目
        for i in range(min(count, len(templates))):
            q = templates[i].copy()
            q["id"] = i + 1
            q["type"] = "multiple_choice"
            q["question"] = f"[{subject}-{topic}] 第{i+1}题：" + templates[i]["question"]
            questions.append(q)
        
        return {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": "选择题",
            "count": len(questions),
            "questions": questions
        }
    
    async def _generate_short_answer(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        count: int
    ) -> Dict[str, Any]:
        """生成简答题"""
        if self._tools and "generate_short_answer" in self._tool_map:
            try:
                tool = self._tool_map["generate_short_answer"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "difficulty": difficulty,
                        "count": count
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to generate short answer: {e}")
        
        # 生成默认简答题
        questions = []
        templates = [
            f"请简述{topic}的基本概念和应用场景。",
            f"解释{topic}中核心术语的含义。",
            f"说明学习{topic}的重要性和方法。",
            f"分析{topic}的主要特点和优势。"
        ]
        
        for i in range(min(count, len(templates))):
            questions.append({
                "id": i + 1,
                "type": "short_answer",
                "question": f"[{topic}] 简答题{i+1}：" + templates[i],
                "answer_hint": "请从基本原理、实际应用等角度作答。"
            })
        
        return {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": "简答题",
            "count": len(questions),
            "questions": questions
        }
    
    async def _generate_questions_with_llm(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str
    ) -> Dict[str, Any]:
        """使用讯飞大模型生成练习题"""
        if not self._llm_client:
            logger.warning("[QuestionAgent] No LLM client available")
            return None
        
        # 构建 prompt
        prompt = f"""你是一位大数据教育专家。请为以下主题生成练习题。

主题：{subject} - {topic}
难度：{difficulty}
题目类型：{question_type}
数量：{count}道

要求：
1. 题目要有专业性，体现{subject}的核心知识点
2. 答案要准确，不能有歧义
3. 返回JSON格式，包含questions数组，每个题目包含question、options（A-D）和answer字段
4. 如果是简答题或编程题，只包含question和answer_hint字段
5. 只返回JSON，不要有其他解释说明

JSON格式示例：
{{
    "questions": [
        {{
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A"
        }}
    ]
}}"""

        try:
            messages = [{"role": "user", "content": prompt}]
            # 使用 run_in_executor 避免阻塞
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._llm_client.chat(messages)
            )
            
            if result:
                # 尝试解析 JSON
                import re
                # 提取 JSON 部分
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)
                    raw_questions = data.get("questions", [])
                    
                    # 转换格式以匹配期望的输出格式
                    questions = []
                    for q in raw_questions:
                        formatted_q = {
                            "question": q.get("question", ""),
                            "answer": q.get("answer", ""),
                            "explanation": q.get("explanation", ""),
                            "type": "multiple_choice"
                        }
                        
                        # 处理 options 格式
                        options = q.get("options", [])
                        if options:
                            if isinstance(options[0], str):
                                # 字符串格式 ["A. 选项1", "B. 选项2", ...]
                                formatted_q["options"] = []
                                for opt in options:
                                    if ". " in opt:
                                        key, text = opt.split(". ", 1)
                                        formatted_q["options"].append({"key": key.strip(), "text": text.strip()})
                                    elif opt and len(opt) > 0:
                                        formatted_q["options"].append({"key": opt[0], "text": opt[1:].strip() if len(opt) > 1 else opt})
                            else:
                                # 已经是对象格式
                                formatted_q["options"] = options
                        
                        questions.append(formatted_q)
                    
                    return {
                        "subject": subject,
                        "topic": topic,
                        "difficulty": difficulty,
                        "question_type": question_type,
                        "count": len(questions),
                        "questions": questions,
                        "generated_by": "llm"
                    }
                    
        except Exception as e:
            logger.error(f"[QuestionAgent] LLM generation failed: {e}")
        
        return None
    
    async def _generate_coding(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        count: int
    ) -> Dict[str, Any]:
        """生成编程题"""
        if self._tools and "generate_coding" in self._tool_map:
            try:
                tool = self._tool_map["generate_coding"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "difficulty": difficulty,
                        "count": count
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to generate coding: {e}")
        
        # 生成默认编程题
        questions = [
            {
                "id": 1,
                "type": "coding",
                "question": f"[{topic}] 编程题1：实现一个简单的{topic}示例",
                "requirements": ["使用基础语法", "包含注释", "输出正确结果"],
                "sample_code": f"# 请实现一个{topic}相关的代码示例\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()"
            }
        ]
        
        return {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": "编程题",
            "count": len(questions),
            "questions": questions
        }
    
    async def _save_questions(
        self,
        user_id: str,
        subject: str,
        topic: str,
        difficulty: str,
        mc_result: Dict[str, Any],
        sa_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """保存题目到题库"""
        if self._tools and "save_question" in self._tool_map:
            try:
                tool = self._tool_map["save_question"]
                
                # 保存选择题
                for q in mc_result.get("questions", []):
                    await asyncio.to_thread(
                        tool.invoke,
                        {
                            "subject": subject,
                            "topic": topic,
                            "difficulty": difficulty,
                            "question_type": "选择题",
                            "question_data": json.dumps(q),
                            "answer_data": json.dumps({"answer": q.get("answer"), "explanation": q.get("explanation")})
                        }
                    )
                
                return {"success": True, "saved_count": len(mc_result.get("questions", []))}
            except Exception as e:
                self.log_error(f"Failed to save questions: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": True, "simulated": True}
    
    def _format_response(
        self,
        subject: str,
        topic: str,
        mc_result: Dict[str, Any],
        sa_result: Dict[str, Any]
    ) -> str:
        """格式化响应内容 - 适度引导风格"""
        mc_count = mc_result.get("count", 0)
        sa_count = sa_result.get("count", 0)
        
        response = f"""✍️ **基础** 练习题已生成！来检验一下学习成果 📝

**科目：** {subject}
**题型：** 选择题 {mc_count}道 + 简答题 {sa_count}道

"""
        
        # 添加部分题目预览
        for i, q in enumerate(mc_result.get("questions", [])[:3]):
            response += f"""**第{i+1}题：** {q.get('question', '')}
- A. {q['options'][0]['text'] if q.get('options') else ''}
- B. {q['options'][1]['text'] if q.get('options') else ''}
- C. {q['options'][2]['text'] if q.get('options') else ''}
- D. {q['options'][3]['text'] if q.get('options') else ''}

"""
        
        response += """---
做完后可以告诉我答案，我来帮你评分！遇到不懂的随时问 😊"""
        
        return response


# 全局实例
_question_agent: Optional[QuestionAgent] = None


def get_question_agent() -> QuestionAgent:
    """获取全局QuestionAgent实例"""
    global _question_agent
    if _question_agent is None:
        _question_agent = QuestionAgent()
    return _question_agent
