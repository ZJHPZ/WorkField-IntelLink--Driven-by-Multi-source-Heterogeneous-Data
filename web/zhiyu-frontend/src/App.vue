<template>
  <!-- 宇宙星空背景 (深色主题 + 个人侧可见, 全屏/企业侧隐藏) -->
  <CosmicBackground v-if="!appStore.isEnterprise && themeStore.mode === 'dark' && !isFullscreen" />
  <div class="flex h-screen overflow-hidden relative z-10" :class="appStore.isEnterprise ? 'ent-shell' : ''" :style="{ backgroundColor: 'var(--bg-primary)' }">
    <!-- Sidebar — 深空舰桥导航面板 -->
    <aside
      v-if="!isFullscreen"
      class="fixed inset-y-0 left-0 z-50 w-64 flex flex-col lg:relative overflow-hidden sidebar-depth"
      :style="{ backgroundColor: 'var(--sidebar-bg)' }"
    >
      <!-- 网格 + 电路纹双层覆盖 -->
      <div class="absolute inset-0 pointer-events-none z-0" style="opacity:0.04;background-image:linear-gradient(rgba(128,128,128,0.5) 1px,transparent 1px),linear-gradient(90deg,rgba(128,128,128,0.5) 1px,transparent 1px);background-size:16px 16px"></div>
      <div class="absolute inset-0 pointer-events-none z-0 opacity-[0.03]">
        <div class="absolute bottom-20 left-4 w-12 h-px" style="background:var(--brand-500)"></div>
        <div class="absolute bottom-20 left-4 w-px h-12" style="background:var(--brand-500)"></div>
        <div class="absolute top-24 right-6 w-8 h-px" style="background:var(--brand-500)"></div>
        <div class="absolute top-24 right-6 w-px h-8" style="background:var(--brand-500)"></div>
      </div>
      <!-- 扫描线 -->
      <div class="absolute left-0 right-0 h-px pointer-events-none z-0" style="background:linear-gradient(90deg,transparent,var(--brand-400),transparent);animation:scanLine 6s linear infinite"></div>

      <div class="relative z-[1] flex flex-col h-full">
      <!-- Logo — 六角形 + 铭牌 -->
      <div class="px-5 py-4" style="border-bottom:1px solid var(--sidebar-border)">
        <div class="flex items-center gap-3">
          <div class="relative shrink-0" style="width:38px;height:38px">
            <svg viewBox="0 0 56 56" class="w-full h-full" style="filter:drop-shadow(0 0 8px rgba(232,83,108,0.3))">
              <polygon points="28,2 52,16 52,40 28,54 4,40 4,16" fill="url(#sideHexGrad)" stroke="var(--brand-400)" stroke-width="1.5"/>
              <defs><linearGradient id="sideHexGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="var(--brand-600)"/><stop offset="100%" stop-color="var(--brand-400)"/></linearGradient></defs>
            </svg>
            <span class="absolute inset-0 flex items-center justify-center text-white font-bold text-sm">职</span>
          </div>
          <div>
            <div class="flex items-center gap-1.5">
              <h1 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">职域智联</h1>
              <span class="tag-plate" style="font-size:7px;padding:1px 4px">{{ appStore.isEnterprise?'ENT':'PER' }}</span>
            </div>
            <p class="text-xs font-mono tracking-wider mt-0.5" :style="{color:'var(--text-muted)'}">
              {{ appStore.isEnterprise ? 'ENTERPRISE COMMAND' : 'CAREER COMMAND' }}
            </p>
          </div>
        </div>
      </div>

      <!-- 分类标签 -->
      <div class="px-5 pt-3 pb-1">
        <span class="text-xs font-mono tracking-[0.15em] uppercase" style="color:var(--text-muted)">— Navigation —</span>
      </div>

      <!-- Nav links — 带属性徽章 -->
      <nav class="flex-1 px-3 py-1 space-y-2 overflow-y-auto">
        <router-link
          v-for="item in enrichedNavItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-3 nav-chip"
          :class="isActive(item.path) ? 'nav-chip-active' : ''"
          :style="{ color: isActive(item.path) ? 'var(--text-primary)' : 'var(--text-secondary)' }"
        >
          <!-- 图标 -->
          <img v-if="item.iconType==='svg'" :src="item.icon" class="w-5 h-5 shrink-0 transition-all" :style="{opacity:isActive(item.path)?'1':'0.55',filter:isActive(item.path)?'drop-shadow(0 0 4px var(--brand-400))':'none'}" alt="" />
          <span v-else class="text-base shrink-0">{{ item.icon }}</span>

          <!-- 标签 -->
          <span class="text-sm font-bold tracking-wide">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 结构梁 -->
      <div class="beam-divider"></div>

      <!-- 底部 — 用户状态卡，点击进入个人中心 -->
      <router-link to="/personal/center" class="px-4 py-3 block transition-all hover:bg-brand-50/5 group" style="border-top:1px solid var(--sidebar-border)">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-full bg-brand-gradient flex items-center justify-center text-white font-bold text-xs shrink-0 group-hover:scale-105 transition-transform">张</div>
          <div class="flex-1 min-w-0">
            <div class="text-xs font-bold tracking-wide truncate" :style="{color:'var(--text-primary)'}">张明</div>
            <div class="h-1 mt-1.5 rounded-sm" style="background:var(--bg-secondary)"><div class="h-full rounded-sm" style="width:65%;background:var(--brand-500)"></div></div>
          </div>
          <span class="text-xs shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" :style="{color:'var(--text-muted)'}">→</span>
        </div>
      </router-link>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- Top header -->
      <header
        v-if="!isFullscreen"
        class="px-4 py-3 flex items-center gap-4 shrink-0"
        :style="{ backgroundColor: 'var(--header-bg)', borderBottom: '1px solid var(--header-border)' }"
      >
        <div class="flex-1">
          <h2 class="text-lg font-semibold" :style="{ color: 'var(--text-primary)' }">{{ currentTitle }}</h2>
        </div>

        <div class="flex items-center gap-3">
          <!-- Role switcher -->
          <div class="flex items-center bg-gray-100 rounded-lg p-0.5">
            <button
              :class="['px-2.5 py-1.5 rounded-md text-xs font-medium transition-all', appStore.isEnterprise ? 'bg-white text-space-700 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              @click="switchToEnterprise"
            >🏢 企业</button>
            <button
              :class="['px-2.5 py-1.5 rounded-md text-xs font-medium transition-all', appStore.isPersonal ? 'bg-white text-brand-700 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              @click="switchToPersonal"
            >👤 个人</button>
          </div>

          <!-- Theme toggle -->
          <button
            class="relative p-2 rounded-lg transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
            :style="{ color: 'var(--text-secondary)' }"
            @click="themeStore.toggle()"
            :title="themeStore.mode === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
          >
            <svg v-if="themeStore.mode === 'dark'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
          </button>
        </div>
      </header>

      <!-- Page content — 主板基板纹理 -->
      <div :class="isFullscreen ? 'flex-1' : 'flex-1 overflow-y-auto p-3 md:p-4'" class="main-board">
        <router-view v-slot="{ Component }">
          <transition name="slide-up" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
  <NotificationBar
    :visible="notifyState.visible"
    :message="notifyState.message"
    :detail="notifyState.detail"
    :type="notifyState.type"
    @close="notifyClose"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { useAppStore } from '@/stores/app'
