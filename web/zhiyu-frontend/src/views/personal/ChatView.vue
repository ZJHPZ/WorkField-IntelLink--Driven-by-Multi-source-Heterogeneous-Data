<template>
  <div class="space-y-0 h-full flex flex-col">
    <!-- ═══════════════════════ 全息指挥台头部 ═══════════════════════ -->
    <div class="panel-neon holo-overlay scan-line-fast p-0 overflow-hidden shadow-deep flex-shrink-0">
      <div class="relative z-[3] flex flex-col lg:flex-row">
        <!-- 左侧：AI 身份 -->
        <div class="flex-1 p-5 panel-circuit">
          <div class="flex items-center gap-4 relative z-[1]">
            <!-- 六角终端图标 -->
            <HexAvatar :size="56" :glow="10">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            </HexAvatar>
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="tag-plate">ADVISOR</span>
                <span class="text-[10px] font-mono tracking-widest" style="color:var(--brand-400)">SYS: ONLINE</span>
                <span class="w-1.5 h-1.5 rounded-full bg-mint-500" style="box-shadow:0 0 6px var(--mint-500)"></span>
              </div>
              <h1 class="text-lg font-bold tracking-tight data-segment" style="color:var(--text-primary)">AI Career Advisor</h1>
              <p class="text-[10px] mt-0.5 tracking-wider" style="color:var(--text-muted)">基于技能画像 × 岗位图谱 · 个性化职业建议</p>
            </div>
          </div>
        </div>
        <!-- 右侧：系统读数 -->
        <div class="lg:w-80 p-4 grid grid-cols-3 gap-0 panel-dark-zone" style="border-left:1px solid var(--brand-500);border-left-style:dashed">
          <div class="text-center p-2 relative">
            <div class="data-segment text-xl text-brand-500 mb-0.5">{{ chatStore.sessions.length }}</div>
            <div class="text-[9px] tracking-widest" style="color:var(--text-muted)">SESSIONS</div>
            <div class="absolute bottom-1 left-2 right-2 h-px bg-brand-500/20"></div>
          </div>
          <div class="text-center p-2 relative">
            <div class="data-segment text-xl text-cyan-500 mb-0.5">{{ totalMessages }}</div>
            <div class="text-[9px] tracking-widest" style="color:var(--text-muted)">MESSAGES</div>
            <div class="absolute bottom-1 left-2 right-2 h-px bg-cyan-500/20"></div>
          </div>
          <div class="text-center p-2 relative">
            <div class="data-segment text-xl mb-0.5" :class="chatStore.isStreaming ? 'text-amber-500' : 'text-mint-500'">
              {{ chatStore.isStreaming ? 'BUSY' : 'RDY' }}
            </div>
            <div class="text-[9px] tracking-widest" style="color:var(--text-muted)">STATUS</div>
            <div class="absolute bottom-1 left-2 right-2 h-px" :class="chatStore.isStreaming ? 'bg-amber-500/30' : 'bg-mint-500/20'"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ 结构梁分隔 ═══════════════════════ -->
    <div class="beam-divider flex-shrink-0"></div>

    <!-- ═══════════════════════ 主体区域 ═══════════════════════ -->
    <div class="flex-1 flex gap-4 min-h-0 pt-3">

      <!-- ── 左侧：会话列表 — 控制台面板 ── -->
      <div class="w-56 flex-shrink-0 flex flex-col gap-3">
        <!-- 新建按钮 -->
        <button
          @click="chatStore.createSession()"
          class="w-full px-4 py-2.5 text-[10px] font-bold tracking-[0.2em] uppercase text-white transition-all hover:scale-[1.02] shadow-deep"
          style="background:linear-gradient(135deg,var(--brand-600),var(--brand-500));clip-path:polygon(0 0,calc(100% - 8px) 0,100% 100%,0 100%);box-shadow:0 4px 16px color-mix(in srgb, var(--brand-500) 30%, transparent)"
        >
          + NEW SESSION
        </button>

        <!-- 会话列表 -->
        <div class="flex-1 panel-bridge p-3 overflow-y-auto">
          <div class="text-[9px] uppercase tracking-[0.2em] mb-3 flex items-center gap-2" style="color:var(--text-muted)">
            <span class="w-1.5 h-1.5 bg-brand-500/50 rounded-full"></span>
            HISTORY
          </div>

          <div
            v-for="(session, idx) in chatStore.sessions"
            :key="session.id"
            @click="chatStore.switchSession(session.id)"
            class="group px-3 py-2.5 mb-2 cursor-pointer transition-all relative"
            :class="session.id === chatStore.currentSessionId ? 'nav-chip-active' : 'nav-chip'"
          >
            <!-- 序号 -->
            <span class="absolute top-1 right-2 text-[8px] font-mono" style="color:var(--text-muted)">
              {{ String(idx + 1).padStart(2, '0') }}
            </span>
            <div class="flex items-center gap-2 mb-1">
              <span class="w-1 h-1 rounded-full" :class="session.id === chatStore.currentSessionId ? 'bg-brand-400' : 'bg-gray-600'"></span>
              <span class="text-[11px] truncate tracking-wide font-medium" style="color:var(--text-primary)">{{ session.title }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[9px] font-mono tracking-wider" style="color:var(--text-muted)">
                {{ session.messages.length }} MSG
              </span>
              <button
                @click.stop="chatStore.deleteSession(session.id)"
                class="opacity-0 group-hover:opacity-100 text-[9px] font-mono transition-opacity hover:text-rose-400"
                style="color:var(--text-muted)"
              >DEL</button>
            </div>
          </div>

          <div v-if="!chatStore.sessions.length" class="text-center py-8">
            <div class="text-[9px] font-mono tracking-widest" style="color:var(--text-muted)">NO DATA</div>
          </div>
        </div>
      </div>

      <!-- ── 右侧：对话主区 ── -->
      <div class="flex-1 flex flex-col min-h-0 panel-asymmetric shadow-deep">
        <!-- 消息列表 -->
        <div ref="messagesEl" class="flex-1 overflow-y-auto p-5 space-y-4">

          <!-- ═══ 空状态 ═══ -->
          <div v-if="!chatStore.messages.length" class="h-full flex flex-col items-center justify-center">
            <!-- 装甲板终端图标 -->
            <div class="panel-industrial p-5 mb-5 relative">
              <div class="rivet" style="top:6px;left:6px"></div>
              <div class="rivet" style="top:6px;right:6px"></div>
              <div class="rivet" style="bottom:6px;left:6px"></div>
              <div class="rivet" style="bottom:6px;right:6px"></div>
              <svg class="w-12 h-12 text-brand-400/50 relative z-[1]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <p class="text-xs tracking-[0.15em] uppercase font-bold mb-1" style="color:var(--text-primary)">Career Advisor Online</p>
            <p class="text-[10px] tracking-wider mb-8 text-center max-w-md" style="color:var(--text-muted)">基于你的技能画像和岗位图谱数据，提供职业规划建议</p>

            <!-- 快捷问题 — 金属铭牌网格 -->
            <div class="grid grid-cols-2 gap-3 max-w-lg w-full">
              <button
                v-for="(q, i) in quickQuestions"
                :key="q"
                @click="chatStore.sendMessage(q)"
                class="panel-asymmetric p-3 text-left transition-all hover:bg-brand-500/10 group"
              >
                <div class="flex items-start gap-2">
                  <span class="data-segment text-[10px] text-brand-500/60">{{ String(i + 1).padStart(2, '0') }}</span>
                  <span class="text-[11px] tracking-wide" style="color:var(--text-secondary)">{{ q }}</span>
                </div>
              </button>
            </div>
          </div>

          <!-- ═══ 消息列表 ═══ -->
          <ChatMessage v-for="msg in chatStore.messages" :key="msg.id" :msg="msg" />

          <!-- ═══ Agent 状态指示器 ═══ -->
          <div v-if="chatStore.isStreaming && chatStore.agentStatus" class="flex items-center gap-3 px-4 py-2">
            <span class="w-2 h-2 bg-cyan-400 rounded-full animate-pulse-slow" style="box-shadow:0 0 8px var(--cyan-400)"></span>
            <span class="data-segment text-[10px]">{{ chatStore.agentStatus }}</span>
          </div>
        </div>

        <!-- ═══ 输入区 — 底部控制台 ═══ -->
        <div class="flex-shrink-0 p-4 border-t" style="border-color:var(--border-color)">
          <div class="flex gap-3 items-end">
            <div class="flex-1 relative">
              <textarea
                v-model="chatStore.inputText"
                @keydown.enter.exact.prevent="onSend"
                placeholder="输入你的职业问题... (Enter 发送, Shift+Enter 换行)"
                rows="2"
                class="w-full resize-none px-4 py-3 text-xs tracking-wide focus:outline-none focus:ring-1 focus:ring-brand-500/40 font-mono"
                style="background:var(--bg-secondary);border:1px solid var(--border-color);color:var(--text-primary);clip-path:polygon(0 0,100% 0,100% calc(100% - 6px),calc(100% - 6px) 100%,0 100%)"
                :disabled="chatStore.isStreaming"
              />
              <!-- 输入提示 -->
              <div class="absolute bottom-1 right-3 text-[8px] font-mono" style="color:var(--text-muted)">
                {{ chatStore.inputText.length }} CHARS
              </div>
            </div>
            <button
              v-if="!chatStore.isStreaming"
              @click="onSend"
              :disabled="!chatStore.inputText.trim()"
              class="self-end px-6 py-3 text-[10px] font-bold tracking-[0.2em] uppercase text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:scale-[1.02] shadow-deep"
              style="background:linear-gradient(135deg,var(--brand-600),var(--brand-500));clip-path:polygon(0 0,calc(100% - 8px) 0,100% 100%,0 100%);box-shadow:0 4px 16px color-mix(in srgb, var(--brand-500) 30%, transparent)"
            >
              <span class="flex items-center gap-2">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
                SEND
              </span>
            </button>
            <!-- 停止生成（rose 应急色：中断当前回复） -->
            <button
              v-else
              @click="chatStore.stopStreaming()"
              class="self-end px-6 py-3 text-[10px] font-bold tracking-[0.2em] uppercase text-white transition-all hover:scale-[1.02] shadow-deep"
              style="background:linear-gradient(135deg,var(--rose-600),var(--rose-500));clip-path:polygon(0 0,calc(100% - 8px) 0,100% 100%,0 100%);box-shadow:0 4px 16px color-mix(in srgb, var(--rose-500) 30%, transparent)"
            >
              <span class="flex items-center gap-2">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1" fill="currentColor" stroke="none"/></svg>
                STOP
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import HexAvatar from '@/components/common/HexAvatar.vue'

const chatStore = useChatStore()
const messagesEl = ref<HTMLElement | null>(null)

const totalMessages = computed(() =>
  chatStore.sessions.reduce((sum, s) => sum + s.messages.length, 0)
)

const quickQuestions = [
  '我的技能和 AI 算法工程师匹配度如何？',
  '我应该优先学习哪些技能？',
  '转行做全栈开发可行吗？',
  '我的哪些技能在贬值？',
  '帮我制定一个学习计划',
  '分析我的职业竞争力',
]

function onSend() {
  if (chatStore.inputText.trim() && !chatStore.isStreaming) {
    chatStore.sendMessage(chatStore.inputText)
  }
}

// 自动滚动到底部
watch(
  () => chatStore.messages.length,
  () => chatStore.scrollToBottom(messagesEl.value)
)
watch(
  () => chatStore.messages[chatStore.messages.length - 1]?.content,
  () => chatStore.scrollToBottom(messagesEl.value)
)
</script>
