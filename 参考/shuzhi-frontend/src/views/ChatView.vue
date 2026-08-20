<template>
  <div class="flex h-full gap-4">
    <!-- Session list sidebar -->
    <div class="hidden lg:flex flex-col w-64 shrink-0 glass-card rounded-2xl overflow-hidden">
      <div class="p-4 border-b border-gray-100/60">
        <button @click="newChat" class="w-full py-2.5 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/20 active:scale-[0.98]">
          + 新对话
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div v-for="session in chatStore.sessions" :key="session.id"
          class="p-3 rounded-xl cursor-pointer transition-all text-sm"
          :class="chatStore.currentSessionId === session.id ? 'bg-brand-50 text-brand-700 shadow-sm' : 'hover:bg-gray-50 text-gray-700'"
          @click="chatStore.switchSession(session.id)">
          <p class="truncate font-medium">{{ session.title }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ session.messages.length }}条消息</p>
        </div>
        <div v-if="chatStore.sessions.length === 0" class="text-center py-8 text-gray-400 text-sm">
          暂无对话记录
        </div>
      </div>
    </div>

    <!-- Chat area -->
    <div class="flex-1 flex flex-col glass-card rounded-2xl overflow-hidden min-w-0 relative">
      <!-- Welcome / empty state -->
      <div v-if="!currentSession || currentSession.messages.length === 0" class="flex-1 flex flex-col items-center justify-center p-8">
        <div class="relative mb-6">
          <!-- AI 心跳脉冲光环 -->
          <div class="absolute inset-0 rounded-full animate-heartbeat" style="margin: -8px;" />
          <div class="w-24 h-24 bg-brand-gradient rounded-full flex items-center justify-center text-5xl shadow-2xl shadow-brand-500/30 animate-float relative z-10">
            🧙
          </div>
          <div class="absolute -bottom-1 -right-1 w-8 h-8 bg-cyan-400 rounded-full flex items-center justify-center text-sm shadow-lg animate-pulse-slow z-20">
            <img :src="iconShortMessage" class="w-4 h-4" alt="" />
          </div>
        </div>
        <div v-if="avatarStore.enabled" class="mb-6 w-48">
          <AvatarPlayer
            @close="avatarStore.stopSession()"
          />
        </div>
        <h2 class="text-xl font-bold text-space-800 mb-2">帕克 · AI 对话助手</h2>
        <p class="text-gray-400 text-sm mb-8 text-center max-w-md">你好，我是帕克！你的专属学习伙伴，可以帮你解答问题、规划学习路径、生成练习题等。试试向我提问吧！</p>

        <!-- Quick question cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
          <button v-for="q in quickQuestions" :key="q.text" @click="sendQuick(q.text)"
            class="text-left p-3.5 bg-gray-50 hover:bg-brand-50 rounded-2xl text-sm text-gray-600 hover:text-brand-700 transition-all border border-transparent hover:border-brand-200">
            <img v-if="q.icon" :src="q.icon" class="quick-q-icon" alt="" /> {{ q.text }}
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div v-else ref="msgContainer" class="flex-1 overflow-y-auto p-4 space-y-3 relative">
        <ChatMessage v-for="msg in currentSession.messages" :key="msg.id" :message="msg" />
        <!-- 思考中指示器 — 动态展示智能体调度状态 -->
        <div v-if="chatStore.isStreaming" class="flex items-center gap-3 px-4 py-3">
          <div class="relative shrink-0">
            <div class="absolute inset-0 rounded-xl animate-heartbeat" style="margin: -4px;" />
            <div class="w-8 h-8 rounded-xl flex items-center justify-center text-sm relative z-10 transition-all duration-500"
              :class="chatStore.activeAgent ? 'bg-purple-100' : 'bg-brand-100'">
              <Transition name="icon-swap" mode="out-in">
                <span v-if="chatStore.activeAgent" key="bot">🤖</span>
                <span v-else key="brain">🧠</span>
              </Transition>
            </div>
          </div>
          <div class="flex gap-1.5" v-if="!chatStore.activeAgent">
            <span class="w-2 h-2 bg-brand-400 rounded-full animate-typing" style="animation-delay: 0s"></span>
            <span class="w-2 h-2 bg-brand-400 rounded-full animate-typing" style="animation-delay: 0.2s"></span>
            <span class="w-2 h-2 bg-brand-400 rounded-full animate-typing" style="animation-delay: 0.4s"></span>
          </div>
          <Transition name="status-text" mode="out-in">
            <span v-if="chatStore.activeAgent" key="agent" class="text-xs font-medium text-purple-600">
              <span class="font-semibold">帕克</span>
              <span class="animate-fadeIn inline-block ml-1">{{ chatStore.activeAgent.statusMessage }}</span>
              <span v-if="chatStore.activeAgent.id !== 'multi'" class="text-[10px] px-1.5 py-0.5 bg-purple-50 text-purple-500 rounded-full font-medium ml-1.5">
                {{ chatStore.activeAgent.name }}
              </span>
            </span>
            <span v-else key="thinking" class="text-xs font-medium text-brand-500">
              <span class="font-semibold">帕克</span>正在思考<span class="animate-pulse">...</span>
            </span>
          </Transition>
        </div>

      </div>

      <!-- Input area -->
      <div class="p-4 border-t border-gray-100/60 bg-gray-50/30">
        <!-- 录音状态栏 -->
        <div v-if="recorder.isRecording.value" class="flex items-center gap-3 mb-3 px-3 py-2.5 bg-red-50 rounded-xl border border-red-200 animate-fadeIn">
          <span class="relative flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
          <span class="text-sm font-medium text-red-600">{{ recorder.useWebSpeech ? '正在聆听' : '录音中' }}</span>
          <span class="text-sm text-red-400 font-mono">{{ formatDuration(recorder.duration.value) }}</span>
          <div class="flex-1 flex items-center gap-0.5 px-4">
            <div v-for="i in 12" :key="i" class="w-1 bg-red-400 rounded-full animate-wave" :style="{ height: (8 + Math.random() * 20) + 'px', animationDelay: (i * 0.08) + 's' }"></div>
          </div>
          <button @click="cancelRecording" class="text-xs px-2.5 py-1.5 bg-red-100 text-red-500 rounded-lg hover:bg-red-200 transition-colors shrink-0">
            取消
          </button>
        </div>
        <!-- Web Speech 实时识别文本 -->
        <div v-if="recorder.isRecording.value && interimSpeechText" class="mb-3 px-3 py-2 bg-gray-50 rounded-xl border border-gray-200 animate-fadeIn">
          <span class="text-sm text-gray-500 italic">{{ interimSpeechText }}</span>
          <span class="inline-block w-1 h-4 bg-brand-500 ml-1 animate-pulse rounded-sm align-middle"></span>
        </div>
        <!-- 识别中 -->
        <div v-if="isRecognizing" class="flex items-center gap-2 mb-3 px-3 py-2 bg-blue-50 rounded-xl border border-blue-200 animate-fadeIn">
          <span class="text-sm text-blue-600">正在识别语音...</span>
          <span class="flex gap-1">
            <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-typing" style="animation-delay: 0s"></span>
            <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-typing" style="animation-delay: 0.2s"></span>
            <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-typing" style="animation-delay: 0.4s"></span>
          </span>
        </div>
        <!-- ASR 错误提示 -->
        <div v-if="asrError" class="flex items-center gap-2 mb-3 px-3 py-2 bg-red-50 rounded-xl border border-red-200 animate-fadeIn">
          <span class="text-sm text-red-600">{{ asrError }}</span>
          <button @click="asrError = ''" class="ml-auto text-xs text-red-400 hover:text-red-600 shrink-0">✕</button>
        </div>
        <div class="flex items-end gap-3">
          <!-- 已选图片预览 -->
        <div v-if="uploadedImages.length" class="flex items-center gap-2 mb-3 flex-wrap">
          <div v-for="(img, idx) in uploadedImages" :key="'img-'+idx" class="relative group shrink-0">
            <img :src="img.url" class="w-16 h-16 object-cover rounded-xl border-2 border-brand-200 shadow-sm" />
            <button @click="removeImage(idx)"
              class="absolute -top-2 -right-2 w-5 h-5 bg-rose-500 text-white rounded-full text-[10px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-md">✕</button>
            <span v-if="img.uploading" class="absolute inset-0 bg-black/30 rounded-xl flex items-center justify-center">
              <span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            </span>
          </div>
        </div>

        <!-- 已选文件预览 -->
        <div v-if="uploadedFiles.length" class="flex items-center gap-2 mb-3 flex-wrap">
          <div v-for="(f, idx) in uploadedFiles" :key="'file-'+idx" class="relative group shrink-0">
            <div class="flex items-center gap-2 px-3 py-2 bg-white rounded-xl border-2 border-amber-200 shadow-sm min-w-[120px]">
              <img :src="fileIcon(f)" class="file-type-icon shrink-0" alt="" />
              <div class="min-w-0">
                <p class="text-xs font-medium text-gray-700 truncate max-w-[120px]">{{ f.filename }}</p>
                <p class="text-[10px] text-gray-400">{{ formatFileSize(f.size) }}</p>
              </div>
            </div>
            <button @click="removeFile(idx)"
              class="absolute -top-2 -right-2 w-5 h-5 bg-rose-500 text-white rounded-full text-[10px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-md">✕</button>
            <span v-if="f.uploading" class="absolute inset-0 bg-black/20 rounded-xl flex items-center justify-center">
              <span class="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></span>
            </span>
          </div>
        </div>

        <!-- 图片上传按钮 -->
          <button
            @click="triggerImageUpload"
            :disabled="chatStore.isStreaming"
            class="p-3 rounded-xl text-sm transition-all shrink-0 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed"
            :class="uploadedImages.length ? 'bg-brand-100 text-brand-600 border border-brand-300' : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700'"
            title="上传图片"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </button>
          <input
            ref="imageInput"
            type="file"
            accept="image/*"
            multiple
            class="hidden"
            @change="onImagesSelected"
          />

        <!-- 文件上传按钮 -->
          <button
            @click="triggerFileUpload"
            :disabled="chatStore.isStreaming"
            class="p-3 rounded-xl text-sm transition-all shrink-0 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed"
            :class="uploadedFiles.length ? 'bg-amber-50 text-amber-600 border border-amber-300' : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700'"
            title="上传文件"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
          </button>
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv"
            multiple
            class="hidden"
            @change="onFilesSelected"
          />

          <!-- 麦克风按钮 -->
          <button v-if="recorder.isSupported.value"
            @click="toggleRecording"
            :disabled="chatStore.isStreaming || isRecognizing"
            class="p-3 rounded-xl text-sm transition-all shrink-0 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed"
            :class="recorder.isRecording.value
              ? 'bg-red-500 text-white shadow-lg shadow-red-500/20 hover:bg-red-600'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700'"
            :title="recorder.isRecording.value ? '停止录音' : '语音输入'"
          >
            <svg v-if="!recorder.isRecording.value" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V6a4 4 0 0 0-4-4z"/><path d="M19 10v1a7 7 0 1 1-14 0v-1"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
          </button>
          <textarea v-model="inputText" @keydown.enter.exact.prevent="send"
            placeholder="向帕克提问... (Enter发送，Shift+Enter换行)"
            rows="1"
            class="flex-1 resize-none rounded-xl border px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 max-h-32"
            style="background: rgba(15,23,42,0.6); border-color: var(--border-color); color: var(--text-primary);"
            :disabled="chatStore.isStreaming"
            @input="autoResize"
          ></textarea>
          <button @click="send" :disabled="(!inputText.trim() && !uploadedImages.length && !uploadedFiles.length) || chatStore.isStreaming"
            class="px-5 py-3 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-brand-500/20 shrink-0 active:scale-[0.97]">
            <span v-if="chatStore.isStreaming" class="flex gap-1">
              <span class="w-1.5 h-1.5 bg-white rounded-full animate-typing" style="animation-delay: 0s"></span>
              <span class="w-1.5 h-1.5 bg-white rounded-full animate-typing" style="animation-delay: 0.2s"></span>
              <span class="w-1.5 h-1.5 bg-white rounded-full animate-typing" style="animation-delay: 0.4s"></span>
            </span>
            <span v-else>发送</span>
          </button>
        </div>
        <!-- 语音控制栏 -->
        <div class="flex items-center justify-between mt-2">
          <div class="flex items-center gap-2">
            <!-- 语音播报开关 -->
            <button
              @click="toggleVoiceMode"
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
              :class="voiceEngine.isEnabled
                ? 'bg-brand-50 text-brand-600 border border-brand-200'
                : 'bg-gray-50 text-gray-400 border border-gray-200 hover:text-gray-600'"
              :title="voiceEngine.isEnabled ? '关闭语音播报' : '开启边输出边朗读'"
            >
              <span v-if="voiceEngine.isEnabled">🔊</span>
              <span v-else>🔈</span>
              {{ voiceEngine.isEnabled ? '朗读中' : '开启朗读' }}
            </button>
            <!-- 数字人开关 -->
            <button
              @click="avatarStore.toggle()"
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
              :class="avatarStore.enabled
                ? 'bg-purple-50 text-purple-600 border border-purple-200'
                : 'bg-gray-50 text-gray-400 border border-gray-200 hover:text-gray-600'"
              :disabled="avatarStore.isConnecting"
              :title="avatarStore.enabled ? '关闭数字人' : '开启数字人形象'"
            >
              <span v-if="avatarStore.isConnecting" class="inline-block w-3 h-3 border border-purple-400 border-t-transparent rounded-full animate-spin mr-0.5"></span>
              <span v-else>🧑‍💻</span>
              {{ avatarStore.isConnecting ? '连接中' : avatarStore.enabled ? '数字人' : '数字人' }}
            </button>
            <!-- 音色选择（仅开启时显示） -->
            <select
              v-if="voiceEngine.isEnabled"
              :value="voiceEngine.speaker.value"
              @change="voiceEngine.setSpeaker(($event.target as HTMLSelectElement).value)"
              class="px-2 py-1 rounded-lg text-[11px] font-medium bg-white border border-brand-200 text-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-400 cursor-pointer"
            >
              <option v-for="(name, id) in SPEAKERS" :key="id" :value="id">{{ name }}</option>
            </select>
            <!-- 朗读状态指示 -->
            <span v-if="voiceEngine.isEnabled && voiceEngine.state.value === 'speaking'" class="text-[10px] text-brand-500 animate-pulse">
              正在朗读...
            </span>
          </div>
          <span class="text-[10px] text-gray-400">
            Enter 发送 · Shift+Enter 换行 · 🎤 语音输入
          </span>
        </div>
      </div>

      <!-- 数字人迷你浮窗（有消息时显示） -->
      <AvatarPlayer
        v-if="avatarStore.enabled && currentSession && currentSession.messages.length > 0"
        :mini="true"
        @close="avatarStore.stopSession()"
      />

      <!-- 苏格拉底反思蒙版 — 覆盖对话区（含欢迎态和消息态） -->
      <div
        v-if="socraticStore.showOverlay && socraticStore.hasContent"
        class="absolute inset-0 z-40 flex flex-col items-center justify-center rounded-2xl"
        style="background: rgba(15, 23, 42, 0.82); backdrop-filter: blur(6px);"
        @click.self="socraticStore.dismissOverlay()"
      >
        <span class="text-4xl mb-4 animate-float">🏛️</span>
        <p class="text-base font-semibold text-center px-6" style="color: var(--text-primary);">
          {{ overlayQuote }}
        </p>
        <p class="text-xs mt-2 text-center px-6" style="color: var(--text-muted);">
          苏格拉底邀请你先反思，再阅读答案
        </p>
        <div class="flex gap-3 mt-6">
          <button
            @click="socraticStore.openPanel()"
            class="px-4 py-2 rounded-lg text-white text-sm font-medium transition-all hover:opacity-90 active:scale-[0.97]"
            style="background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 4px 14px rgba(245,158,11,0.35);"
          >📖 查看反思</button>
          <button
            @click="socraticStore.dismissOverlay()"
            class="px-4 py-2 rounded-lg text-sm border transition-all hover:bg-white/5 active:scale-[0.97]"
            style="border-color: var(--border-color); color: var(--text-muted);"
          >我知道了</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useSocraticStore } from '@/stores/socratic'
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { useVoiceEngine, SPEAKERS } from '@/composables/voice-engine'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import AvatarPlayer from '@/components/avatar/AvatarPlayer.vue'
import { useAvatarStore } from '@/stores/avatar'
import iconShortMessage from '@/assets/icons/fang/short-message-svgrepo-com.svg'
import iconInsertWord from '@/assets/icons/jian/insert-word-svgrepo-com.svg'
import iconPieChart from '@/assets/icons/jian/pie-chart-svgrepo-com.svg'
import iconPicture from '@/assets/icons/jian/picture-svgrepo-com.svg'
import iconTrend from '@/assets/icons/jian/trend-analysis-svgrepo-com.svg'
import iconMail from '@/assets/icons/fang/mail-svgrepo-com.svg'
import iconIllumination from '@/assets/icons/fang/illumination-svgrepo-com.svg'
import iconMap from '@/assets/icons/fang/map-svgrepo-com.svg'
import iconPlanList from '@/assets/icons/blue/plan-list-svgrepo-com.svg'

