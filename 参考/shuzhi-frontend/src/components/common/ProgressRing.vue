<template>
  <div class="progress-ring" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" class="progress-ring__svg">
      <circle class="progress-ring__bg" :cx="size/2" :cy="size/2" :r="radius"
        fill="none" :stroke-width="strokeWidth" />
      <circle class="progress-ring__bar" :cx="size/2" :cy="size/2" :r="radius"
        fill="none" :stroke-width="strokeWidth"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        :stroke="isGradient ? 'url(#ringGradient)' : color"
        :style="!isGradient ? { stroke: color } : {}" />
      <defs v-if="isGradient">
        <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#6366f1" />
          <stop offset="50%" stop-color="#a855f7" />
          <stop offset="100%" stop-color="#06b6d4" />
        </linearGradient>
      </defs>
    </svg>
    <div class="progress-ring__content">
      <slot>
        <span class="progress-ring__value" :style="{ color: textColor }">{{ displayValue }}</span>
        <span v-if="label" class="progress-ring__label">{{ label }}</span>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  percentage: number
  size?: number
  strokeWidth?: number
  color?: string
  label?: string
  showSign?: boolean
}>(), {
  size: 120,
  strokeWidth: 8,
  color: '#6366f1',
})

const isGradient = computed(() => props.color.startsWith('url('))
const textColor = computed(() => isGradient.value ? '#6366f1' : props.color)

const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const offset = computed(() => circumference.value - (Math.min(props.percentage, 100) / 100) * circumference.value)
const displayValue = computed(() => props.showSign ? `${Math.round(props.percentage)}%` : `${Math.round(props.percentage)}`)
</script>

<style scoped>
.progress-ring { position: relative; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.progress-ring__svg { transform: rotate(-90deg); }
.progress-ring__bg { stroke: #e5e7eb; }
.progress-ring__bar { transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1); stroke-linecap: round; }
.progress-ring__content { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.progress-ring__value { font-size: 1.5rem; font-weight: 700; line-height: 1; }
.progress-ring__label { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
</style>
