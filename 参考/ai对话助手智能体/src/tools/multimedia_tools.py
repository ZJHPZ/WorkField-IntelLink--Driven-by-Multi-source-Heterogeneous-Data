"""
多模态智能体工具模块
功能：生成图文内容、短视频或动画讲解
"""
import json
from typing import Optional, Union, List
from langchain.tools import tool
from coze_coding_dev_sdk import ImageGenerationClient
from coze_coding_dev_sdk.video import VideoGenerationClient, TextContent, ImageURLContent, ImageURL
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.log.write_log import request_context


@tool
def generate_illustration_image(subject: str, topic: str, style: str = "educational") -> str:
    """
    生成知识点教学配图（真实图片URL）。
    
    ✅ 此工具会调用 AI 图片生成服务，生成可下载的真实图片！
    ✅ 适合生成：大数据技术架构图、系统组件图、学习知识点示意图
    
    Args:
        subject: 科目
        topic: 知识点
        style: 图像风格 (educational/realistic/cartoon/minimalist)
    
    Returns:
        JSON格式，包含生成的图片URL
    """
    ctx = request_context.get() or new_context(method="generate_illustration_image")
    
    try:
        client = ImageGenerationClient(ctx=ctx)
        
        # 构建专业的技术图表提示词
        prompt = f"""Professional technical architecture diagram or schematic illustration about {topic} for {subject} learning.

REQUIREMENTS:
- Must be a technical diagram/schematic/architecture diagram, NOT a real photo or 3D rendering
- Clean white background with clear labels and text
- Use boxes, arrows, and geometric shapes to show components and relationships
- Include proper labels and annotations in Chinese or English
- Style: Clean, professional, educational infographic
- NO laptop computers, coffee cups, or desk scenes
- NO real-world objects or photography

The diagram should clearly show the key components and their relationships for: {topic}"""
        
        response = client.generate(
            prompt=prompt,
            size="2K"
        )
        
        if response.success:
            image_url = response.image_urls[0] if response.image_urls else None
            return json.dumps({
                "success": True,
                "subject": subject,
                "topic": topic,
                "style": style,
                "image_url": image_url,
                "message": "配图生成成功"
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": response.error_messages,
                "message": "配图生成失败"
            }, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "生成过程中出错"
        }, ensure_ascii=False)


@tool
def generate_concept_diagram(subject: str, concept: str, diagram_type: str = "flowchart") -> str:
    """
    ⚠️ 重要：当用户要求生成图、架构图、流程图、关系图时，必须调用此工具！
    
    此工具会调用 AI 图片生成服务，生成可下载的真实图片URL。
    
    ✅ 当用户说以下任何词时，必须调用此工具：
       - "图"、"图片"、"图像"
       - "架构图"、"流程图"、"关系图"、"示意图"
       - "画"、"绘制"、"生成图"
       - "展示"、"可视化"
    
    ✅ 此工具会生成真实图片URL，不是 Mermaid 图表，不是文字描述！
    
    Args:
        subject: 科目（如"大数据"）
        concept: 概念名称（如"Hadoop架构"）
        diagram_type: 图表类型 (flowchart/mindmap/hierarchy/comparison)
    
    Returns:
        JSON格式，包含生成的图片URL
    """
    ctx = request_context.get() or new_context(method="generate_concept_diagram")
    
    try:
        client = ImageGenerationClient(ctx=ctx)
        
        # 构建专业的技术图表提示词
        style_prompts = {
            "flowchart": "flowchart diagram with arrows and boxes showing process flow",
            "mindmap": "mind map diagram with hierarchical branches",
            "hierarchy": "hierarchical tree diagram or organizational chart",
            "comparison": "comparison table or Venn diagram showing differences"
        }
        
        diagram_style = style_prompts.get(diagram_type, "technical diagram")
        
        prompt = f"""Professional technical {diagram_style} explaining {concept} in {subject} field.

REQUIREMENTS:
- Must be a technical diagram/schematic/architecture diagram, NOT a real photo or 3D rendering
- Clean white background with clear labels and text
- Use boxes, arrows, circles, and geometric shapes to show components and relationships
- Include proper labels and annotations in Chinese or English
- Style: Clean, professional, educational infographic
- NO laptop computers, coffee cups, desks, or real-world objects
- NO photography or 3D renderings

The diagram should clearly illustrate: {concept} with all key components and their relationships"""
        
        response = client.generate(
            prompt=prompt,
            size="2K"
        )
        
        if response.success:
            image_url = response.image_urls[0] if response.image_urls else None
            return json.dumps({
                "success": True,
                "subject": subject,
                "concept": concept,
                "diagram_type": diagram_type,
                "image_url": image_url,
                "message": "概念图生成成功"
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": response.error_messages,
                "message": "概念图生成失败"
            }, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "生成过程中出错"
        }, ensure_ascii=False)


