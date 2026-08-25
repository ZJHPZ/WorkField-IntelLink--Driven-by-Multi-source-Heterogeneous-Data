<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:#f59e0b;border-color:#f59e0b">GROWTH</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">职业成长轨迹</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ currentLevel.label }} · LV.{{ userLevel }}</span>
      </div>
    </div>

    <!-- 等级进阶 — 进化链 -->
    <div class="panel-neon p-5 shadow-deep relative overflow-hidden holo-overlay">
      <HolographicBackdrop color="#f59e0b" :intensity="0.15" :speed="0.7" />
      <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
      <div class="relative z-[1]">
        <div class="flex items-center justify-between mb-4">
          <PanelHeader label="EVOLUTION" title="职业进化链" color="amber" margin="none" />
          <div class="text-right"><div class="text-sm font-bold text-brand-500">{{ currentLevel.label }}</div><div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">CURRENT</div></div>
        </div>
        <EvolutionChain :levels="chainLevels" :current-level="currentLevelIdx" @level-click="onLevelClick" />
        <!-- 等级详情卡片 -->
        <div class="grid grid-cols-4 gap-3 mt-4 spring-list">
          <div v-for="level in levels" :key="level.key" class="relative p-3 text-center transition-all lift-on-hover"
            :style="{background:level.status==='locked'?'var(--bg-secondary)':'var(--bg-card)',border:'1px solid '+(level.status==='achieved'||level.status==='current'?level.color+'40':'var(--border-color)'),opacity:level.status==='locked'?0.5:1}">
            <div class="h-1.5 progress-track-dark mb-2" style="background:var(--bg-secondary)"><div class="h-full rounded-sm transition-all duration-700" :style="{width:level.progress+'%',background:'linear-gradient(90deg,'+level.color+','+level.glowColor+')'}"></div></div>
            <div class="text-xs font-mono font-bold" :style="{color:level.color}">{{ level.progress }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 时间轴 + 下一等级 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 view-section">
      <div class="panel-industrial p-5 shadow-deep">
        <div class="rivet" style="top:8px;left:8px"></div>
        <PanelHeader label="HISTORY" title="技能增长时间轴" color="cyan" />
        <div class="relative pl-8">
          <div class="absolute left-4 top-0 bottom-0 w-0.5" style="background:linear-gradient(180deg,var(--brand-500),#a855f7,var(--cyan-500),var(--mint-500))"></div>
          <div v-for="(event,idx) in skillTimeline" :key="idx" class="relative pb-5 last:pb-0">
            <div class="absolute left-[-17px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-white" :style="{background:event.color,boxShadow:'0 0 8px '+event.color}"></div>
            <div class="p-3 panel-asymmetric" :style="{borderLeft:'3px solid '+event.color}">
              <div class="flex items-center justify-between mb-1"><span class="text-xs font-mono font-bold" :style="{color:event.color}">{{ event.date }}</span><span class="text-xs px-1.5 py-0.5 rounded-sm font-mono font-bold" :style="{background:event.badgeBg,color:event.badgeColor}">+{{ event.skillsGained }}</span></div>
              <p class="text-xs leading-relaxed mb-1.5" :style="{color:'var(--text-secondary)'}">{{ event.description }}</p>
              <div class="flex flex-wrap gap-1"><span v-for="skill in event.skills" :key="skill" class="text-xs px-1.5 py-0.5 rounded-sm font-mono" :style="{background:event.color+'15',color:event.color}">{{ skill }}</span></div>
              <div class="text-xs mt-1.5 font-mono" :style="{color:'var(--text-muted)'}">累计: <span class="font-bold" :style="{color:'var(--text-primary)'}">{{ event.cumulativeCount }}</span> SKILLS</div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel-bridge p-5 shadow-deep">
        <PanelHeader label="NEXT" :title="nextLevelTitle" color="purple" />
        <div v-if="nextLevel" class="space-y-4">
          <div class="flex items-center gap-3 p-4 panel-asymmetric" :style="{border:'1px solid '+nextLevel.color+'40',background:'linear-gradient(135deg,'+nextLevel.color+'15,'+nextLevel.color+'05)'}">
            <div class="text-3xl">{{ nextLevel.icon }}</div>
            <div><div class="text-base font-bold" :style="{color:nextLevel.color}">{{ nextLevel.label }}</div><div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ nextLevel.skillRequirement }}</div></div>
            <div class="ml-auto text-right"><div class="data-giant text-2xl" :style="{color:nextLevel.color}">{{ nextLevel.progress }}%</div><div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">PROGRESS</div></div>
          </div>
          <div v-if="unmetRequirements.length" class="space-y-1.5">
            <div class="text-xs font-bold tracking-wide flex items-center gap-1" :style="{color:'var(--text-muted)'}"><span class="w-1.5 h-1.5 rounded-full" style="background:#f59e0b"></span>待提升 ({{ unmetRequirements.length }})</div>
            <div v-for="req in unmetRequirements" :key="req.skill" class="flex items-center gap-2 p-2.5 text-xs panel-asymmetric" style="background:color-mix(in srgb, var(--rose-500) 02%, transparent)">
              <span class="font-mono font-bold" :style="{color:'var(--text-primary)'}">{{ req.skill }}</span>
              <span class="font-mono ml-auto" :style="{color:'var(--text-muted)'}">{{ req.currentLevel }} → {{ req.requiredLevel }}</span>
              <div class="w-12 h-1.5 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full rounded-sm bg-brand-gradient" :style="{width:req.progress+'%'}"></div></div>
            </div>
          </div>
          <div class="p-3 text-center text-xs panel-dark-zone" :style="{color:'var(--text-secondary)'}">按当前学习节奏，预计 <span class="font-bold font-mono text-brand-500">{{ estMonthsToNext }}</span> 后达到 {{ nextLevel.label }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import { PALETTE } from '@/utils/color'
import { useScrollReveal } from '@/composables/useScrollReveal'
import EvolutionChain from '@/components/personal/EvolutionChain.vue'
import PanelHeader from '@/components/common/PanelHeader.vue'
import HolographicBackdrop from '@/components/common/HolographicBackdrop.vue'
useScrollReveal()
const store = usePersonalStore()
const userLevel = computed(() => store.growth?.currentLevel ?? 24)

interface LevelDef { key:string;label:string;icon:string;color:string;glowColor:string;skillRequirement:string;progress:number;status:'achieved'|'current'|'upcoming'|'locked' }
const levels = computed<LevelDef[]>(()=>{
  const total=store.skillCount; const expert=store.skills.filter(s=>s.level==='expert'||s.level==='advanced').length
  const defs:LevelDef[]=[
    {key:'junior',label:'初级',icon:'◆',color:'#6b7280',glowColor:'#9ca3af',skillRequirement:'5 SKILLS',progress:100,status:'achieved'},
    {key:'mid',label:'中级',icon:'◈',color:'var(--brand-500)',glowColor:'var(--brand-400)',skillRequirement:'8 SKILLS',progress:Math.min(100,Math.round((total/8)*100)),status:'current'},
    {key:'senior',label:'高级',icon:'▲',color:'#06b6d4',glowColor:'#22d3ee',skillRequirement:'10 SKILLS + 3 EXPERT',progress:Math.min(100,Math.round((expert/3)*100)),status:'upcoming'},
    {key:'expert',label:'专家',icon:'★',color:'#10b981',glowColor:'#34d399',skillRequirement:'12 SKILLS + 5 EXPERT',progress:Math.min(100,Math.round((expert/5)*100)),status:'locked'},
  ]
  if(expert>=5&&total>=12){defs[3].status='current';defs[2].status='achieved';defs[1].status='achieved'}
  else if(expert>=3&&total>=10){defs[2].status='current';defs[1].status='achieved'}
  return defs
})
const currentLevelIdx = computed(()=>levels.value.findIndex(l=>l.status==='current'))
const currentLevel = computed(()=>levels.value[currentLevelIdx.value]||levels.value[0])
// 点选链条节点可聚焦对应等级要求（默认指向下一等级）
const focusedLevelIdx = ref<number | null>(null)
const nextLevel = computed(()=>{
  const i = focusedLevelIdx.value ?? currentLevelIdx.value + 1
  return levels.value[i] || levels.value[levels.value.length - 1]
})
const nextLevelTitle = computed(()=>{
  const l = focusedLevelIdx.value != null ? levels.value[focusedLevelIdx.value] : null
  return l && l.status === 'current' ? `${l.label} · 当前等级要求` : '下一等级要求'
})

// 进化链数据
const chainLevels = computed(() => levels.value.map(l => ({
  level: levels.value.indexOf(l) + 1,
  name: l.label,
  icon: l.icon,
  unlocked: l.status === 'achieved' || l.status === 'current',
  current: l.status === 'current',
  skillCount: store.skillCount,
  requiredCount: parseInt(l.skillRequirement) || 5,
})))
function onLevelClick(node: any) {
  const idx = levels.value.findIndex(l => l.key === node?.key)
  focusedLevelIdx.value = idx >= 0 ? idx : null
}

interface Requirement { skill:string;currentLevel:string;requiredLevel:string;progress:number }
const unmetRequirements = computed<Requirement[]>(()=>[
  {skill:'深度学习',currentLevel:'高级',requiredLevel:'专家',progress:72},
  {skill:'MLOps',currentLevel:'初级',requiredLevel:'高级',progress:38},
  {skill:'系统设计',currentLevel:'中级',requiredLevel:'高级',progress:65},
])
const estMonthsToNext = computed(()=>{const u=unmetRequirements.value.length;return u<=1?'3 MONTHS':u<=2?'6 MONTHS':(u*3)+' MONTHS'})

const demoSkillTimeline = [
  {date:'2022.03',color:'#6b7280',badgeBg:'rgba(107,114,128,0.1)',badgeColor:'#6b7280',skillsGained:3,skills:['Python','SQL','Git'],cumulativeCount:3,description:'毕业后入职，Java后端开发起步'},
  {date:'2023.06',color:'var(--brand-500)',badgeBg:'color-mix(in srgb, var(--brand-500) 10%, transparent)',badgeColor:'var(--brand-500)',skillsGained:2,skills:['Docker/K8s','React'],cumulativeCount:5,description:'转向全栈开发，接触前端和容器化'},
  {date:'2024.03',color:'#06b6d4',badgeBg:'color-mix(in srgb, var(--cyan-500) 10%, transparent)',badgeColor:'#06b6d4',skillsGained:2,skills:['深度学习','NLP'],cumulativeCount:7,description:'AI浪潮下转投机器学习方向'},
  {date:'2024.09',color:'#a855f7',badgeBg:'color-mix(in srgb, var(--purple-500) 10%, transparent)',badgeColor:'#a855f7',skillsGained:3,skills:['TypeScript','系统设计','数据分析'],cumulativeCount:10,description:'系统性提升架构能力和工程化思维'},
  {date:'2025.06',color:'#10b981',badgeBg:'color-mix(in srgb, var(--mint-500) 10%, transparent)',badgeColor:'#10b981',skillsGained:2,skills:['MLOps','Go'],cumulativeCount:12,description:'ML工程化实践，Go语言入门'},
]
const timelineColors = [PALETTE.mint, PALETTE.cyan, PALETTE.purple, PALETTE.amber, PALETTE.rose]
// 真实 /api/personal/growth.timeline 覆盖 demo（Silent Fallback）
const skillTimeline = computed(() => {
  const real = store.growth?.timeline
  if (real?.length) {
    return real.map((ev, i) => {
      const c = timelineColors[i % timelineColors.length]
      return {
        date: String(ev.date).slice(0, 10),
        color: c, badgeBg: c + '1a', badgeColor: c,
        skillsGained: ev.skillsGained, skills: ev.skills,
        cumulativeCount: ev.cumulativeCount, description: ev.description,
      }
    })
  }
  return demoSkillTimeline
})

onMounted(() => { store.fetchSkills(); store.fetchGrowth() })
</script>
