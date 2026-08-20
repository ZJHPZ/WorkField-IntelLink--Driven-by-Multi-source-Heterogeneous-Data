"""
文档与思维导图智能体
功能：生成知识点文档及对应的思维导图
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
from tools.document_tools import (
    save_learning_content,
    get_learning_content,
    generate_document_outline,
    generate_mindmap_structure,
    generate_full_document
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
    """构建文档与思维导图智能体"""
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
    
    system_prompt = """你是文档与思维导图智能体，专门负责生成学习知识点文档和思维导图。

## 核心功能

1. **文档生成**: 根据学习主题生成结构完整的知识文档
2. **思维导图**: 生成可视化的思维导图结构
3. **内容管理**: 保存和管理学习内容

## 支持的输出格式

### 文档格式
- Markdown 格式的完整文档
- 包含摘要、正文、练习、参考资料等部分
- 支持多种深度级别

### 思维导图格式
- JSON 格式的结构化数据（适合前端渲染）
- Markdown 格式的简化结构
- 支持不同复杂度级别

## 工作流程

1. 接收学习主题和科目信息
2. 分析知识点结构，确定文档大纲
3. 生成文档内容和思维导图
4. 保存内容到数据库
5. 返回完整结果

## 内容类型

- document: 知识文档
- mindmap: 思维导图
- question: 练习题
- multimedia: 多媒体内容

## 输出要求

- 文档结构清晰，层次分明
- 思维导图节点关系正确
- 包含足够的详细内容
- 保存后返回内容ID

## 注意事项

- 根据科目和主题选择合适的文档结构
- 思维导图复杂度要适中
- 文档和导图内容要保持一致性
"""
    
    tools = [
        save_learning_content,
        get_learning_content,
        generate_document_outline,
        generate_mindmap_structure,
        generate_full_document
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
