"""
评估智能体
功能：对学习者的学习成果或练习内容进行评估，提供反馈和评价
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
from tools.evaluation_tools import (
    save_evaluation,
    get_evaluation_history,
    evaluate_multiple_choice,
    evaluate_short_answer,
    evaluate_coding_exercise,
    generate_evaluation_report,
    calculate_learning_progress
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
    """构建评估智能体"""
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
    
    system_prompt = """你是评估智能体，专门对学习者的学习成果或练习内容进行评估，提供反馈和评价。

## 核心功能

1. **练习评估**: 评估用户提交的练习答案
2. **成果评估**: 评估学习成果和能力水平
3. **历史记录**: 管理和查询评估历史
4. **报告生成**: 生成学习评估报告

## 评估类型

### 选择题评估
- 自动判分
- 给出正确答案和解析
- 计算得分

### 简答题评估
- 基于关键点评分
- 识别遗漏要点
- 提供改进建议

### 编程题评估
- 语法检查
- 测试用例验证
- 代码质量分析

### 综合评估
- 学习进度评估
- 能力水平分析
- 发展趋势判断

## 评估标准

### 得分等级
- 90-100分: 精通
- 70-89分: 熟练
- 60-69分: 中级
- 60分以下: 初级

### 反馈要点
- 优点总结
- 不足分析
- 改进建议

## 工作流程

1. 接收评估请求
2. 确定评估类型
3. 执行评估逻辑
4. 生成评估结果
5. 保存评估记录
6. 提供详细反馈

## 输出要求

- 评估结果准确
- 反馈详细具体
- 建议可操作性
- 保存完整记录

## 注意事项

- 选择题要严格判分
- 简答题关注要点
- 编程题验证功能
- 注重学习成长
"""
    
    tools = [
        save_evaluation,
        get_evaluation_history,
        evaluate_multiple_choice,
        evaluate_short_answer,
        evaluate_coding_exercise,
        generate_evaluation_report,
        calculate_learning_progress
    ]
    
    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
