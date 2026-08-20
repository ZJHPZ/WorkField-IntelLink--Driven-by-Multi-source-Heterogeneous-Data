"""
QA Agent - 答疑解惑Agent
功能：解答学习问题、提供深入讲解、知识检索
处理模式：联邦式（独立处理）
"""
import json
import logging
import asyncio
import re
from typing import Any, Dict, List, Optional

from integrations.llm_factory import LLMFactory
from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context
from ..system_prompts import UNIFIED_LEARNING_PARTNER_PROMPT

logger = logging.getLogger(__name__)

# 默认 LLM 配置（从配置文件读取）
def _load_llm_config():
    """从配置文件加载 LLM 配置"""
    import json
    import os
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, "config/agent_llm_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {
            "provider": config['config'].get('provider', 'xunfei'),
            "model": config['config'].get('model', 'SPARKX2'),
            "version": config['config'].get('version', 'x2'),
            "app_id": config['config'].get('app_id'),
            "api_key": config['config'].get('api_key'),
            "api_secret": config['config'].get('api_secret')
        }
    except Exception:
        return {
            "provider": "xunfei",
            "model": "SPARKX2",
            "version": "x2"
        }

DEFAULT_LLM_CONFIG = _load_llm_config()


class QAAgent(BaseAgent):
    """
    答疑Agent
    
    核心职责：
    1. 解答学习中的各种疑问
    2. 深入讲解复杂概念
    3. 提供相关知识关联
    4. 推荐学习资源
    """
    
    def __init__(self):
        super().__init__(
            agent_id="qa",
            name="答疑解惑Agent",
            description="负责解答学习问题和深入讲解",
            processing_mode=ProcessingMode.FEDERATED
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具
        self._tools = None
        
        # LLM 客户端 (按需初始化)
        self._llm = None
        
        logger.info("[QAAgent] Initialized")
    
    def _get_llm(self):
        """获取 LLM 客户端（延迟初始化）"""
        if self._llm is None:
            try:
                provider = DEFAULT_LLM_CONFIG.get("provider", "xunfei")
                
                if provider == "xunfei":
                    # 讯飞大模型配置
                    self._llm = LLMFactory.create(
                        provider="xunfei",
                        model_config={
                            "model": DEFAULT_LLM_CONFIG.get("model", "SPARKX2"),
                            "version": DEFAULT_LLM_CONFIG.get("version", "x2"),
                            "app_id": DEFAULT_LLM_CONFIG.get("app_id"),
                            "api_key": DEFAULT_LLM_CONFIG.get("api_key"),
                            "api_secret": DEFAULT_LLM_CONFIG.get("api_secret"),
                            "temperature": 0.7,
                            "max_tokens": 2000
                        }
                    )
                else:
                    # 其他提供商（doubao等）
                    self._llm = LLMFactory.create(
                        provider=provider,
                        model_config={
                            "model": DEFAULT_LLM_CONFIG.get("model"),
                            "use_ark": False,
                            "temperature": 0.7,
                            "max_tokens": 2000
                        }
                    )
                logger.info(f"[QAAgent] LLM initialized: {DEFAULT_LLM_CONFIG['model']} (Coze内部大模型)")
            except Exception as e:
                logger.error(f"[QAAgent] Failed to initialize LLM: {e}")
        return self._llm
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.QA
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self.tools = tools  # ✅ 同时更新 tools 属性
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[QAAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理答疑请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing QA request: {user_input[:50]}...")
        
        # 解析问题
        question = self._parse_question(user_input)
        
        # 1. 搜索相关知识
        related_content = await self._search_related_content(question)
        
        # 2. 生成详细解答
        answer = await self._generate_answer(question, related_content)
        
        # 3. 生成相关推荐
        recommendations = await self._generate_recommendations(question)
        
        # 4. 保存问答记录
        save_result = await self._save_qa_record(user_id, question, answer)
        
        # 5. 生成友好响应
        response = self._format_response(question, answer, recommendations)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "question": question,
            "answer": answer,
            "related_content": related_content,
            "recommendations": recommendations,
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
    
    def _parse_question(self, user_input: str) -> Dict[str, Any]:
        """解析问题 - 正确提取知识点"""
        # 提取问题核心
        question_text = user_input.strip()
        original = question_text
        
        # 识别科目 (优先匹配，放在前缀移除之后)
        subject = "通用"
        
        # 先移除前缀 (注意：使用 r'' 前缀使 \s 正确工作)
        prefixes_patterns = [
            (r'^介绍一下\s*', ''),
            (r'^介绍\s*', ''),
            (r'^为我介绍\s*', ''),  # 这个要放在 ^介绍 之前！
            (r'^帮我介绍\s*', ''),  # 这个要放在 ^介绍 之前！
            (r'^什么是\s*', ''),
            (r'^请问\s*', ''),
            (r'^我想问\s*', ''),
            (r'^为什么\s*', ''),
            (r'^如何\s*', ''),
            (r'^怎么\s*', ''),
            (r'^为我\s*', ''),
            (r'^帮我\s*', ''),
            (r'^给我讲讲\s*', ''),
            (r'^讲解\s*', ''),
        ]
        
        topic = question_text
        for pattern, replacement in prefixes_patterns:
            new_topic = re.sub(pattern, replacement, topic).strip()
            if new_topic != topic:  # 只有真正被匹配替换了才更新
                topic = new_topic
                break
        
        # 如果 topic 变成空的，使用原始输入
        if not topic or len(topic) < 2:
            topic = question_text
        
        # 识别科目 - 使用 RAG 知识点配置（大小写不敏感）
        subjects_map = {}
        try:
            from config.bigdata_knowledge import SUBJECTS, SUBJECT_KEYWORDS
            
            # 添加科目本身
            for subj in SUBJECTS:
                subjects_map[subj] = subj
            
            # 添加科目关键词
            for keyword, subj in SUBJECT_KEYWORDS.items():
                if keyword not in subjects_map:
                    subjects_map[keyword] = subj
                    
        except ImportError:
            # 兜底：使用内置列表
            subjects_map = {
                "Hadoop": "Hadoop大数据",
                "Spark": "Spark大数据",
                "Kafka": "Kafka消息队列",
                "Flink": "Flink流计算",
                "Hive": "Hive数据仓库",
                "Python": "Python编程",
                "Java": "Java编程",
            }
        
        matched_subject = None
        matched_key = None
        for key, value in subjects_map.items():
            if key.lower() in topic.lower():
                matched_subject = value
                matched_key = key
                break
        
        # 如果识别到科目，更新 subject，并清理 topic
        if matched_subject:
            subject = matched_subject
            # 清理 topic 中的科目名（避免重复）
            topic = topic.replace(matched_key, '').replace(matched_key.lower(), '').strip()
            if not topic:
                topic = matched_key
        
        return {
            "original": original,
            "text": topic,  # 知识点
            "subject": subject,
            "type": self._classify_question_type(user_input)
        }
    
    def _classify_question_type(self, question: str) -> str:
        """分类问题类型"""
        if question.startswith("什么是") or question.startswith("解释"):
            return "definition"
        elif question.startswith("为什么"):
            return "reason"
        elif question.startswith("如何") or question.startswith("怎么"):
            return "method"
        elif "区别" in question or "不同" in question:
            return "comparison"
        elif "哪个好" in question or "选择" in question:
            return "choice"
        else:
            return "general"
    
    async def _search_related_content(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """搜索相关内容"""
        if self._tools and "search_related_content" in self._tool_map:
            try:
                tool = self._tool_map["search_related_content"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": question.get("subject", "通用"),
                        "topic": question.get("text", ""),
                        "limit": 3
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to search content: {e}")
        
        # 返回默认内容
        return {
            "results": [],
            "count": 0,
            "message": "未找到相关内容"
        }
    
    async def _generate_answer(
        self,
        question: Dict[str, Any],
        related_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成答案 - 使用 LLM"""
        topic = question.get("text", question.get("original", ""))
        subject = question.get("subject", "通用")
        q_type = question.get("type", "general")
        
        # 尝试使用 LLM 生成答案
        llm = self._get_llm()
        if llm:
            try:
                # 构建提示词 - 使用统一的对话风格
                context = ""
                if related_content and related_content.get("results"):
                    context = "\n\n## 知识库相关内容：\n"
                    for item in related_content.get("results", [])[:3]:
                        context += f"- {item.get('content', str(item))}\n"
                
                # 构建对话式提示（直接回答，不加问候语）
                prompt = f"""使用"亦师亦友的大数据学习伙伴"风格回答以下问题：

问题：{question.get('original', topic)}

要求：
1. 直接回答问题，不要输出问候语或引导语
2. 给出准确的定义和核心概念
3. 解释核心原理和工作机制
4. 提供实际应用场景和案例
5. 如果是技术概念，给出代码示例
6. 用 Markdown 格式回答，结构清晰
7. 内容充实、有深度
{context}

请直接回答："""
                
                # 调用 LLM (使用 chat 方法)
                response = await asyncio.to_thread(
                    llm.chat,
                    [{"role": "user", "content": prompt}]
                )
                
                answer_text = response if isinstance(response, str) else str(response)
                
                return {
                    "question": question.get("original", ""),
                    "answer": answer_text,
                    "topic": topic,
                    "subject": subject,
                    "type": q_type,
                    "source": "llm"
                }
            except Exception as e:
                self.log_error(f"LLM generation failed: {e}")
        
        # 如果 LLM 失败，回退到模板答案
        return self._generate_default_answer(question)
    
    def _generate_default_answer(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """生成默认答案"""
        topic = question.get("text", "这个问题")
        q_type = question.get("type", "general")
        
        # 根据问题类型生成不同风格的答案
        if q_type == "definition":
            answer = f"""**{topic}** 是一个重要的概念。

### 基本定义
{topic}是指...（请提供更多背景信息以便给出准确解释）

### 核心要点
1. 理解基本概念
2. 掌握核心原理
3. 了解应用场景

### 示例说明
```python
# {topic}示例
def example():
    # 这里是{topic}的典型用法
    pass
```
"""
        elif q_type == "reason":
            answer = f"""关于**为什么**会出现{topic}这个问题，让我来解释：

### 原因分析
1. **根本原因**：{topic}产生的主要原因是...
2. **直接原因**：导致这个问题具体表现是...
3. **深层原因**：从更广的角度看...

### 解决思路
- 理解原理
- 实践验证
- 总结经验
"""
        elif q_type == "method":
            answer = f"""要解决/学习**{topic}**，可以按照以下步骤：

### 方法步骤
1. **理解概念**：先弄清楚什么是{topic}
2. **学习原理**：掌握{topic}的核心原理
3. **实践操作**：动手练习{topic}的用法
4. **总结经验**：归纳{topic}的使用技巧

### 注意事项
- 注意细节
- 多做练习
- 及时总结
"""
        else:
            answer = f"""关于**{topic}**，我来为你详细解答：

### 概念解释
{topic}是{question.get('subject', '学习')}中的重要内容。

### 核心要点
1. 基本概念和定义
2. 核心原理和机制
3. 实际应用场景

### 学习建议
- 多看相关资料
- 多做练习实践
- 及时总结归纳

如果还有疑问，欢迎继续提问！
"""
        
        return {
            "question": question.get("original"),
            "answer": answer,
            "explanation": f"关于{topic}的详细解答",
            "examples": [
                {
                    "type": "代码",
                    "code": f"# {topic}示例\n# 请参考上方说明"
                }
            ]
        }
    
    async def _generate_recommendations(self, question: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成相关推荐"""
        topic = question.get("text", "")
        subject = question.get("subject", "通用")
        
        recommendations = [
            {
                "type": "知识点",
                "title": f"{topic}相关知识点",
                "description": f"学习{topic}的前置知识"
            },
            {
                "type": "练习",
                "title": f"{topic}练习题",
                "description": f"检验对{topic}的理解"
            },
            {
                "type": "文档",
                "title": f"{topic}详细文档",
                "description": f"深入学习{topic}"
            }
        ]
        
        return recommendations
    
    async def _save_qa_record(
        self,
        user_id: str,
        question: Dict[str, Any],
        answer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """保存问答记录"""
        if self._tools and "save_qa_record" in self._tool_map:
            try:
                tool = self._tool_map["save_qa_record"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "user_id": user_id,  # 添加 user_id
                        "subject": question.get("subject", "通用"),
                        "question": question.get("original", ""),
                        "answer": answer.get("answer", ""),
                        "helpful": True
                    }
                )
                save_result = json.loads(result) if isinstance(result, str) else result
                return save_result
            except Exception as e:
                self.log_error(f"Failed to save QA record: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": True, "simulated": True}
    
    def _format_response(
        self,
        question: Dict[str, Any],
        answer: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """格式化响应内容 - 使用统一对话风格（直接回答，禁止引导语）"""
        response = f"""{answer.get('answer', '抱歉，暂时无法回答这个问题。')}
"""
        
        if recommendations:
            response += """**📚 相关推荐**

"""
            for rec in recommendations[:3]:
                response += f"- **{rec['title']}**：{rec['description']}\n"
        
        return response


# 全局实例
_qa_agent: Optional[QAAgent] = None


def get_qa_agent() -> QAAgent:
    """获取全局QAAgent实例"""
    global _qa_agent
    if _qa_agent is None:
        _qa_agent = QAAgent()
    return _qa_agent
