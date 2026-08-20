<template>
  <div class="glass-card rounded-2xl" :class="[paddingClass, { 'cursor-pointer hover:shadow-lg': clickable }]" @click="clickable && $emit('click')">
    <div v-if="$slots.header || title" class="flex items-center justify-between mb-3">
      <h3 v-if="title" class="text-base font-semibold" :style="{ color: 'var(--text-primary)' }">{{ title }}</h3>
      <slot name="header" />
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  padding?: string
  clickable?: boolean
}>(), {
  padding: 'p-5',
})

defineEmits<{ (e: 'click'): void }>()

const paddingClass = computed(() => props.padding)
</script>
