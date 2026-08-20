import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export interface WrongQuestionOption {
  key: string
  text: string
}

export interface WrongQuestionItem {
  question_id: number
  type: string
  topic_id: string
  topic_name: string
  difficulty: string
  content: string
  options: WrongQuestionOption[]
  user_answer: string
  correct_answer: string
  explanation: string
  source: string
  source_label: string
  created_at: string | null
  reviewed: boolean
}

export interface WrongTopicGroup {
  topic_id: string
  topic_name: string
  wrong_count: number
  total_attempts: number
  error_rate: number
  questions: WrongQuestionItem[]
}

export interface WrongBookResponse {
  groups: WrongTopicGroup[]
  total_wrong: number
  total_topics: number
  total_questions: number
}

export interface WrongBookStats {
  total_wrong: number
  total_topics: number
  total_questions: number
  topic_distribution: { topic_id: string; topic_name: string; wrong_count: number; rate: number }[]
  daily_trend: { date: string; wrong_count: number }[]
}

export const useWrongBookStore = defineStore('wrongBook', () => {
  const groups = ref<WrongTopicGroup[]>([])
  const stats = ref<WrongBookStats | null>(null)
  const loading = ref(false)
  const filterTopic = ref<string | null>(null)

  // Book mode state
  const bookTopicId = ref<string | null>(null)
  const bookPageIndex = ref(0)

  const totalWrong = computed(() => {
    if (filterTopic.value) {
      const g = groups.value.find(g => g.topic_id === filterTopic.value)
      return g ? g.wrong_count : 0
    }
    return groups.value.reduce((sum, g) => sum + g.wrong_count, 0)
  })

  const filteredGroups = computed(() => {
    if (!filterTopic.value) return groups.value
    return groups.value.filter(g => g.topic_id === filterTopic.value)
  })

  // Book mode computed
  const bookTopic = computed(() =>
    groups.value.find(g => g.topic_id === bookTopicId.value) ?? null
  )

  const bookQuestions = computed(() =>
    bookTopic.value?.questions ?? []
  )

  const bookTotalPages = computed(() =>
    bookQuestions.value.length
  )

  const bookCurrentQuestion = computed(() =>
    bookQuestions.value[bookPageIndex.value] ?? null
  )

  async function fetchWrongBook(topicId?: string | null) {
    loading.value = true
    try {
      const params: Record<string, string> = {}
      if (topicId) params.topic_id = topicId
      const data = await client.get('/api/v1/wrong-book/', { params }) as WrongBookResponse
      groups.value = data.groups
    } finally {
      loading.value = false
    }
  }

  async function markReviewed(questionId: number, source: string) {
    try {
      await client.post('/api/v1/wrong-book/review', { question_id: questionId, source })
      // 本地更新状态
      for (const g of groups.value) {
        const q = g.questions.find(q => q.question_id === questionId && q.source === source)
        if (q) { q.reviewed = true; break }
      }
    } catch { /* ignore */ }
  }

  async function fetchStats() {
    stats.value = await client.get('/api/v1/wrong-book/stats') as WrongBookStats
  }

  function openBook(topicId: string) {
    bookTopicId.value = topicId
    bookPageIndex.value = 0
  }

  function closeBook() {
    bookTopicId.value = null
    bookPageIndex.value = 0
  }

  function goToPage(index: number) {
    if (index >= 0 && index < bookTotalPages.value) {
      bookPageIndex.value = index
    }
  }

  function nextPage() {
    goToPage(bookPageIndex.value + 1)
  }

  function prevPage() {
    goToPage(bookPageIndex.value - 1)
  }

  return {
    groups,
    stats,
    loading,
    filterTopic,
    totalWrong,
    filteredGroups,
    fetchWrongBook,
    fetchStats,
    markReviewed,
    // Book mode
    bookTopicId,
    bookPageIndex,
    bookTopic,
    bookQuestions,
    bookTotalPages,
    bookCurrentQuestion,
    openBook,
    closeBook,
    goToPage,
    nextPage,
    prevPage,
  }
})
