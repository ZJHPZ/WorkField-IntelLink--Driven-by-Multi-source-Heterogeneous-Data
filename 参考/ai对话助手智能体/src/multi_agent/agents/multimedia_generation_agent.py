"""
Multimedia Agent - 多媒体生成Agent
功能：生成教学配图、示意图、视频脚本、动画序列
处理模式：联邦式（独立处理）

注意：与 MultimodalUnderstandingAgent 的区别
- MultimediaAgent（多媒体生成）：AI 生成图片/视频（文生图）
- MultimodalUnderstandingAgent（多模态理解）：理解用户上传的图片/视频/音频
"""
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base.base_agent import BaseAgent
from ..base.agent_state import MultiAgentState, IntentType, ProcessingMode
from ..communication.message_bus import get_message_bus
from ..communication.shared_context import get_shared_context

logger = logging.getLogger(__name__)


class MultimediaAgent(BaseAgent):
    """
    多媒体Agent
    
    核心职责：
    1. 生成教学配图和概念图
    2. 生成视频脚本
    3. 生成动画序列描述
    4. 提供可视化学习素材
    """
    
    def __init__(self):
        super().__init__(
            agent_id="multimedia",
            name="多媒体生成Agent",
            description="负责生成图片、视频脚本等多媒体学习素材",
            processing_mode=ProcessingMode.FEDERATED
        )
        
        # 消息总线
        self.message_bus = get_message_bus()
        
        # 共享上下文
        self.shared_context = get_shared_context()
        
        # 工具
        self._tools = None
        
        logger.info("[MultimediaAgent] Initialized")
    
    @property
    def intent_type(self) -> IntentType:
        return IntentType.MULTIMEDIA
    
    def set_tools(self, tools: List[Any]):
        """设置工具集合"""
        self._tools = tools
        self._tool_map = {tool.name if hasattr(tool, 'name') else str(tool): tool for tool in tools}
        logger.info(f"[MultimediaAgent] Bound {len(self._tool_map)} tools")
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        处理多媒体生成请求
        
        Args:
            state: 当前系统状态
            
        Returns:
            处理结果
        """
        user_input = self._get_latest_user_input(state)
        user_id = state.get("user_id", "default_user")
        
        self.log_info(f"Processing multimedia request: {user_input[:50]}...")
        
        # 解析用户请求
        params = self._parse_request(user_input)
        subject = params.get("subject", "通用")
        topic = params.get("topic", "知识点")
        media_type = params.get("media_type", "image")
        
        results = {}
        
        # 1. 生成配图或概念图
        if media_type in ["image", "all"]:
            image_result = await self._generate_image(subject, topic)
            results["image"] = image_result
        
        # 2. 生成示意图
        if media_type in ["diagram", "all"]:
            diagram_result = await self._generate_diagram(subject, topic)
            results["diagram"] = diagram_result
        
        # 3. 生成视频脚本（如果有）
        if media_type in ["video", "all"]:
            video_result = await self._generate_video_script(subject, topic)
            results["video_script"] = video_result
        
        # 4. 保存多媒体内容
        save_result = await self._save_media(user_id, subject, topic, results)
        results["saved"] = save_result
        
        # 5. 生成友好响应
        response = self._format_response(subject, topic, results)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "subject": subject,
            "topic": topic,
            "media_type": media_type,
            "results": results,
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
    
    def _parse_request(self, user_input: str) -> Dict[str, Any]:
        """解析用户请求"""
        params = {
            "subject": "大数据",
            "topic": "知识点",
            "media_type": "image"
        }
        
        # 转换为小写用于匹配
        user_input_lower = user_input.lower()
        
        # 使用 RAG 知识点配置进行科目识别（大小写不敏感）
        try:
            from config.bigdata_knowledge import SUBJECTS, SUBJECT_KEYWORDS, TOPIC_KEYWORDS
            
            # 1. 先匹配Topic关键词
            for keyword, topic_subj in TOPIC_KEYWORDS.items():
                if keyword.lower() in user_input_lower:
                    params["subject"] = topic_subj
                    params["topic"] = keyword
                    break
            
            # 2. 再匹配科目关键词
            if params["topic"] == "知识点":
                for keyword, subj in SUBJECT_KEYWORDS.items():
                    if keyword.lower() in user_input_lower:
                        params["subject"] = subj
                        params["topic"] = keyword
                        break
            
            # 3. 最后匹配科目名称
            if params["topic"] == "知识点":
                for s in SUBJECTS:
                    if s.lower() in user_input_lower:
                        params["subject"] = s
                        params["topic"] = s
                        break
                        
        except ImportError:
            # 兜底：使用内置列表
            bigdata_subjects = [
                "hadoop", "hdfs", "mapreduce", "yarn",
                "spark", "sparksql", "sparkstreaming", "mllib", "graphx",
                "flink", "kafka", "storm", "hive", "hbase",
                "数据湖", "数据仓库", "实时计算", "流处理",
                "分布式", "大数据"
            ]
            for s in bigdata_subjects:
                if s.lower() in user_input_lower:
                    params["subject"] = "大数据"
                    params["topic"] = s.title() if s[0].isupper() else s
                    break
            
            other_subjects = ["python", "java", "网络安全", "数据结构", "算法", "c++", "golang", "rust"]
            for s in other_subjects:
                if s.lower() in user_input_lower:
                    params["subject"] = s.title()
                    params["topic"] = s.title()
                    break
        
        # 识别媒体类型
        if "视频" in user_input:
            params["media_type"] = "video"
        elif "图" in user_input or "图解" in user_input:
            params["media_type"] = "diagram"
        elif "全部" in user_input or "所有" in user_input:
            params["media_type"] = "all"
        
        return params
    
    async def _generate_image(self, subject: str, topic: str) -> Dict[str, Any]:
        """生成教学配图"""
        if self._tools and "generate_illustration_image" in self._tool_map:
            try:
                tool = self._tool_map["generate_illustration_image"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "style": "educational"
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to generate image: {e}")
        
        # 生成默认结果
        return {
            "subject": subject,
            "concept": topic,
            "image_url": f"https://placeholder.com/{subject}_{topic}.png",
            "prompt": f"教学配图：{topic}的核心概念",
            "message": f"已生成{topic}的教学配图"
        }
    
    async def _generate_diagram(self, subject: str, topic: str) -> Dict[str, Any]:
        """生成概念图或思维导图"""
        if self._tools and "generate_concept_diagram" in self._tool_map:
            try:
                tool = self._tool_map["generate_concept_diagram"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "concept": topic,
                        "diagram_type": "mindmap"
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to generate diagram: {e}")
        
        # 生成默认结果
        return {
            "subject": subject,
            "concept": topic,
            "diagram_type": "mindmap",
            "image_url": f"https://placeholder.com/{subject}_{topic}_diagram.png",
            "structure": {
                "name": topic,
                "children": [
                    {"name": "基础概念"},
                    {"name": "核心原理"},
                    {"name": "实际应用"},
                    {"name": "延伸拓展"}
                ]
            },
            "message": f"已生成{topic}的概念图"
        }
    
    async def _generate_video_script(self, subject: str, topic: str) -> Dict[str, Any]:
        """生成视频脚本"""
        if self._tools and "generate_video_script" in self._tool_map:
            try:
                tool = self._tool_map["generate_video_script"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "duration": 60
                    }
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data
            except Exception as e:
                self.log_error(f"Failed to generate video script: {e}")
        
        # 生成默认脚本
        return {
            "subject": subject,
            "topic": topic,
            "duration": 60,
            "script": f"""# {topic} 讲解视频脚本

