<template>
  <div class="spectrum-page space-y-4">
    <!-- ═══ 头部 — 指挥台 + 聚合统计 ═══ -->
    <header class="panel-industrial p-4 noise-texture holo-overlay scan-line-fast view-section">
      <div class="rivet" style="top:8px;left:8px"></div>
      <div class="rivet" style="top:8px;right:8px"></div>
      <div class="rivet" style="bottom:8px;left:8px"></div>
      <div class="rivet" style="bottom:8px;right:8px"></div>
      <div class="relative z-[1]">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <span class="tag-plate" style="color:#a855f7;border-color:#a855f7">SPECTRUM</span>
            <h1 class="text-lg font-bold tracking-wide uppercase truncate" :style="{color:'var(--text-primary)'}">技能信号光谱</h1>
          </div>
          <div class="flex items-center gap-4 text-xs font-mono shrink-0" :style="{color:'var(--text-muted)'}">
            <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-mint-500 animate-star-glow"></span> LIVE</span>
            <span class="hidden md:inline">4 SOURCES</span>
            <span>{{ store.signalDetails.length }} SKILLS</span>
            <span class="data-segment text-sm" :style="{color:'var(--brand-400)'}">{{ totalSignals }} SIGNALS</span>
          </div>
        </div>

        <!-- 聚合统计 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3">
          <div v-for="stat in stats" :key="stat.label" class="stat-box">
            <div class="stat-num" :style="{color:stat.color}">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </header>

    <!-- ═══ 搜索 + 状态筛选 ═══ -->
    <div class="view-section">
      <div class="flex flex-wrap items-center gap-2">
        <input
          v-model="keyword"
          type="text"
          class="filter-input"
          placeholder="搜索技能名 / 类别…"
          :style="{color:'var(--text-primary)'}"
        />
        <button
          v-for="f in statusFilters"
          :key="f.key"
          class="src-chip"
          :class="{ active: statusFilter === f.key }"
          :style="{ '--chip-color': f.color }"
          @click="statusFilter = statusFilter === f.key ? 'all' : f.key"
        >
          <span class="w-1.5 h-1.5 rounded-full" :style="{background:f.color, boxShadow:'0 0 5px '+f.color}"></span>
          {{ f.label }}
        </button>
        <span class="ml-auto text-[10px] font-mono" :style="{color:'var(--text-muted)'}">
          SHOWING {{ filteredSkills.length }} / {{ store.signalDetails.length }}
        </span>
      </div>
    </div>

    <!-- ═══ 技能点卡片网格 ═══ -->
    <div v-if="filteredSkills.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 view-section">
      <button
        v-for="(skill, idx) in filteredSkills"
        :key="skill.skillName"
        class="skill-card panel-bridge p-4 text-left lift-on-hover shadow-deep relative overflow-hidden"
        :style="{ animationDelay: idx * 0.05 + 's' }"
        @click="goDetail(skill)"
      >
        <div class="rivet" style="top:8px;left:8px"></div>
        <div class="rivet" style="top:8px;right:8px"></div>
        <div class="relative z-[1]">
          <!-- 顶部：类别 + 状态 -->
          <div class="flex items-center justify-between gap-2">
            <span class="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider" :style="{color:'var(--text-muted)'}">
              <span class="status-led" :style="{background:statusColor(skill),boxShadow:'0 0 6px '+statusColor(skill)}"></span>
              {{ skill.category }}
            </span>
            <span class="status-pill" :style="{background:statusColor(skill)+'18',color:statusColor(skill),borderColor:statusColor(skill)+'40'}">
              {{ skill.verificationStatus.toUpperCase() }}
            </span>
          </div>

          <!-- 主体：技能名 + 来源微条 vs 置信度环 -->
          <div class="flex items-center justify-between gap-3 mt-2">
            <div class="min-w-0 flex-1">
              <div class="text-base font-bold truncate" :style="{color:'var(--text-primary)'}">{{ skill.skillName }}</div>
              <!-- 来源微条（条形码） -->
              <div class="flex items-end gap-1 mt-2 source-bars">
                <span
                  v-for="src in skill.sources"
                  :key="src.source"
                  class="src-bar"
                  :style="{ height: barHeight(skill, src.source) + 'px', background: sourceColors[src.source] }"
                  :title="sourceLabels[src.source] + ' ×' + getFreq(skill, src.source)"
                />
              </div>
              <div class="text-[9px] font-mono mt-1.5" :style="{color:'var(--text-muted)'}">
                {{ skill.sources.length }} SOURCES · ×{{ skillTotalFreq(skill) }}
              </div>
            </div>
            <ProgressRing
              :percentage="skill.totalConfidence * 100"
              :size="72"
              :stroke-width="6"
              :color="statusColor(skill)"
            >
              <span class="text-base font-mono font-bold leading-none" :style="{color:statusColor(skill)}">
                {{ (skill.totalConfidence * 100).toFixed(0) }}<span class="text-[10px]">%</span>
              </span>
            </ProgressRing>
          </div>

          <!-- 进入详情提示 -->
          <div class="flex items-center justify-end mt-3 text-[9px] font-mono tracking-widest" :style="{color:'var(--text-muted)'}">
            ANALYZE SIGNAL <span class="ml-1" :style="{color:'var(--cyan-400)'}">→</span>
          </div>
        </div>
      </button>
    </div>

    <!-- 空态 -->
    <div v-else class="panel-asymmetric p-8 view-section flex items-center justify-center">
      <div class="text-center">
        <div class="text-3xl opacity-30 animate-glow-pulse mb-2" :style="{color:'var(--brand-500)'}">◇</div>
        <p class="text-xs font-mono" :style="{color:'var(--text-muted)'}">未匹配到技能信号，尝试调整筛选条件</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePersonalStore } from '@/stores/personal'
