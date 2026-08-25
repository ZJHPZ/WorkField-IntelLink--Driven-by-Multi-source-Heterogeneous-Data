<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate">MATCH</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">人岗匹配</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ store.skillCount }} SKILLS · 3 POSITIONS</span>
      </div>
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
            <div class="text-xs font-mono text-brand-500 mt-0.5">{{ m.salaryRange }}</div>
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
          <MatchRadar :dimensions="radarDimensions" user-name="我的画像" :target-name="selectedMatch.positionName" />
        </div>
      </div>
      <div class="panel-industrial p-4 flex flex-col shadow-deep">
        <h3 class="text-sm font-bold tracking-wide uppercase mb-3" :style="{color:'var(--text-primary)'}">差距分析</h3>
        <div class="mb-3"><div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:var(--mint-500)"><span class="w-1.5 h-1.5 rounded-full bg-mint-500"></span> MATCHED ({{ selectedMatch.matchedSkills.length }})</div><div class="flex flex-wrap gap-1"><span v-for="s in selectedMatch.matchedSkills" :key="s" class="text-xs px-1.5 py-0.5 rounded-sm font-mono" style="background:color-mix(in srgb, var(--mint-500) 06%, transparent);color:var(--mint-500);border:1px solid color-mix(in srgb, var(--mint-500) 20%, transparent)">{{ s }}</span></div></div>
        <div class="mb-3"><div class="text-xs font-bold tracking-wide mb-1 flex items-center gap-1" style="color:#f87171"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> MISSING ({{ selectedMatch.missingSkills.length }})</div><div class="space-y-1.5"><div v-for="s in selectedMatch.missingSkills" :key="s" class="flex justify-between text-xs p-1.5 rounded-sm font-mono" style="border:1px solid color-mix(in srgb, var(--rose-500) 15%, transparent);background:color-mix(in srgb, var(--rose-500) 03%, transparent)"><span style="color:#f87171">{{ s }}</span><span style="color:#f87171">~{{ estH(s) }}h</span></div></div></div>
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
      <PanelHeader label="COMPARE" title="三岗位横向对比" color="cyan" margin="sm" />
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

const compRows = computed(()=>{const ms=store.matches;return [{label:'匹配率',values:ms.map(m=>m.matchRate),suffix:'%',hi:Math.max(...ms.map(m=>m.matchRate))},{label:'已匹配技能',values:ms.map(m=>m.matchedSkills.length),hi:Math.max(...ms.map(m=>m.matchedSkills.length))},{label:'缺失技能',values:ms.map(m=>m.missingSkills.length),hi:Math.min(...ms.map(m=>m.missingSkills.length))},{label:'薪资范围',values:ms.map(m=>m.salaryRange)}]})

function estH(s:string):number{const m:Record<string,number>={MLOps:30,AWS:25,'分布式训练':40,Kubernetes:40,'联邦学习':35};return m[s]||25}
const estMonths = computed(()=>{if(!selectedMatch.value)return'—';const t=selectedMatch.value.missingSkills.reduce((s,sk)=>s+estH(sk),0);return Math.ceil(t/5/4)})

onMounted(()=>{store.fetchMatches();if(store.matches.length) selectedMatch.value=store.matches[0]})
</script>
