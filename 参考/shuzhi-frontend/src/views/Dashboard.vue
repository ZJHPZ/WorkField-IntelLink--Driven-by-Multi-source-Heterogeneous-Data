<template>
  <div class="space-y-5 animate-fade-in-up">
    <!-- 阶段完成庆祝弹窗 -->
    <StageCompleteModal
      :visible="showStageComplete"
      :title="celebrationData.title"
      :description="celebrationData.description"
      :icon="celebrationData.icon"
      :rewards="celebrationData.rewards"
      primary-action="进入下一阶段"
      next-route="/learning-path"
      @close="showStageComplete = false"
      @next="showStageComplete = false"
    />

    <!-- ===== 欢迎横幅 - AI 情绪化问候 ===== -->
    <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-brand-500 to-cyan-500 p-6 md:p-8 text-white shadow-xl shadow-brand-500/25">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-4 right-16 w-32 h-32 rounded-full bg-white blur-3xl"></div>
        <div class="absolute bottom-0 left-1/4 w-48 h-24 rounded-full bg-cyan-300 blur-3xl"></div>
      </div>
      <div class="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex-1">
          <h1 class="text-2xl md:text-3xl font-bold mb-1 flex items-center gap-2">
            欢迎回来，{{ userStore.profile.nickname }}
            <span class="inline-block animate-bounce-in ml-1">👋</span>
          </h1>
        </div>
        <div class="flex items-center gap-3">
          <div class="text-center px-4 py-3 bg-white/15 rounded-2xl backdrop-blur-sm">
            <div class="text-3xl font-extrabold tabular-nums">{{ learningStore.streakDays }}</div>
            <div class="text-xs text-white/70"><img :src="iconFan" class="hud-inline-icon" alt="" /> 连续学习</div>
          </div>
          <div class="text-center px-4 py-3 bg-white/15 rounded-2xl backdrop-blur-sm">
            <div class="text-3xl font-extrabold tabular-nums">{{ userStore.profile.currentLevel }}</div>
            <div class="text-xs text-white/70">⚡ 当前等级</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 舰桥 HUD 状态条 ===== -->
    <div class="glass-card rounded-2xl px-5 py-3.5">
      <div class="grid grid-cols-3 md:grid-cols-6 gap-2 text-center">
        <div v-for="item in hudItems" :key="item.label"
          class="group relative py-1.5 px-2 rounded-xl transition-all duration-200 cursor-default"
          :style="{ background: 'transparent' }"
          @mouseenter="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-card-hover)' }"
          @mouseleave="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }"
        >
          <img v-if="isImgIcon(item.icon)" :src="item.icon" class="hud-item-icon" alt="" />
          <span v-else class="text-xl">{{ item.icon }}</span>
          <div class="text-sm font-bold tabular-nums" style="color: var(--text-primary);">
            {{ item.value }}
            <span v-if="item.trend !== undefined" class="text-[10px] ml-0.5" :style="{ color: item.trendColor }">
              {{ item.trendArrow }}
            </span>
          </div>
          <div class="text-[10px]" style="color: var(--text-muted);">{{ item.label }}</div>
          <!-- Tooltip -->
          <div class="absolute -top-1 left-1/2 -translate-x-1/2 -translate-y-full px-2.5 py-1.5 rounded-lg text-[10px] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10"
            style="background: rgba(15,23,42,0.95); border: 1px solid rgba(99,102,241,0.3); color: var(--text-secondary);">
            {{ item.tooltip }}
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 主体: 双栏布局 ===== -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <!-- 左栏: 学习曲线 + 学习路径 -->
      <div class="space-y-5">
        <!-- 本周学习曲线 -->
        <div class="glass-card rounded-2xl p-5">
          <h3 class="text-base font-semibold mb-3 flex items-center gap-2" style="color: var(--text-primary);">
            <span><img :src="iconTrend" class="section-icon" alt="" /></span> 本周学习曲线
          </h3>
          <div ref="weekChartEl" class="w-full" style="height:200px"></div>
        </div>

        <!-- 学习路径 — 精简版: 当前 + 下一阶段 -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-semibold flex items-center gap-2" style="color: var(--text-primary);">
              <span><img :src="iconMap" class="section-icon" alt="" /></span> 学习路径
            </h3>
            <span v-if="learningStore.currentPath" class="text-xs font-medium px-2.5 py-1 rounded-full"
              style="background: rgba(99,102,241,0.1); color: var(--brand-400);">
              阶段 {{ learningStore.currentPath.currentStage }}/{{ learningStore.currentPath.totalStages }}
            </span>
          </div>

          <!-- 总进度条 -->
          <div class="h-2 rounded-full overflow-hidden mb-4" style="background: rgba(99,102,241,0.1);">
            <div class="h-full bg-energy-gradient rounded-full transition-all duration-700 flex items-center justify-end pr-1.5"
              :style="{ width: learningStore.overallProgress + '%' }">
              <span v-if="learningStore.overallProgress > 20" class="text-[9px] text-white font-bold">{{ Math.round(learningStore.overallProgress) }}%</span>
            </div>
          </div>

          <div v-if="learningStore.currentPath" class="space-y-3">
            <!-- 当前阶段 -->
            <div v-for="stage in visibleStages" :key="stage.stageId"
              class="flex items-center gap-3 p-3 rounded-xl transition-colors"
              :class="stage.status === 'in_progress' ? '' : ''"
              :style="stage.status === 'in_progress' ? { background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)' } : {}"
            >
              <div class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                :style="stageStyle(stage).dot">
                {{ stage.status === 'completed' ? '✓' : stage.status === 'in_progress' ? '▶' : stage.stageId }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ stage.title }}</p>
                  <span class="text-[10px] px-1.5 py-0.5 rounded-full shrink-0" :style="stageStyle(stage).badge">
                    {{ stageStyle(stage).badgeText }}
                  </span>
                </div>
                <p class="text-[11px] mt-0.5" style="color: var(--text-muted);">
                  {{ stage.topics.slice(0, 3).join(' · ') }}
                </p>
                <div class="h-1.5 rounded-full mt-2 overflow-hidden" style="background: rgba(99,102,241,0.08);">
                  <div class="h-full rounded-full transition-all duration-700"
                    :style="{ width: stage.progress + '%', background: stage.status === 'completed' ? 'var(--mint-500)' : 'var(--brand-500)' }" />
                </div>
              </div>
              <span class="text-xs font-bold tabular-nums shrink-0" :style="{ color: stage.status === 'completed' ? 'var(--mint-500)' : 'var(--text-secondary)' }">
                {{ stage.progress }}%
              </span>
            </div>
          </div>

          <router-link to="/learning-path" class="flex items-center justify-center gap-1 text-sm font-medium py-2.5 mt-2 rounded-xl transition-all"
            style="color: var(--brand-400);"
            @mouseenter="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.06)' }"
            @mouseleave="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }"
          >
            查看完整路径 <span class="text-base">→</span>
          </router-link>
        </div>

        <!-- AI 学习分析 -->
        <LearningAnalyzer />
      </div>

      <!-- 右栏: 专注灯塔 + 复习队列 + 好奇心引擎 -->
      <div class="space-y-5">
        <!-- 专注灯塔 -->
        <FocusLighthouse :today-minutes="learningStore.todayMinutes" />

        <!-- 复习队列 -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-semibold flex items-center gap-2" style="color: var(--text-primary);">
              <span><img :src="iconPlanList" class="section-icon" alt="" /></span> 待复习
            </h3>
            <span v-if="learningStore.urgentReviews.length" class="text-xs font-medium px-2 py-0.5 rounded-full"
              style="background: rgba(244,63,94,0.1); color: var(--rose-500);">
              {{ learningStore.urgentReviews.length }} 紧急
            </span>
          </div>

          <!-- 紧急复习 -->
          <div v-if="learningStore.urgentReviews.length" class="space-y-2 mb-3">
            <div v-for="item in learningStore.urgentReviews.slice(0, 3)" :key="item.id"
              class="flex items-center gap-3 p-3 rounded-xl"
              style="background: rgba(244,63,94,0.06); border: 1px solid rgba(244,63,94,0.12);">
              <span class="text-sm shrink-0">⚠️</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ item.topicName }}</p>
                <p class="text-xs" style="color: var(--rose-500);">保留率 {{ item.retentionRate }}% · 现在复习</p>
              </div>
              <button class="shrink-0 text-xs bg-rose-500 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-rose-600 transition-colors">
                复习
              </button>
            </div>
          </div>

          <!-- 常规复习 -->
          <div v-if="learningStore.reviewItems.filter(r => r.priority !== 'high').length" class="space-y-1.5">
            <div v-for="item in learningStore.reviewItems.filter(r => r.priority !== 'high').slice(0, 3)" :key="item.id"
              class="flex items-center gap-3 p-2.5 rounded-xl transition-colors"
              @mouseenter="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-card-hover)' }"
              @mouseleave="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }"
            >
              <span class="text-sm">📅</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm truncate" style="color: var(--text-primary);">{{ item.topicName }}</p>
                <p class="text-xs" style="color: var(--text-muted);">保留率 {{ item.retentionRate }}% · {{ item.dueReason }}</p>
              </div>
            </div>
          </div>

          <div v-if="!learningStore.reviewItems.length" class="py-6 text-center text-sm" style="color: var(--text-muted);">
            暂无复习任务 🎉
          </div>
        </div>

        <!-- 好奇心引擎 — 重构: 叙事化 -->
        <div class="glass-card rounded-2xl p-5">
          <h3 class="text-base font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary);">
            <span>🧠</span> 好奇心引擎
          </h3>

          <!-- 指标条 — 紧凑单行 -->
          <div class="flex items-center gap-4 mb-4">
            <div class="flex-1">
              <div class="flex justify-between text-xs mb-1.5">
                <span style="color: var(--text-muted);">好奇指数</span>
                <span class="font-bold tabular-nums" style="color: var(--brand-400);">{{ learningStore.curiosityIndex }}%</span>
              </div>
              <div class="h-2 rounded-full overflow-hidden" style="background: rgba(99,102,241,0.1);">
                <div class="h-full rounded-full transition-all duration-700 bg-gradient-to-r from-brand-400 via-brand-500 to-purple-500"
                  :style="{ width: learningStore.curiosityIndex + '%' }" />
              </div>
            </div>
            <!-- 活跃标签 -->
            <div class="flex items-center gap-1 shrink-0">
              <span class="text-[10px] px-2 py-1 rounded-full" style="background: rgba(99,102,241,0.08); color: var(--brand-400);">深入提问</span>
              <span class="text-[10px] px-2 py-1 rounded-full" style="background: rgba(6,182,212,0.08); color: var(--cyan-400);">探索行为</span>
            </div>
          </div>

          <!-- 叙事推荐 — 从指标到行动 -->
          <div class="rounded-xl p-4" style="background: rgba(99,102,241,0.04); border: 1px solid rgba(99,102,241,0.08);">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0"
                style="background: rgba(99,102,241,0.12);">
                <img :src="iconIllumination" class="curiosity-icon" alt="" />
              </div>
              <div>
                <p class="text-sm font-medium mb-1" style="color: var(--text-primary);">
                  {{ curiosityNudge.title }}
                </p>
                <p class="text-xs leading-relaxed" style="color: var(--text-secondary);">
                  {{ curiosityNudge.body }}
                </p>
                <button class="mt-2 text-xs font-medium px-3 py-1.5 rounded-lg transition-all"
                  style="background: rgba(99,102,241,0.12); color: var(--brand-400);"
                  @mouseenter="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.2)' }"
                  @mouseleave="(e: MouseEvent) => { (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.12)' }"
                >
                  {{ curiosityNudge.cta }} →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SVG 渐变定义 (被 ECharts 使用) -->
    <svg width="0" height="0" class="absolute">
      <defs>
        <linearGradient id="energyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#6366f1" />
          <stop offset="50%" stop-color="#a855f7" />
          <stop offset="100%" stop-color="#06b6d4" />
        </linearGradient>
      </defs>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { useLearningStore } from '@/stores/learning'
