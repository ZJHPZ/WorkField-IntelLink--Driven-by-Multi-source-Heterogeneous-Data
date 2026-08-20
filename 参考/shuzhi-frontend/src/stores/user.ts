import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export interface UserProfile {
  id: string
  username: string
  nickname: string
  email: string
  avatarUrl: string
  totalCoins: number
  currentLevel: number
  totalExp: number
  joinDate: string
}

export interface Achievement {
  id: string
  code: string
  name: string
  description: string
  iconUrl: string
  category: 'milestone' | 'streak' | 'skill' | 'special'
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  isUnlocked: boolean
  unlockedAt?: string
  progress: number
  target: number
}

export interface WeeklyReport {
  week: string
  startDate: string
  endDate: string
  summary: {
    totalStudyHours: number
    daysActive: number
    newTopics: number
    exercisesCompleted: number
    accuracy: number
    rankChange: number
  }
  topTopics: { name: string; hours: number }[]
  weakTopics: { name: string; accuracy: number }[]
  achievementsUnlocked: { name: string; days: number }[]
}

function getUserId(): string {
  return localStorage.getItem('user_id') || 'default_user'
}

function mapCategory(cat: string): Achievement['category'] {
  switch (cat) {
    case 'learning': return 'milestone'
    case 'streak': return 'streak'
    case 'mastery': return 'skill'
    default: return 'special'
  }
}

