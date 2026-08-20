# -*- coding: utf-8 -*-
"""
独立TTS服务 - 专门处理文本转语音
与对话逻辑解耦，可以给任意文本生成语音
"""

import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from coze_coding_dev_sdk import TTSClient
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


@dataclass
class TTSResult:
    """TTS结果"""
    success: bool
    audio_url: Optional[str] = None
    audio_size: Optional[int] = None
    format: Optional[str] = None
    speaker: Optional[str] = None
    error: Optional[str] = None


class StandaloneTTSService:
    """
    独立TTS服务

    功能：
    - 给任意文本生成语音
    - 支持多种音色选择
    - 与对话逻辑解耦
    """

    # 默认音色
    DEFAULT_SPEAKER = "zh_female_xiaohe_uranus_bigtts"

    # 可用音色列表
    SPEAKERS = {
        "zh_female_xiaohe_uranus_bigtts": "小和（温柔女声）",
        "zh_female_vv_uranus_bigtts": "Vivian（双语女声）",
        "zh_male_m191_uranus_bigtts": "云舟（清晰男声）",
        "zh_male_taocheng_uranus_bigtts": "萧天（稳重男声）",
        "zh_male_dayi_saturn_bigtts": "大义（正式播音男声）",
        "zh_female_xueayi_saturn_bigtts": "雪艾（儿童故事）",
    }

    def __init__(self):
        self._client: Optional[TTSClient] = None

    @property
    def client(self) -> TTSClient:
        """延迟初始化TTS客户端"""
        if self._client is None:
            ctx = new_context(method="standalone_tts")
            self._client = TTSClient(ctx=ctx)
        return self._client

    def synthesize(
        self,
        text: str,
        speaker: str = DEFAULT_SPEAKER,
        audio_format: str = "mp3",
        sample_rate: int = 24000,
        speech_rate: int = 0,
        uid: str = "default_user"
    ) -> TTSResult:
        """
        将文本转换为语音

        Args:
            text: 要转换的文本
            speaker: 音色选择
            audio_format: 音频格式
            sample_rate: 采样率
            speech_rate: 语速
            uid: 用户ID

        Returns:
            TTSResult: TTS结果
        """
        if not text or not text.strip():
            return TTSResult(success=False, error="文本不能为空")

        try:
            audio_url, audio_size = self.client.synthesize(
                uid=uid,
                text=text.strip(),
                speaker=speaker,
                audio_format=audio_format,
                sample_rate=sample_rate,
                speech_rate=speech_rate
            )

            return TTSResult(
                success=True,
                audio_url=audio_url,
                audio_size=audio_size,
                format=audio_format,
                speaker=speaker
            )

        except Exception as e:
            logger.error(f"[StandaloneTTS] TTS synthesis failed: {e}")
            return TTSResult(success=False, error=str(e))

    def synthesize_batch(
        self,
        texts: list,
        speaker: str = DEFAULT_SPEAKER,
        audio_format: str = "mp3",
        sample_rate: int = 24000,
        speech_rate: int = 0,
        uid: str = "default_user"
    ) -> list:
        """
        批量将多个文本片段转换为语音

        Args:
            texts: 文本片段列表
            speaker: 音色选择
            audio_format: 音频格式
            sample_rate: 采样率
            speech_rate: 语速
            uid: 用户ID

        Returns:
            list: TTSResult列表
        """
        results = []
        for i, text in enumerate(texts):
            result = self.synthesize(
                text=text,
                speaker=speaker,
                audio_format=audio_format,
                sample_rate=sample_rate,
                speech_rate=speech_rate,
                uid=f"{uid}_segment_{i}"
            )
            results.append({
                "index": i,
                "text": text[:50] + "..." if len(text) > 50 else text,
                "result": result
            })
        return results

    def get_available_speakers(self) -> Dict[str, str]:
        """获取可用音色列表"""
        return self.SPEAKERS.copy()


# 全局TTS服务实例
_tts_service: Optional[StandaloneTTSService] = None


def get_tts_service() -> StandaloneTTSService:
    """获取全局TTS服务实例"""
    global _tts_service
    if _tts_service is None:
        _tts_service = StandaloneTTSService()
    return _tts_service
