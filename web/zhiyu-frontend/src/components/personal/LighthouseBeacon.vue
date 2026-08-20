<template>
  <div class="lighthouse-wrap relative flex items-end justify-center" :style="{ height: height + 'px' }">
    <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="w-full h-full" style="max-width:320px">
      <defs>
        <!-- 灯塔光束渐变 -->
        <radialGradient id="beamGrad" cx="50%" cy="100%" r="100%">
          <stop offset="0%" :stop-color="beamColor" stop-opacity="0.6" />
          <stop offset="60%" :stop-color="beamColor" stop-opacity="0.15" />
          <stop offset="100%" :stop-color="beamColor" stop-opacity="0" />
        </radialGradient>
        <!-- 塔身渐变 -->
        <linearGradient id="towerGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#4a5568" />
          <stop offset="30%" stop-color="#718096" />
          <stop offset="70%" stop-color="#718096" />
          <stop offset="100%" stop-color="#4a5568" />
        </linearGradient>
        <!-- 光晕 -->
        <filter id="glow">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- 底座 — 半圆形仪表盘 -->
      <g transform="translate(160, 340)">
        <!-- 仪表盘外圈 -->
        <path d="M-100,0 A100,100 0 0,1 100,0" fill="none" :stroke="gaugeTrackColor" stroke-width="3" />
        <!-- 仪表盘刻度 -->
        <g v-for="tick in gaugeTicks" :key="tick.angle">
          <line
            :x1="(92) * Math.cos(tick.angle)" :y1="(92) * Math.sin(tick.angle)"
            :x2="(100) * Math.cos(tick.angle)" :y2="(100) * Math.sin(tick.angle)"
            :stroke="tick.color" :stroke-width="tick.major ? 2 : 1" />
          <text v-if="tick.major"
            :x="(82) * Math.cos(tick.angle)" :y="(82) * Math.sin(tick.angle)"
            text-anchor="middle" dominant-baseline="middle"
            font-size="8" font-family="Courier New, monospace" font-weight="700"
            :fill="tick.color">
            {{ tick.label }}
          </text>
        </g>
        <!-- 仪表盘填充弧 -->
        <path :d="gaugeArc" fill="none" :stroke="gaugeFillColor" stroke-width="5" stroke-linecap="round"
          filter="url(#glow)" class="transition-all duration-1000" />
        <!-- 指针 -->
        <g :transform="`rotate(${gaugeAngle})`" class="transition-transform duration-1000" style="transform-origin: 0 0">
          <line x1="0" y1="0" x2="0" y2="-85" stroke="var(--brand-400)" stroke-width="2" stroke-linecap="round" />
          <circle cx="0" cy="0" r="4" fill="var(--brand-500)" />
        </g>
        <!-- 中心数值 — 七段数码管 -->
        <text x="0" y="30" text-anchor="middle" font-size="28" font-family="Courier New, monospace"
          font-weight="700" :fill="valueColor" filter="url(#glow)">
          {{ percentage }}%
        </text>
        <text x="0" y="46" text-anchor="middle" font-size="8" font-family="Courier New, monospace"
          font-weight="700" fill="var(--text-muted)" letter-spacing="0.1em">
          HEALTH INDEX
        </text>
      </g>

      <!-- 塔身 -->
      <g transform="translate(160, 340)">
        <!-- 塔身主体 — 梯形 -->
        <polygon points="-18,0 -14,-160 14,-160 18,0" fill="url(#towerGrad)" stroke="#4a5568" stroke-width="0.5" />
        <!-- 条纹装饰 -->
        <g v-for="i in 6" :key="i">
          <rect :x="-16" :y="-i * 24 - 4" width="32" height="3" rx="1"
            :fill="i <= stripeCount ? 'var(--brand-500)' : '#4a5568'" opacity="0.6" />
        </g>
        <!-- 铆钉 -->
        <circle v-for="rivet in towerRivets" :key="rivet.id"
          :cx="rivet.x" :cy="rivet.y" r="2"
          fill="url(#towerGrad)" stroke="#4a5568" stroke-width="0.5" />
      </g>

      <!-- 灯室 -->
      <g transform="translate(160, 180)">
        <!-- 灯室玻璃 -->
        <rect x="-16" y="-20" width="32" height="28" rx="3"
          :fill="beamColor" fill-opacity="0.15" :stroke="beamColor" stroke-width="1" />
        <!-- 灯泡 -->
        <circle cx="0" cy="-6" r="6" :fill="beamColor" filter="url(#glow)" :opacity="beamOpacity" />
        <!-- 灯室顶盖 -->
        <polygon points="-20,-20 0,-30 20,-20" fill="#4a5568" stroke="#4a5568" stroke-width="0.5" />
        <!-- 旋转光束 -->
        <g :style="{ animation: `beacon-rotate ${beamSpeed}s linear infinite` }">
          <polygon :points="beamPoints" :fill="beamColor" fill-opacity="0.08" />
          <line x1="0" y1="-6" :x2="beamLength" y2="-6"
            :stroke="beamColor" stroke-width="2" opacity="0.4" stroke-linecap="round" />
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  percentage: number
  height?: number
}>(), { height: 400 })

