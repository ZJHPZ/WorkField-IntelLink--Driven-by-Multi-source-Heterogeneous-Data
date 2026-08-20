<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-start justify-center bg-black/50 overflow-y-auto py-8" @click.self="$emit('close')">
      <div class="bg-white rounded-2xl p-6 w-full max-w-2xl mx-4 shadow-2xl animate-scale-in">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-space-800">
            {{ isEdit ? '编辑试卷' : '创建试卷' }}
          </h3>
          <button class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100" @click="$emit('close')">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="space-y-5 max-h-[70vh] overflow-y-auto pr-1">
          <!-- Title -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">试卷标题 *</label>
            <input
              v-model="form.title"
              class="w-full px-4 py-2.5 rounded-xl border-2 border-gray-200 text-sm focus:border-brand-300 focus:outline-none transition-colors"
              placeholder="例如：大数据期末综合测试"
              maxlength="100"
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">试卷描述</label>
            <textarea
              v-model="form.description"
              class="w-full px-4 py-2.5 rounded-xl border-2 border-gray-200 text-sm focus:border-brand-300 focus:outline-none transition-colors resize-none"
              rows="3"
              placeholder="简要描述考试范围和目标..."
              maxlength="500"
            />
          </div>

          <!-- Topic selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              选题范围
              <span class="text-gray-400 font-normal">（不选则从全部题库抽题）</span>
            </label>
            <div v-if="topicOptions.length === 0" class="text-xs text-gray-400 py-2">加载题库主题中...</div>
            <div v-else class="grid grid-cols-2 gap-1.5 max-h-40 overflow-y-auto">
              <label
                v-for="t in topicOptions"
                :key="t.id"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors text-xs"
                :class="form.topic_ids.includes(t.id) ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-gray-100 text-gray-500 hover:border-gray-200'"
              >
                <input
                  type="checkbox"
                  :checked="form.topic_ids.includes(t.id)"
                  class="sr-only"
                  @change="toggleTopic(t.id)"
                />
                <span class="font-medium truncate">{{ t.name }}</span>
                <span class="text-gray-300 ml-auto shrink-0">{{ t.question_count }}题</span>
              </label>
            </div>
          </div>

          <!-- Difficulty mix -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-3">难度分布（%）</label>
            <div class="space-y-3">
              <div v-for="d in difficulties" :key="d.key" class="flex items-center gap-3">
                <span class="text-xs font-medium w-10 shrink-0" :class="d.color">{{ d.label }}</span>
                <input
                  type="range"
                  :min="0"
                  :max="100"
                  :value="form.difficulty_mix[d.key] || 0"
                  class="flex-1 h-2 rounded-full appearance-none cursor-pointer"
                  :class="d.sliderClass"
                  :style="{ background: d.trackBg }"
                  @input="onDifficultyChange(d.key, $event)"
                />
                <span class="text-xs font-bold w-12 text-right tabular-nums text-gray-600">{{ form.difficulty_mix[d.key] || 0 }}%</span>
              </div>
              <p v-if="diffSum !== 100" class="text-xs text-rose-500">总和必须为 100%，当前 {{ diffSum }}%</p>
            </div>
          </div>

          <!-- Config grid -->
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">题目数量</label>
              <select v-model.number="form.total_questions" class="w-full px-3 py-2.5 rounded-xl border-2 border-gray-200 text-sm focus:border-brand-300 focus:outline-none">
                <option v-for="n in [5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]" :key="n" :value="n">{{ n }} 题</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">考试时长（分钟）</label>
              <select v-model.number="form.time_limit" class="w-full px-3 py-2.5 rounded-xl border-2 border-gray-200 text-sm focus:border-brand-300 focus:outline-none">
                <option v-for="n in [10, 15, 20, 30, 45, 60, 90, 120, 150, 180]" :key="n" :value="n">{{ n }} 分钟</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">及格线（%）</label>
              <select v-model.number="form.passing_score" class="w-full px-3 py-2.5 rounded-xl border-2 border-gray-200 text-sm focus:border-brand-300 focus:outline-none">
                <option v-for="n in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]" :key="n" :value="n">{{ n }}%</option>
              </select>
            </div>
          </div>

          <!-- Publish toggle -->
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50">
            <div>
              <p class="text-sm font-medium text-gray-700">发布试卷</p>
              <p class="text-xs text-gray-400">发布后学生即可看到并开始考试</p>
            </div>
            <button
              type="button"
              class="relative w-12 h-7 rounded-full transition-colors duration-200"
              :class="form.is_active ? 'bg-mint-500' : 'bg-gray-300'"
              @click="form.is_active = !form.is_active"
            >
              <span class="absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white shadow transition-transform duration-200"
                :class="form.is_active ? 'translate-x-5' : ''" />
            </button>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 mt-6 pt-4 border-t border-gray-100">
          <button
            class="flex-1 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 transition-colors"
            @click="$emit('close')"
          >取消</button>
          <button
            class="flex-1 py-3 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98] disabled:opacity-50"
            :disabled="!valid || saving"
            @click="handleSave"
          >
            <span v-if="saving" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
            {{ saving ? '保存中...' : (isEdit ? '保存修改' : '创建试卷') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useExamStore } from '@/stores/exam'

const props = defineProps<{
  paper?: any  // passed when editing
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const examStore = useExamStore()
const saving = ref(false)
const topicOptions = computed(() => examStore.topicOptions)

const isEdit = computed(() => !!props.paper)

const difficulties = [
  { key: 'easy', label: '简单', color: 'text-mint-600', sliderClass: 'accent-mint-500', trackBg: 'linear-gradient(to right, #10b981 var(--p), #e5e7eb var(--p))' },
  { key: 'medium', label: '中等', color: 'text-amber-600', sliderClass: 'accent-amber-500', trackBg: 'linear-gradient(to right, #f59e0b var(--p), #e5e7eb var(--p))' },
  { key: 'hard', label: '困难', color: 'text-rose-600', sliderClass: 'accent-rose-500', trackBg: 'linear-gradient(to right, #ef4444 var(--p), #e5e7eb var(--p))' },
]

function defaultForm() {
  return {
    title: '',
    description: '' as string | null,
    topic_ids: [] as string[],
    difficulty_mix: { easy: 40, medium: 40, hard: 20 } as Record<string, number>,
    total_questions: 20,
    time_limit: 30,
    passing_score: 60,
    is_active: false,
  }
}

const form = reactive(defaultForm())

const diffSum = computed(() => {
  return (form.difficulty_mix.easy || 0) + (form.difficulty_mix.medium || 0) + (form.difficulty_mix.hard || 0)
})

const valid = computed(() => {
  return form.title.trim().length > 0 && diffSum.value === 100 && form.total_questions >= 5
})

function toggleTopic(id: string) {
  const idx = form.topic_ids.indexOf(id)
  if (idx >= 0) {
    form.topic_ids.splice(idx, 1)
  } else {
    form.topic_ids.push(id)
  }
}

function onDifficultyChange(key: string, event: Event) {
  const target = event.target as HTMLInputElement
  const newVal = parseInt(target.value)
  const oldVal = form.difficulty_mix[key] || 0
  const delta = newVal - oldVal

  if (delta === 0) return

  // Adjust other sliders to keep sum at 100
  const others = ['easy', 'medium', 'hard'].filter(k => k !== key)
  let remaining = -delta

  // Distribute delta across other two
  for (let i = 0; i < others.length; i++) {
    const k = others[i]
    const current = form.difficulty_mix[k] || 0
    if (i === others.length - 1) {
      // Last one takes the remainder
      form.difficulty_mix[k] = Math.max(0, Math.min(100, current + remaining))
    } else {
      const share = Math.round(remaining / (others.length - i))
      form.difficulty_mix[k] = Math.max(0, Math.min(100, current + share))
      remaining -= (form.difficulty_mix[k] - current)
    }
  }
  form.difficulty_mix[key] = newVal
}

// Load topics on mount
onMounted(() => {
  examStore.fetchTopicOptions()
})

// Populate form when editing
watch(() => props.paper, (paper) => {
  if (paper) {
    form.title = paper.title || ''
    form.description = paper.description || ''
    form.topic_ids = [...(paper.topic_ids || [])]
    form.difficulty_mix = { ...{ easy: 30, medium: 50, hard: 20 }, ...(paper.difficulty_mix || {}) }
    form.total_questions = paper.total_questions || 20
    form.time_limit = paper.time_limit || 30
    form.passing_score = paper.passing_score || 60
    form.is_active = paper.is_active ?? false
  }
}, { immediate: true })

async function handleSave() {
  if (!valid.value) return
  saving.value = true
  try {
    const data: Record<string, any> = {
      title: form.title.trim(),
      description: (form.description || '').trim() || null,
      topic_ids: form.topic_ids,
      difficulty_mix: { ...form.difficulty_mix },
      total_questions: form.total_questions,
      time_limit: form.time_limit,
      passing_score: form.passing_score,
      is_active: form.is_active,
    }
    if (isEdit.value && props.paper) {
      await examStore.updatePaper(props.paper.id, data as any)
    } else {
      await examStore.createPaper(data as any)
    }
    emit('saved')
    emit('close')
  } catch (e: any) {
    alert('保存失败: ' + (e.message || '请稍后重试'))
  } finally {
    saving.value = false
  }
}
</script>
