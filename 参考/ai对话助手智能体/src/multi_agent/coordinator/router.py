"""
Intent Router
意图路由器 - 识别用户意图并路由到对应Agent
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..base.agent_state import IntentType

logger = logging.getLogger(__name__)


@dataclass
class IntentPattern:
    """意图模式"""
    keywords: List[str]
    intent_type: IntentType
    priority: int = 0
    examples: List[str] = None


class IntentRouter:
    """
    意图路由器
    
    根据用户输入识别意图类型，并路由到对应的Agent。
    使用关键词匹配 + 模式识别的方式。
    """
    
    # 默认意图模式
    DEFAULT_PATTERNS = [
        # 邮件发送 - 最高优先级，避免被其他模式拦截
        IntentPattern(
            keywords=["邮件", "邮箱", "发送", "发到", "发一封", "email", "写信", "写信给", "道歉信", "祝福信", "感谢信"],
            intent_type=IntentType.EMAIL,
            priority=5,
            examples=["发送学习计划到邮箱", "写一封道歉信"]
        ),
        
        # 多模态理解 - 最高优先级，处理用户上传的图片/视频/音频
        IntentPattern(
            keywords=["看图", "看这张图", "看那张图", "这张图", "那张图", "分析图", "解释图", "这是什么图", "图片分析", "图片解释", "图片里", "图中", "图上", "看图片", "分析图片"],
            intent_type=IntentType.MULTIMODAL,
            priority=8,  # 最高优先级
            examples=["看这张图讲讲", "分析这张图片", "这是什么图", "图片里是什么"]
        ),
        
        # 图片/视频生成 - 高优先级，确保多媒体生成优先于其他意图
        IntentPattern(
            keywords=["生成图", "生成图片", "生成视频", "制作图", "制作图片", "制作视频", "图解", "可视化", "画一个", "配图", "示意图", "概念图", "思维导图", "结构图", "流程图", "diagram", "生成一张", "生成一个", "做一张", "做一个", "视频", "短视频", "教学视频", "动画", "影片", "录像", "做个图", "做张图"],
            intent_type=IntentType.MULTIMEDIA,
            priority=7,  # 高优先级
            examples=["生成一张解释闭包的图片", "做一个动画演示", "生成一张概念图", "生成教学视频", "制作短视频"]
        ),
        
        # 文档生成 - 笔记、生成笔记、整理笔记（优先级高于学习路径）
        IntentPattern(
            keywords=["整理", "文档", "大纲", "笔记", "总结", "归纳", "报告", "写个", "生成笔记", "生成学习笔记", "整理笔记"],
            intent_type=IntentType.DOCUMENT,
            priority=7,  # 高于 LEARNING_PATH 的 6
            examples=["帮我整理Python的基础知识", "写一份报告", "生成学习笔记", "帮我生成笔记"]
        ),
        
        # 题库练习 - 高优先级，确保题目相关意图优先于学习路径
        IntentPattern(
            keywords=["练习", "做题", "出题", "题", "考试", "测验", "测试", "检验", "挑战"],
            intent_type=IntentType.QUESTION,
            priority=4,
            examples=["给我出几道Python练习题", "我想做点题巩固一下"]
        ),
        
        # 答疑解惑 - 确保技术问题被正确识别，优先级高于技术名称匹配
        IntentPattern(
            keywords=["疑问", "不懂", "为什么", "解释", "什么意思", "怎样", "问", "解答", "讲解", "区别", "比较", "对比", "是什么", "什么是", "讲讲", "介绍", "做什么", "什么用", "有什么用", "用来", "关系", "有什么关系", "有什么", "干嘛", "干啥的", "用来干嘛", "是用", "做啥", "理解"],
            intent_type=IntentType.QA,
            priority=6,  # 高优先级
            examples=["为什么Python要用缩进", "装饰器是什么意思", "Hadoop和Spark有什么区别", "什么是Hadoop", "介绍一下Spark", "Kafka是做什么用的", "Hive和HDFS有什么关系", "如何理解闭包", "怎么理解"]
        ),
        
        # 学习路径 - 确保学习意图被正确识别（放在QA之后，但优先级相同）
        IntentPattern(
            keywords=["学习", "想学习", "想学", "要学习", "要学", "学习计划", "制定计划", "规划学习", "学习路径", "学习路线", "学习方案", "怎么学", "如何学习", "从头学", "系统学习", "开始学习"],
            intent_type=IntentType.LEARNING_PATH,
            priority=6,  # 高优先级，与QA同等
            examples=["帮我制定一个学习计划", "如何系统学习Python", "我想从头学习大数据", "如何系统学习Spark", "我想学习Python编程", "我要学Java", "Hadoop怎么学"]
        ),
        
        # 学习评估（优先级高于学习路径）
        IntentPattern(
            keywords=["评估", "评价", "水平", "效果", "分析", "诊断", "检测", "评估一下", "成果", "分析学习效果", "学习评估", "水平评估", "效果评估", "能力评估"],
            intent_type=IntentType.EVALUATION,
            priority=7,  # 高于 LEARNING_PATH 的 6
            examples=["评估一下我的Python水平", "分析一下学习效果", "评价一下我的能力"]
        ),
        
        # 对话学习 - 最低优先级兜底（但系统学习特定技术时不应该匹配）
        IntentPattern(
            keywords=["你好", "心情", "难过", "开心", "分享", "交流", "讨论", "聊聊", "说说", "迷茫", "焦虑"],
            intent_type=IntentType.CONVERSATION,
            priority=1,
            examples=["我想学习Python", "能告诉我什么是机器学习吗"]
        ),
        
        # 个性化推荐 - 优先级高于学习路径
        IntentPattern(
            keywords=["推荐", "推送", "建议", "适合我", "个性化", "教程推荐", "资源推荐", "网站推荐", "课程推荐", "好网站", "好教程", "好课程", "学习资源", "学习网站", "学习教程"],
            intent_type=IntentType.RECOMMENDATION,
            priority=8,  # 高于 LEARNING_PATH 的 6
            examples=["推荐一些学习内容", "推送适合我的资料", "推荐一些Python学习网站", "有什么好的教程推荐"]
        ),
        
        # 语音处理 (TTS/ASR) - 高优先级
        IntentPattern(
            keywords=["语音输入", "语音播报", "读给我听", "朗读", "播放", "有声", "读一下", "说出来", "录音"],
            intent_type=IntentType.AUDIO,
            priority=5,
            examples=["把这段话读给我听", "我语音输入一个问题", "播放这个知识点"]
        ),
        
        # RAG题库检索 - 高优先级
        IntentPattern(
            keywords=["题库搜索", "题库检索", "从题库搜索", "题库找", "题目检索", "搜索题目", "题库", "检索题目"],
            intent_type=IntentType.RAG_QUESTION,
            priority=5,
            examples=["从题库搜索Spark相关题目", "检索Hadoop的练习题"]
        ),
    ]
    
    def __init__(self, patterns: Optional[List[IntentPattern]] = None):
        """
        初始化意图路由器
        
        Args:
            patterns: 自定义意图模式列表
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self._build_index()
        logger.info(f"[IntentRouter] Initialized with {len(self.patterns)} patterns")
    
    def recognize_intent(self, user_input: str, multimodal_data: Optional[Dict] = None) -> IntentType:
        """识别单个主要意图（兼容旧接口）"""
        intents = self.recognize_intents(user_input, multimodal_data)
        return intents[0] if intents else IntentType.CONVERSATION

    def recognize_intents(self, user_input: str, multimodal_data: Optional[Dict] = None) -> List[IntentType]:
        """
        ✅ 新增：识别多个意图
        
        适用于多意图场景，例如：
        - "帮我规划学习计划并发送到邮箱" → [LEARNING_PATH, EMAIL]
        - "解释一下Spark并生成思维导图" → [QA, MULTIMEDIA]

        Args:
            user_input: 用户输入文本
            multimodal_data: 多模态数据字典

        Returns:
            识别的意图类型列表（按优先级排序）
        """
        # 优先检测多模态
        if multimodal_data and any(
            multimodal_data.get(k) for k in ("images", "videos", "audio", "files")
        ):
            logger.info(
                f"[IntentRouter] Multimodal input detected, "
                f"images={len(multimodal_data.get('images', []))}, "
                f"videos={len(multimodal_data.get('videos', []))}, "
                f"audio={len(multimodal_data.get('audio', []))}"
            )
            return [IntentType.MULTIMODAL]

        if not user_input:
            return [IntentType.CONVERSATION]

        # 按优先级排序
        sorted_patterns = sorted(self.patterns, key=lambda p: p.priority, reverse=True)

        # ✅ 支持多意图：收集所有匹配的意图
        matched_intents: List[IntentType] = []
        matched_keywords: Dict[IntentType, List[str]] = {}  # 用于调试
        
        for pattern in sorted_patterns:
            for keyword in pattern.keywords:
                # 使用小写匹配，不区分大小写
                if keyword.lower() in user_input.lower():
                    if pattern.intent_type not in matched_intents:
                        matched_intents.append(pattern.intent_type)
                        matched_keywords[pattern.intent_type] = []
                    matched_keywords[pattern.intent_type].append(keyword)
                    # ✅ 继续检查其他意图，不要break

        if matched_intents:
            logger.info(
                f"[IntentRouter] Recognized {len(matched_intents)} intents: {matched_intents} "
                f"(matched: {matched_keywords})"
            )
            return matched_intents

        # 默认返回对话
        return [IntentType.CONVERSATION]
    
    def _build_index(self) -> None:
        """构建关键词索引"""
        self._keyword_index: Dict[str, List[IntentPattern]] = {}
        
        for pattern in self.patterns:
            for keyword in pattern.keywords:
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = []
                self._keyword_index[keyword].append(pattern)
        
        # 按优先级排序
        for keyword in self._keyword_index:
            self._keyword_index[keyword].sort(key=lambda p: p.priority)
    
    def add_pattern(self, pattern: IntentPattern) -> None:
        """添加意图模式"""
        self.patterns.append(pattern)
        
        for keyword in pattern.keywords:
            if keyword not in self._keyword_index:
                self._keyword_index[keyword] = []
            self._keyword_index[keyword].append(pattern)
            self._keyword_index[keyword].sort(key=lambda p: p.priority)
        
        logger.info(f"[IntentRouter] Added pattern: {pattern.intent_type}")
    
    def recognize_multi(self, user_input: str, multimodal_data: Optional[Dict] = None) -> Tuple[List[IntentType], float, List[IntentPattern]]:
        """
        ✅ 新增：识别多个意图（多意图场景）
        
        适用于多意图场景，例如：
        - "帮我规划学习计划并发送到邮箱" → [LEARNING_PATH, EMAIL]
        - "介绍一下Hadoop并发送到邮箱 3461953863@qq.com" → [QA, EMAIL]
        - "解释一下Spark并生成思维导图" → [QA, MULTIMEDIA]

        Args:
            user_input: 用户输入文本
            multimodal_data: 多模态数据字典

        Returns:
            (意图类型列表, 置信度, 匹配的意图模式列表)
        """
        # ✅ 快速路径：多模态输入直接返回多模态意图
        if multimodal_data and any(multimodal_data.get(k) for k in ("images", "videos", "audio", "files")):
            logger.info("[IntentRouter] Fast path: multimodal input detected")
            return [IntentType.MULTIMODAL], 0.99, []

        if not user_input or not user_input.strip():
            return [IntentType.CONVERSATION], 0.5, []

        user_input_lower = user_input.lower().strip()
        matched_patterns = []
        seen_intents = set()

        # ✅ 支持多意图：收集所有匹配的意图模式
        for keyword, patterns in self._keyword_index.items():
            if keyword in user_input_lower:
                for pattern in patterns:
                    if pattern.intent_type not in seen_intents:
                        seen_intents.add(pattern.intent_type)
                        matched_patterns.append(pattern)

        if matched_patterns:
            # 按优先级排序
            matched_patterns.sort(key=lambda p: p.priority, reverse=True)
            
            # 计算置信度
            keyword_count = len(matched_patterns)
            top_priority = matched_patterns[0].priority if matched_patterns else 6
            base_confidence = 0.7 + (top_priority * 0.05)
            bonus = min(keyword_count * 0.02, 0.15)
            
            # 多意图时降低置信度，但保持合理范围
            confidence = min(base_confidence + bonus - 0.1, 0.9)
            
            intent_types = [p.intent_type for p in matched_patterns]
            logger.info(
                f"[IntentRouter] Recognized {len(intent_types)} intents: {intent_types} "
                f"(confidence: {confidence:.2f})"
            )
            return intent_types, confidence, matched_patterns

        return [IntentType.CONVERSATION], 0.5, []
    
    def recognize(self, user_input: str, multimodal_data: Optional[Dict] = None) -> Tuple[IntentType, float, List[IntentPattern]]:
        """
        识别用户意图（兼容旧接口 - 返回单个意图）
        
        Args:
            user_input: 用户输入
            multimodal_data: 多模态数据
            
        Returns:
            (意图类型, 置信度, 匹配的意图模式列表)
        """
        intents, confidence, patterns = self.recognize_multi(user_input, multimodal_data)
        return intents[0] if intents else IntentType.CONVERSATION, confidence, patterns
    
    def route(self, user_input: str) -> List[Tuple[IntentType, float]]:
        """
        路由用户输入到多个可能的意图
        
        Args:
            user_input: 用户输入
            
        Returns:
            [(意图类型, 置信度), ...] 按置信度降序排列
        """
        _, confidence, patterns = self.recognize(user_input)
        
        results = [(patterns[0].intent_type, confidence)]
        
        # 如果有多个匹配的模式，返回所有可能意图
        for pattern in patterns[1:]:
            # 降低后续意图的置信度
            reduced_confidence = confidence * 0.7
            results.append((pattern.intent_type, reduced_confidence))
        
        return results
    
    def route_to_agent(self, intent: IntentType) -> str:
        """
        根据意图类型路由到对应的Agent ID

        Args:
            intent: 意图类型

        Returns:
            Agent ID
        """
        # 意图类型到Agent ID的映射
        INTENT_TO_AGENT = {
            IntentType.CONVERSATION: "conversation",
            IntentType.DOCUMENT: "document",
            IntentType.QUESTION: "question",
            IntentType.MULTIMEDIA: "multimedia",
            IntentType.MULTIMODAL: "multimodal",  # ✅ 新增多模态路由
            IntentType.QA: "qa",
            IntentType.LEARNING_PATH: "learning_path",
            IntentType.EVALUATION: "evaluation",
            IntentType.RECOMMENDATION: "recommendation",
            IntentType.EMAIL: "email",
            IntentType.UNKNOWN: "conversation",
        }

        return INTENT_TO_AGENT.get(intent, "conversation")
    
    def get_agent_mapping(self) -> Dict[IntentType, str]:
        """获取意图到Agent的映射"""
        return {
            IntentType.CONVERSATION: "conversation",
            IntentType.DOCUMENT: "document",
            IntentType.QUESTION: "question",
            IntentType.MULTIMEDIA: "multimedia",
            IntentType.QA: "qa",
            IntentType.LEARNING_PATH: "learning_path",
            IntentType.EVALUATION: "evaluation",
            IntentType.RECOMMENDATION: "recommendation",
        }
    
    def get_intent_description(self, intent_type: IntentType) -> str:
        """获取意图类型的描述"""
        descriptions = {
            IntentType.CONVERSATION: "对话学习 - 了解学习需求，采集用户信息",
            IntentType.DOCUMENT: "文档生成 - 生成知识文档、思维导图",
            IntentType.QUESTION: "题库练习 - 生成练习题、测试题",
            IntentType.MULTIMEDIA: "多媒体生成 - 生成图片、视频、动画",
            IntentType.QA: "答疑解惑 - 解答学习中的疑问",
            IntentType.LEARNING_PATH: "学习路径 - 制定学习计划、规划学习路径",
            IntentType.EVALUATION: "学习评估 - 评估学习效果、分析学习水平",
            IntentType.RECOMMENDATION: "个性化推荐 - 推荐学习内容、推送提醒",
            IntentType.UNKNOWN: "未知意图 - 需要更多上下文",
        }
        return descriptions.get(intent_type, "未知意图")


# 全局路由器实例
_global_router: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    """获取全局意图路由器实例"""
    global _global_router
    if _global_router is None:
        _global_router = IntentRouter()
    return _global_router
