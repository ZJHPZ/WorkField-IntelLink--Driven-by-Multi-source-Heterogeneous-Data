<template>
  <div class="lighthouse-wrap relative flex items-end justify-center" :style="{ height: height + 'px' }">
    <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="w-full h-full" style="max-width:320px">
      <defs>
        <filter :id="glowFilterId">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- ══ 扫描光束（绕灯室摆动；健康度越高越长越亮，低于 50 闪烁告警）══ -->
      <g :transform="`translate(${cx}, ${lampY})`">
        <g :class="percentage < 50 ? 'beacon-flicker' : ''">
          <animateTransform
            attributeName="transform" type="rotate"
            from="-52 0 0" to="52 0 0" :dur="swayDur"
            values="-52;52;-52" keyTimes="0;0.5;1" repeatCount="indefinite" />
          <polygon :points="beamPoints" :fill="beamColor" :fill-opacity="beamOpacity" />
          <line x1="0" y1="-6" :x2="0" :y2="-beamLen" :stroke="beamColor" stroke-width="2" stroke-linecap="round"
            :opacity="beamLineOpacity" :filter="'url(#' + glowFilterId + ')'" />
        </g>
      </g>

      <!-- ══ 半环仪表（数据重心：健康弧 + 刻度 + 指针 + 中心值）══ -->
      <g :transform="`translate(${cx}, ${gaugeCy})`">
        <!-- 轨道弧 -->
        <path d="M -44 0 A 44 44 0 1 1 44 0" fill="none" :stroke="gaugeTrackColor" stroke-width="3" :opacity="0.35" />
        <!-- 健康弧（dash 平滑过渡） -->
        <path d="M -44 0 A 44 44 0 1 1 44 0" fill="none" :stroke="healthColor" stroke-width="5" stroke-linecap="round"
          :stroke-dasharray="arcLen" :stroke-dashoffset="arcOffset"
          :filter="'url(#' + glowFilterId + ')'" class="arc-animate" />
        <!-- 刻度 + 主刻度标签 -->
        <g v-for="tick in gaugeTicks" :key="tick.v">
          <line :x1="tick.inner.x" :y1="tick.inner.y" :x2="tick.outer.x" :y2="tick.outer.y"
            :stroke="tick.color || 'var(--text-muted)'" :stroke-width="tick.major ? 1.5 : 0.7"
            :opacity="tick.major ? 0.9 : 0.45" />
          <text v-if="tick.major" :x="tick.label.x" :y="tick.label.y" text-anchor="middle" dominant-baseline="middle"
            font-size="7.5" font-weight="700" :fill="tick.color" style="font-family:var(--font-mono)">
            {{ tick.v }}
          </text>
        </g>
        <!-- 指针 -->
        <line x1="0" y1="0" :x2="needle.x" :y2="needle.y" :stroke="healthColor" stroke-width="1.5" stroke-linecap="round"
          :filter="'url(#' + glowFilterId + ')'" class="arc-animate" />
        <circle cx="0" cy="0" r="3.5" :fill="healthColor" />
        <!-- 中心值 -->
        <text x="0" y="20" text-anchor="middle" font-size="30" font-weight="700" :fill="healthColor"
          :filter="'url(#' + glowFilterId + ')'" style="font-family:var(--font-mono)">{{ percentage }}%</text>
        <text x="0" y="34" text-anchor="middle" font-size="7" font-weight="700" fill="var(--text-muted)"
          style="font-family:var(--font-mono);letter-spacing:0.2em">{{ statusLabel }}</text>
      </g>

      <!-- ══ 塔身（主题 token 色，非硬编码灰蓝）══ -->
      <g :transform="`translate(${cx}, ${towerBaseY})`">
        <!-- 基座平台 -->
        <polygon points="-24,2 -20,-5 20,-5 24,2"
          :style="{ fill: 'color-mix(in srgb, var(--bg-card) 92%, #000)', stroke: 'var(--border-color)' }" stroke-width="0.5" />
        <!-- 塔身梯形 -->
        <polygon points="-18,0 -13,-84 13,-84 18,0"
          :style="{ fill: 'color-mix(in srgb, var(--bg-card) 88%, #000)', stroke: 'var(--border-color)' }" stroke-width="0.8" />
        <!-- 左侧品牌高光 -->
        <rect x="-15" y="-82" width="1.6" height="80"
          :style="{ fill: 'color-mix(in srgb, var(--brand-500) 22%, transparent)' }" />
        <!-- 条纹（点亮数 = 健康度） -->
        <g v-for="i in 6" :key="i">
          <rect :x="-16" :y="-12 - (i - 1) * 12" width="32" height="7" rx="1"
            :fill="i <= stripeCount ? healthColor : 'var(--border-color)'"
            :opacity="i <= stripeCount ? 0.5 : 0.35" />
        </g>
        <!-- 铆钉 -->
        <circle v-for="rv in rivets" :key="rv.id" :cx="rv.x" :cy="rv.y" r="1.8"
          :style="{ fill: 'var(--bg-card)', stroke: 'var(--border-color)' }" stroke-width="0.5" />
      </g>

      <!-- ══ 灯室 ══ -->
      <g :transform="`translate(${cx}, ${lampY})`">
        <!-- 连接颈 -->
        <rect x="-5" y="12" width="10" height="6"
          :style="{ fill: 'var(--bg-card)', stroke: 'var(--border-color)' }" stroke-width="0.5" />
        <!-- 玻璃罩 -->
        <rect x="-14" y="-14" width="28" height="28" rx="2"
          :fill="beamColor" :fill-opacity="0.12" :stroke="beamColor" :stroke-opacity="0.55" stroke-width="1" />
        <!-- 灯泡 -->
        <circle cx="0" cy="-5" r="5.5" :fill="beamColor" :filter="'url(#' + glowFilterId + ')'" :opacity="beamBulbOpacity" />
        <!-- 顶盖 -->
        <polygon points="-16,-14 0,-24 16,-14"
          :style="{ fill: 'var(--bg-card)', stroke: 'var(--border-color)' }" stroke-width="0.5" />
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue'
import { PALETTE } from '@/utils/color'

