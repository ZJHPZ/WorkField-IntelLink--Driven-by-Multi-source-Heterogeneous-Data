<template>
  <div class="space-y-6 animate-fade-in-up">
    <div>
      <h1 class="text-2xl font-bold text-space-800"><img :src="rocketIcon" class="icon-title" alt="" /> 练习中心</h1>
      <p class="text-gray-400 text-sm mt-1">街机闯关式练习，挑战你的知识极限！</p>
    </div>

    <!-- Stats bar -->
    <div class="grid grid-cols-3 gap-4">
      <div class="glass-card rounded-2xl p-4 text-center">
        <div class="text-2xl font-bold text-brand-600 tabular-nums">{{ score }}</div>
        <div class="text-xs text-gray-400">当前得分</div>
      </div>
      <div class="glass-card rounded-2xl p-4 text-center">
        <div class="text-2xl font-bold text-mint-600 tabular-nums">{{ streak }}</div>
        <div class="text-xs text-gray-400">连续答对</div>
      </div>
      <div class="glass-card rounded-2xl p-4 text-center">
        <div class="text-2xl font-bold text-amber-600 tabular-nums">{{ totalAnswered }}</div>
        <div class="text-xs text-gray-400">已答题数</div>
      </div>
    </div>

    <!-- Quiz area -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Topic selection -->
      <div class="glass-card rounded-2xl p-5">
        <h3 class="text-base font-semibold text-space-800 mb-4"><img :src="planListIcon" class="icon-title" alt="" /> 选择题库</h3>

        <!-- Loading topics -->
        <div v-if="topicsLoading" class="space-y-2">
          <div v-for="i in 5" :key="i" class="h-12 bg-gray-100 rounded-xl animate-pulse" />
        </div>

        <!-- Category accordion -->
        <div v-else class="space-y-1 max-h-64 overflow-y-auto">
          <template v-for="cat in categories" :key="cat.id">
            <button
              class="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1"
              @click="toggleCategory(cat.id)"
            >
              <span class="transition-transform text-[10px]" :class="expandedCats.has(cat.id) ? 'rotate-90' : ''">▶</span>
              {{ cat.name }} ({{ cat.topics.reduce((s, t) => s + t.question_count, 0) }}题)
            </button>
            <div v-if="expandedCats.has(cat.id)" class="space-y-0.5 ml-2">
              <button
                v-for="topic in cat.topics" :key="topic.id"
                class="w-full text-left px-3 py-2 rounded-xl border transition-all text-sm"
                :class="selectedTopicId === topic.id ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-transparent hover:bg-gray-50 text-gray-600'"
                @click="selectTopic(topic)"
              >
                <span class="font-medium">{{ topic.name }}</span>
                <span class="text-xs text-gray-400 ml-2">{{ topic.question_count }}题</span>
              </button>
            </div>
          </template>
        </div>

        <!-- Difficulty -->
        <div class="mt-4 space-y-2">
          <label class="text-xs text-gray-500 font-medium">难度</label>
          <div class="flex gap-2">
            <button
              v-for="d in availableDifficulties" :key="d.value"
              class="flex-1 py-2 rounded-lg text-xs font-medium border transition-all"
              :class="selectedDifficulty === d.value ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-gray-100 text-gray-500 hover:bg-gray-50'"
              @click="selectedDifficulty = d.value"
            >{{ d.label }}</button>
          </div>
        </div>

        <!-- Count selector -->
        <div class="mt-3 space-y-1">
          <label class="text-xs text-gray-500 font-medium">题目数量</label>
          <div class="flex gap-2">
            <button
              v-for="n in [5, 10, 15, 20]" :key="n"
              class="flex-1 py-1.5 rounded-lg text-xs font-medium border transition-all"
              :class="questionCount === n ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-gray-100 text-gray-500 hover:bg-gray-50'"
              @click="questionCount = n"
            >{{ n }}题</button>
          </div>
        </div>

        <button
          @click="startQuiz"
          :disabled="!selectedTopicId || questionsLoading"
          class="w-full mt-4 py-3 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="questionsLoading" class="flex items-center justify-center gap-2">
            <span class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            加载中...
          </span>
          <span v-else>开始练习</span>
        </button>
      </div>

      <!-- Question area -->
      <div class="lg:col-span-2">
        <div v-if="quizActive && currentQuestion" class="glass-card rounded-2xl p-6">
          <!-- Progress bar -->
          <div class="flex items-center gap-3 mb-6">
            <span class="text-xs text-gray-400">第 {{ currentIndex + 1 }}/{{ questions.length }} 题</span>
            <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-brand-500 rounded-full transition-all duration-500"
                :style="{ width: ((currentIndex + 1) / questions.length * 100) + '%' }" />
            </div>
            <span v-if="timer > 0" class="text-xs font-bold tabular-nums" :class="timer < 10 ? 'text-rose-500 animate-pulse' : 'text-gray-500'">
              ⏱️ {{ timer }}s
            </span>
          </div>

          <!-- Question -->
          <div class="mb-6">
            <span class="text-xs px-2 py-0.5 rounded-full font-medium mb-2 inline-block"
              :class="difficultyBadgeClass">{{ difficultyLabel }}</span>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium mb-2 inline-block ml-1"
              :class="questionTypeBadge">{{ questionTypeLabel }}</span>
            <h3 class="text-lg font-semibold text-space-800 mt-2">{{ currentQuestion.content }}</h3>
          </div>

          <!-- Options -->
          <div class="space-y-3">
            <button v-for="option in currentQuestion.options" :key="option.key"
              class="w-full text-left p-4 rounded-xl border-2 transition-all duration-300"
              :class="optionClass(option.key)"
              :disabled="answered"
              @click="submitAnswer(option.key)">
              <div class="flex items-center gap-3">
                <span class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 transition-colors"
                  :class="optionKeyBg(option.key)">{{ option.key }}</span>
                <span class="text-sm">{{ option.text }}</span>
                <span v-if="answered && option.key === correctAnswer" class="ml-auto text-mint-500 font-medium">✓ 正确</span>
                <span v-else-if="answered && option.key === selectedAnswer && option.key !== correctAnswer" class="ml-auto text-rose-500 font-medium">✗</span>
              </div>
            </button>
          </div>

          <!-- Feedback -->
          <div v-if="answered" class="mt-6 p-4 rounded-xl animate-fade-in-up"
            :class="isCorrect ? 'bg-mint-50 border border-mint-200' : 'bg-rose-50 border border-rose-200'">
            <p class="text-sm font-semibold mb-1" :class="isCorrect ? 'text-mint-700' : 'text-rose-700'">
              <img v-if="isCorrect" :src="happyIcon" class="icon-inline" alt="" />
              <img v-else :src="sadIcon" class="icon-inline" alt="" />
              {{ isCorrect ? ' 回答正确！' : ' 回答错误' }}
            </p>
            <p class="text-xs text-gray-500 mb-3">{{ feedbackExplanation }}</p>
            <button @click="nextQuestion"
              class="px-5 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              {{ currentIndex + 1 < questions.length ? '下一题 →' : '查看结果' }}
            </button>
          </div>
        </div>

        <!-- Quiz result -->
        <div v-else-if="quizFinished" class="glass-card rounded-2xl p-8 text-center animate-scale-in">
          <img :src="resultIcon" class="icon-result-lg mx-auto mb-4" alt="" />
          <h2 class="text-2xl font-bold text-space-800 mb-2">练习完成！</h2>
          <div class="grid grid-cols-3 gap-4 my-6">
            <div class="bg-mint-50 rounded-xl p-4">
              <div class="text-2xl font-bold text-mint-600 tabular-nums">{{ correctCount }}/{{ questions.length }}</div>
              <div class="text-xs text-gray-400">正确率</div>
            </div>
            <div class="bg-brand-50 rounded-xl p-4">
              <div class="text-2xl font-bold text-brand-600 tabular-nums">{{ score }}</div>
              <div class="text-xs text-gray-400">得分</div>
            </div>
            <div class="bg-amber-50 rounded-xl p-4">
              <div class="text-2xl font-bold text-amber-600 tabular-nums">+{{ earnedCoins }}</div>
              <div class="text-xs text-gray-400">金币</div>
            </div>
          </div>
          <div class="flex gap-3 justify-center">
            <button @click="startQuiz" class="px-6 py-3 bg-brand-500 text-white rounded-xl font-medium hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98]">
              再来一局
            </button>
            <button @click="resetQuiz" class="px-6 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium hover:bg-gray-50 transition-colors">
              换题库
            </button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="glass-card rounded-2xl p-12 text-center">
          <img :src="rocketIcon" class="icon-empty mx-auto mb-4" alt="" />
          <h3 class="text-lg font-semibold text-gray-600 mb-2">选择题库开始练习</h3>
          <p class="text-sm text-gray-400">左侧选择题库和难度，开始你的知识闯关之旅！</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import client from '@/api/client'
