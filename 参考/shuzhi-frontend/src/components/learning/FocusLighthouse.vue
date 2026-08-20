<template>
  <div class="glass-card rounded-2xl p-5 overflow-hidden relative">
    <h3 class="text-base font-semibold text-space-800 mb-4 flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
      专注灯塔
    </h3>

    <!-- 灯塔可视化 -->
    <div class="relative flex flex-col items-center">
      <!-- 光柱 -->
      <div class="relative w-24 h-48 flex items-end justify-center">
        <!-- 光束主体 -->
        <div
          class="absolute bottom-0 w-16 rounded-t-full transition-all duration-1000 ease-out"
          :style="beamStyle"
        >
          <!-- 光柱内部流光 -->
          <div class="absolute inset-0 rounded-t-full overflow-hidden">
            <div
              class="absolute inset-0 shimmer-effect"
              style="background: linear-gradient(0deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 60%);"
            />
          </div>
          <!-- 顶部光晕 -->
          <div
            class="absolute -top-4 left-1/2 -translate-x-1/2 w-12 h-8 rounded-full blur-xl"
            :style="{ background: beamGlowColor }"
          />
        </div>

        <!-- 灯塔底座 -->
        <div class="absolute bottom-0 w-20 h-3 rounded-full bg-space-800/80 shadow-lg" />

        <!-- 光柱刻度线 -->
        <div class="absolute inset-0 pointer-events-none">
          <div v-for="i in 4" :key="i"
            class="absolute left-0 right-0 border-t border-white/15"
            :style="{ bottom: (i * 25) + '%' }"
          />
        </div>
      </div>

      <!-- 时间指示 -->
      <div class="mt-4 text-center">
        <div class="text-2xl font-extrabold tabular-nums" :class="timeColorClass">
          {{ formattedTime }}
        </div>
        <div class="text-xs text-gray-400 mt-1">
          <template v-if="todayMinutes === 0">开启今日学习之旅</template>
          <template v-else-if="todayMinutes < 30">专注刚刚开始</template>
          <template v-else-if="todayMinutes < 60">进入学习状态</template>
          <template v-else-if="todayMinutes < 120">深度专注中</template>
          <template v-else>已达峰体验</template>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="flex gap-2 mt-4 w-full">
        <button
          @click="$router.push('/chat')"
          class="flex-1 py-2.5 bg-brand-500 text-white rounded-xl text-sm font-medium hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/20 active:scale-[0.98]"
        >
          💬 开始学习
        </button>
        <button
          @click="$router.push('/practice')"
          class="flex-1 py-2.5 border border-brand-200 text-brand-600 rounded-xl text-sm font-medium hover:bg-brand-50 transition-colors"
        >
          🎯 做练习题
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  todayMinutes?: number
}>(), {
  todayMinutes: 0,
})

const formattedTime = computed(() => {
  const m = props.todayMinutes
  if (m < 60) return `${m}min`
  const h = Math.floor(m / 60)
  const remaining = m % 60
  return remaining > 0 ? `${h}h ${remaining}min` : `${h}h`
})

const fillPercent = computed(() => {
  return Math.min((props.todayMinutes / 120) * 100, 100)
})

const beamColor = computed(() => {
  const p = fillPercent.value
  if (p < 25) return '#6366f1'
  if (p < 50) return '#818cf8'
  if (p < 75) return '#a78bfa'
  return '#06b6d4'
})

const beamGlowColor = computed(() => {
  const p = fillPercent.value
  if (p < 25) return 'rgba(99,102,241,0.6)'
  if (p < 50) return 'rgba(129,140,248,0.6)'
  if (p < 75) return 'rgba(167,139,250,0.6)'
  return 'rgba(6,182,212,0.7)'
})

const beamStyle = computed(() => ({
  height: fillPercent.value + '%',
  background: `linear-gradient(to top, ${beamColor.value}, ${beamColor.value}88)`,
  boxShadow: `0 0 30px ${beamGlowColor.value}, 0 0 60px ${beamGlowColor.value}`,
  borderRadius: '999px 999px 0 0',
}))

const timeColorClass = computed(() => {
  const p = fillPercent.value
  if (p < 25) return 'text-brand-600'
  if (p < 50) return 'text-brand-500'
  if (p < 75) return 'text-purple-500'
  return 'text-cyan-500'
})
</script>
