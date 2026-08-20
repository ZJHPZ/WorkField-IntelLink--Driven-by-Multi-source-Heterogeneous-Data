<template>
  <Teleport to="body">
    <!-- 收起态：右下角浮动按钮 -->
    <button
      v-if="store.floatingVisible && store.floatingCollapsed"
      class="fixed z-[9998] w-11 h-11 rounded-full flex items-center justify-center text-lg shadow-lg transition-all hover:scale-110"
      style="background: var(--brand-500); color: #fff;"
      :style="{ bottom: '80px', right: '20px' }"
      @click="store.toggleFloating()"
      title="展开分析报告"
    >
      📊
    </button>

    <!-- 展开态：可拖拽悬浮窗 -->
    <div
      v-if="store.floatingVisible && !store.floatingCollapsed"
      ref="windowRef"
      class="fixed z-[9998] rounded-xl shadow-2xl flex flex-col overflow-hidden"
      :style="windowStyle"
      style="background: var(--bg-card); border: 1px solid var(--sidebar-border);"
    >
      <!-- 标题栏（拖拽抓手） -->
      <div
        class="flex items-center justify-between px-4 py-2.5 cursor-grab select-none shrink-0"
        :class="isDragging ? 'cursor-grabbing' : ''"
        style="background: rgba(99,102,241,0.08); border-bottom: 1px solid var(--sidebar-border);"
        @mousedown.prevent="onDragStart"
        @touchstart.prevent="onDragStart"
      >
        <span class="text-sm font-medium truncate" style="color: var(--text-primary);">
          📊 {{ store.floatingFileName || '分析报告' }}
        </span>
        <div class="flex items-center gap-1 ml-2 shrink-0">
          <button
            class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-colors hover:bg-white/10"
            style="color: var(--text-muted);"
            @click.stop="store.toggleFloating()"
            title="收起"
          >
            ─
          </button>
          <button
            class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-colors hover:bg-red-500/20"
            style="color: var(--text-muted);"
            @click.stop="store.closeFloating()"
            title="关闭"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- 报告内容 -->
      <div
        class="px-4 py-3 overflow-y-auto text-sm leading-relaxed"
        style="max-height: 60vh; color: var(--text-primary); scroll-behavior: smooth;"
        v-html="renderedContent"
      ></div>

      <!-- 底部操作栏 -->
      <div
        class="flex items-center justify-end gap-2 px-4 py-2.5 shrink-0"
        style="border-top: 1px solid var(--sidebar-border);"
      >
        <button
          class="text-xs px-3 py-1.5 rounded-lg transition-all"
          style="background: rgba(99,102,241,0.08); color: var(--brand-400);"
          @click="copyResult"
        >
          {{ copied ? '已复制' : '复制报告' }}
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import MarkdownIt from 'markdown-it'

const store = useAnalysisStore()
const md = new MarkdownIt({ breaks: true, linkify: true })

const windowRef = ref<HTMLElement | null>(null)
const copied = ref(false)

// 拖拽状态
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0, winX: 0, winY: 0 })
const windowPos = ref({ x: 20, y: 80 }) // 初始: right:20px, bottom:80px

const windowStyle = computed(() => ({
  right: windowPos.value.x + 'px',
  bottom: windowPos.value.y + 'px',
  width: '420px',
}))

const renderedContent = computed(() => {
  if (!store.analysisResult) return ''
  return md.render(store.analysisResult)
})

// ===== 拖拽处理 =====
function onDragStart(e: MouseEvent | TouchEvent) {
  const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
  const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY

  dragStart.value = {
    x: clientX,
    y: clientY,
    winX: windowPos.value.x,
    winY: windowPos.value.y,
  }
  isDragging.value = true

  const onMove = (ev: MouseEvent | TouchEvent) => {
    const cx = 'touches' in ev ? ev.touches[0].clientX : ev.clientX
    const cy = 'touches' in ev ? ev.touches[0].clientY : ev.clientY
    const dx = cx - dragStart.value.x
    const dy = cy - dragStart.value.y

    const viewW = window.innerWidth
    const viewH = window.innerHeight
    const winW = 420
    const winH = 400 // approximate minimum

    windowPos.value = {
      x: Math.max(0, Math.min(dragStart.value.winX - dx, viewW - winW)),
      y: Math.max(0, Math.min(dragStart.value.winY + dy, viewH - 60)),
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

// ===== 复制 =====
async function copyResult() {
  try {
    await navigator.clipboard.writeText(store.analysisResult)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
  }
}
</script>
