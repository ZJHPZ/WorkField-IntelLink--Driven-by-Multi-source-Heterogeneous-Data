<template>
  <div class="flex gap-3 mb-4" :class="message.role === 'user' ? 'flex-row-reverse' : ''">
    <!-- 头像 -->
    <div class="shrink-0">
      <div v-if="message.role === 'assistant'"
        class="w-9 h-9 bg-brand-gradient rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-md shadow-brand-500/20">
        帕
      </div>
      <div v-else
        class="w-9 h-9 bg-gradient-to-br from-space-400 to-space-600 rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-md">
        {{ message.content?.charAt(0) || '你' }}
      </div>
    </div>

    <!-- 内容 -->
    <div class="flex-1 min-w-0" :class="message.role === 'user' ? 'flex flex-col items-end' : ''">
      <!-- 消息头 -->
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs font-semibold" :class="message.role === 'assistant' ? 'text-brand-400' : 'text-gray-500'">
          {{ message.role === 'assistant' ? '帕克' : '你' }}
        </span>
        <span v-if="message.agentId" class="text-[10px] px-1.5 py-0.5 bg-brand-50 text-brand-600 rounded-full font-medium">
          {{ agentName }}
        </span>
        <span v-if="message.isStreaming && !message.agentId" class="text-[10px] text-brand-400 animate-pulse">正在输入...</span>
        <span class="text-[10px] text-gray-300">{{ formatRelativeTime(message.timestamp) }}</span>
      </div>

      <!-- 消息气泡 -->
      <div
        class="px-4 py-3 rounded-2xl text-sm leading-relaxed"
        :class="message.role === 'user'
          ? 'bg-brand-500 text-white rounded-tr-md shadow-md shadow-brand-500/15'
          : 'rounded-tl-md shadow-sm'"
        :style="message.role === 'assistant' ? { background: 'var(--bg-card)', border: '1px solid var(--border-color)' } : {}"
      >
        <template v-if="message.role === 'assistant'">
          <div class="markdown-body" v-html="renderedContent" />
          <span v-if="message.isStreaming" class="inline-block w-1.5 h-4 bg-brand-500 ml-0.5 animate-pulse rounded-sm align-middle"></span>
        </template>
        <template v-else>
          <span class="text-white">{{ message.content }}</span>
        </template>
      </div>

      <!-- AI 回复底部: 知识点悬浮卡片 -->
      <div v-if="message.role === 'assistant' && !message.isStreaming" class="flex items-center gap-2 mt-2 flex-wrap">
        <!-- 知识点标签 -->
        <template v-if="message.topics && message.topics.length">
          <img :src="iconIllumination" class="chat-inline-icon" alt="" />
          <KnowledgePopover
            v-for="topic in message.topics"
            :key="topic"
            :name="topic"
            :topic-id="getTopicId(topic)"
            :mastery-level="getTopicMastery(topic)"
            :status="getTopicStatus(topic)"
            :category="getTopicCategory(topic)"
          />
        </template>
      </div>

      <!-- AI 生成 / 用户上传的图片 -->
      <div v-if="message.images && message.images.length" class="mt-3 space-y-3" :class="message.role === 'user' ? 'flex flex-col items-end' : ''">
        <div
          v-for="(img, idx) in message.images" :key="idx"
          class="rounded-xl overflow-hidden border border-gray-100/60 shadow-sm"
          :class="message.role === 'user' ? 'max-w-[200px]' : ''"
          :style="{ background: 'var(--bg-card)' }"
        >
          <img
            :src="img.url"
            :alt="img.alt"
            class="w-full h-auto object-cover cursor-pointer"
            loading="lazy"
            @click="openImage(img.url)"
          />
          <div v-if="img.alt && img.alt !== 'AI生成的图片' && img.alt !== '用户上传图片'" class="px-3 py-2 border-t border-gray-50">
            <p class="text-xs" style="color: var(--text-secondary);">
              <img :src="iconPicture" class="chat-inline-icon" alt="" /> {{ img.alt }}
            </p>
          </div>
        </div>
      </div>

      <!-- 用户上传的文件 -->
      <div v-if="message.files && message.files.length" class="mt-2 space-y-1.5" :class="message.role === 'user' ? 'flex flex-col items-end' : ''">
        <a v-for="(f, idx) in message.files" :key="'uf-'+idx"
          :href="f.url"
          target="_blank"
          class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-amber-200 bg-white hover:bg-amber-50 transition-colors shadow-sm max-w-[220px]"
        >
          <img :src="fileIcon(f.filename)" class="file-type-icon shrink-0" alt="" />
          <div class="min-w-0">
            <p class="text-xs font-medium text-gray-700 truncate">{{ f.filename }}</p>
            <p class="text-[10px] text-gray-400">{{ formatFileSize(f.size) }}</p>
          </div>
          <span class="text-[10px] text-gray-300 shrink-0">↗</span>
        </a>
      </div>

      <!-- 图片全屏预览 -->
      <Teleport to="body">
        <Transition name="img-preview-fade">
          <div v-if="previewUrl" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/85"
            @click="previewUrl = null">
            <button class="absolute top-4 right-4 text-white text-3xl opacity-70 hover:opacity-100 transition-opacity">✕</button>
            <img :src="previewUrl" class="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl" />
          </div>
        </Transition>
      </Teleport>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ChatMessage } from '@/stores/chat'