const chatStore = useChatStore()
const socraticStore = useSocraticStore()
const avatarStore = useAvatarStore()

// ── 苏格拉底蒙版名言轮换 ──
const overlayQuotes = [
  '你真的理解了吗，还是只是记住了答案？',
  '未经审视的知识不值得拥有。',
  '停下来，想一想——这背后的原理是什么？',
  '提问比答案更重要。',
  '不要急于阅读答案，先问问自己。',
  '知识的源头在于提问，而非答案。',
  '理解一个问题，比得到一个答案更重要。',
  '一个人提出问题的深度，决定了他思想的深度。',
]
const overlayQuote = computed(() => {
  const idx = Math.floor(Date.now() / 8000) % overlayQuotes.length
  return `"${overlayQuotes[idx]}" —— 苏格拉底`
})
const recorder = useAudioRecorder()
const voiceEngine = useVoiceEngine()
const inputText = ref('')
const msgContainer = ref<HTMLElement | null>(null)
const isRecognizing = ref(false)
const asrError = ref('')
const interimSpeechText = ref('')  // Web Speech 实时中间结果

interface UploadedImage {
  url: string
  uploading: boolean
}
interface UploadedFile {
  url: string
  uploading: boolean
  filename: string
  size: number
  content_type: string
}
const uploadedImages = ref<UploadedImage[]>([])
const uploadedFiles = ref<UploadedFile[]>([])
const imageInput = ref<HTMLInputElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

