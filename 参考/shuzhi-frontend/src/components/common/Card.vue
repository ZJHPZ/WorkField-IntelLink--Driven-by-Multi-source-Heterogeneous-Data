<template>
  <div class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-300" :class="paddingClass">
    <div v-if="$slots.header" class="flex items-center justify-between mb-3">
      <h3 class="text-base font-semibold text-gray-800">{{ title }}</h3>
      <slot name="header" />
    </div>
    <h3 v-else-if="title" class="text-base font-semibold text-gray-800 mb-3">{{ title }}</h3>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  padding?: string
}>(), {
  padding: 'p-5',
})

const paddingClass = computed(() => props.padding)
</script>
