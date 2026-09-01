<template>
  <div class="skill-matrix panel-neon panel-circuit p-5 shadow-deep holo-overlay">
    <div class="rivet" style="top:10px;left:10px"></div>
    <div class="rivet" style="top:10px;right:10px"></div>

    <div class="relative z-[1]">
      <!-- 面板头 -->
      <div class="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <PanelHeader label="MATRIX" title="技能遥测矩阵" color="purple" margin="none" />
        <div class="flex items-center gap-3 flex-wrap">
          <span class="flex items-center gap-1.5 text-[9px] font-mono tracking-widest" :style="{color:'var(--text-muted)'}">
            <span class="w-1.5 h-1.5 rounded-full bg-mint-500 animate-star-glow"></span> LIVE
          </span>
          <span class="text-[9px] font-mono tracking-widest" :style="{color:'var(--text-muted)'}">{{ skills.length }} TRACKS</span>
          <span v-for="l in legend" :key="l.key" class="flex items-center gap-1 text-[9px] font-mono" :style="{color:'var(--text-muted)'}">
            <span class="w-1.5 h-1.5 rounded-full" :style="{background:l.color, boxShadow:'0 0 4px '+l.color}"></span>{{ l.label }}
          </span>
        </div>
      </div>

      <!-- 表体（横向窄屏可滚动） -->
      <div class="matrix-scroll">
        <!-- 表头 —— 可排序列点击切换升/降序 -->
        <div class="matrix-head">
          <span class="col-sys" title="STATUS"></span>
          <button class="col-name" :class="{ active: sortKey==='name' }" @click="setSort('name')">SKILL {{ sortIcon('name') }}</button>
          <button class="col-cat" :class="{ active: sortKey==='category' }" @click="setSort('category')">CAT {{ sortIcon('category') }}</button>
          <button class="col-lvl" :class="{ active: sortKey==='level' }" @click="setSort('level')">LVL {{ sortIcon('level') }}</button>
          <button class="col-fresh" :class="{ active: sortKey==='freshness' }" @click="setSort('freshness')">FRESH {{ sortIcon('freshness') }}</button>
          <button class="col-demand" :class="{ active: sortKey==='marketDemand' }" @click="setSort('marketDemand')">DEMAND {{ sortIcon('marketDemand') }}</button>
          <span class="col-signal">SIGNAL</span>
          <span class="col-exp">EXP</span>
        </div>

        <!-- 数据行 -->
        <div v-for="skill in sortedSkills" :key="skill.id" class="matrix-item">
          <div
            class="matrix-row"
            :class="{ expanded: expandedId===skill.id }"
            :style="{ '--row-color': statusColor(skill) }"
            @click="toggleRow(skill.id)"
          >
            <span class="col-sys"><span class="led" :style="ledStyle(skill)"></span></span>
            <span class="col-name">
              <span class="row-name" :style="{ color: statusColor(skill) }">{{ skill.name }}</span>
            </span>
            <span class="col-cat">{{ skill.category }}</span>
            <span class="col-lvl">
              <span class="lvl-gauge">
                <span v-for="i in 4" :key="i" class="seg" :class="{ on: i <= levelRank[skill.level] }"></span>
              </span>
            </span>
            <span class="col-fresh">
              <span class="fresh-val" :style="{ color: freshColor(skill.freshness) }">{{ skill.freshness }}%</span>
            </span>
            <span class="col-demand"><span class="demand-val">{{ skill.marketDemand }}</span></span>
            <span class="col-signal"><span class="signal-mark" :style="signalStyle(skill)">{{ signalMark(skill) }}</span></span>
            <span class="col-exp">{{ skill.yearsOfExperience }}Y</span>
          </div>

          <!-- 展开明细 —— 传感器读数卡 -->
          <Transition name="fade">
            <div v-if="expandedId===skill.id" class="matrix-detail" :style="{ '--row-color': statusColor(skill) }" @click.stop>
              <div class="md-cell">
                <div class="md-label">EMERG</div>
                <div class="md-value" :style="{ color: emergColor(skill.emergence) }">{{ (skill.emergence*100).toFixed(0) }}%</div>
              </div>
              <div class="md-cell">
                <div class="md-label">DECLINE</div>
                <div class="md-value" :style="{ color: declineColor(skill.decline) }">{{ (skill.decline*100).toFixed(0) }}%</div>
              </div>
              <div class="md-cell">
                <div class="md-label">DF</div>
                <div class="md-value">{{ skill.marketDf }}</div>
              </div>
              <div class="md-cell">
                <div class="md-label">CONF</div>
                <div class="md-value">{{ (skill.confidence*100).toFixed(0) }}%</div>
              </div>
              <div class="md-cell">
                <div class="md-label">FIRST SEEN</div>
                <div class="md-value">{{ skill.firstSeen }}</div>
              </div>
              <div class="md-cell md-related">
                <div class="md-label">RELATED POSITIONS</div>
                <div class="md-tags">
                  <span v-for="t in relatedPositions(skill)" :key="t" class="md-tag">{{ t }}</span>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <div v-if="!sortedSkills.length" class="matrix-empty">— NO TRACKS —</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { PALETTE, getBrandColor } from '@/utils/color'
