<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">PATH</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">学习路径</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ targetRole }} · {{ completedSteps }}/{{ store.learningPath.length }} STEPS · {{ totalHours }}H</span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-3 gap-3">
      <div class="panel-bridge p-4 text-center shadow-deep">
        <div class="data-giant text-3xl text-brand-500 data-segment mb-1">{{ completedSteps }}/{{ store.learningPath.length }}</div>
        <div class="text-xs tracking-widest uppercase" :style="{color:'var(--text-muted)'}">Completed</div>
        <div class="h-1.5 mt-2 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full rounded-sm bg-brand-500 transition-all duration-700" :style="{width:overallProgress+'%'}"></div></div>
      </div>
      <div class="panel-bridge p-4 text-center shadow-deep">
        <div class="data-giant text-3xl mb-1 data-segment" :style="{color:'var(--text-primary)'}">{{ totalHours }}<span class="text-lg">h</span></div>
        <div class="text-xs tracking-widest uppercase" :style="{color:'var(--text-muted)'}">Total Hours</div>
        <div class="text-xs font-mono mt-2 text-brand-500">~{{ estWeeks }}周 (5h/周)</div>
      </div>
      <div class="panel-bridge p-4 text-center shadow-deep">
        <div class="data-giant text-3xl text-mint-500 data-segment mb-1">+{{ skillGain }}<span class="text-lg">%</span></div>
        <div class="text-xs tracking-widest uppercase" :style="{color:'var(--text-muted)'}">Match Gain</div>
      </div>
    </div>

    <!-- 时间轴 -->
    <div class="panel-industrial p-5 relative shadow-deep view-section">
      <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
      <PanelHeader label="TIMELINE" title="学习步骤" color="cyan" />
      <div class="relative">
        <div class="absolute left-6 top-0 bottom-0 w-0.5" style="background:linear-gradient(180deg,var(--brand-500),var(--cyan-500),var(--mint-500))"></div>
        <div class="space-y-3 spring-list">
          <div v-for="(step,idx) in store.learningPath" :key="step.id" class="relative pl-14">
            <div class="absolute left-4 -translate-x-1/2 w-8 h-8 flex items-center justify-center text-xs z-10 border-2 transition-all"
              :style="{
                background:step.status==='completed'?'var(--mint-500)':step.status==='in_progress'?'var(--brand-500)':step.status==='available'?'var(--bg-card)':'var(--bg-secondary)',
                borderColor:step.status==='completed'?'var(--mint-400)':step.status==='in_progress'?'var(--brand-400)':step.status==='available'?'var(--brand-400)':'var(--border-color)',
                color:step.status==='locked'?'var(--text-muted)':'white',
                boxShadow:step.status==='in_progress'?'0 0 12px rgba(232,83,108,0.5)':step.status==='completed'?'0 0 10px rgba(16,185,129,0.4)':'none'
              }">
              <span v-if="step.status==='completed'">✓</span><span v-else-if="step.status==='in_progress'">●</span><span v-else class="font-mono">{{ idx+1 }}</span>
            </div>
            <div class="panel-asymmetric p-3 shadow-deep" :class="step.status==='in_progress'?'panel-neon':step.status==='locked'?'opacity-50':''">
              <div class="flex items-start justify-between mb-1.5">
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs px-1.5 py-0 rounded-sm font-mono font-bold"
                      :style="{background:step.status==='completed'?'rgba(16,185,129,0.1)':step.status==='in_progress'?'rgba(232,83,108,0.1)':step.status==='available'?'rgba(6,182,212,0.1)':'rgba(107,114,128,0.1)',color:step.status==='completed'?'var(--mint-500)':step.status==='in_progress'?'var(--brand-500)':step.status==='available'?'var(--cyan-500)':'var(--text-muted)'}">
                      {{ statusLabel(step.status) }}
                    </span>
                    <span class="text-xs" :style="{color:'var(--text-muted)'}">{{ step.skill }}</span>
                  </div>
                  <h3 class="text-sm font-bold mt-1" :style="{color:'var(--text-primary)'}">{{ step.title }}</h3>
                </div>
                <div class="text-right shrink-0"><span class="font-mono text-sm font-bold text-brand-500">{{ step.estimatedHours }}h</span></div>
              </div>
              <div class="p-2 text-xs font-mono" :style="{background:'var(--bg-secondary)',color:'var(--text-secondary)',borderLeft:'2px solid var(--border-color)'}">{{ step.resource }}</div>
              <div v-if="step.status!=='locked'" class="mt-2">
                <div class="h-1.5 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full rounded-sm transition-all duration-700" :class="step.status==='completed'?'bg-mint-500':'bg-brand-500'" :style="{width:step.progress+'%'}"></div></div>
              </div>
              <div class="flex gap-1.5 mt-2" v-if="step.status==='in_progress'"><button @click="continueStep(step)" class="text-xs px-4 py-1.5 font-mono font-bold text-white transition-all hover:scale-105" style="background:var(--brand-500);clip-path:polygon(0 0,calc(100% - 6px) 0,100% 100%,0 100%)">CONTINUE</button></div>
              <div class="flex gap-1.5 mt-2" v-else-if="step.status==='available'"><button @click="startStep(step)" class="text-xs px-4 py-1.5 font-mono font-bold text-white transition-all hover:scale-105" style="background:var(--brand-500);clip-path:polygon(0 0,calc(100% - 6px) 0,100% 100%,0 100%)">START</button></div>
            </div>
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
const targetRole = ref('AI 算法工程师')
const completedSteps = computed(()=>store.learningPath.filter(s=>s.status==='completed').length)
const totalHours = computed(()=>store.learningPath.reduce((s,x)=>s+x.estimatedHours,0))
const overallProgress = computed(()=>store.learningPath.length?Math.round(store.learningPath.reduce((s,x)=>s+x.progress,0)/store.learningPath.length):0)
const estWeeks = computed(()=>Math.ceil(store.learningPath.filter(s=>s.status!=='completed').reduce((s,x)=>s+x.estimatedHours,0)/5))
const skillGain = computed(()=>store.learningPath.filter(s=>s.status==='completed').length*8)
function statusLabel(s:string):string{const m:Record<string,string>={locked:'LOCKED',available:'AVAILABLE',in_progress:'IN PROGRESS',completed:'DONE'};return m[s]||s}
function continueStep(step:any){step.progress=Math.min(100,step.progress+20);if(step.progress>=100){step.status='completed';notify('🎉 学习完成！',`${step.title} 已标记为完成`,'success')}else{notify('📚 继续学习',`${step.title} 进度 ${step.progress}%`,'info')}}
function startStep(step:any){step.status='in_progress';step.progress=5;notify('🚀 开始学习',`${step.title} 已开始`,'success')}
onMounted(()=>store.fetchLearningPath())
</script>
