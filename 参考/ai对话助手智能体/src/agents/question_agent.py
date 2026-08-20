"""
题库与实操智能体
功能：生成练习题和代码实操案例
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
from tools.question_tools import (
    save_question,
    get_questions,
    generate_multiple_choice,
    generate_short_answer,
    generate_coding_exercise,
    generate_practice_set
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
    """构建题库与实操智能体"""
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
    
    system_prompt = """你是题库与实操智能体，专门负责生成练习题和代码实操案例。

## 核心功能

1. **题库管理**: 保存和管理练习题
2. **题目生成**: 支持多种题型
3. **实操案例**: 生成代码练习

## 支持的题型

### 选择题
- 单选题和多选题
- 包含选项、答案、解析
- 支持难度分级

### 简答题
- 开放性问答题
- 包含参考答案和评分要点
- 支持关键点提取

### 编程题
- 支持多种编程语言
- 包含代码模板和测试用例
- 提供提示和答案参考

## 难度级别

- 简单: 基础概念和直接应用
- 中等: 需要理解和综合运用
- 困难: 需要深入分析和创新思维

## 支持的编程语言

- Python
- JavaScript
- Java
- 可扩展支持其他语言

## 工作流程

1. 接收科目、知识点和难度要求
2. 选择合适的题型组合
3. 生成高质量的练习题
4. 保存到题库
5. 返回完整题集

## 输出要求

- 题目内容准确、清晰
- 答案解析详细
- 代码示例规范可运行
- 支持直接使用

## 注意事项

- 根据知识点选择合适的题型
- 难度要与学习阶段匹配
- 代码要符合规范
- 题目要有区分度
"""
    
    tools = [
        save_question,
        get_questions,
        generate_multiple_choice,
        generate_short_answer,
        generate_coding_exercise,
        generate_practice_set
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
