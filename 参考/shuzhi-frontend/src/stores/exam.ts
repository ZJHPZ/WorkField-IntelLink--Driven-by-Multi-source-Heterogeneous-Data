import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export interface ExamPaper {
  id: string
  title: string
  description: string | null
  topic_ids: string[]
  difficulty_mix: Record<string, number>
  total_questions: number
  time_limit: number
  passing_score: number
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export interface ExamQuestion {
  index: number
  id: number
  type: string
  topic_id: string
  difficulty: string
  content: string
  options: { key: string; text: string }[]
  time_limit: number
}

export interface ExamSession {
  session_id: string
  paper_title: string
  paper_id: string
  total_questions: number
  time_limit: number
  questions: ExamQuestion[]
  started_at: string
}

export interface AnswerResult {
  question_index: number
  is_correct: boolean
  correct_answer: string
  explanation: string
  score: number
}

export interface AnswerDetail {
  question_index: number
  question_id: number
  type: string
  topic_id: string
  difficulty: string
  content: string
  options: { key: string; text: string }[]
  user_answer: string
  correct_answer: string
  is_correct: boolean
  explanation: string
  score: number
}

export interface ExamResult {
  session_id: string
  paper_id: string
  paper_title: string
  status: string
  total_score: number
  max_score: number
  correct_count: number
  total_questions: number
  accuracy: number
  is_passed: boolean
  passing_score: number
  time_spent: number
  started_at: string | null
  submitted_at: string | null
  answers: AnswerDetail[]
  topic_breakdown: { topic_id: string; total: number; correct: number; rate: number }[]
}

export interface ExamHistoryItem {
  session_id: string
  paper_id: string
  paper_title: string
  status: string
  total_score: number
  max_score: number
  correct_count: number
  total_questions: number
  accuracy: number
  is_passed: boolean
  time_spent: number
  started_at: string | null
  submitted_at: string | null
}

export const useExamStore = defineStore('exam', () => {
  // ===== State =====
  const papers = ref<ExamPaper[]>([])
  const papersLoading = ref(false)
  const savingPaper = ref(false)

  // Topic list for paper form
  const topicOptions = ref<{ id: string; name: string; category: string; question_count: number }[]>([])

  const session = ref<ExamSession | null>(null)
  const sessionLoading = ref(false)

  const answers = ref<Record<number, string>>({})
  const answerResults = ref<Record<number, AnswerResult>>({})

  const timerSeconds = ref(0)
  const timeLimitSeconds = ref(0)
  const examStatus = ref<'idle' | 'in_progress' | 'submitting' | 'completed'>('idle')

  const result = ref<ExamResult | null>(null)
  const resultLoading = ref(false)

  const history = ref<ExamHistoryItem[]>([])
  const historyLoading = ref(false)

  let timerInterval: ReturnType<typeof setInterval> | null = null
  let autoSaveInterval: ReturnType<typeof setInterval> | null = null

  // ===== Computed =====
  const currentQuestion = computed(() => {
    if (!session.value) return null
    const idx = currentIndex.value
    return session.value.questions[idx] || null
  })

  const currentIndex = ref(0)

  const answeredCount = computed(() => Object.keys(answers.value).length)

  const timeRemaining = computed(() => {
    return Math.max(0, timeLimitSeconds.value - timerSeconds.value)
  })

  const progressPercent = computed(() => {
    if (!session.value) return 0
    return Math.round((answeredCount.value / session.value.total_questions) * 100)
  })

  // ===== Actions =====

  async function fetchPapers(activeOnly = false) {
    papersLoading.value = true
    try {
      const data = await client.get('/api/v1/exam/papers', { params: { active_only: activeOnly } }) as any
      papers.value = data.papers || []
    } catch (e) {
      console.error('获取试卷列表失败:', e)
    } finally {
      papersLoading.value = false
    }
  }

  // ===== Admin actions =====

  async function fetchTopicOptions() {
    if (topicOptions.value.length > 0) return
    try {
      const cats = await client.get('/api/v1/practice/categories') as any[]
      const topics: { id: string; name: string; category: string; question_count: number }[] = []
      for (const cat of (cats || [])) {
        for (const t of (cat.topics || [])) {
          topics.push({ id: t.id, name: t.name, category: cat.name, question_count: t.question_count })
        }
      }
      topicOptions.value = topics
    } catch (e) {
      console.error('获取题库主题失败:', e)
    }
  }

  async function createPaper(data: {
    title: string; description: string; topic_ids: string[]
    difficulty_mix: Record<string, number>; total_questions: number
    time_limit: number; passing_score: number; is_active: boolean
  }) {
    savingPaper.value = true
    try {
      await client.post('/api/v1/exam/papers', data)
      await fetchPapers(false)
    } catch (e: any) {
      throw e
    } finally {
      savingPaper.value = false
    }
  }

  async function updatePaper(paperId: string, data: Record<string, any>) {
    savingPaper.value = true
    try {
      await client.put(`/api/v1/exam/papers/${paperId}`, data)
      await fetchPapers(false)
    } catch (e: any) {
      throw e
    } finally {
      savingPaper.value = false
    }
  }

  async function deletePaper(paperId: string) {
    try {
      await client.delete(`/api/v1/exam/papers/${paperId}`)
      papers.value = papers.value.filter(p => p.id !== paperId)
    } catch (e: any) {
      throw e
    }
  }

  async function togglePublish(paperId: string, isActive: boolean) {
    try {
      await client.put(`/api/v1/exam/papers/${paperId}`, { is_active: isActive })
      const p = papers.value.find(p => p.id === paperId)
      if (p) p.is_active = isActive
    } catch (e: any) {
      throw e
    }
  }

  async function fetchPaper(paperId: string): Promise<ExamPaper | null> {
    try {
      return await client.get(`/api/v1/exam/papers/${paperId}`) as ExamPaper
    } catch (e) {
      console.error('获取试卷详情失败:', e)
      return null
    }
  }

  async function startSelfTest(topicIds: string[], questionCount: number, timeLimit: number) {
    sessionLoading.value = true
    try {
      const data = await client.post('/api/v1/exam/self-test', {
        topic_ids: topicIds,
        question_count: questionCount,
        time_limit: timeLimit,
      }) as any
      session.value = data as ExamSession
      answers.value = {}
      answerResults.value = {}
      currentIndex.value = 0
      timeLimitSeconds.value = (data.time_limit || 60) * 60
      timerSeconds.value = 0
      examStatus.value = 'in_progress'
      result.value = null
      startTimer()
      return data.session_id as string
    } catch (e: any) {
      console.error('开始自测失败:', e)
      throw e
    } finally {
      sessionLoading.value = false
    }
  }

  async function startExam(paperId: string) {
    sessionLoading.value = true
    try {
      const data = await client.post(`/api/v1/exam/papers/${paperId}/start`) as any
      session.value = data as ExamSession
      answers.value = {}
      answerResults.value = {}
      currentIndex.value = 0
      timeLimitSeconds.value = (data.time_limit || 60) * 60
      timerSeconds.value = 0
      examStatus.value = 'in_progress'
      result.value = null
      startTimer()
    } catch (e: any) {
      console.error('开始考试失败:', e)
      throw e
    } finally {
      sessionLoading.value = false
    }
  }

  async function resumeSession(sessionId: string) {
    sessionLoading.value = true
    try {
      const data = await client.get(`/api/v1/exam/sessions/${sessionId}`) as any
      session.value = data as ExamSession

      // 获取进度
      const progress = await client.get(`/api/v1/exam/sessions/${sessionId}/progress`) as any
      currentIndex.value = progress.current_index || 0
      timeLimitSeconds.value = progress.time_limit || 0
      timerSeconds.value = progress.time_spent || 0
      examStatus.value = progress.status === 'completed' ? 'completed' : 'in_progress'

      if (examStatus.value === 'in_progress') {
        startTimer()
      }
    } catch (e: any) {
      console.error('恢复考试失败:', e)
      throw e
    } finally {
      sessionLoading.value = false
    }
  }

  async function submitAnswer(questionIndex: number, answer: string) {
    if (!session.value) return

    answers.value = { ...answers.value, [questionIndex]: answer }

    try {
      const data = await client.post(`/api/v1/exam/sessions/${session.value.session_id}/answer`, {
        question_index: questionIndex,
        answer,
      }) as AnswerResult
      answerResults.value = { ...answerResults.value, [questionIndex]: data }
    } catch (e) {
      console.error('提交答案失败:', e)
    }
  }

  function selectAnswer(questionIndex: number, answer: string) {
    submitAnswer(questionIndex, answer)
  }

  function goToQuestion(index: number) {
    if (index >= 0 && session.value && index < session.value.total_questions) {
      currentIndex.value = index
    }
  }

  async function completeExam() {
    if (!session.value) return
    examStatus.value = 'submitting'
    stopTimer()
    try {
      const data = await client.post(`/api/v1/exam/sessions/${session.value.session_id}/complete`) as ExamResult
      result.value = data
      examStatus.value = 'completed'
    } catch (e: any) {
      console.error('交卷失败:', e)
      examStatus.value = 'in_progress'
      startTimer()
      throw e
    }
  }

  async function fetchResult(sessionId: string) {
    resultLoading.value = true
    try {
      result.value = await client.get(`/api/v1/exam/sessions/${sessionId}/result`) as ExamResult
    } catch (e) {
      console.error('获取考试结果失败:', e)
    } finally {
      resultLoading.value = false
    }
  }

  async function fetchHistory() {
    historyLoading.value = true
    try {
      history.value = await client.get('/api/v1/exam/sessions') as ExamHistoryItem[]
    } catch (e) {
      console.error('获取考试历史失败:', e)
    } finally {
      historyLoading.value = false
    }
  }

  // ===== Timer =====

  function startTimer() {
    stopTimer()
    timerInterval = setInterval(() => {
      timerSeconds.value++
      if (timerSeconds.value >= timeLimitSeconds.value) {
        completeExam()
      }
    }, 1000)
    autoSaveInterval = setInterval(() => {
      if (session.value && examStatus.value === 'in_progress') {
        client.post(`/api/v1/exam/sessions/${session.value.session_id}/progress`, {
          current_index: currentIndex.value,
          time_spent: timerSeconds.value,
        }).catch(() => {})
      }
    }, 30000)
  }

  function stopTimer() {
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
    if (autoSaveInterval) { clearInterval(autoSaveInterval); autoSaveInterval = null }
  }

  function resetExam() {
    stopTimer()
    session.value = null
    answers.value = {}
    answerResults.value = {}
    currentIndex.value = 0
    timerSeconds.value = 0
    timeLimitSeconds.value = 0
    examStatus.value = 'idle'
    result.value = null
  }

  return {
    papers,
    papersLoading,
    savingPaper,
    topicOptions,
    session,
    sessionLoading,
    answers,
    answerResults,
    timerSeconds,
    timeLimitSeconds,
    examStatus,
    result,
    resultLoading,
    history,
    historyLoading,
    currentIndex,
    currentQuestion,
    answeredCount,
    timeRemaining,
    progressPercent,
    fetchPapers,
    fetchPaper,
    fetchTopicOptions,
    createPaper,
    updatePaper,
    deletePaper,
    togglePublish,
    startSelfTest,
    startExam,
    resumeSession,
    submitAnswer,
    selectAnswer,
    goToQuestion,
    completeExam,
    fetchResult,
    fetchHistory,
    resetExam,
    stopTimer,
  }
})