import type { LearningStage } from '@/stores/learning'
import FocusLighthouse from '@/components/learning/FocusLighthouse.vue'
import StageCompleteModal from '@/components/learning/StageCompleteModal.vue'
import LearningAnalyzer from '@/components/learning/LearningAnalyzer.vue'
import { formatMinutes } from '@/utils/format'
import client from '@/api/client'
import * as echarts from 'echarts'
import iconFan from '@/assets/icons/blue/fan-svgrepo-com.svg'
import iconAlarmClock from '@/assets/icons/blue/alarm-clock-svgrepo-com.svg'
import iconTrend from '@/assets/icons/jian/trend-analysis-svgrepo-com.svg'
import iconMap from '@/assets/icons/fang/map-svgrepo-com.svg'
import iconPlanList from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import iconIllumination from '@/assets/icons/fang/illumination-svgrepo-com.svg'
import iconCamera from '@/assets/icons/blue/camera-svgrepo-com.svg'
import iconTrophy from '@/assets/icons/blue/trophy-svgrepo-com.svg'

const userStore = useUserStore()
const learningStore = useLearningStore()
const weekChartEl = ref<HTMLElement | null>(null)

// ===== 阶段完成庆祝 =====
const showStageComplete = ref(false)
const celebrationData = ref({
  title: '阶段完成！',
  description: '你完成了一个学习阶段',
  icon: iconTrophy,
  rewards: [] as Array<{ icon: string; value: string; label: string }>,
})

