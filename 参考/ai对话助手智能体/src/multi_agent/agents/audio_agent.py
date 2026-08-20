# -*- coding: utf-8 -*-
"""
语音处理Agent - 处理文字转语音(TTS)和语音转文字(ASR)
"""
import json
import logging
from typing import Dict, Any, List, Optional

from multi_agent.base.base_agent import BaseAgent
from multi_agent.base.agent_state import IntentType, MultiAgentState
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.log.write_log import request_context

logger = logging.getLogger(__name__)


class AudioAgent(BaseAgent):
    """语音处理Agent"""

    def __init__(self, agent_id: str = "audio", agent_name: str = "语音处理Agent"):
        super().__init__(agent_id, agent_name)
        self.description = "处理文字转语音(TTS)和语音转文字(ASR)"
        self._tools = None
        self._tool_map = {}
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.AUDIO
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[AudioAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理语音请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing audio request: {user_input[:50]}...")
        
        return await self._execute_impl(state)

    def _build_system_prompt(self) -> str:
        """构建语音Agent的系统提示词"""
        return """# 角色：语音处理专家

你是一个语音处理专家，负责：
1. 将文本内容转换为语音（TTS - Text to Speech）
2. 将语音内容转换为文字（ASR - Automatic Speech Recognition）

## 可用的语音工具

### TTS 文字转语音
- `tts_synthesize`: 通用文字转语音
- `tts_announcement`: 播音风格语音（适合正式通知）
- `tts_storytelling`: 讲故事风格语音（适合生动讲解）

### ASR 语音转文字
- `asr_recognize`: 通过URL识别语音
- `asr_recognize_base64`: 通过Base64数据识别语音

## 使用场景

1. **语音播报**：用户希望"朗读"学习内容
2. **语音输入**：用户通过语音提问（需要先ASR转文字）
3. **有声内容**：生成有声学习材料

## 输出格式

对于TTS请求，返回：
```json
{
  "success": true,
  "audio_url": "https://...",
  "audio_size": 12345,
  "format": "mp3",
  "speaker": "zh_female_xiaohe_uranus_bigtts"
}
```

对于ASR请求，返回：
```json
{
  "success": true,
  "text": "识别的文字内容",
  "duration_ms": 5000
}
```

## 注意事项

- 如果用户没有指定声音风格，根据内容选择合适的：
  - 正式通知 → tts_announcement
  - 生动讲解 → tts_storytelling
  - 其他场景 → tts_synthesize
"""

    def _get_tool_names(self) -> List[str]:
        """获取该Agent使用的工具名称"""
        return [
            "tts_synthesize", "tts_announcement", "tts_storytelling",
            "asr_recognize", "asr_recognize_base64"
        ]

    async def _execute_impl(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行语音处理"""
        ctx = request_context.get() or new_context(method=f"audio.agent")

        # 获取用户输入
        user_input = self._get_user_input(state)
        multimodal_data = state.get("multimodal_data")

        # 检查是否有语音数据输入
        if multimodal_data and multimodal_data.get("audio_url"):
            # 用户上传了语音，需要先ASR转文字
            audio_url = multimodal_data["audio_url"]
            asr_result = self._tool_map["asr_recognize"].invoke({
                "audio_url": audio_url,
                "uid": state.get("user_id", "default_user")
            })

            try:
                asr_data = json.loads(asr_result)
                if asr_data.get("success"):
                    user_input = asr_data.get("text", user_input)
                    logger.info(f"[AudioAgent] ASR recognized: {user_input}")
                else:
                    return {
                        "success": False,
                        "error": f"ASR识别失败: {asr_data.get('error', '未知错误')}"
                    }
            except json.JSONDecodeError:
                logger.error("[AudioAgent] Failed to parse ASR result")

        # 根据输入判断用户意图
        input_lower = user_input.lower()

        # 判断是否需要TTS（文字转语音）
        tts_keywords = ["读", "朗读", "播放", "语音播报", "有声", "播报", "读给我听"]
        needs_tts = any(keyword in input_lower for keyword in tts_keywords)

        # 判断是否需要ASR（语音转文字）
        asr_keywords = ["语音", "说话", "录音", "语音输入"]
        needs_asr_input = any(keyword in input_lower for keyword in asr_keywords) and multimodal_data

        if needs_tts and not multimodal_data:
            # 用户要求将文本转为语音
            return await self._handle_tts(user_input, state)
        elif needs_asr_input:
            # 用户提供了语音输入
            return await self._handle_asr(multimodal_data, state)
        else:
            # 默认处理：返回语音处理能力说明
            return {
                "success": True,
                "message": "语音处理Agent已就绪",
                "capabilities": {
                    "tts": ["tts_synthesize", "tts_announcement", "tts_storytelling"],
                    "asr": ["asr_recognize", "asr_recognize_base64"]
                }
            }

    async def _handle_tts(self, text: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理TTS请求"""
        ctx = request_context.get() or new_context(method="audio.handle_tts")

        # 提取要转语音的文本
        # 移除TTS相关的关键词
        tts_keywords = ["读", "朗读", "播放", "语音播报", "有声", "播报", "读给我听"]
        content_text = text
        for keyword in tts_keywords:
            content_text = content_text.replace(keyword, "")

        if not content_text.strip():
            content_text = "您好，有什么可以帮助您的？"

        # 选择合适的声音
        input_lower = text.lower()
        if "通知" in text or "公告" in text:
            tool_name = "tts_announcement"
        elif "讲" in text or "故事" in text or "讲解" in text:
            tool_name = "tts_storytelling"
        else:
            tool_name = "tts_synthesize"

        # 调用TTS工具
        tool = self._tool_map.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"TTS工具 {tool_name} 不可用"
            }

        try:
            result = tool.invoke({
                "text": content_text,
                "uid": state.get("user_id", "default_user")
            })

            result_data = json.loads(result)
            if result_data.get("success"):
                return {
                    "success": True,
                    "event": "tts_success",
                    "audio_url": result_data.get("audio_url"),
                    "audio_size": result_data.get("audio_size"),
                    "format": result_data.get("format", "mp3"),
                    "message": "语音生成成功！"
                }
            else:
                return {
                    "success": False,
                    "error": f"语音生成失败: {result_data.get('error', '未知错误')}"
                }
        except Exception as e:
            logger.error(f"[AudioAgent] TTS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_asr(self, multimodal_data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """处理ASR请求"""
        ctx = request_context.get() or new_context(method="audio.handle_asr")

        audio_url = multimodal_data.get("audio_url")
        base64_data = multimodal_data.get("audio_base64")

        if not audio_url and not base64_data:
            return {
                "success": False,
                "error": "未提供音频数据"
            }

        # 选择合适的ASR工具
        if base64_data:
            tool = self._tool_map.get("asr_recognize_base64")
            tool_input = {
                "base64_data": base64_data,
                "uid": state.get("user_id", "default_user")
            }
        else:
            tool = self._tool_map.get("asr_recognize")
            tool_input = {
                "audio_url": audio_url,
                "uid": state.get("user_id", "default_user")
            }

        if not tool:
            return {
                "success": False,
                "error": "ASR工具不可用"
            }

        try:
            result = tool.invoke(tool_input)
            result_data = json.loads(result)

            if result_data.get("success"):
                return {
                    "success": True,
                    "event": "asr_success",
                    "text": result_data.get("text"),
                    "duration_ms": result_data.get("duration_ms"),
                    "message": "语音识别成功！"
                }
            else:
                return {
                    "success": False,
                    "error": f"语音识别失败: {result_data.get('error', '未知错误')}"
                }
        except Exception as e:
            logger.error(f"[AudioAgent] ASR error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _format_response(self, result: Dict[str, Any]) -> str:
        """格式化响应"""
        if not result.get("success", False):
            return f"❌ 语音处理失败：{result.get('error', '未知错误')}"

        # TTS成功
        if "audio_url" in result:
            audio_url = result["audio_url"]
            return f"""🎙️ **语音生成成功！**

🔊 音频已生成，点击播放：[点击播放]({audio_url})

📊 信息：
- 格式：{result.get('format', 'mp3')}
- 大小：{result.get('audio_size', 0)} bytes

💡 您可以直接点击上方链接收听，或右键保存到本地。"""

        # ASR成功
        if "text" in result:
            text = result["text"]
            duration = result.get("duration_ms", 0)
            return f"""🎙️ **语音识别成功！**

📝 识别结果：
{text}

⏱️ 时长：{duration / 1000:.1f} 秒

💡 如果识别有误，请告诉我，我会重新为您识别。"""

        # 默认
        return "✅ 语音处理完成"
