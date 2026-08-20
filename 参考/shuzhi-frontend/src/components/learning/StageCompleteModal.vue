<template>
  <Teleport to="body">
    <transition name="modal">
      <div v-if="visible" class="fixed inset-0 z-[10000] flex items-center justify-center" @click.self="close">
        <!-- 半透明遮罩 -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        <!-- 彩纸全屏 -->
        <div class="absolute inset-0 pointer-events-none overflow-hidden">
          <div v-for="c in confetti" :key="c.id"
            class="absolute rounded-sm"
            :style="{
              width: c.size + 'px',
              height: c.size * 0.6 + 'px',
              backgroundColor: c.color,
              top: c.startY + '%',
              left: c.startX + '%',
              animation: `confetti-fall ${c.duration}s ${c.delay}s ease-out forwards`,
              transform: `rotate(${c.rotation}deg)`,
            }" />
        </div>

        <!-- 弹窗内容 -->
        <div class="relative z-10 glass-card-dark rounded-3xl p-8 max-w-md w-full mx-4 text-center shadow-2xl border border-white/10 animate-scale-in">
          <!-- 庆祝图标 -->
          <div class="relative mb-6">
            <div class="w-20 h-20 mx-auto rounded-full flex items-center justify-center text-5xl animate-bounce-in"
              style="background: linear-gradient(135deg, #6366f1, #a855f7, #06b6d4);">
              <img :src="icon" class="complete-icon" alt="" />
            </div>
            <!-- 光爆粒子环 -->
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full animate-glow-pulse-strong pointer-events-none"
              style="box-shadow: 0 0 40px rgba(99,102,241,0.6), 0 0 80px rgba(6,182,212,0.4);" />
          </div>

          <!-- 标题 -->
          <h2 class="text-2xl font-bold text-white mb-2">{{ title }}</h2>
          <p class="text-gray-400 text-sm mb-6">{{ description }}</p>

          <!-- 获得的奖励 -->
          <div v-if="rewards.length" class="grid grid-cols-3 gap-3 mb-6">
            <div v-for="r in rewards" :key="r.label"
              class="bg-white/10 rounded-xl p-3 text-center">
              <div class="text-2xl mb-1">{{ r.icon }}</div>
              <div class="text-lg font-bold text-white">{{ r.value }}</div>
              <div class="text-[10px] text-gray-400">{{ r.label }}</div>
            </div>
          </div>

          <!-- 按钮 -->
          <div class="flex gap-3">
            <button @click="handleNext"
              class="flex-1 py-3 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98]">
              {{ primaryAction }}
            </button>
            <button @click="close"
              class="flex-1 py-3 border border-white/20 text-gray-300 rounded-xl font-medium text-sm hover:bg-white/10 transition-colors">
              继续学习
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePetStore } from '@/stores/pet'
import iconTrophy from '@/assets/icons/blue/trophy-svgrepo-com.svg'

const props = withDefaults(defineProps<{
  visible?: boolean
  title?: string
  description?: string
  icon?: string
  primaryAction?: string
  nextRoute?: string
  rewards?: Array<{ icon: string; value: string; label: string }>
}>(), {
  visible: false,
  title: '阶段完成！',
  description: '你完成了一个学习阶段，离目标又近了一步',
  icon: iconTrophy,
  primaryAction: '进入下一阶段',
  nextRoute: '/learning-path',
  rewards: () => [],
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'next'): void
}>()

const router = useRouter()

const confetti = Array.from({ length: 40 }, (_, i) => ({
  id: i,
  size: 6 + Math.random() * 10,
  color: ['#6366f1', '#a855f7', '#06b6d4', '#f59e0b', '#10b981', '#f43f5e', '#ec4899'][i % 7],
  startX: Math.random() * 100,
  startY: -10 - Math.random() * 20,
  duration: 1.5 + Math.random() * 2.5,
  delay: Math.random() * 0.8,
  rotation: Math.random() * 360,
}))

watch(() => props.visible, (v) => {
  if (v) {
    const petStore = usePetStore()
    petStore.celebrate(`太厉害了！${props.title} 🎉`)
  }
})

function handleNext() {
  emit('next')
  if (props.nextRoute) {
    router.push(props.nextRoute)
  }
}

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-enter-active { transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.modal-leave-active { transition: all 0.25s ease-in; }
.modal-enter-from { opacity: 0; }
.modal-enter-from > div:last-child { opacity: 0; transform: scale(0.85) translateY(20px); }
.modal-leave-to { opacity: 0; }
.modal-leave-to > div:last-child { opacity: 0; transform: scale(0.9); }

.complete-icon {
  width: 2em;
  height: 2em;
}
</style>
