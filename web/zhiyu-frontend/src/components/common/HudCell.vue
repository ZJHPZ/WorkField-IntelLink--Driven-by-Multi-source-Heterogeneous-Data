<template>
  <div class="glass-card rounded-lg px-3 py-2 text-center transition-all duration-500" :class="{ 'animate-glow-pulse': pulse }">
    <div class="flex items-center justify-center gap-1.5">
      <span class="text-sm">{{ icon }}</span>
      <span class="text-base font-bold tabular-nums transition-all duration-700" :class="valueClass">
        <span v-if="valueText">{{ valueText }}</span>
        <span v-else>{{ animatedValue }}</span
        ><span v-if="suffix" class="text-xs">{{ suffix }}</span>
      </span>
      <span v-if="trend !== 0 && !valueText" class="text-xs font-bold" :class="trend>0?'text-mint-500':'text-rose-500'">{{ trend>0?'↑':'↓' }}{{ Math.abs(trend) }}</span>
    </div>
    <div class="text-xs mt-0.5" :style="{color:'var(--text-muted)'}">{{ label }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = withDefaults(defineProps<{
  value: number; prevValue?: number; label: string; icon?: string
  valueClass?: string; suffix?: string; valueText?: string; pulse?: boolean
}>(), { icon:'📊' })

const animatedValue = ref(props.prevValue??0)
const trend = ref(0)

function animateTo(target:number){
  const start=animatedValue.value, diff=target-start
  if(diff===0) return
  trend.value=diff
  const duration=800, startTime=performance.now()
  function step(now:number){const p=Math.min((now-startTime)/duration,1);const e=1-Math.pow(1-p,3);animatedValue.value=Math.round(start+diff*e);if(p<1) requestAnimationFrame(step)}
  requestAnimationFrame(step)
  setTimeout(()=>{trend.value=0},3000)
}

onMounted(()=>{ if(!props.valueText) animateTo(props.value) })
watch(()=>props.value, (v)=>{ if(!props.valueText) animateTo(v) })
</script>
