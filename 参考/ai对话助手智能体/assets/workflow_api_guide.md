# 画像增强对话工作流API调用说明

## 一、概述

### 1.1 工作流定位
本工作流是**画像增强对话系统**的预处理层，在用户请求到达智能体之前，通过查询用户画像数据，为智能体提供个性化上下文信息。

### 1.2 核心功能
- ✅ **画像状态查询**：判断用户画像是否可用
- ✅ **画像数据获取**：获取用户学习风格、知识水平等画像信息
- ✅ **智能分支决策**：根据画像状态自动选择个性化策略或降级策略
- ✅ **上下文拼接**：将画像信息拼接到用户消息中
- ✅ **对话记录**：异步记录对话到后端系统

### 1.3 架构关系
```
用户请求 → 工作流系统（画像增强） → 智能体系统（对话生成） → 返回结果
           ├─ 画像状态查询
           ├─ 画像数据获取
           ├─ 上下文拼接
           └─ 对话记录
```

---

## 二、API接口定义

### 2.1 基础信息
| 项目 | 值 |
|------|-----|
| 服务地址 | `http://localhost:9000` |
| 流式接口 | `/stream_run` |
| 非流式接口 | `/run` |
| 请求方式 | POST |
| 数据格式 | JSON |
| 响应格式 | SSE流式 / JSON |

### 2.2 接口选择建议
| 接口 | 适用场景 | 特点 |
|------|---------|------|
| `/stream_run` | 实时对话、聊天场景 | 流式输出，用户体验好 |
| `/run` | 批量处理、测试场景 | 一次性返回，便于调试 |

---

## 三、请求格式

### 3.1 流式接口请求

**接口地址：** `POST http://localhost:9000/stream_run`

**请求头：**
```json
{
  "Content-Type": "application/json"
}
```

**请求体：**
```json
{
  "user_id": "user_123",
  "session_id": "session_001",
  "user_message": "什么是Hadoop？"
}
```

**字段说明：**

| 字段名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `user_id` | string | ✅ | 用户唯一标识符 | `"user_123"` |
| `session_id` | string | ✅ | 会话唯一标识符（用于维持上下文） | `"session_001"` |
| `user_message` | string | ✅ | 用户输入的消息内容 | `"什么是Hadoop？"` |

### 3.2 curl示例

```bash
curl -X POST http://localhost:9000/stream_run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "session_id": "session_001",
    "user_message": "什么是Hadoop？"
  }'
```

---

## 四、响应格式

### 4.1 流式响应（SSE格式）

工作流会以Server-Sent Events（SSE）格式返回流式数据：

```
event: message
data: {"type": "answer", "content": {"answer": "你好呀"}, "node_name": "ai_chat_node"}

event: message
data: {"type": "answer", "content": {"answer": "！很高兴"}, "node_name": "ai_chat_node"}

event: message
data: {"type": "answer", "content": {"answer": "再次见到你"}, "node_name": "ai_chat_node"}
```

### 4.2 响应数据结构

**单个chunk结构：**
```json
{
  "type": "answer",
  "content": {
    "answer": "文本片段"
  },
  "node_name": "ai_chat_node"
}
```

**完整响应拼接：**
```python
# JavaScript示例
let fullResponse = "";
for (const chunk of stream) {
  if (chunk.type === "answer") {
    fullResponse += chunk.content.answer;
  }
}
console.log(fullResponse);
```

### 4.3 非流式响应（JSON格式）

**接口地址：** `POST http://localhost:9000/run`

**响应示例：**
```json
{
  "ai_response": "你好呀！很高兴再次见到你😊 既然你已经了解了我的核心服务方向，现在可以告诉我：\n1. 🎯 你想学习哪个具体的大数据技术？\n..."
}
```

---

## 五、工作流处理流程

### 5.1 完整处理流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户请求：什么是Hadoop？                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                  ┌──────────────────────┐
                  │  获取画像状态节点      │
                  │  GET /api/v1/profile │
                  │  /{user_id}/status   │
                  └──────────┬───────────┘
                             │
                             ↓
                  ┌──────────────────────┐
                  │  条件判断节点         │
                  │  is_ready?           │
                  └──────────┬───────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ↓                 ↓
         ┌──────────────┐    ┌──────────────┐
         │ use_profile  │    │use_fallback  │
         │  分支        │    │   分支       │
         └──────┬───────┘    └──────┬───────┘
                │                   │
                ↓                   │
    ┌─────────────────────┐         │
    │ 获取画像摘要节点     │         │
    │ GET /api/v1/profile │         │
    │ /{user_id}/summary  │         │
    └──────┬──────────────┘         │
           │                        │
           ↓                        ↓
    ┌─────────────────────┐  ┌─────────────────────┐
    │ 构建系统提示词节点   │  │ 构建系统提示词节点   │
    │ 6维画像+扩展字段    │  │ 默认提示词         │
    └──────┬──────────────┘  └──────┬──────────────┘
           │                        │
           └────────┬───────────────┘
                    ↓
          ┌──────────────────────┐
          │   AI对话节点          │
          │   调用智能体API       │
          │   https://tg6v6v36r5 │
          │   .coze.site/stream  │
          │   _run               │
          └──────┬───────────────┘
                 │
                 ↓
          ┌──────────────────────┐
          │  Webhook记录节点      │
          │  POST /api/v1/profile│
          │  /chat-log           │
          └──────────┬───────────┘
                     │
                     ↓
          ┌──────────────────────┐
          │   返回AI回复          │
          └──────────────────────┘
