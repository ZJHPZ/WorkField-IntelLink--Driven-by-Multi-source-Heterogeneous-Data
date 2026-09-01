<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate">MATCH</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">人岗匹配</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ store.skillCount }} SKILLS · {{ store.matches.length }} POSITIONS</span>
      </div>
    </div>

    <!-- 匹配引擎遥测条 —— 技能画像 / 岗位库 / 匹配统计 -->
    <div class="flex items-center gap-2 text-[10px] font-mono px-3 py-1.5 rounded-sm flex-wrap" :style="{border:'1px solid color-mix(in srgb, var(--cyan-500) 30%, transparent)',background:'color-mix(in srgb, var(--cyan-500) 6%, transparent)',color:'var(--cyan-400)'}">
      <span class="w-1.5 h-1.5 rounded-full animate-star-glow shrink-0" style="background:var(--cyan-400)"></span>
      <span class="font-bold tracking-wider">MATCH ENGINE</span>
      <span class="opacity-75">· 技能画像 {{ store.skillCount }} 项</span>
      <span v-if="store.positions.length" class="opacity-75">· 岗位库 {{ store.positions.length }} 条已扫描</span>
      <span class="ml-auto opacity-75">展示匹配 {{ store.matches.length }} 个 · 平均匹配率 {{ avgMatchRate }}%</span>
    </div>

    <!-- 匹配卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 spring-list">
      <div v-for="m in store.matches" :key="m.id"
        class="panel-bridge p-4 cursor-pointer transition-all lift-on-hover shadow-deep relative overflow-hidden"
        :class="selectedMatch?.id===m.id?'panel-neon':''"
        @click="selectedMatch = selectedMatch?.id===m.id ? null : m">
        <div class="relative z-[1] flex items-center gap-3">
          <ProgressRing :percentage="m.matchRate" :size="48" :stroke-width="4" color="url(#ringGradient)" :show-sign="false">
            <span class="text-xs font-bold font-mono data-segment" :style="{color:'var(--text-primary)'}">{{ m.matchRate }}%</span>
          </ProgressRing>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-bold truncate" :style="{color:'var(--text-primary)'}">{{ m.positionName }}</div>
            <div class="text-xs" :style="{color:'var(--text-muted)'}">{{ m.company }}</div>
            <div class="text-xs font-mono text-brand-500 mt-0.5 flex items-center gap-2">
              <span>{{ m.salaryRange }}</span>
              <span v-if="m.techStack" class="opacity-70" :style="{color:'var(--text-muted)'}">{{ m.techStack }} · {{ m.city || '—' }}</span>
              <span v-if="m.requiredSkills?.length" class="ml-auto shrink-0 font-bold" :style="{color:'var(--mint-500)'}">{{ matchedCount(m) }}/{{ m.requiredSkills.length }}</span>
            </div>
            <div class="flex gap-1 mt-1.5 flex-wrap">
              <span v-for="s in m.matchedSkills.slice(0,2)" :key="s" class="text-xs px-1 rounded-sm font-mono" style="background:color-mix(in srgb, var(--mint-500) 08%, transparent);color:var(--mint-500);border:1px solid color-mix(in srgb, var(--mint-500) 20%, transparent)">{{ s }}</span>
              <span v-if="m.missingSkills.length" class="text-xs px-1 rounded-sm font-mono" style="background:color-mix(in srgb, var(--rose-500) 06%, transparent);color:#f87171;border:1px solid color-mix(in srgb, var(--rose-500) 15%, transparent)">-{{ m.missingSkills.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情 -->
    <div v-if="selectedMatch" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="panel-neon panel-circuit p-4 shadow-deep holo-overlay">
        <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
        <div class="relative z-[1]">
          <PanelHeader label="RADAR" :title="selectedMatch.positionName + ' · 多维对比'" margin="sm" />
          <div class="flex items-center gap-2 text-[9px] font-mono mb-2 flex-wrap" :style="{color:'var(--text-muted)'}">
            <span>{{ selectedMatch.techStack || '—' }}</span>
            <span>· {{ selectedMatch.city || '—' }}</span>
            <span v-if="selectedMatch.jdCount">· JD 样本 × {{ selectedMatch.jdCount }}</span>
            <span v-if="selectedMatch.requiredSkills?.length" class="ml-auto">要求技能 {{ selectedMatch.requiredSkills.length }} 项</span>
          </div>
          <MatchRadar :dimensions="radarDimensions" user-name="我的画像" :target-name="selectedMatch.positionName" />
        </div>
      </div>
      <div class="panel-industrial p-4 flex flex-col shadow-deep">
        <h3 class="text-sm font-bold tracking-wide uppercase mb-3" :style="{color:'var(--text-primary)'}">差距分析</h3>
        <div class="mb-3"><div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:var(--mint-500)"><span class="w-1.5 h-1.5 rounded-full bg-mint-500"></span> MATCHED ({{ selectedMatch.matchedSkills.length }}<template v-if="selectedMatch.partialSkills?.length">+{{ selectedMatch.partialSkills.length }}≈</template>)</div><div class="flex flex-wrap gap-1"><span v-for="s in selectedMatch.matchedSkills" :key="s" class="text-xs px-1.5 py-0.5 rounded-sm font-mono" style="background:color-mix(in srgb, var(--mint-500) 06%, transparent);color:var(--mint-500);border:1px solid color-mix(in srgb, var(--mint-500) 20%, transparent)">{{ s }}</span><span v-for="s in selectedMatch.partialSkills" :key="s+'~'" class="text-xs px-1.5 py-0.5 rounded-sm font-mono" style="background:color-mix(in srgb, var(--cyan-500) 06%, transparent);color:var(--cyan-400);border:1px solid color-mix(in srgb, var(--cyan-500) 20%, transparent)" title="近似匹配">≈{{ s }}</span></div></div>
        <div class="mb-3"><div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:#f87171"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> MISSING ({{ selectedMatch.missingSkills.length }})</div><div class="space-y-1.5"><div v-for="s in selectedMatch.missingSkills" :key="s" class="flex justify-between text-xs p-1.5 rounded-sm font-mono" style="border:1px solid color-mix(in srgb, var(--rose-500) 15%, transparent);background:color-mix(in srgb, var(--rose-500) 03%, transparent)"><span style="color:#f87171">{{ s }}</span><span style="color:#f87171">~{{ hoursOf(selectedMatch, s) }}h</span></div></div></div>
        <div v-if="selectedMatch.learningPath?.length" class="mb-3"><div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:var(--brand-400)"><span class="w-1.5 h-1.5 rounded-full bg-brand-500"></span> LEARNING PATH ({{ selectedMatch.learningPath.length }})</div><div class="space-y-1"><div v-for="lp in selectedMatch.learningPath" :key="lp.skill" class="flex items-center gap-2 text-xs p-1.5 rounded-sm font-mono" style="border:1px solid color-mix(in srgb, var(--brand-500) 15%, transparent);background:color-mix(in srgb, var(--brand-500) 03%, transparent)"><span class="font-bold shrink-0" style="color:var(--brand-400)">{{ lp.skill }}</span><span class="opacity-60 shrink-0" :style="{color:'var(--text-muted)'}">{{ lp.duration }}</span><span class="ml-auto opacity-80 truncate max-w-[42%]" :style="{color:'var(--text-muted)'}" :title="lp.resource">{{ lp.resource }}</span><span class="opacity-90 shrink-0 font-bold" style="color:var(--text-primary)">{{ lp.hours }}h</span></div></div></div>
        <div v-if="selectedMatch.requiredSkills?.length" class="mb-3">
          <div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:var(--text-primary)"><span class="w-1.5 h-1.5 rounded-full bg-cyan-500"></span> REQUIRED COVERAGE ({{ matchedCount(selectedMatch) }}/{{ selectedMatch.requiredSkills.length }})</div>
          <div class="flex flex-wrap gap-1">
            <span v-for="r in selectedMatch.requiredSkills" :key="r" class="text-[10px] px-1.5 py-0.5 rounded-sm font-mono" :style="coverageStyle(selectedMatch, r)">{{ coverageMark(selectedMatch, r) }} {{ r }}</span>
          </div>
        </div>
        <div v-if="selectedMatch.topCompanies?.length" class="mb-3">
          <div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:var(--brand-400)"><span class="w-1.5 h-1.5 rounded-full bg-brand-500"></span> TOP EMPLOYERS</div>
          <div class="flex flex-wrap gap-1">
            <span v-for="c in selectedMatch.topCompanies" :key="c.company_name" class="text-[10px] px-1.5 py-0.5 rounded-sm font-mono" style="background:color-mix(in srgb, var(--brand-500) 06%, transparent);color:var(--brand-400);border:1px solid color-mix(in srgb, var(--brand-500) 15%, transparent)">{{ c.company_name }}<span class="opacity-60"> ×{{ c.count }}</span></span>
          </div>
        </div>
        <div class="mt-auto p-3 flex items-center gap-3 panel-dark-zone" style="border:1px solid var(--border-color)">
          <ProgressRing :percentage="selectedMatch.matchRate" :size="40" :stroke-width="4" :color="selectedMatch.matchRate>=80?'#10b981':selectedMatch.matchRate>=65?'#f59e0b':getBrandColor()" :show-sign="false" />
          <div class="text-xs">
            <span :style="{color:'var(--text-primary)'}">当前 {{ selectedMatch.matchRate }}%，补充 {{ selectedMatch.missingSkills.length }} 项可达 </span><span class="text-mint-500 font-bold font-mono">{{ Math.min(selectedMatch.matchRate+selectedMatch.missingSkills.length*8,98) }}%</span>
            <br/><span :style="{color:'var(--text-muted)'}">预计 <b class="text-brand-500 font-mono">{{ estMonths }}</b> 个月 (5h/周)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 三岗位对比表 -->
    <div class="panel-industrial p-4 shadow-deep view-section">
      <PanelHeader label="COMPARE" :title="store.matches.length + ' 岗位横向对比'" color="cyan" margin="sm" />
      <div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr :style="{borderBottom:'2px solid var(--border-color)'}"><th class="text-left py-2 px-3 font-mono tracking-wide" :style="{color:'var(--text-muted)'}">DIM</th><th v-for="m in store.matches" :key="m.id" class="text-center py-2 px-3 font-mono font-bold" :style="{color:'var(--text-primary)'}">{{ m.positionName }}</th></tr></thead><tbody><tr v-for="dim in compRows" :key="dim.label" :style="{borderBottom:'1px solid var(--border-color)'}"><td class="py-2 px-3 font-mono tracking-wide" :style="{color:'var(--text-secondary)'}">{{ dim.label }}</td><td v-for="(v,i) in dim.values" :key="i" class="text-center py-2 px-3 font-mono"><span :class="dim.hi!==undefined&&v===dim.hi?'font-bold text-brand-500':''" :style="{color:dim.hi===undefined||v!==dim.hi?'var(--text-primary)':undefined}">{{ v }}{{ dim.suffix||'' }}</span></td></tr></tbody></table></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import type { JobMatch } from '@/stores/personal'
import ProgressRing from '@/components/common/ProgressRing.vue'
import PanelHeader from '@/components/common/PanelHeader.vue'
import MatchRadar from '@/components/personal/MatchRadar.vue'
import { buildMatchRadarDimensions } from '@/utils/matches'
import { getBrandColor } from '@/utils/color'
import { useScrollReveal } from '@/composables/useScrollReveal'
useScrollReveal()

const store = usePersonalStore()
const selectedMatch = ref<JobMatch|null>(null)

const radarDimensions = computed(() =>
  selectedMatch.value ? buildMatchRadarDimensions(selectedMatch.value) : []
)

// ── 岗位技能覆盖统计（详细缺口分析）──
function matchedCount(m: JobMatch): number { return m.matchedSkills.length + (m.partialSkills?.length || 0) }
function skillStatus(m: JobMatch, s: string): 'matched' | 'partial' | 'missing' {
  if (m.matchedSkills.includes(s)) return 'matched'
  if (m.partialSkills?.includes(s)) return 'partial'
  return 'missing'
}
function coverageMark(m: JobMatch, s: string) { const st = skillStatus(m, s); return st === 'matched' ? '✓' : st === 'partial' ? '≈' : '✗' }
function coverageStyle(m: JobMatch, s: string) {
  const st = skillStatus(m, s)
  return st === 'matched'
    ? { color: 'var(--mint-500)', border: '1px solid color-mix(in srgb, var(--mint-500) 20%, transparent)', background: 'color-mix(in srgb, var(--mint-500) 06%, transparent)' }
    : st === 'partial'
      ? { color: 'var(--cyan-400)', border: '1px solid color-mix(in srgb, var(--cyan-500) 20%, transparent)', background: 'color-mix(in srgb, var(--cyan-500) 06%, transparent)' }
      : { color: '#f87171', border: '1px solid color-mix(in srgb, var(--rose-500) 15%, transparent)', background: 'color-mix(in srgb, var(--rose-500) 03%, transparent)' }
}
const avgMatchRate = computed(() => Math.round(store.matches.reduce((s, m) => s + m.matchRate, 0) / Math.max(store.matches.length, 1)))

const compRows = computed(()=>{const ms=store.matches
  const hoursOfList = (m: JobMatch) => m.learningPath ? m.learningPath.reduce((s,l)=>s+l.hours,0) : m.missingSkills.reduce((s,sk)=>s+estH(sk),0)
  return [
    {label:'匹配率',values:ms.map(m=>m.matchRate),suffix:'%',hi:Math.max(...ms.map(m=>m.matchRate))},
    {label:'已匹配技能',values:ms.map(m=>m.matchedSkills.length),hi:Math.max(...ms.map(m=>m.matchedSkills.length))},
    {label:'近似匹配',values:ms.map(m=>m.partialSkills?.length||0),hi:Math.max(...ms.map(m=>m.partialSkills?.length||0))},
    {label:'缺失技能',values:ms.map(m=>m.missingSkills.length),hi:Math.min(...ms.map(m=>m.missingSkills.length))},
    {label:'补缺学时',values:ms.map(m=>hoursOfList(m)),suffix:'h',hi:Math.min(...ms.map(m=>hoursOfList(m)))},
    {label:'薪资范围',values:ms.map(m=>m.salaryRange)},
    {label:'JD 样本',values:ms.map(m=>m.jdCount??'—')},
  ]})

function estH(s:string):number{const m:Record<string,number>={MLOps:30,AWS:25,'分布式训练':40,Kubernetes:40,'联邦学习':35};return m[s]||25}
/** 逐技能学时：优先取学习路径里的精确学时，缺省回退 estH */
function hoursOf(m: JobMatch, s: string): number { return m.learningPath?.find(lp => lp.skill === s)?.hours ?? estH(s) }
const estMonths = computed(()=>{if(!selectedMatch.value)return'—'
  const t = selectedMatch.value.learningPath
    ? selectedMatch.value.learningPath.reduce((s,l)=>s+l.hours,0)
    : selectedMatch.value.missingSkills.reduce((s,sk)=>s+estH(sk),0)
  return Math.ceil(t/5/4)})

onMounted(()=>{store.fetchMatches();if(store.matches.length) selectedMatch.value=store.matches[0]})
</script>
