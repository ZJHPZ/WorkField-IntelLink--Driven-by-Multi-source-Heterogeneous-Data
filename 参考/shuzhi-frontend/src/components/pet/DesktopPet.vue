<template>
  <div
    v-if="petStore.isVisible"
    ref="petWrapper"
    class="fixed z-[9999] select-none"
    :class="petStore.isDragging ? 'cursor-grabbing' : 'cursor-grab'"
    :style="wrapperStyle"
    @mousedown.prevent="onDragStart"
    @touchstart.prevent="onDragStart"
    @click.stop="onPetClick"
    @dblclick="onPetDblClick"
  >
    <!-- 对话框气泡 -->
    <PetBubble
      v-if="petStore.bubbleMessage"
      :message="petStore.bubbleMessage.text"
      :buttons="petStore.bubbleMessage.buttons"
      :pet-name="petStore.petName"
      @action="petStore.handleAlertAction"
      @dismiss="petStore.dismissBubble"
    />

    <!-- Lottie 动画容器 -->
    <div
      ref="lottieContainer"
      class="relative transition-transform duration-300"
      :class="animationClass"
      :style="{ width: petStore.size + 'px', height: petStore.size + 'px' }"
    />

    <!-- 彩纸庆祝粒子 -->
    <div v-if="showConfetti" class="absolute inset-0 pointer-events-none overflow-visible" style="top: -60px; left: -40px; width: 200px; height: 200px;">
      <div v-for="c in confettiPieces" :key="c.id"
        class="confetti-piece absolute rounded-sm"
        :style="{
          width: c.size + 'px',
          height: c.size * 0.6 + 'px',
          backgroundColor: c.color,
          top: (50 + c.startX) + '%',
          left: (50 + c.startY) + '%',
          animationDelay: c.delay + 's',
          animationDuration: c.duration + 's',
        }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import lottie, { type AnimationItem } from 'lottie-web'
import { usePetStore } from '@/stores/pet'
import { useLearningStore } from '@/stores/learning'
import PetBubble from './PetBubble.vue'

const petStore = usePetStore()
const learningStore = useLearningStore()
const route = useRoute()

const petWrapper = ref<HTMLElement | null>(null)
const lottieContainer = ref<HTMLElement | null>(null)

let animInstance: AnimationItem | null = null
let restTimer: ReturnType<typeof setInterval> | null = null
let idleTimer: ReturnType<typeof setTimeout> | null = null

// 拖拽状态
const dragStart = ref({ x: 0, y: 0, petX: 0, petY: 0 })
const hasDragged = ref(false)

// 动画样式
const animationClass = computed(() => {
  switch (petStore.currentState) {
    case 'active':   return 'scale-110 animate-bounce-small'
    case 'celebrate': return 'scale-125 animate-bounce'
    case 'sleeping':  return 'scale-90 opacity-75'
    default:          return 'hover:scale-105'
  }
})

// 定位样式：右下角 + 偏移
const wrapperStyle = computed(() => {
  const { x, y } = petStore.position
  return {
    right: Math.max(0, x) + 'px',
    bottom: Math.max(0, y) + 'px',
  }
})

