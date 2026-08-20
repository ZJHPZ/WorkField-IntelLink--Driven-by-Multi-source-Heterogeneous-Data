<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-space-800"><img :src="mapIcon" class="icon-title" alt="" /> 学习路径</h1>
        <p class="text-gray-400 text-sm mt-1">{{ learningStore.currentPath?.title || '大数据工程师成长之路' }}</p>
      </div>
      <div class="text-right">
        <div class="text-sm text-gray-400">预计完成</div>
        <div class="text-lg font-bold text-brand-600">{{ learningStore.currentPath?.estimatedDuration || '90天' }}</div>
      </div>
    </div>

    <!-- Overall progress -->
    <div class="glass-card rounded-2xl p-5">
      <div class="flex items-center gap-6">
        <ProgressRing :percentage="learningStore.overallProgress" :size="80" :stroke-width="6" color="url(#pathGradient)" />
        <div class="flex-1">
          <div class="flex justify-between text-sm mb-1">
            <span class="text-gray-500">总进度</span>
            <span class="font-bold text-space-800">{{ Math.round(learningStore.overallProgress) }}%</span>
          </div>
          <div class="text-sm text-gray-400 space-y-0.5">
            <p>已完成 {{ learningStore.masteredCount }} / {{ learningStore.totalTopics }} 个知识点</p>
            <p>累计学习 {{ learningStore.currentPath?.totalStudyHours || 0 }} 小时</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Stages timeline -->
    <div class="relative">
      <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 hidden md:block" />

      <div class="space-y-4 spring-list">
        <div v-for="(stage, index) in stages" :key="stage.stageId"
          class="md:ml-16 relative">
          <div class="hidden md:flex absolute -left-[3.15rem] top-6 w-6 h-6 rounded-full border-4 border-white z-10 shadow-sm"
            :class="dotClass(stage.status)" />

          <div class="glass-card card-3d rounded-2xl p-5 cursor-pointer"
            :class="stage.status === 'in_progress' ? 'ring-2 ring-brand-300/50' : ''"
            @click="selectStage(stage)">
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-3">
                <span class="text-lg font-bold text-space-800">{{ stage.title }}</span>
                <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                  :class="statusBadgeClass(stage.status)">{{ statusLabel(stage.status) }}</span>
              </div>
              <span class="text-xs text-gray-400">{{ stage.estimatedDays }}天</span>
            </div>
            <div class="flex flex-wrap gap-2 mb-3">
              <span v-for="topic in stage.topics" :key="topic"
                class="text-xs px-2.5 py-1 bg-brand-50 text-brand-600 rounded-full font-medium">
                {{ topic }}
              </span>
            </div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-700"
                :class="stage.status === 'completed' ? 'bg-mint-500' : 'bg-brand-500'"
                :style="{ width: stage.progress + '%' }" />
            </div>
            <p class="text-xs text-gray-400 mt-1.5">{{ stage.progress }}% 完成</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Radar chart for mastery -->
    <div class="glass-card rounded-2xl p-5">
      <h3 class="text-base font-semibold text-space-800 mb-4"><img :src="pieChartIcon" class="icon-title" alt="" /> 知识掌握度雷达图</h3>
      <div v-if="radarReady" ref="radarChart" class="w-full h-80"></div>
      <div v-else class="py-8 text-center text-gray-400">加载中...</div>
    </div>

    <!-- SVG defs -->
    <svg width="0" height="0" class="absolute">
      <defs>
        <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#6366f1" />
          <stop offset="50%" stop-color="#a855f7" />
          <stop offset="100%" stop-color="#06b6d4" />
        </linearGradient>
      </defs>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useLearningStore } from '@/stores/learning'
import type { LearningStage } from '@/stores/learning'
import ProgressRing from '@/components/common/ProgressRing.vue'
import * as echarts from 'echarts'
import mapIcon from '@/assets/icons/fang/map-svgrepo-com.svg'
import pieChartIcon from '@/assets/icons/jian/pie-chart-svgrepo-com.svg'

const learningStore = useLearningStore()
const stages = computed(() => learningStore.currentPath?.stages || [])
const radarChart = ref<HTMLElement | null>(null)
const radarReady = ref(false)

function dotClass(status: LearningStage['status']) {
  return {
    completed: 'bg-mint-500',
    in_progress: 'bg-brand-500 animate-pulse-slow shadow-lg shadow-brand-500/40',
    available: 'bg-gray-300',
    locked: 'bg-gray-200',
  }[status] || 'bg-gray-200'
}

function statusBadgeClass(status: LearningStage['status']) {
  return {
    completed: 'bg-mint-50 text-mint-600',
    in_progress: 'bg-brand-50 text-brand-600',
    available: 'bg-gray-100 text-gray-500',
    locked: 'bg-gray-100 text-gray-400',
  }[status] || 'bg-gray-100 text-gray-400'
}

function statusLabel(status: LearningStage['status']) {
  return {
    completed: '已完成',
    in_progress: '进行中',
    available: '可开始',
    locked: '未解锁',
  }[status] || '未知'
}

function selectStage(stage: LearningStage) {
  // Could open a modal or navigate to detailed view
}

onMounted(async () => {
  await learningStore.fetchLearningPath()
  await learningStore.fetchTopicMastery()
  await nextTick()
  renderRadar()
})

function renderRadar() {
  if (!radarChart.value) return
  const chart = echarts.init(radarChart.value)
  const topics = learningStore.topicMasteryList
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { data: ['当前掌握度', '目标掌握度'], bottom: 0, textStyle: { color: '#64748b' } },
    radar: {
      center: ['50%', '50%'],
      radius: '70%',
      indicator: topics.map(t => ({ name: t.name, max: 1 })),
      axisName: { fontSize: 11, color: '#64748b' },
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: topics.map(t => t.masteryLevel),
          name: '当前掌握度',
          areaStyle: { color: 'rgba(99, 102, 241, 0.2)' },
          lineStyle: { color: '#6366f1', width: 2 },
          itemStyle: { color: '#6366f1' },
        },
        {
          value: topics.map(() => 0.85),
          name: '目标掌握度',
          areaStyle: { color: 'rgba(16, 185, 129, 0.08)' },
          lineStyle: { color: '#10b981', width: 1.5, type: 'dashed' as const },
          itemStyle: { color: '#10b981' },
        },
      ],
    }],
  })
  radarReady.value = true
  window.addEventListener('resize', () => chart.resize())
}
</script>

<style scoped>
.icon-title {
  width: 1.5em;
  height: 1.5em;
  display: inline-block;
  vertical-align: middle;
}
</style>
