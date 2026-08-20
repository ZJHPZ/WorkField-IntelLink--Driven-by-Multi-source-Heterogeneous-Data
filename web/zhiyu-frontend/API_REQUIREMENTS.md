# 职域智联 · 个人侧后端接口需求文档

> 版本: v2.0  
> 更新: 2026-08-03  
> 目标: 为后端开发提供完整的数据模型、API端点、业务逻辑规格

---

## 一、数据模型

### 1.1 UserProfile — 用户职业档案

```typescript
interface UserProfile {
  userId: string                    // 唯一标识
  name: string                      // 真实姓名
  title: string                     // 当前职位，如 "高级前端开发工程师"
  phone: string                     // 手机号
  email: string                     // 邮箱
  birthYear: number                 // 出生年份，如 1995
  status: 'employed_looking' | 'employed_not_looking' | 'unemployed' | 'fresh_graduate' | 'freelance'
  industry: string                  // 所在行业，如 "互联网/IT"
  education: '大专' | '本科' | '硕士' | '博士'
  major: string                     // 专业，如 "计算机科学与技术"
  englishLevel: string              // 英语水平，如 "CET-6"
  experienceYears: string           // 工作年限范围，如 "5-8年"
  city: string                      // 所在城市

  // 求职意向
  targetRole: string                // 期望职位
  targetCity: string                // 期望城市
  targetIndustry: string            // 期望行业
  salaryMin: number                 // 薪资下限 K/月
  salaryMax: number                 // 薪资上限 K/月
  priority: 'salary_first' | 'tech_growth' | 'work_life_balance' | 'stability' | 'team_culture'
  travelOk: boolean                 // 接受出差
  relocateOk: boolean               // 接受异地
  workMode: 'onsite' | 'hybrid' | 'remote' | 'any'

  // 简历
  resumeUrl: string                 // 简历文件URL
  resumeParsedAt: string            // 最近解析时间 ISO

  // 元数据
  avatarEmoji: string               // 头像emoji，如 "👨‍💻"
  level: number                     // 用户等级 1-99
  createdAt: string                 // 注册时间 ISO
  updatedAt: string                 // 最后更新时间 ISO
}
```

### 1.2 SkillItem — 用户技能

```typescript
interface SkillItem {
  id: string                        // 唯一标识
  name: string                      // 技能名称，如 "Python"
  canonicalName: string             // 规范名称，用于去重
  category: string                  // 类别：编程语言 / AI/ML / 前端 / 数据 / DevOps / 架构
  level: 'basic' | 'intermediate' | 'advanced' | 'expert'
  marketDemand: number              // 市场需求指数 0-100
  marketDf: number                  // 市场文档频率 (JD中出现次数)
  emergence: number                 // 新兴度 0-1 (增长率)
  decline: number                   // 衰退率 0-1
  freshness: number                 // 保鲜度 0-100
  yearsOfExperience: number         // 使用年限
  confidence: number                // 技能识别置信度 0-1 (简历解析准确度)
  firstSeen: string                 // 首次识别日期 ISO
  status: 'healthy' | 'alert' | 'missing_high' | 'missing_low' | 'matched'
}
```

### 1.3 JobMatch — 岗位匹配

```typescript
interface JobMatch {
  id: string
  positionId: string                // 岗位标准ID
  positionName: string              // 岗位名称，如 "AI 算法工程师"
  company: string                   // 示例公司
  matchRate: number                 // 匹配率 0-100
  matchedSkills: string[]           // 已匹配技能名称列表
  missingSkills: string[]           // 缺失技能名称列表
  salaryRange: string               // 薪资范围，如 "40-70K"
}
```

### 1.4 LearningStep — 学习路径步骤

```typescript
interface LearningStep {
  id: string
  title: string                     // 步骤标题，如 "Kubernetes 基础"
  skill: string                     // 目标技能
  resource: string                  // 推荐资源，如 "K8s 官方教程 + CKAD 认证"
  estimatedHours: number            // 预估学时
  status: 'locked' | 'available' | 'in_progress' | 'completed'
  progress: number                  // 进度 0-100
  prerequisites: string[]           // 前置技能
  order: number                     // 排序
}
```

### 1.5 FreshnessAlert — 保鲜预警

```typescript
interface FreshnessAlert {
  skillName: string
  halfLife: number                  // 半衰期 (月)
  currentFreshness: number          // 当前保鲜度 0-100
  declineRate: number               // 衰退速率 0-1
  suggestedAction: string           // 建议行动
  urgency: 'high' | 'medium' | 'low'
}
```

### 1.6 CareerSwitchOption — 转行选项

```typescript
interface CareerSwitchOption {
  targetRole: string                // 目标岗位
  transferabilityScore: number      // 可迁移性评分 0-100
  skillOverlap: string[]            // 技能重叠列表
  skillGaps: string[]               // 技能缺口列表
  estimatedTransitionMonths: number // 预估过渡周期 (月)
  marketDemand: number              // 目标市场需求 0-100
  jaccardSimilarity: number         // Jaccard 相似系数 0-100
}
```