import CosmicBackground from '@/components/common/CosmicBackground.vue'
import NotificationBar from '@/components/common/NotificationBar.vue'
import { useNotify } from '@/composables/useNotify'
import { usePersonalStore } from '@/stores/personal'
import dashboardIcon from '@/assets/icons/dashboard.svg'
import profileIcon from '@/assets/icons/profile.svg'
import matchIcon from '@/assets/icons/match.svg'
import learningIcon from '@/assets/icons/learning.svg'
import freshnessIcon from '@/assets/icons/freshness.svg'
import switchIcon from '@/assets/icons/switch.svg'
import growthIcon from '@/assets/icons/growth.svg'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()
const appStore = useAppStore()
const personalStore = usePersonalStore()
const { state: notifyState, close: notifyClose } = useNotify()

// 企业侧 / 个人侧 → html 上的 data-side 属性，enterprise.css 据此接管外壳
watchEffect(() => {
  document.documentElement.dataset.side = appStore.isEnterprise ? 'enterprise' : 'personal'
})

const isFullscreen = computed(() => route.meta.fullscreen === true)
const currentTitle = computed(() => route.meta.title || '职域智联')

// ── Navigation items ──
const enterpriseNavItems = [
  { path: '/enterprise', label: '企业工作台', icon: '🏠' },
  { path: '/enterprise/positions', label: '岗位标准', icon: '📋' },
  { path: '/enterprise/discovery', label: '新岗位发现', icon: '🔍' },
  { path: '/enterprise/diagnose', label: 'JD 诊断', icon: '🩺' },
  { path: '/enterprise/team', label: '团队盘点', icon: '👥' },
  { path: '/enterprise/forecast', label: '需求预测', icon: '📊' },
  { path: '/enterprise/graph', label: '全图谱', icon: '🗺️' },
]

