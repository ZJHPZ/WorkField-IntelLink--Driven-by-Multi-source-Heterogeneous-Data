# 工作流迁移指南

## 一、接口差异对比

### 1. 请求格式对比

| 项目 | 智能体接口 | 工作流接口 |
|-----|-----------|-----------|
| **请求方式** | POST | POST |
| **API地址** | `https://tg6v6v36r5.coze.site/stream_run` | `http://localhost:9000/stream_run` |
| **认证方式** | Bearer Token（固定） | 可选（可在工作流中配置） |
| **请求格式** | 嵌套JSON | 扁平JSON |
| **响应格式** | SSE流式 | SSE流式（相同） |

### 2. 请求体结构

**智能体接口：**
```json
{
  "content": {
    "query": {
      "prompt": [
        {
          "type": "text",
          "content": {"text": "什么是Hadoop？"}
        }
      ]
    }
  },
  "type": "query",
  "session_id": "session_001",
  "project_id": "7634252730730840079"
}
```

**工作流接口：**
```json
{
  "user_id": "user_001",
  "session_id": "session_001",
  "user_message": "什么是Hadoop？"
}
```

### 3. 功能差异

| 功能 | 智能体接口 | 工作流接口 |
|-----|-----------|-----------|
| **画像增强** | ❌ 无 | ✅ 有（自动判断并应用） |
| **对话记录** | ❌ 无 | ✅ 有（异步Webhook记录） |
| **降级策略** | ❌ 无 | ✅ 有（画像不可用时降级） |
| **个性化** | ❌ 通用 | ✅ 基于用户画像个性化 |
| **智能体配置** | ✅ 使用固定Bot | ✅ 相同Bot（已集成） |

---

## 二、迁移准备清单

### ✅ 步骤1：环境配置

需要在部署环境中配置以下环境变量：

```bash
# 必需配置
export BACKEND_URL="https://your-backend-domain.com"
export BACKEND_API_KEY="your_backend_api_key"

# 可选配置（已内置默认值）
export AGENT_API_URL="https://tg6v6v36r5.coze.site/stream_run"
export AGENT_API_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6ImE2OTQ4OTk2LWQyNjItNDJlNS1hNmU1LTI4YjA0ZGZkYTQ0YSJ9..."
```

### ✅ 步骤2：后端接口依赖

确保您的后端系统提供以下接口：

| 接口 | 方法 | URL | 说明 |
|-----|------|-----|------|
| 获取画像状态 | GET | `/api/v1/profile/{user_id}/status` | 返回用户画像是否可用 |
| 获取画像摘要 | GET | `/api/v1/profile/{user_id}/summary` | 返回用户画像详细信息 |
| 记录对话 | POST | `/api/v1/profile/chat-log` | 接收对话记录（异步） |

**画像状态接口响应格式：**
```json
{
  "is_ready": true,
  "fallback_used": false,
  "message": "画像可用"
}
```

**画像摘要接口响应格式：**
```json
{
  "learning_style": "visual",
  "knowledge_level": "intermediate",
  "interests": ["Python", "大数据", "机器学习"],
  "communication_preferences": {
    "explanation_style": "visual_with_examples",
    "feedback_style": "encouraging_specific"
  },
  "avoid_patterns": ["过度批评", "纯理论讲解"],
  "strengths": ["编程基础", "逻辑思维"],
  "weaknesses": ["分布式系统理解"]
}
```

### ✅ 步骤3：启动工作流服务

```bash
# 方式1：直接启动（开发环境）
python src/main.py

# 方式2：使用uvicorn启动（生产环境）
uvicorn src.main:app --host 0.0.0.0 --port 9000

# 服务启动后可访问：
# - POST http://localhost:9000/run （同步接口）
# - POST http://localhost:9000/stream_run （流式接口）
# - POST http://localhost:9000/cancel/{run_id} （取消接口）
```

---

## 三、代码修改建议

### 方案A：修改现有项目调用（推荐）

如果您现有项目通过HTTP调用智能体，只需修改：

```python
# ❌ 原调用方式
import requests

response = requests.post(
    "https://tg6v6v36r5.coze.site/stream_run",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "content": {
            "query": {
                "prompt": [{"type": "text", "content": {"text": user_message}}]
            }
        },
        "type": "query",
        "session_id": session_id,
        "project_id": "7634252730730840079"
    },
    stream=True
)

# ✅ 新调用方式
response = requests.post(
    "http://localhost:9000/stream_run",  # 改为工作流地址
    json={  # 简化的请求格式
        "user_id": user_id,  # 新增：用户ID（用于画像）
        "session_id": session_id,
        "user_message": user_message
    },
    stream=True
)
```

