<template>
  <Teleport to="body">
    <Transition name="star-fade">
      <div v-if="visible" class="fixed inset-0 z-40" style="background: rgba(0,0,0,0.4);" @click="$emit('close')" />
    </Transition>

    <Transition name="star-slide">
      <aside
        v-if="visible"
        class="fixed top-0 right-0 h-full w-[400px] z-50 flex flex-col shadow-2xl overflow-hidden"
        :style="{ background: 'rgba(8,8,24,0.96)', borderLeft: '1px solid rgba(99,102,241,0.2)', color: 'var(--text-primary)' }"
      >
        <!-- 标题栏 -->
        <div class="flex items-center justify-between px-5 py-4 shrink-0" :style="{ borderBottom: '1px solid rgba(99,102,241,0.12)' }">
          <div class="flex items-center gap-2">
            <img :src="iconGalaxy" class="profile-panel-icon" alt="" />
            <div>
              <h2 class="text-base font-bold">学习星图</h2>
            </div>
          </div>
          <button class="text-gray-400 hover:text-white transition-colors text-lg leading-none" @click="$emit('close')">✕</button>
        </div>

        <!-- 星图舞台: 3D / 2D 双模切换 -->
        <div class="relative shrink-0">
          <!-- 视图切换按钮 -->
          <div class="absolute top-3 right-3 z-10 flex rounded-lg overflow-hidden"
            style="background: rgba(8,8,24,0.7); border: 1px solid rgba(99,102,241,0.15);">
            <button
              class="px-2.5 py-1.5 text-[10px] font-semibold transition-all"
              :style="viewMode === '3d'
                ? { background: 'rgba(99,102,241,0.25)', color: '#a5b4fc' }
                : { color: 'rgba(255,255,255,0.4)' }"
              @click="viewMode = '3d'"
            >3D 星座</button>
            <button
              class="px-2.5 py-1.5 text-[10px] font-semibold transition-all"
              :style="viewMode === '2d'
                ? { background: 'rgba(99,102,241,0.25)', color: '#a5b4fc' }
                : { color: 'rgba(255,255,255,0.4)' }"
              @click="viewMode = '2d'"
            >2D 星盘</button>
          </div>

          <!-- 3D 星座 -->
          <ProfileStar3D
            v-if="viewMode === '3d'"
            :dimensions="dimensions"
            :hovered-star="hoveredStar"
            @hover-star="hoveredStar = $event"
            @focus-dimension="focusDimension"
          />
          <!-- 2D 星盘 -->
          <ProfileStar2D
            v-else
            :dimensions="dimensions"
            :hovered-star="hoveredStar"
            @hover-star="hoveredStar = $event"
            @focus-dimension="focusDimension"
          />
        </div>

        <!-- 底部: AI 星舰日志 + 维度条 -->
        <div class="flex-1 overflow-y-auto px-5 py-4 space-y-4" ref="detailPanel">
          <!-- AI 星舰日志 -->
          <div v-if="aiSummary" class="rounded-2xl p-4" :style="{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.08)' }">
            <div class="flex items-start gap-3">
              <img :src="iconRadioStation" class="profile-panel-icon-sm" alt="" />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <p class="text-xs font-semibold" style="color: var(--brand-400);">星舰日志</p>
                  <button
                    class="text-[10px] px-2 py-0.5 rounded-full transition-all"
                    style="background: rgba(99,102,241,0.1); color: var(--brand-400); border: 1px solid rgba(99,102,241,0.15);"
                    :disabled="feedbackLoading"
                    @click="$emit('refreshFeedback')"
                    title="让智能体重新分析你的画像"
                  >
                    <span v-if="feedbackLoading" class="feedback-spinner"></span>
                    {{ feedbackLoading ? '分析中...' : '↻ 刷新' }}
                  </button>
                </div>
                <p class="text-xs leading-relaxed" style="color: var(--text-secondary);">{{ aiSummary }}</p>
              </div>
            </div>
          </div>

          <!-- 维度恒星详情 -->
          <div class="space-y-2">
            <h3 class="text-[11px] font-semibold uppercase tracking-wider" style="color: var(--text-muted);">维度恒星</h3>
            <div
              v-for="d in dimensions" :key="d.key"
              :data-dim="d.key"
              class="flex items-center gap-3 p-2.5 rounded-xl transition-all duration-400"
              :class="{ 'flash-bar': flashKey === d.key }"
              :style="dimBarStyle(d)"
              @mouseenter="hoveredStar = d.key"
              @mouseleave="hoveredStar = null"
            >
              <div class="w-3 h-3 rounded-full shrink-0 transition-all duration-400" :style="{
                background: `radial-gradient(circle, ${d.color}, ${d.color}44)`,
                boxShadow: hoveredStar === d.key ? `0 0 ${8 + d.value / 15}px ${d.color}` : `0 0 ${4 + d.value / 25}px ${d.color}`,
              }"></div>
              <span class="text-sm flex-1" style="color: var(--text-primary);">{{ d.label }}</span>
              <div class="flex-1 h-1.5 rounded-full overflow-hidden mx-2" style="background: rgba(99,102,241,0.06);">
                <div class="h-full rounded-full transition-all duration-700" :style="{ width: d.value + '%', backgroundColor: d.color }" />
              </div>
              <span class="text-sm font-bold tabular-nums w-8 text-right" :style="{ color: d.color }">{{ d.value }}</span>
              <span class="text-xs font-bold tabular-nums w-8 text-right"
                :style="{ color: trendColor(d) }">
                {{ trendArrow(d) }}{{ Math.abs(d.value - d.previousValue) }}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import type { ProfileDimension } from '@/stores/profileModeling'
