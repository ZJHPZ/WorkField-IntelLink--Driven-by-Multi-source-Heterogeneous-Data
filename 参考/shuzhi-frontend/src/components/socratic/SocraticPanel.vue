<template>
  <Teleport to="body">
    <!-- 收起态：右下角浮动按钮 -->
    <button
      v-if="!store.panelVisible || store.panelCollapsed"
      class="socratic-fab fixed z-[9997] w-12 h-12 rounded-full flex items-center justify-center text-xl shadow-xl transition-all duration-300"
      :class="store.shouldAutoTrigger ? 'socratic-fab-pulse' : 'hover:scale-110'"
      :style="fabStyle"
      @click="store.togglePanel()"
      :title="store.shouldAutoTrigger ? '你已连续提问多次，来一次苏格拉底之问吧' : '开启苏格拉底之问'"
    >
      <span class="relative z-10">🏛️</span>
    </button>

    <!-- 展开态：可拖拽悬浮窗 -->
    <div
      v-if="store.panelVisible && !store.panelCollapsed"
      ref="panelRef"
      class="socratic-window fixed z-[9997] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
      :style="panelStyle"
    >
      <!-- 标题栏（拖拽抓手） -->
      <div
        class="flex items-center justify-between px-4 py-3 cursor-grab select-none shrink-0 socratic-header"
        @mousedown.prevent="onDragStart"
        @touchstart.prevent="onDragStart"
      >
        <div class="flex items-center gap-2">
          <span class="text-lg">🏛️</span>
          <span class="text-sm font-semibold" style="color: var(--text-primary);">苏格拉底之问</span>
          <span class="text-xs px-1.5 py-0.5 rounded-full" style="background: rgba(245,158,11,0.15); color: #d97706;">引导反思</span>
        </div>
        <div class="flex items-center gap-1 ml-2 shrink-0">
          <button
            class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-colors hover:bg-white/10"
            style="color: var(--text-muted);"
            @click.stop="store.closePanel()"
            title="收起"
          >─</button>
          <button
            class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-colors hover:bg-red-500/20"
            style="color: var(--text-muted);"
            @click.stop="store.dismissPanel()"
            title="关闭"
          >✕</button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-y-auto px-4 py-3" style="max-height: 55vh;">
        <!-- 空态：等待用户在 AI对话助手 中提问 -->
        <div v-if="!store.hasContent && !store.isGenerating" class="space-y-3">
          <div class="text-center py-6">
            <span class="text-3xl">🏛️</span>
            <p class="text-xs leading-relaxed mt-3" style="color: var(--text-muted);">
              在<span style="color: var(--brand-400);"> AI对话助手 </span>中提问后，苏格拉底会在此自动给出引导反思。
            </p>
            <p class="text-xs mt-2" style="color: var(--text-muted); opacity: 0.7;">
              苏格拉底不会给你答案，但会帮你找到通往答案的路。
            </p>
          </div>
        </div>

        <!-- 生成中 -->
        <div v-if="store.isGenerating" class="flex flex-col items-center justify-center py-8 gap-3">
          <div class="socratic-spinner w-8 h-8 rounded-full border-2 border-transparent" style="border-top-color: #f59e0b;"></div>
          <p class="text-xs" style="color: var(--text-muted);">苏格拉底正在思考你的问题...</p>
        </div>

        <!-- 生成结果 — 分段展示 -->
        <div v-if="store.hasContent && !store.isGenerating" class="space-y-4">
          <!-- 引导性问题 -->
          <div
            v-if="store.questionsSection"
            class="socratic-section rounded-xl p-3.5"
          >
            <div class="flex items-center gap-2 mb-2">
              <span class="text-base">💬</span>
              <span class="text-xs font-semibold uppercase tracking-wider" style="color: #6366f1;">引导性问题</span>
            </div>
            <div class="text-sm leading-relaxed whitespace-pre-line" style="color: var(--text-primary);">{{ store.questionsSection }}</div>
          </div>

          <!-- 关键假设检验 -->
          <div
            v-if="store.assumptionsSection"
            class="socratic-section rounded-xl p-3.5"
          >
            <div class="flex items-center gap-2 mb-2">
              <span class="text-base">⚡</span>
              <span class="text-xs font-semibold uppercase tracking-wider" style="color: #f59e0b;">关键假设检验</span>
            </div>
            <div class="text-sm leading-relaxed whitespace-pre-line" style="color: var(--text-primary);">{{ store.assumptionsSection }}</div>
          </div>

          <!-- 一句话反思 -->
          <div
            v-if="store.reflectionSection"
            class="socratic-section rounded-xl p-3.5"
          >
            <div class="flex items-center gap-2 mb-2">
              <span class="text-base">✨</span>
              <span class="text-xs font-semibold uppercase tracking-wider" style="color: #10b981;">一句话反思</span>
            </div>
            <div class="text-sm leading-relaxed font-medium italic" style="color: var(--text-primary);">{{ store.reflectionSection }}</div>
          </div>

          <!-- 苏格拉底名言 -->
          <div class="text-center pt-1">
            <p class="text-xs italic opacity-60" style="color: var(--text-muted);">{{ currentQuote }}</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSocraticStore } from '@/stores/socratic'

