# -*- coding: utf-8 -*-
"""
音频处理工具模块 (Audio Tools)
提供文字转语音 (TTS) 和语音转文字 (ASR) 能力
"""

import json
from typing import Optional, Tuple
from langchain.tools import tool
from coze_coding_dev_sdk import TTSClient, ASRClient
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.log.write_log import request_context


# ============================================================================
# TTS 文字转语音工具
# ============================================================================

@tool
def tts_synthesize(
    text: str,
    uid: Optional[str] = None,
    speaker: str = "zh_female_xiaohe_uranus_bigtts",
    audio_format: str = "mp3",
    sample_rate: int = 24000,
    speech_rate: int = 0
) -> str:
    """
    文字转语音 (TTS) - 将文本内容转换为语音音频

    适用场景:
    - 将学习内容朗读给用户听
    - 生成语音播报
    - 创建有声内容

    参数:
        text: 要转换的文本内容（必填）
        uid: 用户唯一标识（可选）
        speaker: 声音选择，默认"小和"女声
        audio_format: 音频格式，支持 mp3/pcm/ogg_opus
        sample_rate: 采样率，默认 24000Hz
        speech_rate: 语速调节，范围 -50 到 100

    返回:
        JSON 字符串，包含 audio_url 和 audio_size
    """
    ctx = request_context.get() or new_context(method="tts.synthesize")
    client = TTSClient(ctx=ctx)

    # 文本验证
    if not text or not text.strip():
        return json.dumps({
            "success": False,
            "error": "文本内容不能为空"
        }, ensure_ascii=False)

    try:
        audio_url, audio_size = client.synthesize(
            uid=uid or "default_user",
            text=text,
            speaker=speaker,
            audio_format=audio_format,
            sample_rate=sample_rate,
            speech_rate=speech_rate
        )

        result = {
            "success": True,
            "audio_url": audio_url,
            "audio_size": audio_size,
            "format": audio_format,
            "speaker": speaker,
            "text_preview": text[:50] + "..." if len(text) > 50 else text
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@tool
def tts_announcement(
    text: str,
    uid: Optional[str] = None
) -> str:
    """
    语音播报 (TTS) - 使用播音风格生成语音

    适用场景:
    - 重要通知播报
    - 正式公告
    - 教学讲解

    参数:
        text: 要播报的文本内容（必填）
        uid: 用户唯一标识（可选）

    返回:
        JSON 字符串，包含 audio_url 和 audio_size
    """
    ctx = request_context.get() or new_context(method="tts.announcement")
    client = TTSClient(ctx=ctx)

    if not text or not text.strip():
        return json.dumps({
            "success": False,
            "error": "文本内容不能为空"
        }, ensure_ascii=False)

    try:
        # 使用男声播音员风格
        audio_url, audio_size = client.synthesize(
            uid=uid or "default_user",
            text=text,
            speaker="zh_male_dayi_saturn_bigtts",  # 正式男声
            audio_format="mp3",
            sample_rate=24000,
            speech_rate=0
        )

        result = {
            "success": True,
            "audio_url": audio_url,
            "audio_size": audio_size,
            "format": "mp3",
            "speaker": "zh_male_dayi_saturn_bigtts",
            "style": "announcement",
            "text_preview": text[:50] + "..." if len(text) > 50 else text
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@tool
def tts_storytelling(
    text: str,
    uid: Optional[str] = None
) -> str:
    """
    故事讲解 (TTS) - 使用讲故事风格生成语音

    适用场景:
    - 生动讲解知识点
    - 案例分析讲述
    - 友好的教学风格

    参数:
        text: 要讲述的文本内容（必填）
        uid: 用户唯一标识（可选）

    返回:
        JSON 字符串，包含 audio_url 和 audio_size
    """
    ctx = request_context.get() or new_context(method="tts.storytelling")
    client = TTSClient(ctx=ctx)

    if not text or not text.strip():
        return json.dumps({
            "success": False,
            "error": "文本内容不能为空"
        }, ensure_ascii=False)

    try:
        # 使用甜美女声讲故事
        audio_url, audio_size = client.synthesize(
            uid=uid or "default_user",
            text=text,
            speaker="zh_female_meilinvyou_saturn_bigtts",  # 甜美女声
            audio_format="mp3",
            sample_rate=24000,
            speech_rate=-10  # 稍微放慢，适合讲故事
        )

        result = {
            "success": True,
            "audio_url": audio_url,
            "audio_size": audio_size,
            "format": "mp3",
            "speaker": "zh_female_meilinvyou_saturn_bigtts",
            "style": "storytelling",
            "text_preview": text[:50] + "..." if len(text) > 50 else text
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


# ============================================================================
# ASR 语音转文字工具
# ============================================================================

@tool
def asr_recognize(
    audio_url: str,
    uid: Optional[str] = None
) -> str:
    """
    语音识别 (ASR) - 将音频内容转换为文字

    适用场景:
    - 用户语音输入
    - 语音消息转文字
    - 语音笔记转文本

    参数:
        audio_url: 音频文件 URL（必填）
                   支持格式: MP3, WAV, OGG OPUS, M4A
                   音频时长: ≤ 2小时
                   文件大小: ≤ 100MB
        uid: 用户唯一标识（可选）

    返回:
        JSON 字符串，包含识别结果 text 和详细信息
    """
    ctx = request_context.get() or new_context(method="asr.recognize")
    client = ASRClient(ctx=ctx)

    if not audio_url or not audio_url.strip():
        return json.dumps({
            "success": False,
            "error": "音频URL不能为空"
        }, ensure_ascii=False)

    try:
        text, data = client.recognize(
            uid=uid or "default_user",
            url=audio_url
        )

        # 提取详细信息
        duration = data.get("result", {}).get("duration", 0)

        result = {
            "success": True,
            "text": text,
            "duration_ms": duration,
            "duration_str": f"{duration / 1000:.1f}秒" if duration else "未知",
            "segments": len(data.get("result", {}).get("utterances", []))
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@tool
def asr_recognize_base64(
    base64_data: str,
    uid: Optional[str] = None
) -> str:
    """
    语音识别 (ASR) - 通过 Base64 编码的音频数据进行识别

    适用场景:
    - 前端上传的语音数据
    - 无法提供 URL 的本地音频

    参数:
        base64_data: Base64 编码的音频数据（必填）
        uid: 用户唯一标识（可选）

    返回:
        JSON 字符串，包含识别结果 text 和详细信息
    """
    ctx = request_context.get() or new_context(method="asr.recognize_base64")
    client = ASRClient(ctx=ctx)

    if not base64_data or not base64_data.strip():
        return json.dumps({
            "success": False,
            "error": "Base64 数据不能为空"
        }, ensure_ascii=False)

    try:
        text, data = client.recognize(
            uid=uid or "default_user",
            base64_data=base64_data
        )

        duration = data.get("result", {}).get("duration", 0)

        result = {
            "success": True,
            "text": text,
            "duration_ms": duration,
            "duration_str": f"{duration / 1000:.1f}秒" if duration else "未知"
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


# ============================================================================
# 工具映射表
# ============================================================================

# 用于动态导入的工具映射
TOOL_MAPPING = {
    "tts_synthesize": tts_synthesize,
    "tts_announcement": tts_announcement,
    "tts_storytelling": tts_storytelling,
    "asr_recognize": asr_recognize,
    "asr_recognize_base64": asr_recognize_base64,
}


def get_audio_tools():
    """获取所有音频工具列表"""
    return [
        tts_synthesize,
        tts_announcement,
        tts_storytelling,
        asr_recognize,
        asr_recognize_base64,
    ]


# ============================================================================
# 可用的声音列表（供参考）
# ============================================================================

AVAILABLE_SPEAKERS = {
    # 通用声音
    "zh_female_xiaohe_uranus_bigtts": "小和 (默认女声)",
    "zh_female_vv_uranus_bigtts": "Vivian (中英双语女声)",
    "zh_male_m191_uranus_bigtts": "云舟 (男声)",
    "zh_male_taocheng_uranus_bigtts": "萧天 (男声)",

    # 儿童有声书
    "zh_female_xueayi_saturn_bigtts": "雪艾 (儿童有声书)",

    # 视频配音
    "zh_male_dayi_saturn_bigtts": "大义 (正式男声)",
    "zh_female_mizai_saturn_bigtts": "迷彩 (女声)",
    "zh_female_jitangnv_saturn_bigtts": "鸡汤女 (励志女声)",
    "zh_female_meilinvyou_saturn_bigtts": "魅力女 (甜美女声)",

    # 角色扮演
    "saturn_zh_female_keainvsheng_tob": "可爱女声",
    "saturn_zh_female_tiaopigongzhu_tob": "调皮公主",
    "saturn_zh_male_shuanglangshaonian_tob": "爽朗少年",
}
