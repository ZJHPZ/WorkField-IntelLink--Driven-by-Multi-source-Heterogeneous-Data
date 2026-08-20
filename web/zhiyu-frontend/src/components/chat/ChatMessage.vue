<template>
  <div class="flex gap-3" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
    <!-- Assistant 头像 — 六角终端 -->
    <div v-if="msg.role === 'assistant'" class="flex-shrink-0 relative" style="width:36px;height:36px">
      <svg viewBox="0 0 40 40" class="w-full h-full" style="filter:drop-shadow(0 0 6px rgba(99,102,241,0.3))">
        <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="var(--bg-card)" stroke="var(--brand-500)" stroke-width="1"/>
      </svg>
      <span class="absolute inset-0 flex items-center justify-center">
        <svg class="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
      </span>
    </div>

    <!-- 消息气泡 -->
    <div
      class="max-w-[80%] px-4 py-3 text-xs leading-relaxed relative"
      :class="bubbleClass"
    >
      <!-- 铆钉装饰（AI 消息） -->
      <template v-if="msg.role === 'assistant'">
        <div class="rivet" style="top:4px;left:4px;transform:scale(0.7)"></div>
        <div class="rivet" style="top:4px;right:4px;transform:scale(0.7)"></div>
      </template>

      <!-- 流式加载指示器 -->
      <div v-if="msg.isStreaming && !msg.content" class="flex items-center gap-3 relative z-[1]">
        <span class="w-2 h-2 bg-brand-400 rounded-full animate-pulse-slow" style="box-shadow:0 0 8px var(--brand-400)"></span>
        <span class="data-segment text-[10px]">PROCESSING</span>
      </div>

      <!-- Markdown 内容 -->
      <div v-else class="chat-content relative z-[1]" v-html="renderedContent"></div>

      <!-- 底部信息栏 -->
      <div class="flex items-center justify-between mt-2 relative z-[1]">
        <span class="text-[9px] font-mono tracking-wider" :class="msg.role === 'user' ? 'text-white/40' : ''" :style="msg.role === 'assistant' ? { color: 'var(--text-muted)' } : {}">
          {{ formatTime(msg.timestamp) }}
        </span>
        <span v-if="msg.role === 'assistant'" class="text-[8px] font-mono tracking-widest" style="color:var(--brand-500)">
          AI ADVISOR
        </span>
      </div>
    </div>

    <!-- 用户头像 — 六角终端 -->
    <div v-if="msg.role === 'user'" class="flex-shrink-0 relative" style="width:36px;height:36px">
      <svg viewBox="0 0 40 40" class="w-full h-full" style="filter:drop-shadow(0 0 6px rgba(6,182,212,0.3))">
        <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="var(--bg-card)" stroke="var(--cyan-500)" stroke-width="1"/>
      </svg>
      <span class="absolute inset-0 flex items-center justify-center">
        <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{ msg: ChatMessage }>()

const md = new MarkdownIt({ breaks: true, linkify: true })

const renderedContent = computed(() => {
  if (props.msg.role === 'user') return escapeHtml(props.msg.content)
  return md.render(props.msg.content || '')
})

const bubbleClass = computed(() => {
  if (props.msg.role === 'user') {
    return 'bg-brand-500/90 text-white shadow-deep'
      + ' [clip-path:polygon(0_0,100%_0,100%_calc(100%-8px),calc(100%-8px)_100%,0_100%)]'
  }
  return 'shadow-deep [clip-path:polygon(0_0,100%_0,100%_calc(100%-6px),calc(100%-6px)_100%,0_100%)] border'
})

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* AI 消息面板样式 */
.chat-content {
  background: var(--bg-card);
  border-color: var(--border-color);
}

/* Markdown 渲染 — 工业风格 */
.chat-content :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-color);
  padding: 12px;
  overflow-x: auto;
  font-size: 11px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}
.chat-content :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85em;
  background: rgba(99, 102, 241, 0.1);
  padding: 1px 4px;
}
.chat-content :deep(p) {
  margin: 0.5em 0;
}
.chat-content :deep(ul), .chat-content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}
.chat-content :deep(li) {
  margin: 0.2em 0;
}
.chat-content :deep(h2) {
  font-size: 0.85em;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin: 0.8em 0 0.4em;
  color: var(--brand-400);
  padding-bottom: 4px;
  border-bottom: 1px dashed var(--border-color);
}
.chat-content :deep(h3) {
  font-size: 0.8em;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0.6em 0 0.3em;
  color: var(--cyan-400);
}
.chat-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 11px;
  margin: 0.5em 0;
}
.chat-content :deep(th), .chat-content :deep(td) {
  border: 1px solid var(--border-color);
  padding: 6px 10px;
  text-align: left;
}
.chat-content :deep(th) {
  background: rgba(99, 102, 241, 0.08);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 9px;
  letter-spacing: 0.15em;
  color: var(--brand-400);
}
.chat-content :deep(strong) {
  color: var(--brand-300);
  font-weight: 600;
}
.chat-content :deep(blockquote) {
  border-left: 2px solid var(--brand-500);
  padding-left: 12px;
  margin: 0.5em 0;
  color: var(--text-secondary);
  font-style: italic;
}
</style>