const apiBase = import.meta.env.VITE_API_BASE_URL || ''

// 注册 Web Speech 结果回调
recorder.onResult((text: string) => {
  if (text.trim()) {
    inputText.value = text.trim()
    interimSpeechText.value = ''
  }
})
recorder.onInterim((text: string) => {
  interimSpeechText.value = text
})

const currentSession = computed(() => chatStore.getCurrentSession())

const quickQuestions = [
  { text: '什么是Hadoop？它有哪些核心组件？', icon: '' },
  { text: '帮我规划大数据学习路径', icon: iconMap },
  { text: '给我出几道Spark相关的练习题', icon: iconPlanList },
  { text: '解释一下MapReduce的工作原理', icon: iconIllumination },
]

function newChat() {
  chatStore.createSession()
}

function toggleVoiceMode() {
  voiceEngine.toggle()
}

async function send() {
  const text = inputText.value.trim()
  const hasImages = uploadedImages.value.length > 0
  const hasFiles = uploadedFiles.value.length > 0
  if ((!text && !hasImages && !hasFiles) || chatStore.isStreaming) return

  // 检查是否有文件/图片还在上传中
  const stillUploading = uploadedImages.value.some(i => i.uploading) || uploadedFiles.value.some(f => f.uploading)
  if (stillUploading) return  // 等待上传完成，避免静默丢弃

  inputText.value = ''

  if (avatarStore.isActive) avatarStore.interrupt()

  if (!chatStore.getCurrentSession()) {
    chatStore.createSession()
  }

  // 收集已上传完成的图片 URL
  const imageUrls = uploadedImages.value.map(i => i.url)
  uploadedImages.value = []

  // 收集已上传完成的文件信息
  const files = uploadedFiles.value.map(f => ({
    url: f.url,
    filename: f.filename,
    size: f.size,
    content_type: f.content_type,
  }))
  uploadedFiles.value = []

  // 自动生成默认消息（仅文件/图片时）
  let msgText = text
  if (!msgText) {
    if (hasFiles && hasImages) msgText = '请分析这些文件'
    else if (hasFiles) msgText = '请分析这份文件'
    else if (hasImages) msgText = '请分析这张图片'
  }

  await chatStore.sendMessage(msgText, imageUrls.length ? imageUrls : undefined, files.length ? files : undefined)
  await scrollToBottom()

  // 通知苏格拉底Store: 用户提了一个潜在的知识问题
  if (msgText && _isKnowledgeQuestion(msgText)) {
    socraticStore.onKnowledgeQuestionAsked(msgText)
  }
}

