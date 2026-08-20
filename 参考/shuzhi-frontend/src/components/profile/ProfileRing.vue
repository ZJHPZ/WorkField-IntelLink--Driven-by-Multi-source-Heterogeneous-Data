<template>
  <button
    class="relative flex items-center justify-center rounded-full shrink-0 group"
    :style="{ width: size + 'px', height: size + 'px' }"
    @click="$emit('open')"
    @mouseenter="hovering = true"
    @mouseleave="hovering = false"
    title="学习星图"
  >
    <!-- 外层辉光环 (悬停时扩展) -->
    <div
      class="absolute inset-0 rounded-full transition-all duration-500"
      :style="{
        transform: hovering ? 'scale(1.35)' : 'scale(1)',
        opacity: hovering ? 0.3 : 0.12,
        background: `radial-gradient(circle, ${dominantColor} 0%, transparent 70%)`,
      }"
    />

    <!-- 核心脉冲星 -->
    <div
      class="relative z-10 rounded-full transition-all duration-300"
      :style="{
        width: coreSize + 'px',
        height: coreSize + 'px',
        background: `radial-gradient(circle at 35% 35%, white, ${dominantColor} 60%, transparent 100%)`,
        boxShadow: `0 0 ${glowRadius}px ${dominantColor}, 0 0 ${glowRadius * 2}px ${dominantColor}44`,
        animation: `pulsar-breathe ${pulseDuration}s ease-in-out infinite`,
      }"
    />

    <!-- 悬停: 6 颗子星弹出 -->
    <div
      v-for="(d, i) in topDimensions" :key="d.key"
      class="absolute transition-all duration-400 rounded-full"
      :style="starletStyle(d, i, hovering)"
    >
      <!-- 迷你光点 -->
      <div
        class="rounded-full transition-all duration-300"
        :style="{
          width: starletSize(d) + 'px',
          height: starletSize(d) + 'px',
          background: `radial-gradient(circle, ${d.color}88, ${d.color}44)`,
          boxShadow: `0 0 ${3 + d.value / 30}px ${d.color}`,
          opacity: hovering ? 1 : 0,
        }"
      />
    </div>

    <!-- 悬停 Tooltip -->
    <div
      v-if="hovering && dimensions.length"
      class="absolute top-full mt-3 left-1/2 -translate-x-1/2 px-3 py-2 rounded-xl text-[10px] leading-relaxed whitespace-nowrap pointer-events-none z-50 shadow-xl"
      :style="{ background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(99,102,241,0.3)', color: 'var(--text-primary)' }"
    >
      <div v-for="d in dimensions" :key="d.key" class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full shrink-0" :style="{ backgroundColor: d.color }"></span>
        <span style="color: var(--text-secondary);">{{ d.label }}</span>
        <span class="font-bold tabular-nums" :style="{ color: d.color }">{{ d.value }}</span>
      </div>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ProfileDimension } from '@/stores/profileModeling'

const props = withDefaults(defineProps<{
  dimensions: ProfileDimension[]
  size?: number
}>(), { size: 38 })

defineEmits<{ open: [] }>()

const hovering = ref(false)

const coreSize = computed(() => Math.round(props.size * 0.28))
const avgValue = computed(() => {
  if (!props.dimensions.length) return 50
  return props.dimensions.reduce((s, d) => s + d.value, 0) / props.dimensions.length
})
// 均值高 = 脉动快 (0.8s) ; 均值低 = 缓慢呼吸 (2.5s)
const pulseDuration = computed(() => Math.max(0.8, 2.5 - (avgValue.value / 100) * 1.7))
const glowRadius = computed(() => 4 + (avgValue.value / 100) * 10)

// 核心颜色取自最强维度
const dominant = computed(() => {
  if (!props.dimensions.length) return { color: '#6366f1' }
  return props.dimensions.reduce((a, b) => a.value > b.value ? a : b)
})
const dominantColor = computed(() => dominant.value.color)

// 悬停时展示 top 6 维度 (值最高的6个)
const topDimensions = computed(() => {
  return [...props.dimensions].sort((a, b) => b.value - a.value).slice(0, 6)
})

function starletSize(d: ProfileDimension): number {
  return 3 + (d.value / 100) * 5
}

function starletStyle(d: ProfileDimension, i: number, hover: boolean) {
  const count = topDimensions.value.length
  const angle = (i / count) * Math.PI * 2 - Math.PI / 2
  const dist = props.size * 0.7
  const x = Math.cos(angle) * dist
  const y = Math.sin(angle) * dist
  return {
    width: '0px', height: '0px',
    top: '50%', left: '50%',
    transform: hover
      ? `translate(${x}px, ${y}px) scale(1)`
      : 'translate(0, 0) scale(0)',
    transitionDuration: `${300 + i * 50}ms`,
    transitionTimingFunction: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    zIndex: 5,
  }
}
</script>

<style scoped>
@keyframes pulsar-breathe {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.25); opacity: 1; }
}
</style>
