<template>
  <div class="energy-bar" :class="{ 'energy-bar--pulse': isAnimating }">
    <div class="flex items-center justify-between mb-1.5">
      <span class="text-xs text-gray-500">{{ label }}</span>
      <span class="text-xs font-bold" :class="textColor">{{ Math.round(percentage) }}%</span>
    </div>
    <div class="h-2.5 rounded-full overflow-hidden" :class="trackClass">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out"
        :class="[barClass, isAnimating ? 'animate-energy-pulse' : '']"
        :style="{ width: Math.max(percentage, 4) + '%' }"
      />
    </div>
    <p v-if="hint" class="text-xs text-gray-400 mt-1.5">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  percentage: number
  label?: string
  hint?: string
  variant?: 'brand' | 'mint' | 'amber' | 'rose' | 'energy'
  isAnimating?: boolean
}>(), {
  variant: 'brand',
  isAnimating: false,
})

const configMap: Record<string, { bar: string; track: string; text: string }> = {
  brand: { bar: 'bg-brand-500', track: 'bg-brand-100', text: 'text-brand-600' },
  mint: { bar: 'bg-mint-500', track: 'bg-mint-100', text: 'text-mint-600' },
  amber: { bar: 'bg-amber-500', track: 'bg-amber-100', text: 'text-amber-600' },
  rose: { bar: 'bg-rose-500', track: 'bg-rose-100', text: 'text-rose-600' },
  energy: { bar: 'bg-energy-gradient', track: 'bg-gray-100', text: 'text-brand-600' },
}

const config = computed(() => configMap[props.variant] || configMap.brand)
const barClass = computed(() => config.value.bar)
const trackClass = computed(() => config.value.track)
const textColor = computed(() => config.value.text)
</script>
