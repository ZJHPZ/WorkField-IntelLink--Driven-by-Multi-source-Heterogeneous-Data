<template>
  <div class="relative shrink-0 overflow-hidden select-none flex items-center justify-center"
    style="height: 340px; background: radial-gradient(ellipse at 50% 60%, #12103a 0%, #08081a 50%, #040412 100%);"
  >
    <svg
      :viewBox="`0 0 ${svgSize} ${svgSize}`"
      :width="svgSize"
      :height="svgSize"
      class="block"
    >
      <defs>
        <!-- 面积渐变 -->
        <radialGradient id="area-grad-2d" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="rgba(99,102,241,0.0)" />
          <stop offset="60%" stop-color="rgba(99,102,241,0.08)" />
          <stop offset="100%" stop-color="rgba(99,102,241,0.22)" />
        </radialGradient>
        <!-- 节点发光滤镜 -->
        <filter id="node-glow-2d" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- 同心六边形网格 -->
      <polygon
        v-for="level in [25, 50, 75, 100]" :key="'g'+level"
        :points="gridPolygon(level)"
        fill="none"
        :stroke="level === 100 ? 'rgba(99,102,241,0.2)' : 'rgba(99,102,241,0.08)'"
        :stroke-width="level === 100 ? 1 : 0.5"
        :stroke-dasharray="level === 100 ? '4 3' : 'none'"
      />

      <!-- 轴线 -->
      <line
        v-for="(d, i) in dimensions" :key="'axis'+d.key"
        :x1="cx" :y1="cy"
        :x2="axisPoint(112, i).x" :y2="axisPoint(112, i).y"
        stroke="rgba(99,102,241,0.1)"
        stroke-width="0.5"
      />

      <!-- 前值面积 -->
      <polygon
        v-if="prevPolyPoints"
        :points="prevPolyPoints"
        fill="rgba(99,102,241,0.04)"
        stroke="rgba(99,102,241,0.12)"
        stroke-width="0.5"
        stroke-dasharray="3 4"
      />

      <!-- 当前值面积 -->
      <polygon
        :points="currPolyPoints"
        fill="url(#area-grad-2d)"
        stroke="rgba(99,102,241,0.3)"
        stroke-width="1"
        class="area-transition"
      />

      <!-- 粒子流轨道 (虚线动画) -->
      <polyline
        v-for="pi in 3" :key="'p'+pi"
        :points="currPolyClosed"
        fill="none"
        stroke="rgba(255,255,255,0.55)"
        stroke-width="2"
        stroke-linecap="round"
        :stroke-dasharray="`1 ${10 + pi * 4}`"
        class="particle-orbit"
        :style="{ animationDuration: (2 + pi * 1.5) + 's', animationDelay: (pi * 0.7) + 's' }"
      />

      <!-- 节点触控区 (透明大圆) -->
      <circle
        v-for="d in dimensions" :key="'hit'+d.key"
        :cx="currPoint(d).x" :cy="currPoint(d).y"
        r="14"
        fill="transparent"
        class="cursor-pointer"
        @mouseenter="$emit('hoverStar', d.key)"
        @mouseleave="$emit('hoverStar', null)"
        @click.stop="$emit('focusDimension', d.key)"
      />

      <!-- 节点辉光环 -->
      <circle
        v-for="d in dimensions" :key="'halo'+d.key"
        :cx="currPoint(d).x" :cy="currPoint(d).y"
        :r="nodeRadius(d) + 5"
        fill="none"
        :stroke="d.color"
        :stroke-opacity="hoveredStar === d.key ? 0.4 : 0.12"
        stroke-width="1"
        class="transition-all duration-400"
      />

      <!-- 发光节点 -->
      <circle
        v-for="d in dimensions" :key="'node'+d.key"
        :cx="currPoint(d).x" :cy="currPoint(d).y"
        :r="hoveredStar === d.key ? nodeRadius(d) * 1.5 : nodeRadius(d)"
        :fill="d.color"
        :opacity="hoveredStar && hoveredStar !== d.key ? 0.25 : 0.9"
        filter="url(#node-glow-2d)"
        class="transition-all duration-400"
      />

      <!-- 节点中心亮点 -->
      <circle
        v-for="d in dimensions" :key="'core'+d.key"
        :cx="currPoint(d).x" :cy="currPoint(d).y"
        :r="hoveredStar === d.key ? 2.5 : 1.5"
        fill="white"
        :opacity="hoveredStar && hoveredStar !== d.key ? 0.3 : 0.8"
        class="transition-all duration-400"
      />

      <!-- 轴标签: 图标 + 名称 -->
      <text
        v-for="(d, i) in dimensions" :key="'lbl'+d.key"
        :x="labelPos(i).x" :y="labelPos(i).y"
        :text-anchor="labelAnchor(i)"
        dominant-baseline="middle"
        :fill="d.color"
        font-size="10"
        font-weight="600"
        :opacity="hoveredStar && hoveredStar !== d.key ? 0.3 : 0.9"
        class="transition-all duration-400 pointer-events-none"
      >
        {{ d.icon }} {{ d.label }}
      </text>

      <!-- 轴标签: 数值 -->
      <text
        v-for="(d, i) in dimensions" :key="'val'+d.key"
        :x="labelPos(i).x" :y="labelPos(i).y + 13"
        :text-anchor="labelAnchor(i)"
        dominant-baseline="middle"
        :fill="d.color"
        font-size="9"
        font-weight="700"
        :opacity="hoveredStar && hoveredStar !== d.key ? 0.25 : 0.8"
        class="transition-all duration-400 pointer-events-none"
      >
        {{ d.value }}
      </text>

      <!-- 悬停 Tooltip -->
      <g v-if="hoveredStar" class="pointer-events-none">
        <rect
          :x="tooltipPos.x - 40" :y="tooltipPos.y - 28"
          width="80" height="20"
          rx="6"
          fill="rgba(8,8,24,0.92)"
          stroke="rgba(99,102,241,0.3)"
          stroke-width="0.5"
        />
        <text
          :x="tooltipPos.x" :y="tooltipPos.y - 15"
          text-anchor="middle" dominant-baseline="middle"
          fill="white" font-size="9" font-weight="600"
        >
          {{ hoveredDim?.label }} {{ hoveredDim?.value }}
        </text>
      </g>
    </svg>

    <!-- 图例 -->
    <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2 text-[9px]"
      style="color: var(--text-muted); background: rgba(8,8,24,0.7); padding: 3px 10px; border-radius: 999px; border: 1px solid rgba(99,102,241,0.1);">
      <span class="w-1.5 h-1.5 rounded-full" style="background: #6366f1; box-shadow: 0 0 6px #6366f1;"></span> 高值
      <span class="w-1.5 h-1.5 rounded-full" style="background: #6366f1; opacity: 0.3;"></span> 低值
      <span class="ml-2">| 悬停节点查看详情 · 点击跳转维度</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProfileDimension } from '@/stores/profileModeling'

