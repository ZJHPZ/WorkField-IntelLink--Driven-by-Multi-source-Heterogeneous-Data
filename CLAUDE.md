# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**职域智联 (Zhiyu Zhilian)** — 多源异构数据驱动岗位和能力图谱构建与动态演化分析系统。Full-stack application with a Python/FastAPI backend and a Vue 3 frontend.

| Layer | Directory | Tech |
|---|---|---|
| **后端** | `后/` | Python 3.12 + FastAPI + **MySQL only** (graph store is MySQL, Neo4j is dead code) + 讯飞星火 LLM |
| **前端** | `web/zhiyu-frontend/` | Vue 3.5 + TypeScript + Vite + Pinia + Tailwind CSS + ECharts + Three.js |

The frontend is effectively **two separate projects** living in one repo — they do NOT share a design system:

| Mode | Route prefix | Target User | Purpose |
|---|---|---|---|
| **个人侧** | `/personal` | Individual professionals | Skill profiling, job matching, learning paths, freshness monitoring, career switching |
| **企业侧** | `/enterprise` | HR / managers | Position standard management, JD quality diagnosis, market trends, team skill gaps |

Design languages are separate — **two independent design systems, both implemented**:
- **个人侧** uses **"深空舰桥工业风格" (Deep Space Battleship Bridge Industrial Style)** — real spacecraft control panels, not glassmorphism (`DESIGN_SYSTEM.md` v2.0 + `utilities.css`).
- **企业侧** uses **"蓝皮书 · 权威纸面" (Blue Book · Authoritative Paper)** — deep navy + coral "seals" on a fixed light-paper background, designed to read as a formal position-standard document in effect (`DESIGN_SYSTEM_企业侧.md` v1.0 + `enterprise.css`). It does NOT use the industrial panel classes.

## Directory Layout

```
前后/                              ← project root
├── 后/                            ← backend (FastAPI, its own git repo)
│   ├── app/
│   │   ├── main.py               # FastAPI factory + lifespan (manages MySQL connection only)
│   │   ├── config.py             # pydantic-settings (reads .env); MySQL + Neo4j settings
│   │   ├── deps.py               # DI helpers
│   │   ├── api/                  # Route handlers: enterprise, personal, match, graph, positions, metrics
│   │   ├── agents/               # Multi-agent system: orchestrator + 8 agents + registry/router/executor
│   │   ├── adapters/             # External data sources: arxiv, github, jd, resume, fusion
│   │   ├── pipeline/             # L1→L4 data processing pipeline (stateless functions)
│   │   ├── services/             # Business logic: career, enterprise, evolution, match, pipeline, resume
│   │   ├── graph/                # Graph repository — now MySQL-backed (Neo4j client.py is unused legacy)
│   │   ├── persistence/          # SQLAlchemy async models + repository (MySQL via aiomysql)
│   │   ├── domain/               # Domain models: metrics, signals (pure dataclasses)
│   │   ├── eval/                 # Accuracy evaluation: jd, match, resume
│   │   └── utils/                # spark (LLM client), text processing
│   ├── tests/                    # pytest: unit, integration, API, pipeline, services, graph
│   ├── data/jd/                  # JD source data files (batch1.jsonl)
│   ├── pyproject.toml            # Dependencies + ruff + pytest config
│   ├── Dockerfile, docker-compose.yml   # ⚠ docker-compose.yml is STALE (still Neo4j/Postgres)
│   ├── 多智能体架构设计.md        # Multi-agent system design doc
│   ├── 需求文档_个人侧.md / 需求文档_企业侧.md   # Requirement docs
│   └── 重构方案.md               # Historical SSOT for backend architecture — code has DIVERGED (see Gotchas)
│
├── 参考/                          ← reference projects (read-only)
│   ├── shuzhi-frontend/          # "数知" frontend reference
│   └── ai对话助手智能体/          # AI agent reference
│
└── web/                           ← frontend workspace
    ├── zhiyu-frontend/            ← the Vue 3 frontend app
    │   ├── src/
    │   │   ├── api/client.ts      # Axios instance + interceptor (returns response.data directly)
    │   │   ├── components/
    │   │   │   ├── common/        # 15 shared components (CosmicBackground, StatusCard, ProgressRing, EnergyBar, GlassCard, HolographicBackdrop, etc.)
    │   │   │   ├── enterprise/    # Enterprise-specific components
    │   │   │   ├── personal/      # Personal-specific (MatchRadar, MatchOrbit, SkillConstellation, PrismScene, SignalPrism, etc.)
    │   │   │   └── chat/          # ChatMessage.vue (AI chat)
    │   │   ├── composables/       # useEChartsTheme, useMagneticHover, useNotify, useRippleClick, useScrollReveal
    │   │   ├── router/index.ts    # 10 enterprise + 15 personal routes (lazy-loaded)
    │   │   ├── stores/            # Pinia: app, enterprise, personal, chat, theme
    │   │   ├── styles/            # CSS files — the real design system
    │   │   └── views/
    │   │       ├── enterprise/    # 10 views
    │   │       └── personal/      # 15 views
    │   ├── DESIGN_SYSTEM.md       # 深空舰桥工业风格完整规范 (v2.0) — 个人侧
    │   └── DESIGN_SYSTEM_企业侧.md # 蓝皮书·权威纸面完整规范 (v1.0) — 企业侧
    │
    ├── CLAUDE.md                  # Frontend-scoped CLAUDE.md (subset of this file)
    └── 前端设计_*.md              # Frontend design specs and implementation guides
```