async function sendQuick(q: string) {
  inputText.value = q
  await send()
}

// ── 数字人：AI 回复完成后自动驱动播报 ──
watch(() => chatStore.isStreaming, (streaming, wasStreaming) => {
  if (!streaming && wasStreaming && avatarStore.isActive && avatarStore.mode === 'driver') {
    const session = currentSession.value
    if (!session) return
    const msgs = session.messages
    const lastAssistant = [...msgs].reverse().find(m => m.role === 'assistant')
    if (lastAssistant && lastAssistant.content) {
      const text = lastAssistant.content.replace(/<[^>]+>/g, '').slice(0, 500)
      if (text.trim()) avatarStore.driveText(text)
    }
  }
})

// ── 图片上传 ──
function triggerImageUpload() {
  imageInput.value?.click()
}

async function onImagesSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files || !files.length) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    // 本地预览
    const localUrl = URL.createObjectURL(file)
    const img: UploadedImage = { url: localUrl, uploading: true }
    uploadedImages.value.push(img)
    const idx = uploadedImages.value.length - 1

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', localStorage.getItem('user_id') || 'default_user')

      const resp = await fetch(`${apiBase}/api/v1/chat/upload`, {
        method: 'POST',
        headers: { 'X-User-Id': localStorage.getItem('user_id') || 'default_user' },
        body: formData,
      })
      if (resp.ok) {
        const json = await resp.json()
        URL.revokeObjectURL(localUrl)
        if (json.success) {
          uploadedImages.value[idx] = { url: json.url, uploading: false }
        } else {
          throw new Error(json.message || '上传失败')
        }
      } else {
        const errData = await resp.json().catch(() => ({}))
        throw new Error(errData.detail || `上传失败 (${resp.status})`)
      }
    } catch (e: any) {
      URL.revokeObjectURL(localUrl)
      uploadedImages.value.splice(idx, 1)
      asrError.value = e.message || '图片上传失败，请重试'
      setTimeout(() => { asrError.value = '' }, 4000)
    }
  }
  input.value = ''
}