import type { SkillItem } from '@/stores/personal'
import PanelHeader from '@/components/common/PanelHeader.vue'

const props = defineProps<{ skills: SkillItem[] }>()

// ── 状态语义色（与全站一致：健康 mint / 匹配 brand / 预警 amber / 缺失 rose）──
function statusColor(s: SkillItem): string {
  const m: Record<string, string> = {
    healthy: PALETTE.mint,
    matched: getBrandColor(),
    alert: PALETTE.amber,
    missing_high: PALETTE.rose,
    missing_low: PALETTE.roseLight,
  }
  return m[s.status] || '#6b7280'
}
function isMissing(status: string) { return status === 'missing_high' || status === 'missing_low' }

const legend = [
  { key: 'healthy', label: '健康', color: PALETTE.mint },
  { key: 'matched', label: '匹配', color: getBrandColor() },
  { key: 'alert', label: '预警', color: PALETTE.amber },
  { key: 'missing', label: '缺失', color: PALETTE.rose },
]

// ── 状态 LED ──
function ledStyle(s: SkillItem) {
  const c = statusColor(s)
  if (s.status === 'alert') return { background: c, color: c, boxShadow: `0 0 6px ${c}`, animation: 'led-blink 1.2s steps(2,start) infinite' }
  if (isMissing(s.status)) return { background: 'transparent', border: `1.5px solid ${c}`, color: c, boxShadow: `0 0 4px ${c}66` }
  return { background: c, color: c, boxShadow: `0 0 6px ${c}` }
}

// ── 定级 4 段仪表 ──
const levelRank: Record<string, number> = { basic: 1, intermediate: 2, advanced: 3, expert: 4 }

// ── 保鲜度配色 ──
function freshColor(f: number) { return f >= 70 ? PALETTE.mint : f >= 40 ? PALETTE.amber : PALETTE.rose }

// ── 信号趋势（新兴 vs 衰退，优先告警）──
function signalMark(s: SkillItem): string {
  if (s.decline > 0.2) return '▼'
  if (s.emergence > 0.5) return '▲'
  if (s.emergence > 0.25) return '↗'
  return '◆'
}
function signalStyle(s: SkillItem) {
  const c = s.decline > 0.2 ? PALETTE.rose : s.emergence > 0.5 ? PALETTE.mint : s.emergence > 0.25 ? PALETTE.cyan : '#64748b'
  return { color: c, textShadow: `0 0 6px ${c}` }
}
function emergColor(e: number) { return e > 0.5 ? PALETTE.mint : e > 0.25 ? PALETTE.cyan : '#64748b' }
function declineColor(d: number) { return d > 0.2 ? PALETTE.rose : PALETTE.mint }

// ── 排序（点击表头切换）──
type SortKey = 'name' | 'category' | 'level' | 'freshness' | 'marketDemand'
const sortKey = ref<SortKey>('freshness')
const sortDir = ref<1 | -1>(1)
function setSort(k: SortKey) {
  if (sortKey.value === k) sortDir.value = sortDir.value === 1 ? -1 : 1
  else { sortKey.value = k; sortDir.value = 1 }
}
function sortIcon(k: SortKey) { return sortKey.value === k ? (sortDir.value === 1 ? '▲' : '▼') : '' }
const sortedSkills = computed(() => {
  const arr = [...props.skills]
  const d = sortDir.value
  arr.sort((a, b) => {
    if (sortKey.value === 'level') return d * (levelRank[a.level] - levelRank[b.level])
    if (sortKey.value === 'name' || sortKey.value === 'category') return d * a[sortKey.value].localeCompare(b[sortKey.value])
    return d * (a[sortKey.value] - b[sortKey.value])
  })
  return arr
})

// ── 展开明细 ──
const expandedId = ref<string | null>(null)
function toggleRow(id: string) { expandedId.value = expandedId.value === id ? null : id }

// ── 相关岗位（按类别）──
const posMap: Record<string, string[]> = {
  '编程语言': ['全栈开发', '后端工程师', 'AI工程师'],
  'AI/ML': ['AI工程师', 'ML Engineer', '算法工程师'],
  '前端': ['前端开发', '全栈开发'],
  '数据': ['数据分析师', '大数据工程师'],
  'DevOps': ['DevOps工程师', 'SRE'],
  '架构': ['技术总监', '架构师'],
}
function relatedPositions(s: SkillItem): string[] { return posMap[s.category] || ['相关岗位'] }
</script>

