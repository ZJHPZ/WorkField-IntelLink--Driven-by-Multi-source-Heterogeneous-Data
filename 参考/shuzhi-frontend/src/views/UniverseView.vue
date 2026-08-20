<template>
  <div class="universe-view fixed inset-0 z-0 bg-[#050510]">
    <!-- Three.js canvas -->
    <canvas ref="canvasRef" class="absolute inset-0" />

    <!-- Loading overlay -->
    <transition name="fade">
      <div v-if="!isReady" class="absolute inset-0 flex items-center justify-center bg-[#050510]/90 z-10">
        <div class="text-center">
          <div ref="loaderContainer" class="w-40 h-40 mx-auto mb-2" />
          <p class="text-gray-400 text-sm tracking-wider">知识宇宙正在生成...</p>
        </div>
      </div>
    </transition>

    <!-- Top-left: scene status -->
    <div class="absolute top-6 left-6 z-10 pointer-events-none">
      <h1 class="text-2xl font-bold text-white/90 tracking-wide" style="text-shadow: 0 0 30px rgba(99,102,241,0.5);">
        知识宇宙
      </h1>
      <p class="text-xs text-white/40 mt-1 tracking-wider">
        {{ isIdle ? '静滞 · 等待唤醒' : isWakingUp ? '正在唤醒...' : '利萨如旋转 · 探索中' }}
      </p>
    </div>

    <!-- Top-right: legend -->
    <div class="absolute top-6 right-6 z-10 flex flex-col gap-1.5 pointer-events-none">
      <div class="flex items-center gap-2 text-xs text-white/60 bg-black/30 backdrop-blur-md rounded-lg px-3 py-1.5 border border-white/5">
        <span class="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.8)]" /> 已掌握
      </div>
      <div class="flex items-center gap-2 text-xs text-white/60 bg-black/30 backdrop-blur-md rounded-lg px-3 py-1.5 border border-white/5">
        <span class="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_6px_rgba(99,102,241,0.8)]" /> 学习中
      </div>
      <div class="flex items-center gap-2 text-xs text-white/60 bg-black/30 backdrop-blur-md rounded-lg px-3 py-1.5 border border-white/5">
        <span class="w-2 h-2 rounded-full bg-slate-600" /> 待解锁
      </div>
      <div class="flex items-center gap-2 text-xs text-white/40 bg-black/30 backdrop-blur-md rounded-lg px-3 py-1.5 border border-white/5 mt-1">
        <span class="w-1.5 h-1.5 rounded-full bg-indigo-400/50" /> 装饰节点
      </div>
    </div>

    <!-- Center: selected node name浮现 -->
    <transition name="fade">
      <div v-if="showNodeLabel"
        class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 pointer-events-none text-center">
        <p class="text-white/70 text-base tracking-[0.2em] animate-pulse">
          {{ selectedNode?.name }} · 已展开
        </p>
      </div>
    </transition>

    <!-- Bottom: selected node detail panel -->
    <transition name="slide-up-panel">
      <div
        v-if="selectedNode"
        class="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 w-full max-w-md"
      >
        <div class="glass-card mx-4 rounded-2xl p-5 border border-white/10 backdrop-blur-xl"
          style="background: rgba(15,15,40,0.85);">
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shrink-0"
              :style="{ background: nodeCatStyle(selectedNode.category).bg }">
              {{ nodeCatStyle(selectedNode.category).icon }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <h3 class="text-lg font-bold text-white">{{ selectedNode.name }}</h3>
                <span class="text-[10px] px-2 py-0.5 rounded-full font-medium"
                  :style="nodeStatusBadge(selectedNode.status)">
                  {{ nodeStatusLabel(selectedNode.status) }}
                </span>
              </div>
              <p class="text-xs text-white/50">{{ categoryName(selectedNode.category) }} · 掌握度 {{ Math.round(selectedNode.masteryLevel * 100) }}%</p>

              <!-- Mastery bar -->
              <div class="h-1.5 rounded-full mt-3 overflow-hidden" style="background: rgba(255,255,255,0.08);">
                <div class="h-full rounded-full transition-all duration-700"
                  :style="{
                    width: (selectedNode.masteryLevel * 100) + '%',
                    background: nodeCatStyle(selectedNode.category).fill,
                  }" />
              </div>

              <!-- Actions -->
              <div class="flex gap-2 mt-4">
                <button class="flex-1 py-2 rounded-xl text-sm font-medium transition-all active:scale-95"
                  style="background: rgba(99,102,241,0.3); color: #c7d2fe; border: 1px solid rgba(99,102,241,0.3);"
                  @click="goToChat(selectedNode)">
                  <img :src="shortMessageIcon" class="icon-btn" alt="" /> 提问
                </button>
                <button class="flex-1 py-2 rounded-xl text-sm font-medium transition-all active:scale-95"
                  style="background: rgba(16,185,129,0.3); color: #a7f3d0; border: 1px solid rgba(16,185,129,0.3);"
                  @click="goToPractice(selectedNode)">
                  <img :src="brushIcon" class="icon-btn" alt="" /> 练习
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Idle overlay -->
    <transition name="fade">
      <div v-if="isIdle && !isWakingUp"
        class="absolute inset-0 z-5 pointer-events-none flex items-center justify-center">
        <p class="text-white/15 text-sm tracking-[0.3em] animate-pulse">静 滞 模 式</p>
      </div>
    </transition>

    <!-- Wake-up flash overlay -->
    <transition name="fade">
      <div v-if="isWakingUp"
        class="absolute inset-0 z-5 pointer-events-none"
        style="background: radial-gradient(ellipse at center, rgba(99,102,241,0.08) 0%, transparent 70%);" />
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import lottie, { type AnimationItem } from 'lottie-web'
import { useUniverse } from '@/composables/useUniverse'
import { useLearningStore, type TopicMastery } from '@/stores/learning'
import shortMessageIcon from '@/assets/icons/fang/short-message-svgrepo-com.svg'
import brushIcon from '@/assets/icons/blue/brush-svgrepo-com.svg'