export const useUserStore = defineStore('user', () => {
  const isAdmin = getUserId() === 'admin_user'

  const profile = ref<UserProfile>(isAdmin ? {
    id: 'admin_user', username: 'admin', nickname: '大数据高手',
    email: 'admin@example.com', avatarUrl: '', totalCoins: 2850,
    currentLevel: 10, totalExp: 7300, joinDate: '2023-01-01',
  } : {
    id: getUserId(), username: 'learner', nickname: '大数据学习者',
    email: 'learner@example.com', avatarUrl: '', totalCoins: 240,
    currentLevel: 5, totalExp: 1250, joinDate: '2024-01-01',
  })

  const achievements = ref<Achievement[]>([])
  const weeklyReport = ref<WeeklyReport | null>(null)
  const isLoggedIn = computed(() => !!profile.value.id)

  const expToNextLevel = computed(() => profile.value.currentLevel * 300)
  const levelProgress = computed(() => (profile.value.totalExp % 300) / 300 * 100)

  const demoAchievements: Achievement[] = [
    { id: '1', code: 'first_topic', name: '初次解锁', description: '完成第一个知识点的学习', iconUrl: '', category: 'milestone', rarity: 'common', isUnlocked: true, unlockedAt: '2024-01-05', progress: 1, target: 1 },
    { id: '2', code: 'streak_7', name: '连续7天', description: '连续学习7天', iconUrl: '', category: 'streak', rarity: 'rare', isUnlocked: true, unlockedAt: '2024-01-12', progress: 7, target: 7 },
    { id: '3', code: 'master_5', name: '知识学徒', description: '掌握5个知识点', iconUrl: '', category: 'skill', rarity: 'rare', isUnlocked: true, unlockedAt: '2024-01-14', progress: 5, target: 5 },
    { id: '4', code: 'coins_500', name: '币圈达人', description: '累计获得500金币', iconUrl: '', category: 'milestone', rarity: 'epic', isUnlocked: false, progress: 240, target: 500 },
    { id: '5', code: 'master_all', name: '知识大师', description: '点亮所有基础知识', iconUrl: '', category: 'skill', rarity: 'legendary', isUnlocked: false, progress: 3, target: 8 },
    { id: '6', code: 'streak_30', name: '学习达人', description: '连续学习30天', iconUrl: '', category: 'streak', rarity: 'epic', isUnlocked: false, progress: 7, target: 30 },
    { id: '7', code: 'quiz_100', name: '答题高手', description: '完成100道练习题', iconUrl: '', category: 'skill', rarity: 'epic', isUnlocked: false, progress: 45, target: 100 },
    { id: '8', code: 'perfect_quiz', name: '完美通关', description: '一次练习正确率100%', iconUrl: '', category: 'special', rarity: 'legendary', isUnlocked: false, progress: 0, target: 1 },
  ]

  const demoReport: WeeklyReport = {
    week: '2024-W03', startDate: '2024-01-15', endDate: '2024-01-21',
    summary: { totalStudyHours: 12.5, daysActive: 6, newTopics: 3, exercisesCompleted: 45, accuracy: 78.5, rankChange: 5 },
    topTopics: [{ name: 'Spark RDD', hours: 4.5 }, { name: 'Shuffle', hours: 3.0 }],
    weakTopics: [{ name: 'DataFrame', accuracy: 0.55 }, { name: 'YARN', accuracy: 0.62 }],
    achievementsUnlocked: [{ name: '连续学习', days: 7 }],
  }

  // Admin (大数据高手) demo data
  const adminDemoAchievements: Achievement[] = [
    { id: '1', code: 'first_topic', name: '初次解锁', description: '完成第一个知识点的学习', iconUrl: '', category: 'milestone', rarity: 'common', isUnlocked: true, unlockedAt: '2024-01-05', progress: 1, target: 1 },
    { id: '2', code: 'streak_7', name: '连续7天', description: '连续学习7天', iconUrl: '', category: 'streak', rarity: 'rare', isUnlocked: true, unlockedAt: '2024-01-12', progress: 7, target: 7 },
    { id: '3', code: 'master_5', name: '知识学徒', description: '掌握5个知识点', iconUrl: '', category: 'skill', rarity: 'rare', isUnlocked: true, unlockedAt: '2024-01-20', progress: 24, target: 5 },
    { id: '4', code: 'coins_500', name: '币圈达人', description: '累计获得500金币', iconUrl: '', category: 'milestone', rarity: 'epic', isUnlocked: true, unlockedAt: '2024-02-10', progress: 500, target: 500 },
    { id: '5', code: 'master_all', name: '知识大师', description: '点亮所有基础知识', iconUrl: '', category: 'skill', rarity: 'legendary', isUnlocked: true, unlockedAt: '2024-05-15', progress: 24, target: 8 },
    { id: '6', code: 'streak_30', name: '学习达人', description: '连续学习30天', iconUrl: '', category: 'streak', rarity: 'epic', isUnlocked: true, unlockedAt: '2024-02-15', progress: 365, target: 30 },
    { id: '7', code: 'quiz_100', name: '答题高手', description: '完成100道练习题', iconUrl: '', category: 'skill', rarity: 'epic', isUnlocked: true, unlockedAt: '2024-04-01', progress: 500, target: 100 },
    { id: '8', code: 'perfect_quiz', name: '完美通关', description: '一次练习正确率100%', iconUrl: '', category: 'special', rarity: 'legendary', isUnlocked: true, unlockedAt: '2024-03-20', progress: 1, target: 1 },
  ]

  const adminDemoReport: WeeklyReport = {
    week: '2024-W20', startDate: '2024-05-13', endDate: '2024-05-19',
    summary: { totalStudyHours: 52.5, daysActive: 7, newTopics: 24, exercisesCompleted: 500, accuracy: 98.5, rankChange: 0 },
    topTopics: [{ name: 'Spark Streaming', hours: 12.5 }, { name: 'Flink', hours: 10.0 }],
    weakTopics: [],
    achievementsUnlocked: [{ name: '知识大师', days: 365 }, { name: '完美通关', days: 200 }, { name: '学习达人', days: 30 }],
  }

  async function fetchProfile() {
    const userId = getUserId()
    try {
      const data = await client.get(`/api/v1/users/${userId}/profile`) as any
      if (data?.code === 200 && data.data) {
        const d = data.data
        profile.value = {
          id: d.user_id || userId,
          username: d.username || userId,
          nickname: d.nickname || '学习者',
          email: d.email || '',
          avatarUrl: d.avatar_url || '',
          totalCoins: d.curiosity_score ? d.curiosity_score * 3 : 240,
          currentLevel: d.overall_level || 1,
          totalExp: (d.total_hours || 0) * 10,
          joinDate: d.created_at || '2024-01-01',
        }
        return
      }
    } catch { /* use demo data */ }
  }

  async function fetchAchievements() {
    try {
      const [userAchs, progress] = await Promise.all([
        client.get('/api/v1/achievements/user') as any,
        client.get('/api/v1/achievements/user/progress') as any,
      ])

      if (Array.isArray(userAchs) && userAchs.length > 0) {
        const progressMap: Record<string, any> = {}
        if (Array.isArray(progress)) {
          progress.forEach((p: any) => { progressMap[p.achievement_id] = p })
        }

        achievements.value = userAchs.map((ua: any) => {
          const ach = ua.achievement || {}
          const prog = progressMap[ua.achievement_id] || {}
          return {
            id: ua.id || '',
            code: ach.code || '',
            name: ach.name || '未知成就',
            description: ach.description || '',
            iconUrl: ach.icon_url || '',
            category: mapCategory(ach.category || ''),
            rarity: (ach.points || 0) > 50 ? 'legendary' : (ach.points || 0) > 30 ? 'epic' : (ach.points || 0) > 10 ? 'rare' : 'common',
            isUnlocked: true,
            unlockedAt: ua.unlocked_at,
            progress: prog.current_progress || 0,
            target: prog.target || 1,
          }
        })
        return
      }
    } catch { /* use demo data */ }
    achievements.value = getUserId() === 'admin_user' ? adminDemoAchievements : demoAchievements
  }

  async function updateAvatar(avatarUrl: string) {
    const userId = getUserId()
    profile.value.avatarUrl = avatarUrl
    try {
      await client.put(`/api/v1/users/${userId}/avatar`, { avatar_url: avatarUrl })
    } catch { /* 后端不可用时本地已更新 */ }
  }

  async function fetchWeeklyReport() {
    try {
      const data = await client.get('/api/v1/learning/reports/weekly') as any
      if (data) {
        weeklyReport.value = {
          week: data.week_start ? `${data.week_start} ~ ${data.week_end}` : '本周',
          startDate: data.week_start || '',
          endDate: data.week_end || '',
          summary: {
            totalStudyHours: data.total_learning_hours || 0,
            daysActive: data.days_active || data.total_sessions || 0,
            newTopics: data.topics_learned || 0,
            exercisesCompleted: data.total_exercises || 0,
            accuracy: data.correct_rate || 0,
            rankChange: 0,
          },
          topTopics: (data.strengths || []).map((s: string) => ({ name: s, hours: 0 })),
          weakTopics: (data.improvements || []).map((s: string) => ({ name: s, accuracy: 0 })),
          achievementsUnlocked: (data.new_achievements || []).map((s: string) => ({ name: s, days: 0 })),
        }
        return
      }
    } catch { /* use demo data */ }
    weeklyReport.value = getUserId() === 'admin_user' ? adminDemoReport : demoReport
  }

  return {
    profile, achievements, weeklyReport, isLoggedIn, expToNextLevel, levelProgress,
    fetchProfile, fetchAchievements, fetchWeeklyReport, updateAvatar,
  }
})
