<template>
  <div
    class="relative rounded-2xl border-2 p-5 transition-all duration-300 cursor-pointer"
    :class="statusClasses"
    @click="$emit('click')"
  >
    <!-- Status indicator -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full"
        :class="statusBadgeClass">{{ statusLabel }}</span>
      <span v-if="stage.progress > 0 && stage.progress < 100" class="text-sm font-bold" :class="statusTextClass">
        {{ Math.round(stage.progress) }}%
      </span>
      <span v-else-if="stage.progress === 100" class="text-mint-500">✓</span>
    </div>

    <!-- Title -->
    <h3 class="font-semibold text-gray-800 mb-3">{{ stage.title }}</h3>

    <!-- Progress bar -->
    <div class="h-2 bg-gray-100 rounded-full mb-3 overflow-hidden">
      <div class="h-full rounded-full transition-all duration-700"
        :class="progressBarClass"
        :style="{ width: Math.max(stage.progress, 5) + '%' }" />
    </div>

    <!-- Topics -->
    <div class="flex flex-wrap gap-1.5 mb-3">
      <span v-for="topic in stage.topics" :key="topic"
        class="text-xs px-2 py-1 rounded-lg font-medium bg-gray-50 text-gray-600 border border-gray-100">
        {{ topic }}
      </span>
    </div>

    <!-- Meta -->
    <div class="flex items-center text-xs text-gray-400 gap-3">
      <span>⏱️ 预计{{ stage.estimatedDays }}天</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LearningStage } from '@/stores/learning'

const props = defineProps<{ stage: LearningStage }>()
defineEmits<{ (e: 'click'): void }>()

const statusMap = {
  completed: { label: '已完成', classes: 'border-mint-200 bg-mint-50/30', badge: 'bg-mint-100 text-mint-700', text: 'text-mint-600', bar: 'bg-mint-500' },
  in_progress: { label: '进行中', classes: 'border-brand-200 bg-brand-50/20 shadow-md shadow-brand-500/10', badge: 'bg-brand-100 text-brand-700', text: 'text-brand-600', bar: 'bg-brand-500' },
  available: { label: '可开始', classes: 'border-gray-200 bg-white', badge: 'bg-gray-100 text-gray-600', text: 'text-gray-500', bar: 'bg-gray-400' },
  locked: { label: '🔒 锁定', classes: 'border-gray-100 bg-gray-50/50 opacity-60', badge: 'bg-gray-100 text-gray-400', text: 'text-gray-400', bar: 'bg-gray-200' },
}
const s = computed(() => statusMap[props.stage.status] || statusMap.locked)
const statusClasses = computed(() => s.value.classes)
const statusLabel = computed(() => s.value.label)
const statusBadgeClass = computed(() => s.value.badge)
const statusTextClass = computed(() => s.value.text)
const progressBarClass = computed(() => s.value.bar)
</script>
