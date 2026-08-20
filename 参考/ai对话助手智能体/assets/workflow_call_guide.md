# 工作流调用说明（简化版）

## 一、快速开始

### 1.1 接口地址
```
流式接口：POST http://localhost:9000/stream_run
非流式接口：POST http://localhost:9000/run
```

### 1.2 请求示例（curl）

**流式调用：**
```bash
curl -X POST http://localhost:9000/stream_run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好",
    "session_id": "session_001",
    "user_profile": {
      "user_id": "user_001",
      "learning_style": "visual",
      "knowledge_level": "intermediate"
    }
  }'
```

**非流式调用：**
```bash
curl -X POST http://localhost:9000/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好",
    "session_id": "session_001",
    "user_profile": {
      "user_id": "user_001",
      "learning_style": "visual",
      "knowledge_level": "intermediate"
    }
  }'
```

---

## 二、请求格式

### 2.1 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `query` | string | ✅ | 用户消息（已包含画像上下文） |
| `session_id` | string | ✅ | 会话ID（用于维持对话上下文） |
| `user_profile` | object | ❌ | 用户画像数据（可选） |

### 2.2 user_profile字段说明

| 字段名 | 类型 | 必填 | 说明 | 可选值 |
|--------|------|------|------|--------|
| `user_id` | string | ✅ | 用户唯一标识 | - |
| `learning_style` | string | ❌ | 学习风格 | `visual`, `auditory`, `kinesthetic`, `mixed` |
| `knowledge_level` | string | ❌ | 知识水平 | `beginner`, `intermediate`, `advanced` |
| `interests` | array | ❌ | 兴趣领域 | `["Python", "大数据"]` |
| `communication_preferences` | object | ❌ | 沟通偏好 | 见下方 |

### 2.3 communication_preferences字段

```json
{
  "explanation_style": "visual_with_examples",
  "feedback_style": "encouraging_specific"
}
```

**可选值：**
- `explanation_style`: `visual_with_examples`, `conceptual_theoretical`, `practical_step_by_step`
- `feedback_style`: `encouraging_specific`, `direct_concise`, `socratic_questioning`

---

## 三、响应格式

### 3.1 流式响应（SSE格式）

```
id: node_1_0
event: message
data: {"type": "ai_response", "content": {"text": "你好呀！"}}

id: node_1_1
event: message
data: {"type": "ai_response", "content": {"text": "看来我们的学习之旅要正式启航啦🚀"}}

...

id: end
event: message
data: {"type": "end", "run_id": "340beccb-6c5a-46ad-837f-de9de435e144"}
```

### 3.2 非流式响应（JSON格式）

```json
{
  "ai_response": "你好呀！看来我们的学习之旅要正式启航啦🚀 为了给你提供更精准的帮助...",
  "run_id": "340beccb-6c5a-46ad-837f-de9de435e144"
}
```

---

## 四、代码调用示例

### 4.1 Python示例（流式）

```python
import requests
import json

url = "http://localhost:9000/stream_run"

payload = {
    "query": "你好",
    "session_id": "session_001",
    "user_profile": {
        "user_id": "user_001",
        "learning_style": "visual",
        "knowledge_level": "intermediate"
    }
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers, stream=True)

full_response = ""
for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]
            try:
                data = json.loads(data_str)
                if data.get("type") == "ai_response":
                    text = data.get("content", {}).get("text", "")
                    full_response += text
                    print(text)  # 实时打印
            except:
                pass

print(f"\n完整回复: {full_response}")
```

### 4.2 Python示例（非流式）

```python
import requests

url = "http://localhost:9000/run"

payload = {
    "query": "你好",
    "session_id": "session_001",
    "user_profile": {
        "user_id": "user_001",
        "learning_style": "visual"
    }
}

response = requests.post(url, json=payload)
result = response.json()

print(f"AI回复: {result['ai_response']}")
print(f"Run ID: {result['run_id']}")
```

### 4.3 JavaScript示例（流式）

```javascript
const url = 'http://localhost:9000/stream_run';

const payload = {
    query: "你好",
    session_id: "session_001",
    user_profile: {
        user_id: "user_001",
        learning_style: "visual",
        knowledge_level: "intermediate"
    }
};

fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
})
.then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    function read() {
        return reader.read().then(({done, value}) => {
            if (done) return;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            lines.forEach(line => {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    if (data.type === 'ai_response') {
                        console.log(data.content.text);
                    }
                }
            });
            
            return read();
        });
    }
    
    return read();
});
```