function checkStageMilestone() {
  const path = learningStore.currentPath
  if (!path) return
  for (const stage of path.stages) {
    if (stage.progress >= 100 && stage.status === 'completed') {
      const key = `stage_celebrated_${stage.stageId}`
      if (sessionStorage.getItem(key)) continue
      sessionStorage.setItem(key, '1')
      celebrationData.value = {
        title: `${stage.title} 完成！`,
        description: `你成功完成了「${stage.title}」的所有学习内容`,
        icon: iconTrophy,
        rewards: [
          { icon: '⭐', value: '+50', label: '经验值' },
          { icon: '🪙', value: '+30', label: '金币' },
          { icon: '🔥', value: '达成', label: '里程碑' },
        ],
      }
      showStageComplete.value = true
      return
    }
  }
}


// ===== HUD 状态条数据 =====
const hudItems = computed(() => [
  {
    icon: iconFan, value: `${learningStore.streakDays}天`, label: '连续学习',
    trend: 12, trendArrow: '↑', trendColor: 'var(--mint-500)',
    tooltip: `比上周 +12% · 最长记录 ${Math.max(learningStore.streakDays, 7)} 天`,
  },
  {
    icon: iconAlarmClock, value: formatMinutes(learningStore.todayMinutes), label: '今日学习',
    trend: learningStore.todayMinutes > 30 ? 8 : -2, trendArrow: learningStore.todayMinutes > 30 ? '↑' : '↓',
    trendColor: learningStore.todayMinutes > 30 ? 'var(--mint-500)' : 'var(--rose-500)',
    tooltip: `${learningStore.todayMinutes < 30 ? '距离每日目标还差 ' + (30 - learningStore.todayMinutes) + ' 分钟' : '今日目标已达成！'} · 光束颜色=${learningStore.todayMinutes >= 90 ? '青' : learningStore.todayMinutes >= 60 ? '蓝' : learningStore.todayMinutes >= 30 ? '靛' : '紫'}`,
  },
  {
    icon: '🎯', value: `${Math.round(learningStore.overallProgress)}%`, label: '整体进度',
    trend: 5, trendArrow: '↑', trendColor: 'var(--mint-500)',
    tooltip: `完成 ${learningStore.currentPath?.stages.filter(s => s.status === 'completed').length || 0}/${learningStore.currentPath?.totalStages || 5} 个阶段`,
  },
  {
    icon: '🧠', value: `${learningStore.curiosityIndex}%`, label: '好奇指数',
    trend: learningStore.curiosityIndex >= 70 ? 3 : -3,
    trendArrow: learningStore.curiosityIndex >= 70 ? '↑' : '↓',
    trendColor: learningStore.curiosityIndex >= 70 ? 'var(--mint-500)' : 'var(--amber-500)',
    tooltip: '基于提问深度、探索广度、学习频率综合计算',
  },
  {
    icon: '🌊', value: flowEmoji(), label: '心流',
    trend: learningStore.flowState === 'flow' ? 10 : learningStore.flowState === 'engaged' ? 5 : -5,
    trendArrow: learningStore.flowState === 'flow' || learningStore.flowState === 'engaged' ? '↑' : '↓',
    trendColor: learningStore.flowState === 'flow' ? 'var(--mint-500)' : learningStore.flowState === 'engaged' ? 'var(--brand-400)' : 'var(--amber-500)',
    tooltip: flowTooltip(),
  },
  {
    icon: '⚡', value: `Lv.${userStore.profile.currentLevel}`, label: '等级',
    trend: undefined, trendArrow: '', trendColor: '',
    tooltip: `${userStore.profile.totalExp} EXP · 距下一级还需 ${userStore.expToNextLevel - (userStore.profile.totalExp % (userStore.profile.currentLevel * 300))} EXP`,
  },
])

