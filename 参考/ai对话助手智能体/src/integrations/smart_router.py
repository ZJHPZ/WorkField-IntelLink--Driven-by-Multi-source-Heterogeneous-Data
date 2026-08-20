"""
智能路由器 (Smart Router)

根据用户意图自动选择合适的 LLM 适配器:
- 讯飞大模型: 用于纯对话场景
- Coze 平台: 用于需要工具调用的场景

实现无感知的模型切换，用户体验一致。
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Iterator, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型枚举"""
    # 纯对话类
    CHAT = "chat"                    # 闲聊、问答
    EXPLANATION = "explanation"      # 概念解释
    TRANSLATION = "translation"      # 翻译

    # 工具调用类
    QUESTION = "question"           # 题目练习
    IMAGE = "image"                # 图片生成
    VIDEO = "video"                # 视频生成
    DOCUMENT = "document"           # 文档生成
    LEARNING_PATH = "learning_path" # 学习计划
    KNOWLEDGE = "knowledge"        # 知识检索
    EVALUATION = "evaluation"       # 学习评估

    # 复杂场景
    COMPLEX = "complex"            # 复杂多轮对话
    UNKNOWN = "unknown"            # 未知


@dataclass
class RoutingDecision:
    """路由决策结果"""
    intent: IntentType
    provider: str  # "xunfei" or "coze"
    reason: str
    confidence: float  # 0.0 - 1.0


class IntentClassifier:
    """
    意图分类器

    分析用户输入，判断需要的意图类型。
    """

    # 意图关键词模式
    INTENT_PATTERNS = {
        IntentType.CHAT: [
            r"你好", r"hi", r"hello", r"在吗", r"嗨", r"早", r"晚安",
            r"谢谢", r"再见", r"没事", r"随便聊聊"
        ],
        IntentType.EXPLANATION: [
            r"什么是", r"啥是", r"解释一下", r"介绍一下",
            r"是什么", r"讲讲", r"说说什么是"
        ],
        IntentType.TRANSLATION: [
            r"翻译", r"translate", r"用英文说", r"翻译成"
        ],
        IntentType.QUESTION: [
            r"练习", r"做题", r"测验", r"考考我", r"出题",
            r"刷题", r"作业", r"考试", r"关于.*的题"
        ],
        IntentType.IMAGE: [
            r"图", r"画.*", r"生成.*图", r"给我看.*",
            r"diagram", r"chart", r"流程图", r"架构图"
        ],
        IntentType.VIDEO: [
            r"视频", r"生成.*视频", r"movie", r"动画"
        ],
        IntentType.DOCUMENT: [
            r"文档", r"报告", r"总结", r"生成.*pdf",
            r"生成.*word", r"生成.*ppt", r"写.*文章"
        ],
        IntentType.LEARNING_PATH: [
            r"学习计划", r"怎么学", r"学习路线", r"学习路径",
            r"阶段目标", r"先学.*再学"
        ],
        IntentType.KNOWLEDGE: [
            r"讲讲.*", r"介绍一下.*", r"学.*", r"知识点",
            r"概念", r"原理", r"为什么", r"怎么.*实现"
        ],
        IntentType.EVALUATION: [
            r"评估", r"测试我", r"我.*怎么样", r"水平",
            r"薄弱点", r"哪些.*不懂"
        ]
    }

    # 工具调用关键词
    TOOL_KEYWORDS = [
        r"搜索", r"查询", r"检索", r"查找",
        r"生成", r"创建", r"制作",
        r"调用", r"执行", r"运行"
    ]

    def classify(self, user_input: str) -> RoutingDecision:
        """
        分类用户意图

        Args:
            user_input: 用户输入

        Returns:
            路由决策结果
        """
        user_input_lower = user_input.lower()

        # 1. 检查是否需要工具调用
        needs_tools = self._check_tool_requirement(user_input)

        if needs_tools:
            # 需要工具调用，走 Coze 平台
            intent = self._detect_intent_type(user_input)
            return RoutingDecision(
                intent=intent,
                provider="coze",
                reason=f"检测到需要工具调用: {intent.value}",
                confidence=0.9
            )

        # 2. 纯对话场景，走讯飞
        intent = self._detect_intent_type(user_input)
        return RoutingDecision(
            intent=intent,
            provider="xunfei",
            reason=f"纯对话场景，使用讯飞大模型",
            confidence=0.8
        )

    def _check_tool_requirement(self, user_input: str) -> bool:
        """检查是否需要工具调用"""
        # 检查是否包含工具调用关键词
        for keyword in self.TOOL_KEYWORDS:
            if re.search(keyword, user_input):
                return True

        # 检查意图类型
        intent = self._detect_intent_type(user_input)
        tool_intents = {
            IntentType.QUESTION,
            IntentType.IMAGE,
            IntentType.VIDEO,
            IntentType.DOCUMENT,
            IntentType.LEARNING_PATH,
        }

        if intent in tool_intents:
            return True

        return False

    def _detect_intent_type(self, user_input: str) -> IntentType:
        """检测意图类型"""
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_input):
                    return intent_type

        return IntentType.UNKNOWN


