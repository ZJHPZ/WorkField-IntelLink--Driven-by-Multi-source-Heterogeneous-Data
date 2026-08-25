<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">SWITCH</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">转行可行性分析</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ fromRole }} → {{ toRole }}</span>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- 选择器 -->
      <div class="lg:col-span-2 space-y-4">
        <div class="panel-bridge p-5 shadow-deep">
          <PanelHeader label="FROM/TO" title="转行方向" />
          <div><label class="text-xs font-bold tracking-wide block mb-1.5" :style="{color:'var(--text-muted)'}">CURRENT</label><select v-model="fromRole" class="w-full px-3 py-2.5 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option v-for="r in allRoles" :key="r" :value="r">{{ r }}</option></select></div>
          <div class="flex justify-center my-3"><span class="w-8 h-8 flex items-center justify-center text-lg font-bold rounded-sm" style="background:linear-gradient(135deg,color-mix(in srgb, var(--brand-500) 10%, transparent),color-mix(in srgb, var(--purple-500) 10%, transparent))">↓</span></div>
          <div><label class="text-xs font-bold tracking-wide block mb-1.5" :style="{color:'var(--text-muted)'}">TARGET</label><select v-model="toRole" class="w-full px-3 py-2.5 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option v-for="r in allRoles.filter(x=>x!==fromRole)" :key="r" :value="r">{{ r }}</option></select></div>
          <button @click="runAnalysis" :disabled="isAnalyzing" class="w-full mt-4 py-2.5 text-xs font-mono font-bold text-white transition-all hover:scale-105 disabled:opacity-60 disabled:cursor-wait" :class="isAnalyzing?'animate-pulse-slow':''" style="background:linear-gradient(135deg,var(--brand-600),var(--brand-500));clip-path:polygon(0 0,calc(100% - 10px) 0,100% 100%,0 100%)">{{ isAnalyzing?'ANALYZING...':'RUN ANALYSIS' }}</button>
        </div>
        <div class="panel-asymmetric p-4">
          <div class="text-xs font-bold tracking-wide mb-2" :style="{color:'var(--text-muted)'}">QUICK PRESETS</div>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="p in presets" :key="p.label" class="text-xs px-3 py-1.5 font-mono border transition-all hover:border-brand-400" :style="{color:'var(--text-secondary)',borderColor:'var(--border-color)'}" @click="fromRole=p.from;toRole=p.to">{{ p.label }}</button>
          </div>
        </div>
      </div>

      <!-- 仪表盘 -->
      <div class="lg:col-span-3 panel-neon holo-overlay scan-line-fast p-5 shadow-deep relative overflow-hidden">
        <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
        <div class="relative z-[3]">
          <PanelHeader label="GAUGE" title="可行性仪表盘" color="cyan" />
          <div class="flex items-center gap-6">
            <div class="relative shrink-0" style="width:160px;height:160px">
              <svg viewBox="0 0 160 160" class="w-full h-full -rotate-90"><circle cx="80" cy="80" r="65" fill="none" stroke="var(--bg-secondary)" stroke-width="14"/><circle cx="80" cy="80" r="65" fill="none" :stroke="feasibilityColor" stroke-width="14" stroke-linecap="round" :stroke-dasharray="(2*Math.PI*65)" :stroke-dashoffset="(2*Math.PI*65*(1-feasibilityScore/100))" class="transition-all duration-1000" style="filter:drop-shadow(0 0 10px currentColor)"/></svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center"><div class="data-segment text-4xl font-bold" :style="{color:feasibilityColor}">{{ feasibilityScore }}</div><div class="text-xs font-mono tracking-widest mt-1" :style="{color:'var(--text-muted)'}">FEASIBILITY</div><div class="text-xs mt-1 px-2 py-0.5 rounded-sm font-mono font-bold" :style="{background:feasibilityBadgeBg,color:feasibilityColor}">{{ feasibilityLabel }}</div></div>
            </div>
            <div class="flex-1 grid grid-cols-2 gap-2">
              <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--mint-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--mint-500) 10%, transparent)"><div class="data-giant text-xl text-mint-500">{{ totalOverlap }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">TRANSFER</div></div>
              <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--rose-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--rose-500) 10%, transparent)"><div class="data-giant text-xl text-rose-500">{{ totalGap }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">NEW SKILLS</div></div>
              <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--brand-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--brand-500) 10%, transparent)"><div class="data-giant text-xl text-brand-500">{{ estimatedMonths }}M</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">EST. TIME</div></div>
              <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--cyan-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--cyan-500) 10%, transparent)"><div class="data-giant text-xl text-cyan-500">{{ marketDemand }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">DEMAND</div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 技能重叠 + 韦恩图 -->
    <div class="panel-industrial panel-circuit p-5 shadow-deep view-section">
      <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
      <div class="relative z-[1]">
        <PanelHeader label="OVERLAP" title="技能重叠分析 · Jaccard {{ jaccardSimilarity }}%" color="mint" />
        <div class="flex flex-col lg:flex-row items-center gap-6">
          <div class="shrink-0 relative" style="width:300px;height:240px">
            <svg viewBox="0 0 300 240" class="w-full h-full">
              <circle cx="100" cy="120" r="70" fill="color-mix(in srgb, var(--brand-500) 04%, transparent)" stroke="var(--brand-400)" stroke-width="2" stroke-dasharray="6 3" opacity="0.6"/>
              <circle cx="200" cy="120" r="70" fill="color-mix(in srgb, var(--cyan-500) 04%, transparent)" stroke="#06b6d4" stroke-width="2" stroke-dasharray="6 3" opacity="0.6"/>
              <clipPath id="c2c"><circle cx="200" cy="120" r="70"/></clipPath>
              <circle cx="100" cy="120" r="70" fill="color-mix(in srgb, var(--mint-500) 08%, transparent)" clip-path="url(#c2c)"/>
              <text v-for="(s,i) in overlapSkills.slice(0,4)" :key="'o'+i" :x="150" :y="115+(i-(Math.min(overlapSkills.length,4)-1)/2)*15" text-anchor="middle" font-size="10" font-weight="bold" fill="#10b981" font-family="monospace">{{ s }}</text>
              <text v-for="(s,i) in fromOnlySkills" :key="'f'+i" :x="60" :y="110+(i-(fromOnlySkills.length-1)/2)*14" text-anchor="middle" font-size="9" fill="var(--brand-400)" font-family="monospace">{{ s }}</text>
              <text v-for="(s,i) in toOnlySkills" :key="'t'+i" :x="240" :y="110+(i-(toOnlySkills.length-1)/2)*14" text-anchor="middle" font-size="9" fill="#06b6d4" font-family="monospace">{{ s }}</text>
              <text x="100" y="215" text-anchor="middle" font-size="10" font-weight="bold" fill="var(--text-secondary)" font-family="monospace">{{ fromRole }}</text>
              <text x="200" y="215" text-anchor="middle" font-size="10" font-weight="bold" fill="var(--text-secondary)" font-family="monospace">{{ toRole }}</text>
            </svg>
          </div>
          <div class="flex-1 grid grid-cols-2 gap-3">
            <div class="panel-asymmetric p-3">
              <div class="text-xs font-bold tracking-wide mb-2 flex items-center gap-1" style="color:var(--mint-500)"><span class="w-1.5 h-1.5 rounded-full bg-mint-500"></span>可迁移 ({{ overlapSkills.length }})</div>
              <div class="space-y-1"><div v-for="s in overlapSkills" :key="s" class="text-xs font-mono p-1.5 rounded-sm flex items-center gap-2" style="background:color-mix(in srgb, var(--mint-500) 04%, transparent);color:var(--mint-500);border:1px solid color-mix(in srgb, var(--mint-500) 15%, transparent)"><span class="w-1 h-1 rounded-full bg-mint-500"></span>{{ s }}</div></div>
            </div>
            <div class="panel-asymmetric p-3">
              <div class="text-xs font-bold tracking-wide mb-2 flex items-center gap-1" style="color:#f87171"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>需新学 ({{ toOnlySkills.length }})</div>
              <div class="space-y-1"><div v-for="(s,i) in toOnlySkills" :key="s" class="text-xs font-mono p-1.5 rounded-sm flex items-center gap-2" style="background:color-mix(in srgb, var(--rose-500) 03%, transparent);color:#f87171;border:1px solid color-mix(in srgb, var(--rose-500) 15%, transparent)"><span class="w-1 h-1 rounded-full" :style="{background:i===0?'#f43f5e':'#f59e0b'}"></span>{{ s }} <span class="ml-auto" :style="{color:'var(--text-muted)'}">{{ estimatedHoursPerSkill[i]||'2-3月' }}</span></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分阶段路径 -->
    <div class="panel-bridge p-5 shadow-deep view-section">
      <PanelHeader label="PLAN" title="建议转行路径" color="purple" />
      <div class="relative pl-8">
        <div class="absolute left-4 top-0 bottom-0 w-0.5" style="background:linear-gradient(180deg,var(--brand-500),#a855f7,var(--cyan-500))"></div>
        <div v-for="(phase,idx) in transitionPhases" :key="idx" class="relative pb-6 last:pb-0">
          <div class="absolute left-[-17px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white" :style="{background:phase.color,boxShadow:'0 0 10px '+phase.color}"></div>
          <div class="p-4 panel-asymmetric shadow-deep" :style="{borderLeft:'3px solid '+phase.color}">
            <div class="flex items-center gap-2 mb-2"><span class="text-xs px-2 py-0.5 rounded-sm font-mono font-bold text-white" :style="{background:phase.color}">PHASE {{ idx+1 }}</span><span class="text-sm font-bold" :style="{color:'var(--text-primary)'}">{{ phase.title }}</span><span class="text-xs font-mono ml-auto" :style="{color:'var(--text-muted)'}">{{ phase.duration }}</span></div>
            <p class="text-xs leading-relaxed mb-2" :style="{color:'var(--text-secondary)'}">{{ phase.description }}</p>
            <div class="flex flex-wrap gap-1"><span v-for="tag in phase.tags" :key="tag" class="text-xs px-2 py-0.5 font-mono border rounded-sm" :style="{color:'var(--text-secondary)',borderColor:'var(--border-color)'}">{{ tag }}</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import { useNotify } from '@/composables/useNotify'
