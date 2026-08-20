<template>
  <span class="knowledge-tag-wrapper relative inline-block">
    <span
      class="knowledge-tag inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-medium cursor-pointer transition-all duration-200 border"
      :class="tagClasses"
      @click.stop="showPopover = !showPopover"
      @mouseenter="onHover"
      @mouseleave="onLeave"
    >
      <span class="text-[10px]">{{ icon }}</span>
      <span>{{ name }}</span>
    </span>

    <!-- Popover -->
    <Teleport to="body">
      <div v-if="showPopover" class="fixed inset-0 z-[9998]" @click="showPopover = false" />
      <transition name="popover">
        <div
          v-if="showPopover"
          class="fixed z-[9999] w-64 p-4 rounded-2xl shadow-2xl border border-white/20"
          :style="popoverStyle"
          style="background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(20px);"
        >
          <!-- 箭头 -->
          <div class="absolute -top-2 left-6 w-4 h-4 rotate-45" style="background: rgba(15, 23, 42, 0.95);" />

          <div class="relative space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                :class="catBgClass">
                {{ icon }}
              </div>
              <div>
                <h4 class="text-sm font-bold text-white">{{ name }}</h4>
                <span class="text-xs px-1.5 py-0.5 rounded-full font-medium"
                  :class="statusBadgeClass">
                  {{ statusLabel }}
                </span>
              </div>
            </div>

            <!-- 掌握度 -->
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-400">掌握度</span>
                <span class="font-bold text-white">{{ Math.round((masteryLevel ?? 0) * 100) }}%</span>
              </div>
              <div class="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{ width: ((masteryLevel ?? 0) * 100) + '%', background: catFill }"
                />
              </div>
            </div>

            <!-- 快捷操作 -->
            <div class="flex gap-2 pt-1">
              <button
                v-if="status !== 'mastered'"
                class="flex-1 py-2 bg-brand-500 text-white rounded-lg text-xs font-medium hover:bg-brand-600 transition-colors"
                @click.stop="handleLearn"
              >
                <img :src="iconRocket" class="popover-action-icon" alt="" /> 开始学习
              </button>
              <button
                class="flex-1 py-2 border border-white/20 text-gray-300 rounded-lg text-xs font-medium hover:bg-white/10 transition-colors"
                @click.stop="handleExplore"
              >
                <img :src="iconThePlanet" class="popover-action-icon" alt="" /> 查看详情
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import iconRocket from '@/assets/icons/star/rocket-svgrepo-com.svg'
import iconThePlanet from '@/assets/icons/star/the-planet-svgrepo-com.svg'

const props = defineProps<{
  name: string
  topicId?: string
  masteryLevel?: number
  status?: string
  category?: string
}>()

const router = useRouter()
const showPopover = ref(false)
const tagRef = ref<HTMLElement | null>(null)
const popoverStyle = ref({ top: '0px', left: '0px' })

const categoryConfig: Record<string, { icon: string; bg: string; fill: string }> = {
  foundation: { icon: '🟢', bg: 'bg-mint-500/20', fill: '#10b981' },
  core: { icon: '🟣', bg: 'bg-brand-500/20', fill: '#6366f1' },
  advanced: { icon: '🔵', bg: 'bg-cyan-500/20', fill: '#06b6d4' },
}
const cat = computed(() => categoryConfig[props.category || ''] || categoryConfig.core)
const icon = computed(() => cat.value.icon)
const catBgClass = computed(() => cat.value.bg)
const catFill = computed(() => cat.value.fill)

const ml = computed(() => props.masteryLevel ?? 0)
const tagClasses = computed(() => {
  if (ml.value >= 0.85) return 'bg-mint-50 text-mint-700 border-mint-200 hover:bg-mint-100'
  if (ml.value > 0) return 'bg-brand-50 text-brand-700 border-brand-200 hover:bg-brand-100'
  return 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
})

const statusLabel = computed(() => {
  if (ml.value >= 0.85) return '✨ 已掌握'
  if (ml.value > 0) return '🚀 学习中'
  return '🔒 待解锁'
})

const statusBadgeClass = computed(() => {
  if (ml.value >= 0.85) return 'bg-mint-500/20 text-mint-400'
  if (ml.value > 0) return 'bg-brand-500/20 text-brand-400'
  return 'bg-gray-500/20 text-gray-400'
})

function onHover(e: MouseEvent) {
  // position the popover near the tag
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  popoverStyle.value = {
    top: (rect.bottom + 8) + 'px',
    left: Math.max(16, Math.min(rect.left - 100, window.innerWidth - 280)) + 'px',
  }
}

function onLeave() {
  // keep popover open on click, close on mouse leave if not clicked
}

function handleLearn() {
  showPopover.value = false
  router.push('/learning-path')
}

function handleExplore() {
  showPopover.value = false
  router.push('/knowledge-graph')
}
</script>

<style scoped>
.knowledge-tag-wrapper {
  vertical-align: middle;
}

.popover-action-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
  flex-shrink: 0;
}

.popover-enter-active { transition: all 0.2s ease-out; }
.popover-leave-active { transition: all 0.15s ease-in; }
.popover-enter-from { opacity: 0; transform: translateY(-4px) scale(0.95); }
.popover-leave-to { opacity: 0; transform: translateY(-2px) scale(0.97); }
</style>