function removeImage(idx: number) {
  const img = uploadedImages.value[idx]
  if (img && img.url.startsWith('blob:')) {
    URL.revokeObjectURL(img.url)
  }
  uploadedImages.value.splice(idx, 1)
}

// ── 文件上传 ──
const FILE_EXT_ICONS: Record<string, string> = {
  '.pdf': iconPicture,
  '.docx': iconInsertWord,
  '.xlsx': iconPieChart,
  '.pptx': iconPicture,
  '.txt': iconInsertWord,
  '.csv': iconTrend,
}

function fileIcon(f: UploadedFile): string {
  const ext = f.filename ? f.filename.slice(f.filename.lastIndexOf('.')).toLowerCase() : ''
  return FILE_EXT_ICONS[ext] || iconMail
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}

function triggerFileUpload() {
  fileInput.value?.click()
}

async function onFilesSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files || !files.length) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const f: UploadedFile = {
      url: '',
      uploading: true,
      filename: file.name,
      size: file.size,
      content_type: file.type,
    }
    uploadedFiles.value.push(f)
    const idx = uploadedFiles.value.length - 1

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', localStorage.getItem('user_id') || 'default_user')

      const resp = await fetch(`${apiBase}/api/v1/chat/upload`, {
        method: 'POST',
        headers: { 'X-User-Id': localStorage.getItem('user_id') || 'default_user' },
        body: formData,
      })
      if (resp.ok) {
        const json = await resp.json()
        if (json.success) {
          uploadedFiles.value[idx] = { url: json.url, uploading: false, filename: json.original_name || file.name, size: json.size, content_type: json.content_type }
        } else {
          throw new Error(json.message || '上传失败')
        }
      } else {
        const errData = await resp.json().catch(() => ({}))
        throw new Error(errData.detail || `上传失败 (${resp.status})`)
      }
    } catch (e: any) {
      uploadedFiles.value.splice(idx, 1)
      asrError.value = e.message || '文件上传失败，请重试'
      setTimeout(() => { asrError.value = '' }, 4000)
    }
  }
  input.value = ''
}

