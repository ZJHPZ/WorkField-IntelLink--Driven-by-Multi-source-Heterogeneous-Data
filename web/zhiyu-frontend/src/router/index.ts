import { createRouter, createWebHistory } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ── Root redirect：记忆上次选择 → 直接进对应侧；新用户 → 选边页 ──
    {
      path: '/',
      redirect: () => {
        const r = localStorage.getItem('app_role')
        return r === 'personal' ? '/personal' : r === 'enterprise' ? '/enterprise' : '/choose'
      },
    },

    // ═══════════════════════════════════════════
    // 选边页 (Role Choose) — 双端前门，无 meta.role（守卫放行）
    // ═══════════════════════════════════════════
    {
      path: '/choose',
      name: 'RoleChoose',
      component: () => import('@/views/RoleChooseView.vue'),
      meta: { title: '选择工作台', fullscreen: true },
    },

    // ═══════════════════════════════════════════
    // 企业侧 (Enterprise) — 10 routes
    // ═══════════════════════════════════════════
    {
      path: '/enterprise',
      name: 'EnterpriseDashboard',
      component: () => import('@/views/enterprise/DashboardView.vue'),
      meta: { title: '企业工作台', role: 'enterprise' },
    },
    {
      path: '/enterprise/positions',
      name: 'Positions',
      component: () => import('@/views/enterprise/PositionsView.vue'),
      meta: { title: '岗位标准管理', role: 'enterprise' },
    },
    {
      // 岗位 title 可能含 `/`（如 法务专员/助理），`:id(.*)` 允许斜杠
      path: '/enterprise/positions/:id(.*)',
      name: 'PositionDetail',
      component: () => import('@/views/enterprise/PositionDetailView.vue'),
      meta: { title: '岗位详情', role: 'enterprise' },
    },
    {
      path: '/enterprise/positions/:id(.*)/diff',
      name: 'PositionDiff',
      component: () => import('@/views/enterprise/PositionDiffView.vue'),
      meta: { title: '差异报告', role: 'enterprise' },
    },
    {
      path: '/enterprise/discovery',
      name: 'Discovery',
      component: () => import('@/views/enterprise/DiscoveryView.vue'),
      meta: { title: '新岗位发现', role: 'enterprise' },
    },
    {
      path: '/enterprise/diagnose',
      name: 'Diagnose',
      component: () => import('@/views/enterprise/DiagnoseView.vue'),
      meta: { title: 'JD 质量诊断', role: 'enterprise' },
    },
    {
      path: '/enterprise/diagnose/batch',
      name: 'DiagnoseBatch',
      component: () => import('@/views/enterprise/BatchDiagnoseView.vue'),
      meta: { title: '批量审计', role: 'enterprise' },
    },
    {
      path: '/enterprise/team',
      name: 'Team',
      component: () => import('@/views/enterprise/TeamView.vue'),
      meta: { title: '团队技能盘点', role: 'enterprise' },
    },
    {
      path: '/enterprise/forecast',
      name: 'Forecast',
      component: () => import('@/views/enterprise/ForecastView.vue'),
      meta: { title: '人才需求预测', role: 'enterprise' },
    },
    {
      path: '/enterprise/graph',
      name: 'Graph',
      component: () => import('@/views/enterprise/GraphView.vue'),
      meta: { title: '全图谱可视化', role: 'enterprise', fullscreen: true },
    },

    // ═══════════════════════════════════════════
    // 个人侧 (Personal) — 8 routes
    // ═══════════════════════════════════════════
    {
      path: '/personal',
      name: 'PersonalDashboard',
      component: () => import('@/views/personal/DashboardView.vue'),
      meta: { title: '个人主页', role: 'personal' },
    },
    {
      path: '/personal/explore',
      name: 'Explore',
      component: () => import('@/views/personal/ExploreView.vue'),
      meta: { title: '岗位探索', role: 'personal' },
    },
    {
      path: '/personal/profile',
      name: 'Profile',
      component: () => import('@/views/personal/ProfileView.vue'),
      meta: { title: '技能画像', role: 'personal' },
    },
    {
      path: '/personal/match',
      name: 'Match',
      component: () => import('@/views/personal/MatchView.vue'),
      meta: { title: '人岗匹配', role: 'personal' },
    },
    {
      path: '/personal/match/compare',
      name: 'MatchCompare',
      component: () => import('@/views/personal/CompareView.vue'),
      meta: { title: '岗位对比', role: 'personal' },
    },
    {
      path: '/personal/resume',
      name: 'Resume',
      component: () => import('@/views/personal/ResumeView.vue'),
      meta: { title: '简历解析', role: 'personal' },
    },
    {
      path: '/personal/learning-path',
      name: 'LearningPath',
      component: () => import('@/views/personal/LearningPathView.vue'),
      meta: { title: '学习路径', role: 'personal' },
    },
    {
      path: '/personal/freshness',
      name: 'Freshness',
      component: () => import('@/views/personal/FreshnessView.vue'),
      meta: { title: '技能保鲜', role: 'personal' },
    },
    {
      path: '/personal/switch',
      name: 'CareerSwitch',
      component: () => import('@/views/personal/SwitchView.vue'),
      meta: { title: '转行分析', role: 'personal' },
    },
    {
      path: '/personal/growth',
      name: 'Growth',
      component: () => import('@/views/personal/GrowthView.vue'),
      meta: { title: '成长轨迹', role: 'personal' },
    },
    {
      path: '/personal/chat',
      name: 'AIChat',
      component: () => import('@/views/personal/ChatView.vue'),
      meta: { title: 'AI 职业顾问', role: 'personal' },
    },
    {
      path: '/personal/center',
      name: 'PersonalCenter',
      component: () => import('@/views/personal/PersonalCenterView.vue'),
      meta: { title: '个人中心', role: 'personal' },
    },
    {
      path: '/personal/spectrum',
      name: 'Spectrum',
      component: () => import('@/views/personal/SpectrumView.vue'),
      meta: { title: '技能信号光谱', role: 'personal' },
    },
    {
      // 技能名可能含 `/`，同样用 `(.*)` 放行斜杠
      path: '/personal/spectrum/:skill(.*)',
      name: 'SpectrumDetail',
      component: () => import('@/views/personal/SpectrumDetailView.vue'),
      meta: { title: '技能信号示波', role: 'personal' },
    },
    {
      path: '/personal/evolution',
      name: 'EvolutionTheater',
      component: () => import('@/views/personal/EvolutionTheaterView.vue'),
      meta: { title: '岗位演化剧场', role: 'personal' },
    },
  ],
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '职域智联'} - 岗位标准智能管理平台`
  // 跨侧守卫：目标路由声明了 role 且与当前身份不符 → 弹回选边页
  const role = to.meta.role
  if (role && role !== useAppStore().role) return '/choose'
})

export default router
