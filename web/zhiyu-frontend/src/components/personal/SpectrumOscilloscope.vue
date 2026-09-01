<template>
  <div class="scope panel-neon panel-circuit shadow-deep relative overflow-hidden holo-overlay">
    <!-- 铆钉四角 -->
    <div class="rivet" style="top:10px;left:10px;z-index:20"></div>
    <div class="rivet" style="top:10px;right:10px;z-index:20"></div>
    <div class="rivet" style="bottom:10px;left:10px;z-index:20"></div>
    <div class="rivet" style="bottom:10px;right:10px;z-index:20"></div>

    <!-- 蓝图网格背景 -->
    <div class="scope-grid pointer-events-none"></div>

    <!-- ── 面板头部 ── -->
    <div class="relative z-[1] flex items-center justify-between gap-3 px-4 pt-3 pb-2">
      <div class="flex items-center gap-2 min-w-0">
        <span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">OSCILLOSCOPE</span>
        <h3 class="text-sm font-bold tracking-wide uppercase truncate" :style="{color:'var(--text-primary)'}">{{ signal.skillName }}</h3>
      </div>
      <div class="flex items-center gap-3 text-[10px] font-mono shrink-0" :style="{color:'var(--text-muted)'}">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-mint-500 animate-star-glow"></span> LIVE
        </span>
        <span class="hidden md:inline">HOVER TO TRACE</span>
        <span class="status-pill" :style="{background:statusColor(signal)+'18',color:statusColor(signal),borderColor:statusColor(signal)+'40'}">
          {{ signal.verificationStatus.toUpperCase() }}
        </span>
      </div>
    </div>

    <!-- ── CRT 示波屏 ── -->
    <div class="scope-screen relative z-[1] mx-3 mb-1">
      <!-- 屏内光栅格线 -->
      <div class="screen-graticule pointer-events-none"></div>
      <svg :viewBox="`0 0 ${W} ${H}`" class="w-full block" @mousemove="onMove" @mouseleave="onLeave">
        <!-- 参考栅格：中心基线 + 振幅刻度 + 时间刻度 -->
        <line :x1="PAD_L" :x2="W - PAD_R" :y1="TRACK_Y" :y2="TRACK_Y"
              stroke="var(--border-color)" stroke-opacity="0.4" stroke-dasharray="3 4" />
        <line :x1="PAD_L" :x2="W - PAD_R" :y1="TRACK_Y - AMP * 0.5" :y2="TRACK_Y - AMP * 0.5"
              stroke="var(--border-color)" stroke-opacity="0.18" stroke-dasharray="2 6" />
        <line :x1="PAD_L" :x2="W - PAD_R" :y1="TRACK_Y + AMP * 0.5" :y2="TRACK_Y + AMP * 0.5"
              stroke="var(--border-color)" stroke-opacity="0.18" stroke-dasharray="2 6" />
        <line v-for="(tx, i) in timeTicks" :key="'t' + i"
              :x1="tx" :x2="tx" :y1="0" :y2="H"
              stroke="var(--border-color)" stroke-opacity="0.08" />

        <!-- 来源谐波层：每条染色弱波 = 该来源对融合信号的贡献（d 由 rAF 直写，phase 非响应式） -->
        <path
          v-for="src in signal.sources"
          :key="src.source"
          class="scope-src"
          :class="{ hot: hoverSrc === src.source }"
          :d="srcPath(src)"
          :stroke="srcColor(src.source)"
          fill="none"
          stroke-width="1.2"
          :ref="(el) => registerTrace(src.source, el)"
        />

        <!-- 融合波形（4 谐波叠加）：亮主线 + 泛光辉光 -->
        <path class="scope-glow" :d="fusedPath()"
              :stroke="statusColor(signal)"
              fill="none" stroke-width="6" stroke-opacity="0.14" stroke-linecap="round"
              :ref="(el) => registerTrace('fused-glow', el)" />
        <path class="scope-trace" :d="fusedPath()"
              :stroke="statusColor(signal)"
              fill="none" stroke-width="2" stroke-linecap="round"
              :style="{ '--trace-c': statusColor(signal) }"
              :ref="(el) => registerTrace('fused', el)" />

        <!-- 悬浮探针：鼠标悬停 → 竖向光标 + 波形取样点 + 读数 -->
        <g v-if="hoverU !== null" class="scope-cursor">
          <line :x1="hoverX" :x2="hoverX" :y1="0" :y2="H" stroke="#67e8f9" stroke-width="1" stroke-opacity="0.45" />
          <circle :cx="hoverX" :cy="hoverY" r="3.2" :fill="statusColor(signal)" class="scope-probe-dot" />
          <g v-if="hoverLabel" :transform="`translate(${hoverLabel.lx}, ${hoverLabel.ly})`">
            <rect width="94" height="28" fill="#05060f" stroke="#67e8f9" stroke-opacity="0.45" />
            <text x="7" y="12" class="scope-probe" fill="#67e8f9">AMP {{ hoverLabel.amp }}%</text>
            <text x="7" y="23" class="scope-probe" fill="var(--text-muted)">T+{{ hoverLabel.t }}ms</text>
          </g>
        </g>

        <!-- 屏内标签 -->
        <text :x="PAD_L + 8" :y="18" class="scope-tag" :fill="statusColor(signal)">SIG·{{ signal.skillName }}</text>
        <text :x="W - PAD_R - 8" :y="18" text-anchor="end" class="scope-tag" :fill="statusColor(signal)">
          {{ (signal.totalConfidence * 100).toFixed(0) }}%
        </text>
      </svg>

      <!-- CRT 荧光粉扫描线 + 边缘暗角 -->
      <div class="crt-scanlines pointer-events-none"></div>
      <div class="crt-vignette pointer-events-none"></div>
    </div>

    <!-- ── 来源拆解条：hover 提亮对应谐波 ── -->
    <div class="relative z-[1] px-3 pb-1">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div
          v-for="src in orderedSources"
          :key="src.source"
          class="src-card"
          :class="{ hot: hoverSrc === src.source }"
          @mouseenter="hoverSrc = src.source"
          @mouseleave="hoverSrc = null"
        >
          <div class="flex items-center justify-between gap-1">
            <span class="flex items-center gap-1.5 text-[10px] font-bold font-mono uppercase" :style="{color:srcColor(src.source)}">
              <span class="w-1.5 h-1.5 rounded-full" :style="{background:srcColor(src.source),boxShadow:'0 0 5px '+srcColor(src.source)}"></span>
              {{ sourceLabels[src.source] }}
            </span>
            <span class="text-[9px] font-mono" :style="{color:'var(--text-muted)'}">×{{ src.frequency }}</span>
          </div>
          <div class="flex items-baseline justify-between mt-0.5">
            <span class="text-sm font-mono font-bold leading-none" :style="{color:srcColor(src.source)}">
              {{ (src.confidence * 100).toFixed(0) }}<span class="text-[9px]">%</span>
            </span>
            <span class="text-[8px] font-mono tracking-widest" :style="{color:'var(--text-muted)'}">CONF</span>
          </div>
          <div class="h-1 mt-1 src-bar" :style="{background:'var(--bg-secondary)'}">
            <div class="h-full" :style="{width:src.confidence*100+'%',background:srcColor(src.source),boxShadow:'0 0 6px '+srcColor(src.source)}"></div>
          </div>
          <div v-if="src.examples.length" class="flex flex-wrap gap-1 mt-1">
            <span v-for="ex in src.examples.slice(0, 2)" :key="ex" class="ex-chip" :style="{color:srcColor(src.source)}">{{ ex }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 数码管读数 ── -->
    <div class="relative z-[1] px-4 pb-3 pt-1.5 flex items-end justify-between gap-3">
      <div class="min-w-0">
        <div class="text-[9px] font-mono tracking-[0.2em] uppercase" :style="{color:'var(--text-muted)'}">HOVER SOURCE</div>
        <div class="data-readout text-base mt-0.5 truncate" :style="{color: hoverSrc ? srcColor(hoverSrc) : 'var(--text-muted)'}">
          {{ hoverSrc ? sourceLabels[hoverSrc] + ' · ×' + getFreq(hoverSrc) : '— MIX —' }}
        </div>
      </div>
      <div class="text-right shrink-0">
        <div class="text-[9px] font-mono tracking-[0.2em] uppercase" :style="{color:'var(--text-muted)'}">FUSION CONFIDENCE</div>
        <div class="data-giant text-4xl leading-none mt-1" :style="{color:statusColor(signal)}">
          {{ (signal.totalConfidence * 100).toFixed(0) }}<span class="text-lg">%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, onUnmounted, ref } from 'vue'
