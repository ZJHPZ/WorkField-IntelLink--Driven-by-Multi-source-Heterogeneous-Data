<template>
  <div class="glass-card rounded-2xl p-4">
    <h3 class="text-sm font-semibold text-space-800 mb-3 flex items-center gap-1.5"><img :src="iconInsertTable" class="answer-card-icon" alt="" /> 答题卡</h3>

    <!-- 统计 -->
    <div class="grid grid-cols-3 gap-2 mb-4">
      <div class="text-center bg-mint-50 rounded-lg py-2">
        <div class="text-lg font-bold text-mint-600 tabular-nums">{{ answeredCount }}</div>
        <div class="text-[10px] text-gray-400">已答</div>
      </div>
      <div class="text-center bg-amber-50 rounded-lg py-2">
        <div class="text-lg font-bold text-amber-600 tabular-nums">{{ flaggedCount }}</div>
        <div class="text-[10px] text-gray-400">标记</div>
      </div>
      <div class="text-center bg-gray-50 rounded-lg py-2">
        <div class="text-lg font-bold text-gray-500 tabular-nums">{{ unansweredCount }}</div>
        <div class="text-[10px] text-gray-400">未答</div>
      </div>
    </div>

    <!-- 题号网格 -->
    <div class="grid grid-cols-5 gap-2 mb-4">
      <button
        v-for="i in totalQuestions"
        :key="i - 1"
        class="w-full aspect-square rounded-lg text-xs font-bold transition-all"
        :class="numberClass(i - 1)"
        @click="$emit('go', i - 1)"
      >
        {{ i }}
      </button>
    </div>

    <!-- 图例 -->
    <div class="flex items-center gap-3 text-[10px] text-gray-400">
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-mint-500" /> 已答</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-amber-400" /> 标记</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-gray-200" /> 未答</span>
      <span class="flex items-center gap-1"><span class="w-3 h-3 rounded border-2 border-brand-400 bg-white" /> 当前</span>
    </div>

    <!-- 交卷按钮 -->
    <button
      class="w-full mt-4 py-3 bg-rose-500 text-white rounded-xl font-medium text-sm hover:bg-rose-600 transition-all shadow-lg shadow-rose-500/25 active:scale-[0.98]"
      @click="$emit('submit')"
    >
      交卷
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import iconInsertTable from '@/assets/icons/jian/insert-table-svgrepo-com.svg'

const props = defineProps<{
  totalQuestions: number
  currentIndex: number
  answers: Record<number, string>
  flagged: number[]
  answeredCount: number
}>()

defineEmits<{
  go: [index: number]
  submit: []
}>()

const flaggedCount = computed(() => props.flagged.length)

const unansweredCount = computed(() => {
  return props.totalQuestions - new Set([...Object.keys(props.answers).map(Number), ...props.flagged]).size
})

function numberClass(index: number) {
  const isCurrent = index === props.currentIndex
  const isFlagged = props.flagged.includes(index)
  const isAnswered = props.answers[index] !== undefined

  if (isCurrent) return 'ring-2 ring-brand-400 bg-white text-brand-600 font-bold'
  if (isFlagged) return 'bg-amber-100 text-amber-700'
  if (isAnswered) return 'bg-mint-100 text-mint-700'
  return 'bg-gray-100 text-gray-400'
}
</script>

<style scoped>
.answer-card-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
}
</style>