class SmartRouter:
    """
    智能路由器

    根据意图路由到合适的 LLM 适配器。
    """

    def __init__(
        self,
        xunfei_adapter=None,
        coze_adapter=None,
        intent_classifier: Optional[IntentClassifier] = None
    ):
        """
        初始化智能路由器

        Args:
            xunfei_adapter: 讯飞适配器实例
            coze_adapter: Coze 适配器实例
            intent_classifier: 意图分类器
        """
        self.xunfei_adapter = xunfei_adapter
        self.coze_adapter = coze_adapter
        self.intent_classifier = intent_classifier or IntentClassifier()

        # 缓存最近的路由决策
        self._last_decision: Optional[RoutingDecision] = None

    def route(
        self,
        user_input: str,
        messages: Optional[List[Dict[str, str]]] = None,
        force_provider: Optional[str] = None
    ) -> RoutingDecision:
        """
        执行路由决策

        Args:
            user_input: 用户输入
            messages: 对话历史 (用于上下文分析)
            force_provider: 强制使用指定 provider

        Returns:
            路由决策结果
        """
        # 如果强制指定 provider
        if force_provider:
            self._last_decision = RoutingDecision(
                intent=IntentType.UNKNOWN,
                provider=force_provider,
                reason=f"强制使用 {force_provider}",
                confidence=1.0
            )
            return self._last_decision

        # 意图分析
        decision = self.intent_classifier.classify(user_input)
        self._last_decision = decision

        logger.info(f"路由决策: {decision.provider} (意图: {decision.intent.value}, 置信度: {decision.confidence})")

        return decision

    def chat(
        self,
        messages: List[Dict[str, str]],
        user_input: Optional[str] = None,
        force_provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        智能对话

        根据路由决策选择合适的适配器。

        Args:
            messages: 对话消息列表
            user_input: 当前用户输入 (用于意图分析)
            force_provider: 强制使用指定 provider
            **kwargs: 其他参数

        Returns:
            助手回复
        """
        # 获取用户输入（从 messages 中提取）
        if not user_input and messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_input = msg.get("content", "")
                    break

        # 执行路由
        decision = self.route(user_input or "", messages, force_provider)

        # 根据路由选择适配器
        if decision.provider == "xunfei" and self.xunfei_adapter:
            return self.xunfei_adapter.chat(messages, **kwargs)
        elif decision.provider == "coze" and self.coze_adapter:
            return self.coze_adapter.chat(messages, **kwargs)
        else:
            # Fallback: 使用 Coze
            if self.coze_adapter:
                logger.warning("指定适配器不可用，Fallback 到 Coze")
                return self.coze_adapter.chat(messages, **kwargs)
            elif self.xunfei_adapter:
                logger.warning("指定适配器不可用，Fallback 到讯飞")
                return self.xunfei_adapter.chat(messages, **kwargs)
            else:
                return "没有可用的 LLM 适配器"

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        user_input: Optional[str] = None,
        force_provider: Optional[str] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        智能流式对话

        Args:
            messages: 对话消息列表
            user_input: 当前用户输入
            force_provider: 强制使用指定 provider
            **kwargs: 其他参数

        Yields:
            增量文本片段
        """
        # 获取用户输入
        if not user_input and messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_input = msg.get("content", "")
                    break

        # 执行路由
        decision = self.route(user_input or "", messages, force_provider)

        # 根据路由选择适配器
        if decision.provider == "xunfei" and self.xunfei_adapter:
            yield from self.xunfei_adapter.stream_chat(messages, **kwargs)
        elif decision.provider == "coze" and self.coze_adapter:
            yield from self.coze_adapter.stream_chat(messages, **kwargs)
        else:
            # Fallback
            if self.coze_adapter:
                yield from self.coze_adapter.stream_chat(messages, **kwargs)
            elif self.xunfei_adapter:
                yield from self.xunfei_adapter.stream_chat(messages, **kwargs)
            else:
                yield "没有可用的 LLM 适配器"

    def get_last_decision(self) -> Optional[RoutingDecision]:
        """获取最近的路由决策"""
        return self._last_decision


def create_smart_router(
    provider: str = "auto",
    **kwargs
) -> SmartRouter:
    """
    创建智能路由器

    Args:
        provider: 首选 provider ("xunfei", "coze", "auto")
        **kwargs: 其他参数

    Returns:
        SmartRouter 实例
    """
    from .xunfei_adapter import XunfeiAdapter
    from .coze_adapter import CozeAdapter

    xunfei_adapter = None
    coze_adapter = None

    if provider in ["xunfei", "auto"]:
        try:
            xunfei_adapter = XunfeiAdapter(**kwargs)
        except Exception as e:
            logger.warning(f"讯飞适配器初始化失败: {e}")

    if provider in ["coze", "auto"]:
        try:
            coze_adapter = CozeAdapter(**kwargs)
        except Exception as e:
            logger.warning(f"Coze 适配器初始化失败: {e}")

    return SmartRouter(
        xunfei_adapter=xunfei_adapter,
        coze_adapter=coze_adapter
    )
