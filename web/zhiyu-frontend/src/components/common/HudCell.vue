<template>
  <div class="glass-card rounded-lg px-3 py-2 text-center transition-all duration-500" :class="{ 'animate-glow-pulse': pulse }">
    <div class="flex items-center justify-center gap-1.5">
      <span class="text-sm">{{ icon }}</span>
      <span class="text-base font-bold tabular-nums transition-all duration-700" :class="valueClass">
        <span v-if="valueText">{{ valueText }}</span>
        <span v-else ref="valEl">{{ animatedValue }}</span
        ><span v-if="suffix" class="text-xs">{{ suffix }}</span>
      </span>
      <span v-if="trend !== 0 && !valueText" class="text-xs font-bold" :class="trend>0?'text-mint-500':'text-rose-500'">{{ trend>0?'↑':'↓' }}{{ Math.abs(trend) }}</span>
    </div>
    <div class="text-xs mt-0.5" :style="{color:'var(--text-muted)'}">{{ label }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = withDefaults(defineProps<{
  value: number; prevValue?: number; label: string; icon?: string
  valueClass?: string; suffix?: string; valueText?: string; pulse?: boolean
}>(), { icon:'▦' })

const animatedValue = ref(props.prevValue??0)
const valEl = ref<HTMLElement | null>(null)
const trend = ref(0)

// 数字滚动：逐帧值直写 DOM（textContent），不动响应式 animatedValue ——
// 否则过渡切换期间每帧触发组件更新会撞上"更新已卸载组件"崩溃（parentNode null）。
let lastShown = props.prevValue ?? 0
let stepRaf = 0
let stepTimer = 0
let disposed = false

function animateTo(target:number){
  const start=lastShown, diff=target-start
  if(diff===0) return
  trend.value=diff
  const duration=800, startTime=performance.now()
  function step(now:number){
    if(disposed) return
    const p=Math.min((now-startTime)/duration,1)
    const e=1-Math.pow(1-p,3)
    const v=Math.round(start+diff*e)
    lastShown=v
    if(valEl.value) valEl.value.textContent=String(v)
    if(p<1) stepRaf=requestAnimationFrame(step)
  }
  stepRaf=requestAnimationFrame(step)
  stepTimer=window.setTimeout(()=>{ if(!disposed) trend.value=0 },3000)
}

onMounted(()=>{ if(!props.valueText) animateTo(props.value) })
watch(()=>props.value, (v)=>{ if(!props.valueText) animateTo(v) })
onBeforeUnmount(()=>{ disposed=true; cancelAnimationFrame(stepRaf); window.clearTimeout(stepTimer) })
</script>
