<template>
  <div class="space-y-6 max-w-4xl animate-fade-in-up">
    <!-- Profile header -->
    <div class="glass-card rounded-2xl p-6">
      <div class="flex flex-col sm:flex-row items-center gap-6">
        <div class="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-lg shadow-brand-500/20 overflow-hidden cursor-pointer hover:shadow-xl hover:shadow-brand-500/30 transition-all group relative"
          title="点击更换头像" @click="showAvatarPicker = !showAvatarPicker">
          <img v-if="getAvatarSrc(userStore.profile.avatarUrl)" :src="getAvatarSrc(userStore.profile.avatarUrl)" class="w-full h-full object-contain p-2" alt="" />
          <span v-else class="text-3xl font-bold" style="color: var(--brand-500);">{{ userStore.profile.nickname.charAt(0) }}</span>
          <div class="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <span class="text-white text-xs font-medium">更换</span>
          </div>
        </div>
        <div class="flex-1 text-center sm:text-left">
          <h2 class="text-xl font-bold text-space-800">{{ userStore.profile.nickname }}</h2>
          <p class="text-sm text-gray-400">@{{ userStore.profile.username }} · {{ userStore.profile.email }}</p>
          <div class="flex items-center gap-4 mt-3 justify-center sm:justify-start">
            <span class="text-sm"><span class="font-bold text-space-800">Lv.{{ userStore.profile.currentLevel }}</span> <span class="text-gray-400">等级</span></span>
            <span class="text-sm"><span class="font-bold text-space-800"><img :src="iconMoney" class="inline-stat-icon" alt="" /> {{ userStore.profile.totalCoins }}</span> <span class="text-gray-400">金币</span></span>
            <span class="text-sm"><span class="font-bold text-space-800">⭐ {{ userStore.profile.totalExp }}</span> <span class="text-gray-400">经验</span></span>
          </div>
          <!-- Level progress -->
          <div class="mt-3 max-w-xs mx-auto sm:mx-0">
            <div class="flex justify-between text-xs text-gray-400 mb-1">
              <span>经验值</span>
              <span>{{ userStore.profile.totalExp }} / {{ userStore.expToNextLevel }}</span>
            </div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-energy-gradient rounded-full transition-all duration-700" :style="{ width: userStore.levelProgress + '%' }" />
            </div>
          </div>
        </div>
        <button class="px-4 py-2 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors">
          编辑资料
        </button>
      </div>
    </div>

    <!-- 头像选择面板 -->
    <Transition name="slide-down">
      <div v-if="showAvatarPicker" class="glass-card rounded-2xl p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold" style="color: var(--text-primary);">选择头像</h3>
          <button @click="showAvatarPicker = false" class="text-gray-400 hover:text-gray-600 text-lg leading-none">✕</button>
        </div>
        <div class="grid grid-cols-6 sm:grid-cols-9 md:grid-cols-13 gap-2">
          <button
            v-for="(avatar, idx) in avatarList" :key="idx"
            @click="selectAvatar(avatar)"
            class="w-12 h-12 rounded-xl flex items-center justify-center p-2 transition-all duration-200 border-2"
            :class="userStore.profile.avatarUrl === getAvatarFileName(avatar)
              ? 'border-brand-400 bg-brand-50 shadow-sm scale-110'
              : 'border-gray-100 bg-gray-50 hover:border-gray-300 hover:bg-gray-100 hover:scale-105'"
          >
            <img :src="avatar" class="w-full h-full object-contain" alt="" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- Tabs -->
    <div class="flex gap-2 border-b border-gray-200 pb-0 overflow-x-auto">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
        class="px-5 py-3 text-sm font-medium rounded-t-xl transition-all whitespace-nowrap"
        :class="activeTab === tab.key ? 'text-brand-400 border-b-2 border-brand-500 -mb-[2px]' : 'text-gray-400 hover:text-gray-600'"
        :style="activeTab === tab.key ? { background: 'var(--bg-card)' } : {}">
        <img :src="tab.icon" class="tab-icon" alt="" /> {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Star Chart -->
    <div v-if="activeTab === 'star'" class="space-y-4">
      <!-- 星图舞台 -->
      <div class="glass-card rounded-2xl overflow-hidden">
        <div class="flex items-center justify-between px-5 pt-4 pb-0">
          <div class="flex items-center gap-2">
            <span class="text-lg"><img :src="iconGalaxy" class="section-icon-lg" alt="" /></span>
            <div>
              <h3 class="text-base font-bold" style="color: var(--text-primary);">学习星图</h3>
            </div>
          </div>
          <!-- 视图切换 -->
          <div class="flex rounded-lg overflow-hidden"
            style="background: rgba(8,8,24,0.7); border: 1px solid rgba(99,102,241,0.15);">
            <button
              class="px-2.5 py-1.5 text-[10px] font-semibold transition-all"
              :style="starViewMode === '3d'
                ? { background: 'rgba(99,102,241,0.25)', color: '#a5b4fc' }
                : { color: 'rgba(255,255,255,0.4)' }"
              @click="starViewMode = '3d'"
            >3D 星座</button>
            <button
              class="px-2.5 py-1.5 text-[10px] font-semibold transition-all"
              :style="starViewMode === '2d'
                ? { background: 'rgba(99,102,241,0.25)', color: '#a5b4fc' }
                : { color: 'rgba(255,255,255,0.4)' }"
              @click="starViewMode = '2d'"
            >2D 星盘</button>
          </div>
        </div>

        <!-- 星图渲染 -->
        <ProfileStar3D
          v-if="starViewMode === '3d' && profileStore.dimensions.length"
          :dimensions="profileStore.dimensions"
          :hovered-star="hoveredStarKey"
          @hover-star="hoveredStarKey = $event"
          @focus-dimension="focusStarDimension"
        />
        <ProfileStar2D
          v-else-if="starViewMode === '2d' && profileStore.dimensions.length"
          :dimensions="profileStore.dimensions"
          :hovered-star="hoveredStarKey"
          @hover-star="hoveredStarKey = $event"
          @focus-dimension="focusStarDimension"
        />
        <div v-else class="flex items-center justify-center h-[340px]" style="background: radial-gradient(ellipse at 50% 60%, #12103a 0%, #08081a 50%, #040412 100%);">
          <div class="text-center" style="color: var(--text-muted);">
            <span class="text-3xl block mb-2"><img :src="iconGalaxy" class="section-icon-xl" alt="" /></span>
            <p class="text-sm">画像数据加载中...</p>
            <p class="text-xs mt-1">开始与帕克对话，智能体会自动构建你的学习星图</p>
          </div>
        </div>
      </div>

      <!-- AI 星舰日志 -->
      <div v-if="profileStore.aiSummary" class="glass-card rounded-2xl p-4"
        style="background: rgba(99,102,241,0.03); border: 1px solid rgba(99,102,241,0.08);">
        <div class="flex items-start gap-3">
          <span class="text-base shrink-0"><img :src="iconRadioStation" class="section-icon-md" alt="" /></span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <p class="text-xs font-semibold" style="color: var(--brand-400);">星舰日志</p>
              <button
                class="text-[10px] px-2 py-0.5 rounded-full transition-all"
                style="background: rgba(99,102,241,0.1); color: var(--brand-400); border: 1px solid rgba(99,102,241,0.15);"
                :disabled="profileStore.isFeedbackLoading"
                @click="refreshAgentFeedback"
                title="让智能体重新分析你的画像"
              >
                <span v-if="profileStore.isFeedbackLoading" class="inline-block w-3 h-3 border border-r-transparent rounded-full feedback-spinner mr-0.5" style="border-color: var(--brand-400); border-right-color: transparent;"></span>
                {{ profileStore.isFeedbackLoading ? '分析中...' : '↻ 刷新' }}
              </button>
            </div>
            <p class="text-xs leading-relaxed" style="color: var(--text-secondary);">{{ profileStore.aiSummary }}</p>
          </div>
        </div>
      </div>

      <!-- 维度详情卡片 -->
      <div class="glass-card rounded-2xl p-5">
        <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">维度恒星</h3>
        <div class="space-y-2">
          <div
            v-for="d in profileStore.dimensions" :key="d.key"
            :data-dim="d.key"
            ref="dimBars"
            class="flex items-center gap-3 p-2.5 rounded-xl transition-all duration-400"
            :class="{ 'flash-bar': flashStarKey === d.key }"
            :style="{
              background: hoveredStarKey === d.key ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.02)',
              border: hoveredStarKey === d.key ? `1px solid ${d.color}33` : '1px solid transparent',
            }"
            @mouseenter="hoveredStarKey = d.key"
            @mouseleave="hoveredStarKey = null"
          >
            <div class="w-3 h-3 rounded-full shrink-0 transition-all duration-400" :style="{
              background: `radial-gradient(circle, ${d.color}, ${d.color}44)`,
              boxShadow: hoveredStarKey === d.key ? `0 0 ${8 + d.value / 15}px ${d.color}` : `0 0 ${4 + d.value / 25}px ${d.color}`,
            }"></div>
            <span class="text-sm flex-1" style="color: var(--text-primary);">{{ d.label }}</span>
            <div class="flex-1 h-1.5 rounded-full overflow-hidden mx-2" style="background: rgba(99,102,241,0.06);">
              <div class="h-full rounded-full transition-all duration-700" :style="{ width: d.value + '%', backgroundColor: d.color }" />
            </div>
            <span class="text-sm font-bold tabular-nums w-8 text-right" :style="{ color: d.color }">{{ d.value }}</span>
            <span class="text-xs font-bold tabular-nums w-8 text-right"
              :style="{ color: d.value - d.previousValue > 2 ? '#10b981' : d.value - d.previousValue < -2 ? '#f43f5e' : 'var(--text-muted)' }">
              {{ d.value - d.previousValue > 2 ? '↑' : d.value - d.previousValue < -2 ? '↓' : '→' }}{{ Math.abs(d.value - d.previousValue) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Achievements -->
    <div v-if="activeTab === 'achievements'" class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-bold text-space-800"><img :src="iconTrophy" class="section-icon" alt="" /> 成就徽章</h3>
        <span class="text-sm text-gray-400">
          {{ unlockedCount }}/{{ userStore.achievements.length }} 已解锁
        </span>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <BadgeCard v-for="a in userStore.achievements" :key="a.id" :achievement="a" />
      </div>
    </div>

    <!-- Tab: Review Plan (Forgetting Curve) -->
    <div v-if="activeTab === 'review'" class="space-y-6">
      <div class="glass-card rounded-2xl p-5">
        <h3 class="text-base font-semibold text-space-800 mb-4">
          <img :src="iconTrend" class="section-icon" alt="" /> 遗忘曲线与复习计划
          <span class="text-xs font-normal ml-2" style="color: var(--text-muted);">
            · 点击散点或复习项可联动定位
          </span>
        </h3>
        <div ref="curveChart" class="w-full h-72"></div>
      </div>

      <div class="glass-card rounded-2xl p-5">
        <h3 class="text-base font-semibold text-space-800 mb-4">
          📚 复习队列
          <span class="text-xs font-normal ml-2" style="color: var(--text-muted);">
            {{ learningStore.reviewItems.length }} 个待复习
          </span>
        </h3>
        <div v-if="!learningStore.reviewItems.length" class="text-center py-8">
          <p class="text-sm" style="color: var(--text-muted);">暂无待复习知识点，继续保持！</p>
        </div>
        <div v-if="learningStore.urgentReviews.length" class="space-y-2 mb-4">
          <h4 class="text-sm font-semibold text-rose-600">⚠️ 紧急 (保留率 &lt; 30%)</h4>
          <div v-for="item in learningStore.urgentReviews" :key="item.id"
            :data-review-id="item.id"
            class="review-list-item flex items-center gap-3 p-3 bg-rose-50 rounded-xl border cursor-pointer transition-all duration-300"
            :class="{ 'ring-2 ring-rose-400 scale-[1.02]': highlightedReviewId === item.id }"
            @click="focusReviewItem(item.id)">
            <span class="text-sm font-bold text-rose-600">⚠️</span>
            <div class="flex-1">
              <p class="text-sm font-medium text-space-800">{{ item.topicName }}</p>
              <p class="text-xs text-rose-500">保留率 {{ item.retentionRate }}% → 现在复习</p>
            </div>
            <button class="text-xs bg-rose-500 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-rose-600 transition-colors">复习</button>
          </div>
        </div>
        <div class="space-y-2">
          <h4 class="text-sm font-semibold text-gray-600">📅 计划复习</h4>
          <div v-for="item in learningStore.reviewItems.filter(r => r.priority !== 'high')" :key="item.id"
            :data-review-id="item.id"
            class="review-list-item flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-all duration-300 cursor-pointer"
            :class="{ 'bg-brand-50 ring-2 ring-brand-200 scale-[1.01]': highlightedReviewId === item.id }"
            @click="focusReviewItem(item.id)">
            <span class="text-sm">📅</span>
            <div class="flex-1">
              <p class="text-sm text-gray-700">{{ item.topicName }}</p>
              <p class="text-xs text-gray-400">保留率 {{ item.retentionRate }}% - {{ item.dueReason }}</p>
            </div>
            <button class="text-xs border border-gray-200 text-gray-600 px-3 py-1.5 rounded-lg font-medium hover:bg-gray-50 transition-colors">开始</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Learning Materials -->
    <div v-if="activeTab === 'materials'">
      <LearningContent />
    </div>

    <!-- Tab: Settings -->
    <div v-if="activeTab === 'settings'" class="space-y-4">
      <div class="glass-card rounded-2xl p-6">
        <h3 class="text-base font-semibold text-space-800 mb-4">⚙️ 个人设置</h3>
        <div class="space-y-4 max-w-md">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">昵称</label>
            <input type="text" :value="userStore.profile.nickname" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <input type="email" :value="userStore.profile.email" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">每日学习目标 (分钟)</label>
            <select class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400">
              <option>30</option><option selected>60</option><option>90</option><option>120</option>
            </select>
          </div>
          <button class="w-full py-3 bg-brand-500 text-white rounded-xl font-medium hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 mt-2 active:scale-[0.98]">
            保存设置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { useLearningStore } from '@/stores/learning'
import { useProfileModelingStore } from '@/stores/profileModeling'
import ProfileStar3D from '@/components/profile/ProfileStar3D.vue'
import ProfileStar2D from '@/components/profile/ProfileStar2D.vue'
import BadgeCard from '@/components/achievement/BadgeCard.vue'
import LearningContent from '@/components/learning/LearningContent.vue'
import * as echarts from 'echarts'
import iconGalaxy from '@/assets/icons/star/galaxy-svgrepo-com.svg'
import iconTrophy from '@/assets/icons/blue/trophy-svgrepo-com.svg'
import iconPlanList from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import iconSetUp from '@/assets/icons/fang/set-up-svgrepo-com.svg'
import iconMoney from '@/assets/icons/blue/money-svgrepo-com.svg'
import iconRadioStation from '@/assets/icons/fang/radio-station-svgrepo-com.svg'
import iconTrend from '@/assets/icons/jian/trend-analysis-svgrepo-com.svg'
import iconInsertWord from '@/assets/icons/jian/insert-word-svgrepo-com.svg'
import { avatarList, getAvatarSrc, getAvatarFileName } from '@/utils/avatars'

const userStore = useUserStore()
const learningStore = useLearningStore()
const profileStore = useProfileModelingStore()
const activeTab = ref('star')
const showAvatarPicker = ref(false)
const curveChart = ref<HTMLElement | null>(null)
const dimBars = ref<HTMLElement[]>([])
let chartInstance: echarts.ECharts | null = null
const highlightedReviewId = ref<string | null>(null)

function selectAvatar(avatarSrc: string) {
  const fileName = getAvatarFileName(avatarSrc)
  userStore.updateAvatar(fileName)
}

const tabs = [
  { key: 'star', label: '学习星图', icon: iconGalaxy },
  { key: 'achievements', label: '成就', icon: iconTrophy },
  { key: 'review', label: '复习', icon: iconPlanList },
  { key: 'materials', label: '学习内容', icon: iconInsertWord },
  { key: 'settings', label: '设置', icon: iconSetUp },
]

const unlockedCount = computed(() => userStore.achievements.filter(a => a.isUnlocked).length)

// ── 星图相关状态 ──
const starViewMode = ref<'3d' | '2d'>('3d')
const hoveredStarKey = ref<string | null>(null)
const flashStarKey = ref<string | null>(null)

async function focusStarDimension(key: string) {
  await nextTick()
  const el = (document.querySelector(`[data-dim="${key}"]`) as HTMLElement | null)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    flashStarKey.value = key
    setTimeout(() => { flashStarKey.value = null }, 1500)
  }
}

const lastUpdatedText = computed(() => {
  if (!profileStore.lastUpdated) return ''
  const diff = Date.now() - new Date(profileStore.lastUpdated).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  return `${Math.floor(hours / 24)} 天前`
})

async function refreshAgentFeedback() {
  await profileStore.fetchAgentFeedback()
}

onMounted(async () => {
  userStore.fetchProfile()
  userStore.fetchAchievements()
  await profileStore.fetchProfileModel()
  await learningStore.fetchReviews()
  await nextTick()
  if (activeTab.value === 'review') renderForgettingCurve()
})

watch(activeTab, async (tab) => {
  if (tab === 'review') {
    await nextTick()
    renderForgettingCurve()
  }
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

function renderForgettingCurve() {
  if (!curveChart.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(curveChart.value)

  // ── 艾宾浩斯理论曲线数据 (时间 → 保留率) ──
  const ebbTimes = [0, 0.01, 0.04, 0.33, 1, 2, 7, 14, 30]  // 天
  const ebbLabels = ['0', '15分钟', '1小时', '8小时', '1天', '2天', '7天', '14天', '30天']
  const ebbCurve = [100, 95, 85, 70, 58, 44, 25, 15, 8]
  const idealCurve = [100, 95, 90, 88, 85, 82, 78, 72, 65]

  // ── 用户实际数据 (散点) ──
  const now = Date.now()
  const actualScatter = learningStore.reviewItems.map(item => {
    const daysSince = item.lastReviewedAt
      ? Math.max(0, Math.round((now - new Date(item.lastReviewedAt).getTime()) / 86400000 * 10) / 10)
      : 7
    const colorMap = { high: '#f43f5e', medium: '#f59e0b', low: '#10b981' }
    return {
      name: item.topicName,
      value: [daysSince, item.retentionRate],
      itemStyle: {
        color: colorMap[item.priority] || '#6366f1',
        shadowBlur: 6,
        shadowColor: 'rgba(0,0,0,0.15)',
      },
      symbolSize: item.priority === 'high' ? 16 : item.priority === 'medium' ? 12 : 9,
      itemId: item.id,
      priority: item.priority,
      dueReason: item.dueReason,
    }
  })

  const xMax = Math.max(30, ...actualScatter.map(d => d.value[0] as number)) + 3

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15,23,42,0.94)',
      borderColor: 'rgba(99,102,241,0.2)',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (p: any) => {
        if (p.seriesName === '你的知识点') {
          const priLabel = p.data.priority === 'high' ? '紧急' : p.data.priority === 'medium' ? '中等' : '正常'
          return `<b>${p.name}</b><br/>
            距上次复习: <b>${p.value[0]}</b> 天<br/>
            保留率: <b>${p.value[1]}%</b><br/>
            优先级: <span style="color:${p.color}">● ${priLabel}</span><br/>
            <span style="font-size:11px;color:#94a3b8">${p.data.dueReason || ''}</span>`
        }
        if (p.seriesName === '危险线 (30%)') return null
        const idx = (p.dataIndex ?? p.data?.dataIndex) ?? -1
        if (idx >= 0 && idx < ebbLabels.length) {
          return `${p.seriesName}<br/>时间: ${ebbLabels[idx]}<br/>保留率: ${p.value}%`
        }
        return `${p.seriesName}<br/>保留率: ${p.value}%`
      },
    },
    xAxis: {
      type: 'value',
      name: '距上次复习 (天)',
      nameLocation: 'middle',
      nameGap: 28,
      min: 0,
      max: xMax,
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
    },
    yAxis: {
      type: 'value',
      name: '保留率 (%)',
      max: 100,
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
    },
    series: [
      {
        name: '艾宾浩斯遗忘曲线 (参考)',
        type: 'line',
        data: ebbTimes.map((t, i) => [t, ebbCurve[i]]),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#94a3b8', width: 1.5, type: 'dashed' },
        z: 1,
      },
      {
        name: '按时复习曲线 (参考)',
        type: 'line',
        data: ebbTimes.map((t, i) => [t, idealCurve[i]]),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 1.5, type: 'dotted' },
        areaStyle: { color: 'rgba(16, 185, 129, 0.06)' },
        z: 1,
      },
      {
        name: '危险线 (30%)',
        type: 'line',
        markLine: {
          silent: true,
          symbol: 'none',
          data: [{ yAxis: 30, label: { formatter: '危险线 30%', color: '#f59e0b', fontSize: 10 }, lineStyle: { color: '#f59e0b', type: 'dashed', width: 1 } }],
        },
        data: [],
        z: 2,
      },
      {
        name: '你的知识点',
        type: 'scatter',
        data: actualScatter,
        z: 10,
        emphasis: {
          scale: 1.5,
          itemStyle: { shadowBlur: 14, shadowColor: 'rgba(0,0,0,0.35)' },
        },
      },
    ],
    legend: {
      bottom: 0,
      textStyle: { color: '#64748b', fontSize: 10 },
      itemWidth: 12,
      itemHeight: 12,
    },
    grid: { top: 15, right: 25, bottom: 42, left: 55 },
  })

  // ── 图表 click → 列表联动 ──
  chartInstance.off('click')
  chartInstance.on('click', (params: any) => {
    if (params.seriesName === '你的知识点' && params.data?.itemId) {
      const itemId = params.data.itemId as string
      highlightedReviewId.value = itemId
      scrollToReviewItem(itemId)
      setTimeout(() => { highlightedReviewId.value = null }, 3000)
    }
  })

  // resize
  window.addEventListener('resize', () => chartInstance?.resize())
}