### 1.7 CareerMilestone — 职业里程碑

```typescript
interface CareerMilestone {
  id: number
  name: string                      // 如 "首次匹配"
  description: string               // 如 "完成第一次人岗匹配分析"
  icon: string                      // emoji 图标
  rarity: 'COMMON' | 'RARE' | 'EPIC' | 'LEGENDARY'
  unlocked: boolean
  unlockedAt: string | null         // ISO
  progress: number                  // 当前进度
  target: number                    // 目标值
}
```

### 1.8 GrowthTimeline — 成长时间轴事件

```typescript
interface GrowthTimelineEvent {
  date: string                      // 日期，如 "2022.03"
  skillsGained: number              // 新增技能数
  skills: string[]                  // 新增技能名称
  cumulativeCount: number           // 累计技能总数
  description: string               // 描述
}
```

### 1.9 AIInsight — AI 分析洞察

```typescript
interface AIInsight {
  type: 'advantage' | 'gap' | 'alert' | 'suggestion'
  color: string                     // #10b981 / #f59e0b / #f43f5e / #6366f1
  label: string                     // "优势方向" / "待提升" / "保鲜预警" / "建议"
  text: string                      // 具体内容
}

interface AISummary {
  summaryText: string               // AI 职业顾问总结文本
  insights: AIInsight[]             // 4条洞察
  generatedAt: string               // 生成时间 ISO
}
```

---

## 二、REST API 端点

### 2.1 用户档案

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/profile` | 获取用户档案 | — | `UserProfile` |
| PUT | `/api/personal/profile` | 更新用户档案 | `Partial<UserProfile>` | `UserProfile` |
| POST | `/api/personal/profile/resume` | 上传简历 (multipart) | `FormData { file }` | `{ resumeUrl, parsedSkills: SkillItem[] }` |

### 2.2 技能管理

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/skills` | 获取全部技能列表 | — | `{ skills: SkillItem[], totalCount, healthyCount, alertCount }` |
| GET | `/api/personal/skills/:id` | 获取单个技能详情 | — | `SkillItem` |
| POST | `/api/personal/skills` | 手动添加技能 | `{ name, category, level }` | `SkillItem` |
| PUT | `/api/personal/skills/:id` | 更新技能 | `Partial<SkillItem>` | `SkillItem` |
| DELETE | `/api/personal/skills/:id` | 删除技能 | — | `204` |
| GET | `/api/personal/skills/radar` | 获取雷达图维度数据 | — | `{ dimensions: RadarDimension[] }` |

### 2.3 岗位匹配

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/matches` | 获取匹配岗位列表 | query: `?positionId=` | `{ matches: JobMatch[] }` |
| GET | `/api/personal/matches/:id` | 获取单个匹配详情 | — | `{ match: JobMatch, radarData, gapAnalysis }` |
| POST | `/api/personal/matches/compare` | 多岗位对比 | `{ positionIds: string[] }` | `{ comparisons: CompareResult[] }` |
| POST | `/api/personal/matches/analyze` | 触发AI岗位匹配分析 | `{ positionId }` | `JobMatch` (SSE流式返回) |

### 2.4 学习路径

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/learning-path` | 获取完整学习路径 | — | `{ steps: LearningStep[], totalHours, estWeeks }` |
| PUT | `/api/personal/learning-path/:id` | 更新步骤状态/进度 | `{ status?, progress? }` | `LearningStep` |
| POST | `/api/personal/learning-path/generate` | 根据匹配结果生成学习路径 | `{ positionId }` | `{ steps: LearningStep[] }` |

### 2.5 技能保鲜

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/freshness` | 获取保鲜数据 | — | `{ alerts: FreshnessAlert[], healthPercent, healthySkills, lighthouseData }` |
| POST | `/api/personal/freshness/scan` | 触发保鲜度扫描分析 | — | `{ alerts: FreshnessAlert[], updatedAt }` |

### 2.6 转行分析

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/switch` | 获取转行选项列表 | — | `{ options: CareerSwitchOption[] }` |
| GET | `/api/personal/switch/analyze` | 分析指定转行方向 | query: `?from=&to=` | `CareerSwitchOption` (含详细分析) |
| GET | `/api/personal/switch/presets` | 获取预设热门转行方向 | — | `{ presets: { from, to, label }[] }` |

### 2.7 成长轨迹

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/growth` | 获取成长数据 | — | `{ currentLevel, levels, timeline: GrowthTimelineEvent[] }` |
| GET | `/api/personal/growth/level-requirements` | 获取下一等级要求 | — | `{ nextLevel, requirements, estMonths }` |

### 2.8 职业里程碑

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/milestones` | 获取里程碑列表 | — | `{ milestones: CareerMilestone[], unlockedCount }` |