import ProfileStar3D from './ProfileStar3D.vue'
import ProfileStar2D from './ProfileStar2D.vue'
import iconGalaxy from '@/assets/icons/star/galaxy-svgrepo-com.svg'
import iconRadioStation from '@/assets/icons/fang/radio-station-svgrepo-com.svg'

const props = defineProps<{
  visible: boolean
  dimensions: ProfileDimension[]
  aiSummary: string
  lastUpdated: string
  feedbackLoading?: boolean
}>()

defineEmits<{ close: []; refreshFeedback: [] }>()

// ── 视图模式 ──
const viewMode = ref<'3d' | '2d'>('3d')

// ── 交互状态 (跨组件共享) ──
const hoveredStar = ref<string | null>(null)
const flashKey = ref<string | null>(null)
const detailPanel = ref<HTMLElement | null>(null)

// ── 点击星/节点 → 滚动到维度条 ──
async function focusDimension(key: string) {
  await nextTick()
  const el = (detailPanel.value as HTMLElement | null)?.querySelector(`[data-dim="${key}"]`) as HTMLElement | null
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    flashKey.value = key
    setTimeout(() => { flashKey.value = null }, 1500)
  }
}

// ── 维度条样式 ──
function dimBarStyle(d: ProfileDimension) {
  const isHovered = hoveredStar.value === d.key
  return {
    background: isHovered ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.02)',
    border: isHovered ? `1px solid ${d.color}33` : '1px solid transparent',
  }
}

// ── 趋势 ──
function trendColor(d: ProfileDimension): string {
  return d.value - d.previousValue > 2 ? 'var(--mint-500)' : d.value - d.previousValue < -2 ? 'var(--rose-500)' : 'var(--text-muted)'
}

function trendArrow(d: ProfileDimension): string {
  return d.value - d.previousValue > 2 ? '↑' : d.value - d.previousValue < -2 ? '↓' : '→'
}

const timeAgo = computed(() => {
  if (!props.lastUpdated) return ''
  const diff = Date.now() - new Date(props.lastUpdated).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  return `${Math.floor(hours / 24)} 天前`
})
</script>

<style scoped>
.star-fade-enter-active { transition: opacity 0.3s ease; }
.star-fade-leave-active { transition: opacity 0.25s ease; }
.star-fade-enter-from,
.star-fade-leave-to { opacity: 0; }

.star-slide-enter-active { transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.star-slide-leave-active { transition: transform 0.25s ease-in; }
.star-slide-enter-from,
.star-slide-leave-to { transform: translateX(100%); }

@keyframes bar-flash {
  0%, 100% { box-shadow: 0 0 0px transparent; border-color: transparent; }
  50% { box-shadow: 0 0 14px var(--bar-color, transparent); border-color: var(--bar-color, transparent); }
}

.flash-bar {
  --bar-color: currentColor;
  animation: bar-flash 1.5s ease-in-out;
}

.profile-panel-icon {
  width: 1.25em;
  height: 1.25em;
  display: inline-block;
}

.profile-panel-icon-sm {
  width: 1em;
  height: 1em;
  display: inline-block;
  flex-shrink: 0;
}

.feedback-spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(99,102,241,0.3);
  border-right-color: var(--brand-400);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 2px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