### 方案B：创建适配层

如果您不想修改现有代码，可以创建适配层：

```python
# adapter.py
import requests

def call_workflow(user_id, session_id, user_message):
    """工作流适配器"""
    response = requests.post(
        "http://localhost:9000/stream_run",
        json={
            "user_id": user_id,
            "session_id": session_id,
            "user_message": user_message
        },
        stream=True
    )
    
    # 解析SSE响应（与原格式相同）
    for line in response.iter_lines():
        if line:
            yield line.decode('utf-8')
```

---

## 四、测试验证

### 1. 本地测试

```bash
# 测试同步接口
curl -X POST http://localhost:9000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "session_id": "session_001",
    "user_message": "什么是Hadoop？"
  }'

# 测试流式接口
curl -X POST http://localhost:9000/stream_run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "session_id": "session_001",
    "user_message": "什么是Hadoop？"
  }'
```

### 2. 画像功能验证

**场景1：画像可用**
```json
请求：{"user_id": "user_with_profile", "session_id": "s1", "user_message": "什么是Spark？"}
预期：
1. 调用画像接口获取用户信息
2. 根据画像调整回复风格（如视觉型学习者→更多图表示例）
3. Webhook记录对话
```

**场景2：画像不可用（降级）**
```json
请求：{"user_id": "user_without_profile", "session_id": "s2", "user_message": "什么是Spark？"}
预期：
1. 画像接口返回 is_ready=false
2. 直接调用智能体（无画像增强）
3. Webhook记录对话
```

### 3. 性能对比

| 指标 | 智能体接口 | 工作流接口 | 说明 |
|-----|-----------|-----------|------|
| **首字节延迟** | ~500ms | ~600ms | 增加100ms（画像查询） |
| **吞吐量** | 高 | 中 | 工作流有额外处理 |
| **功能完整度** | 基础 | 完整 | 工作流提供画像增强 |

---

## 五、回滚方案

如果迁移后出现问题，可快速回滚：

### 方案1：修改API地址
```python
# 临时回滚到智能体接口
WORKFLOW_URL = "https://tg6v6v36r5.coze.site/stream_run"  # 原智能体地址
```

### 方案2：禁用画像功能
```python
# 在工作流中禁用画像
export ENABLE_PROFILE_ENHANCEMENT="false"
```

### 方案3：完全回滚
```bash
# 切换回原智能体调用代码
git checkout <previous_version>
```

---

## 六、监控与运维

### 1. 日志监控

工作流日志位置：`/app/work/logs/bypass/app.log`

```bash
# 查看最近日志
tail -f /app/work/logs/bypass/app.log

# 搜索错误
grep -i "error\|exception" /app/work/logs/bypass/app.log | tail -n 20
```

### 2. 性能监控

```bash
# 查看工作流执行状态
curl http://localhost:9000/health

# 查看正在运行的任务
# （可通过日志中的run_id追踪）
```

### 3. 告警配置

建议配置以下告警：
- 工作流启动失败
- 画像接口调用失败率 > 10%
- 智能体调用失败率 > 5%
- 平均响应时间 > 3秒

---

## 七、常见问题

### Q1: 画像接口返回失败怎么办？
**A:** 工作流自动降级，直接调用智能体，不影响用户使用。

### Q2: 如何判断画像是否生效？
**A:** 查看日志，搜索 `use_profile` 或 `use_fallback` 关键字。

### Q3: 如何临时禁用某个用户画像？
**A:** 在画像状态接口返回 `is_ready=false`。

### Q4: 工作流可以同时服务多个应用吗？
**A:** 可以，每个应用通过不同的 `user_id` 区分画像。

---

## 八、迁移时间表

| 阶段 | 时间 | 任务 |
|-----|------|------|
| 准备阶段 | Day 1 | 配置环境变量、部署工作流 |
| 测试阶段 | Day 2-3 | 本地测试、画像功能验证 |
| 灰度阶段 | Day 4-5 | 10%流量切换到工作流 |
| 全量阶段 | Day 6-7 | 100%流量切换、监控告警 |
| 优化阶段 | Day 8+ | 根据监控数据优化画像策略 |

---

## 九、联系方式

如有问题，请查看：
- 工作流文档：`AGENTS.md`
- 日志文件：`/app/work/logs/bypass/app.log`
- 项目结构：`README.md`
