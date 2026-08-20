<template>
  <div
    ref="stageEl"
    class="relative shrink-0 overflow-hidden select-none"
    style="height: 340px; background: radial-gradient(ellipse at 50% 60%, #12103a 0%, #08081a 50%, #040412 100%);"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
  >
    <!-- 深空微粒背景 -->
    <div class="absolute inset-0 opacity-40">
      <div v-for="p in 30" :key="p"
        class="absolute rounded-full"
        :style="{
          width: (0.5 + (p % 3) * 0.4) + 'px',
          height: (0.5 + (p % 3) * 0.4) + 'px',
          top: ((p * 37 + 13) % 100) + '%',
          left: ((p * 53 + 7) % 100) + '%',
          backgroundColor: 'rgba(255,255,255,' + (0.15 + (p % 5) * 0.08) + ')',
          animation: p % 3 === 0 ? 'star-twinkle ' + (2 + p % 3) + 's ease-in-out infinite' : 'none',
          animationDelay: (p * 0.3) + 's',
        }"
      />
    </div>

    <!-- 3D 星座容器 -->
    <div
      class="absolute inset-0 flex items-center justify-center"
      :style="{
        perspective: '700px',
        perspectiveOrigin: '50% 55%',
      }"
    >
      <div
        class="relative"
        :style="{
          width: '280px', height: '280px',
          transformStyle: 'preserve-3d',
          transform: `rotateY(${baseRotation + dragRotY + (isDragging ? 0 : mouseX * 0.15)}deg) rotateX(${dragRotX + (isDragging ? 0 : mouseY * 0.1)}deg)`,
          transition: isDragging ? 'none' : dragReturning ? 'transform 2s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : mouseX === 0 && mouseY === 0 ? 'transform 60s linear infinite' : 'transform 0.15s ease-out',
        }"
      >
        <!-- 连接线 -->
        <div
          v-for="(line, li) in activeLines" :key="'l'+li"
          class="absolute rounded-full origin-center transition-opacity duration-400"
          :style="{
            top: '50%', left: '50%',
            width: line.len + 'px',
            height: '1px',
            background: 'linear-gradient(90deg, ' + line.c1 + '44, ' + line.c2 + '44)',
            transform: `translate3d(${line.x1}px, ${line.y1}px, ${line.z1}px) rotateY(${line.rotY}deg) rotateX(${line.rotX}deg)`,
            opacity: lineOpacity(line),
          }"
        />

        <!-- 幽灵星点 -->
        <div
          v-for="d in dimensions" :key="'ghost_'+d.key"
          class="absolute rounded-full transition-all duration-400"
          :style="{
            width: ghostSize(d) + 'px', height: ghostSize(d) + 'px',
            top: '50%', left: '50%',
            marginLeft: ghostSize(d) / -2 + 'px',
            marginTop: ghostSize(d) / -2 + 'px',
            background: `radial-gradient(circle, ${d.color}55 0%, transparent 70%)`,
            boxShadow: `0 0 ${ghostSize(d)}px ${d.color}33`,
            transform: `translate3d(${starPos(d, true).x}px, ${starPos(d, true).y}px, ${starPos(d, true).z}px)`,
            opacity: hoveredStar ? 0 : 1,
          }"
        />

        <!-- 维度恒星 -->
        <div
          v-for="d in dimensions" :key="d.key"
          class="absolute rounded-full cursor-pointer"
          :style="starWrapperStyle(d)"
          @mouseenter="$emit('hoverStar', d.key)"
          @mouseleave="$emit('hoverStar', null)"
          @click.stop="onStarClick(d.key)"
        >
          <div
            class="w-full h-full rounded-full transition-all"
            :class="{ 'animate-star-burst': burstKey === d.key }"
            :style="{
              background: `radial-gradient(circle at 40% 35%, rgba(255,255,255,0.9), ${d.color}cc 50%, ${d.color}22 80%, transparent 100%)`,
              boxShadow: starGlowEnhanced(d),
              animation: starAnimation(d),
              transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
            }"
          />
          <div
            class="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2 py-1 rounded-lg text-[10px] font-bold whitespace-nowrap transition-opacity pointer-events-none z-20"
            :style="{
              background: 'rgba(8,8,24,0.9)',
              border: '1px solid ' + d.color + '44',
              color: d.color,
              opacity: hoveredStar === d.key ? 1 : 0,
            }"
          >
            {{ d.label }} {{ d.value }}
          </div>
        </div>

        <!-- 轨迹环 -->
        <div
          v-if="topDimension"
          class="absolute rounded-full"
          :style="{
            width: '8px', height: '8px',
            top: '50%', left: '50%',
            marginLeft: '-4px', marginTop: '-4px',
            background: 'transparent',
            border: '1px solid ' + topDimension.color + '66',
            borderRadius: '50%',
            transform: `translate3d(${starPos(topDimension, false).x}px, ${starPos(topDimension, false).y}px, ${starPos(topDimension, false).z}px)`,
            animation: 'orbit-ring 3s linear infinite',
            opacity: hoveredStar ? 0 : 0.25,
          }"
        />
      </div>
    </div>

    <!-- 图例 -->
    <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2 text-[9px]"
      style="color: var(--text-muted); background: rgba(8,8,24,0.7); padding: 3px 10px; border-radius: 999px; border: 1px solid rgba(99,102,241,0.1);">
      <span class="w-1.5 h-1.5 rounded-full" style="background: #6366f1; box-shadow: 0 0 6px #6366f1;"></span> 高值
      <span class="w-1.5 h-1.5 rounded-full" style="background: #6366f1; opacity: 0.3;"></span> 低值
      <span class="ml-2">| 拖拽旋转 · 点击恒星探索维度</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ProfileDimension } from '@/stores/profileModeling'