function removeFile(idx: number) {
  uploadedFiles.value.splice(idx, 1)
}

async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

function formatDuration(secs: number): string {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

async function toggleRecording() {
  if (recorder.isRecording.value) {
    asrError.value = ''
    if (recorder.useWebSpeech) {
      // Web Speech 模式：停止识别，结果已通过 onResult 回调填入
      recorder.stop()
    } else {
      // MediaRecorder 降级模式：等待 blob → 上传后端 ASR
      const blob = await recorder.stop()
      if (blob) {
        await recognizeAudio()
      }
    }
  } else {
    asrError.value = ''
    interimSpeechText.value = ''
    recorder.start()
  }
}

function cancelRecording() {
  recorder.cancel()
  interimSpeechText.value = ''
  asrError.value = ''
}

async function recognizeAudio() {
  const blob = recorder.audioBlob.value
  if (!blob) {
    asrError.value = '录音数据为空，请重试'
    return
  }

  asrError.value = ''
  isRecognizing.value = true
  try {
    const formData = new FormData()
    const ext = blob.type.includes('ogg') ? 'ogg' : 'webm'
    formData.append('audio_file', blob, `recording.${ext}`)
    formData.append('uid', localStorage.getItem('user_id') || 'default_user')

    const resp = await fetch(`${apiBase}/api/v1/audio/asr/upload`, {
      method: 'POST',
      headers: {
        'X-User-Id': localStorage.getItem('user_id') || 'default_user',
      },
      body: formData,
    })

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}))
      asrError.value = (errData as any).detail || `语音识别失败 (${resp.status})`
      return
    }

    const json = await resp.json()
    const text = json.data?.text || ''
    if (text.trim()) {
      inputText.value = text.trim()
    } else {
      asrError.value = '未能识别到语音内容，请重试'
    }
  } catch (e: any) {
    asrError.value = e.message || '语音识别请求失败，请检查网络'
  } finally {
    isRecognizing.value = false
  }
}