import rocketIcon from '@/assets/icons/star/rocket-svgrepo-com.svg'
import planListIcon from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import happyIcon from '@/assets/icons/lian/emoji-emoticon-happy-svgrepo-com.svg'
import sadIcon from '@/assets/icons/lian/emoji-emoticon-sad-svgrepo-com.svg'
import trophyIcon from '@/assets/icons/blue/trophy-svgrepo-com.svg'

interface QuizOption { key: string; text: string }
interface QuizQuestion {
  id: number; type: string; topic_id: string; difficulty: string;
  content: string; options: QuizOption[]; time_limit: number;
}
interface PracticeTopic {
  id: string; name: string; category: string; question_count: number; difficulties: string[];
}
interface PracticeCategory {
  id: string; name: string; topics: PracticeTopic[];
}

// ===== 题库加载 =====
const categories = ref<PracticeCategory[]>([])
const topicsLoading = ref(false)
const expandedCats = ref<Set<string>>(new Set())

const selectedTopicId = ref('')
const selectedDifficulty = ref('medium')
const questionCount = ref(10)

const allDifficulties = [
  { value: 'easy', label: '🌟 简单' },
  { value: 'medium', label: '⭐ 中等' },
  { value: 'hard', label: '💫 困难' },
]

const availableDifficulties = computed(() => {
  const topic = findTopic(selectedTopicId.value)
  if (!topic || topic.difficulties.length === 0) return allDifficulties
  return allDifficulties.filter(d => topic.difficulties.includes(d.value))
})

