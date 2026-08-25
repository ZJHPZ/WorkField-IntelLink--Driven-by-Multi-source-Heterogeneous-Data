<template>
  <div class="hex-avatar relative shrink-0" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :viewBox="`0 0 ${size} ${size}`" class="w-full h-full" :style="glowStyle">
      <polygon :points="hexPoints" :fill="`url(#${gid})`" stroke="var(--brand-400)" :stroke-width="stroke" />
      <defs>
        <linearGradient :id="gid" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="var(--brand-600)" />
          <stop offset="100%" stop-color="var(--brand-400)" />
        </linearGradient>
      </defs>
    </svg>
    <!-- 默认插槽（自定义图形）优先于字母 -->
    <span v-if="$slots.default" class="absolute inset-0 flex items-center justify-center">
      <slot />
    </span>
    <span v-else class="absolute inset-0 flex items-center justify-center text-white font-bold"
      :style="{ fontSize: Math.round(size * 0.36) + 'px' }">{{ letter }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(defineProps<{
  /** 中心字母（有默认 slot 时自动忽略） */
  letter?: string
  size?: number
  stroke?: number
  /** 霓虹光晕半径 px（>0 生效，跟随主题品牌色） */
  glow?: number
}>(), {
  letter: '',
  size: 56,
  stroke: 1.5,
  glow: 0,
})

const gid = useId()
/** 正六边形顶点（viewBox 百分比，适配任意尺寸） */
const hexPoints = computed(() => {
  const x = (p: number) => ((p / 100) * props.size).toFixed(1)
  const y = (p: number) => ((p / 100) * props.size).toFixed(1)
  return [
    `${x(50)},${y(3.6)}`,
    `${x(92.9)},${y(28.6)}`,
    `${x(92.9)},${y(71.4)}`,
    `${x(50)},${y(96.4)}`,
    `${x(7.1)},${y(71.4)}`,
    `${x(7.1)},${y(28.6)}`,
  ].join(' ')
})

const glowStyle = computed(() =>
  props.glow > 0
    ? { filter: `drop-shadow(0 0 ${props.glow}px color-mix(in srgb, var(--brand-500) 40%, transparent))` }
    : {}
)
</script>