### 2.9 用户偏好

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/preferences` | 获取偏好设置 | — | `{ targetRoles, salaryMin, salaryMax, city, notifyFreq }` |
| PUT | `/api/personal/preferences` | 更新偏好设置 | `{ targetRoles?, salaryMin?, ... }` | `Preferences` |

### 2.10 AI 分析

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/personal/ai/summary` | 获取AI职业顾问总结 | — | `AISummary` |
| POST | `/api/personal/ai/refresh` | 触发AI重新分析 | — | `AISummary` (SSE流式返回) |

---

## 三、SSE 流式接口

### 3.1 通用 SSE 格式

```
Content-Type: text/event-stream

data: {"type":"progress","message":"正在分析技能画像...","percent":30}

data: {"type":"partial","field":"summaryText","content":"基于你的12项技能..."}

data: {"type":"complete","result":{...}}

data: {"type":"error","message":"分析超时，请重试"}
```

### 3.2 SSE 端点

| 端点 | 触发时机 | 流式内容 |
|------|---------|---------|
| `/api/personal/ai/refresh` | AI刷新按钮 | 逐字段生成 AISummary |
| `/api/personal/matches/analyze` | 岗位匹配分析 | 逐字段生成 JobMatch |
| `/api/personal/freshness/scan` | 保鲜度扫描 | 逐技能分析保鲜度 |

---

## 四、通用规范

### 4.1 认证

所有接口需要 Bearer Token:
```
Authorization: Bearer <jwt_token>
```

### 4.2 响应格式

成功:
```json
{
  "code": 0,
  "data": { ... },
  "message": "ok"
}
```

错误:
```json
{
  "code": 40001,
  "data": null,
  "message": "技能不存在"
}
```

### 4.3 分页

列表接口支持分页:
```
GET /api/personal/skills?page=1&pageSize=20
```

响应:
```json
{
  "code": 0,
  "data": {
    "items": [...],
    "total": 12,
    "page": 1,
    "pageSize": 20
  }
}
```

### 4.4 前端容错策略 (已实现)

所有 Store 遵循 **Silent Fallback** 模式:
```typescript
// 初始化时填充完整 demo 数据
const skills = ref<SkillItem[]>([...demoSkills])

// API成功则覆盖，失败则静默保留demo数据
async function fetchSkills() {
  try {
    const res = await client.get('/api/personal/skills')
    if (res?.skills?.length) skills.value = res.skills
  } catch {
    // 静默 — demo数据保留
  }
}
```

后端只需实现 API 并返回正确格式，前端无需改动即可对接。

---

## 五、数据依赖关系

```
UserProfile (基础档案)
  ├── SkillItem[] (技能列表)
  │     ├── FreshnessAlert[] (保鲜预警 — 基于技能衰退率计算)
  │     └── RadarDimension[] (雷达图 — 按类别聚合技能)
  ├── JobMatch[] (岗位匹配 — 基于技能+JD分析)
  │     └── LearningStep[] (学习路径 — 基于匹配缺口生成)
  ├── CareerSwitchOption[] (转行分析 — 基于技能可迁移性)
  ├── CareerMilestone[] (里程碑 — 基于用户行为触发)
  ├── GrowthTimelineEvent[] (成长时间轴 — 基于技能增长历史)
  └── AISummary (AI分析 — 基于以上所有数据)
```

---

## 六、实施优先级

| 优先级 | 接口组 | 依赖页面 | 说明 |
|--------|--------|---------|------|
| **P0** | 技能管理 (2.2) | 全部8页面 | 核心数据，所有页面依赖 |
| **P0** | 用户档案 (2.1) | PersonalCenterView, ProfileView | 基本信息展示 |
| **P1** | 岗位匹配 (2.3) | DashboardView, MatchView, PersonalCenterView | 核心功能 |
| **P1** | 学习路径 (2.4) | LearningPathView, DashboardView | 基于匹配结果 |
| **P1** | 技能保鲜 (2.5) | FreshnessView, DashboardView | 基于技能衰退率 |
| **P2** | 转行分析 (2.6) | SwitchView | 基于技能可迁移性 |
| **P2** | 成长轨迹 (2.7) | GrowthView | 基于技能增长历史 |
| **P2** | AI分析 (2.10) | DashboardView, ProfileView | 增强体验 |
| **P3** | 职业里程碑 (2.8) | PersonalCenterView | 游戏化 |
| **P3** | 用户偏好 (2.9) | PersonalCenterView | 个性化 |

---

## 七、前端 Store 参考

文档对应的前端 Store 文件: `src/stores/personal.ts`

当前 demo 数据覆盖:
- 12 项技能 (6个类别)
- 3 个岗位匹配
- 5 个学习步骤
- 4 条保鲜预警
- 6 个转行选项
- 8 个里程碑

所有 demo 数据结构与上述接口响应格式完全一致，后端按此规范实现即可无缝替换。