@tool
def generate_teaching_video(subject: str, topic: str, duration: int = 5,
                             resolution: str = "720p",
                             image_url: Optional[str] = None) -> str:
    """
    生成教学短视频。
    
    Args:
        subject: 科目
        topic: 知识点
        duration: 视频时长（秒，4-12秒）
        resolution: 视频分辨率 (480p/720p/1080p)
        image_url: 起始帧图片URL（可选，用于图生视频）
    
    Returns:
        生成的视频URL
    """
    ctx = request_context.get() or new_context(method="generate_teaching_video")
    
    try:
        client = VideoGenerationClient(ctx=ctx)
        
        # 构建视频内容
        content_items = []
        
        # 添加文本描述
        text_content = f"Educational video explaining {topic} in {subject}, clear narration style, professional teaching presentation"
        content_items.append(TextContent(text=text_content))
        
        # 如果有图片，添加为起始帧
        if image_url:
            content_items.insert(0, ImageURLContent(
                image_url=ImageURL(url=image_url),
                role="first_frame"
            ))
        
        # 生成视频
        video_url, response, last_frame_url = client.video_generation(
            content_items=content_items,
            resolution=resolution,
            duration=duration,
            watermark=False
        )
        
        return json.dumps({
            "success": video_url is not None,
            "subject": subject,
            "topic": topic,
            "duration": duration,
            "resolution": resolution,
            "video_url": video_url,
            "last_frame_url": last_frame_url,
            "response": response,
            "message": "视频生成成功" if video_url else "视频生成失败"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "生成过程中出错"
        }, ensure_ascii=False)


@tool
def generate_animation_sequence(subject: str, topic: str, scenes: int = 3,
                                  duration_per_scene: int = 5) -> str:
    """
    生成动画讲解序列（多段视频连贯播放）。
    
    Args:
        subject: 科目
        topic: 知识点
        scenes: 场景数量
        duration_per_scene: 每场景时长（秒）
    
    Returns:
        生成的视频URL列表
    """
    ctx = request_context.get() or new_context(method="generate_animation_sequence")
    
    try:
        client = VideoGenerationClient(ctx=ctx)
        
        video_urls = []
        last_frame_url = None
        
        # 定义场景提示
        scene_prompts = [
            f"Animation introducing {topic} concept in {subject}, smooth transition",
            f"Animation explaining the details of {topic} in {subject}, step by step",
            f"Animation showing applications of {topic} in {subject}, practical examples"
        ]
        
        for i in range(min(scenes, len(scene_prompts))):
            content_items = [TextContent(text=scene_prompts[i])]
            
            # 使用上一段的最后一帧作为下一段的起始帧
            if last_frame_url:
                content_items.insert(0, ImageURLContent(
                    image_url=ImageURL(url=last_frame_url),
                    role="first_frame"
                ))
            
            video_url, response, last_frame_url = client.video_generation(
                content_items=content_items,
                duration=duration_per_scene,
                watermark=False,
                return_last_frame=True
            )
            
            if video_url:
                video_urls.append(video_url)
        
        return json.dumps({
            "success": len(video_urls) > 0,
            "subject": subject,
            "topic": topic,
            "scenes": len(video_urls),
            "video_urls": video_urls,
            "message": f"成功生成{len(video_urls)}段动画"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "生成过程中出错"
        }, ensure_ascii=False)