function findTopic(id: string): PracticeTopic | undefined {
  for (const cat of categories.value) {
    const t = cat.topics.find(t => t.id === id)
    if (t) return t
  }
}

// ===== 题目 =====
const questionsLoading = ref(false)
const quizActive = ref(false)
const quizFinished = ref(false)
const questions = ref<QuizQuestion[]>([])
const currentIndex = ref(0)
const selectedAnswer = ref('')
const answered = ref(false)
const isCorrect = ref(false)
const correctAnswer = ref('')
const feedbackExplanation = ref('')
const score = ref(0)
const streak = ref(0)
const totalAnswered = ref(0)
const correctCount = ref(0)
const earnedCoins = ref(0)
const timer = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)

const difficultyLabel = computed(() => {
  const d = allDifficulties.find(d => d.value === selectedDifficulty.value)
  return d?.label || ''
})
const difficultyBadgeClass = computed(() => ({
  easy: 'bg-mint-50 text-mint-600',
  medium: 'bg-amber-50 text-amber-600',
  hard: 'bg-rose-50 text-rose-600',
}[selectedDifficulty.value] || 'bg-gray-100 text-gray-600'))

const questionTypeLabel = computed(() => {
  const t = currentQuestion.value?.type
  const map: Record<string, string> = { single_choice: '单选题', multi_choice: '多选题', short_answer: '简答题' }
  return map[t] || '单选题'
})
const questionTypeBadge = computed(() => ({
  single_choice: 'bg-blue-50 text-blue-600',
  multi_choice: 'bg-purple-50 text-purple-600',
  short_answer: 'bg-gray-50 text-gray-600',
}[currentQuestion.value?.type || 'single_choice'] || 'bg-gray-100 text-gray-600'))

const resultIcon = computed(() => {
  const rate = correctCount.value / Math.max(questions.value.length, 1)
  if (rate >= 0.9) return trophyIcon
  if (rate >= 0.7) return happyIcon
  if (rate >= 0.5) return rocketIcon
  return planListIcon
})

// ===== API 调用 =====
async function fetchTopics() {
  topicsLoading.value = true
  try {
    const data = await client.get('/api/v1/practice/categories') as any
    if (Array.isArray(data)) {
      categories.value = data
      // 默认展开第一个分类、选中第一个主题
      if (data.length > 0) {
        expandedCats.value.add(data[0].id)
        if (data[0].topics.length > 0) {
          selectTopic(data[0].topics[0])
        }
      }
    }
  } catch (e) {
    console.error('加载题库列表失败:', e)
  } finally {
    topicsLoading.value = false
  }
}

function toggleCategory(catId: string) {
  if (expandedCats.value.has(catId)) {
    expandedCats.value.delete(catId)
  } else {
    expandedCats.value.add(catId)
  }
}