import { useScrollReveal } from '@/composables/useScrollReveal'
import PanelHeader from '@/components/common/PanelHeader.vue'
const store = usePersonalStore()
const { show: notify } = useNotify()
useScrollReveal()
const isAnalyzing = ref(false)
function runAnalysis(){
  isAnalyzing.value=true
  setTimeout(()=>{isAnalyzing.value=false;notify('▶ 分析完成',`${fromRole.value} → ${toRole.value} 可行性评分: ${feasibilityScore.value}`,'success')},1500)
}

const allRoles = ['Java后端','AI工程师','大数据工程师','AI产品经理','数据架构师','全栈开发','前端开发','ML Engineer']
const fromRole = ref('Java后端')
const toRole = ref('大数据工程师')
const presets = [
  {label:'Java→大数据',from:'Java后端',to:'大数据工程师'},{label:'后端→AI PM',from:'Java后端',to:'AI产品经理'},
  {label:'后端→数据架构',from:'Java后端',to:'数据架构师'},{label:'前端→全栈',from:'前端开发',to:'全栈开发'},
]

const currentOption = computed(()=>store.switchOptions.find(o=>o.targetRole===toRole.value)||store.switchOptions[0])
const feasibilityScore = computed(()=>currentOption.value?.transferabilityScore||0)
const totalOverlap = computed(()=>currentOption.value?.skillOverlap?.length||0)
const totalGap = computed(()=>currentOption.value?.skillGaps?.length||0)
const estimatedMonths = computed(()=>currentOption.value?.estimatedTransitionMonths||6)
const marketDemand = computed(()=>currentOption.value?.marketDemand||0)
const overlapSkills = computed(()=>currentOption.value?.skillOverlap||[])
const toOnlySkills = computed(()=>currentOption.value?.skillGaps||[])
const jaccardSimilarity = computed(()=>{const o=overlapSkills.value.length;const t=o+toOnlySkills.value.length;return t?Math.round((o/t)*100):0})
const feasibilityColor = computed(()=>feasibilityScore.value>=70?'#10b981':feasibilityScore.value>=40?'#f59e0b':'#f43f5e')
const feasibilityLabel = computed(()=>feasibilityScore.value>=70?'FEASIBLE':feasibilityScore.value>=40?'PLAN NEEDED':'DIFFICULT')
const feasibilityBadgeBg = computed(()=>feasibilityScore.value>=70?'color-mix(in srgb, var(--mint-500) 10%, transparent)':feasibilityScore.value>=40?'color-mix(in srgb, var(--amber-500) 10%, transparent)':'color-mix(in srgb, var(--rose-500) 10%, transparent)')
const fromOnlySkills = ['Java','Spring Boot','MyBatis','SQL','Linux','Git'].filter(s=>!overlapSkills.value.includes(s)).slice(0,3)
const estimatedHoursPerSkill = ['3-4个月','2-3个月','1-2个月','2-3个月','1-2个月']

