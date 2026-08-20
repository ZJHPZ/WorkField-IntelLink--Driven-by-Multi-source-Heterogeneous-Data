<template>
  <div v-if="question" class="animate-fade-in-up">
    <!-- 题目标题栏 -->
    <div class="flex items-center gap-2 mb-4 flex-wrap">
      <span class="text-sm font-semibold text-space-800">第 {{ question.index + 1 }} 题</span>
      <span
        class="px-2 py-0.5 rounded-full text-xs font-medium"
        :class="difficultyBadgeClass"
      >{{ difficultyLabel }}</span>
      <span
        class="px-2 py-0.5 rounded-full text-xs font-medium"
        :class="typeBadgeClass"
      >{{ typeLabel }}</span>
      <span class="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-500">{{ question.topic_id }}</span>
      <button
        class="ml-auto px-3 py-1 rounded-lg text-xs border transition-colors"
        :class="isFlagged ? 'border-amber-300 bg-amber-50 text-amber-600' : 'border-gray-200 text-gray-400 hover:border-amber-300 hover:text-amber-500'"
        @click="$emit('toggle-flag', question.index)"
      >
        <img :src="iconSetUp" class="flag-icon" :class="isFlagged ? '' : 'opacity-50'" alt="" /> {{ isFlagged ? '已标记' : '标记' }}
      </button>
    </div>

    <!-- 题目内容 -->
    <div class="mb-6">
      <p class="text-base text-space-800 leading-relaxed">{{ question.content }}</p>
    </div>

    <!-- 选项 -->
    <div v-if="question.options.length > 0" class="space-y-3">
      <button
        v-for="option in question.options"
        :key="option.key"
        class="w-full text-left p-4 rounded-xl border-2 transition-all duration-200"
        :class="optionClass(option.key)"
        :disabled="disabled"
        @click="$emit('select', question.index, option.key)"
      >
        <div class="flex items-center gap-3">
          <span
            class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 transition-colors"
            :class="optionKeyBg(option.key)"
          >{{ option.key }}</span>
          <span class="text-sm">{{ option.text }}</span>
          <span v-if="showResult && option.key === correctAnswer" class="ml-auto text-mint-500 font-medium text-sm">✓ 正确</span>
          <span v-else-if="showResult && option.key === selectedAnswer && option.key !== correctAnswer" class="ml-auto text-rose-500 font-medium text-sm">✗</span>
        </div>
      </button>
    </div>

    <!-- 简答题输入 -->
    <div v-else>
      <textarea
        :value="selectedAnswer"
        class="w-full p-4 rounded-xl border-2 border-gray-200 text-sm resize-none focus:border-brand-300 focus:outline-none transition-colors"
        rows="4"
        placeholder="请输入你的答案..."
        :disabled="disabled"
        @input="$emit('select', question.index, ($event.target as HTMLTextAreaElement).value)"
      />
    </div>

    <!-- 答题反馈 -->
    <div v-if="showResult && result" class="mt-4 p-4 rounded-xl animate-fade-in-up"
      :class="result.is_correct ? 'bg-mint-50 border border-mint-200' : 'bg-rose-50 border border-rose-200'">
      <p class="text-sm font-semibold mb-1" :class="result.is_correct ? 'text-mint-700' : 'text-rose-700'">
        {{ result.is_correct ? '回答正确！' : '回答错误' }}
      </p>
      <p class="text-xs text-gray-500">正确答案：{{ result.correct_answer }}</p>
      <p v-if="result.explanation" class="text-xs text-gray-600 mt-1">{{ result.explanation }}</p>
    </div>
  </div>

  <div v-else class="text-center py-12 text-gray-400">
    <img :src="iconInsertTable" class="empty-icon" alt="" />
    <p>暂无题目</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ExamQuestion, AnswerResult } from '@/stores/exam'
import iconSetUp from '@/assets/icons/jian/set-up-svgrepo-com.svg'
import iconInsertTable from '@/assets/icons/jian/insert-table-svgrepo-com.svg'

const props = defineProps<{
  question: ExamQuestion | null
  selectedAnswer: string
  result: AnswerResult | null
  isFlagged: boolean
  disabled: boolean
  showResult: boolean
  correctAnswer: string
}>()

defineEmits<{
  select: [index: number, answer: string]
  'toggle-flag': [index: number]
}>()

const difficultyLabel = computed(() => {
  const map: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' }
  return map[props.question?.difficulty || ''] || '中等'
})

const difficultyBadgeClass = computed(() => {
  const map: Record<string, string> = {
    easy: 'bg-mint-50 text-mint-600',
    medium: 'bg-amber-50 text-amber-600',
    hard: 'bg-rose-50 text-rose-600',
  }
  return map[props.question?.difficulty || ''] || 'bg-gray-100 text-gray-600'
})

const typeLabel = computed(() => {
  const map: Record<string, string> = { single_choice: '单选', multi_choice: '多选', short_answer: '简答' }
  return map[props.question?.type || ''] || '单选'
})

const typeBadgeClass = computed(() => {
  const map: Record<string, string> = {
    single_choice: 'bg-blue-50 text-blue-600',
    multi_choice: 'bg-purple-50 text-purple-600',
    short_answer: 'bg-gray-50 text-gray-600',
  }
  return map[props.question?.type || ''] || 'bg-gray-100 text-gray-600'
})

function optionClass(key: string) {
  if (!props.showResult) {
    if (props.selectedAnswer === key) return 'border-brand-400 bg-brand-50'
    return 'border-gray-200 hover:border-brand-300 hover:bg-brand-50/30 cursor-pointer'
  }
  if (key === props.correctAnswer) return 'border-mint-400 bg-mint-50'
  if (key === props.selectedAnswer && key !== props.correctAnswer) return 'border-rose-400 bg-rose-50'
  return 'border-gray-100 bg-gray-50/50 opacity-60'
}

function optionKeyBg(key: string) {
  if (!props.showResult) {
    if (props.selectedAnswer === key) return 'bg-brand-500 text-white'
    return 'bg-gray-100 text-gray-600'
  }
  if (key === props.correctAnswer) return 'bg-mint-500 text-white'
  if (key === props.selectedAnswer && key !== props.correctAnswer) return 'bg-rose-500 text-white'
  return 'bg-gray-100 text-gray-400'
}
</script>

<style scoped>
.flag-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
  flex-shrink: 0;
}

.empty-icon {
  width: 3em;
  height: 3em;
  display: block;
  margin: 0 auto 0.75rem;
  opacity: 0.4;
}
</style>