---

## 五、架构说明

### 5.1 工作流处理流程

```
用户请求 → 中间件（画像增强）
              ├─ 获取画像（user_profile或SharedContext）
              └─ 增强消息（拼接画像上下文）
           → 工作流
              ├─ ai_chat_node（调用Coze智能体）
              └─ webhook_log_node（记录对话）
           → 返回结果
```

### 5.2 节点说明

| 节点 | 功能 | 处理时间 |
|------|------|---------|
| `ai_chat_node` | 调用Coze智能体API生成回复 | ~6秒 |
| `webhook_log_node` | 记录对话到后端Webhook | ~200ms（异步） |

---

## 六、错误处理

### 6.1 错误响应格式

```json
{
  "error_code": "AGENT_API_ERROR",
  "error_message": "智能体API调用失败: Connection refused",
  "stack_trace": "..."
}
```

### 6.2 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| `INVALID_JSON` | JSON格式错误 | 检查请求体JSON格式 |
| `MISSING_REQUIRED_FIELD` | 缺少必填字段 | 检查query和session_id |
| `AGENT_API_ERROR` | 智能体API调用失败 | 检查API地址和Token |
| `WEBHOOK_ERROR` | Webhook调用失败 | 检查BACKEND_URL配置 |

---

## 七、环境配置

### 7.1 必需配置

```bash
# 智能体API配置
export AGENT_API_URL="https://tg6v6v36r5.coze.site/stream_run"
export AGENT_API_TOKEN="eyJhbGciOi..."
export AGENT_PROJECT_ID="7634252730730840079"
```

### 7.2 可选配置

```bash
# 后端Webhook配置（可选）
export BACKEND_URL="https://your-backend.com"
export BACKEND_API_KEY="your_api_key"
```

### 7.3 启动服务

```bash
# 开发环境
python src/main.py

# 生产环境
uvicorn src.main:app --host 0.0.0.0 --port 9000
```

---

## 八、性能优化建议

### 8.1 画像缓存

建议在中间件层缓存用户画像：

```python
import redis

# 缓存用户画像（5分钟过期）
redis_client.setex(f"profile:{user_id}", 300, json.dumps(profile))
```

### 8.2 异步处理

Webhook记录异步处理，不阻塞主流程：

```python
# webhook_log_node 异步调用
asyncio.create_task(webhook_callback(...))
```

### 8.3 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 画像查询 | <100ms | 缓存命中 |
| 智能体处理 | ~6秒 | 取决于智能体复杂度 |
| Webhook记录 | 异步 | 不阻塞主流程 |
| **总延迟** | <6.5秒 | 包含所有处理 |

---

## 九、监控与日志

### 9.1 日志位置
```
/app/work/logs/bypass/app.log
```

### 9.2 关键日志字段

```json
{
  "run_id": "340beccb-6c5a-46ad-837f-de9de435e144",
  "session_id": "session_001",
  "user_id": "user_001",
  "node": "ai_chat_node",
  "duration_ms": 6420,
  "status": "success"
}
```

### 9.3 监控指标

- 成功率：>99%
- 平均延迟：<7秒
- P99延迟：<10秒
- Webhook成功率：>95%

---

## 十、常见问题

### Q1: 画像数据如何获取？
**答:** 画像数据在中间件层获取，可从请求中的`user_profile`字段或从SharedContext查询。

### Q2: 如何维持对话上下文？
**答:** 使用`session_id`字段，智能体系统会自动维护对话历史。

### Q3: Webhook失败会影响对话吗？
**答:** 不会，Webhook异步处理，失败不影响用户对话体验。

### Q4: 如何调试工作流？
**答:** 查看日志文件 `/app/work/logs/bypass/app.log`，搜索run_id定位问题。

### Q5: 如何取消正在执行的请求？
**答:** 使用Header `x-run-id` 指定run_id，然后调用取消接口。

---

## 十一、版本信息

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0 | 2026-06-04 | 简化架构，适配中间件格式 |
| v1.0 | 2026-05-25 | 初版发布 |

---

## 十二、联系与支持

如有问题，请查看：
1. 日志文件：`/app/work/logs/bypass/app.log`
2. 详细文档：`docs/workflow_api_guide.md`
3. 架构说明：`AGENTS.md`