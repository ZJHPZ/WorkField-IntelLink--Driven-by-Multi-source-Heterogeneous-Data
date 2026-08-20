<template>
  <div class="evolution-chain relative">
    <!-- 水平链条 -->
    <svg class="w-full" :height="svgH" :viewBox="`0 0 ${svgW} ${svgH}`">
      <defs>
        <!-- 金属链条渐变 -->
        <linearGradient id="chainMetal" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#9ca3af" />
          <stop offset="50%" stop-color="#6b7280" />
          <stop offset="100%" stop-color="#9ca3af" />
        </linearGradient>
        <!-- 光流渐变 -->
        <linearGradient id="flowGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="var(--brand-500)" stop-opacity="0" />
          <stop offset="50%" stop-color="var(--brand-400)" stop-opacity="1" />
          <stop offset="100%" stop-color="var(--brand-500)" stop-opacity="0" />
        </linearGradient>
        <!-- 霓虹发光滤镜 -->
        <filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- 链条连接线 -->
      <g v-for="(link, i) in chainLinks" :key="i">
        <!-- 链节背景 -->
        <rect :x="link.x" :y="link.y - 2" :width="link.w" height="4" rx="2"
          fill="url(#chainMetal)" opacity="0.4" />
        <!-- 链节高亮（已完成） -->
        <rect v-if="link.active" :x="link.x" :y="link.y - 2" :width="link.w" height="4" rx="2"
          fill="var(--brand-500)" opacity="0.6" />
        <!-- 光流动画 -->
        <rect v-if="link.active" :x="link.x" :y="link.y - 2" :width="link.w" height="4" rx="2"
          fill="url(#flowGrad)" class="animate-chain-flow" />
        <!-- 链节铆钉 -->
        <circle :cx="link.x" :cy="link.y" r="4" fill="url(#chainMetal)"
          :stroke="link.active ? 'var(--brand-500)' : '#4a5568'" stroke-width="1" />
        <circle :cx="link.x + link.w" :cy="link.y" r="4" fill="url(#chainMetal)"
          :stroke="link.active ? 'var(--brand-500)' : '#4a5568'" stroke-width="1" />
      </g>

      <!-- 等级节点 -->
      <g v-for="(node, i) in levelNodes" :key="node.level"
        class="cursor-pointer" @click="$emit('level-click', node)">
        <!-- 六角螺母外框 -->
        <polygon :points="hexPoints(node.x, node.y, node.size)"
          :fill="node.fill" :stroke="node.stroke" stroke-width="1.5"
          :opacity="node.locked ? 0.4 : 1"
          :filter="!node.locked ? 'url(#neonGlow)' : ''" />
        <!-- 内部发光 -->
        <polygon v-if="!node.locked" :points="hexPoints(node.x, node.y, node.size - 4)"
          fill="none" :stroke="node.stroke" stroke-width="0.5" opacity="0.4" />
        <!-- 外圈光晕 -->
        <circle v-if="!node.locked" :cx="node.x" :cy="node.y" :r="node.size + 3"
          fill="none" :stroke="node.stroke" stroke-width="0.5" opacity="0.2" />
        <!-- 等级图标 -->
        <text :x="node.x" :y="node.y - 2" text-anchor="middle" dominant-baseline="middle"
          font-size="16" :opacity="node.locked ? 0.4 : 1">
          {{ node.icon }}
        </text>
        <!-- 等级名称 -->
        <text :x="node.x" :y="node.y + node.size + 14" text-anchor="middle"
          font-size="11" font-family="system-ui" font-weight="700"
          :fill="node.locked ? 'var(--text-muted)' : 'var(--text-primary)'">
          {{ node.name }}
        </text>
        <!-- 等级标签 -->
        <text :x="node.x" :y="node.y + node.size + 28" text-anchor="middle"
          font-size="9" font-family="Courier New, monospace" font-weight="700"
          letter-spacing="0.08em" :fill="node.labelColor">
          {{ node.label }}
        </text>
        <!-- 锁图标 -->
        <text v-if="node.locked" :x="node.x" :y="node.y + 2" text-anchor="middle"
          font-size="10" opacity="0.5">🔒</text>
        <!-- 脉冲环（当前等级） -->
        <circle v-if="node.current" :cx="node.x" :cy="node.y" :r="node.size + 6"
          fill="none" :stroke="node.stroke" stroke-width="2" opacity="0.5"
          class="animate-node-ring" />
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Level {
  level: number
  name: string
  icon: string
  unlocked: boolean
  current: boolean
  skillCount: number
  requiredCount: number
}

const props = withDefaults(defineProps<{
  levels: Level[]
  currentLevel?: number
}>(), { currentLevel: 1 })

defineEmits<{ 'level-click': [level: Level] }>()

const svgW = 600
const svgH = 120
const nodeSpacing = svgW / (props.levels.length + 1)
const nodeY = svgH / 2
const nodeSize = 28

// 等级节点
const levelNodes = computed(() => {
  const colors = ['#10b981', '#06b6d4', '#f59e0b', '#f43f5e']
  const labels = ['JUNIOR', 'MID', 'SENIOR', 'EXPERT']
  return props.levels.map((level, i) => {
    const x = nodeSpacing * (i + 1)
    const active = level.unlocked
    const color = colors[i] || '#6366f1'
    return {
      ...level,
      x,
      y: nodeY,
      size: nodeSize,
      fill: active ? `${color}20` : 'var(--bg-secondary)',
      stroke: active ? color : 'var(--border-color)',
      labelColor: active ? color : 'var(--text-muted)',
      label: labels[i] || `LV${level.level}`,
      locked: !level.unlocked,
    }
  })
})

// 链条连接
const chainLinks = computed(() => {
  const links = []
  for (let i = 0; i < levelNodes.value.length - 1; i++) {
    const a = levelNodes.value[i]
    const b = levelNodes.value[i + 1]
    links.push({
      x: a.x + a.size,
      y: nodeY,
      w: b.x - b.size - (a.x + a.size),
      active: a.unlocked && b.unlocked,
    })
  }
  return links
})

// 六角形顶点
function hexPoints(cx: number, cy: number, r: number) {
  return Array.from({ length: 6 }, (_, i) => {
    const angle = (i * 60 - 30) * (Math.PI / 180)
    return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`
  }).join(' ')
}
</script>

<style scoped>
.evolution-chain {
  overflow: visible;
}
</style>
