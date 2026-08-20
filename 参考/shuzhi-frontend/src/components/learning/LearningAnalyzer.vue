<template>
  <div class="glass-card rounded-2xl p-5">
    <h3 class="text-base font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary);">
      <span>🔍</span> AI 学习分析
      <span v-if="analyzing" class="text-[10px] px-1.5 py-0.5 bg-brand-500/20 rounded-full text-brand-400 animate-pulse">
        分析中...
      </span>
    </h3>

    <!-- 文件上传区域 -->
    <div
      v-if="!result && !analyzing"
      class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all"
      :class="dragOver ? 'border-brand-400 bg-brand-500/5' : 'border-slate-600/30 hover:border-brand-500/40'"
      :style="dragOver ? {} : { borderColor: 'rgba(100,116,139,0.3)' }"
      @click="triggerUpload"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".txt,.pdf,.docx,.xlsx,.pptx,.csv,.jpg,.jpeg,.png,.gif,.webp,.bmp"
        class="hidden"
        @change="handleFileSelect"
      />
      <div v-if="!selectedFile" class="space-y-2">
        <div class="text-3xl">{{ isDragOverImage ? '🖼️' : '📄' }}</div>
        <p class="text-sm font-medium" style="color: var(--text-primary);">
          上传学习笔记或课件
        </p>
        <p class="text-xs" style="color: var(--text-muted);">
          支持 TXT / PDF / Word / Excel / 图片 · 最大 10MB
        </p>
      </div>
      <div v-else class="space-y-2">
        <div class="text-2xl">{{ selectedFileIsImage ? '🖼️' : '📎' }}</div>
        <p class="text-sm font-medium" style="color: var(--text-primary);">
          {{ selectedFile.name }}
        </p>
        <p class="text-xs" style="color: var(--text-muted);">
          {{ formatSize(selectedFile.size) }}
        </p>
      </div>
    </div>

    <!-- 分析指令 -->
    <div v-if="selectedFile && !analyzing && !result" class="mt-3 space-y-2">
      <input
        v-model="customQuery"
        type="text"
        placeholder="自定义分析指令（可选）"
        class="w-full text-sm px-3 py-2 rounded-lg bg-transparent border outline-none transition-colors"
        :style="{ borderColor: 'rgba(100,116,139,0.3)', color: 'var(--text-primary)' }"
        @focus="(e: FocusEvent) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--brand-400)' }"
        @blur="(e: FocusEvent) => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(100,116,139,0.3)' }"
      />
      <button
        class="w-full py-2.5 rounded-xl text-sm font-medium transition-all bg-brand-500 text-white hover:bg-brand-600"
        @click="startAnalysis"
      >
        开始分析
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg && !analyzing" class="mt-3">
      <div class="rounded-xl p-3 text-sm" style="background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); color: #f87171;">
        {{ errorMsg }}
        <button class="ml-2 underline text-xs" @click="resetAnalysis">重试</button>
      </div>
    </div>

    <!-- 分析中 — 流式输出 -->
    <div v-if="analyzing" class="mt-3">
      <div class="rounded-xl p-4 max-h-96 overflow-y-auto" style="background: rgba(15,23,42,0.6); border: 1px solid rgba(99,102,241,0.15);">
        <div class="text-sm leading-relaxed whitespace-pre-wrap" style="color: var(--text-primary);" v-html="renderedContent"></div>
        <span v-if="analyzing" class="inline-block w-2 h-4 bg-brand-400 animate-pulse ml-0.5 align-text-bottom"></span>
      </div>
      <div class="flex items-center gap-3 mt-3">
        <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background: rgba(99,102,241,0.1);">
          <div class="h-full bg-energy-gradient rounded-full animate-pulse" style="width: 100%;"></div>
        </div>
        <span class="text-xs shrink-0" style="color: var(--text-muted);">AI 正在分析...</span>
      </div>
    </div>

    <!-- 分析结果 -->
    <div v-if="result && !analyzing" class="mt-3 space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium px-2 py-1 rounded-full" style="background: rgba(16,185,129,0.1); color: var(--mint-500);">
          ✓ 分析完成
        </span>
        <div class="flex gap-2">
          <button
            class="text-xs px-3 py-1.5 rounded-lg transition-all"
            style="background: rgba(99,102,241,0.08); color: var(--brand-400);"
            @click="resetAnalysis"
          >
            重新分析
          </button>
          <button
            class="text-xs px-3 py-1.5 rounded-lg transition-all"
            style="background: rgba(99,102,241,0.08); color: var(--brand-400);"
            @click="copyResult"
          >
            {{ copied ? '已复制' : '复制结果' }}
          </button>
          <button
            class="text-xs px-3 py-1.5 rounded-lg transition-all"
            style="background: rgba(16,185,129,0.08); color: var(--mint-500);"
            @click="openFloatingWindow"
          >
            悬浮窗
          </button>
        </div>
      </div>
      <div
        class="rounded-xl p-4 max-h-96 overflow-y-auto text-sm leading-relaxed"
        style="background: rgba(15,23,42,0.6); border: 1px solid rgba(99,102,241,0.1); color: var(--text-primary);"
        v-html="renderedContent"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import MarkdownIt from 'markdown-it'
