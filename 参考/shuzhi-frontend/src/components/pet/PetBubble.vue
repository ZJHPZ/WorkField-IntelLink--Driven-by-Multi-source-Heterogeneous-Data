<template>
  <div
    class="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 animate-fade-in-up"
    :style="{ minWidth: '180px', maxWidth: '260px' }"
  >
    <div class="bg-white/95 backdrop-blur-md rounded-2xl px-4 py-3 shadow-xl shadow-black/10 border border-gray-100">
      <!-- 消息文本 -->
      <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
        {{ displayedText }}
      </p>

      <!-- 操作按钮 -->
      <div v-if="buttons && buttons.length" class="flex gap-2 mt-2.5">
        <button
          v-for="btn in buttons"
          :key="btn.value"
          class="flex-1 py-1.5 px-3 text-xs font-medium rounded-xl transition-all active:scale-95"
          :class="btn.value === 'dismiss'
            ? 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            : 'bg-brand-500 text-white hover:bg-brand-600 shadow-sm shadow-brand-500/20'"
          @click.stop="$emit('action', btn.value)"
        >
          {{ btn.label }}
        </button>
      </div>
    </div>

    <!-- 小三角 -->
    <div class="absolute left-1/2 -translate-x-1/2 -bottom-1.5 w-3 h-3 bg-white/95 border-r border-b border-gray-100 rotate-45" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  message: string
  buttons?: { label: string; value: string }[]
  petName?: string
}>()

defineEmits<{
  action: [value: string]
  dismiss: []
}>()

const displayedText = ref('')

// 打字机效果
onMounted(() => {
  displayedText.value = ''
  const chars = props.message.split('')
  let i = 0
  const timer = setInterval(() => {
    if (i < chars.length) {
      displayedText.value += chars[i]
      i++
    } else {
      clearInterval(timer)
    }
  }, 30)
})

watch(() => props.message, () => {
  displayedText.value = props.message
})
</script>