const props = defineProps<{
  dimensions: ProfileDimension[]
  hoveredStar: string | null
}>()

defineEmits<{
  hoverStar: [key: string | null]
  focusDimension: [key: string]
}>()

const svgSize = 280
const cx = 140
const cy = 145 // 略下移让顶部标签不贴边

// 角度: 从正上方开始, 顺时针
function angle(i: number): number {
  return (i / 6) * Math.PI * 2 - Math.PI / 2
}

function axisPoint(r: number, i: number): { x: number; y: number } {
  return {
    x: Math.round(cx + Math.cos(angle(i)) * r),
    y: Math.round(cy + Math.sin(angle(i)) * r),
  }
}

// 网格六边形
function gridPolygon(level: number): string {
  const r = (level / 100) * 110
  return Array.from({ length: 6 }, (_, i) => {
    const p = axisPoint(r, i)
    return `${p.x},${p.y}`
  }).join(' ')
}

// 当前值点
function currPoint(d: ProfileDimension): { x: number; y: number } {
  const i = props.dimensions.findIndex(dd => dd.key === d.key)
  return axisPoint((d.value / 100) * 110, i)
}

// 前值点
function prevPoint(d: ProfileDimension): { x: number; y: number } {
  const i = props.dimensions.findIndex(dd => dd.key === d.key)
  return axisPoint((d.previousValue / 100) * 110, i)
}

// 多边形字符串
const currPolyPoints = computed(() =>
  props.dimensions.map(d => {
    const p = currPoint(d)
    return `${p.x},${p.y}`
  }).join(' ')
)

const currPolyClosed = computed(() => {
  if (!props.dimensions.length) return ''
  const pts = props.dimensions.map(d => {
    const p = currPoint(d)
    return `${p.x},${p.y}`
  })
  pts.push(pts[0]) // 闭合
  return pts.join(' ')
})

const prevPolyPoints = computed(() => {
  if (!props.dimensions.length) return ''
  return props.dimensions.map(d => {
    const p = prevPoint(d)
    return `${p.x},${p.y}`
  }).join(' ')
})

function nodeRadius(d: ProfileDimension): number {
  return 3 + (d.value / 100) * 7
}

// 标签位置
function labelPos(i: number): { x: number; y: number } {
  return axisPoint(128, i)
}

function labelAnchor(i: number): string {
  const a = angle(i)
  const cos = Math.cos(a)
  if (Math.abs(cos) < 0.15) return 'middle'
  return cos > 0 ? 'start' : 'end'
}

// Tooltip 位置
const hoveredDim = computed(() =>
  props.dimensions.find(d => d.key === props.hoveredStar) || null
)

const tooltipPos = computed(() => {
  if (!hoveredDim.value) return { x: 0, y: 0 }
  const p = currPoint(hoveredDim.value)
  // 偏移到节点上方
  return { x: p.x, y: p.y - 18 }
})
</script>

<style scoped>
.area-transition {
  transition: all 0.8s ease;
}

.particle-orbit {
  animation: dash-flow linear infinite;
}

@keyframes dash-flow {
  0% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -200; }
}
</style>