const svgW = 320
const svgH = 380

// 颜色映射
const beamColor = computed(() => props.percentage >= 80 ? '#10b981' : props.percentage >= 50 ? '#f59e0b' : '#f43f5e')
const valueColor = computed(() => props.percentage >= 80 ? '#10b981' : props.percentage >= 50 ? '#f59e0b' : '#f43f5e')
const gaugeTrackColor = 'var(--border-color)'
const gaugeFillColor = computed(() => props.percentage >= 80 ? '#10b981' : props.percentage >= 50 ? '#f59e0b' : '#f43f5e')

// 光束速度（健康度越低越快/闪烁）
const beamSpeed = computed(() => props.percentage >= 80 ? 6 : props.percentage >= 50 ? 4 : 2)
const beamOpacity = computed(() => 0.6 + (props.percentage / 100) * 0.4)
const beamLength = 120
const beamPoints = computed(() => `-4,-6 ${beamLength},-20 ${beamLength},8`)

// 塔身条纹数
const stripeCount = computed(() => Math.ceil(props.percentage / 16.67))

// 塔身铆钉
const towerRivets = computed(() => {
  const rivets = []
  for (let i = 0; i < 6; i++) {
    const y = -i * 24 - 12
    const xOff = 14 - i * 0.5
    rivets.push({ id: `l-${i}`, x: -xOff, y })
    rivets.push({ id: `r-${i}`, x: xOff, y })
  }
  return rivets
})

// 仪表盘刻度
const gaugeTicks = computed(() => {
  const ticks = []
  for (let v = 0; v <= 100; v += 10) {
    const angle = (-180 + (v / 100) * 180) * (Math.PI / 180)
    const major = v % 25 === 0
    const color = v >= 80 ? '#10b981' : v >= 50 ? '#f59e0b' : '#f43f5e'
    ticks.push({ angle, major, label: v.toString(), color })
  }
  return ticks
})

// 仪表盘指针角度 (-180 到 0)
const gaugeAngle = computed(() => -180 + (props.percentage / 100) * 180)

// 仪表盘填充弧
const gaugeArc = computed(() => {
  const r = 96
  const startAngle = -180
  const endAngle = -180 + (props.percentage / 100) * 180
  const startRad = (startAngle * Math.PI) / 180
  const endRad = (endAngle * Math.PI) / 180
  const x1 = r * Math.cos(startRad)
  const y1 = r * Math.sin(startRad)
  const x2 = r * Math.cos(endRad)
  const y2 = r * Math.sin(endRad)
  const largeArc = props.percentage > 50 ? 1 : 0
  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`
})
</script>

<style scoped>
.lighthouse-wrap {
  overflow: visible;
}
.transition-transform {
  transition: transform 1s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>