const props = withDefaults(defineProps<{
  percentage: number
  height?: number
}>(), { height: 240 })

const svgW = 280
const svgH = 240
const cx = 140
const lampY = 34      // 灯室中心
const towerBaseY = 136 // 塔身底部（与半环弧顶衔接）
const gaugeCy = 180    // 半环圆心
const arcR = 44        // 健康弧半径
const glowFilterId = useId()

// —— 健康语义色（mint / amber / rose）——
const healthColor = computed(() => props.percentage >= 80 ? PALETTE.mint : props.percentage >= 50 ? PALETTE.amber : PALETTE.rose)
// 光束 / 灯室颜色跟随健康度
const beamColor = healthColor
const statusLabel = computed(() => props.percentage >= 80 ? 'HEALTHY' : props.percentage >= 50 ? 'WATCH' : 'ALERT')
const gaugeTrackColor = 'var(--border-color)'

// —— 光束：健康度越高越长越亮；低于 50 闪烁告警 ——
const beamLen = computed(() => 50 + props.percentage * 0.8)            // 50 → 130
const beamOpacity = computed(() => 0.18 + (props.percentage / 100) * 0.45)   // 0.18 → 0.63
const beamLineOpacity = computed(() => 0.3 + (props.percentage / 100) * 0.5) // 0.3 → 0.8
const beamBulbOpacity = computed(() => 0.55 + (props.percentage / 100) * 0.45) // 0.55 → 1.0
const swayDur = computed(() => (props.percentage >= 80 ? 7 : props.percentage >= 50 ? 5 : 3.5) + 's')
const beamPoints = computed(() => {
  const l = beamLen.value
  const w = Math.max(14, l * 0.22)
  return `-9,0 ${l},-${w} ${l},${w} -9,0`
})

// —— 半环仪表 ——
const arcLen = Math.PI * arcR // ≈ 138.23
const arcOffset = computed(() => arcLen * (1 - clampPercent(props.percentage) / 100))
const polar = (r: number, deg: number) => {
  const rad = (deg * Math.PI) / 180
  return { x: r * Math.cos(rad), y: r * Math.sin(rad) }
}
const gaugeTicks = computed(() => {
  const ticks: { v: number; major: boolean; color?: string; inner: { x: number; y: number }; outer: { x: number; y: number }; label: { x: number; y: number } }[] = []
  for (let v = 0; v <= 100; v += 10) {
    const deg = -180 + v * 1.8
    const major = v % 25 === 0
    const color = major ? (v >= 80 ? PALETTE.mint : v >= 50 ? PALETTE.amber : PALETTE.rose) : undefined
    ticks.push({
      v, major, color,
      inner: polar(major ? 36 : 40, deg),
      outer: polar(46, deg),
      label: polar(33, deg),
    })
  }
  return ticks
})
const needleAngle = computed(() => -180 + clampPercent(props.percentage) * 1.8)
const needle = computed(() => polar(30, needleAngle.value))

// —— 塔身 ——
const stripeCount = computed(() => Math.ceil(clampPercent(props.percentage) / 16.67))
const rivets = computed(() => {
  const out: { id: string; x: number; y: number }[] = []
  for (let i = 0; i < 4; i++) {
    const y = -16 - i * 14
    out.push({ id: `l-${i}`, x: -15.5, y })
    out.push({ id: `r-${i}`, x: 15.5, y })
  }
  return out
})

function clampPercent(v: number) {
  return Math.min(Math.max(v, 0), 100)
}
</script>

<style scoped>
.lighthouse-wrap {
  overflow: visible;
}
/* 半环健康弧 / 指针的平滑过渡 */
.arc-animate {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.34, 1.56, 0.64, 1), x2 0.8s cubic-bezier(0.34, 1.56, 0.64, 1), y2 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}
/* 低健康度告警闪烁（只作用于 opacity，不影响 SMIL 摆动） */
@keyframes beacon-flicker {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.95; }
}
.beacon-flicker {
  animation: beacon-flicker 0.8s ease-in-out infinite;
}
</style>