## Development Commands

### Frontend (from `web/zhiyu-frontend/`)

```bash
npm run dev       # Vite dev server on http://localhost:3001, proxies /api → http://localhost:8001
npm run build     # vue-tsc -b && vite build (type-check then bundle)
npm run preview   # Preview production build
```

No test runner, linter, or formatter is configured for the frontend.

### Backend (from `后/`)

```bash
pip install -e .[dev]           # Install in dev mode (ruff + mypy)
uvicorn app.main:app --reload   # Dev server — run on --port 8001 to match the Vite proxy target
pytest                          # Run all tests (addopts auto-includes --cov=app)
pytest tests/test_api.py        # Run single test file
pytest -k "test_name"           # Run single test by name
ruff check .                    # Lint
ruff format .                   # Format

# End-to-end pipeline (no LLM calls)
python -m app.services.pipeline_service --n 10 --no-spark

# End-to-end pipeline with agent system
python -m app.services.pipeline_service --n 10 --agent
```

Backend requires Python 3.12+ and **MySQL** (database `zhiyv`, see `.env.example`). Neo4j is NOT required at runtime — the graph store is MySQL.

⚠ **Known dependency gap**: `pyproject.toml` still lists `asyncpg` but the code actually imports `aiomysql`/`pymysql` (via `config.py`'s `mysql+aiomysql` / `mysql+pymysql` URLs), which are NOT in the dependencies. `pip install -e .` may not bring in the MySQL driver — install `aiomysql pymysql` explicitly if the DB connection fails.

## Backend Architecture

### Six-Layer Pipeline

Data flows through `app/pipeline/` in layers:

- **L1** (`l1_clean.py`, `l1_segment.py`): Clean raw JD text, segment into sections, classify skill levels (L0 noise → L3 hard skills)
- **L2** (`l2_dedup.py`, `l2_normalize.py`, `l2_confidence.py`, `l2_cooccurrence.py`, `l2_metrics.py`): Dedup (SimHash), normalize skill names, compute confidence scores, co-occurrence analysis, six dynamic metrics (emergence/decline/volatility/half-life/etc.)
- **L3** (`l3_extract.py`, `l3_verify.py`): Extract skills via LLM + rules fallback, then gate through hallucination prevention (three-stage verification: citation → evidence check → content check)
- **L4** (`l4_graph.py`, `l4_snapshot.py`): Build graph JSON (AntV G6) and **write to MySQL** — `skill_stats`, `verified_skills`, `skill_cooccurrence`, `graph_snapshots` tables

Entry point: `python -m app.services.pipeline_service`

### Data Layer — MySQL is the single store (Neo4j migrated out)

**Everything** (graph data, metrics, user data) lives in the MySQL `zhiyv` database via `app/persistence/zhiyv_models.py` (SQLAlchemy async + aiomysql). 14 tables: `skill_stats`, `verified_skills`, `skill_cooccurrence`, `graph_snapshots`, `new_roles`, `evolution_records`, `user_profiles`, `user_skills`, `user_matches`, `learning_steps`, `career_milestones`, `growth_timeline`, `ai_insights`, `user_preferences`.

- **Graph layer migrated from Neo4j to MySQL**: `app/graph/repository.py`'s docstring states it *"替代原 Neo4j Cypher 查询"* — it issues SQLAlchemy queries against the MySQL tables above with the same external interface (AntV G6 output). The Neo4j client (`app/graph/client.py`) is unused legacy code (0 imports anywhere in `app/`).
- **Legacy remnants still present** (don't assume they work): Neo4j settings in `config.py`, `neo4j`/`asyncpg` in `pyproject.toml`, the Docker Compose file (still spins up Neo4j 5.26 + Postgres 16, but the app now needs neither).
- Config: `app/config.py` reads from `.env` (pydantic-settings); `.env.example` is the template.

### Multi-Agent System

Located in `app/agents/`. Infrastructure evolved beyond a plain shared-context pattern:

- `system.py` — `MultiAgentSystem` is the single entry point: `initialize(llm_client)` registers all agents, then `process(intent, params)` / `process_pipeline(items, agent_ids)` execute. Business code calls this, never individual agents.
- `agent_state.py` — `IntentType` (16 intents, each mapped to an API endpoint — **not NLP**), `TaskStatus`, `MultiAgentState`, `ProcessingMode` (FEDERATED / COLLABORATIVE / PIPELINE).
- `registry.py` — Singleton `AgentRegistry`: intent→agent mapping + dependency graph.
- `router.py` — Static `IntentType → agent_id` map.
- `executor.py` — `AgentExecutor` (singleton): federated (independent agents run parallel), collaborative (dependency chain, results passed via state), pipeline (MapReduce over batch data).
- `base.py` — `BaseAgent` (abstract), `FederatedAgent`, `CollaborativeAgent`.
- `shared_context.py` — Primary inter-agent communication is a shared state dict. `message.py` (`AgentMessage`) is used only for debate-style structured exchange, not a full message bus.
- Agents registered (8 + orchestrator): `extract`, `verify`, `normalize`, `match`, `discovery`, `judge`, `evolution`, `suggest`, plus `OrchestratorAgent` (intent decomposition + scheduling). There is **no `skeptic_agent`** anymore — the debate pair is discovery (proposer) + judge (verdict).

LLM: 讯飞星火 via OpenAI-compatible SDK (`app/utils/spark.py`). Default model is **`spark-x`** (configurable via `.env` `SPARK_MODEL`). SparkClient exposes `chat()`, `extract_json()`, and throttles requests.

### API Routes

All routes aggregated in `app/api/router.py`, prefixed with `/api`. **All ~50 endpoints are implemented** — there are no 501 stubs left:

- `/api/graph` — full graph (AntV G6), snapshots, snapshot diff
- `/api/metrics` — metric report, emerging/declining skill rankings
- `/api/positions` — position list, detail, evolution timeline
- `/api/match` — `resume/parse`, `match`, `match/batch`
- `/api/enterprise/*` — JD diagnosis, position standards, team gap, talent forecast, discovery, evolution
- `/api/personal/*` — profile CRUD, skills, matches, learning path, freshness, switch, growth, milestones, preferences, `ai/summary`, `ai/chat` (SSE streaming)

## Frontend Architecture

### Key Files to Understand First

| File | Why it matters |
|---|---|
| `src/styles/variables.css` | CSS variable definitions for 4 theme modes (dark, light, warm-light, industrial) |
| `src/styles/utilities.css` | 6 panel types, 13 decoration classes — all industrial design utilities (个人侧) |
| `src/styles/enterprise.css` | Enterprise 蓝皮书 utilities (`.panel-doc`, `.seal-chip`, `.doc-masthead`, …) — only for enterprise views |
| `DESIGN_SYSTEM_企业侧.md` | 蓝皮书·权威纸面完整规范 (v1.0) — applies to **企业侧 only** |
| `src/styles/animations.css` | Keyframe animations: glow, heartbeat-pulse, confetti, scan-line |
| `src/styles/dark-override.css` | `[data-theme="dark"]` overrides for Tailwind utility classes |
| `src/components/common/CosmicBackground.vue` | 3-layer radial-gradient + 80 CSS star particles + data flow lines |
| `src/components/common/StatusCard.vue` | Generic 4-state card — `statusConfig` prop drives visual per domain |
| `src/components/common/HolographicBackdrop.vue` | Three.js canvas holographic layer (one of two Three.js components) |
| `src/stores/personal.ts` | Silent Fallback pattern: demo data → API override → silent catch |
| `src/router/index.ts` | All routes (10 enterprise + 15 personal) with `meta.title` and `meta.role` for nav filtering |

### CSS Architecture

9 style files imported **in order by `src/main.ts`** (not `tailwind.css`, which only holds the `@tailwind` directives):

1. **`variables.css`** — CSS custom properties for 4 theme modes: `:root` (deep space dark), `[data-theme="light"]`, `[data-theme="warm-light"]`, `[data-theme="industrial"]` — personal-side palettes; enterprise has its own scoped palette (see below)
2. **`base.css`** — Reset + global element styles
3. **`utilities.css`** — Personal-side industrial design system: `.panel-industrial`, `.panel-bridge`, `.panel-asymmetric`, `.panel-neon`, `.panel-circuit`, `.panel-hazard`, `.rivet`, `.tag-plate`, `.data-segment`, `.holo-overlay`, `.scan-line-fast`, `.beam-divider`, `.nav-chip`, `.sidebar-depth`, `.main-board`, etc.
4. **`animations.css`** — Keyframes: `glowBrand`, `heartbeat-pulse`, `confetti-burst`, `scaleIn`, `fadeInUp`, `shimmer`, `twinkle`
5. **`advanced-animations.css`** — `@property`-registered animatable CSS vars + ripple / magnetic / scroll effects
6. **`dark-override.css`** — Maps Tailwind `.bg-white` etc. under `[data-theme="dark"]`
7. **`enterprise.css`** — Enterprise 蓝皮书 design system (`.ent-shell`, `.panel-doc`, `.doc-masthead`, `.seal-chip`, `.leader-row`, `.stat-tile`, `.coral-glow`, …). Scoped via `[data-side="enterprise"]` / `.ent-shell`; keeps enterprise on fixed light paper even in dark mode
8. **`markdown.css`** — Styles for markdown-it rendered content
9. **`tailwind.css`** — `@tailwind base/components/utilities`

Theme switching: set `data-theme` attribute on `<html>`. The `stores/theme.ts` store manages this.

### Frontend Tech Stack (actual versions from `package.json`)

```
Vue 3.5 + TypeScript 6.0 + Vite 8.2 + Pinia 4.0 + Vue Router 5.2
Tailwind CSS 3.4 (custom color system)
ECharts 6.1 + vue-echarts 8.0
Three.js 0.185 + @tresjs/core (holographic/prism scenes)
Axios 1.19
markdown-it 15 + markdown-it-katex
```

Note: Three.js WAS added for `HolographicBackdrop.vue` and `PrismScene.vue`. It is NOT used for a full 3D universe (that's still a 数知 carryover to avoid).

### Routes

**Enterprise (10):**
```
/enterprise                   Dashboard (HUD bar + timeline + discovery list)
/enterprise/positions          Position standards table
/enterprise/positions/:id      Position detail + evolution timeline
/enterprise/positions/:id/diff Market vs standard diff report
/enterprise/discovery          New role discovery center
/enterprise/diagnose           JD quality diagnosis
/enterprise/diagnose/batch     Batch audit
/enterprise/team               Team skill inventory
/enterprise/forecast           Talent demand forecast
/enterprise/graph              Full graph visualization (AntV G6)
```

**Personal (15):**
```
/personal                      Dashboard (skill star chart + match radar + freshness bar)
/personal/profile              Skill profile + growth timeline
/personal/explore              Position exploration
/personal/match                Person-position matching
/personal/match/compare        Multi-position comparison
/personal/resume               Resume parsing
/personal/learning-path        Learning path planner
/personal/freshness            Skill freshness center
/personal/switch               Career switch feasibility analysis
/personal/growth               Career growth trajectory
/personal/chat                 AI career advisor (SSE streaming)
/personal/center               Personal center (tabs)
/personal/spectrum             Skill signal spectrum
/personal/spectrum/:skill      Single-skill oscilloscope detail
/personal/evolution            Position evolution theater
```

Note: the `/` route **redirects to `/enterprise`** — the enterprise side is the default landing.

## Key Patterns

### Silent Fallback (Frontend Stores)
Initialize with realistic demo data first, override on API success, keep silently on failure. The app launches instantly with full UI — no loading spinners.
```ts
const items = ref<Item[]>(demoItems)  // pre-filled with 12+ realistic entries, not placeholders
async function fetchItems() {
  try { const res = await client.get('/api/items'); if (res) items.value = res }
  catch { /* silent — demo data stays */ }
}
```
The Axios `client` in `src/api/client.ts` returns `response.data` directly (response interceptor) and logs errors with a normalized message — callers see the payload, not the Axios envelope.

### CSS Variable Theming (NOT Tailwind `dark:`)
Theme switched via `data-theme="dark"|"light"|"warm-light"|"industrial"` on `<html>`. Global CSS variables define `--bg-primary`, `--bg-card`, `--text-primary`, `--border-color`, etc. Tailwind `dark:` is NOT used — all overrides go through `variables.css` and `dark-override.css`.

### Color System — Semantic Mapping
| Token | Tailwind class | Enterprise meaning | Personal meaning |
|---|---|---|---|
| `brand` (indigo) | `brand-*` | Primary interactions, buttons, links | Same |
| `cyan` | `cyan-*` | "Confirmed" status, emerging skills | "Matched" skills |
| `mint` | `mint-*` | "Verified", healthy skills | "Healthy" skills |
| `amber` | `amber-*` | "Pending verification", warning | "Freshness alert" |
| `rose` | `rose-*` | "Rejected", declining skills | "Missing required skill" |

### StatusCard — 4-State Pattern
Generic card whose `statusConfig` prop defines visual mapping per domain:
- Enterprise: `confirmed` (mint), `emerging` (brand glow), `stable` (gray), `declining` (rose dimmed), `candidate` (amber)
- Personal: `matched` (mint), `missing_high` (rose), `missing_low` (amber), `alert` (rose), `healthy` (mint)

### SSE Streaming
Server-Sent Events consumed via `fetch` + `ReadableStream` reader → parse `data:` JSON lines → async generator. Used for AI streaming responses in `/personal/chat` (backed by `POST /api/personal/ai/chat`).

## Visual Design Language — 深空舰桥工业风格 (个人侧 only)

All of the following applies to the **个人侧 (personal side)** views. Do NOT apply these industrial utilities (`panel-*`, `rivet`, `nav-chip`, etc.) to enterprise views — they have their own, fully separate design language (next section).

### Core Principles
- **No rounded corners** — use `clip-path` polygon cuts, asymmetric radii
- **Three panel identities**: `panel-industrial` (armor plate), `panel-bridge` (console), `panel-asymmetric` (auxiliary)
- **Light effects replace decoration**: neon glow, holographic scan lines, 7-segment data displays
- **Industrial details**: rivets (`.rivet`), circuit traces (`.panel-circuit`), hazard stripes (`.panel-hazard`), structural beams
- **Monospace typography**: uppercase labels, wide tracking, LED indicator dots

### Visual Metaphors
| Element | Metaphor | Implementation |
|---|---|---|
| Background | Deep space nebula | `CosmicBackground.vue` |
| Position/skill cards | Stars — glowing, stable, or fading | `StatusCard.vue` with `statusConfig` |
| Match rate | Orbital progress ring | `ProgressRing.vue` (SVG circle, gradient stroke) |
| Health bar | Lighthouse beam | `EnergyBar.vue` with brand/mint/amber/rose variants |
| Discovery celebration | Supernova burst | `StageCompleteModal` (confetti + scale-in) |
| AI processing | Heartbeat pulse | `heartbeat-pulse` keyframe |
| Holographic layer | 3D hologram | `HolographicBackdrop.vue` / `PrismScene.vue` (Three.js) |
| Sidebar nav items | IC chip modules | `.nav-chip` with metallic border, pin contacts, power-on glow |
| Sidebar | Raised console | `.sidebar-depth` on `.main-board` |

## Visual Design Language — 企业侧「蓝皮书 · 权威纸面」

The enterprise side has its **own** design language, implemented 2026-08-18, fully separate from the personal-side industrial style:

- **Concept**: every screen reads as *a position-standard document in effect* — deep navy print skeleton, coral "seals" marking the info that needs an HR decision, data rows laid out like a financial/consulting report (leader-dot + right-aligned mono values).
- **Look**: **fixed light paper** background (`--ent-paper`), never follows the global dark theme. Palette: navy (`#00094C`) + coral (`#C85C56`) + paper. **Coral is the only glow color in the system** (scarcity principle).
- **Signature classes** (in `src/styles/enterprise.css`, scoped via `.ent-shell` / `[data-side="enterprise"]`): `panel-doc` (paper card), `doc-masthead` (navy file header + coral seal), `seal-chip` (square ink-seal status badge, `rotate(-1deg)`, not a rounded pill), `leader-row` (dot-leader report row), `stat-tile`, `ent-btn`, `section-rule` (navy + coral double rule), `coral-glow`, `faded-ink` (strikethrough for declining/rejected).
- **Wiring**: `App.vue` sets `document.documentElement.dataset.side = 'enterprise'|'personal'` and adds `ent-shell` to the shell; `enterprise.css` takes over sidebar (navy TOC), background (paper grid), and content area.
- **Do NOT** reuse personal-side classes (`panel-*`, `rivet`, `nav-chip`, `CosmicBackground`) in enterprise views, or enterprise classes in personal views. The only shared habit is mono data typography.
- Reference view: `/enterprise` DashboardView. Spec: `web/zhiyu-frontend/DESIGN_SYSTEM_企业侧.md` v1.0.

## Things NOT to Carry Over from 数知
The `参考/` directory contains reference projects. Do NOT port these from `参考/shuzhi-frontend/`:
- DesktopPet, PetBubble, PetSwitcher (gamification)
- SocraticPanel (learning reflection)
- AnalysisFloatingWindow, DebugPanel
- Avatar/WebRTC SDK components
- Full Three.js 3D universe (a minimal Three.js canvas backdrop is already in use — don't expand it)
- Audio recorder/player composables

## Current Phase

Phase 3 (To B / To C business APIs) is **implemented** — all `/api/enterprise/*` and `/api/personal/*` endpoints are live, including SSE chat. Remaining work per `重构方案.md`: Phase 4 (evaluation targets: three ≥90% accuracy metrics, ≥60% pytest coverage) and Phase 5 (deliverables). Note that the code has already diverged from several `重构方案.md` specs (see Gotchas).

Recent (Aug 2026): the **enterprise-side design language** (蓝皮书·权威纸面) was spec'd (`DESIGN_SYSTEM_企业侧.md` v1.0) and implemented across all 10 enterprise views, replacing the placeholder glass-card styling.

## Key Design Decisions

1. No LangChain/LangGraph — custom lightweight Orchestrator (`AgentExecutor` + `AgentRegistry` + static intent router)
2. **MySQL is the single data store** — graph data, metrics, and user data all live in `zhiyv`; the Neo4j-backed graph layer was migrated to MySQL (`app/graph/repository.py`) with the same external interface. Neo4j is unused legacy.
3. Intents are static `IntentType` values mapped 1:1 to API endpoints — no NLP intent recognition
4. VerifyAgent is pure rules (no LLM) — gate itself must not hallucinate
5. `DATA_DIR` points to `后/data/jd/` for JD source files
6. `重构方案.md` is the historical architecture SSOT but the code has diverged (PostgreSQL→MySQL, skeptic agent removed, match agent added, l4_snapshot added) — **verify against code before acting**
7. **Two independent design systems, both implemented and deliberately non-interchangeable**: 深空舰桥工业风格 (个人侧) and 蓝皮书·权威纸面 (企业侧). Enterprise keeps a fixed light theme independent of the global `data-theme`.

## Gotchas / Known Drift

- **`重构方案.md` vs code**: The SSOT doc still says PostgreSQL 16 + Python 3.13 + Neo4j 6.x + a `skeptic_agent`. The code actually uses **MySQL + aiomysql, Python 3.12, no runtime Neo4j, no skeptic agent**. Treat the doc as history; the code is current truth.
- **Docker Compose is stale**: `后/docker-compose.yml` spins up Neo4j + Postgres and mounts an old data path — it does not reflect the current MySQL-only app.
- **Ports**: Vite dev server is on **3001** and proxies `/api` → **localhost:8001** (`vite.config.ts`). Run uvicorn with `--port 8001` for the proxy to connect.
- **MySQL driver dependency gap**: `pyproject.toml` lists `asyncpg` (Postgres) but the code needs `aiomysql`/`pymysql`, which are missing — install them manually if missing.
- **LLM model default is `spark-x`**, not "Spark-X2-Flash" — configurable via `.env` `SPARK_MODEL`.
- **个人侧 / 企业侧 are two separate design projects**: 深空舰桥工业风格 (industrial panels, rivets, nav-chips) belongs to the **personal side only**. The enterprise side has its **own 蓝皮书·权威纸面** design language (paper, navy, coral seals) — see "Visual Design Language — 企业侧". Don't mix the industrial utilities into enterprise views, and don't assume DESIGN_SYSTEM.md applies to both sides — each side reads its own spec (`DESIGN_SYSTEM.md` vs `DESIGN_SYSTEM_企业侧.md`).
