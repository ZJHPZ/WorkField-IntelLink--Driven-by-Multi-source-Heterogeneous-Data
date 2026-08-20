# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**职域智联 (Zhiyu Zhilian)** frontend — Vue 3 app at `web/zhiyu-frontend/`. It talks to the FastAPI backend in `../后/` (sibling directory, MySQL-backed).

The frontend is effectively **two separate projects** in one repo — they do **NOT** share a design system:

| Mode | Route prefix | Target User | Design language |
|---|---|---|---|
| **个人侧** | `/personal` | Individual professionals | **深空舰桥工业风格** — `DESIGN_SYSTEM.md` v2.0 |
| **企业侧** | `/enterprise` | HR / managers | **蓝皮书 · 权威纸面** — `DESIGN_SYSTEM_企业侧.md` v1.0, implemented in `enterprise.css` across all 10 views (Aug 2026) |

> ⚠ Two fully separate design systems, both implemented. Do NOT apply the industrial utilities (`panel-*`, `rivet`, `nav-chip`, …) to enterprise views — they belong to the personal side only. Enterprise views use `enterprise.css` classes (`.panel-doc`, `.doc-masthead`, `.seal-chip`, `.leader-row`, …) and stay on a fixed light paper regardless of the global dark theme.

## Tech Stack (actual versions from `package.json`)

```
Vue 3.5 + TypeScript 6.0 + Vite 8.2 + Pinia 4.0 + Vue Router 5.2
Tailwind CSS 3.4 (custom color system)
ECharts 6.1 + vue-echarts 8.0
Three.js 0.185 + @tresjs/core  (HolographicBackdrop.vue, PrismScene.vue)
Axios 1.19
markdown-it 15 + markdown-it-katex
```

Three.js IS used — but only for canvas holographic/prism backdrops, NOT a full 3D universe (that remains a 数知 carryover to avoid).

## Development Commands (from `zhiyu-frontend/`)

```bash
npm run dev       # Vite dev server on http://localhost:3001, proxies /api → http://localhost:8001
npm run build     # vue-tsc -b && vite build (type-check then bundle)
npm run preview   # Preview production build
```

No test runner, linter, or formatter is configured. Proxy target is **8001** — run the backend on that port (not the uvicorn default 8000).

## Frontend Architecture

### Key Files to Understand First

| File | Why it matters |
|---|---|
| `src/styles/variables.css` | CSS variable definitions for 4 theme modes (dark, light, warm-light, industrial) |
| `src/styles/utilities.css` | 6 panel types, 13 decoration classes — all industrial design utilities (个人侧) |
| `src/styles/animations.css` | Keyframe animations: glow, heartbeat-pulse, confetti, scan-line |
| `src/styles/advanced-animations.css` | `@property` registered CSS vars + ripple/magnetic effects |
| `src/styles/dark-override.css` | `[data-theme="dark"]` overrides for Tailwind utility classes |
| `src/components/common/CosmicBackground.vue` | 3-layer radial-gradient + 80 CSS star particles + data flow lines |
| `src/components/common/StatusCard.vue` | Generic 4-state card — `statusConfig` prop drives visual per domain |
| `src/components/common/HolographicBackdrop.vue` | Three.js holographic canvas layer |
| `src/stores/personal.ts` | Silent Fallback pattern: demo data → API override → silent catch |
| `src/router/index.ts` | All routes (10 enterprise + 14 personal) with `meta.title` and `meta.role` for nav filtering |
| `src/api/client.ts` | Axios instance; response interceptor returns `response.data` directly |
| `DESIGN_SYSTEM.md` | 深空舰桥工业风格完整规范 (v2.0) — applies to **个人侧 only** |
| `DESIGN_SYSTEM_企业侧.md` | 蓝皮书·权威纸面完整规范 (v1.0) — applies to **企业侧 only** |

### CSS Architecture

9 style files, imported **in order by `src/main.ts`** (not `tailwind.css`, which only holds Tailwind directives):

1. `variables.css` — CSS custom properties for 4 theme modes: `:root` (deep space dark), `[data-theme="light"]`, `[data-theme="warm-light"]`, `[data-theme="industrial"]`
2. `base.css` — Reset + global element styles
3. `utilities.css` — Industrial design system (个人侧): `.panel-industrial`, `.panel-bridge`, `.panel-asymmetric`, `.panel-neon`, `.panel-circuit`, `.panel-hazard`, `.rivet`, `.tag-plate`, `.data-segment`, `.holo-overlay`, `.scan-line-fast`, `.beam-divider`, `.nav-chip`, `.sidebar-depth`, `.main-board`, etc.
4. `animations.css` — Keyframes: `glowBrand`, `heartbeat-pulse`, `confetti-burst`, `scaleIn`, `fadeInUp`, `shimmer`, `twinkle`
5. `advanced-animations.css` — `@property`-registered animatable CSS variables, ripple / magnetic / scroll effects
6. `dark-override.css` — Maps Tailwind `.bg-white` etc. under `[data-theme="dark"]`
7. `enterprise.css` — Enterprise 蓝皮书 design system (`.ent-shell`, `.panel-doc`, `.doc-masthead`, `.seal-chip`, `.leader-row`, `.stat-tile`, `.coral-glow`, …). Scoped via `.ent-shell` / `[data-side="enterprise"]`; keeps enterprise on fixed light paper even in dark mode
8. `markdown.css` — Styles for markdown-it rendered content
9. `tailwind.css` — `@tailwind base/components/utilities`