const router = useRouter()
const learningStore = useLearningStore()
const canvasRef = ref<HTMLCanvasElement | null>(null)
const loaderContainer = ref<HTMLDivElement | null>(null)
let loaderAnim: AnimationItem | null = null
const showNodeLabel = ref(false)
let nodeLabelTimer: ReturnType<typeof setTimeout> | null = null

const {
  isReady,
  selectedNode,
  hoveredNode,
  isIdle,
  isWakingUp,
  init,
  focusNode,
  notifyProgress,
} = useUniverse(canvasRef, {
  knowledgeNodes: computed(() => learningStore.topicMasteryList),
})

const categoryColors: Record<string, { fill: string; bg: string; icon: string }> = {
  foundation: { fill: '#10b981', bg: 'rgba(16,185,129,0.15)', icon: '🟢' },
  core:       { fill: '#6366f1', bg: 'rgba(99,102,241,0.15)', icon: '🟣' },
  advanced:   { fill: '#06b6d4', bg: 'rgba(6,182,212,0.15)', icon: '🔵' },
}

function categoryName(c: string) {
  const map: Record<string, string> = { foundation: '基础模块', core: '核心模块', advanced: '进阶模块' }
  return map[c] || c
}

function nodeCatStyle(c: string) {
  return categoryColors[c] || categoryColors.advanced
}

function nodeStatusLabel(status: string) {
  const map: Record<string, string> = { mastered: '✨ 已掌握', learning: '🚀 学习中', locked: '🔒 待解锁' }
  return map[status] || status
}

function nodeStatusBadge(status: string) {
  switch (status) {
    case 'mastered': return { background: 'rgba(251,191,36,0.2)', color: '#fbbf24' }
    case 'learning': return { background: 'rgba(99,102,241,0.2)', color: '#818cf8' }
    default: return { background: 'rgba(100,116,139,0.2)', color: '#94a3b8' }
  }
}

function goToChat(node: TopicMastery) {
  router.push({ path: '/chat', query: { topic: node.name } })
}

function goToPractice(node: TopicMastery) {
  router.push({ path: '/practice', query: { topic: node.name } })
}

// Watch selected node → center label浮现
watch(selectedNode, (node) => {
  if (node) {
    showNodeLabel.value = true
    if (nodeLabelTimer) clearTimeout(nodeLabelTimer)
    nodeLabelTimer = setTimeout(() => { showNodeLabel.value = false }, 3000)
  } else {
    showNodeLabel.value = false
  }
})

// Watch learning progress changes → micro-feedback
let prevMasteryMap = new Map<string, number>()
watch(() => learningStore.topicMasteryList, (newList) => {
  for (const topic of newList) {
    const prev = prevMasteryMap.get(topic.topicId)
    if (prev !== undefined && Math.abs(prev - topic.masteryLevel) > 0.001) {
      notifyProgress(topic.topicId, prev, topic.masteryLevel)
    }
    prevMasteryMap.set(topic.topicId, topic.masteryLevel)
  }
}, { deep: true })

onMounted(async () => {
  // Start rocket loader animation
  if (loaderContainer.value) {
    loaderAnim = lottie.loadAnimation({
      container: loaderContainer.value,
      renderer: 'svg',
      loop: true,
      autoplay: true,
      path: '/assets/universe/rocket-loader.json',
    })
  }

  await learningStore.fetchTopicMastery()
  // Seed the mastery map to avoid false notifications on first load
  for (const topic of learningStore.topicMasteryList) {
    prevMasteryMap.set(topic.topicId, topic.masteryLevel)
  }
  await learningStore.fetchKnowledgeEdges()
  init()
})

onUnmounted(() => {
  if (loaderAnim) {
    loaderAnim.destroy()
    loaderAnim = null
  }
})
</script>

<style scoped>
.universe-view {
  /* Full-screen canvas container */
}

.glass-card {
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.6s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-panel-enter-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-panel-leave-active {
  transition: all 0.3s ease-in;
}
.slide-up-panel-enter-from {
  opacity: 0;
  transform: translate(-50%, 40px);
}
.slide-up-panel-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

.icon-btn {
  width: 1em;
  height: 1em;
  display: inline-block;
  vertical-align: middle;
}
</style>