// ===== 拖拽处理 =====
function onDragStart(e: MouseEvent | TouchEvent) {
  const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
  const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
  dragStart.value = {
    x: clientX,
    y: clientY,
    petX: petStore.position.x,
    petY: petStore.position.y,
  }
  hasDragged.value = false
  petStore.isDragging = true

  const onMove = (ev: MouseEvent | TouchEvent) => {
    const cx = 'touches' in ev ? ev.touches[0].clientX : ev.clientX
    const cy = 'touches' in ev ? ev.touches[0].clientY : ev.clientY
    const dx = cx - dragStart.value.x
    const dy = cy - dragStart.value.y
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
      hasDragged.value = true
    }
    const viewportW = window.innerWidth
    const viewportH = window.innerHeight
    petStore.setPosition(
      Math.max(0, Math.min(dragStart.value.petX - dx, viewportW - petStore.size - 20)),
      Math.max(0, Math.min(dragStart.value.petY + dy, viewportH - petStore.size - 20)),
    )
  }

  const onUp = () => {
    petStore.isDragging = false
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

// ===== 点击处理 =====
function onPetClick() {
  if (hasDragged.value) return
  petStore.interact()
}

function onPetDblClick() {
  petStore.celebrate('帕克被双击了！好开心~ 🐱')
}

// ===== Lottie 动画控制 =====
function loadAnimation(reload = false) {
  if (!lottieContainer.value) return
  const config = petStore.currentConfig
  if (!config) return

  // 路径相同不重复加载
  if (!reload && currentAssetPath === config.assetPath && animInstance) return
  currentAssetPath = config.assetPath

  // 销毁旧实例
  if (animInstance) {
    animInstance.destroy()
    animInstance = null
  }

  animInstance = lottie.loadAnimation({
    container: lottieContainer.value,
    renderer: 'svg',
    loop: true,
    autoplay: true,
    path: config.assetPath,
  })

  animInstance.setSpeed(0.6)
}

function playStateSegments() {
  if (!animInstance) return
  const config = petStore.currentConfig
  if (!config) return

  let speed = 0.6

  switch (petStore.currentState) {
    case 'active':
      speed = 1.2
      animInstance.playSegments([config.activeSegments[0], config.activeSegments[1]], true)
      break
    case 'alert':
      speed = 1.0
      animInstance.playSegments([config.alertSegments[0], config.alertSegments[1]], true)
      break
    case 'celebrate':
      speed = 2.0
      animInstance.playSegments([config.activeSegments[0], config.activeSegments[1]], true)
      break
    case 'sleeping':
      speed = 0.25
      animInstance.playSegments([config.idleSegments[0], config.idleSegments[1]], true)
      break
    default:
      speed = 0.6
      animInstance.playSegments([config.idleSegments[0], config.idleSegments[1]], true)
  }

  animInstance.setSpeed(speed)
}

// 彩纸庆祝
const showConfetti = ref(false)
const confettiPieces = ref<Array<{ id: number; size: number; color: string; startX: number; startY: number; delay: number; duration: number }>>([])

function triggerConfetti() {
  const colors = ['#6366f1', '#a855f7', '#06b6d4', '#f59e0b', '#10b981', '#f43f5e', '#ec4899', '#3b82f6']
  confettiPieces.value = Array.from({ length: 24 }, (_, i) => ({
    id: i,
    size: 6 + Math.random() * 8,
    color: colors[i % colors.length],
    startX: (Math.random() - 0.5) * 40,
    startY: (Math.random() - 0.5) * 20,
    delay: Math.random() * 0.3,
    duration: 1 + Math.random() * 1.5,
  }))
  showConfetti.value = true
  setTimeout(() => { showConfetti.value = false }, 2000)
}

// 记录当前动画路径，用于恢复
let currentAssetPath = ''

// ===== 休息提醒定时器 =====
function startRestTimer() {
  restTimer = setInterval(() => {
    // 从 learningStore 同步学习时间
    petStore.tickLearning(1)
    if (petStore.shouldRest) {
      petStore.triggerAlert()
    }
    // 空闲检测
    if (petStore.shouldSleep && petStore.currentState === 'idle') {
      petStore.setState('sleeping')
    }
  }, 60_000) // 每分钟检查一次
}

// ===== 路由感知 =====
watch(() => route.path, (path) => {
  if (petStore.currentState === 'alert' || petStore.currentState === 'celebrate') return

  if (path.includes('knowledge') || path.includes('graph')) {
    petStore.setState('idle')
    if (Math.random() > 0.6) {
      petStore.showBubble({ text: '这片星云里有好多知识点，一起探索吧！🌟', duration: 4000 })
    }
  } else if (path.includes('chat')) {
    petStore.setState('idle')
  } else if (path.includes('learning') || path.includes('path')) {
    petStore.setState('active')
  } else if (path.includes('profile')) {
    petStore.setState('sleeping')
  } else if (path.includes('practice')) {
    petStore.setState('active')
    petStore.showBubble({ text: '做题时间到！帕克在旁边给你加油~', duration: 3500 })
  }
})

// 监听状态变化 → 切换动画 + 庆祝彩纸
watch(() => petStore.currentState, (newState) => {
  playStateSegments()
  if (newState === 'celebrate') {
    triggerConfetti()
  }
})

// 监听宠物切换
watch(() => petStore.currentPet, () => {
  loadAnimation(true)
  setTimeout(() => playStateSegments(), 200)
})

// ===== 生命周期 =====
onMounted(() => {
  loadAnimation()
  startRestTimer()

  // 初始问候
  setTimeout(() => {
    const hour = new Date().getHours()
    let greeting = '你好！我是帕克，很高兴认识你~ 🐱'
    if (hour < 9) greeting = '早上好！帕克陪你开启元气满满的一天~ ☀️'
    else if (hour < 12) greeting = '上午好！学习的最佳时间，一起加油！📚'
    else if (hour < 14) greeting = '中午好！别忘了吃饭休息哦~ 🍱'
    else if (hour < 18) greeting = '下午好！帕克陪你度过高效学习时光~ ✨'
    else if (hour < 22) greeting = '晚上好！温故知新，帕克陪着你~ 🌙'
    else greeting = '夜深了…别熬太晚，帕克会担心的~ 😴'
    petStore.showBubble({ text: greeting, duration: 5000 })
  }, 1500)
})

onUnmounted(() => {
  if (animInstance) {
    animInstance.destroy()
    animInstance = null
  }
  if (restTimer) {
    clearInterval(restTimer)
    restTimer = null
  }
  if (idleTimer) {
    clearTimeout(idleTimer)
    idleTimer = null
  }
})
</script>

<style scoped>
@keyframes bounce-small {
  0%, 100% { transform: translateY(0) scale(1.1); }
  50% { transform: translateY(-6px) scale(1.1); }
}

.animate-bounce-small {
  animation: bounce-small 0.6s ease-in-out infinite;
}
</style>
