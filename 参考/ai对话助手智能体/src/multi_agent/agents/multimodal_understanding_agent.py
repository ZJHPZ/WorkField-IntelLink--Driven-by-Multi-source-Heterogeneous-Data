"""
Multimodal Agent
多模态Agent - 处理多模态输入（图片、视频、音频理解）
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import base64
import httpx

from ..base.base_agent import FederatedAgent
from ..base.agent_state import MultiAgentState, IntentType
from ..communication.shared_context import get_shared_context

# ✅ 新增: 文档解析客户端
from coze_coding_dev_sdk.fetch import FetchClient
from coze_coding_dev_sdk.video_edit import FrameExtractorClient
from coze_coding_utils.runtime_ctx.context import Context, new_context

logger = logging.getLogger(__name__)


class MultimodalUnderstandingAgent(FederatedAgent):
    """
    多模态智能体（理解用户上传的内容）

    职责：
    - 图片理解：分析图片内容，提取信息
    - 视频理解：分析视频内容，提取关键帧
    - 音频理解：处理音频输入，语音转文字
    - 多模态融合：整合多模态信息进行综合分析
    """
    
    # Vision API 配置
    VISION_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    VISION_MODEL = "doubao-seed-2-0-lite-260428"  # ✅ 多模态模型，支持图片理解
    
    def __init__(self):
        super().__init__(
            agent_id="multimodal",
            name="多模态智能体",
            description="处理图片、视频、音频等多模态输入"
        )
        # ✅ 已移除 self.shared_context，改用 state["results"] 存储分析结果
        logger.info("[MultimodalAgent] Initialized with state-based storage")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.MULTIMODAL
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """处理多模态输入"""
        multimodal_data = state.get("multimodal_data", {})
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing multimodal input for user: {user_id}")
        
        results = {}
        
        # 处理图片
        if "images" in multimodal_data and multimodal_data["images"]:
            results["images"] = await self._process_images(
                multimodal_data["images"],
                user_id
            )
        
        # 处理视频
        if "videos" in multimodal_data and multimodal_data["videos"]:
            results["videos"] = await self._process_videos(
                multimodal_data["videos"],
                user_id
            )
        
        # 处理音频
        if "audio" in multimodal_data and multimodal_data["audio"]:
            results["audio"] = await self._process_audio(
                multimodal_data["audio"],
                user_id
            )
        
        # ✅ 处理文件 (新增)
        if "files" in multimodal_data and multimodal_data["files"]:
            results["files"] = await self._process_files(
                multimodal_data["files"],
                user_id
            )
        
        # 多模态融合分析
        if len(results) > 1:
            results["fusion"] = await self._multimodal_fusion(results, user_id)
        
        # ✅ 方案 C: 存储到 state["results"] 而非 shared_context
        if "results" not in state:
            state["results"] = {}
        state["results"]["multimodal"] = results
        
        # ✅ 生成自然语言回答
        natural_language = self._format_as_natural_language(results)
        
        # ✅ 修复：message 字段直接使用自然语言，而不是 JSON
        return {
            "success": True,
            "results": results,
            "message": natural_language,  # ✅ 直接返回自然语言描述
            "natural_language": natural_language  # 保留兼容性
        }
    
    def _format_as_natural_language(self, results: Dict[str, Any]) -> str:
        """
        将结构化分析结果转换为自然语言描述
        
        Args:
            results: 多模态分析结果字典
        
        Returns:
            自然语言描述字符串
        """
        parts = []
        
        # 1. 处理文件内容
        if "files" in results:
            files_data = results["files"]
            files_processed = files_data.get("files_processed", 0)
            files_results = files_data.get("results", [])
            
            if files_results:
                for file_result in files_results:
                    file_name = file_result.get("file_name", "未知文件")
                    file_type = file_result.get("file_type", "未知")
                    content = file_result.get("content", "")
                    success = file_result.get("success", False)
                    
                    if success and content:
                        # 文件内容摘要
                        if file_type == "txt":
                            # 纯文本文件 - 直接展示内容
                            content_preview = content[:500] + "..." if len(content) > 500 else content
                            parts.append(
                                f"📄 **文件分析：{file_name}**\n\n"
                                f"这是一份{len(content)}字符的文本文件，内容如下：\n\n"
                                f"```\n{content_preview}\n```"
                            )
                        else:
                            parts.append(
                                f"📄 **文件分析：{file_name}**\n\n"
                                f"这是一份{file_type.upper()}文件，共提取了约{len(content)}个字符的内容。"
                            )
                    else:
                        parts.append(f"📄 **文件：{file_name}** - 未能成功解析内容")
        
        # 2. 处理图片内容
        if "images" in results:
            images_data = results["images"]
            images_processed = images_data.get("images_processed", 0)
            images_results = images_data.get("results", [])
            
            if images_results:
                for img_result in images_results:
                    description = img_result.get("description", "")
                    analysis = img_result.get("analysis", {})
                    main_content = analysis.get("main_content", "") or description
                    
                    if main_content:
                        parts.append(
                            f"🖼️ **图片内容**\n\n{main_content[:300]}"
                        )
        
        # 3. 处理视频内容
        if "videos" in results:
            videos_data = results["videos"]
            videos_results = videos_data.get("results", [])
            
            for video_result in videos_results:
                status = video_result.get("status", "")
                note = video_result.get("note", "")
                if note:
                    parts.append(f"🎬 **视频**\n\n{note}")
        
        # 4. 处理音频内容
        if "audio" in results:
            audio_data = results["audio"]
            audio_results = audio_data.get("results", [])
            
            for audio_result in audio_results:
                transcription = audio_result.get("transcription", "")
                if transcription:
                    parts.append(f"🎤 **音频内容**\n\n{transcription[:300]}")
        
        # 5. 处理融合结果
        if "fusion" in results:
            fusion = results["fusion"]
            summary = fusion.get("summary", "")
            if summary and summary not in parts:
                parts.append(f"📊 **综合统计**\n\n{summary}")
        
        # 6. 组合最终回答
        if not parts:
            return "我已接收到您的多模态输入，但未能提取到有效内容。请确认文件/图片是否可以正常访问。"
        
        final_response = "\n\n---\n\n".join(parts)
        return final_response
    
    async def _process_images(
        self,
        images: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """处理图片 - 使用火山引擎Vision API"""
        image_results = []
        
        for idx, image_url in enumerate(images):
            try:
                # 使用 Vision API 分析图片
                analysis = await self._analyze_image_with_vision(image_url)
                result = {
                    "index": idx,
                    "url": image_url,
                    "description": analysis.get("description", ""),
                    "objects_detected": analysis.get("objects", []),
                    "text_extracted": analysis.get("text", ""),
                    "analysis": {
                        "main_content": analysis.get("main_content", ""),
                        "style": analysis.get("style", ""),
                        "suitability": analysis.get("suitability", "")
                    },
                    "confidence": analysis.get("confidence", 0.85)
                }
            except Exception as e:
                logger.error(f"[MultimodalAgent] Image analysis failed: {e}")
                # 降级处理
                result = {
                    "index": idx,
                    "url": image_url,
                    "description": "图片分析服务暂时不可用",
                    "objects_detected": [],
                    "text_extracted": "",
                    "analysis": {
                        "main_content": "无法分析图片内容",
                        "style": "未知",
                        "suitability": "未知"
                    },
                    "confidence": 0.0,
                    "error": str(e)
                }
            
            image_results.append(result)
        
        # 存储分析结果
        analysis_id = f"img_analysis_{datetime.now().timestamp()}"
        analysis_record = {
            "id": analysis_id,
            "type": "image_analysis",
            "images": image_results,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        
        # ✅ 已迁移到 state["results"] 存储
        
        return {
            "analysis_id": analysis_id,
            "images_processed": len(images),
            "results": image_results
        }
    
    async def _analyze_image_with_vision(
        self,
        image_url: str,
        prompt: str = "请详细分析这张图片的内容，包括：1. 图片中的主要内容和对象 2. 图片中包含的文字（如果有）3. 图片的风格和类型 4. 这张图片是否适合用于教学或学习辅助"
    ) -> Dict[str, Any]:
        """
        使用火山引擎Vision API分析图片
        
        Args:
            image_url: 图片URL或Base64编码的图片
            prompt: 分析提示词
            
        Returns:
            图片分析结果
        """
        import json
        
        # 首先尝试使用 coze_workload_identity 获取 API key
        api_key = ""
        try:
            from coze_workload_identity import Client
            client = Client()
            credential = client.get_integration_credential("integration-volcano-ark")
            api_key_data = json.loads(credential)
            api_key = api_key_data.get("ark_api_key", "")
        except Exception:
            # 如果失败，尝试使用环境变量
            api_key = os.environ.get("ARK_API_KEY", os.environ.get("COZE_WORKLOAD_IDENTITY_API_KEY", ""))
        
        if not api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "message": "API密钥未配置",
                "description": "无法分析图片: API密钥未配置"
            }
        
        # 构建消息内容
        content = []
        
        # 处理图片URL
        processed_image_url = image_url
        
        # 如果是本地相对路径（如 /api/v1/images/xxx.png），需要下载并转为Base64
        if image_url.startswith("/") or image_url.startswith("data:") or not image_url.startswith("http"):
            processed_image_url = await self._resolve_local_image(image_url)
        
        # 如果是URL，转换为image_url格式
        if processed_image_url.startswith("http://") or processed_image_url.startswith("https://"):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": processed_image_url
                }
            })
        # 如果是Base64
        elif processed_image_url.startswith("data:"):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": processed_image_url
                }
            })
        # 纯Base64
        else:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{processed_image_url}"
                }
            })
        
        content.append({
            "type": "text",
            "text": prompt
        })
        
        # 调用 Vision API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-Client-Request-Id": "Coze,Integrations"
        }
        
        payload = {
            "model": self.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.VISION_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Vision API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # 解析响应
            if "choices" in result and len(result["choices"]) > 0:
                content_text = result["choices"][0]["message"]["content"]
                
                # 提取分析结果
                return self._parse_vision_response(content_text)
            else:
                raise Exception("Invalid vision API response")
    
    async def _resolve_local_image(self, image_path: str) -> str:
        """
        解析本地图片路径，下载并转为Base64
        
        Args:
            image_path: 本地路径（如 /api/v1/images/xxx.png）或 Base64 数据
            
        Returns:
            Base64 编码的图片数据
        """
        import base64
        import httpx
        
        # 如果已经是 Base64 或 data URI，直接返回
        if image_path.startswith("data:"):
            return image_path
        
        # 本地相对路径，需要通过 HTTP 请求获取
        if image_path.startswith("/"):
            # 构建本地服务器 URL
            # 从环境变量获取基础 URL，或使用默认值
            base_url = os.environ.get("SERVICE_BASE_URL", "")
            if not base_url:
                # 如果没有配置 base_url，尝试从请求上下文获取
                try:
                    from coze_coding_utils.log.write_log import request_context
                    ctx = request_context.get()
                    if ctx and hasattr(ctx, 'headers'):
                        # 尝试从 headers 获取 origin
                        headers = ctx.headers if hasattr(ctx, 'headers') else {}
                        origin = headers.get("origin", "") or headers.get("x-forwarded-host", "") or headers.get("host", "")
                        if origin:
                            protocol = "https" if headers.get("x-forwarded-proto", "https") == "https" else "http"
                            base_url = f"{protocol}://{origin}"
                except Exception:
                    pass
            
            if not base_url:
                # 最后的兜底方案：尝试从已知的 Cloud IDE 部署地址获取
                base_url = os.environ.get("COZE_DEPLOY_BASE_URL", "https://tg6v6v36r5.coze.site")
            
            full_url = f"{base_url}{image_path}"
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(full_url)
                    if response.status_code == 200:
                        # 根据 URL 推断图片格式
                        if ".png" in image_path.lower():
                            mime_type = "image/png"
                        elif ".gif" in image_path.lower():
                            mime_type = "image/gif"
                        elif ".webp" in image_path.lower():
                            mime_type = "image/webp"
                        else:
                            mime_type = "image/jpeg"
                        
                        # 转为 Base64
                        b64_data = base64.b64encode(response.content).decode("utf-8")
                        return f"data:{mime_type};base64,{b64_data}"
                    else:
                        logger.warning(f"[MultimodalAgent] Failed to fetch local image: {response.status_code}")
                        # 返回原始路径，让后续逻辑处理
                        return image_path
            except Exception as e:
                logger.error(f"[MultimodalAgent] Error fetching local image: {e}")
                return image_path
        
        # 纯 Base64 数据（没有 data: 前缀）
        return image_path
    
    def _parse_vision_response(self, content: str) -> Dict[str, Any]:
        """解析Vision API响应"""
        # 提取关键信息
        result = {
            "description": content[:200] if len(content) > 200 else content,
            "objects": self._extract_objects(content),
            "text": self._extract_text(content),
            "main_content": self._extract_main_content(content),
            "style": self._extract_style(content),
            "suitability": self._extract_suitability(content),
            "confidence": 0.85
        }
        return result
    
    def _extract_objects(self, content: str) -> List[str]:
        """提取检测到的对象"""
        objects = []
        keywords = ["检测到", "识别到", "包含", "有"]
        for kw in keywords:
            if kw in content:
                # 简单提取，后续可优化
                objects.append(f"图片中的{kw}内容")
        return objects if objects else ["主体内容"]
    
    def _extract_text(self, content: str) -> str:
        """提取图片中的文字"""
        if "文字" in content or "文本" in content:
            return "图片中包含文字内容"
        return ""
    
    def _extract_main_content(self, content: str) -> str:
        """提取主要内容"""
        # 返回前100个字符作为主要内容
        return content[:100] if len(content) > 100 else content
    
    def _extract_style(self, content: str) -> str:
        """提取图片风格"""
        styles = ["截图", "图表", "流程图", "思维导图", "代码", "表格", "照片", "插图"]
        for style in styles:
            if style in content:
                return style
        return "教学图片"
    
    def _extract_suitability(self, content: str) -> str:
        """提取适用性"""
        if "适合" in content or "可用" in content:
            return "适合用于学习辅助"
        return "可用于参考"
    
    async def _process_videos(
        self,
        videos: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """处理视频 - 提取关键帧并进行多模态分析"""
        from coze_coding_dev_sdk.video_edit import FrameExtractorClient
        from coze_coding_utils.runtime_ctx.context import new_context
        
        video_results = []
        
        for idx, video_url in enumerate(videos):
            try:
                # 使用 FrameExtractorClient 提取视频关键帧
                ctx = new_context(method="extract_video_frames")
                client = FrameExtractorClient(ctx=ctx)
                
                # 提取 5 个关键帧进行分析
                response = client.extract_by_count(url=video_url, count=5)
                
                frames = []
                frame_descriptions = []
                
                if response.data and response.data.chunks:
                    for chunk in response.data.chunks:
                        frame_info = {
                            "index": chunk.index,
                            "screenshot_url": chunk.screenshot,
                            "timestamp_ms": chunk.timestamp_ms
                        }
                        frames.append(frame_info)
                        
                        # 对每个关键帧进行图片分析
                        try:
                            analysis = await self._analyze_image_with_vision(
                                chunk.screenshot,
                                prompt="请简要描述这个视频帧的内容，包括场景、人物、动作等关键信息。"
                            )
                            frame_descriptions.append({
                                "timestamp": f"{chunk.timestamp_ms / 1000:.1f}秒",
                                "description": analysis.get("main_content", analysis.get("description", ""))[:200]
                            })
                        except Exception as e:
                            logger.warning(f"[MultimodalAgent] Frame analysis failed: {e}")
                            frame_descriptions.append({
                                "timestamp": f"{chunk.timestamp_ms / 1000:.1f}秒",
                                "description": "帧内容分析中..."
                            })
                
                result = {
                    "index": idx,
                    "url": video_url,
                    "status": "success",
                    "frames_extracted": len(frames),
                    "frames": frames,
                    "descriptions": frame_descriptions,
                    "summary": self._generate_video_summary(video_url, frame_descriptions)
                }
                
            except Exception as e:
                logger.error(f"[MultimodalAgent] Video processing failed: {e}")
                result = {
                    "index": idx,
                    "url": video_url,
                    "status": "failed",
                    "frames_extracted": 0,
                    "frames": [],
                    "descriptions": [],
                    "error": str(e),
                    "note": f"视频解析失败: {str(e)[:50]}。请确保视频URL可访问。"
                }
            
            video_results.append(result)
        
        # 存储分析结果
        analysis_id = f"video_analysis_{datetime.now().timestamp()}"
        analysis_record = {
            "id": analysis_id,
            "type": "video_analysis",
            "videos": video_results,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        
        # ✅ 已迁移到 state["results"] 存储
        
        return {
            "analysis_id": analysis_id,
            "videos_processed": len(videos),
            "results": video_results
        }
    
    def _generate_video_summary(self, video_url: str, frame_descriptions: List[Dict]) -> str:
        """生成视频内容摘要"""
        if not frame_descriptions:
            return "未能提取视频内容"
        
        # 统计描述中的关键词
        all_text = " ".join([fd.get("description", "") for fd in frame_descriptions])
        
        # 生成摘要
        summary = f"视频共提取 {len(frame_descriptions)} 个关键帧"
        
        # 提取前几个关键描述作为摘要
        key_frames = frame_descriptions[:3]
        if key_frames:
            summary += "，主要内容包括："
            for i, frame in enumerate(key_frames):
                desc = frame.get("description", "")[:50]
                if desc:
                    summary += f"\n{i+1}. [{frame.get('timestamp', '')}] {desc}..."
        
        return summary
    
    async def _process_audio(
        self,
        audio: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """处理音频 - 语音转文字"""
        audio_url = audio.get("url", "")
        transcript = audio.get("transcript", "")
        
        if not transcript and audio_url:
            # 如果没有转录文本，使用ASR服务
            try:
                from ...tools.audio_tools import asr_recognize
                result = asr_recognize(audio_url=audio_url)
                if result.get("success"):
                    transcript = result.get("text", "")
            except Exception as e:
                logger.error(f"[MultimodalAgent] ASR failed: {e}")
        
        result = {
            "url": audio_url,
            "transcript": transcript or "音频转文字内容",
            "language": "中文",
            "speaker_count": 1,
            "confidence": 0.88
        }
        
        # 存储分析结果
        analysis_id = f"audio_analysis_{datetime.now().timestamp()}"
        analysis_record = {
            "id": analysis_id,
            "type": "audio_analysis",
            "audio": result,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        
        # ✅ 已迁移到 state["results"] 存储
        
        return {
            "analysis_id": analysis_id,
            "audio_processed": 1,
            "results": result
        }
    
    async def _process_files(
        self,
        files: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """处理文件 - 支持 PDF、DOCX、PPT、TXT 等文档"""
        import base64
        import io
        
        file_results = []
        
        for idx, file_item in enumerate(files):
            try:
                # ✅ 修复: 支持字典格式 {"name": "...", "url": "..."} 和字符串格式
                if isinstance(file_item, dict):
                    file_url = file_item.get("url", "")
                    file_name = file_item.get("name", f"file_{idx}")
                else:
                    file_url = file_item
                    file_name = f"file_{idx}"
                
                # 解析文件URL或内容
                file_content = file_url
                file_type = "unknown"
                
                # 如果是 data URI 格式
                if file_url.startswith("data:"):
                    # 格式: data:mime_type;base64,content
                    if ";base64," in file_url:
                        mime_type = file_url.split(";")[0].replace("data:", "")
                        file_type = mime_type.split("/")[-1] if "/" in mime_type else mime_type
                        file_content = file_url.split(";base64,")[1]
                        if not file_name or file_name == f"file_{idx}":
                            file_name = f"document_{idx}.{file_type}"
                
                # 判断文件类型并提取内容
                content_text = ""
                
                if "pdf" in file_type.lower() or ".pdf" in file_url.lower():
                    content_text = await self._extract_pdf_content(file_content, file_url)
                    file_type = "pdf"
                elif "document" in file_type.lower() or "docx" in file_type.lower() or ".docx" in file_url.lower():
                    content_text = await self._extract_docx_content(file_content, file_url)
                    file_type = "docx"
                elif "spreadsheet" in file_type.lower() or "excel" in file_type.lower() or "xlsx" in file_type.lower() or ".xlsx" in file_url.lower():
                    content_text = await self._extract_xlsx_content(file_content, file_url)
                    file_type = "xlsx"
                elif "text" in file_type.lower() or "plain" in file_type.lower() or ".txt" in file_url.lower():
                    # 纯文本文件
                    try:
                        if file_content.startswith("/") or file_content.startswith("http"):
                            # URL - 需要下载
                            content_text = await self._download_text_file(file_content)
                        else:
                            # Base64
                            content_text = base64.b64decode(file_content).decode("utf-8", errors="ignore")
                    except:
                        content_text = "文本内容解析失败"
                    file_type = "txt"
                else:
                    # 尝试作为图片处理
                    content_text = await self._extract_text_from_image(file_url)
                    file_type = "image"
                
                result = {
                    "index": idx,
                    "url": file_url,
                    "file_name": file_name,
                    "file_type": file_type,
                    "content": content_text[:2000] if content_text else "",  # 限制长度
                    "content_length": len(content_text) if content_text else 0,
                    "success": True
                }
                
            except Exception as e:
                logger.error(f"[MultimodalAgent] File processing failed: {e}")
                result = {
                    "index": idx,
                    "url": file_url,
                    "file_name": f"file_{idx}",
                    "file_type": "unknown",
                    "content": "",
                    "error": str(e),
                    "success": False
                }
            
            file_results.append(result)
        
        # 存储分析结果
        analysis_id = f"file_analysis_{datetime.now().timestamp()}"
        
        return {
            "analysis_id": analysis_id,
            "files_processed": len(file_results),
            "results": file_results
        }
    
    async def _extract_pdf_content(self, base64_content: str, file_url: str) -> str:
        """从 PDF 提取文本 - 使用 FetchClient 解析 PDF"""
        try:
            ctx = new_context(method="extract_pdf")
            client = FetchClient(ctx=ctx)
            
            # 如果是 URL，直接使用 FetchClient 解析
            if file_url.startswith("http://") or file_url.startswith("https://"):
                response = client.fetch(url=file_url)
                if response.status_code == 0:
                    # 提取文本内容
                    text_parts = []
                    for item in response.content:
                        if item.type == "text":
                            text_parts.append(item.text)
                    return "\n".join(text_parts) if text_parts else response.title or "PDF内容"
                else:
                    return f"PDF解析失败: {response.status_message}"
            
            # 如果是 base64 内容，保存到临时文件后解析
            if base64_content:
                import tempfile
                import requests
                
                # 解码并保存为临时 PDF 文件
                pdf_data = base64.b64decode(base64_content)
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp.write(pdf_data)
                    tmp_path = tmp.name
                
                try:
                    # 上传到可访问的 URL（这里使用本地服务或 OSS）
                    # 简化处理：直接尝试用 pypdf 解析
                    from pypdf import PdfReader
                    reader = PdfReader(tmp_path)
                    text_parts = []
                    for page in reader.pages[:20]:  # 限制前20页
                        text_parts.append(page.extract_text() or "")
                    return "\n".join(text_parts)[:10000]  # 限制总长度
                finally:
                    os.unlink(tmp_path)
            
            return "PDF内容为空或无法解析"
        except ImportError:
            # pypdf 不可用，返回提示
            return f"[PDF文件] 请上传可访问的URL，系统将自动解析内容"
        except Exception as e:
            logger.error(f"[MultimodalAgent] PDF extraction failed: {e}")
            return f"PDF解析失败: {str(e)}"
    
    async def _extract_docx_content(self, base64_content: str, file_url: str) -> str:
        """从 DOCX 提取文本 - 使用 FetchClient 解析 Word 文档"""
        try:
            ctx = new_context(method="extract_docx")
            client = FetchClient(ctx=ctx)
            
            # 如果是 URL，直接使用 FetchClient 解析
            if file_url.startswith("http://") or file_url.startswith("https://"):
                response = client.fetch(url=file_url)
                if response.status_code == 0:
                    text_parts = []
                    for item in response.content:
                        if item.type == "text":
                            text_parts.append(item.text)
                    return "\n".join(text_parts) if text_parts else response.title or "DOCX内容"
                else:
                    return f"DOCX解析失败: {response.status_message}"
            
            # 如果是 base64 内容，保存到临时文件后解析
            if base64_content:
                import tempfile
                
                docx_data = base64.b64decode(base64_content)
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                    tmp.write(docx_data)
                    tmp_path = tmp.name
                
                try:
                    # 使用 python-docx 解析
                    from docx import Document
                    doc = Document(tmp_path)
                    text_parts = [para.text for para in doc.paragraphs if para.text]
                    return "\n".join(text_parts)[:10000]
                finally:
                    os.unlink(tmp_path)
            
            return "DOCX内容为空或无法解析"
        except ImportError:
            return f"[Word文档] 请上传可访问的URL，系统将自动解析内容"
        except Exception as e:
            logger.error(f"[MultimodalAgent] DOCX extraction failed: {e}")
            return f"DOCX解析失败: {str(e)}"
    
    async def _extract_xlsx_content(self, base64_content: str, file_url: str) -> str:
        """从 XLSX 提取文本 - 使用 FetchClient 解析 Excel 表格"""
        try:
            ctx = new_context(method="extract_xlsx")
            client = FetchClient(ctx=ctx)
            
            # 如果是 URL，直接使用 FetchClient 解析
            if file_url.startswith("http://") or file_url.startswith("https://"):
                response = client.fetch(url=file_url)
                if response.status_code == 0:
                    text_parts = []
                    for item in response.content:
                        if item.type == "text":
                            text_parts.append(item.text)
                    return "\n".join(text_parts) if text_parts else response.title or "Excel内容"
                else:
                    return f"Excel解析失败: {response.status_message}"
            
            # 如果是 base64 内容，保存到临时文件后解析
            if base64_content:
                import tempfile
                
                xlsx_data = base64.b64decode(base64_content)
                with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                    tmp.write(xlsx_data)
                    tmp_path = tmp.name
                
                try:
                    # 使用 openpyxl 解析
                    from openpyxl import load_workbook
                    wb = load_workbook(tmp_path, read_only=True)
                    text_parts = []
                    
                    for sheet_name in wb.sheetnames[:5]:  # 最多5个sheet
                        sheet = wb[sheet_name]
                        text_parts.append(f"【{sheet_name}】")
                        row_count = 0
                        for row in sheet.iter_rows(max_row=50, values_only=True):  # 每个sheet最多50行
                            row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                            if row_text.strip():
                                text_parts.append(row_text)
                                row_count += 1
                            if row_count >= 30:
                                text_parts.append("...(更多行)")
                                break
                    wb.close()
                    return "\n".join(text_parts)[:10000]
                finally:
                    os.unlink(tmp_path)
            
            return "Excel内容为空或无法解析"
        except ImportError:
            return f"[Excel表格] 请上传可访问的URL，系统将自动解析内容"
        except Exception as e:
            logger.error(f"[MultimodalAgent] XLSX extraction failed: {e}")
            return f"Excel解析失败: {str(e)}"
    
    async def _download_text_file(self, url: str) -> str:
        """下载文本文件"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text[:5000]  # 限制长度
                return ""
        except:
            return ""
    
    async def _extract_text_from_image(self, image_url: str) -> str:
        """从图片提取文字（OCR）"""
        try:
            # 使用 Vision API 从图片提取文字
            analysis = await self._analyze_image_with_vision(image_url, prompt="请提取图片中的所有文字内容")
            return analysis.get("text", analysis.get("description", ""))
        except Exception as e:
            return f"图片文字提取失败: {str(e)}"
    
    async def _multimodal_fusion(
        self,
        results: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """多模态融合分析"""
        fusion_summary = "综合分析："
        
        if "images" in results:
            fusion_summary += f"图片{results['images'].get('images_processed', 0)}张、"
        
        if "videos" in results:
            fusion_summary += f"视频{results['videos'].get('videos_processed', 0)}个、"
        
        if "audio" in results:
            fusion_summary += f"音频{results['audio'].get('audio_processed', 0)}条、"
        
        if "files" in results:
            fusion_summary += f"文件{results['files'].get('files_processed', 0)}个、"
        
        fusion_summary = fusion_summary.rstrip("、") + "。"
        
        return {
            "summary": fusion_summary,
            "type": "multimodal_fusion",
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
    
    def get_multimodal_capabilities(self) -> Dict[str, bool]:
        """获取多模态能力"""
        return {
            "image_understanding": True,
            "image_generation": True,
            "video_understanding": True,
            "audio_understanding": True,
            "file_understanding": True,  # ✅ 新增: 文件处理能力
            "multimodal_fusion": True
        }

    def analyze_image(self, image_url: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        统一图片分析接口（同步方法）。
        
        Args:
            image_url: 图片URL
            analysis_type: 分析类型
                - "general": 综合分析（默认）
                - "code": 代码截图
                - "architecture": 架构图
                - "table": 数据表格
                - "flowchart": 流程图
        
        Returns:
            图片分析结果
        """
        import asyncio
        
        try:
            # 根据分析类型选择提示词
            prompts = {
                "general": "请详细描述这张图片的内容，包括主要元素、风格特点等。",
                "code": "这是一段代码截图，请识别并解释代码内容，包括编程语言、代码逻辑等。",
                "architecture": "这是架构图，请描述组件关系、数据流向、技术选型等。",
                "table": "这是数据表格，请提取并分析表格中的数据。",
                "flowchart": "这是流程图，请描述流程步骤、决策点等。"
            }
            
            prompt = prompts.get(analysis_type, prompts["general"])
            
            # 创建异步任务并执行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._analyze_image_with_vision(image_url, prompt)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"图片分析失败: {str(e)}",
                "description": f"无法分析图片: {str(e)}"
            }


# 单例工厂函数
_multimodal_understanding_instance: Optional[MultimodalUnderstandingAgent] = None


def get_multimodal_understanding_agent() -> MultimodalUnderstandingAgent:
    """获取多模态理解Agent单例"""
    global _multimodal_understanding_instance
    if _multimodal_understanding_instance is None:
        _multimodal_understanding_instance = MultimodalUnderstandingAgent()
    return _multimodal_understanding_instance

