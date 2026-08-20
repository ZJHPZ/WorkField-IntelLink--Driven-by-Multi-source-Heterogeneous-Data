<template>
  <!-- 宇宙星空背景 (深色主题下可见, 全屏模式下隐藏) -->
  <CosmicBackground v-if="themeStore.mode === 'dark' && !isFullscreen" />
  <!-- 桌面宠物：全局悬浮 (全屏模式下隐藏) -->
  <DesktopPet v-if="!isFullscreen" />
  <!-- 分析报告悬浮窗 (全屏模式下隐藏) -->
  <AnalysisFloatingWindow v-if="!isFullscreen" />
  <!-- 苏格拉底引导反思悬浮窗 -->
  <SocraticPanel />
  <!-- 管理员宠物管理面板 -->
  <PetSwitcher v-if="currentUserId === 'admin_user'" />
  <!-- 管理员调试面板 -->
  <DebugPanel v-if="currentUserId === 'admin_user'" />
  <!-- 学习画像面板 -->
  <ProfilePanel
    :visible="showProfilePanel"
    :dimensions="profileModelingStore.dimensions"
    :ai-summary="profileModelingStore.aiSummary"
    :last-updated="profileModelingStore.lastUpdated"
    :feedback-loading="profileModelingStore.isFeedbackLoading"
    @close="showProfilePanel = false"
    @refresh-feedback="profileModelingStore.fetchAgentFeedback()"
  />

  <div class="flex h-screen overflow-hidden relative z-10" style="background-color: var(--bg-primary);">
    <!-- Mobile menu overlay -->
    <div v-if="sidebarOpen && !isFullscreen" class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      @click="sidebarOpen = false" />

    <!-- Sidebar -->
    <aside
      v-if="!isFullscreen"
      :class="[
        'fixed inset-y-0 left-0 z-50 w-64 flex flex-col transition-transform duration-300 lg:relative lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
      style="background-color: var(--sidebar-bg); border-right: 1px solid var(--sidebar-border);"
    >
      <!-- Logo -->
      <div class="flex items-center gap-3 px-6 py-5" style="border-bottom: 1px solid var(--sidebar-border);">
        <div class="w-9 h-9 bg-brand-gradient rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-brand-500/25">
          数
        </div>
        <div>
          <h1 class="text-lg font-bold" style="color: var(--text-primary);">数知</h1>
          <p class="text-xs" style="color: var(--text-secondary);">大数据智能学习平台</p>
        </div>
      </div>

      <!-- Nav links -->
      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all duration-200"
          :class="isActive(item.path) ? 'bg-brand-50 text-brand-700 shadow-sm' : ''"
          :style="isActive(item.path) ? {} : { color: 'var(--text-secondary)' }"
          @mouseenter="(e: MouseEvent) => { if (!isActive(item.path)) (e.target as HTMLElement).style.backgroundColor = 'var(--bg-card)' }"
          @mouseleave="(e: MouseEvent) => { if (!isActive(item.path)) (e.target as HTMLElement).style.backgroundColor = '' }"
          @click="sidebarOpen = false"
        >
          <img :src="item.icon" class="nav-icon" alt="" />
          <span>{{ item.label }}</span>
          <span v-if="item.badge" class="ml-auto bg-rose-500 text-white text-xs px-2 py-0.5 rounded-full">{{ item.badge }}</span>
        </router-link>
      </nav>

      <!-- Bottom user card -->
      <div class="p-4" style="border-top: 1px solid var(--sidebar-border);">
        <router-link to="/profile" class="flex items-center gap-3 p-2 rounded-xl transition-colors" style="color: var(--text-primary);">
          <div class="w-9 h-9 bg-white rounded-full flex items-center justify-center font-bold text-sm overflow-hidden" style="color: var(--brand-500);">
            <img v-if="getAvatarSrc(userStore.profile.avatarUrl)" :src="getAvatarSrc(userStore.profile.avatarUrl)" class="w-full h-full object-contain p-1" alt="" />
            <span v-else>{{ userStore.profile.nickname.charAt(0) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-800 truncate">{{ userStore.profile.nickname }}</p>
            <p class="text-xs text-gray-400">Lv.{{ userStore.profile.currentLevel }}</p>
          </div>
          <div class="text-gray-400">›</div>
        </router-link>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- Top header -->
      <header v-if="!isFullscreen" class="px-4 py-3 flex items-center gap-4 shrink-0" style="background-color: var(--header-bg); border-bottom: 1px solid var(--header-border);">
        <button class="lg:hidden" style="color: var(--text-secondary);" @click="sidebarOpen = !sidebarOpen">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>

        <div class="flex-1">
          <h2 class="text-lg font-semibold" style="color: var(--text-primary);">{{ currentTitle }}</h2>
        </div>

        <div class="flex items-center gap-3">
          <!-- 学习画像环 -->
          <ProfileRing
            :dimensions="profileModelingStore.dimensions"
            @open="showProfilePanel = true"
          />
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
          <!-- User role switcher -->
          <div class="flex items-center bg-gray-100 rounded-lg p-0.5">
            <button
              :class="['px-2.5 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5', currentUserId === 'default_user' ? 'bg-white text-space-700 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              @click="switchUser('default_user')"
            ><img :src="iconStudent" class="role-icon" alt="" /> 学习者</button>
            <button
              :class="['px-2.5 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5', currentUserId === 'admin_user' ? 'bg-white text-brand-700 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              @click="switchUser('admin_user')"
            ><img :src="iconExpert" class="role-icon" alt="" /> 高手</button>
          </div>
          <!-- Quick streak indicator -->
          <div class="hidden sm:flex items-center gap-1.5 bg-warning-50 text-warning-600 px-3 py-1.5 rounded-full text-sm font-medium">
            <img :src="iconStreak" class="header-icon" alt="" /> {{ learningStore.streakDays }}天
          </div>
          <!-- Coins -->
          <div class="hidden sm:flex items-center gap-1.5 bg-brand-50 text-brand-700 px-3 py-1.5 rounded-full text-sm font-medium">
            <img :src="iconCoin" class="header-icon" alt="" /> {{ userStore.profile.totalCoins }}
          </div>
          <!-- Notification bell -->
          <button class="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
            <span class="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full"></span>
          </button>
        </div>
      </header>

      <!-- Page content -->
      <div :class="isFullscreen ? 'flex-1' : 'flex-1 overflow-y-auto p-4 md:p-6'">
        <router-view v-slot="{ Component }">
          <transition :name="isFullscreen ? 'fade' : 'slide-up'" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useLearningStore } from '@/stores/learning'
import { useThemeStore } from '@/stores/theme'
import CosmicBackground from '@/components/common/CosmicBackground.vue'
import DesktopPet from '@/components/pet/DesktopPet.vue'
import PetSwitcher from '@/components/pet/PetSwitcher.vue'
import DebugPanel from '@/components/debug/DebugPanel.vue'
import { useProfileModelingStore } from '@/stores/profileModeling'
import ProfileRing from '@/components/profile/ProfileRing.vue'
import ProfilePanel from '@/components/profile/ProfilePanel.vue'
import AnalysisFloatingWindow from '@/components/analysis/AnalysisFloatingWindow.vue'
import SocraticPanel from '@/components/socratic/SocraticPanel.vue'
import { getAvatarSrc } from '@/utils/avatars'

// SVG 图标导入 — 蓝集（日常学习物件）
import iconDashboard from '@/assets/icons/blue/desk-lamp-svgrepo-com.svg'
import iconChat from '@/assets/icons/blue/earphone-svgrepo-com.svg'
import iconLearningPath from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import iconPractice from '@/assets/icons/blue/chip-svgrepo-com.svg'
import iconExam from '@/assets/icons/blue/alarm-clock-svgrepo-com.svg'
import iconWrongBook from '@/assets/icons/blue/brush-svgrepo-com.svg'
import iconProfile from '@/assets/icons/blue/wallet-svgrepo-com.svg'
// SVG 图标导入 — 星集（太空宇宙主题）
import iconKnowledgeGraph from '@/assets/icons/star/galaxy-svgrepo-com.svg'
import iconUniverse from '@/assets/icons/star/telescope-svgrepo-com.svg'
import iconAgentSquare from '@/assets/icons/star/spaceship-svgrepo-com.svg'
import iconStudent from '@/assets/icons/blue/desk-lamp-svgrepo-com.svg'
import iconExpert from '@/assets/icons/blue/trophy-svgrepo-com.svg'
import iconCoin from '@/assets/icons/blue/money-svgrepo-com.svg'
import iconStreak from '@/assets/icons/blue/fan-svgrepo-com.svg'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const learningStore = useLearningStore()
const themeStore = useThemeStore()
const profileModelingStore = useProfileModelingStore()
const sidebarOpen = ref(false)
const showProfilePanel = ref(false)

const currentUserId = ref(localStorage.getItem('user_id') || 'default_user')

const navItems = [
  { path: '/dashboard', label: '学习仪表盘', icon: iconDashboard },
  { path: '/agent-square', label: '智能体广场', icon: iconAgentSquare },
  { path: '/chat', label: 'AI对话助手', icon: iconChat },
  { path: '/learning-path', label: '学习路径', icon: iconLearningPath },
  { path: '/knowledge-graph', label: '知识图谱', icon: iconKnowledgeGraph },
  { path: '/universe', label: '知识宇宙', icon: iconUniverse },
  { path: '/practice', label: '练习中心', icon: iconPractice, badge: '' },
  { path: '/exam', label: '考试中心', icon: iconExam },
  { path: '/wrong-book', label: '错题本', icon: iconWrongBook },
  { path: '/profile', label: '个人中心', icon: iconProfile },
]

const isFullscreen = computed(() => route.meta.fullscreen === true)

const currentTitle = computed(() => route.meta.title || '数知')

function isActive(path: string): boolean {
  return route.path === path || (path !== '/dashboard' && route.path.startsWith(path))
}

function switchUser(userId: string) {
  if (currentUserId.value === userId) return
  localStorage.setItem('user_id', userId)
  window.location.reload()
}

let ws: WebSocket | null = null

onMounted(() => {
  userStore.fetchAchievements()
  learningStore.fetchReviews()
  learningStore.fetchTopicMastery()
  themeStore.applyTheme()
  profileModelingStore.fetchProfileModel()

  // ── WebSocket 连接（接收画像实时更新）──
  connectProfileWs()
})

function connectProfileWs() {
  const uid = localStorage.getItem('user_id') || 'default_user'
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location.host || 'localhost:8003'
  const wsUrl = `${proto}//${host}/ws/learning?user_id=${encodeURIComponent(uid)}`

  try {
    ws = new WebSocket(wsUrl)
    ws.onopen = () => {
      ws?.send(JSON.stringify({ type: 'subscribe', topic: 'profile' }))
    }
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        profileModelingStore.onWsMessage(msg)
      } catch { /* ignore */ }
    }
    ws.onclose = () => {
      // 5秒后自动重连
      setTimeout(() => { if (!ws || ws.readyState === WebSocket.CLOSED) connectProfileWs() }, 5000)
    }
    ws.onerror = () => { ws?.close() }
  } catch { /* WebSocket 不可用时忽略 */ }
}
</script>

<style scoped>
.nav-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  opacity: 0.85;
}

.router-link-active .nav-icon {
  opacity: 1;
}

.role-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.header-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
</style>
