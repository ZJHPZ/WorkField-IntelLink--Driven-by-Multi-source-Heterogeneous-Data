<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:#f87171;border-color:#f87171">FRESHNESS</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">技能保鲜中心</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ healthyCount }}/{{ totalCount }} HEALTHY</span>
      </div>
    </div>

    <!-- 灯塔 + 统计 -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <div class="lg:col-span-3 panel-neon p-5 shadow-deep relative overflow-hidden holo-overlay">
        <HolographicBackdrop color="#10b981" :intensity="0.15" :speed="0.6" />
        <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
        <div class="relative z-[1]">
          <div class="flex items-center justify-between mb-4">
            <PanelHeader label="LIGHTHOUSE" title="技能保鲜灯塔" color="rose" margin="none" />
            <div class="text-right"><div class="data-segment text-2xl font-bold" :class="healthPercent>=80?'text-mint-500':healthPercent>=50?'text-amber-500':'text-rose-500'">{{ healthPercent }}%</div><div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ healthyCount }}/{{ totalCount }} HEALTHY</div></div>
          </div>
          <div class="flex items-end justify-center gap-8 px-4" style="height:240px">
            <LighthouseBeacon :percentage="healthPercent" :height="240" />
            <div class="flex flex-col justify-between h-full py-2 relative">
              <div v-for="tick in ticks" :key="tick.value" class="relative flex items-center" :style="{height:(100/ticks.length)+'%'}"
                :title="tick.alertSkills.length ? tick.value + '%: ' + tick.alertSkills.map(a=>a.skillName).join(', ') : tick.value + '% — 无预警'">
                <div class="absolute right-0 w-6 h-px" :style="{background:tick.color}"></div>
                <span class="absolute right-8 text-xs font-mono font-bold" :style="{color:tick.color}">{{ tick.value }}%</span>
                <div v-if="tick.alertSkills.length" class="absolute right-7 w-2.5 h-2.5 rounded-full border-2 border-white" :style="{background:tick.alertSkills[0].urgency==='high'?'#f43f5e':'#f59e0b',boxShadow:'0 0 6px '+(tick.alertSkills[0].urgency==='high'?'rgba(244,63,94,0.5)':'rgba(245,158,11,0.5)')}"></div>
              </div>
            </div>
            <div class="flex items-end gap-1 h-full pb-2">
              <div v-for="cat in categoryBars" :key="cat.name" class="w-6 rounded-t-sm transition-all duration-700 relative cursor-pointer hover:brightness-125 hover:scale-x-110"
                :title="cat.name + ': 健康度 ' + cat.percent + '%'"
                :style="{height:(cat.percent*2)+'px',background:cat.percent>=80?'var(--mint-400)':cat.percent>=50?'#fbbf24':'#fb7185',opacity:0.7}">
                <div class="absolute -bottom-5 left-1/2 -translate-x-1/2 text-xs font-mono whitespace-nowrap" :style="{color:'var(--text-muted)'}">{{ cat.name }}</div>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-center gap-6 mt-4 text-xs font-mono" :style="{color:'var(--text-muted)'}">
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-mint-500"></span> HEALTHY</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full" style="background:#f59e0b"></span> WATCH</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-rose-500"></span> ALERT</span>
          </div>
        </div>
      </div>

      <div class="lg:col-span-2 flex flex-col gap-3">
        <div class="panel-bridge p-4 flex-1 shadow-deep">
          <div class="text-xs font-bold tracking-wide mb-1" :style="{color:'var(--text-muted)'}">HEALTH INDEX</div>
          <div class="data-giant text-4xl font-bold mb-1 data-segment" :class="healthPercent>=80?'text-mint-500':healthPercent>=50?'text-amber-500':'text-rose-500'">{{ healthPercent }}</div>
          <div class="text-xs font-mono" :style="{color:'var(--text-muted)'}"><span v-if="healthPercent>=80">技能体系健康，保持当前节奏</span><span v-else-if="healthPercent>=50">部分技能需关注，建议制定更新计划</span><span v-else>多项技能面临衰退，需立即行动</span></div>
          <div class="mt-3 flex items-center gap-1"><div v-for="i in 12" :key="i" class="flex-1 h-1.5 rounded-sm transition-all" :style="{background:i<=healthyCount?'var(--mint-400)':i<=healthyCount+alertCount?'#f59e0b':'var(--bg-secondary)'}"></div><span class="text-xs font-mono ml-1" :style="{color:'var(--text-muted)'}">{{ totalCount }}</span></div>
        </div>
        <div class="panel-bridge p-4 flex-1 shadow-deep">
          <div class="text-xs font-bold tracking-wide mb-2" :style="{color:'var(--text-muted)'}">HALF-LIFE DIST</div>
          <div class="space-y-2">
            <div v-for="hl in halfLifeDist" :key="hl.label" class="flex items-center gap-2">
              <span class="text-xs font-mono w-16" :style="{color:'var(--text-secondary)'}">{{ hl.label }}</span>
              <div class="flex-1 h-2 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full rounded-sm transition-all duration-700" :style="{width:(hl.count/Math.max(totalCount,1)*100)+'%',background:hl.color}"></div></div>
              <span class="text-xs font-mono font-bold w-6 text-right" :style="{color:'var(--text-secondary)'}">{{ hl.count }}</span>
            </div>
          </div>
        </div>
        <div class="panel-asymmetric p-4" :style="{borderColor:healthPercent>=80?'rgba(16,185,129,0.2)':'rgba(245,158,11,0.2)'}">
          <div class="text-xs font-bold tracking-wide mb-2" :style="{color:'var(--text-primary)'}">RECOMMENDATION</div>
          <p class="text-xs leading-relaxed font-mono" :style="{color:'var(--text-secondary)'}">{{ topSuggestion }}</p>
        </div>
      </div>
    </div>

    <!-- 预警技能 -->
    <div class="panel-industrial p-5 shadow-deep view-section" :class="highUrgencyCount>0?'panel-hazard':''">
      <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
      <div class="flex items-center justify-between mb-4">
        <PanelHeader label="ALERTS" title="预警技能" color="rose" margin="none" />
        <span class="text-xs font-mono px-2.5 py-1 font-bold rounded-sm" :class="highUrgencyCount>0?'bg-rose-500':'bg-amber-500'" style="color:white">{{ alertSkills.length }} ALERTS · {{ highUrgencyCount }} HIGH</span>
      </div>
      <div v-if="alertSkills.length===0" class="text-center py-8"><div class="text-4xl mb-2">✨</div><p class="text-sm font-mono" :style="{color:'var(--text-secondary)'}">ALL SKILLS HEALTHY</p></div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3 spring-list">
        <div v-for="alert in alertSkills" :key="alert.skillName" class="p-4 rounded-sm transition-all lift-on-hover shadow-deep relative overflow-hidden"
          :style="{background:'var(--bg-card)',border:'1px solid '+(alert.urgency==='high'?'rgba(244,63,94,0.3)':'rgba(245,158,11,0.3)'),borderLeft:'3px solid '+(alert.urgency==='high'?'#f43f5e':'#f59e0b')}">
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full shrink-0 mt-1" :class="alert.urgency==='high'?'bg-rose-500':'bg-amber-400'" :style="{boxShadow:'0 0 8px '+(alert.urgency==='high'?'rgba(244,63,94,0.5)':'rgba(245,158,11,0.4)')}"></span>
              <div><h4 class="text-sm font-bold" :style="{color:'var(--text-primary)'}">{{ alert.skillName }}</h4><span class="text-xs font-mono px-1.5 py-0.5 rounded-sm font-bold" :class="alert.urgency==='high'?'bg-rose-500':'bg-amber-500'" style="color:white">{{ alert.urgency==='high'?'HIGH':'MEDIUM' }}</span></div>
            </div>
            <div class="text-right"><div class="data-giant text-lg" :class="alert.urgency==='high'?'text-rose-500':'text-amber-500'">{{ alert.currentFreshness }}%</div><div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">FRESHNESS</div></div>
          </div>
          <div class="mb-3"><div class="flex items-center justify-between text-xs font-mono mb-1"><span :style="{color:'var(--text-muted)'}">HALF-LIFE</span><span :style="{color:'var(--text-secondary)'}">{{ alert.halfLife }}M</span></div>
            <div class="h-2.5 progress-track-dark relative" style="background:var(--bg-secondary)"><div class="h-full rounded-sm transition-all duration-700 absolute" :style="{width:alert.currentFreshness+'%',background:alert.currentFreshness<40?'linear-gradient(90deg,#f43f5e,#fb923c)':'linear-gradient(90deg,#f59e0b,#fbbf24)'}"></div><div class="absolute left-1/2 top-0 bottom-0 w-px bg-white opacity-30"></div></div>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-mono flex items-center gap-1" :style="{color:'var(--text-secondary)'}"><span class="w-1 h-1 rounded-full bg-brand-400"></span> {{ alert.suggestedAction }}</span>
            <button @click="updatePlan(alert)" class="text-xs px-3 py-1.5 font-mono font-bold text-white rounded-sm transition-all hover:scale-105" :class="alert.urgency==='high'?'bg-rose-500':'bg-amber-500'">UPDATE PLAN</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 健康技能 + 时间线 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 view-section">
      <div class="lg:col-span-2 panel-bridge p-5 shadow-deep">
        <div class="flex items-center justify-between mb-4"><div class="flex items-center gap-2"><span class="tag-plate" style="color:var(--mint-400);border-color:var(--mint-500)">HEALTHY</span><h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">健康技能</h3></div><span class="text-xs font-mono px-2 py-1 rounded-sm" style="background:rgba(16,185,129,0.08);color:var(--mint-500);border:1px solid rgba(16,185,129,0.2)">{{ healthySkills.length }} HEALTHY</span></div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 spring-list">
          <div v-for="skill in healthySkills" :key="skill.name" class="p-3 text-center transition-all lift-on-hover rounded-sm relative overflow-hidden group" style="background:rgba(16,185,129,0.02);border:1px solid rgba(16,185,129,0.15)">
            <div class="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-mint-400 to-mint-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="text-sm font-bold mb-0.5" :style="{color:'var(--text-primary)'}">{{ skill.name }}</div>
            <div class="text-xs font-mono mb-1.5" :style="{color:'var(--text-muted)'}">{{ skill.category }}</div>
            <div class="flex items-center justify-center gap-1"><span class="text-xs font-mono font-bold text-mint-500">{{ skill.freshness }}%</span></div>
            <div class="mt-2 h-1 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full rounded-sm bg-mint-400 transition-all duration-700" :style="{width:skill.freshness+'%'}"></div></div>
          </div>
        </div>
      </div>
      <div class="panel-asymmetric p-5 shadow-deep">
        <h3 class="text-sm font-bold tracking-wide uppercase mb-4" :style="{color:'var(--text-primary)'}">保鲜时间线</h3>
        <div class="relative pl-6 space-y-0">
          <div v-for="(event,idx) in timelineEvents" :key="idx" class="relative pb-5 last:pb-0">
            <div v-if="idx<timelineEvents.length-1" class="absolute left-[-18px] top-3 w-px h-full" :style="{background:'linear-gradient(180deg,'+event.color+',transparent)'}"></div>
            <div class="absolute left-[-22px] top-1 w-2.5 h-2.5 rounded-full border-2 border-white" :style="{background:event.color,boxShadow:'0 0 8px '+event.color}"></div>
            <div class="p-3 rounded-sm transition-all lift-on-hover" style="background:rgba(255,255,255,0.01)">
              <div class="flex items-center justify-between mb-1"><span class="text-xs font-mono font-bold" :style="{color:event.color}">{{ event.month }}</span><span class="text-xs px-1.5 py-0.5 rounded-sm font-mono font-bold" :style="{background:event.badgeBg,color:event.badgeColor}">{{ event.badge }}</span></div>
              <p class="text-xs leading-relaxed font-mono" :style="{color:'var(--text-secondary)'}">{{ event.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import { useNotify } from '@/composables/useNotify'
import { useScrollReveal } from '@/composables/useScrollReveal'
import LighthouseBeacon from '@/components/personal/LighthouseBeacon.vue'
import PanelHeader from '@/components/common/PanelHeader.vue'
import HolographicBackdrop from '@/components/common/HolographicBackdrop.vue'
const store = usePersonalStore()
const { show: notify } = useNotify()
useScrollReveal()

const totalCount = computed(()=>store.skills.length)
const healthyCount = computed(()=>store.skills.filter(s=>s.status==='healthy'||s.status==='matched').length)
const alertCount = computed(()=>store.skills.filter(s=>s.status==='alert').length)
const healthPercent = computed(()=>totalCount.value?Math.round((healthyCount.value/totalCount.value)*100):0)
const alertSkills = computed(()=>store.alerts.map(a=>({...a,trendData:Array.from({length:8},(_,i)=>{const d=a.currentFreshness;const decay=(i/7)*(a.urgency==='high'?25:15);return Math.max(5,Math.round(d-decay))})})))
const highUrgencyCount = computed(()=>alertSkills.value.filter(a=>a.urgency==='high').length)
const healthySkills = computed(()=>store.skills.filter(s=>s.status==='healthy'||s.status==='matched').sort((a,b)=>b.freshness-a.freshness))

const ticks = computed(()=>{const r:{value:number;color:string;alertSkills:typeof alertSkills.value}[]=[];for(let v=100;v>=0;v-=25){const color=v>=80?'#10b981':v>=50?'#f59e0b':'#f43f5e';const near=alertSkills.value.filter(a=>{const f=a.currentFreshness;return f>=v-12&&f<v+12});r.push({value:v,color,alertSkills:near})}return r})
const categoryBars = computed(()=>{const cats=new Map<string,{total:number;healthy:number}>();store.skills.forEach(s=>{const c=cats.get(s.category)||{total:0,healthy:0};c.total++;if(s.freshness>=60)c.healthy++;cats.set(s.category,c)});return [...cats.entries()].map(([name,v])=>({name,percent:Math.round((v.healthy/Math.max(v.total,1))*100)}))})
const halfLifeDist = computed(()=>[{label:'<6M',count:store.alerts.filter(a=>a.halfLife<6).length,color:'#f43f5e'},{label:'6-12M',count:store.alerts.filter(a=>a.halfLife>=6&&a.halfLife<12).length,color:'#f59e0b'},{label:'12-18M',count:store.alerts.filter(a=>a.halfLife>=12&&a.halfLife<18).length,color:'#fbbf24'},{label:'>18M',count:store.alerts.filter(a=>a.halfLife>=18).length,color:'#10b981'}])

const timelineEvents = computed(()=>{
  const e:{month:string;color:string;badge:string;badgeBg:string;badgeColor:string;description:string}[]=[]
  const h=alertSkills.value.filter(a=>a.urgency==='high');const m=alertSkills.value.filter(a=>a.urgency==='medium')
  if(h.length)e.push({month:'1 MONTH',color:'#f43f5e',badge:'URGENT',badgeBg:'rgba(244,63,94,0.1)',badgeColor:'#f43f5e',description:`${h.map(a=>a.skillName).join('、')} 保鲜度低于30%，需立即制定学习计划`})
  if(m.length)e.push({month:'3 MONTHS',color:'#f59e0b',badge:'WATCH',badgeBg:'rgba(245,158,11,0.1)',badgeColor:'#f59e0b',description:`${m.map(a=>a.skillName).join('、')} 半衰期临近，建议安排技能更新`})
  e.push({month:'ONGOING',color:'#10b981',badge:'HEALTHY',badgeBg:'rgba(16,185,129,0.1)',badgeColor:'#10b981',description:`${healthySkills.value.slice(0,3).map(s=>s.name).join('、')} 等 ${healthyCount.value} 项技能保鲜度良好`})
  e.push({month:'PLAN',color:'#6366f1',badge:'TODO',badgeBg:'rgba(99,102,241,0.1)',badgeColor:'#6366f1',description:'每季度进行一次技能保鲜度全面审查，建立持续学习机制'})
  return e
})

onMounted(() => { store.fetchSkills(); store.fetchFreshness() })

const topSuggestion = computed(()=>{
  const h=alertSkills.value.filter(a=>a.urgency==='high')
  if(h.length)return `优先处理 ${h[0].skillName} 的衰退风险：${h[0].suggestedAction}。同时关注其余 ${h.length-1} 项高危技能。`
  if(alertSkills.value.length)return `关注 ${alertSkills.value.map(a=>a.skillName).join('、')} 的技能更新，建议在未来 3-6 个月内完成。`
  return '技能体系整体健康！继续保持当前的学习习惯，关注新兴技术趋势。'
})

function updatePlan(alert:any){notify('📋 计划已更新',`已为 ${alert.skillName} 生成保鲜更新计划`,'success')}

</script>
