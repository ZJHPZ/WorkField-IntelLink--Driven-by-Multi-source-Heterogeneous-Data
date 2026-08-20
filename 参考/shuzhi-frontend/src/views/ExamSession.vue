<template>
  <div class="flex-1 flex flex-col" style="background-color: var(--bg-primary);">
    <!-- Header bar -->
    <header class="px-4 py-3 flex items-center gap-4 shrink-0 border-b" style="border-color: var(--sidebar-border);">
      <button
        class="p-2 rounded-lg transition-colors hover:bg-gray-100"
        style="color: var(--text-secondary);"
        @click="confirmExit"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <div class="flex-1">
        <h2 class="text-sm font-semibold truncate" style="color: var(--text-primary);">{{ examStore.session?.paper_title }}</h2>
      </div>
      <div class="flex items-center gap-4">
        <!-- Progress -->
        <div class="hidden sm:flex items-center gap-2">
          <div class="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-brand-500 rounded-full transition-all duration-500"
              :style="{ width: examStore.progressPercent + '%' }"
            />
          </div>
          <span class="text-xs text-gray-400">{{ examStore.answeredCount }}/{{ examStore.session?.total_questions }}</span>
        </div>
        <!-- Timer -->
        <div
          class="px-3 py-1.5 rounded-lg text-sm font-bold tabular-nums font-mono"
          :class="timerClass"
        ><img :src="alarmClockIcon" class="icon-timer" alt="" /> {{ timerDisplay }}</div>
      </div>
    </header>

    <!-- Main exam area -->
    <div v-if="examStore.sessionLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="inline-block w-10 h-10 border-3 border-brand-200 border-t-brand-500 rounded-full animate-spin mb-3" />
        <p class="text-sm text-gray-400">加载试卷...</p>
      </div>
    </div>

    <div v-else-if="examStore.sessionLoading === false && !examStore.session" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-sm text-gray-400 mb-3">试卷加载失败</p>
        <button class="px-4 py-2 text-sm text-brand-500 border border-brand-200 rounded-lg hover:bg-brand-50 transition-colors" @click="router.push('/exam')">返回考试中心</button>
      </div>
    </div>

    <div v-else-if="examStore.session" class="flex-1 flex overflow-hidden">
      <!-- Question area -->
      <div class="flex-1 overflow-y-auto p-4 md:p-6">
        <QuestionViewer
          :question="examStore.currentQuestion"
          :selected-answer="examStore.currentQuestion ? examStore.answers[examStore.currentQuestion.index] || '' : ''"
          :result="examStore.currentQuestion ? examStore.answerResults[examStore.currentQuestion.index] || null : null"
          :is-flagged="examStore.currentQuestion ? flaggedSet.has(examStore.currentQuestion.index) : false"
          :disabled="examStore.examStatus !== 'in_progress'"
          :show-result="false"
          correct-answer=""
          @select="examStore.selectAnswer"
          @toggle-flag="toggleFlag"
        />

        <!-- Navigation -->
        <div class="flex items-center justify-between mt-6 pt-4 border-t" style="border-color: var(--sidebar-border);">
          <button
            class="px-4 py-2 border rounded-lg text-sm font-medium transition-colors"
            :class="examStore.currentIndex > 0 ? 'border-gray-200 text-gray-600 hover:bg-gray-50' : 'border-gray-100 text-gray-300 cursor-not-allowed'"
            :disabled="examStore.currentIndex <= 0"
            @click="examStore.goToQuestion(examStore.currentIndex - 1)"
          >← 上一题</button>

          <span class="text-xs text-gray-400">
            {{ examStore.currentIndex + 1 }} / {{ examStore.session?.total_questions }}
          </span>

          <button
            v-if="examStore.currentIndex < (examStore.session?.total_questions || 0) - 1"
            class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            @click="examStore.goToQuestion(examStore.currentIndex + 1)"
          >下一题 →</button>

          <button
            v-else
            class="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98]"
            @click="showSubmitModal = true"
          >交卷</button>
        </div>
      </div>

      <!-- Answer card sidebar -->
      <aside class="hidden lg:block w-64 p-4 border-l overflow-y-auto shrink-0" style="border-color: var(--sidebar-border);">
        <AnswerCard
          :total-questions="examStore.session?.total_questions || 0"
          :current-index="examStore.currentIndex"
          :answers="examStore.answers"
          :flagged="flaggedList"
          :answered-count="examStore.answeredCount"
          @go="examStore.goToQuestion"
          @submit="showSubmitModal = true"
        />
      </aside>
    </div>

    <!-- Mobile answer sheet (bottom drawer) -->
    <div v-if="examStore.session" class="lg:hidden border-t px-4 py-3 shrink-0" style="border-color: var(--sidebar-border);">
      <div class="flex items-center gap-2 overflow-x-auto pb-1">
        <button
          v-for="i in examStore.session.total_questions"
          :key="i - 1"
          class="w-8 h-8 rounded-lg text-xs font-bold shrink-0 transition-all"
          :class="mobileNumberClass(i - 1)"
          @click="examStore.goToQuestion(i - 1)"
        >{{ i }}</button>
      </div>
      <button
        class="w-full mt-2 py-2.5 bg-rose-500 text-white rounded-xl text-sm font-medium active:scale-[0.98] transition-all"
        @click="showSubmitModal = true"
      >交卷 (已答 {{ examStore.answeredCount }}/{{ examStore.session?.total_questions }})</button>
    </div>

    <!-- Submit confirm modal -->
    <Teleport to="body">
      <div
        v-if="showSubmitModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showSubmitModal = false"
      >
        <div class="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl animate-scale-in">
          <h3 class="text-lg font-semibold text-space-800 mb-2">确认交卷</h3>
          <div class="text-sm text-gray-500 space-y-2 mb-4">
            <p>已答 <strong class="text-gray-700">{{ examStore.answeredCount }}</strong> / {{ examStore.session?.total_questions }} 题</p>
            <p v-if="unansweredCount > 0" class="text-rose-500">⚠️ 还有 {{ unansweredCount }} 题未作答</p>
            <p v-else class="text-mint-500">✅ 所有题目已作答</p>
          </div>
          <div class="flex gap-3">
            <button
              class="flex-1 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 transition-colors"
              @click="showSubmitModal = false"
            >继续检查</button>
            <button
              class="flex-1 py-3 bg-rose-500 text-white rounded-xl font-medium text-sm hover:bg-rose-600 transition-all shadow-lg shadow-rose-500/25 active:scale-[0.98]"
              :disabled="submitting"
              @click="handleSubmit"
            >
              <span v-if="submitting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
              {{ submitting ? '提交中...' : '确认交卷' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Exit confirm modal -->
      <div
        v-if="showExitModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showExitModal = false"
      >
        <div class="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl animate-scale-in">
          <h3 class="text-lg font-semibold text-space-800 mb-2">退出考试</h3>
          <p class="text-sm text-gray-500 mb-4">退出后考试进度将保留，你可以稍后继续。确定要退出吗？</p>
          <div class="flex gap-3">
            <button
              class="flex-1 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 transition-colors"
              @click="showExitModal = false"
            >取消</button>
            <button
              class="flex-1 py-3 bg-gray-500 text-white rounded-xl font-medium text-sm hover:bg-gray-600 transition-all active:scale-[0.98]"
              @click="router.push('/exam')"
            >退出考试</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import QuestionViewer from '@/components/exam/QuestionViewer.vue'
import AnswerCard from '@/components/exam/AnswerCard.vue'
import alarmClockIcon from '@/assets/icons/blue/alarm-clock-svgrepo-com.svg'

const router = useRouter()
const route = useRoute()
const examStore = useExamStore()

const showSubmitModal = ref(false)
const showExitModal = ref(false)
const submitting = ref(false)
const flaggedList = ref<number[]>([])

const flaggedSet = computed(() => new Set(flaggedList.value))

const unansweredCount = computed(() => {
  if (!examStore.session) return 0
  return examStore.session.total_questions - examStore.answeredCount
})

const timerDisplay = computed(() => {
  const remaining = examStore.timeRemaining
  const min = Math.floor(remaining / 60)
  const sec = remaining % 60
  return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
})

const timerClass = computed(() => {
  const remaining = examStore.timeRemaining
  if (remaining < 60) return 'bg-rose-50 text-rose-600 animate-pulse'
  if (remaining < 300) return 'bg-amber-50 text-amber-600'
  return 'bg-gray-100 text-gray-600'
})

function toggleFlag(index: number) {
  const pos = flaggedList.value.indexOf(index)
  if (pos >= 0) {
    flaggedList.value.splice(pos, 1)
  } else {
    flaggedList.value.push(index)
  }
}

function mobileNumberClass(index: number) {
  const isCurrent = index === examStore.currentIndex
  const isFlagged = flaggedList.value.includes(index)
  const isAnswered = examStore.answers[index] !== undefined

  if (isCurrent) return 'ring-2 ring-brand-400 bg-white text-brand-600'
  if (isFlagged) return 'bg-amber-100 text-amber-700'
  if (isAnswered) return 'bg-mint-100 text-mint-700'
  return 'bg-gray-100 text-gray-400'
}

async function handleSubmit() {
  submitting.value = true
  try {
    await examStore.completeExam()
    showSubmitModal.value = false
    router.replace(`/exam/${examStore.session?.session_id}/result`)
  } catch (e: any) {
    alert('交卷失败: ' + (e.message || '请稍后重试'))
  } finally {
    submitting.value = false
  }
}

function confirmExit() {
  showExitModal.value = true
}

onMounted(async () => {
  const sessionId = route.params.sessionId as string
  if (!sessionId) return

  // 如果 store 中已加载同一会话（自测流程已预加载），跳过重新拉取
  if (examStore.session?.session_id === sessionId) return

  try {
    await examStore.resumeSession(sessionId)
  } catch {
    router.replace('/exam')
  }
})

onUnmounted(() => {
  // Don't reset on full page navigation, keep state for result viewing
})
</script>

<style scoped>
.icon-timer {
  width: 1em;
  height: 1em;
  display: inline-block;
  vertical-align: middle;
}
</style>