function selectTopic(topic: PracticeTopic) {
  selectedTopicId.value = topic.id
  // 自动选择该 topic 有的难度
  if (topic.difficulties.length > 0 && !topic.difficulties.includes(selectedDifficulty.value)) {
    selectedDifficulty.value = topic.difficulties[0]
  }
}

async function startQuiz() {
  if (!selectedTopicId.value) return

  questionsLoading.value = true
  resetQuiz()

  try {
    const data = await client.post('/api/v1/practice/questions', {
      topic_id: selectedTopicId.value,
      difficulty: selectedDifficulty.value,
      count: questionCount.value,
    }) as any

    const list = Array.isArray(data) ? data : (data?.questions || [])
    if (list.length === 0) {
      alert('该题库暂无题目，请选择其他题库')
      return
    }
    questions.value = list
    currentIndex.value = 0
    selectedAnswer.value = ''
    answered.value = false
    quizActive.value = true
    quizFinished.value = false
    correctCount.value = 0
    startTimer()
  } catch (e: any) {
    console.error('加载题目失败:', e)
    alert('加载题目失败: ' + (e.message || '请稍后重试'))
  } finally {
    questionsLoading.value = false
  }
}

function resetQuiz() {
  quizActive.value = false
  quizFinished.value = false
  questions.value = []
}

async function submitAnswer(key: string) {
  if (answered.value) return
  selectedAnswer.value = key
  answered.value = true
  stopTimer()

  // 调用后端检查答案
  try {
    const result = await client.post('/api/v1/practice/submit', {
      question_id: currentQuestion.value?.id,
      selected_answer: key,
    }) as any

    isCorrect.value = result.correct
    correctAnswer.value = result.correct_answer
    feedbackExplanation.value = result.explanation || ''
    if (result.correct) {
      score.value += result.score || 100
      streak.value++
      correctCount.value++
      earnedCoins.value += result.coins || 10
      totalAnswered.value++
    } else {
      streak.value = 0
      totalAnswered.value++
    }
  } catch {
    // 后端不可用时的本地回退
    isCorrect.value = key === currentQuestion.value?.options.find(
      o => o.key === key && o.key === correctAnswer.value
    )?.key
    if (isCorrect.value) {
      score.value += 100
      streak.value++
      correctCount.value++
      earnedCoins.value += 10
      totalAnswered.value++
    } else {
      streak.value = 0
      totalAnswered.value++
    }
  }
}

function nextQuestion() {
  if (currentIndex.value + 1 < questions.value.length) {
    currentIndex.value++
    selectedAnswer.value = ''
    answered.value = false
    feedbackExplanation.value = ''
    startTimer()
  } else {
    quizActive.value = false
    quizFinished.value = true
  }
}

function optionClass(key: string) {
  if (!answered.value) return 'border-gray-200 hover:border-brand-300 hover:bg-brand-50/30 cursor-pointer'
  if (key === correctAnswer.value) return 'border-mint-400 bg-mint-50'
  if (key === selectedAnswer.value && key !== correctAnswer.value) return 'border-rose-400 bg-rose-50'
  return 'border-gray-100 bg-gray-50/50 opacity-60'
}

function optionKeyBg(key: string) {
  if (!answered.value) return 'bg-gray-100 text-gray-600'
  if (key === correctAnswer.value) return 'bg-mint-500 text-white'
  if (key === selectedAnswer.value && key !== correctAnswer.value) return 'bg-rose-500 text-white'
  return 'bg-gray-100 text-gray-400'
}

function startTimer() {
  timer.value = currentQuestion.value?.time_limit || 60
  stopTimer()
  timerInterval = setInterval(() => {
    if (timer.value > 0) {
      timer.value--
    } else {
      if (!answered.value) submitAnswer('')
    }
  }, 1000)
}

function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
}

onMounted(() => {
  fetchTopics()
})

onUnmounted(stopTimer)
</script>

<style scoped>
.icon-title {
  width: 1.5em;
  height: 1.5em;
  display: inline-block;
  vertical-align: middle;
}

.icon-empty {
  width: 3em;
  height: 3em;
  display: block;
}

.icon-inline {
  width: 1.2em;
  height: 1.2em;
  display: inline-block;
  vertical-align: middle;
}

.icon-result-lg {
  width: 3em;
  height: 3em;
  display: block;
}
</style>