async function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 128) + 'px'
}

watch(() => currentSession.value?.messages.length, () => {
  scrollToBottom()
})

// ── 知识问题检测（苏格拉底触发用）──
const _KNOWLEDGE_PATTERNS = [
  '什么', '如何', '怎么', '为什么', '区别', '原理', '机制', '过程',
  '架构', '流程', '概念', '定义', '作用', '关系', '对比', '区别',
  '?', '？',
]
function _isKnowledgeQuestion(text: string): boolean {
  if (text.length < 5) return false
  const lower = text.toLowerCase()
  // 过滤闲聊
  const chats = ['你好', '谢谢', '再见', '好的', '嗯', 'ok', 'hi', 'hello', '天气', '今天']
  if (chats.some(c => lower.includes(c))) return false
  return _KNOWLEDGE_PATTERNS.some(p => lower.includes(p))
}
</script>

<style scoped>
.file-type-icon {
  width: 22px;
  height: 22px;
}

.quick-q-icon {
  width: 16px;
  height: 16px;
  display: inline-block;
  vertical-align: middle;
  opacity: 0.7;
  margin-right: 2px;
}

/* 智能体状态切换过渡动画 */
.status-text-enter-active,
.status-text-leave-active {
  transition: all 0.25s ease;
}
.status-text-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.status-text-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.icon-swap-enter-active,
.icon-swap-leave-active {
  transition: all 0.2s ease;
}
.icon-swap-enter-from {
  opacity: 0;
  transform: scale(0.6);
}
.icon-swap-leave-to {
  opacity: 0;
  transform: scale(0.6);
}

/* 录音波形动画 */
@keyframes wave {
  0%, 100% { height: 8px; }
  50% { height: 24px; }
}

.animate-wave {
  animation: wave 0.8s ease-in-out infinite;
}

.animate-fadeIn {
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

</style>