```

### 5.2 画像增强示例

**原始用户消息：**
```
什么是Hadoop？
```

**画像增强后的消息：**
```
【用户画像参考】
用户是视觉型学习者，偏好图表、具体实例
知识水平：中级学习者
兴趣领域：Python, 大数据

【沟通偏好】
- 解释风格: 配合图表和具体实例
- 反馈风格: 鼓励且具体

【用户优势】
- 编程基础扎实

【需要加强】
- 分布式系统理解

【需要避免】
- 过度批评
- 纯理论讲解无实例

【用户问题】
什么是Hadoop？
```

---

## 六、环境配置

### 6.1 必需配置

**后端接口配置：**
```bash
# 后端API基础地址
export BACKEND_URL="https://your-backend-domain.com"

# 后端API密钥（可选）
export BACKEND_API_KEY="your_api_key_here"
```

### 6.2 智能体配置（已内置）

**智能体API配置：**
```python
# 智能体API地址（已硬编码，可环境变量覆盖）
AGENT_API_URL = "https://tg6v6v36r5.coze.site/stream_run"

# 智能体API Token（已硬编码）
AGENT_API_TOKEN = "eyJhbGciOiJSUzI1NiIs..."
```

**通过环境变量修改：**
```bash
export AGENT_API_URL="https://your-agent.coze.site/stream_run"
export AGENT_API_TOKEN="your_token_here"
```

### 6.3 配置验证

启动服务后，访问：`http://localhost:9000/health`

---

## 七、后端接口要求

### 7.1 画像状态查询接口

**接口定义：**
```
GET /api/v1/profile/{user_id}/status
```

**请求头：**
```json
{
  "Authorization": "Bearer {BACKEND_API_KEY}"
}
```

**响应格式：**
```json
{
  "user_id": "user_123",
  "is_ready": true,
  "fallback_used": false,
  "profile_exists": true,
  "message": "画像数据已就绪"
}
```

**字段说明：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `user_id` | string | 用户ID |
| `is_ready` | boolean | 画像是否可用 |
| `fallback_used` | boolean | 是否使用降级策略 |
| `profile_exists` | boolean | 画像是否已创建 |
| `message` | string | 状态描述信息 |

### 7.2 画像摘要获取接口

**接口定义：**
```
GET /api/v1/profile/{user_id}/summary
```

**响应格式：**
```json
{
  "user_id": "user_123",
  "profile_id": 1,
  "created_at": "2025-05-25T10:00:00Z",
  "updated_at": "2025-05-25T18:00:00Z",
  "learning_style": "visual",
  "knowledge_level": "intermediate",
  "interests": ["Python", "大数据"],
  "communication_preferences": {
    "explanation_style": "visual_with_examples",
    "feedback_style": "encouraging_specific"
  },
  "strengths": ["编程基础"],
  "weaknesses": ["分布式系统"],
  "avoid_patterns": ["过度批评"],
  "explanation_style": "visual_with_examples",
  "feedback_style": "encouraging_specific"
}
```

**画像字段说明：**

| 字段名 | 类型 | 说明 | 可选值 |
|--------|------|------|--------|
| `learning_style` | string | 学习风格 | visual/auditory/reading/mixed |
| `knowledge_level` | string | 知识水平 | beginner/intermediate/advanced/unknown |
| `interests` | array | 兴趣领域 | ["Python", "大数据", ...] |
| `communication_preferences` | object | 沟通偏好 | 见下表 |
| `strengths` | array | 用户优势 | ["编程基础", ...] |
| `weaknesses` | array | 需要加强 | ["分布式系统", ...] |
| `avoid_patterns` | array | 需要避免 | ["过度批评", ...] |

**沟通偏好字段：**

| 字段名 | 可选值 | 说明 |
|--------|--------|------|
| `explanation_style` | simple/visual_with_examples/detailed | 解释风格 |
| `feedback_style` | neutral/encouraging_specific/constructive | 反馈风格 |

### 7.3 对话记录接口

**接口定义：**
```
POST /api/v1/profile/chat-log
```

**请求格式：**
```json
{
  "user_id": "user_123",
  "session_id": "session_001",
  "user_message": "什么是Hadoop？",
  "ai_response": "你好呀！很高兴再次见到你...",
  "profile_id": 1,
  "metadata": {
    "timestamp": "2025-05-25T19:30:00Z",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100"
  }
}
```

---

## 八、错误处理

### 8.1 错误码定义

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| `400` | 请求参数错误 | 检查user_id、session_id、user_message是否完整 |
| `401` | 未授权 | 检查BACKEND_API_KEY是否正确 |
| `404` | 画像不存在 | 工作流自动使用降级策略 |
| `500` | 服务器内部错误 | 检查日志，联系管理员 |
| `503` | 后端服务不可用 | 工作流自动使用降级策略 |