<style scoped>
.skill-matrix { position: relative; }

/* ── 表体滚动（窄屏） ── */
.matrix-scroll { overflow-x: auto; }

/* ── 表头 / 行 —— 统一列轨道 ── */
.matrix-head, .matrix-row {
  display: grid;
  grid-template-columns: 30px minmax(0, 1.7fr) minmax(0, 1.1fr) 54px 58px 54px 42px 38px;
  gap: 8px;
  align-items: center;
  min-width: 600px;
  font-family: var(--font-mono);
}

.matrix-head {
  padding: 6px 10px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
  background: color-mix(in srgb, var(--brand-500) 06%, transparent);
}
.matrix-head button {
  font: inherit;
  letter-spacing: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
  padding: 0;
  border: none;
  background: none;
  transition: color 0.2s ease, text-shadow 0.2s ease;
}
.matrix-head button:hover { color: var(--text-primary); text-shadow: 0 0 6px var(--brand-400); }
.matrix-head button.active { color: var(--cyan-400); text-shadow: 0 0 6px var(--cyan-500); }
.matrix-head .col-fresh, .matrix-head .col-demand, .matrix-head .col-exp { text-align: right; }

/* ── 数据行 ── */
.matrix-item { border-bottom: 1px dashed var(--border-color); }
.matrix-row {
  position: relative;
  padding: 7px 10px;
  cursor: pointer;
  transition: background 0.2s ease;
  font-size: 11px;
}
.matrix-row:hover { background: color-mix(in srgb, var(--brand-500) 08%, transparent); }

/* 左侧状态色条（悬停浮现） */
.matrix-row::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 2px;
  background: var(--row-color, var(--brand-500));
  opacity: 0;
  transition: opacity 0.2s ease;
}
.matrix-row:hover::before { opacity: 0.9; }

/* 悬停扫描线 —— 扫过整行 */
.matrix-row::after {
  content: '';
  position: absolute;
  left: 0; right: 0; top: -2px; height: 2px;
  background: linear-gradient(90deg, transparent, var(--row-color, var(--brand-400)), transparent);
  opacity: 0;
  pointer-events: none;
}
.matrix-row:hover::after { animation: row-scan 0.55s linear infinite; }
@keyframes row-scan {
  0%   { top: -2px; opacity: 0; }
  18%  { opacity: 0.8; }
  100% { top: calc(100% + 2px); opacity: 0; }
}

/* ── 单元格 ── */
.col-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-name {
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.matrix-row:hover .row-name { text-shadow: 0 0 8px var(--row-color, var(--brand-400)); }
.col-cat { color: var(--text-muted); font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.col-lvl { display: flex; align-items: center; }
.lvl-gauge { display: inline-flex; gap: 2px; }
.seg {
  width: 11px; height: 6px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: background 0.25s ease, box-shadow 0.25s ease;
}
.seg.on {
  background: linear-gradient(180deg, var(--brand-400), var(--brand-600));
  border-color: transparent;
  box-shadow: 0 0 4px color-mix(in srgb, var(--brand-500) 60%, transparent);
}

.col-fresh, .col-demand { text-align: right; }
.fresh-val, .demand-val { font-weight: 700; font-size: 11px; }
.fresh-val { text-shadow: 0 0 5px currentColor; }
.demand-val { color: var(--text-primary); }

.col-signal { text-align: center; }
.signal-mark { font-size: 12px; font-weight: 700; }
.col-exp { text-align: right; color: var(--text-muted); font-size: 10px; }

/* ── 状态 LED ── */
.led {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
}
@keyframes led-blink { 50% { opacity: 0.25; } }

/* ── 展开明细 ── */
.matrix-detail {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(108px, 1fr));
  gap: 10px;
  padding: 12px 12px 12px 48px;
  margin: 0 10px 10px;
  background: color-mix(in srgb, var(--bg-card) 55%, transparent);
  border: 1px dashed var(--border-color);
  border-left: 2px solid var(--row-color, var(--brand-500));
  font-family: var(--font-mono);
}
.md-label {
  font-size: 8px;
  letter-spacing: 0.18em;
  color: var(--text-muted);
  margin-bottom: 3px;
}
.md-value { font-size: 13px; font-weight: 700; }
.md-related { grid-column: 1 / -1; }
.md-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.md-tag {
  font-size: 9px;
  padding: 2px 7px;
  border: 1px solid color-mix(in srgb, var(--brand-500) 35%, transparent);
  color: var(--brand-400);
  background: color-mix(in srgb, var(--brand-500) 08%, transparent);
  letter-spacing: 0.05em;
}

/* ── 空态 ── */
.matrix-empty {
  min-width: 600px;
  padding: 26px 0;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--text-muted);
}
</style>