@tool
def generate_multimedia_package(subject: str, topic: str, 
                                 include_image: bool = True,
                                 include_video: bool = True) -> str:
    """
    生成完整的多媒体学习包。
    
    Args:
        subject: 科目
        topic: 知识点
        include_image: 是否包含配图
        include_video: 是否包含视频
    
    Returns:
        多媒体资源包（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_multimedia_package")
    
    result = {
        "subject": subject,
        "topic": topic,
        "resources": {},
        "message": ""
    }
    
    # 生成配图
    if include_image:
        image_result = json.loads(generate_illustration_image(subject, topic))
        result["resources"]["image"] = image_result
    
    # 生成视频
    if include_video:
        video_result = json.loads(generate_teaching_video(subject, topic))
        result["resources"]["video"] = video_result
    
    # 总结结果
    success_count = sum(1 for r in result["resources"].values() if r.get("success", False))
    result["total_resources"] = len(result["resources"])
    result["success_count"] = success_count
    result["message"] = f"生成完成，{success_count}/{len(result['resources'])} 项成功"
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def generate_image_batch(prompts: str) -> str:
    """
    批量生成图片。
    
    Args:
        prompts: 图片生成提示词列表（JSON格式字符串）
    
    Returns:
        生成的图片URL列表
    """
    ctx = request_context.get() or new_context(method="generate_image_batch")
    
    try:
        prompt_list = json.loads(prompts) if isinstance(prompts, str) else prompts
        
        client = ImageGenerationClient(ctx=ctx)
        
        image_urls = []
        
        for prompt in prompt_list:
            response = client.generate(
                prompt=prompt,
                size="2K"
            )
            
            if response.success and response.image_urls:
                image_urls.append(response.image_urls[0])
        
        return json.dumps({
            "success": len(image_urls) > 0,
            "total": len(prompt_list),
            "generated": len(image_urls),
            "image_urls": image_urls,
            "message": f"成功生成{len(image_urls)}张图片"
        }, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "批量生成过程中出错"
        }, ensure_ascii=False)


def analyze_uploaded_image(image_url: str, analysis_type: str = "general") -> str:
    """
    分析用户上传的图片内容。
    
    当用户发送图片时，必须调用此工具分析图片内容。
    
    Args:
        image_url: 图片的URL地址
        analysis_type: 分析类型，可选值：
            - "general": 综合分析（默认）
            - "code": 代码截图分析
            - "architecture": 架构图分析
            - "table": 数据表格分析
            - "flowchart": 流程图分析
    
    Returns:
        图片分析结果（JSON格式）
    """
    import json
    from multi_agent.agents.multimodal_understanding_agent import MultimodalUnderstandingAgent as MultimodalAgent
    
    try:
        agent = MultimodalAgent()
        
        result = agent.analyze_image(
            image_url=image_url,
            analysis_type=analysis_type
        )
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "图片分析过程中出错"
        }, ensure_ascii=False)


def describe_image_content(image_url: str) -> str:
    """
    描述图片内容。
    
    当需要描述图片内容时调用此工具。
    
    Args:
        image_url: 图片的URL地址
    
    Returns:
        图片内容描述（文本）
    """
    import json
    from multi_agent.agents.multimodal_understanding_agent import MultimodalUnderstandingAgent as MultimodalAgent
    
    try:
        agent = MultimodalAgent()
        result = agent.analyze_image(image_url=image_url, analysis_type="general")
        
        if result.get("success"):
            return result.get("description", "图片内容无法描述")
        else:
            return f"图片分析失败: {result.get('error', '未知错误')}"
            
    except Exception as e:
        return f"图片分析异常: {str(e)}"


@tool
def parse_document_content(file_url: str) -> str:
    """
    解析用户上传的文档内容。
    
    当用户上传文档（txt, pdf, doc, docx, xls, xlsx, ppt, pptx, csv）时调用此工具。
    
    Args:
        file_url: 文档的URL地址
    
    Returns:
        文档的文本内容
    """
    import json
    import httpx
    from io import BytesIO
    import os
    from urllib.parse import urlparse
    
    try:
        ctx = request_context.get() or new_context(method="parse_document_content")
        
        # 下载文件
        response = httpx.get(file_url, timeout=30)
        response.raise_for_status()
        content_bytes = response.content
        
        # 获取文件扩展名
        path = urlparse(file_url).path
        ext = os.path.splitext(path)[1].lower()
        
        stream = BytesIO(content_bytes)
        text_result = ""
        
        # 解析不同格式
        if ext == '.txt':
            try:
                text_result = content_bytes.decode('utf-8')
            except:
                text_result = content_bytes.decode('gbk', errors='ignore')
        
        elif ext == '.pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(stream)
                for page in reader.pages:
                    text_result += page.extract_text() + "\n"
            except ImportError:
                return "[解析失败] 缺少 pypdf 库"
            except Exception as e:
                return f"[解析失败] {str(e)}"
        
        elif ext in ['.docx', '.doc']:
            try:
                from utils.file.file import read_docx
                text_result = read_docx(stream)
            except Exception as e:
                return f"[解析失败] {str(e)}"
        
        elif ext in ['.xlsx', '.xls', '.csv']:
            try:
                import pandas as pd
                if ext == '.csv':
                    df = pd.read_csv(stream)
                else:
                    df = pd.read_excel(stream)
                text_result = df.to_string()
            except ImportError:
                return "[解析失败] 缺少 pandas 库"
            except Exception as e:
                return f"[解析失败] {str(e)}"
        
        elif ext in ['.ppt', '.pptx']:
            try:
                from utils.file.file import read_ppt
                text_result = read_ppt(stream)
            except Exception as e:
                return f"[解析失败] {str(e)}"
        
        else:
            return f"[暂不支持解析该文档格式: {ext}]"
        
        if not text_result:
            return "[文档内容为空]"
        
        return text_result[:10000]  # 限制返回长度
        
    except Exception as e:
        return f"文档解析异常: {str(e)}"