import { PALETTE } from '@/utils/color'
import type { SignalDetail, SignalSource } from '@/stores/personal'

const props = defineProps<{ signal: SignalDetail }>()

// ── 坐标系统（SVG viewBox 逻辑像素，等比缩放）──
const W = 1000
const H = 320
const PAD_L = 16
const PAD_R = 16
const TRACK_W = W - PAD_L - PAD_R
const TRACK_Y = H / 2           // 中心基线
const AMP = H * 0.34            // 最大半振幅

// ── 四源谐波特征：频率决定波形形状，来源频率占比决定谐波权重 ──
const SRC_PROFILE: Record<string, { freq: number; color: string; amp: number }> = {
  jd:       { freq: 1.6, color: PALETTE.brand, amp: 1.0 },
  github:   { freq: 2.4, color: PALETTE.cyan, amp: 0.9 },
  arxiv:    { freq: 1.1, color: PALETTE.purple, amp: 0.8 },
  standard: { freq: 0.7, color: PALETTE.mint, amp: 0.7 },
}
const sourceLabels: Record<string, string> = { jd: 'JD', github: 'GitHub', arxiv: 'arXiv', standard: 'Standard' }
const statusColors: Record<string, string> = { confirmed: PALETTE.mint, candidate: PALETTE.amber, unverified: '#64748b' }

