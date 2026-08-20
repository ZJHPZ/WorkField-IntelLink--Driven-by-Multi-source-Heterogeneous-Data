<template>
  <div
    class="relative rounded-2xl border-2 p-5 transition-all duration-300"
    :class="[statusClasses, { 'cursor-pointer': clickable }]"
    @click="clickable && $emit('click')"
  >
    <!-- Status badge -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full"
        :class="statusBadgeClass">{{ statusLabel }}</span>
      <span v-if="progress > 0 && progress < 100" class="text-sm font-bold" :class="statusTextClass">
        {{ Math.round(progress) }}%
      </span>
      <span v-else-if="progress === 100" class="text-mint-500">✓</span>
    </div>

    <!-- Title -->
    <h3 class="font-semibold mb-3" :style="{ color: 'var(--text-primary)' }">{{ title }}</h3>

    <!-- Progress bar -->
    <div class="h-2 bg-gray-100 rounded-full mb-3 overflow-hidden">
      <div class="h-full rounded-full transition-all duration-700"
        :class="progressBarClass"
        :style="{ width: Math.max(progress, 5) + '%' }" />
    </div>

    <!-- Tags -->
    <div class="flex flex-wrap gap-1.5 mb-3">
      <span v-for="tag in tags" :key="tag"
        class="text-xs px-2 py-1 rounded-lg font-medium bg-gray-50 text-gray-600 border border-gray-100">
        {{ tag }}
      </span>
    </div>

    <!-- Meta -->
    <div class="flex items-center text-xs gap-3" :style="{ color: 'var(--text-muted)' }">
      <span v-if="estimatedTime">⏱️ {{ estimatedTime }}</span>
      <slot name="meta" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface StatusStyle {
  label: string
  classes: string
  badge: string
  text: string
  bar: string
}

const props = withDefaults(defineProps<{
  title: string
  status: string
  statusConfig: Record<string, StatusStyle>
  progress?: number
  tags?: string[]
  estimatedTime?: string
  clickable?: boolean
}>(), {
  progress: 0,
  tags: () => [],
  clickable: false,
})

defineEmits<{ (e: 'click'): void }>()

const fallback: StatusStyle = {
  label: '未知',
  classes: 'border-gray-100 bg-gray-50/50 opacity-60',
  badge: 'bg-gray-100 text-gray-400',
  text: 'text-gray-400',
  bar: 'bg-gray-200',
}

const s = computed<StatusStyle>(() => props.statusConfig[props.status] || fallback)
const statusClasses = computed(() => s.value.classes)
const statusLabel = computed(() => s.value.label)
const statusBadgeClass = computed(() => s.value.badge)
const statusTextClass = computed(() => s.value.text)
const progressBarClass = computed(() => s.value.bar)
</script>
