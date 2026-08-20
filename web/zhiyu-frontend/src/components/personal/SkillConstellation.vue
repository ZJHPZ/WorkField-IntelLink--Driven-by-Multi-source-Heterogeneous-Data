<template>
  <div class="constellation-wrap relative" :style="{ height: height + 'px' }">
    <!-- 星轨环 — 工业坐标环 -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none" :viewBox="`0 0 ${w} ${h}`">
      <!-- 同心轨道环 -->
      <circle v-for="r in orbitRadii" :key="r" :cx="cx" :cy="cy" :r="r"
        fill="none" :stroke="ringColor" stroke-width="0.5" stroke-dasharray="3 6" opacity="0.3" />
      <!-- 十字坐标线 -->
      <line :x1="cx" :y1="cy - maxR" :x2="cx" :y2="cy + maxR" :stroke="ringColor" stroke-width="0.5" opacity="0.15" />
      <line :x1="cx - maxR" :y1="cy" :x2="cx + maxR" :y2="cy" :stroke="ringColor" stroke-width="0.5" opacity="0.15" />
      <!-- 刻度标记 -->
      <g v-for="angle in tickAngles" :key="angle">
        <line
          :x1="cx + (maxR - 6) * Math.cos(angle)" :y1="cy + (maxR - 6) * Math.sin(angle)"
          :x2="cx + maxR * Math.cos(angle)" :y2="cy + maxR * Math.sin(angle)"
          :stroke="ringColor" stroke-width="0.8" opacity="0.25" />
      </g>
      <!-- 类别标签 -->
      <g v-for="(cat, i) in categoryLabels" :key="cat.name">
        <text :x="cat.x" :y="cat.y" text-anchor="middle" dominant-baseline="middle"
          fill="currentColor" font-size="9" font-family="Courier New, monospace" font-weight="700"
          letter-spacing="0.08em" opacity="0.5" class="uppercase">
          {{ cat.name }}
        </text>
      </g>
      <!-- 星体连线（悬停时显示关联） -->
      <line v-for="conn in visibleConnections" :key="conn.id"
        :x1="conn.x1" :y1="conn.y1" :x2="conn.x2" :y2="conn.y2"
        :stroke="conn.color" stroke-width="1" opacity="0.4"
        stroke-dasharray="2 3" />
    </svg>

    <!-- 星体节点 -->
    <div v-for="star in stars" :key="star.id"
      class="star-node absolute flex items-center justify-center"
      :style="starStyle(star)"
      @mouseenter="onStarEnter(star)"
      @mouseleave="onStarLeave"
      @click="$emit('skill-click', star.skill)">
      <!-- 光晕 -->
      <div class="absolute rounded-full animate-star-glow" :style="glowStyle(star)"></div>
      <!-- 星体核心 -->
      <div class="relative z-10 rounded-full" :style="coreStyle(star)"></div>
      <!-- 标签 -->
      <transition name="fade">
        <div v-if="hoveredStar?.id === star.id || selectedStar?.id === star.id"
          class="absolute z-20 whitespace-nowrap pointer-events-none"
          :style="{ top: '-32px', left: '50%', transform: 'translateX(-50%)' }">
          <div class="px-2 py-1 text-xs font-bold font-mono rounded-sm"
            style="background:var(--bg-card);border:1px solid var(--border-color);box-shadow:0 4px 12px rgba(0,0,0,0.3)">
            <span :style="{ color: star.color }">{{ star.skill.name }}</span>
            <span class="ml-1" style="color:var(--text-muted)">{{ star.skill.freshness }}%</span>
          </div>
        </div>
      </transition>
    </div>

    <!-- 中心标识 -->
    <div class="absolute flex flex-col items-center justify-center pointer-events-none"
      :style="{ left: cx + 'px', top: cy + 'px', transform: 'translate(-50%, -50%)' }">
      <div class="text-xs font-mono font-bold tracking-wider" style="color:var(--text-muted);opacity:0.4">SKILLS</div>
      <div class="data-readout text-lg" style="color:var(--brand-400)">{{ skills.length }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Skill {
  id: string
  name: string
  category: string
  freshness: number
  level?: string
  status?: string
  marketDemand?: number
}

interface Star {
  id: string
  skill: Skill
  x: number
  y: number
  size: number
  brightness: number
  color: string
  categoryIndex: number
}

const props = withDefaults(defineProps<{
  skills: Skill[]
  height?: number
}>(), { height: 400 })

defineEmits<{ 'skill-click': [skill: Skill] }>()

const w = computed(() => 600)
const h = computed(() => props.height)
const cx = computed(() => w.value / 2)
const cy = computed(() => h.value / 2)
const maxR = computed(() => Math.min(w.value, h.value) / 2 - 40)

const ringColor = 'var(--border-color)'

// 类别颜色映射
const categoryColors: Record<string, string> = {
  'hard': '#818cf8',
  'tool': '#06b6d4',
  'framework': '#a855f7',
  'soft': '#10b981',
  'language': '#f59e0b',
  'default': '#6366f1',
}

// 按类别分组
const categories = computed(() => {
  const map = new Map<string, Skill[]>()
  props.skills.forEach(s => {
    const cat = s.category || 'default'
    if (!map.has(cat)) map.set(cat, [])
    map.get(cat)!.push(s)
  })
  return [...map.entries()]
})

// 轨道半径
const orbitRadii = computed(() => {
  const n = Math.max(categories.value.length, 1)
  return Array.from({ length: n }, (_, i) => ((i + 1) / (n + 1)) * maxR.value)
})

// 星体位置计算
const stars = computed<Star[]>(() => {
  const result: Star[] = []
  categories.value.forEach(([cat, skills], catIdx) => {
    const ringR = orbitRadii.value[catIdx] || maxR.value * 0.5
    const color = categoryColors[cat] || categoryColors.default
    const angleStep = (Math.PI * 2) / Math.max(skills.length, 1)
    const startAngle = -Math.PI / 2 + catIdx * 0.3 // 每类偏移一点

    skills.forEach((skill, i) => {
      const angle = startAngle + i * angleStep
      const jitter = (skill.freshness / 100) * 8 - 4 // 保鲜度影响微偏移
      const x = cx.value + (ringR + jitter) * Math.cos(angle)
      const y = cy.value + (ringR + jitter) * Math.sin(angle)
      const size = 6 + (skill.marketDemand || 50) / 20 // 重要度影响大小
      const brightness = 0.4 + (skill.freshness / 100) * 0.6

      result.push({ id: skill.id, skill, x, y, size, brightness, color, categoryIndex: catIdx })
    })
  })
  return result
})

// 类别标签位置
const categoryLabels = computed(() => {
  return categories.value.map(([name], i) => {
    const r = orbitRadii.value[i] || maxR.value * 0.5
    const angle = -Math.PI / 2 + i * 0.3 - 0.15
    return {
      name,
      x: cx.value + (r + 16) * Math.cos(angle),
      y: cy.value + (r + 16) * Math.sin(angle),
    }
  })
})

// 刻度角度
const tickAngles = computed(() => Array.from({ length: 24 }, (_, i) => (i * Math.PI * 2) / 24))

// 悬停状态
const hoveredStar = ref<Star | null>(null)
const selectedStar = ref<Star | null>(null)

function onStarEnter(star: Star) { hoveredStar.value = star }
function onStarLeave() { hoveredStar.value = null }

// 可见连线（悬停时显示同类别星体的连线）
const visibleConnections = computed(() => {
  const target = hoveredStar.value || selectedStar.value
  if (!target) return []
  return stars.value
    .filter(s => s.id !== target.id && s.categoryIndex === target.categoryIndex)
    .map(s => ({
      id: `${target.id}-${s.id}`,
      x1: target.x, y1: target.y,
      x2: s.x, y2: s.y,
      color: target.color,
    }))
})

// 样式计算
function starStyle(star: Star) {
  return {
    left: `${star.x - star.size / 2}px`,
    top: `${star.y - star.size / 2}px`,
    width: `${star.size}px`,
    height: `${star.size}px`,
    '--twinkle-speed': `${2 + star.brightness * 2}s`,
    animationDelay: `${star.id.charCodeAt(0) % 3}s`,
  }
}

function glowStyle(star: Star) {
  const s = star.size * 2.5
  return {
    width: `${s}px`, height: `${s}px`,
    left: `${-(s - star.size) / 2}px`,
    top: `${-(s - star.size) / 2}px`,
    background: `radial-gradient(circle, ${star.color}40 0%, transparent 70%)`,
    '--glow-color': `${star.color}60`,
    opacity: star.brightness,
  }
}

function coreStyle(star: Star) {
  return {
    width: `${star.size}px`, height: `${star.size}px`,
    background: `radial-gradient(circle at 35% 35%, ${star.color}cc, ${star.color}88)`,
    boxShadow: `0 0 ${star.size}px ${star.color}80`,
    opacity: star.brightness,
  }
}
</script>

<style scoped>
.constellation-wrap {
  position: relative;
  overflow: hidden;
}
.uppercase { text-transform: uppercase; }
</style>