// ── 相位漂移动画 ──
// phase 故意保持「非响应式」：波形每帧流动是纯视觉，改响应式 ref 会让组件每帧重渲染，
// 在路由过渡（out-in）期间触发"更新已卸载组件"崩溃（parentNode null）。
// rAF 里直接用普通变量重算 path 并 setAttribute 直写 SVG，零响应式扰动。
let phase = 0

// SVG path 元素引用：'fused' / 'fused-glow' + 各来源 source 键
const traceEls = new Map<string, SVGPathElement>()
function registerTrace(key: string, el: unknown) {
  if (el instanceof SVGPathElement) traceEls.set(key, el)
  else traceEls.delete(key)
}

const hoverSrc = ref<string | null>(null)
const hoverU = ref<number | null>(null)
let rafId = 0
let disposed = false

/** 来源按置信度降序 → 拆解条主次分明 */
const orderedSources = computed(() =>
  [...props.signal.sources].sort((a, b) => b.confidence - a.confidence)
)

const timeTicks = computed(() => {
  const t: number[] = []
  for (let x = PAD_L; x <= W - PAD_R; x += 100) t.push(x)
  return t
})

function statusColor(s: SignalDetail) { return statusColors[s.verificationStatus] || '#64748b' }
function srcColor(src: string) { return SRC_PROFILE[src]?.color || '#6b7280' }
function getFreq(src: string) { return props.signal.sources.find(s => s.source === src)?.frequency || 0 }