Theme switching: set `data-theme` attribute on `<html>`. The `stores/theme.ts` store manages this.

### Stores & API

- Pinia stores: `app.ts`, `enterprise.ts`, `personal.ts`, `chat.ts`, `theme.ts`
- `client.ts` interceptor returns `response.data` and normalizes errors (backend `detail.error_message` → `detail` → `message`). Callers see the payload, not the Axios envelope.

### Routes

**Enterprise (10)** — 蓝皮书·权威纸面 design language:
```
/enterprise /enterprise/positions /enterprise/positions/:id
/enterprise/positions/:id/diff /enterprise/discovery /enterprise/diagnose
/enterprise/diagnose/batch /enterprise/team /enterprise/forecast /enterprise/graph
```

**Personal (15)** — 深空舰桥工业风格:
```
/personal /personal/profile /personal/explore /personal/match /personal/match/compare
/personal/resume /personal/learning-path /personal/freshness /personal/switch
/personal/growth /personal/chat /personal/center /personal/spectrum
/personal/spectrum/:skill /personal/evolution
```

Note: `/` redirects to `/enterprise` (enterprise is the default landing).

## Key Patterns

### Silent Fallback (Stores)
Initialize with realistic demo data first, override on API success, keep silently on failure. The app launches instantly with full UI — no loading spinners.
```ts
const items = ref<Item[]>(demoItems)  // pre-filled with 12+ realistic entries, not placeholders
async function fetchItems() {
  try { const res = await client.get('/api/items'); if (res) items.value = res }
  catch { /* silent — demo data stays */ }
}
```

### CSS Variable Theming (NOT Tailwind `dark:`)
Theme switched via `data-theme="dark"|"light"|"warm-light"|"industrial"` on `<html>`. Tailwind `dark:` is NOT used — all overrides go through `variables.css` and `dark-override.css`.

### Color System — Semantic Mapping
| Token | Tailwind class | Enterprise meaning | Personal meaning |
|---|---|---|---|
| `brand` (indigo) | `brand-*` | Primary interactions, buttons, links | Same |
| `cyan` | `cyan-*` | "Confirmed" status, emerging skills | "Matched" skills |
| `mint` | `mint-*` | "Verified", healthy skills | "Healthy" skills |
| `amber` | `amber-*` | "Pending verification", warning | "Freshness alert" |
| `rose` | `rose-*` | "Rejected", declining skills | "Missing required skill" |

### SSE Streaming
Server-Sent Events consumed via `fetch` + `ReadableStream` reader → parse `data:` JSON lines → async generator. Used for AI streaming responses in `/personal/chat` (backed by `POST /api/personal/ai/chat`).

## Backend Dependency (condensed — see `../CLAUDE.md` for full detail)

- FastAPI in `../后/`, **MySQL only** (`zhiyv` db). The graph layer was **migrated from Neo4j to MySQL** — `app/graph/repository.py` issues SQLAlchemy queries, Neo4j is dead code. Do not treat Neo4j as a runtime dependency.
- Multi-agent system in `../后/app/agents/`: `MultiAgentSystem` entry → registry / router / executor / `agent_state` (16 static `IntentType`s mapped to API endpoints, not NLP).
- All ~50 `/api/*` endpoints are implemented (no 501s). Dev ports: frontend **3001** → backend **8001**.

## Things NOT to Carry Over from 数知 (`../参考/shuzhi-frontend/`)
- DesktopPet, PetBubble, PetSwitcher (gamification)
- SocraticPanel (learning reflection)
- AnalysisFloatingWindow, DebugPanel
- Avatar/WebRTC SDK components
- Full Three.js 3D universe (minimal canvas backdrop already in use — don't expand it)
- Audio recorder/player composables

## Gotchas

- **个人侧 / 企业侧 are two design projects, both implemented**: industrial utilities belong to personal views only; enterprise views use `enterprise.css` 蓝皮书 classes (see `DESIGN_SYSTEM_企业侧.md`) and stay on fixed light paper regardless of the global dark theme.
- **`../后/docker-compose.yml` is stale** (still Neo4j + Postgres) — not representative of the current MySQL-only app.
- **`../后/pyproject.toml` lists `asyncpg` but the code needs `aiomysql`/`pymysql`** (missing from deps) — install them manually if the DB won't connect.
- **`../后/重构方案.md` is the historical SSOT but the code has diverged** (PostgreSQL→MySQL, Python 3.12, no `skeptic_agent`) — trust the code.
