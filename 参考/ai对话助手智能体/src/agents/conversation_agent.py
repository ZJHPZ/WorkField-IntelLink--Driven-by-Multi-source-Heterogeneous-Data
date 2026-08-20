"""
对话采集与特征抽取智能体
功能：采集用户对话内容，抽取6维特征，支持动态更新
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
from tools.conversation_tools import (
    save_conversation,
    get_user_conversations,
    get_user_profile,
    update_user_feature,
    update_user_profile_full,
    extract_features_from_conversation
)

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    combined = add_messages(old, new)
    result = list(combined)[-MAX_MESSAGES:] if len(combined) > MAX_MESSAGES else list(combined)
    return result

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    """构建对话采集与特征抽取智能体"""
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
    
    # 定义6维特征的描述
    feature_descriptions = """
    用户6维特征定义：
    1. learning_style (学习风格): 视觉型/听觉型/阅读型/动觉型
    2. knowledge_level (知识水平): 入门/初级/中级/高级
    3. learning_goal (学习目标): 用户的学习目标描述
    4. learning_speed (学习速度): 慢速/中速/快速
    5. learning_preference (学习偏好): 详细的偏好配置（JSON格式）
    6. learning_progress (学习进度): 学习进度记录（JSON格式）
    """
    
    system_prompt = f"""你是对话采集与特征抽取智能体，专门负责采集用户对话并从中抽取用户的学习特征。

## 核心功能

1. **对话采集**: 记录用户的每一条对话内容，包括用户消息和助手回复
2. **特征抽取**: 从对话中分析并抽取用户的6维学习特征
3. **动态更新**: 支持实时更新用户画像

## 6维特征定义

{feature_descriptions}

## 工作流程

1. 当用户发起对话时，先保存对话记录
2. 分析对话内容，识别用户的学习特征
3. 根据分析结果更新用户画像
4. 定期回顾历史对话，优化特征预测

## 输出要求

- 对话保存要包含完整内容和元数据
- 特征更新需要明确说明更新的字段和值
- 提供分析建议时要具体、可操作

## 注意事项

- 使用工具时确保传入正确的用户ID
- 更新特征时验证数据格式是否正确
- 保持对话历史的连续性
"""
    
    tools = [
        save_conversation,
        get_user_conversations,
        get_user_profile,
        update_user_feature,
        update_user_profile_full,
        extract_features_from_conversation
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
