"""
多模态智能体
功能：生成图文内容、短视频或动画讲解
"""
import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers, new_context
from storage.memory.memory_saver import get_memory_saver
from tools.multimedia_tools import (
    generate_illustration_image,
    generate_concept_diagram,
    generate_teaching_video,
    generate_animation_sequence,
    generate_multimedia_package,
    generate_image_batch
)

LLM_CONFIG = "config/agent_llm_config.json"

MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    combined = add_messages(old, new)
    result = list(combined)[-MAX_MESSAGES:] if len(combined) > MAX_MESSAGES else list(combined)
    return result

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    """构建多模态智能体"""
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    system_prompt = """你是多模态智能体，专门负责生成图文内容、短视频和动画讲解。

## 核心功能

1. **图片生成**: 生成教学配图、概念图、流程图等
2. **视频生成**: 生成教学短视频和动画讲解
3. **多媒体包**: 生成完整的多媒体学习资源包

## 支持的内容类型

### 静态图片
- 教学配图
- 概念关系图
- 流程图
- 思维导图
- 比较图表

### 视频内容
- 教学短视频（5-12秒）
- 动画讲解序列
- 图生视频

## 图像风格

- educational: 教育风格
- realistic: 写实风格
- cartoon: 卡通风格
- minimalist: 简约风格

## 视频参数

- 分辨率: 480p, 720p, 1080p
- 时长: 4-12秒
- 支持图生视频和文生视频

## 工作流程

1. 接收学习内容需求
2. 分析内容特点选择合适的多媒体形式
3. 生成高质量的多媒体资源
4. 可选择生成多媒体资源包
5. 返回资源链接

## 输出要求

- 图片清晰、适合教学
- 视频流畅、内容连贯
- 支持批量生成
- 可生成完整资源包

## 注意事项

- 图片生成可能需要等待
- 视频生成时间较长，请耐心等待
- 批量操作有并发限制
- 资源包可以一次性获取多种资源
"""
    
    tools = [
        generate_illustration_image,
        generate_concept_diagram,
        generate_teaching_video,
        generate_animation_sequence,
        generate_multimedia_package,
        generate_image_batch
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