const store = useSocraticStore()

const panelRef = ref<HTMLElement | null>(null)

// ── 名言轮换 ──
const quotes = [
  '我只知道一件事，那就是我一无所知。',
  '未经审视的人生不值得过。',
  '智慧始于承认无知。',
  '教育不是灌输，而是点燃火焰。',
  '认识你自己。',
  '最聪明的人是知道自己无知的人。',
  '思考是灵魂与自己的对话。',
  '知识的源头在于提问，而非答案。',
  '理解一个问题，比得到一个答案更重要。',
  '一个人提出问题的深度，决定了他思想的深度。',
]
const currentQuote = computed(() => {
  const idx = Math.floor(Date.now() / 10000) % quotes.length
  return `"${quotes[idx]}" —— 苏格拉底`
})

// ── 拖拽状态 ──
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0, panelX: 0, panelY: 0 })
const panelPos = ref({ x: 20, y: 120 }) // 初始位置右下

const fabStyle = computed(() => ({
  bottom: '100px',
  right: '20px',
  background: 'linear-gradient(135deg, #f59e0b, #d97706)',
  color: '#fff',
}))

const panelStyle = computed(() => ({
  right: panelPos.value.x + 'px',
  bottom: panelPos.value.y + 'px',
  width: '380px',
  minHeight: '200px',
}))

function onDragStart(e: MouseEvent | TouchEvent) {
  const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
  const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
  dragStart.value = { x: clientX, y: clientY, panelX: panelPos.value.x, panelY: panelPos.value.y }
  isDragging.value = true

  const onMove = (ev: MouseEvent | TouchEvent) => {
    const cx = 'touches' in ev ? ev.touches[0].clientX : ev.clientX
    const cy = 'touches' in ev ? ev.touches[0].clientY : ev.clientY
    const dx = cx - dragStart.value.x
    const dy = cy - dragStart.value.y
    panelPos.value = {
      x: Math.max(0, Math.min(dragStart.value.panelX - dx, window.innerWidth - 400)),
      y: Math.max(0, Math.min(dragStart.value.panelY + dy, window.innerHeight - 60)),
    }
  }
  const onUp = () => {
    isDragging.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    document.removeEventListener('touchmove', onMove)
    document.removeEventListener('touchend', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
  document.addEventListener('touchmove', onMove)
  document.addEventListener('touchend', onUp)
}


</script>

<style scoped>
.socratic-header {
  background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(217,119,6,0.04));
  border-bottom: 1px solid rgba(245,158,11,0.15);
}

.socratic-section {
  background: var(--bg-secondary);
  border: 1px solid var(--sidebar-border);
}

.socratic-fab-pulse {
  animation: socratic-pulse 2s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5);
}

@keyframes socratic-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5);
  }
  50% {
    box-shadow: 0 0 0 12px rgba(245, 158, 11, 0);
  }
}

@keyframes socratic-spin {
  to { transform: rotate(360deg); }
}
.socratic-spinner {
  animation: socratic-spin 0.8s linear infinite;
}
</style>
