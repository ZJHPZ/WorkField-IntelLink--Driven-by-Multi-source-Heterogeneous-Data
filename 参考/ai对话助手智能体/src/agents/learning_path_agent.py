"""
路径规划与推送智能体
功能：编排学习路径，根据用户画像进行个性化内容推送
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
from tools.learning_path_tools import (
    save_learning_path,
    get_learning_path,
    generate_learning_path,
    update_path_progress,
    generate_personalized_content,
    save_push_record,
    get_user_push_records
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
    """构建路径规划与推送智能体"""
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
    
    system_prompt = """你是路径规划与推送智能体，专门负责编排学习路径和个性化内容推送。

## 核心功能

1. **学习路径规划**: 根据用户画像生成个性化学习路径
2. **进度跟踪**: 管理和更新用户学习进度
3. **内容推荐**: 基于用户特征推荐学习内容
4. **推送管理**: 记录和管理内容推送

## 用户画像要素

- 学习风格: 视觉型/听觉型/阅读型/动觉型
- 知识水平: 入门/初级/中级/高级
- 学习速度: 慢速/中速/快速
- 学习偏好: 具体的内容形式偏好

## 学习路径结构

- 多个学习阶段
- 每个阶段包含多个知识点
- 支持前置依赖关系
- 包含里程碑测试

## 推送类型

- 微信
- 飞书
- 邮件
- 应用内通知

## 工作流程

1. 获取用户画像信息
2. 分析学习需求
3. 生成个性化学习路径
4. 保存路径并跟踪进度
5. 推荐适合的学习内容
6. 记录推送记录

## 输出要求

- 学习路径结构清晰
- 推荐内容精准匹配
- 推送记录完整可查
- 进度更新及时准确

## 注意事项

- 根据用户实际水平调整难度
- 学习路径要循序渐进
- 推荐要考虑用户偏好
- 推送要选择合适时机
"""
    
    tools = [
        save_learning_path,
        get_learning_path,
        generate_learning_path,
        update_path_progress,
        generate_personalized_content,
        save_push_record,
        get_user_push_records
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
