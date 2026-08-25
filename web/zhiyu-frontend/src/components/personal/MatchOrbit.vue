<template>
  <div class="orbit-wrap relative" :style="{ height: height + 'px' }" ref="containerRef">
    <!-- 中心用户头像 -->
    <div class="absolute z-20 flex items-center justify-center"
      :style="{ left: cx + 'px', top: cy + 'px', transform: 'translate(-50%, -50%)' }">
      <div class="relative">
        <!-- 六角形头像 -->
        <svg width="64" height="64" viewBox="0 0 64 64">
          <polygon points="32,2 58,17 58,47 32,62 6,47 6,17"
            :fill="'url(#' + centerGradId + ')'" stroke="var(--brand-400)" stroke-width="1.5" />
          <defs>
            <linearGradient :id="centerGradId" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="var(--brand-600)" />
              <stop offset="100%" stop-color="var(--brand-400)" />
            </linearGradient>
          </defs>
        </svg>
        <span class="absolute inset-0 flex items-center justify-center text-white font-bold text-xl"
          style="font-family:system-ui">{{ avatarLetter }}</span>
        <!-- 外环发光 -->
        <div class="absolute inset-[-8px] rounded-full animate-star-glow"
          style="--glow-color:color-mix(in srgb, var(--brand-500) 30%, transparent);border-radius:50%"></div>
      </div>
      <div class="absolute mt-2 text-center" style="top:100%;left:50%;transform:translateX(-50%);white-space:nowrap">
        <div class="text-xs font-bold" style="color:var(--text-primary)">{{ userName }}</div>
        <div class="text-xs font-mono" style="color:var(--text-muted);font-size:10px">{{ skillCount }} SKILLS</div>
      </div>
    </div>

    <!-- 轨道环 SVG -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none" :viewBox="`0 0 ${svgW} ${svgH}`">
      <!-- 轨道环 -->
      <ellipse v-for="(track, i) in tracks" :key="i"
        :cx="cx" :cy="cy" :rx="track.rx" :ry="track.ry"
        fill="none" stroke="var(--border-color)" stroke-width="1"
        stroke-dasharray="4 8" opacity="0.3" />
      <!-- 轨道高亮弧 -->
      <ellipse v-for="(track, i) in tracks" :key="`h-${i}`"
        :cx="cx" :cy="cy" :rx="track.rx" :ry="track.ry"
        fill="none" :stroke="track.color" stroke-width="1.5"
        :stroke-dasharray="`${track.highlightLen} ${track.rx * 6}`"
        :stroke-dashoffset="track.highlightOffset"
        opacity="0.4" />
      <!-- 刻度标记 -->
      <g v-for="(track, i) in tracks" :key="`t-${i}`">
        <circle v-for="tick in track.ticks" :key="tick.id"
          :cx="tick.x" :cy="tick.y" r="1.5"
          :fill="track.color" opacity="0.3" />
      </g>
    </svg>

    <!-- 轨道上的岗位卡片 -->
    <div v-for="(orbit, i) in orbits" :key="orbit.match.id"
      class="absolute z-10"
      :style="{
        left: cx + 'px', top: cy + 'px',
        width: '0px', height: '0px',
        animation: `orbit ${orbit.duration}s linear infinite${i % 2 ? ' reverse' : ''}`
      }">
      <!-- 卡片（反向旋转保持水平） -->
      <div class="absolute cursor-pointer transition-all hover:scale-110"
        :style="{
          left: orbit.offsetX + 'px', top: orbit.offsetY + 'px',
          transform: 'translate(-50%, -50%)',
          animation: `orbit ${orbit.duration}s linear infinite${i % 2 ? '' : ' reverse'}`
        }"
        @click="$emit('match-click', orbit.match)">
        <div class="panel-industrial p-2 px-3 shadow-deep" style="min-width:120px">
          <div class="flex items-center gap-2 mb-1">
            <ProgressRing :percentage="orbit.match.matchRate" :size="28" :stroke-width="2"
              :color="orbit.color" :show-sign="false" />
            <div class="min-w-0">
              <div class="text-xs font-bold truncate" style="max-width:90px;color:var(--text-primary)">
                {{ orbit.match.positionName }}
              </div>
              <div class="text-xs font-mono" style="color:var(--text-muted);font-size:9px">
                {{ orbit.match.company }}
              </div>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-mono font-bold" :style="{ color: orbit.color }">
              {{ orbit.match.matchRate }}%
            </span>
            <span class="tag-plate" style="font-size:7px;padding:1px 4px">
              ORBIT {{ i + 1 }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, useId, onMounted, onUnmounted } from 'vue'
import ProgressRing from '@/components/common/ProgressRing.vue'
import { PALETTE, getBrandColor } from '@/utils/color'

interface Match {
  id: string
  positionName: string
  company: string
  matchRate: number
  salaryRange?: string
}

const props = withDefaults(defineProps<{
  matches: Match[]
  userName?: string
  avatarLetter?: string
  skillCount?: number
  height?: number
}>(), {
  userName: '用户',
  avatarLetter: 'U',
  skillCount: 0,
  height: 400,
})

defineEmits<{ 'match-click': [match: Match] }>()

const containerRef = ref<HTMLDivElement | null>(null)
const centerGradId = useId()
const svgW = ref(500)
const svgH = computed(() => props.height)
const cx = computed(() => svgW.value / 2)
const cy = computed(() => svgH.value / 2)

// 轨道配色（主轨道跟随时装主题，次轨道 cyan/purple）
const trackColors = [getBrandColor(), PALETTE.cyan, PALETTE.purple]

function measure() {
  if (containerRef.value) svgW.value = containerRef.value.offsetWidth || 500
}
onMounted(() => {
  measure()
  window.addEventListener('resize', measure)
})
onUnmounted(() => window.removeEventListener('resize', measure))

// 轨道配置（最多3条）
const tracks = computed(() => {
  const configs = [
    { rx: 100, ry: 70, color: trackColors[0] },
    { rx: 160, ry: 110, color: trackColors[1] },
    { rx: 210, ry: 145, color: trackColors[2] },
  ]
  return configs.map((c, i) => ({
    ...c,
    highlightLen: 40 + i * 15,
    highlightOffset: i * -60,
    ticks: Array.from({ length: 12 }, (_, j) => {
      const angle = (j / 12) * Math.PI * 2
      return {
        id: `${i}-${j}`,
        x: cx.value + c.rx * Math.cos(angle),
        y: cy.value + c.ry * Math.sin(angle),
      }
    }),
  }))
})

// 轨道上的岗位
const orbits = computed(() => {
  return props.matches.slice(0, 3).map((match, i) => {
    const track = tracks.value[i]
    return {
      match,
      duration: 18 + i * 6,
      offsetX: track.rx,
      offsetY: 0,
      color: trackColors[i],
    }
  })
})
</script>

<style scoped>
.orbit-wrap {
  overflow: visible;
}
</style>
