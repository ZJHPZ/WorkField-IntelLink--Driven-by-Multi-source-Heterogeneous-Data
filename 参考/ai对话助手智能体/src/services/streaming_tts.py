# -*- coding: utf-8 -*-
"""
流式TTS服务模块 (Streaming TTS)
实现边输出边生成音频的功能，将音频URL实时返回给前端播放
"""

import asyncio
import json
import logging
import re
from typing import Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass, field
from coze_coding_dev_sdk import TTSClient
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


@dataclass
class TTSSegment:
    """TTS音频片段"""
    text: str
    audio_url: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class StreamingTTSService:
    """
    流式TTS服务

    功能：
    - 实时接收文本流，智能断句
    - 边接收边生成音频，返回音频URL
    - 支持指定音色（speaker）
    - 支持异步并发生成
    """

    # 句子结束标点（强烈停顿）
    SENTENCE_ENDINGS = {'。', '！', '？', '.', '!', '?'}
    # 子句结束标点（一般停顿）
    CLAUSE_ENDINGS = {'，', '、', ';', ';', ':', '：'}
    # 列表/代码块分隔符
    LIST_MARKERS = {'\n', '•', '-', '*', '#'}

    def __init__(
        self,
        speaker: str = "zh_female_xiaohe_uranus_bigtts",
        min_segment_length: int = 10,  # 最小片段长度
        max_segment_length: int = 200,  # 最大片段长度
        sample_rate: int = 24000,
        audio_format: str = "mp3",
        speech_rate: int = 0
    ):
        """
        初始化流式TTS服务

        Args:
            speaker: 声音选择，默认"小和"女声
            min_segment_length: 最小片段长度（字符）
            max_segment_length: 最大片段长度（字符）
            sample_rate: 采样率
            audio_format: 音频格式
            speech_rate: 语速
        """
        self.speaker = speaker
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
        self.sample_rate = sample_rate
        self.audio_format = audio_format
        self.speech_rate = speech_rate

        # 文本缓冲区
        self._buffer = ""

        # TTS客户端（按需创建）
        self._client: Optional[TTSClient] = None

    @property
    def client(self) -> TTSClient:
        """延迟初始化TTS客户端"""
        if self._client is None:
            ctx = new_context(method="streaming_tts")
            self._client = TTSClient(ctx=ctx)
        return self._client

    def _should_split(self, text: str) -> Tuple[bool, bool]:
        """
        判断是否应该分割文本

        Returns:
            (should_split, is_sentence_end)
            - should_split: 是否应该分割
            - is_sentence_end: 是否是句子级别的分割（vs 子句分割）
        """
        for char in text:
            if char in self.SENTENCE_ENDINGS:
                return True, True
            if char in self.CLAUSE_ENDINGS:
                return True, False
        return False, False

    async def synthesize_segment(self, text: str) -> TTSSegment:
        """
        将文本片段转换为语音

        Args:
            text: 要转换的文本

        Returns:
            TTSSegment: 包含音频URL的片段
        """
        if not text or not text.strip():
            return TTSSegment(text=text, success=True)

        try:
            # 在异步线程中执行同步TTS调用
            loop = asyncio.get_event_loop()
            audio_url, audio_size = await loop.run_in_executor(
                None,
                lambda: self.client.synthesize(
                    uid="streaming_user",
                    text=text.strip(),
                    speaker=self.speaker,
                    audio_format=self.audio_format,
                    sample_rate=self.sample_rate,
                    speech_rate=self.speech_rate
                )
            )

            return TTSSegment(
                text=text,
                audio_url=audio_url,
                success=True
            )

        except Exception as e:
            logger.error(f"[StreamingTTS] TTS synthesis failed: {e}")
            return TTSSegment(
                text=text,
                success=False,
                error=str(e)
            )

    def add_text(self, text: str) -> List[str]:
        """
        添加文本到缓冲区，返回可以合成的片段列表

        Args:
            text: 新增的文本

        Returns:
            List[str]: 可以合成的文本片段列表
        """
        self._buffer += text
        segments = []

        # 尝试从缓冲区中提取完整句子
        while self._buffer:
            should_split, is_sentence_end = self._should_split(self._buffer)

            # 如果遇到分割点或缓冲区过长
            if should_split or len(self._buffer) >= self.max_segment_length:
                # 找到最近的分割点
                split_pos = -1
                for i, char in enumerate(self._buffer):
                    if char in self.SENTENCE_ENDINGS or char in self.CLAUSE_ENDINGS:
                        split_pos = i + 1
                        if char in self.SENTENCE_ENDINGS:
                            break

                if split_pos > 0:
                    # 提取到分割点（包括分割符）
                    segment = self._buffer[:split_pos]
                    self._buffer = self._buffer[split_pos:]
                    segments.append(segment)
                elif len(self._buffer) >= self.max_segment_length:
                    # 没有找到分割点，按最大长度截断
                    segment = self._buffer[:self.max_segment_length]
                    self._buffer = self._buffer[self.max_segment_length:]
                    segments.append(segment)
                else:
                    break
            else:
                break

        return segments

    def flush(self) -> List[str]:
        """
        刷新缓冲区，返回剩余的所有片段

        Returns:
            List[str]: 所有剩余片段
        """
        segments = []
        if self._buffer:
            segments.append(self._buffer)
            self._buffer = ""
        return segments

    async def process_stream(
        self,
        text_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[TTSSegment, None]:
        """
        处理文本流，实时返回音频片段

        Args:
            text_stream: 文本流

        Yields:
            TTSSegment: 音频片段
        """
        async for text in text_stream:
            # 添加文本并获取可合成的片段
            segments = self.add_text(text)

            # 并发合成所有片段
            if segments:
                tasks = [self.synthesize_segment(seg) for seg in segments]
                results = await asyncio.gather(*tasks)

                for result in results:
                    if result.success and result.audio_url:
                        yield result

        # 刷新剩余缓冲区
        remaining = self.flush()
        if remaining:
            tasks = [self.synthesize_segment(seg) for seg in remaining]
            results = await asyncio.gather(*tasks)
            for result in results:
                yield result


class SmartTextChunker:
    """
    智能文本分块器

    专门处理Markdown格式的文本，过滤掉不需要朗读的符号和格式
    """

    # 需要过滤的模式
    FILTER_PATTERNS = [
        (r'```[\s\S]*?```', ''),  # 代码块
        (r'`[^`]+`', ''),  # 行内代码
        (r'#{1,6}\s*', ''),  # 标题标记
        (r'\*\*([^*]+)\*\*', r'\1'),  # 粗体转普通文本
        (r'\*([^*]+)\*', r'\1'),  # 斜体转普通文本
        (r'\[([^\]]+)\]\([^)]+\)', r'\1'),  # 链接转文本
        (r'!\[[^\]]*\]\([^)]+\)', ''),  # 图片
        (r'\|[^|]+\|', ''),  # 表格行
        (r'^[-*+]\s+', '• '),  # 列表标记统一
        (r'^\d+\.\s+', ''),  # 数字列表
    ]

    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        清理文本，只保留需要朗读的内容

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        result = text

        # 应用所有过滤模式
        for pattern, replacement in cls.FILTER_PATTERNS:
            result = re.sub(pattern, replacement, result)

        # 清理多余空白
        result = re.sub(r'\n{3,}', '\n\n', result)  # 超过2个换行变成2个
        result = re.sub(r' {2,}', ' ', result)  # 多个空格变1个
        result = result.strip()

        return result


class StreamingTTSManager:
    """
    流式TTS管理器

    管理多个用户的流式TTS会话
    """

    def __init__(self):
        self._services: dict[str, StreamingTTSService] = {}
        self._lock = asyncio.Lock()

    def get_or_create(
        self,
        session_id: str,
        speaker: str = "zh_female_xiaohe_uranus_bigtts",
        **kwargs
    ) -> StreamingTTSService:
        """
        获取或创建流式TTS服务

        Args:
            session_id: 会话ID
            speaker: 音色选择
            **kwargs: 其他参数

        Returns:
            StreamingTTSService: TTS服务实例
        """
        if session_id not in self._services:
            self._services[session_id] = StreamingTTSService(
                speaker=speaker,
                **kwargs
            )
        else:
            # 更新音色设置
            self._services[session_id].speaker = speaker

        return self._services[session_id]

    async def remove(self, session_id: str) -> None:
        """
        移除会话的TTS服务

        Args:
            session_id: 会话ID
        """
        async with self._lock:
            if session_id in self._services:
                del self._services[session_id]


# 全局TTS管理器
streaming_tts_manager = StreamingTTSManager()