const props = defineProps<{
  dimensions: ProfileDimension[]
  hoveredStar: string | null
}>()

const emit = defineEmits<{
  hoverStar: [key: string | null]
  focusDimension: [key: string]
}>()

// ── 鼠标 / 拖拽状态 ──
const mouseX = ref(0)
const mouseY = ref(0)
const isDragging = ref(false)
const dragRotY = ref(0)
const dragRotX = ref(0)
const dragReturning = ref(false)
let dragStartX = 0
let dragStartY = 0
let dragBaseY = 0
let dragBaseX = 0
let resumeTimer: ReturnType<typeof setTimeout> | null = null

// ── 自转 ──
const baseRotation = ref(0)
let rotTimer: number | undefined
if (typeof window !== 'undefined') {
  rotTimer = window.setInterval(() => {
    if (!isDragging.value) baseRotation.value += 0.15
  }, 50)
}

// ── 内部状态 ──
const burstKey = ref<string | null>(null)

function onStarClick(key: string) {
  burstKey.value = key
  setTimeout(() => { burstKey.value = null }, 400)
  emit('focusDimension', key)
}

// ── 事件处理 ──
function onMouseDown(e: MouseEvent) {
  isDragging.value = true
  dragReturning.value = false
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragBaseY = dragRotY.value
  dragBaseX = dragRotX.value
  if (resumeTimer) { clearTimeout(resumeTimer); resumeTimer = null }
}

function onMouseMove(e: MouseEvent) {
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()

  if (isDragging.value) {
    const dx = e.clientX - dragStartX
    const dy = e.clientY - dragStartY
    dragRotY.value = dragBaseY + dx * 0.3
    dragRotX.value = dragBaseX + dy * 0.2 * -1
  } else {
    mouseX.value = ((e.clientX - rect.left) / rect.width - 0.5) * 2
    mouseY.value = ((e.clientY - rect.top) / rect.height - 0.5) * 2 * -1
  }
}

function onMouseUp() {
  if (!isDragging.value) return
  isDragging.value = false
  scheduleDragReturn()
}

function onMouseLeave() {
  mouseX.value = 0
  mouseY.value = 0
  if (isDragging.value) {
    isDragging.value = false
    scheduleDragReturn()
  }
}

function scheduleDragReturn() {
  dragReturning.value = true
  resumeTimer = setTimeout(() => {
    dragRotY.value = 0
    dragRotX.value = 0
    setTimeout(() => { dragReturning.value = false }, 2100)
  }, 2000)
}

// ── 星体定位与尺寸 ──
function starPos(d: ProfileDimension, isGhost: boolean): { x: number; y: number; z: number } {
  const dims = props.dimensions
  const idx = dims.findIndex(dd => dd.key === d.key)
  const count = dims.length || 6
  const angle = (idx / count) * Math.PI * 2
  const ringRadius = 100

  const x = Math.cos(angle) * ringRadius
  const v = isGhost ? d.previousValue : d.value
  const y = ((v / 100) - 0.5) * -70
  const z = Math.sin(angle) * ringRadius * 0.6

  return { x: Math.round(x), y: Math.round(y), z: Math.round(z) }
}

