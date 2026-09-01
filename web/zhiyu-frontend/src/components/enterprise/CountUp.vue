<template>
  <span class="count-up" ref="elRef">{{ display }}</span>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, onUnmounted, watch } from 'vue'

const props = defineProps<{ value: number; duration?: number }>()

// display 仅作首帧渲染值；逐帧数字直写 DOM（textContent），不动响应式——
// 否则过渡切换期间每帧触发组件更新会撞上"更新已卸载组件"崩溃（parentNode null）。
const display = ref(0)
const elRef = ref<HTMLElement | null>(null)
let raf = 0
let disposed = false

/** 数字入账式滚动（easeOutCubic）：报告数值"落定" */
function run(to: number) {
  cancelAnimationFrame(raf)
  const from = display.value
  const dur = props.duration ?? 900
  const t0 = performance.now()
  const tick = (t: number) => {
    if (disposed) return
    const p = Math.min(1, (t - t0) / dur)
    const e = 1 - Math.pow(1 - p, 3)
    const v = Math.round(from + (to - from) * e)
    if (elRef.value) elRef.value.textContent = String(v)
    if (p < 1) raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
}

onMounted(() => run(props.value))
watch(() => props.value, (v) => run(v))
onBeforeUnmount(() => { disposed = true; cancelAnimationFrame(raf) })
onUnmounted(() => cancelAnimationFrame(raf))
</script>