const transitionPhases = computed(()=>{
  const phases:{color:string;title:string;duration:string;description:string;tags:string[]}[]=[]
  const overlap=overlapSkills.value;const gaps=toOnlySkills.value;const hg=Math.ceil(gaps.length/2)
  phases.push({color:'#10b981',title:'巩固可迁移技能',duration:`${Math.ceil(estimatedMonths.value*0.2)}M`,description:`强化 ${overlap.slice(0,3).join('、')} 在目标场景下的应用`,tags:overlap.slice(0,3)})
  if(gaps.length){phases.push({color:'#f59e0b',title:'补齐核心缺失',duration:`${Math.ceil(estimatedMonths.value*0.5)}M`,description:`重点学习 ${gaps.slice(0,hg).join('、')}`,tags:gaps.slice(0,hg)})}
  if(gaps.length>hg){phases.push({color:'var(--brand-500)',title:'拓展辅助技能',duration:`${Math.ceil(estimatedMonths.value*0.2)}M`,description:`学习 ${gaps.slice(hg).join('、')}，完善能力矩阵`,tags:gaps.slice(hg)})}
  phases.push({color:'#06b6d4',title:'实战验证与求职',duration:`${Math.ceil(estimatedMonths.value*0.1)||1}M`,description:'完成2-3个项目，更新简历并开始投递',tags:['项目实战','简历优化','面试准备']})
  return phases
})

onMounted(() => { store.fetchSwitchOptions() })
</script>
