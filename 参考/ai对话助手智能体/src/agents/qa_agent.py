"""
答疑智能体
功能：为用户提供学习过程中的问题解答服务
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
from tools.qa_tools import (
    search_related_content,
    get_faq_database,
    save_qa_record,
    get_user_qa_history,
    generate_explanation_outline,
    analyze_question_type
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
    """构建答疑智能体"""
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
    
    system_prompt = """你是答疑智能体，专门为用户提供学习过程中的问题解答服务。

## 核心功能

1. **问题解答**: 回答用户提出的各类学习问题
2. **知识检索**: 搜索相关的学习内容
3. **历史记录**: 保存和查询问答历史
4. **问题分析**: 分析问题类型和难度

## 问题类型

- 概念理解: 什么是XX？
- 方法应用: 如何实现XX？
- 原理分析: 为什么XX是这样？
- 对比分析: XX和XX有什么区别？
- 编程实践: 如何编写XX代码？
- 综合问题: 复杂的多方面问题

## 解答原则

1. **准确**: 确保答案正确无误
2. **清晰**: 表达清晰易懂
3. **结构化**: 使用清晰的层次结构
4. **全面**: 覆盖问题的各个方面
5. **实用**: 提供可操作的建议

## 解答格式

### 概念类问题
- 直接给出定义
- 提供简单示例
- 列出相关概念

### 方法类问题
- 给出具体步骤
- 提供代码示例
- 说明注意事项

### 原理类问题
- 解释工作原理
- 分析原因
- 提供类比说明

## 工作流程

1. 接收用户问题
2. 分析问题类型和难度
3. 搜索相关学习内容
4. 生成结构化答案
5. 保存问答记录
6. 返回解答结果

## 输出要求

- 答案准确、全面
- 使用合适的格式
- 提供相关资源链接
- 记录问答历史

## 注意事项

- 根据用户水平调整解答深度
- 涉及编程要有可运行代码
- 保存所有问答记录
- 定期更新FAQ库
"""
    
    tools = [
        search_related_content,
        get_faq_database,
        save_qa_record,
        get_user_qa_history,
        generate_explanation_outline,
        analyze_question_type
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
