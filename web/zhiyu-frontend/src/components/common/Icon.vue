<template>
  <img v-if="src" :src="src" class="inline-block shrink-0" :class="sizeClass" :alt="alt" />
  <span v-else :class="sizeClass" :style="dotStyle" class="inline-block shrink-0 rounded-full" />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  src?: string
  size?: 'sm' | 'md' | 'lg'
  alt?: string
  /** For dot icons: status color */
  color?: string
}>(), {
  size: 'md',
  alt: '',
})

const sizeClass = computed(() => {
  const map: Record<string, string> = { sm: 'w-3 h-3', md: 'w-5 h-5', lg: 'w-8 h-8' }
  return map[props.size] || map.md
})

const dotStyle = computed(() => {
  if (!props.color) return {}
  return { backgroundColor: props.color }
})
</script>