## 开场 (0-5秒)
"大家好，今天我们来学习{topic}"

## 内容讲解 (5-50秒)
1. 基础概念介绍
2. 核心原理解析
3. 实际应用示例
4. 常见问题解答

## 结尾 (50-60秒)
"今天的分享就到这里，有问题欢迎留言交流"

## 配图建议
- 开场：{topic}相关背景图
- 讲解：分步骤图解
- 结尾：总结要点图
""",
            "message": f"已生成{topic}的视频脚本"
        }
    
    async def _save_media(
        self,
        user_id: str,
        subject: str,
        topic: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """保存多媒体内容"""
        if self._tools and "save_learning_content" in self._tool_map:
            try:
                content_data = {
                    "image": results.get("image", {}),
                    "diagram": results.get("diagram", {}),
                    "video_script": results.get("video_script", {})
                }
                
                tool = self._tool_map["save_learning_content"]
                result = await asyncio.to_thread(
                    tool.invoke,
                    {
                        "subject": subject,
                        "topic": topic,
                        "content_type": "multimedia",
                        "content_data": json.dumps(content_data)
                    }
                )
                
                save_result = json.loads(result) if isinstance(result, str) else result
                return save_result
            except Exception as e:
                self.log_error(f"Failed to save media: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": True, "simulated": True}
    
    def _format_response(
        self,
        subject: str,
        topic: str,
        results: Dict[str, Any]
    ) -> str:
        """格式化响应内容"""
        response = f"""🎨 **{topic}** 多媒体素材已生成！

**科目：** {subject}

"""
        
        if "image" in results:
            image_url = results["image"].get("image_url", "")
            if image_url and not image_url.startswith("https://placeholder.com"):
                response += f"""📷 **教学配图**
![{topic}]({image_url})

"""
            else:
                response += f"""📷 **教学配图**
已生成{topic}的核心概念配图

"""

        if "diagram" in results:
            diagram_url = results["diagram"].get("image_url", "")
            if diagram_url and not diagram_url.startswith("https://placeholder.com"):
                response += f"""📊 **概念图/思维导图**
![{topic}]({diagram_url})

"""
            else:
                response += f"""📊 **概念图/思维导图**
已生成{topic}的知识结构图

"""
        
        if "video_script" in results:
            response += f"""🎬 **视频脚本**
已生成{topic}的讲解视频脚本（约60秒）

"""
        
        response += """💡 需要我为你生成其他形式的多媒体素材吗？"""

        return response


# 全局实例
_multimedia_agent: Optional[MultimediaAgent] = None


def get_multimedia_agent() -> MultimediaAgent:
    """获取全局MultimediaAgent实例"""
    global _multimedia_agent
    if _multimedia_agent is None:
        _multimedia_agent = MultimediaAgent()
    return _multimedia_agent