import { useChatStore } from '@/stores/chat'
import { formatRelativeTime } from '@/utils/format'
import { useLearningStore } from '@/stores/learning'
import KnowledgePopover from './KnowledgePopover.vue'
import MarkdownIt from 'markdown-it'
import iconPicture from '@/assets/icons/jian/picture-svgrepo-com.svg'
import iconInsertWord from '@/assets/icons/jian/insert-word-svgrepo-com.svg'
import iconPieChart from '@/assets/icons/jian/pie-chart-svgrepo-com.svg'
import iconTrend from '@/assets/icons/jian/trend-analysis-svgrepo-com.svg'
import iconMail from '@/assets/icons/fang/mail-svgrepo-com.svg'
import iconIllumination from '@/assets/icons/fang/illumination-svgrepo-com.svg'

const props = defineProps<{ message: ChatMessage }>()

const chatStore = useChatStore()
const learningStore = useLearningStore()

const md = new MarkdownIt({ breaks: true, linkify: true })
const previewUrl = ref<string | null>(null)

function openImage(url: string) {
  previewUrl.value = url
}

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  return md.render(props.message.content)
})

const topicMap = computed(() => {
  const map: Record<string, { id: string; mastery: number; status: string; category: string }> = {}
  for (const t of learningStore.topicMasteryList) {
    map[t.name] = { id: t.topicId, mastery: t.masteryLevel, status: t.status, category: t.category }
  }
  return map
})

function getTopicId(name: string): string {
  return topicMap.value[name]?.id || ''
}

function getTopicMastery(name: string): number {
  return topicMap.value[name]?.mastery ?? 0
}

function getTopicStatus(name: string): string {
  return topicMap.value[name]?.status || 'locked'
}

function getTopicCategory(name: string): string {
  return topicMap.value[name]?.category || 'core'
}

const agentName = computed(() => props.message.agentId ? chatStore.getAgentName(props.message.agentId) : '')

const FILE_ICONS: Record<string, string> = {
  '.pdf': iconPicture, '.docx': iconInsertWord, '.xlsx': iconPieChart, '.pptx': iconPicture, '.txt': iconInsertWord, '.csv': iconTrend,
}

function fileIcon(filename: string): string {
  const ext = filename.slice(filename.lastIndexOf('.')).toLowerCase()
  return FILE_ICONS[ext] || iconMail
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}
</script>

<style scoped>
.chat-inline-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
  flex-shrink: 0;
}

.file-type-icon {
  width: 1.25em;
  height: 1.25em;
  display: inline-block;
}

.img-preview-fade-enter-active { transition: opacity 0.2s ease; }
.img-preview-fade-leave-active { transition: opacity 0.15s ease; }
.img-preview-fade-enter-from,
.img-preview-fade-leave-to { opacity: 0; }
</style>
