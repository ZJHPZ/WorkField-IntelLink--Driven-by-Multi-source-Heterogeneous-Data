<template>
  <div class="glass-card rounded-2xl p-5">
    <h3 class="text-base font-semibold text-space-800 mb-4 flex items-center gap-2">
      <img :src="iconLiquid" class="flow-title-icon" alt="" />
      心流状态
    </h3>

    <!-- 波浪可视化区 -->
    <div class="relative h-16 mb-4 rounded-xl overflow-hidden bg-gray-50">
      <!-- 波浪背景 -->
      <div class="absolute inset-0 opacity-30">
        <div class="absolute bottom-0 left-0 right-0 h-full"
          :class="waveColorClass"
          :style="waveMaskStyle">
        </div>
      </div>
      <!-- 中心文字 -->
      <div class="absolute inset-0 flex items-center justify-center">
        <span class="text-sm font-semibold" :class="flowTextColor">{{ flowLabel }}</span>
      </div>
    </div>

    <!-- 滑动条 -->
    <div class="relative h-2.5 bg-gray-100 rounded-full mb-3 overflow-hidden">
      <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
        :style="{ width: flowPercent + '%' }"
        :class="flowBarClass" />
      <div class="absolute top-1/2 -translate-y-1/2 transition-all duration-700"
        :style="{ left: `calc(${flowPercent}% - 10px)` }">
        <div class="w-5 h-5 rounded-full border-[3px] border-white shadow-lg transition-all duration-500"
          :class="dotClass" />
      </div>
    </div>

    <!-- 标签 -->
    <div class="flex justify-between text-[10px] text-gray-400 mb-3 px-0.5">
      <span>😴 无聊</span>
      <span>🎯 专注</span>
      <span>😤 挫败</span>
    </div>

    <!-- 指标 -->
    <div class="grid grid-cols-3 gap-2 text-center">
      <div class="bg-brand-50 rounded-xl p-2.5">
        <div class="text-lg font-bold text-brand-700 tabular-nums">78<sup class="text-xs">%</sup></div>
        <div class="text-[10px] text-gray-400">参与度</div>
      </div>
      <div class="bg-mint-50 rounded-xl p-2.5">
        <div class="text-lg font-bold text-mint-600 tabular-nums">82<sup class="text-xs">%</sup></div>
        <div class="text-[10px] text-gray-400">难度匹配</div>
      </div>
      <div class="bg-amber-50 rounded-xl p-2.5">
        <div class="text-lg font-bold text-amber-600 tabular-nums">65<sup class="text-xs">%</sup></div>
        <div class="text-[10px] text-gray-400">完成率</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import iconLiquid from '@/assets/icons/blue/liquid-svgrepo-com.svg'

const props = withDefaults(defineProps<{
  state?: 'flow' | 'engaged' | 'bored' | 'frustrated'
}>(), { state: 'engaged' })

const flowMap: Record<string, { percent: number; wave: string; bar: string; dot: string; label: string; textColor: string }> = {
  flow: {
    percent: 85, wave: 'bg-mint-500', bar: 'bg-mint-500', dot: 'bg-mint-600',
    label: '✨ 你已进入心流状态！学习效率最佳',
    textColor: 'text-mint-700',
  },
  engaged: {
    percent: 62, wave: 'bg-brand-500', bar: 'bg-brand-500', dot: 'bg-brand-600',
    label: '📖 保持专注，继续前进',
    textColor: 'text-brand-700',
  },
  bored: {
    percent: 28, wave: 'bg-amber-500', bar: 'bg-amber-500', dot: 'bg-amber-600',
    label: '💤 内容偏简单，建议提升难度',
    textColor: 'text-amber-700',
  },
  frustrated: {
    percent: 92, wave: 'bg-rose-500', bar: 'bg-rose-500', dot: 'bg-rose-600',
    label: '😰 内容偏难，建议回顾前置知识',
    textColor: 'text-rose-700',
  },
}

const f = computed(() => flowMap[props.state] || flowMap.engaged)
const flowPercent = computed(() => f.value.percent)
const waveColorClass = computed(() => f.value.wave)
const flowBarClass = computed(() => f.value.bar)
const dotClass = computed(() => f.value.dot)
const flowLabel = computed(() => f.value.label)
const flowTextColor = computed(() => f.value.textColor)

// Simple sine wave SVG for the wave effect
const waveSvg = computed(() => {
  const color = f.value.bar === 'bg-mint-500' ? '16b981' : f.value.bar === 'bg-brand-500' ? '6366f1' : f.value.bar === 'bg-amber-500' ? 'f59e0b' : 'f43f5e'
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none"><path d="M0,60 C200,10 400,110 600,60 C800,10 1000,110 1200,60 L1200,120 L0,120 Z" fill="%23${color}"/></svg>`
})

const waveMaskStyle = computed(() => ({
  maskImage: `url("data:image/svg+xml,${waveSvg.value}")`,
  WebkitMaskImage: `url("data:image/svg+xml,${waveSvg.value}")`,
  maskSize: '200% 100%',
  WebkitMaskSize: '200% 100%',
  animation: 'waveSlide 3s linear infinite',
}))
</script>

<style scoped>
.flow-title-icon {
  width: 1.25em;
  height: 1.25em;
  display: inline-block;
}

@keyframes waveSlide {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
</style>
