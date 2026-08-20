<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Back button -->
    <button
      class="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-600 transition-colors"
      @click="router.push('/exam')"
    >
      <span>←</span> 返回考试中心
    </button>

    <!-- Loading -->
    <div v-if="examStore.resultLoading" class="text-center py-12">
      <div class="inline-block w-10 h-10 border-3 border-brand-200 border-t-brand-500 rounded-full animate-spin mb-3" />
      <p class="text-sm text-gray-400">加载考试结果...</p>
    </div>

    <template v-else-if="result">
      <!-- Result header -->
      <div
        class="glass-card rounded-2xl p-8 text-center"
        :class="result.is_passed ? 'border-2 border-mint-200' : 'border-2 border-rose-200'"
      >
        <div class="text-6xl mb-4">{{ result.is_passed ? '🎉' : '' }}<img v-if="!result.is_passed" :src="sadIcon" class="icon-result inline-block" alt="" /></div>
        <h2 class="text-2xl font-bold text-space-800 mb-2">
          {{ result.is_passed ? '恭喜通过考试！' : '很遗憾，未通过' }}
        </h2>
        <p class="text-sm text-gray-400 mb-6">{{ result.paper_title }}</p>

        <!-- Score ring -->
        <div class="flex justify-center mb-6">
          <div class="relative w-32 h-32">
            <svg class="w-32 h-32 -rotate-90" viewBox="0 0 128 128">
              <circle cx="64" cy="64" r="56" stroke="currentColor" stroke-width="8" fill="none" class="text-gray-100" />
              <circle
                cx="64" cy="64" r="56"
                stroke="currentColor" stroke-width="8" fill="none"
                stroke-linecap="round"
                :class="result.is_passed ? 'text-mint-500' : 'text-rose-500'"
                :stroke-dasharray="2 * Math.PI * 56"
                :stroke-dashoffset="2 * Math.PI * 56 * (1 - result.accuracy / 100)"
                class="transition-all duration-1000"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-3xl font-bold tabular-nums" :class="result.is_passed ? 'text-mint-600' : 'text-rose-600'">
                {{ result.accuracy }}%
              </span>
              <span class="text-xs text-gray-400">正确率</span>
            </div>
          </div>
        </div>

        <!-- Stats grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-mint-50 rounded-xl p-4">
            <div class="text-xl font-bold text-mint-600 tabular-nums">{{ result.total_score }}</div>
            <div class="text-xs text-gray-400">总分</div>
          </div>
          <div class="bg-brand-50 rounded-xl p-4">
            <div class="text-xl font-bold text-brand-600 tabular-nums">{{ result.correct_count }}/{{ result.total_questions }}</div>
            <div class="text-xs text-gray-400">正确题数</div>
          </div>
          <div class="bg-amber-50 rounded-xl p-4">
            <div class="text-xl font-bold text-amber-600 tabular-nums">{{ formatTime(result.time_spent) }}</div>
            <div class="text-xs text-gray-400">用时</div>
          </div>
          <div class="rounded-xl p-4" :class="result.is_passed ? 'bg-mint-50' : 'bg-rose-50'">
            <div class="text-xl font-bold tabular-nums" :class="result.is_passed ? 'text-mint-600' : 'text-rose-600'">
              {{ result.is_passed ? '通过' : '未通过' }}
            </div>
            <div class="text-xs text-gray-400">及格线 {{ result.passing_score }}%</div>
          </div>
        </div>
      </div>

      <!-- Topic breakdown -->
      <div v-if="result.topic_breakdown.length > 0" class="glass-card rounded-2xl p-5">
        <h3 class="text-base font-semibold text-space-800 mb-4"><img :src="pieChartIcon" class="icon-title" alt="" /> 知识点分析</h3>
        <div class="space-y-3">
          <div v-for="tb in result.topic_breakdown" :key="tb.topic_id" class="flex items-center gap-3">
            <span class="text-sm font-medium text-space-800 w-24 truncate">{{ tb.topic_id }}</span>
            <div class="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-700"
                :class="tb.rate >= 60 ? 'bg-mint-500' : 'bg-rose-400'"
                :style="{ width: tb.rate + '%' }"
              />
            </div>
            <span class="text-xs text-gray-500 w-20 text-right tabular-nums">
              {{ tb.correct }}/{{ tb.total }} ({{ tb.rate }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- Answer review -->
      <div class="glass-card rounded-2xl p-5">
        <h3 class="text-base font-semibold text-space-800 mb-4"><img :src="planListIcon" class="icon-title" alt="" /> 答题详情</h3>
        <div class="space-y-3">
          <div
            v-for="answer in result.answers"
            :key="answer.question_index"
            class="rounded-xl border p-4 transition-colors"
            :class="answer.is_correct ? 'border-mint-100 bg-mint-50/30' : 'border-rose-100 bg-rose-50/30'"
          >
            <div class="flex items-start gap-3">
              <span
                class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                :class="answer.is_correct ? 'bg-mint-500 text-white' : 'bg-rose-500 text-white'"
              >{{ answer.is_correct ? '✓' : '✗' }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1 flex-wrap">
                  <span class="text-sm font-semibold text-space-800">第 {{ answer.question_index + 1 }} 题</span>
                  <span class="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-500">{{ answer.topic_id }}</span>
                  <span class="px-2 py-0.5 rounded-full text-xs" :class="answer.difficulty === 'easy' ? 'bg-mint-50 text-mint-600' : answer.difficulty === 'hard' ? 'bg-rose-50 text-rose-600' : 'bg-amber-50 text-amber-600'">
                    {{ { easy: '简单', medium: '中等', hard: '困难' }[answer.difficulty] || answer.difficulty }}
                  </span>
                </div>
                <p class="text-sm text-space-800 mb-2">{{ answer.content }}</p>
                <div class="text-xs space-y-1">
                  <p v-if="answer.user_answer">
                    <span class="text-gray-400">你的答案：</span>
                    <span :class="answer.is_correct ? 'text-mint-600 font-medium' : 'text-rose-600 font-medium'">{{ answer.user_answer }}</span>
                  </p>
                  <p v-else class="text-amber-500">未作答</p>
                  <p v-if="!answer.is_correct">
                    <span class="text-gray-400">正确答案：</span>
                    <span class="text-mint-600 font-medium">{{ answer.correct_answer }}</span>
                  </p>
                  <p v-if="answer.explanation" class="text-gray-500 mt-1">{{ answer.explanation }}</p>
                </div>
              </div>
              <span class="text-xs font-bold shrink-0" :class="answer.is_correct ? 'text-mint-600' : 'text-rose-500'">
                +{{ answer.score }}
              </span>
            </div>
          </div>
        </div>

        <!-- 错题本入口 -->
        <div class="mt-6 text-center">
          <router-link
            to="/wrong-book"
            class="inline-flex items-center gap-2 px-6 py-3 rounded-2xl border-2 border-amber-300 bg-amber-50 text-amber-700 font-bold hover:bg-amber-100 transition-colors"
          >
            <img :src="brushIcon" class="icon-btn" alt="" /> 查看错题本
          </router-link>
        </div>
      </div>
    </template>

    <!-- Not found -->
    <div v-else class="glass-card rounded-2xl p-12 text-center">
      <img :src="magnifierIcon" class="icon-empty mx-auto mb-4" alt="" />
      <h3 class="text-lg font-semibold text-gray-600 mb-2">未找到考试结果</h3>
      <p class="text-sm text-gray-400">考试结果可能已被清除或链接无效</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import sadIcon from '@/assets/icons/lian/emoji-emoticon-sad-svgrepo-com.svg'
import pieChartIcon from '@/assets/icons/jian/pie-chart-svgrepo-com.svg'
import planListIcon from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import brushIcon from '@/assets/icons/blue/brush-svgrepo-com.svg'
import magnifierIcon from '@/assets/icons/blue/magnifier-svgrepo-com.svg'

const router = useRouter()
const route = useRoute()
const examStore = useExamStore()

const result = computed(() => examStore.result)

onMounted(async () => {
  const sessionId = route.params.sessionId as string
  if (sessionId) {
    await examStore.fetchResult(sessionId)
  }
})

function formatTime(seconds: number): string {
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  return `${min}分${sec}秒`
}
</script>

<style scoped>
.icon-title {
  width: 1.5em;
  height: 1.5em;
  display: inline-block;
  vertical-align: middle;
}

.icon-btn {
  width: 1em;
  height: 1em;
  display: inline-block;
  vertical-align: middle;
}

.icon-empty {
  width: 3em;
  height: 3em;
  display: block;
}

.icon-result {
  width: 1em;
  height: 1em;
  vertical-align: middle;
}
</style>