import { useAnalysisStore } from '@/stores/analysis'

const analysisStore = useAnalysisStore()

const md = new MarkdownIt({ breaks: true, linkify: true })

const IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
const ALLOWED_EXTS = ['txt', 'pdf', 'docx', 'xlsx', 'pptx', 'csv', ...IMAGE_EXTS]

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const dragOver = ref(false)
const isDragOverImage = ref(false)
const customQuery = ref('')
const analyzing = ref(false)
const streamingContent = ref('')
const result = ref('')
const errorMsg = ref('')
const copied = ref(false)

const selectedFileIsImage = computed(() => {
  if (!selectedFile.value) return false
  const ext = selectedFile.value.name.split('.').pop()?.toLowerCase()
  return ext ? IMAGE_EXTS.includes(ext) : false
})

const renderedContent = computed(() => {
  const text = analyzing.value ? streamingContent.value : result.value
  if (!text) return ''
  return md.render(text)
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function triggerUpload() {
  if (analyzing.value) return
  fileInput.value?.click()
}

function validateFile(file: File): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!ext || !ALLOWED_EXTS.includes(ext)) {
    errorMsg.value = `不支持的文件类型 .${ext}`
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    errorMsg.value = '文件大小超过 10MB 限制'
    return false
  }
  errorMsg.value = ''
  return true
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    const file = input.files[0]
    if (validateFile(file)) {
      selectedFile.value = file
    }
  }
}

function handleDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (ext && ALLOWED_EXTS.includes(ext) && file.size <= 10 * 1024 * 1024) {
      selectedFile.value = file
      errorMsg.value = ''
    } else {
      errorMsg.value = '不支持的文件类型或文件过大'
    }
  }
}

async function startAnalysis() {
  if (!selectedFile.value) return
  analyzing.value = true
  streamingContent.value = ''
  result.value = ''
  errorMsg.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('query', customQuery.value)

  try {
    const token = localStorage.getItem('user_id') || 'default_user'
    const response = await fetch('/api/v1/analysis/stream', {
      method: 'POST',
      headers: { 'X-User-Id': token },
      body: formData,
    })

    if (!response.ok) {
      const errText = await response.text()
      throw new Error(errText || `请求失败 (${response.status})`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data:')) {
          try {
            const data = JSON.parse(line.slice(5).trim())
            if (data.type === 'text') {
              streamingContent.value += data.content || ''
            } else if (data.type === 'message_end') {
              // stream complete
            } else if (data.type === 'done') {
              // final done event
            } else if (data.type === 'error') {
              errorMsg.value = data.content || '分析失败'
            }
          } catch {
            // skip parse errors
          }
        }
      }
    }
  } catch (e: any) {
    errorMsg.value = e.message || '分析请求失败'
  } finally {
    analyzing.value = false
    if (!errorMsg.value) {
      result.value = streamingContent.value
    }
  }
}

function resetAnalysis() {
  selectedFile.value = null
  streamingContent.value = ''
  result.value = ''
  errorMsg.value = ''
  customQuery.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function copyResult() {
  try {
    await navigator.clipboard.writeText(result.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
  }
}

function openFloatingWindow() {
  const fileName = selectedFile.value?.name || '分析报告'
  analysisStore.showFloatingWindow(result.value, fileName)
}
</script>
