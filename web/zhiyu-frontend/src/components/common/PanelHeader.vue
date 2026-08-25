<template>
  <div class="panel-header flex items-center gap-2" :class="spacingClass">
    <span class="tag-plate" :style="labelStyle">{{ label }}</span>
    <h3 v-if="title" class="text-sm font-bold tracking-wide uppercase" :style="{ color: 'var(--text-primary)' }">{{ title }}</h3>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/** 铭牌可用的语义色；default 表示不染色（跟随 tag-plate 默认样式） */
export type PanelColor = 'brand' | 'cyan' | 'mint' | 'amber' | 'rose' | 'purple' | 'default'

const props = withDefaults(defineProps<{
  label: string
  title?: string
  color?: PanelColor
  /** 底部留白：md=mb-4（默认）、sm=mb-3、none=无（父容器自行控制间距） */
  margin?: 'none' | 'sm' | 'md'
}>(), {
  color: 'default',
  margin: 'md',
})

const COLOR_MAP: Record<Exclude<PanelColor, 'default'>, { c: string; b: string }> = {
  brand: { c: 'var(--brand-400)', b: 'var(--brand-500)' },
  cyan: { c: 'var(--cyan-400)', b: 'var(--cyan-500)' },
  mint: { c: 'var(--mint-400)', b: 'var(--mint-500)' },
  amber: { c: 'var(--amber-400)', b: 'var(--amber-500)' },
  rose: { c: 'var(--rose-400)', b: 'var(--rose-500)' },
  purple: { c: 'var(--purple-500)', b: 'var(--purple-500)' },
}

const labelStyle = computed(() => {
  const c = props.color !== 'default' ? COLOR_MAP[props.color] : undefined
  return c ? { color: c.c, borderColor: c.b } : {}
})

const spacingClass = computed(() =>
  props.margin === 'sm' ? 'mb-3' : props.margin === 'md' ? 'mb-4' : ''
)
</script>
