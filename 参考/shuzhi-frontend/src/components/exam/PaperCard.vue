<template>
  <div
    class="glass-card rounded-2xl p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-2 relative group"
    :class="borderClass"
  >
    <!-- Admin controls -->
    <div v-if="isAdmin" class="absolute top-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
      <button
        class="p-1.5 rounded-lg text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
        title="编辑试卷"
        @click.stop="$emit('edit')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
      </button>
      <button
        class="p-1.5 rounded-lg text-gray-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
        title="删除试卷"
        @click.stop="$emit('delete')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
      </button>
    </div>

    <div class="flex items-start justify-between mb-3" @click="$emit('click')">
      <h3 class="text-base font-semibold text-space-800 flex-1 pr-16">{{ paper.title }}</h3>
      <!-- Publish toggle for admin, status badge for others -->
      <button
        v-if="isAdmin"
        class="ml-2 px-2 py-0.5 rounded-full text-xs font-medium shrink-0 transition-colors cursor-pointer"
        :class="paper.is_active ? 'bg-mint-50 text-mint-600 hover:bg-mint-100' : 'bg-gray-100 text-gray-400 hover:bg-gray-200'"
        @click.stop="$emit('toggle-publish')"
        :title="paper.is_active ? '已发布，点击下架' : '未发布，点击发布'"
      >
        {{ paper.is_active ? '已发布' : '未发布' }}
      </button>
      <span
        v-else
        class="ml-2 px-2 py-0.5 rounded-full text-xs font-medium shrink-0"
        :class="paper.is_active ? 'bg-mint-50 text-mint-600' : 'bg-gray-100 text-gray-400'"
      >{{ paper.is_active ? '进行中' : '已关闭' }}</span>
    </div>

    <div @click="$emit('click')">
      <p class="text-sm text-gray-400 mb-4 line-clamp-2">{{ paper.description || '暂无描述' }}</p>

      <div class="grid grid-cols-2 gap-2 mb-4">
        <div class="flex items-center gap-1.5 text-xs text-gray-500">
          <img :src="iconPlanList" class="paper-icon" alt="" />
          <span>{{ paper.total_questions }} 题</span>
        </div>
        <div class="flex items-center gap-1.5 text-xs text-gray-500">
          <span>⏱️</span>
          <span>{{ paper.time_limit }} 分钟</span>
        </div>
        <div class="flex items-center gap-1.5 text-xs text-gray-500">
          <img :src="iconTrophy" class="paper-icon" alt="" />
          <span>及格线 {{ paper.passing_score }}%</span>
        </div>
        <div class="flex items-center gap-1.5 text-xs text-gray-500">
          <img :src="iconPieChart" class="paper-icon" alt="" />
          <span>
            <template v-if="paper.difficulty_mix.easy">{{ paper.difficulty_mix.easy }}% 简</template>
            <template v-if="paper.difficulty_mix.medium"> {{ paper.difficulty_mix.medium }}% 中</template>
            <template v-if="paper.difficulty_mix.hard"> {{ paper.difficulty_mix.hard }}% 难</template>
          </span>
        </div>
      </div>

      <div v-if="paper.topic_ids.length > 0" class="flex flex-wrap gap-1 mb-4">
        <span
          v-for="topic in paper.topic_ids.slice(0, 4)"
          :key="topic"
          class="px-2 py-0.5 rounded-md text-xs bg-brand-50 text-brand-600"
        >{{ topic }}</span>
        <span v-if="paper.topic_ids.length > 4" class="text-xs text-gray-400">+{{ paper.topic_ids.length - 4 }}</span>
      </div>
    </div>

    <button
      class="w-full py-2.5 rounded-xl font-medium text-sm transition-all active:scale-[0.98]"
      :class="paper.is_active ? 'bg-brand-500 text-white hover:bg-brand-600 shadow-lg shadow-brand-500/25' : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
      :disabled="!paper.is_active"
      @click.stop="$emit('start')"
    >
      {{ paper.is_active ? '开始考试' : '暂不可用' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ExamPaper } from '@/stores/exam'
import iconPlanList from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import iconTrophy from '@/assets/icons/blue/trophy-svgrepo-com.svg'
import iconPieChart from '@/assets/icons/jian/pie-chart-svgrepo-com.svg'

const props = defineProps<{
  paper: ExamPaper
  isHistory?: boolean
  isAdmin?: boolean
}>()

defineEmits<{
  click: []
  start: []
  edit: []
  delete: []
  'toggle-publish': []
}>()

const borderClass = computed(() =>
  props.isHistory ? 'border-gray-100' : 'border-transparent hover:border-brand-200'
)
</script>

<style scoped>
.paper-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
  flex-shrink: 0;
}
</style>
