<template>
  <div class="evolution-timeline" :style="{ color: 'var(--text-primary)' }">
    <!-- 时间轴轨道 -->
    <div class="relative">
      <!-- 轨道背景 -->
      <div class="h-2 rounded-full" :style="{ backgroundColor: 'var(--border-color)' }">
        <!-- 已播放进度 -->
        <div
          class="h-full rounded-full bg-brand-gradient transition-all duration-500"
          :style="{ width: progressPercent + '%' }"
        />
      </div>

      <!-- 时间标记点 -->
      <div
        v-for="(event, idx) in timeline"
        :key="event.date"
        class="absolute top-1/2 -translate-y-1/2 cursor-pointer group"
        :style="{ left: ((idx / (timeline.length - 1)) * 100) + '%' }"
        @click="$emit('select', idx)"
      >
        <!-- 标记圆点 -->
        <div
          class="w-3.5 h-3.5 rounded-full transition-all duration-300"
          :class="idx === selectedIndex ? 'bg-brand-500 ring-4 ring-brand-500/30 scale-150' :
                  idx <= selectedIndex ? 'bg-brand-400' : 'bg-gray-400'"
        />
        <!-- 日期标签 -->
        <div
          class="absolute top-4 left-1/2 -translate-x-1/2 text-xs font-medium whitespace-nowrap transition-opacity duration-200"
          :class="idx === selectedIndex ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'"
          :style="{ color: idx === selectedIndex ? 'var(--brand-500)' : 'var(--text-muted)' }"
        >
          {{ event.date }}
        </div>
      </div>

      <!-- 当前位置指示器 -->
      <div
        v-if="timeline.length > 0"
        class="absolute -top-1 w-5 h-5 rounded-full border-2 border-white bg-brand-500 shadow-lg shadow-brand-500/30 transition-all duration-500"
        :style="{ left: `calc(${progressPercent}% - 10px)` }"
      />
    </div>

    <!-- 选中时间点详情 -->
    <div v-if="currentEvent" class="mt-8 p-4 rounded-xl glass-card">
      <div class="flex items-center justify-between mb-3">
        <h4 class="font-semibold">{{ currentEvent.label }}</h4>
        <span class="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-700">
          {{ currentEvent.date }}
        </span>
      </div>

      <!-- 一句话总结 -->
      <p class="text-sm mb-3" :style="{ color: 'var(--text-secondary)' }">
        {{ currentEvent.summary }}
      </p>

      <!-- 数据源 -->
      <div class="flex flex-wrap gap-1.5 mb-3">
        <span
          v-for="src in currentEvent.dataSources"
          :key="src"
          class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500"
        >{{ src }}</span>
      </div>

      <!-- 技能变化摘要 -->
      <div class="flex gap-3 text-xs" :style="{ color: 'var(--text-muted)' }">
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-mint-500"></span>
          新增 {{ stats.added }}
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-rose-500"></span>
          删除 {{ stats.removed }}
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-brand-500"></span>
          升级 {{ stats.upgraded }}
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-amber-500"></span>
          降级 {{ stats.downgraded }}
        </span>
      </div>
    </div>

    <!-- 播放控件 -->
    <div v-if="timeline.length > 0" class="flex items-center gap-3 mt-4">
      <button
        class="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
        :style="{ color: 'var(--text-secondary)' }"
        @click="togglePlay"
      >
        <span>{{ isPlaying ? '⏸' : '▶' }}</span>
        {{ isPlaying ? '暂停' : '自动播放' }}
      </button>
      <div class="flex items-center gap-1 text-xs" :style="{ color: 'var(--text-muted)' }">
        <span>速度</span>
        <button
          v-for="s in [1, 2, 4]"
          :key="s"
          class="px-1.5 py-0.5 rounded"
          :class="speed === s ? 'bg-brand-100 text-brand-700' : ''"
          @click="$emit('update:speed', s); speed = s"
        >{{ s }}x</button>
      </div>
      <button
        class="text-xs px-3 py-1.5 rounded-lg border transition-colors ml-auto"
        :style="{ color: 'var(--text-secondary)', borderColor: 'var(--border-color)' }"
        @click="$emit('toggle-diff')"
      >
        📊 对比模式
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import type { TimelineEvent } from '@/stores/enterprise'

const props = withDefaults(defineProps<{
  timeline: TimelineEvent[]
  selectedIndex?: number
  autoPlay?: boolean
  speed?: number
}>(), {
  selectedIndex: 0,
  autoPlay: false,
  speed: 1,
})

const emit = defineEmits<{
  (e: 'select', index: number): void
  (e: 'update:speed', speed: number): void
  (e: 'toggle-diff'): void
}>()

const speed = ref(props.speed)
const isPlaying = ref(props.autoPlay)
let playTimer: ReturnType<typeof setInterval> | null = null

const progressPercent = computed(() =>
  props.timeline.length > 1 ? (props.selectedIndex / (props.timeline.length - 1)) * 100 : 0
)

const currentEvent = computed(() => props.timeline[props.selectedIndex] || null)

const stats = computed(() => {
  if (!currentEvent.value) return { added: 0, removed: 0, upgraded: 0, downgraded: 0 }
  const skills = currentEvent.value.skills
  return {
    added: skills.filter(s => s.change === 'added').length,
    removed: skills.filter(s => s.change === 'removed').length,
    upgraded: skills.filter(s => s.change === 'upgraded').length,
    downgraded: skills.filter(s => s.change === 'downgraded').length,
  }
})

function togglePlay() {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) startPlay()
  else stopPlay()
}

function startPlay() {
  stopPlay()
  const interval = 2000 / speed.value
  playTimer = setInterval(() => {
    const next = (props.selectedIndex + 1) % props.timeline.length
    if (next === 0) { isPlaying.value = false; stopPlay(); return }
    emit('select', next)
  }, interval)
}

function stopPlay() {
  if (playTimer) { clearInterval(playTimer); playTimer = null }
}

watch(() => props.autoPlay, (v) => { if (v) { isPlaying.value = true; startPlay() } })

onUnmounted(() => stopPlay())
</script>