/** 来源权重 ∝ 该来源频率占比 */
function weight(src: SignalSource) {
  const total = props.signal.sources.reduce((a, x) => a + x.frequency, 0) || 1
  return (src.frequency || 0) / total
}

/** 单来源谐波值（带权重，融合波形用） */
function harmonic(src: SignalSource, u: number) {
  const p = SRC_PROFILE[src.source]
  return p ? weight(src) * p.amp * Math.sin(2 * Math.PI * p.freq * u + phase) : 0
}

/** 最强来源置信度：谐波显示振幅以它为基准归一化 */
const maxSourceConf = computed(() => Math.max(0.01, ...props.signal.sources.map(s => s.confidence)))

/** 每来源相位偏移：4 条谐波错开相位，波形相互可见不重叠 */
const SRC_ORDER = ['jd', 'github', 'arxiv', 'standard']
function srcPhaseOffset(src: string) { return SRC_ORDER.indexOf(src) * 0.55 }

/** 谐波显示波：振幅∝该来源相对置信度（归一化到最强来源），保证所有来源波动清晰可辨 */
function srcWave(src: SignalSource, u: number) {
  const p = SRC_PROFILE[src.source]
  if (!p) return 0
  const amp = src.confidence / maxSourceConf.value
  return amp * p.amp * Math.sin(2 * Math.PI * p.freq * u + phase + srcPhaseOffset(src.source))
}

/** 融合波形值 = 4 谐波叠加 */
function fused(u: number) {
  return props.signal.sources.reduce((a, s) => a + harmonic(s, u), 0)
}

function envAt(u: number) { return 0.5 * (1 - Math.cos(2 * Math.PI * u)) }
function waveY(u: number, val: number) {
  return TRACK_Y - props.signal.totalConfidence * AMP * envAt(u) * val
}

function samplePath(sample: (u: number) => number): string {
  const n = 160
  let d = ''
  for (let k = 0; k <= n; k++) {
    const u = k / n
    const x = PAD_L + u * TRACK_W
    d += (k === 0 ? 'M' : 'L') + x.toFixed(1) + ' ' + waveY(u, sample(u)).toFixed(1)
  }
  return d
}

function fusedPath() { return samplePath(fused) }
function srcPath(src: SignalSource) { return samplePath(u => srcWave(src, u)) }

// ── 悬浮探针：鼠标悬停取样（波形持续流动，探针点跟随实时振幅）──
const maxAmp = computed(() =>
  props.signal.sources.reduce((a, s) => a + weight(s) * (SRC_PROFILE[s.source]?.amp || 0), 0) || 1
)
const hoverX = computed(() => (hoverU.value === null ? 0 : PAD_L + hoverU.value * TRACK_W))
const hoverY = computed(() => (hoverU.value === null ? TRACK_Y : waveY(hoverU.value, fused(hoverU.value))))
const hoverLabel = computed(() => {
  if (hoverU.value === null) return null
  const p = (fused(hoverU.value) / maxAmp.value) * 100
  const lx = hoverX.value > W - PAD_R - 110 ? hoverX.value - 110 : hoverX.value + 14
  const ly = hoverY.value > 48 ? hoverY.value - 34 : hoverY.value + 18
  return { lx, ly, amp: (p >= 0 ? '+' : '−') + Math.abs(Math.round(p)), t: Math.round(hoverU.value * 1000) }
})

/** SVG 内鼠标移动 → 换算为波形采样点 u ∈ [0,1] */
function onMove(e: MouseEvent) {
  const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
  const vx = (e.clientX - rect.left) / rect.width * W
  hoverU.value = Math.min(1, Math.max(0, (vx - PAD_L) / TRACK_W))
}
function onLeave() { hoverU.value = null }

