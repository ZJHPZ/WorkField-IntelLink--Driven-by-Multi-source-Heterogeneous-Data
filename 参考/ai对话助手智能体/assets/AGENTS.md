## 项目概述
- **名称**: 数知画像增强对话工作流
- **功能**: 基于用户画像的个性化AI对话系统，通过画像数据增强AI回复的个性化程度，使用自定义智能体系统并保留其系统提示词

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| get_profile_status | `nodes/get_profile_status_node.py` | task | 获取用户画像状态 | - | - |
| should_use_profile | `nodes/should_use_profile_node.py` | condition | 判断是否使用画像 | "use_profile"→get_profile_summary, "use_fallback"→build_system_prompt | - |
| get_profile_summary | `nodes/get_profile_summary_node.py` | task | 获取用户画像摘要 | - | - |
| build_system_prompt | `nodes/build_system_prompt_node.py` | task | 构建画像上下文信息 | - | - |
| ai_chat | `nodes/ai_chat_node.py` | task | 调用自定义智能体系统对话 | - | - |
| webhook_log | `nodes/webhook_log_node.py` | task | 记录对话到后端 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 工作流流程
```
开始 → 获取画像状态 → 条件判断 → 
  ├─ use_profile分支: 获取画像摘要 → 构建画像上下文 → 拼接消息 → AI对话 → Webhook记录 → 结束
  └─ use_fallback分支: 构建空上下文 → 直接对话 → AI对话 → Webhook记录 → 结束
```

## 核心设计
**画像增强方式**：不覆盖智能体的系统提示词，而是将画像信息作为上下文拼接在用户消息前

**消息格式示例**：
```
【用户画像参考】
用户是视觉型学习者...

【沟通偏好】
- 解释风格: visual_with_examples
- 反馈风格: encouraging_specific

【用户问题】
什么是机器学习？
```

## 环境变量配置
- `BACKEND_URL`: 画像后端API地址（默认: https://your-backend-domain.com）
- `BACKEND_API_KEY`: 画像后端API密钥（可选）
- `AGENT_API_URL`: 智能体API地址（默认: https://tg6v6v36r5.coze.site/stream_run）
- `AGENT_API_TOKEN`: 智能体API Token（Bearer认证）

## 后端接口依赖
| 接口 | 方法 | URL | 用途 |
|------|------|-----|------|
| 获取画像状态 | GET | `/api/v1/profile/{user_id}/status` | 判断是否使用画像 |
| 获取画像摘要 | GET | `/api/v1/profile/{user_id}/summary` | 获取画像详情 |
| 记录对话 | POST | `/api/v1/profile/chat-log` | 异步记录对话 |
| 智能体对话 | POST | `/api/v1/chat/stream` | 调用自定义智能体（流式SSE） |

## 技能使用
- HTTP请求使用requests库
- 支持SSE流式响应处理

## 智能体配置
**Bot ID**: `7634252730730840079`

**API地址**: `https://tg6v6v36r5.coze.site/stream_run`

**请求格式**:
```json
{
  "content": {
    "query": {
      "prompt": [{"type": "text", "content": {"text": "用户消息"}}]
    }
  },
  "type": "query",
  "session_id": "会话ID",
  "project_id": "7634252730730840079"
}
```

**认证方式**: Bearer Token（通过环境变量 `AGENT_API_TOKEN` 配置）

**响应格式**: SSE流式响应（text/event-stream）
