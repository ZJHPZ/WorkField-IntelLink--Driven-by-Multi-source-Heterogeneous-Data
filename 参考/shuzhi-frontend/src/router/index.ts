import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '学习仪表盘', icon: 'home' },
    },
    {
      path: '/agent-square',
      name: 'AgentSquare',
      component: () => import('@/views/AgentSquare.vue'),
      meta: { title: '智能体广场', icon: 'agents' },
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { title: 'AI对话助手', icon: 'chat' },
    },
    {
      path: '/learning-path',
      name: 'LearningPath',
      component: () => import('@/views/LearningPath.vue'),
      meta: { title: '学习路径', icon: 'path' },
    },
    {
      path: '/knowledge-graph',
      name: 'KnowledgeGraph',
      component: () => import('@/views/KnowledgeGraph.vue'),
      meta: { title: '知识图谱', icon: 'graph' },
    },
    {
      path: '/practice',
      name: 'Practice',
      component: () => import('@/views/PracticeCenter.vue'),
      meta: { title: '练习中心', icon: 'practice' },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: '个人中心', icon: 'user' },
    },
    {
      path: '/universe',
      name: 'Universe',
      component: () => import('@/views/UniverseView.vue'),
      meta: { title: '知识宇宙', icon: 'universe', fullscreen: true },
    },
    {
      path: '/exam',
      name: 'ExamList',
      component: () => import('@/views/ExamList.vue'),
      meta: { title: '考试中心', icon: 'exam' },
    },
    {
      path: '/exam/:sessionId',
      name: 'ExamSession',
      component: () => import('@/views/ExamSession.vue'),
      meta: { title: '考试中', fullscreen: true },
    },
    {
      path: '/exam/:sessionId/result',
      name: 'ExamResult',
      component: () => import('@/views/ExamResult.vue'),
      meta: { title: '考试结果' },
    },
    {
      path: '/wrong-book',
      name: 'WrongBook',
      component: () => import('@/views/WrongBook.vue'),
      meta: { title: '错题本', fullscreen: true },
    },
  ],
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '数知'} - 大数据智能学习平台`
})

export default router