const personalNavItems = [
  { path: '/personal', label: '个人主页', icon: dashboardIcon, iconType: 'svg' },
  { path: '/personal/explore', label: '岗位探索', icon: new URL('@/assets/icons/chat.svg', import.meta.url).href, iconType: 'svg' },
  { path: '/personal/profile', label: '技能画像', icon: profileIcon, iconType: 'svg' },
  { path: '/personal/match', label: '人岗匹配', icon: matchIcon, iconType: 'svg' },
  { path: '/personal/match/compare', label: '岗位对比', icon: matchIcon, iconType: 'svg' },
  { path: '/personal/resume', label: '简历解析', icon: profileIcon, iconType: 'svg' },
  { path: '/personal/learning-path', label: '学习路径', icon: learningIcon, iconType: 'svg' },
  { path: '/personal/freshness', label: '技能保鲜', icon: freshnessIcon, iconType: 'svg' },
  { path: '/personal/switch', label: '转行分析', icon: switchIcon, iconType: 'svg' },
  { path: '/personal/growth', label: '成长轨迹', icon: growthIcon, iconType: 'svg' },
  { path: '/personal/spectrum', label: '信号光谱', icon: new URL('@/assets/icons/chat.svg', import.meta.url).href, iconType: 'svg' },
  { path: '/personal/evolution', label: '演化剧场', icon: new URL('@/assets/icons/chat.svg', import.meta.url).href, iconType: 'svg' },
  { path: '/personal/chat', label: 'AI 顾问', icon: new URL('@/assets/icons/chat.svg', import.meta.url).href, iconType: 'svg' },
]

const currentNavItems = computed(() =>
  appStore.isEnterprise ? enterpriseNavItems : personalNavItems
)

// 丰富导航项 — 注入实时数据元数据
interface EnrichedNavItem {
  path: string; label: string; icon: any; iconType?: string
  subtitle?: string; statusDot?: string; badge?: string | number; badgeColor?: string
  progress?: number; progressColor?: string
}
const enrichedNavItems = computed<EnrichedNavItem[]>(() => {
  const base = currentNavItems.value
  if (appStore.isEnterprise) return base // 企业侧保持简洁

  const alertCount = personalStore.alertSkillCount
  const bestMatch = personalStore.bestMatch
  const completedSteps = personalStore.learningPath.filter(s => s.status === 'completed').length
  const totalSteps = personalStore.learningPath.length

  return base.map(item => {
    const enriched: EnrichedNavItem = { ...item }
    const p = item.path

    if (p === '/personal') {
      enriched.badge = bestMatch?.matchRate ? `${bestMatch.matchRate}%` : '—'
      enriched.badgeColor = 'var(--brand-500)'
      enriched.statusDot = alertCount > 0 ? '#f59e0b' : '#10b981'
    } else if (p === '/personal/profile') {
      enriched.badge = personalStore.skillCount
      enriched.badgeColor = 'var(--brand-500)'
      enriched.progress = Math.round((personalStore.healthySkillCount / Math.max(personalStore.skillCount, 1)) * 100)
      enriched.progressColor = 'var(--mint-500)'
    } else if (p === '/personal/match') {
      enriched.badge = bestMatch?.matchRate ? `${bestMatch.matchRate}%` : '—'
      enriched.badgeColor = bestMatch?.matchRate && bestMatch.matchRate >= 80 ? 'var(--mint-500)' : 'var(--brand-500)'
    } else if (p === '/personal/learning-path') {
      enriched.progress = totalSteps ? Math.round((completedSteps / totalSteps) * 100) : 0
      enriched.progressColor = completedSteps === totalSteps ? 'var(--mint-500)' : 'var(--brand-500)'
      enriched.badge = `${completedSteps}/${totalSteps}`
    } else if (p === '/personal/freshness') {
      enriched.statusDot = alertCount > 0 ? '#f43f5e' : '#10b981'
      enriched.badge = alertCount > 0 ? alertCount : '✓'
      enriched.badgeColor = alertCount > 0 ? '#f43f5e' : 'var(--mint-500)'
    } else if (p === '/personal/switch') {
      const opt = personalStore.switchOptions[0]
      enriched.badge = opt?.transferabilityScore ? `${opt.transferabilityScore}%` : '—'
      enriched.badgeColor = opt?.transferabilityScore && opt.transferabilityScore >= 70 ? 'var(--mint-500)' : opt?.transferabilityScore && opt.transferabilityScore >= 40 ? '#f59e0b' : '#f43f5e'
    } else if (p === '/personal/growth') {
      enriched.progress = 65
      enriched.progressColor = 'var(--brand-500)'
      enriched.badge = 'Lv.24'
    }
    return enriched
  })
})

function isActive(path: string): boolean {
  // 精确匹配，避免 /personal/match/compare 激活 /personal/match
  return route.path === path
}

function switchToEnterprise() {
  appStore.switchRole('enterprise')
  themeStore.setPalette('indigo')
  router.push('/enterprise')
}

function switchToPersonal() {
  appStore.switchRole('personal')
  themeStore.setPalette('warm')
  router.push('/personal')
}

onMounted(() => {
  // 根据当前角色设置初始 palette
  if (appStore.isPersonal) themeStore.setPalette('warm')
  else themeStore.setPalette('indigo')
  themeStore.applyTheme()
})
</script>