// ── 动画循环：仅相位漂移（波形持续流动，无自动扫描）──
// 每帧重算 path 直写 SVG，避免响应式变更；悬停探针读数在 hoverU 变化时取当前相位，已足够。
function tick() {
  if (disposed) return
  phase += 0.008
  const f = fusedPath()
  traceEls.get('fused')?.setAttribute('d', f)
  traceEls.get('fused-glow')?.setAttribute('d', f)
  for (const src of props.signal.sources) {
    const el = traceEls.get(src.source)
    if (el) el.setAttribute('d', srcPath(src))
  }
  rafId = requestAnimationFrame(tick)
}
onMounted(() => { rafId = requestAnimationFrame(tick) })
onBeforeUnmount(() => { disposed = true; cancelAnimationFrame(rafId) })
onUnmounted(() => { cancelAnimationFrame(rafId) })
</script>

<style scoped>
.scope { background: var(--bg-card); }

/* ── 蓝图网格背景（科技感面板）── */
.scope-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    linear-gradient(rgba(129,140,248,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(129,140,248,0.05) 1px, transparent 1px);
  background-size: 22px 22px;
  background-position: center center;
  mask-image: radial-gradient(130% 100% at 50% 0%, black 30%, transparent 85%);
  -webkit-mask-image: radial-gradient(130% 100% at 50% 0%, black 30%, transparent 85%);
}

/* ── CRT 屏 ── */
.scope-screen {
  background:
    radial-gradient(120% 90% at 50% 0%, rgba(129,140,248,0.06), transparent 60%),
    #05060f;
  border: 1px solid var(--border-color);
  position: relative;
}
[data-theme="light"] .scope-screen,
[data-theme="warm-light"] .scope-screen { background: #06070e; } /* 仪器屏恒为深色 */

/* 屏内光栅格线：细微青色栅格，示波器刻度盘质感 */
.screen-graticule {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(103,232,249,0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(103,232,249,0.055) 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: center center;
}

.crt-scanlines {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0 1px, transparent 1px 3px);
  mix-blend-mode: overlay;
  pointer-events: none;
}
.crt-vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(120% 100% at 50% 50%, transparent 55%, rgba(0,0,0,0.45) 100%);
  pointer-events: none;
}

/* ── 谐波层（4 来源染色波，波动加大后清晰可见）── */
.scope-src {
  opacity: 0.32;
  stroke-width: 1.6;
  transition: opacity 0.3s ease, stroke-width 0.3s ease;
}
.scope-src.hot { opacity: 0.72; stroke-width: 2.4; }

/* ── 融合波形 ── */
.scope-trace {
  filter: drop-shadow(0 0 3px var(--trace-c, currentColor));
  animation: trace-breathe 3s ease-in-out infinite;
}
@keyframes trace-breathe {
  0%, 100% { filter: drop-shadow(0 0 3px var(--trace-c)) brightness(1.15); }
  50%      { filter: drop-shadow(0 0 7px var(--trace-c)) brightness(1.5); }
}

.scope-tag {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  opacity: 0.7;
}

/* ── 悬浮探针 ── */
.scope-probe-dot { filter: drop-shadow(0 0 5px currentColor); }
.scope-probe {
  font-family: 'Courier New', monospace;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  opacity: 0.9;
}

/* ── 来源拆解条 ── */
.src-card {
  padding: 6px 8px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  transition: all 0.25s ease;
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%);
  cursor: default;
}
.src-card:hover, .src-card.hot {
  background: var(--bg-secondary);
  border-color: var(--border-color);
  box-shadow: 0 0 12px rgba(129,140,248,0.15);
}
.src-bar { overflow: hidden; }
.src-bar > div { transition: width 0.6s cubic-bezier(0.34,1.56,0.64,1); }
.ex-chip {
  font-family: 'Courier New', monospace;
  font-size: 8px;
  padding: 0 4px;
  border: 1px solid currentColor;
  opacity: 0.55;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.src-card:hover .ex-chip { opacity: 0.85; }

/* ── 状态胶囊 ── */
.status-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  border: 1px solid;
}
</style>