function scrollToReviewItem(itemId: string) {
  const el = document.querySelector(`[data-review-id="${itemId}"]`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function focusReviewItem(itemId: string) {
  highlightedReviewId.value = itemId
  scrollToReviewItem(itemId)
  // 高亮图表中对应散点
  if (chartInstance) {
    chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 3, dataIndex: -1 })
    const scatterData = (chartInstance.getOption() as any).series[3]?.data || []
    const idx = scatterData.findIndex((d: any) => d?.itemId === itemId)
    if (idx >= 0) {
      chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 3, dataIndex: idx })
      chartInstance.dispatchAction({ type: 'showTip', seriesIndex: 3, dataIndex: idx })
    }
  }
  setTimeout(() => {
    highlightedReviewId.value = null
    if (chartInstance) chartInstance.dispatchAction({ type: 'downplay', seriesIndex: 3 })
  }, 3000)
}
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-12px);
  max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
  max-height: 500px;
}

.tab-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  vertical-align: middle;
}

.section-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  vertical-align: middle;
}

.section-icon-sm {
  width: 15px;
  height: 15px;
  display: inline-block;
  vertical-align: middle;
}

.section-icon-md {
  width: 20px;
  height: 20px;
  display: inline-block;
  vertical-align: middle;
}

.section-icon-lg {
  width: 22px;
  height: 22px;
  display: inline-block;
  vertical-align: middle;
}

.section-icon-xl {
  width: 36px;
  height: 36px;
  display: inline-block;
  vertical-align: middle;
}

.inline-stat-icon {
  width: 16px;
  height: 16px;
  display: inline-block;
  vertical-align: middle;
  opacity: 0.85;
}

.feedback-spinner {
  animation: feedback-spin 0.6s linear infinite;
}

@keyframes feedback-spin {
  to { transform: rotate(360deg); }
}
</style>
