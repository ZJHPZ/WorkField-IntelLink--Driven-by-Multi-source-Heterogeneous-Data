<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-card">
        <div class="modal-header">
          <h3>错题自测</h3>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>

        <div class="modal-body">
          <!-- 选题范围 -->
          <div class="config-section">
            <label class="config-label">选题范围（知识点）</label>
            <div class="topic-grid">
              <label
                v-for="topic in topics"
                :key="topic.topic_id"
                class="topic-chip"
                :class="{ checked: selectedTopics.includes(topic.topic_id) }"
              >
                <input
                  type="checkbox"
                  :value="topic.topic_id"
                  v-model="selectedTopics"
                  class="topic-checkbox"
                />
                <span class="topic-name">{{ topic.topic_name }}</span>
                <span class="topic-count">{{ topic.wrong_count }}题</span>
              </label>
            </div>
            <button
              v-if="topics.length > 0"
              class="select-all-btn"
              @click="toggleAllTopics"
            >
              {{ selectedAll ? '取消全选' : '全选' }}
            </button>
            <p v-if="topics.length === 0" class="empty-hint">暂无错题记录</p>
          </div>

          <!-- 题目数量 -->
          <div class="config-section">
            <label class="config-label">
              题目数量
              <span class="config-value">{{ questionCount }} 题</span>
            </label>
            <input
              type="range"
              v-model.number="questionCount"
              :min="1"
              :max="maxQuestions"
              class="config-slider"
            />
            <div class="slider-labels">
              <span>1</span>
              <span>{{ maxQuestions }}</span>
            </div>
          </div>

          <!-- 时间限制 -->
          <div class="config-section">
            <label class="config-label">
              时间限制
              <span class="config-value">{{ timeLimit }} 分钟</span>
            </label>
            <div class="time-presets">
              <button
                v-for="t in [10, 20, 30, 45, 60]"
                :key="t"
                class="time-btn"
                :class="{ active: timeLimit === t }"
                @click="timeLimit = t"
              >{{ t }}分钟</button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button
            class="start-btn"
            :disabled="!canStart || starting"
            @click="startSelfTest"
          >
            {{ starting ? '正在生成试卷...' : '开始自测' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { WrongTopicGroup } from '@/stores/wrongBook'
import { useExamStore } from '@/stores/exam'

const props = defineProps<{
  visible: boolean
  topics: WrongTopicGroup[]
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const examStore = useExamStore()

const selectedTopics = ref<string[]>([])
const questionCount = ref(10)
const timeLimit = ref(20)
const starting = ref(false)

const maxQuestions = computed(() => {
  if (selectedTopics.value.length === 0) {
    return props.topics.reduce((sum, t) => sum + t.wrong_count, 0)
  }
  return props.topics
    .filter(t => selectedTopics.value.includes(t.topic_id))
    .reduce((sum, t) => sum + t.wrong_count, 0)
})

const selectedAll = computed(() =>
  selectedTopics.value.length >= props.topics.length && props.topics.length > 0
)

const canStart = computed(() => maxQuestions.value > 0 && !starting.value)

watch(() => props.visible, (v) => {
  if (v) {
    selectedTopics.value = props.topics.map(t => t.topic_id)
    questionCount.value = Math.min(10, maxQuestions.value || 10)
    timeLimit.value = 20
  }
})

function toggleAllTopics() {
  if (selectedAll.value) {
    selectedTopics.value = []
  } else {
    selectedTopics.value = props.topics.map(t => t.topic_id)
  }
}

async function startSelfTest() {
  if (!canStart.value) return
  starting.value = true
  try {
    const sessionId = await examStore.startSelfTest(
      selectedTopics.value,
      questionCount.value,
      timeLimit.value,
    )
    // 先跳转，等考试页面加载完成后再关闭弹窗，避免空白过渡
    await router.push(`/exam/${sessionId}`)
    emit('close')
  } catch (e: any) {
    const msg = e?.message || '请稍后重试'
    console.error('[SelfTest] 请求失败:', e)
    alert(`自测创建失败\n${msg}`)
  } finally {
    starting.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal-card {
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.15);
  width: 440px;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 12px;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #4A3020;
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f5f5f5;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e5e5e5;
  color: #333;
}

.modal-body {
  padding: 8px 24px 16px;
  overflow-y: auto;
  flex: 1;
}

.config-section {
  margin-bottom: 20px;
}

.config-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: #6B5840;
  margin-bottom: 10px;
}

.config-value {
  color: #5298D1;
  font-size: 12px;
}

.topic-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 12px;
  border: 1.5px solid #E6DDD2;
  background: #FFFEFA;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 12px;
}

.topic-chip.checked {
  border-color: #5298D1;
  background: #F0F6FF;
}

.topic-checkbox {
  display: none;
}

.topic-name {
  color: #4A3020;
  font-weight: 500;
}

.topic-count {
  color: #B5A898;
  font-size: 11px;
}

.select-all-btn {
  margin-top: 8px;
  font-size: 11px;
  color: #5298D1;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-weight: 600;
}

.select-all-btn:hover {
  text-decoration: underline;
}

.empty-hint {
  font-size: 13px;
  color: #B5A898;
  text-align: center;
  padding: 20px 0;
}

.config-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #E6DDD2;
  outline: none;
}

.config-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #5298D1;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(82, 152, 209, 0.3);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #B5A898;
  margin-top: 4px;
}

.time-presets {
  display: flex;
  gap: 6px;
}

.time-btn {
  flex: 1;
  padding: 8px 4px;
  border-radius: 10px;
  border: 1.5px solid #E6DDD2;
  background: #FFFEFA;
  color: #8B7355;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.time-btn.active {
  border-color: #5298D1;
  background: #F0F6FF;
  color: #5298D1;
}

.time-btn:hover:not(.active) {
  background: #f9f9f9;
}

.modal-footer {
  padding: 0 24px 20px;
}

.start-btn {
  width: 100%;
  padding: 12px;
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #5298D1, #4078B0);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.start-btn:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(82, 152, 209, 0.35);
  transform: translateY(-1px);
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