### 8.2 降级策略

**自动降级机制：**
```
画像查询失败 → 自动切换use_fallback分支 → 使用默认提示词 → 调用智能体 → 返回结果
```

**降级提示词示例：**
```
【用户问题】
什么是Hadoop？
```

**特点：**
- ✅ 无画像数据，智能体使用自己的系统提示词
- ✅ 用户仍可正常对话，体验流畅
- ✅ 后台记录fallback_used标记

---

## 九、使用示例

### 9.1 Python调用示例

```python
import requests
import json

# 流式调用
url = "http://localhost:9000/stream_run"
payload = {
    "user_id": "user_123",
    "session_id": "session_001",
    "user_message": "什么是Hadoop？"
}

response = requests.post(url, json=payload, stream=True)
full_answer = ""

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]
            data = json.loads(data_str)
            if data.get("type") == "answer":
                answer_chunk = data.get("content", {}).get("answer", "")
                full_answer += answer_chunk
                print(answer_chunk, end='', flush=True)

print("\n完整回复：", full_answer)
```

### 9.2 JavaScript调用示例

```javascript
const url = 'http://localhost:9000/stream_run';
const payload = {
  user_id: 'user_123',
  session_id: 'session_001',
  user_message: '什么是Hadoop？'
};

const response = await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

const reader = response.body.getReader();
let fullAnswer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = new TextDecoder().decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.type === 'answer') {
        fullAnswer += data.content.answer;
        console.log(data.content.answer);
      }
    }
  }
}

console.log('完整回复：', fullAnswer);
```

### 9.3 curl测试示例

```bash
# 测试流式接口
curl -X POST http://localhost:9000/stream_run \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_001","session_id":"s1","user_message":"你好"}'

# 测试非流式接口
curl -X POST http://localhost:9000/run \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_001","session_id":"s1","user_message":"你好"}'
```

---

## 十、性能说明

### 10.1 性能影响评估

| 阶段 | 耗时（缓存命中） | 耗时（缓存未命中） |
|------|-----------------|-------------------|
| 画像状态查询 | ~50ms | ~150ms |
| 画像摘要查询 | ~50ms | ~200ms |
| 消息拼接 | ~10ms | ~10ms |
| 智能体处理 | ~6秒 | ~6秒 |
| 对话记录（异步） | ~0ms | ~0ms |
| **总耗时** | **~6.11秒** | **~6.36秒** |

**结论：** 工作流增加的额外延迟<200ms，占比<3%，几乎不影响用户体验。

### 10.2 优化建议

**1. 画像缓存机制：**
```python
import redis

# 画像缓存，5分钟过期
redis_client.setex(f"profile:{user_id}", 300, json.dumps(profile))
```

**2. 异步查询画像：**
```python
import asyncio

# 并行查询画像
async def parallel_query():
    status_task = asyncio.create_task(get_status(user_id))
    summary_task = asyncio.create_task(get_summary(user_id))
    return await asyncio.gather(status_task, summary_task)
```

---

## 十一、监控与日志

### 11.1 日志位置
```
/app/work/logs/bypass/app.log
```

### 11.2 关键日志字段
```json
{
  "timestamp": "2025-05-25T19:30:00Z",
  "run_id": "uuid-xxx",
  "user_id": "user_123",
  "session_id": "session_001",
  "node_name": "get_profile_status_node",
  "event": "画像状态查询成功",
  "is_ready": true,
  "fallback_used": false
}
```

### 11.3 监控指标建议
- 画像查询成功率
- 降级策略使用频率
- 平均响应延迟
- 智能体调用成功率

---

## 十二、常见问题

### Q1：如何测试工作流是否正常？
**A：** 使用curl或test_run工具测试：
```bash
curl -X POST http://localhost:9000/run \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","session_id":"s1","user_message":"你好"}'
```

### Q2：画像查询失败会影响用户对话吗？
**A：** 不会。工作流自动使用降级策略，用户仍可正常对话。

### Q3：如何查看工作流处理日志？
**A：** 查看日志文件：
```bash
tail -f /app/work/logs/bypass/app.log
```

### Q4：如何调整智能体API地址？
**A：** 设置环境变量：
```bash
export AGENT_API_URL="https://new-agent.coze.site/stream_run"
```

### Q5：如何添加新的画像维度？
**A：** 修改`state.py`中的`ProfileSummary`类，并更新`build_system_prompt_node.py`的拼接逻辑。

---

## 十三、版本与更新

| 版本 | 更新时间 | 更新内容 |
|------|---------|---------|
| v1.0 | 2025-05-25 | 初始版本，支持画像增强对话 |
| v1.1 | 2025-05-25 | 适配完整画像格式（6维+扩展字段） |

---

## 十四、联系与支持

如有问题或建议，请：
1. 查看日志文件定位问题
2. 检查环境变量配置
3. 测试后端接口连通性
4. 联系项目负责人

---

**文档更新时间：** 2025-05-25  
**文档版本：** v1.1