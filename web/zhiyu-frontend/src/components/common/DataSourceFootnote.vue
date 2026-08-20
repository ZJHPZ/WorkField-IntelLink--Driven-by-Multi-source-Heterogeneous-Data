<template>
  <div class="data-source-footnote mt-3 pt-3 text-xs flex flex-wrap items-center gap-x-4 gap-y-1"
    :style="{ color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)' }">
    <span v-if="sources.length" class="flex items-center gap-1">
      <span>📊</span>
      <span>数据源: {{ sources.join(' · ') }}</span>
    </span>
    <span v-if="updatedAt" class="flex items-center gap-1">
      <span>🕐</span>
      <span>更新: {{ updatedAt }}</span>
    </span>
    <span v-if="confidence !== undefined" class="flex items-center gap-1">
      <span>🎯</span>
      <ConfidenceBadge :level="confidence" />
    </span>
    <slot />
  </div>
</template>

<script setup lang="ts">
import ConfidenceBadge from './ConfidenceBadge.vue'

withDefaults(defineProps<{
  sources?: string[]
  updatedAt?: string
  confidence?: number
}>(), {
  sources: () => [],
})
</script>