function starRadius(d: ProfileDimension): number {
  return 4 + (d.value / 100) * 12
}

function ghostSize(d: ProfileDimension): number {
  return 2 + (d.previousValue / 100) * 8
}

// ── 星体样式 ──
function isStarFocused(d: ProfileDimension): boolean {
  return props.hoveredStar === d.key
}

function starDimmed(d: ProfileDimension): boolean {
  return props.hoveredStar !== null && props.hoveredStar !== d.key
}

function starWrapperStyle(d: ProfileDimension) {
  const r = starRadius(d)
  const dbl = r * 2
  const scale = isStarFocused(d) ? 1.4 : 1
  const opacity = starDimmed(d) ? 0.25 : 1
  const filter = starDimmed(d) ? 'blur(1.5px)' : 'none'
  const zIndex = isStarFocused(d) ? 30 : 5
  const pos = starPos(d, false)

  return {
    width: dbl + 'px',
    height: dbl + 'px',
    top: '50%',
    left: '50%',
    marginLeft: -r + 'px',
    marginTop: -r + 'px',
    transform: `translate3d(${pos.x}px, ${pos.y}px, ${pos.z}px) scale(${scale})`,
    transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
    zIndex,
    opacity,
    filter,
  }
}

function starGlowEnhanced(d: ProfileDimension): string {
  const r = starRadius(d)
  const mult = isStarFocused(d) ? 2.5 : 1
  return `0 0 ${r * mult}px ${d.color}, 0 0 ${r * 2 * mult}px ${d.color}44, 0 0 ${r * 3 * mult}px ${d.color}22`
}

function starAnimation(d: ProfileDimension): string {
  if (isStarFocused(d)) return 'star-pulse 0.8s ease-in-out infinite'
  if (starDimmed(d)) return 'none'
  if (d.value > 75) return `star-pulse ${1.5 + ((100 - d.value) / 100) * 2}s ease-in-out infinite`
  return 'none'
}

// ── 连接线 ──
const constellationLines = computed(() => {
  const dims = props.dimensions
  if (dims.length < 2) return []
  return dims.map((d, i) => {
    const next = dims[(i + 1) % dims.length]
    const p1 = starPos(d, false)
    const p2 = starPos(next, false)
    const dx = p2.x - p1.x
    const dy = p2.y - p1.y
    const dz = p2.z - p1.z
    const len = Math.sqrt(dx * dx + dy * dy + dz * dz)
    const midX = (p1.x + p2.x) / 2
    const midY = (p1.y + p2.y) / 2
    const midZ = (p1.z + p2.z) / 2
    const rotY = Math.atan2(dx, dz) * (180 / Math.PI)
    const horizDist = Math.sqrt(dx * dx + dz * dz)
    const rotX = Math.atan2(dy, horizDist) * (180 / Math.PI) * -1
    return { x1: midX, y1: midY, z1: midZ, len: Math.round(len), rotY: Math.round(rotY), rotX: Math.round(rotX), c1: d.color, c2: next.color, key1: d.key, key2: next.key }
  })
})

const activeLines = computed(() => {
  if (!props.hoveredStar) return constellationLines.value
  return constellationLines.value.filter(l => l.key1 === props.hoveredStar || l.key2 === props.hoveredStar)
})

function lineOpacity(line: { key1: string; key2: string }): number {
  if (!props.hoveredStar) return 0.35
  if (line.key1 === props.hoveredStar || line.key2 === props.hoveredStar) return 0.5
  return 0
}

const topDimension = computed(() => {
  if (!props.dimensions.length) return null
  return props.dimensions.reduce((a, b) => a.value > b.value ? a : b)
})
</script>

<style scoped>
@keyframes star-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

@keyframes star-twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.9; }
}

@keyframes orbit-ring {
  0% { transform: scale(1) rotate(0deg); opacity: 0.4; }
  100% { transform: scale(2) rotate(180deg); opacity: 0; }
}

@keyframes star-burst {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.6); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

.animate-star-burst {
  animation: star-burst 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>