import type { SignalDetail } from '@/stores/personal'
import ProgressRing from '@/components/common/ProgressRing.vue'
import { useScrollReveal } from '@/composables/useScrollReveal'

const store = usePersonalStore()
const router = useRouter()

const keyword = ref('')
const statusFilter = ref<'all' | 'confirmed' | 'candidate' | 'unverified'>('all')

useScrollReveal()

const sourceLabels: Record<string, string> = { jd: 'JD', github: 'GitHub', arxiv: 'arXiv', standard: 'Standard' }
const sourceColors: Record<string, string> = { jd: 'var(--brand-400)', github: '#06b6d4', arxiv: '#a855f7', standard: '#10b981' }
const statusColors: Record<string, string> = { confirmed: '#10b981', candidate: '#f59e0b', unverified: '#64748b' }
const statusFilters = [
  { key: 'confirmed' as const, label: '已验证', color: '#10b981' },
  { key: 'candidate' as const, label: '候选', color: '#f59e0b' },
  { key: 'unverified' as const, label: '未验证', color: '#64748b' },
]

// ── 聚合统计 ──
const totalSignals = computed(() =>
  store.signalDetails.reduce((sum, s) => sum + s.sources.reduce((ss, src) => ss + src.frequency, 0), 0)
)
const countByStatus = (st: SignalDetail['verificationStatus']) =>
  store.signalDetails.filter(s => s.verificationStatus === st).length
const avgConf = computed(() =>
  store.signalDetails.length
    ? Math.round(store.signalDetails.reduce((a, s) => a + s.totalConfidence, 0) / store.signalDetails.length * 100)
    : 0
)
const stats = computed(() => [
  { label: '已验证', value: countByStatus('confirmed'), color: '#10b981' },
  { label: '候选', value: countByStatus('candidate'), color: '#f59e0b' },
  { label: '未验证', value: countByStatus('unverified'), color: '#64748b' },
  { label: '平均置信度', value: avgConf.value + '%', color: 'var(--brand-400)' },
])

// ── 过滤 ──
const filteredSkills = computed(() =>
  store.signalDetails.filter(s => {
    const kw = keyword.value.trim().toLowerCase()
    const hitKw = !kw || s.skillName.toLowerCase().includes(kw) || s.category.toLowerCase().includes(kw)
    const hitStatus = statusFilter.value === 'all' || s.verificationStatus === statusFilter.value
    return hitKw && hitStatus
  })
)

// ── 工具函数 ──
const globalMaxFreq = computed(() =>
  Math.max(1, ...store.signalDetails.flatMap(s => s.sources.map(x => x.frequency)))
)
function getFreq(s: SignalDetail, key: string) { return s.sources.find(x => x.source === key)?.frequency || 0 }
function skillTotalFreq(s: SignalDetail) { return s.sources.reduce((a, x) => a + x.frequency, 0) }
function barHeight(s: SignalDetail, key: string) { return Math.max(3, (getFreq(s, key) / globalMaxFreq.value) * 28) }
function statusColor(s: SignalDetail) { return statusColors[s.verificationStatus] || '#64748b' }

function goDetail(s: SignalDetail) {
  router.push('/personal/spectrum/' + encodeURIComponent(s.skillName))
}

// 信号数据：挂载时拉取 /api/jd/signals（T5·jd 源），合并进 demo（Silent Fallback）
onMounted(() => { store.fetchSignalDetails() })
</script>

<style scoped>
.spectrum-page { background: var(--bg-primary); }

/* ── 聚合统计 ── */
.stat-box {
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 5px), calc(100% - 5px) 100%, 0 100%);
  position: relative;
}
.stat-num {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.1;
}
.stat-label {
  font-family: 'Courier New', monospace;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ── 筛选输入框 ── */
.filter-input {
  flex: 0 1 220px;
  min-width: 140px;
  padding: 5px 10px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  outline: none;
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%);
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.filter-input::placeholder { color: var(--text-muted); opacity: 0.6; }
.filter-input:focus {
  border-color: var(--brand-500);
  box-shadow: 0 0 10px color-mix(in srgb, var(--brand-500) 20%, transparent);
}

/* ── 状态筛选芯片 ── */
.src-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-family: 'Courier New', monospace;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.25s ease;
  clip-path: polygon(0 3px, 3px 0, 100% 0, 100% calc(100% - 3px), calc(100% - 3px) 100%, 0 100%);
}
.src-chip:hover { color: var(--text-primary); border-color: var(--chip-color); }
.src-chip.active {
  color: var(--chip-color);
  border-color: var(--chip-color);
  box-shadow: 0 0 10px var(--chip-color)40;
}

/* ── 技能卡片 ── */
.skill-card {
  text-align: left;
  cursor: pointer;
  animation: card-in 0.45s cubic-bezier(0.34,1.56,0.64,1) backwards;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}
@keyframes card-in {
  0% { opacity: 0; transform: translateY(12px); }
  100% { opacity: 1; transform: translateY(0); }
}
.skill-card:hover { box-shadow: 0 0 0 1px var(--border-color), 0 8px 24px rgba(0,0,0,0.25); }

.status-led {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  border: 1px solid;
}
.source-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 28px;
}
.src-bar {
  width: 6px;
  border-radius: 1px;
  opacity: 0.85;
  transition: height 0.5s cubic-bezier(0.34,1.56,0.64,1), opacity 0.25s ease;
}
.skill-card:hover .src-bar { opacity: 1; }
</style>
