# 职域智联 · 多源异构数据驱动岗位和能力图谱构建与动态演化分析系统

基于多源异构数据（招聘 JD、行业报告、学术论文）构建**岗位与能力图谱**，支持岗位标准智能管理（企业侧）与职业规划（个人侧）。

| 层 | 目录 | 技术栈 |
|---|---|---|
| **后端** | `后/` | Python 3.12 · FastAPI · MySQL（单数据存储）· 讯飞星火 LLM · 多智能体系统 |
| **前端** | `web/zhiyu-frontend/` | Vue 3.5 · TypeScript · Vite · Pinia · Tailwind · ECharts · Three.js |

## 双端设计语言（各自独立，互不复用）

| 端 | 路由前缀 | 设计语言 | 规范文档 |
|---|---|---|---|
| **个人侧** | `/personal` | 深空舰桥工业风格（面板/铆钉/霓虹/扫描线） | `web/zhiyu-frontend/DESIGN_SYSTEM.md` v2.0 |
| **企业侧** | `/enterprise` | 蓝皮书·权威纸面（深蓝 + 珊瑚印章 + 固定纸面） | `web/zhiyu-frontend/DESIGN_SYSTEM_企业侧.md` v1.0 |

## 后端架构要点

- **六层数据管道 L1→L4**：清洗/去重/抽取/验证 → 构建图谱写入 MySQL（Neo4j 已迁出，为遗留死代码）
- **多智能体系统**（`后/app/agents/`）：Orchestrator + 8 个 Agent，静态 `IntentType` 映射 API，无 NLP 意图识别
- **全部 ~50 个 API 已实现**，含 `/api/personal/ai/chat` SSE 流式对话
- 配置模板见 `后/.env.example`（密钥只存本地 `.env`，不入库）

## 快速开始

```bash
# 后端（端口 8001，配合前端代理）
cd 后
pip install -e .[dev]        # 若 DB 连接失败，补装 aiomysql pymysql
uvicorn app.main:app --port 8001

# 前端（端口 3001，/api 代理到 8001）
cd web/zhiyu-frontend
npm run dev
```

访问 http://localhost:3001 → 默认落地 `/enterprise`。

## 更多文档

- `CLAUDE.md`（项目根）— 完整架构说明与开发命令
- `后/重构方案.md` — 历史架构 SSOT（⚠ 与代码有漂移，以代码为准）
- `web/设计_智能体微服务模板_苏格拉底模式.md` — 「人格即服务」AI 微服务可复用模板
- `web/zhiyu-frontend/` — 前端设计规范（两份独立设计系统）
