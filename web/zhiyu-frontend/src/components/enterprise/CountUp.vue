<template>
  <span class="count-up">{{ display }}</span>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{ value: number; duration?: number }>()

const display = ref(0)
let raf = 0

/** 数字入账式滚动（easeOutCubic）：报告数值"落定" */
function run(to: number) {
  cancelAnimationFrame(raf)
  const from = display.value
  const dur = props.duration ?? 900
  const t0 = performance.now()
  const tick = (t: number) => {
    const p = Math.min(1, (t - t0) / dur)
    const e = 1 - Math.pow(1 - p, 3)
    display.value = Math.round(from + (to - from) * e)
    if (p < 1) raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
}

onMounted(() => run(props.value))
watch(() => props.value, (v) => run(v))
onUnmounted(() => cancelAnimationFrame(raf))
</script>
