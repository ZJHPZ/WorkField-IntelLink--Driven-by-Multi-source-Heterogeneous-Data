<template>
  <span
    class="confidence-badge inline-flex items-center gap-0.5 text-xs font-medium px-1.5 py-0.5 rounded-full"
    :class="badgeClass"
    :title="'置信度 ' + level + '%' + (sources.length ? ' | 来源: ' + sources.join(', ') : '')"
  >
    <span>{{ icon }}</span>
    <span>{{ level }}%</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  level: number        // 0-100
  sources?: string[]
}>(), {
  sources: () => [],
})

const icon = computed(() => props.level >= 85 ? '✓' : props.level >= 60 ? '⚠' : '✗')
const badgeClass = computed(() =>
  props.level >= 85
    ? 'bg-mint-50 text-mint-700 border border-mint-200'
    : props.level >= 60
      ? 'bg-amber-50 text-amber-700 border border-amber-200'
      : 'bg-rose-50 text-rose-500 border border-rose-200'
)
</script>