function isImgIcon(icon: string): boolean {
  return icon.endsWith('.svg')
}

function flowEmoji(): string {
  const map: Record<string, string> = { flow: '专注', engaged: '投入', bored: '无聊', frustrated: '挫败' }
  return map[learningStore.flowState] || '投入'
}

function flowTooltip(): string {
  const map: Record<string, string> = {
    flow: '心流状态 — 学习效率最佳 ✨',
    engaged: '保持专注，稳步前进 📖',
    bored: '内容偏简单，建议提升难度 💤',
    frustrated: '内容偏难，建议回顾前置知识 😰',
  }
  return map[learningStore.flowState] || ''
}

// ===== 学习路径 — 仅显示当前 + 下一阶段 =====
const visibleStages = computed(() => {
  const path = learningStore.currentPath
  if (!path) return []
  const stages = path.stages
  const currentIdx = stages.findIndex(s => s.status === 'in_progress')
  if (currentIdx === -1) return stages.slice(0, 2)
  return stages.slice(currentIdx, currentIdx + 2)
})

function stageStyle(stage: LearningStage) {
  if (stage.status === 'completed') {
    return {
      dot: { background: 'rgba(16,185,129,0.15)', color: 'var(--mint-500)' },
      badge: { background: 'rgba(16,185,129,0.08)', color: 'var(--mint-500)' },
      badgeText: '已完成',
    }
  }
  if (stage.status === 'in_progress') {
    return {
      dot: { background: 'rgba(99,102,241,0.15)', color: 'var(--brand-400)' },
      badge: { background: 'rgba(99,102,241,0.08)', color: 'var(--brand-400)' },
      badgeText: '进行中',
    }
  }
  return {
    dot: { background: 'rgba(100,116,139,0.1)', color: 'var(--text-muted)' },
    badge: { background: 'rgba(100,116,139,0.06)', color: 'var(--text-muted)' },
    badgeText: '待解锁',
  }
}

