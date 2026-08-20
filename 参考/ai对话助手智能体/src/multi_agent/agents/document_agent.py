"""
Document Agent - 文档与思维导图Agent
功能：生成知识文档、大纲、思维导图
处理模式：联邦式（独立处理）
"""
import json
import logging
import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class DocumentAgent(BaseAgent):
    """
    文档生成Agent
    
    核心职责：
    1. 生成知识文档大纲
    2. 生成思维导图结构
    3. 保存和管理学习内容
    4. 提供知识梳理服务
    """
    
    def __init__(self):
        super().__init__(
            agent_id="document",
            name="文档生成Agent",
            description="负责生成知识文档、大纲和思维导图",
            processing_mode=ProcessingMode.FEDERATED
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具（将在初始化时绑定）
        self._tools = None
        
        # LLM 客户端（用于生成真实内容）
        self._llm_client = None
        self._init_llm_client()
        
        logger.info("[DocumentAgent] Initialized")
    
    def _init_llm_client(self):
        """初始化 LLM 客户端 - 使用讯飞大模型"""
        try:
            import json
            
            # 读取讯飞配置
            workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
            config_path = os.path.join(workspace_path, "config/agent_llm_config.json")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 使用 LLMFactory 创建讯飞适配器
            from integrations.llm_factory import LLMFactory
            
            llm_config = {
                "api_key": config.get("api_key") or config.get("config", {}).get("api_key"),
                "api_secret": config.get("api_secret") or config.get("config", {}).get("api_secret"),
                "app_id": config.get("app_id") or config.get("config", {}).get("app_id"),
                "version": config.get("version") or config.get("config", {}).get("version", "x2"),
                "temperature": config.get("temperature") or config.get("config", {}).get("temperature", 0.7),
                "max_tokens": config.get("max_tokens") or config.get("config", {}).get("max_tokens", 4096),
            }
            
            self._llm_client = LLMFactory.create("xunfei", llm_config)
            logger.info("[DocumentAgent] LLM client (Xunfei) initialized")
        except Exception as e:
            logger.error(f"[DocumentAgent] Failed to init LLM client: {e}")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.DOCUMENT
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[DocumentAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理文档生成请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing document request: {user_input[:50]}...")
        
        # 解析用户请求
        subject, topic = self._parse_topic(user_input)
        
        results = {}
        
        # 1. 生成文档大纲
        outline_result = await self._generate_outline(subject, topic)
        results["outline"] = outline_result
        
        # 2. 生成思维导图结构
        mindmap_result = await self._generate_mindmap(subject, topic)
        results["mindmap"] = mindmap_result
        
        # 3. 保存学习内容
        save_result = await self._save_content(
            user_id,
            subject,
            topic,
            outline_result,
            mindmap_result
        )
        results["saved"] = save_result
        
        # 4. 生成友好响应
        response = self._format_response(subject, topic, outline_result, mindmap_result)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "subject": subject,
            "topic": topic,
            "outline": outline_result,
            "mindmap": mindmap_result,
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
    
    def _parse_topic(self, user_input: str) -> tuple:
        """解析用户输入，提取科目和主题"""
        # 默认值
        subject = "通用"
        topic = user_input
        
        # 优先从 RAG 知识点配置中获取科目（大小写不敏感）
        try:
            from config.bigdata_knowledge import SUBJECTS, KNOWLEDGE_KEYWORDS, SUBJECT_ALIASES
            user_input_lower = user_input.lower()
            
            # 1. 先精确匹配知识点关键词
            for keyword, subj in KNOWLEDGE_KEYWORDS.items():
                if keyword.lower() in user_input_lower:
                    subject = subj
                    break
            
            # 2. 再匹配科目名称
            if subject == "通用":
                for s in SUBJECTS:
                    if s.lower() in user_input_lower:
                        subject = s
                        break
            
            # 3. 最后匹配科目别名
            if subject == "通用":
                for subj, aliases in SUBJECT_ALIASES.items():
                    for alias in aliases:
                        if alias.lower() in user_input_lower:
                            subject = subj
                            break
                    else:
                        continue
                    break
        except ImportError:
            # 兜底：使用内置列表
            pass
        
        # 清理主题中的请求描述，保留核心内容
        topic = topic.strip()
        # 移除常见请求词（注意顺序，先长后短）
        for keyword in ["为我整理一份", "请帮我整理", "帮我整理", "为我整理", "制定", "生成", "学习", "整理一份", "整理", "文档", "大纲", "计划"]:
            topic = topic.replace(keyword, "")
        # 清理标点和邮箱
        topic = topic.replace("，", ",").replace("、", ",")
        topic = topic.replace("发送到我的邮箱", "").replace("@qq.com", "")
        topic = topic.strip(", ")
        
        if not topic:
            topic = subject
        
        return subject, topic
    
    async def _generate_outline(self, subject: str, topic: str) -> Dict[str, Any]:
        """生成文档大纲"""
        # 优先使用 LLM 生成真实内容（推荐）
        if self._llm_client:
            outline_result = await self._generate_outline_with_llm(subject, topic)
            if outline_result:
                return outline_result
        
        # 如果 LLM 不可用，尝试使用工具（可能返回模板）
        if self._tools and "generate_document_outline" in self._tool_map:
            try:
                tool = self._tool_map["generate_document_outline"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"subject": subject, "topic": topic, "depth": 3}
                )
                outline_data = json.loads(result) if isinstance(result, str) else result
                return outline_data
            except Exception as e:
                self.log_error(f"Failed to generate outline: {e}")
        
        # 最后兜底：使用模板
        return self._create_default_outline(subject, topic)
    
    async def _generate_outline_with_llm(self, subject: str, topic: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成真实的文档大纲 - 使用讯飞大模型"""
        if not self._llm_client:
            self.logger.warning("_llm_client is None, cannot generate outline with LLM")
            return None
        
        try:
            # 简化 prompt，加快生成速度
            prompt = f"""请为{subject}的{topic}生成一个markdown大纲，包含4-6个章节，每个章节2-3个子节点。只输出大纲内容。"""
            
            # 使用讯飞适配器（同步方法，在线程池中执行）
            messages = [{"role": "user", "content": prompt}]
            
            # 在线程池中执行同步的 chat 方法
            loop = asyncio.get_event_loop()
            outline_content = await loop.run_in_executor(
                None,  # 使用默认线程池
                lambda: self._llm_client.chat(messages)
            )
            
            if not outline_content or len(outline_content.strip()) < 50:
                self.logger.warning(f"LLM returned empty or too short content: {outline_content}")
                return None
            
            return {
                "subject": subject,
                "topic": topic,
                "depth": 3,
                "outline": outline_content,
                "generated_by": "llm",
                "message": f"已为「{topic}」生成文档大纲"
            }
        except Exception as e:
            self.log_error(f"LLM outline generation failed: {e}")
            return None
    
    def _create_default_outline(self, subject: str, topic: str) -> Dict[str, Any]:
        """创建默认文档大纲"""
        outline = f"""# {topic} - 知识文档大纲

## 一、基础概念
### 1.1 定义与背景
### 1.2 核心术语解释
### 1.3 基本原理

## 二、核心知识点
### 2.1 重点内容1
### 2.2 重点内容2
### 2.3 重点内容3

## 三、实践应用
### 3.1 应用场景1
### 3.2 应用场景2
### 3.3 案例分析

## 四、进阶拓展
### 4.1 相关知识点
### 4.2 延伸阅读
### 4.3 发展趋势

## 五、总结与练习
### 5.1 核心要点回顾
### 5.2 自测题
### 5.3 实践作业
"""
        return {
            "subject": subject,
            "topic": topic,
            "depth": 3,
            "outline": outline,
            "message": f"已为{topic}生成文档大纲"
        }
    
    async def _generate_mindmap(self, subject: str, topic: str) -> Dict[str, Any]:
        """生成思维导图结构"""
        # 检查是否有工具支持
        if self._tools and "generate_mindmap_structure" in self._tool_map:
            try:
                tool = self._tool_map["generate_mindmap_structure"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"subject": subject, "topic": topic, "complexity": "medium"}
                )
                mindmap_data = json.loads(result) if isinstance(result, str) else result
                return mindmap_data
            except Exception as e:
                self.log_error(f"Failed to generate mindmap: {e}")
        
        # 使用 LLM 生成真实思维导图（推荐）
        mindmap_result = await self._generate_mindmap_with_llm(subject, topic)
        if mindmap_result:
            return mindmap_result
        
        # 最后兜底：使用模板
        return self._create_default_mindmap(subject, topic)
    
    async def _generate_mindmap_with_llm(self, subject: str, topic: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成真实的思维导图结构 - 使用讯飞大模型"""
        if not self._llm_client:
            self.logger.warning("_llm_client is None, cannot generate mindmap with LLM")
            return None
        
        try:
            prompt = f"""你是一位专业的大数据教育专家。请为以下主题生成一个思维导图结构。

主题：{topic}
科目：{subject}

要求：
1. 输出 JSON 格式的思维导图结构
2. 包含4-5个主要分支，每个分支有3-5个子节点
3. 内容要专业、具体，体现{topic}的核心知识点
4. 遵循此格式：
{{"name": "主题", "children": [{{"name": "分支1", "children": [{{"name": "子节点"}}]}}]}}

请只输出JSON，不要有任何解释。"""
            
            # 使用讯飞适配器（同步方法，在线程池中执行）
            messages = [{"role": "user", "content": prompt}]
            
            # 在线程池中执行同步的 chat 方法
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: self._llm_client.chat(messages)
            )
            
            if not content or len(content.strip()) < 50:
                self.logger.warning(f"LLM returned empty or too short content: {content}")
                return None
            
            # 尝试提取 JSON
            try:
                # 尝试直接解析
                mindmap_data = json.loads(content)
            except json.JSONDecodeError:
                # 尝试从 markdown 代码块中提取
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                if json_match:
                    mindmap_data = json.loads(json_match.group(1))
                else:
                    return None
            
            return {
                "subject": subject,
                "topic": topic,
                "complexity": "medium",
                "mindmap": mindmap_data,
                "generated_by": "llm",
                "message": f"已为「{topic}」生成思维导图"
            }
        except Exception as e:
            self.log_error(f"LLM mindmap generation failed: {e}")
            return None
    
    def _create_default_mindmap(self, subject: str, topic: str) -> Dict[str, Any]:
        """创建默认思维导图"""
        mindmap = {
            "name": topic,
            "children": [
                {
                    "name": "基础概念",
                    "children": [
                        {"name": "定义"},
                        {"name": "原理"},
                        {"name": "术语"}
                    ]
                },
                {
                    "name": "核心知识",
                    "children": [
                        {"name": "重点1"},
                        {"name": "重点2"},
                        {"name": "重点3"}
                    ]
                },
                {
                    "name": "实践应用",
                    "children": [
                        {"name": "场景1"},
                        {"name": "场景2"},
                        {"name": "案例"}
                    ]
                },
                {
                    "name": "进阶拓展",
                    "children": [
                        {"name": "相关知识"},
                        {"name": "延伸阅读"},
                        {"name": "发展趋势"}
                    ]
                }
            ]
        }
        
        return {
            "subject": subject,
            "topic": topic,
            "complexity": "medium",
            "mindmap": mindmap,
            "message": f"已为{topic}生成思维导图"
        }
    
    async def _save_content(
        self,
        user_id: str,
        subject: str,
        topic: str,
        outline: Dict[str, Any],
        mindmap: Dict[str, Any]
    ) -> Dict[str, Any]:
        """保存学习内容"""
        if self._tools and "save_learning_content" in self._tool_map:
            try:
                content_data = {
                    "outline": outline.get("outline", ""),
                    "mindmap": mindmap.get("mindmap", {})
                }
                
                tool = self._tool_map["save_learning_content"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "content_type": "document",
                        "content_data": json.dumps(content_data)
                    }
                )
                
                save_result = json.loads(result) if isinstance(result, str) else result
                self.log_info(f"Content saved: {save_result.get('content_id')}")
                return save_result
            except Exception as e:
                self.log_error(f"Failed to save content: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": True, "simulated": True}
    
    async def _get_content(
        self,
        subject: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取学习内容"""
        if self._tools and "get_learning_content" in self._tool_map:
            try:
                tool = self._tool_map["get_learning_content"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {"subject": subject, "topic": topic, "content_type": "document"}
                )
                return json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                self.log_error(f"Failed to get content: {e}")
                return {"error": str(e)}
        
        return {"contents": [], "count": 0}
    
    def _format_response(
        self,
        subject: str,
        topic: str,
        outline: Dict[str, Any],
        mindmap: Dict[str, Any]
    ) -> str:
        """格式化响应内容 - 返回 LLM 生成的内容"""
        # 如果 LLM 生成了真实内容，直接返回
        if outline.get("generated_by") == "llm" and outline.get("outline"):
            return outline.get("outline", "")
        
        # 如果有工具生成的内容
        if outline.get('outline'):
            return outline.get('outline', '')
        
        # 兜底：返回默认模板
        # 兜底：返回默认模板
        default_outline = (
            "# " + topic + "\n\n"
            "## 一、基础概念\n"
            "### 1.1 定义\n\n"
            "## 二、核心知识点\n"
            "### 2.1 重点内容"
        )
        return default_outline


# 全局实例
_document_agent: Optional[DocumentAgent] = None


def get_document_agent() -> DocumentAgent:
    """获取全局DocumentAgent实例"""
    global _document_agent
    if _document_agent is None:
        _document_agent = DocumentAgent()
    return _document_agent
