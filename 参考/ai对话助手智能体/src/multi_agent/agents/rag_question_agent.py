# -*- coding: utf-8 -*-
"""
RAG题库Agent - 基于知识库的题库检索和练习
"""
import json
import logging
from typing import Dict, Any, List

from multi_agent.base.base_agent import BaseAgent
from multi_agent.base.agent_state import IntentType, MultiAgentState
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.log.write_log import request_context

logger = logging.getLogger(__name__)


class RagQuestionAgent(BaseAgent):
    """RAG题库Agent - 基于知识库的题库检索"""

    def __init__(self, agent_id: str = "rag_question", agent_name: str = "RAG题库Agent"):
        super().__init__(agent_id, agent_name)
        self.description = "基于知识库的题库检索和练习"
        self._tools = None
        self._tool_map = {}
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.RAG_QUESTION
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[RagQuestionAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理RAG题库请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing RAG question: {user_input[:50]}...")
        
        return await self._execute_impl(state)

    def _build_system_prompt(self) -> str:
        """构建RAG题库Agent的系统提示词"""
        return """# 角色：RAG题库助手

你是一个基于知识库的题库助手，负责：
1. 从题库中检索相关题目
2. 根据知识点查找相似题目
3. 生成练习集
4. 提供答案解析

## 可用的工具

- `search_questions`: 根据关键词搜索题库
- `get_similar_questions`: 根据知识点查找相似题目
- `generate_practice_set`: 生成练习集
- `get_answer_explanation`: 获取答案解析

## 使用场景

1. **搜索题目**：用户说"找关于Spark的题目"
2. **相似题目**：用户说"来几道RDD的练习题"
3. **生成练习**：用户说"给我生成一套Hadoop练习题"
4. **查看解析**：用户说"看看这道题的答案"

## 关键词识别

- "练习"、"做题"、"测验"、"题目" → 调用题库工具
- "关于XX的题"、"XX练习题" → search_questions
- "类似"、"相似"、"再来几道" → get_similar_questions
- "生成一套"、"出题" → generate_practice_set
- "答案"、"解析" → get_answer_explanation

## 输出格式

返回格式化的题目列表，包含：
- 题目标题
- 选项（如有）
- 正确答案标记
- 难度等级

## 注意事项

- 必须使用题库检索工具，禁止自己生成题目
- 如果题库中没有相关题目，诚实地告知用户
- 结合用户的学习进度，推荐合适难度的题目
"""

    def _get_tool_names(self) -> List[str]:
        """获取该Agent使用的工具名称"""
        return [
            "search_questions",
            "get_similar_questions",
            "generate_practice_set",
            "get_answer_explanation"
        ]

    async def _execute_impl(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行RAG题库检索"""
        ctx = request_context.get() or new_context(method="rag_question.agent")

        # 获取用户输入
        user_input = self._get_user_input(state)

        # 分析用户意图
        input_lower = user_input.lower()

        # 判断意图类型
        if any(kw in input_lower for kw in ["答案", "解析", "解释"]):
            # 获取答案解析
            return await self._handle_explanation(user_input, state)
        elif any(kw in input_lower for kw in ["生成", "出", "一套", "创建"]):
            # 生成练习集
            return await self._handle_generate_practice(user_input, state)
        elif any(kw in input_lower for kw in ["类似", "相似", "再来", "更多"]):
            # 获取相似题目
            return await self._handle_similar_questions(user_input, state)
        else:
            # 默认：搜索相关题目
            return await self._handle_search_questions(user_input, state)

    async def _handle_search_questions(self, user_input: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理题目搜索"""
        ctx = request_context.get() or new_context(method="rag_question.search")

        tool = self._tool_map.get("search_questions")
        if not tool:
            return {
                "success": False,
                "error": "search_questions工具不可用"
            }

        try:
            # 提取搜索关键词
            keywords = self._extract_keywords(user_input)
            if not keywords:
                keywords = user_input

            result = tool.invoke({
                "query": keywords,
                "top_k": 5
            })

            result_data = json.loads(result)
            return {
                "success": True,
                "questions": result_data.get("questions", []),
                "count": len(result_data.get("questions", [])),
                "message": f"找到 {len(result_data.get('questions', []))} 道相关题目"
            }
        except Exception as e:
            logger.error(f"[RagQuestionAgent] Search error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_similar_questions(self, user_input: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理相似题目查询"""
        ctx = request_context.get() or new_context(method="rag_question.similar")

        tool = self._tool_map.get("get_similar_questions")
        if not tool:
            return {
                "success": False,
                "error": "get_similar_questions工具不可用"
            }

        try:
            # 提取主题
            topic = self._extract_topic(user_input)
            if not topic:
                topic = user_input

            # 提取难度（如果有）
            difficulty = self._extract_difficulty(user_input)

            result = tool.invoke({
                "topic": topic,
                "difficulty": difficulty,
                "count": 5
            })

            result_data = json.loads(result)
            return {
                "success": True,
                "questions": result_data.get("questions", []),
                "count": len(result_data.get("questions", [])),
                "message": f"找到 {len(result_data.get('questions', []))} 道相似题目"
            }
        except Exception as e:
            logger.error(f"[RagQuestionAgent] Similar questions error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_generate_practice(self, user_input: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理练习集生成"""
        ctx = request_context.get() or new_context(method="rag_question.generate")

        tool = self._tool_map.get("generate_practice_set")
        if not tool:
            return {
                "success": False,
                "error": "generate_practice_set工具不可用"
            }

        try:
            # 提取主题
            topic = self._extract_topic(user_input)
            if not topic:
                topic = "大数据基础"

            # 提取难度
            difficulty = self._extract_difficulty(user_input) or "中等"

            # 提取数量
            count = self._extract_count(user_input) or 5

            result = tool.invoke({
                "topic": topic,
                "difficulty": difficulty,
                "count": count
            })

            result_data = json.loads(result)
            return {
                "success": True,
                "practice_set": result_data.get("practice_set", {}),
                "count": result_data.get("count", 0),
                "message": f"已生成 {result_data.get('count', 0)} 道练习题"
            }
        except Exception as e:
            logger.error(f"[RagQuestionAgent] Generate practice error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_explanation(self, user_input: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理答案解析"""
        ctx = request_context.get() or new_context(method="rag_question.explanation")

        tool = self._tool_map.get("get_answer_explanation")
        if not tool:
            return {
                "success": False,
                "error": "get_answer_explanation工具不可用"
            }

        try:
            # 提取问题内容
            question = self._extract_question_from_input(user_input)

            result = tool.invoke({
                "question": question
            })

            result_data = json.loads(result)
            return {
                "success": True,
                "explanation": result_data.get("explanation", ""),
                "answer": result_data.get("answer", ""),
                "message": "答案解析如下"
            }
        except Exception as e:
            logger.error(f"[RagQuestionAgent] Explanation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_keywords(self, text: str) -> str:
        """提取搜索关键词"""
        # 移除常见指令词
        remove_words = ["找", "搜索", "查找", "关于", "的题目", "题", "练习", "测验"]
        keywords = text
        for word in remove_words:
            keywords = keywords.replace(word, "")
        return keywords.strip()

    def _extract_topic(self, text: str) -> str:
        """提取主题"""
        # 简单实现，实际可以更复杂
        remove_words = ["关于", "的", "题", "练习", "题目", "生成", "出", "类似", "相似", "再来", "更多"]
        topic = text
        for word in remove_words:
            topic = topic.replace(word, "")
        return topic.strip()

    def _extract_difficulty(self, text: str) -> str:
        """提取难度等级"""
        text_lower = text.lower()
        if any(w in text_lower for w in ["简单", "基础", "入门"]):
            return "简单"
        elif any(w in text_lower for w in ["困难", "难", "高级"]):
            return "困难"
        elif any(w in text_lower for w in ["中等", "中级"]):
            return "中等"
        return None

    def _extract_count(self, text: str) -> int:
        """提取题目数量"""
        import re
        match = re.search(r"(\d+)\s*道", text)
        if match:
            return int(match.group(1))
        return 5

    def _extract_question_from_input(self, text: str) -> str:
        """从输入中提取问题"""
        # 移除答案解析相关词汇
        remove_words = ["答案", "解析", "解释", "看看", "这个", "这道"]
        question = text
        for word in remove_words:
            question = question.replace(word, "")
        return question.strip()

    def _format_response(self, result: Dict[str, Any]) -> str:
        """格式化响应"""
        if not result.get("success", False):
            return f"❌ 题库检索失败：{result.get('error', '未知错误')}"

        # 搜索题目结果
        if "questions" in result:
            questions = result.get("questions", [])
            if not questions:
                return "🔍 题库中没有找到相关题目，您可以换个关键词试试，或者让我为您生成练习题。"

            response = f"📚 **找到 {len(questions)} 道相关题目**\n\n"
            for i, q in enumerate(questions, 1):
                response += f"**{i}. {q.get('title', '题目' + str(i))}**\n"
                if q.get("options"):
                    for opt in q.get("options", []):
                        response += f"   {opt}\n"
                response += f"   📊 难度：{q.get('difficulty', '未知')}\n\n"
            return response

        # 生成练习集结果
        if "practice_set" in result:
            practice_set = result.get("practice_set", {})
            questions = practice_set.get("questions", [])
            if not questions:
                return "❌ 练习集生成失败，请稍后重试。"

            response = f"📝 **练习集已生成**（{practice_set.get('topic', '未知主题')}）\n\n"
            for i, q in enumerate(questions, 1):
                response += f"**{i}. {q.get('title', '题目' + str(i))}**\n"
                if q.get("options"):
                    for opt in q.get("options", []):
                        response += f"   {opt}\n"
                response += "\n"
            return response

        # 答案解析结果
        if "explanation" in result:
            return f"""📖 **答案解析**

**答案**：{result.get('answer', '暂无')}

**解析**：{result.get('explanation', '暂无解析')}"""

        return "✅ 题库检索完成"