// ===== 好奇心引擎 — 叙事推荐 =====
const curiosityNudge = computed(() => {
  const idx = learningStore.curiosityIndex
  const mastered = learningStore.masteredCount
  const total = learningStore.totalTopics

  if (idx >= 80 && mastered > 5) {
    return {
      title: '你的好奇心很旺盛！',
      body: `已掌握 ${mastered} 个知识点。深入探索「Spark RDD」背后的设计思想，了解它是如何实现容错和分布式计算的。`,
      cta: '探索 Spark RDD',
    }
  }
  if (idx >= 50) {
    return {
      title: '好奇心正在增长',
      body: `你最近的提问和探索显示出对实时计算方向的兴趣。试试了解 Kafka 如何与 Spark Streaming 配合，构建实时数据处理管道。`,
      cta: '学习 Kafka + Spark',
    }
  }
  const weakReview = learningStore.reviewItems.find(r => r.priority === 'high')
  if (weakReview) {
    return {
      title: '从薄弱环节重建好奇',
      body: `「${weakReview.topicName}」的保留率仅 ${weakReview.retentionRate}%。花 5 分钟巩固这个知识点，它会成为你后续学习的基石。`,
      cta: `复习 ${weakReview.topicName}`,
    }
  }
  return {
    title: '开启你的探索之旅',
    body: `从 ${total} 个知识点中选择一个感兴趣的方向，帕克会陪伴你完成第一次深入学习。`,
    cta: '开始探索',
  }
})

// ===== ECharts 周曲线 =====
function renderWeekChart() {
  if (!weekChartEl.value) return
  const chart = echarts.init(weekChartEl.value)
  const days = ['一', '二', '三', '四', '五', '六', '日']
  const minutes = [25, 45, 30, 60, 85, 55, 40]
  chart.setOption({
    grid: { top: 8, right: 12, bottom: 24, left: 40 },
    xAxis: {
      type: 'category', data: days,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#94a3b8' },
    },
    yAxis: {
      type: 'value', name: 'min',
      splitLine: { lineStyle: { color: 'rgba(99,102,241,0.08)' } },
      axisLabel: { fontSize: 10, color: '#94a3b8' },
    },
    series: [{
      type: 'bar', data: minutes, barWidth: 16,
      itemStyle: {
        borderRadius: [8, 8, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#818cf8' },
          { offset: 1, color: '#6366f1' },
        ]),
      },
      emphasis: { itemStyle: { color: '#4f46e5' } },
    }],
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}期: ${p[0].value} 分钟` },
  })
  window.addEventListener('resize', () => chart.resize())
}

onMounted(async () => {
  userStore.fetchProfile()
  await learningStore.fetchLearningPath()
  learningStore.fetchReviews()
  await nextTick()
  renderWeekChart()
  checkStageMilestone()
})
</script>

<style scoped>
.section-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  vertical-align: middle;
}

.hud-inline-icon {
  width: 14px;
  height: 14px;
  display: inline-block;
  vertical-align: middle;
  opacity: 0.9;
}

.hud-item-icon {
  width: 22px;
  height: 22px;
  display: block;
  margin: 0 auto 2px;
}

.curiosity-icon {
  width: 28px;
  height: 28px;
}
</style>
