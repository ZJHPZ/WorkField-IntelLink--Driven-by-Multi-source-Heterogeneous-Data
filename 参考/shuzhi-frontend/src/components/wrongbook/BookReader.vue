<template>
  <div class="book-reader-root">
    <!-- 顶部导航 -->
    <header class="book-topbar">
      <button class="back-to-list" @click="$emit('close')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        <span>返回列表</span>
      </button>
      <span class="book-topic-name">{{ topicName }}</span>
      <div class="book-actions">
        <router-link :to="'/practice'" class="book-action-btn" title="练习此类题目">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14l-5 5-5-5"/><path d="M15 10l-5-5-5 5"/><line x1="10" y1="19" x2="10" y2="5"/></svg>
          练习
        </router-link>
        <router-link :to="'/chat'" class="book-action-btn" title="向AI老师提问">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          问AI
        </router-link>
        <button class="book-action-btn" title="错题自测" @click="showSelfTest = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="18" rx="2"/><line x1="6" y1="8" x2="18" y2="8"/><line x1="6" y1="12" x2="14" y2="12"/><line x1="6" y1="16" x2="10" y2="16"/></svg>
          自测
        </button>
      </div>
      <span class="book-page-indicator">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
        {{ pageIndex + 1 }} / {{ totalPages }}
      </span>
    </header>

    <!-- 翻书场景 -->
    <div class="book-stage" ref="stageRef"
      @touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd"
      @mousedown="onMouseDown">
      <div class="book" :class="{ 'is-flipping': isAnimating, 'flip-backward': flipDir === 'backward' }">
        <!-- 书脊阴影 -->
        <div class="book-spine" />

        <!-- ====== 左页：题目 ====== -->
        <div class="page page-left">
          <div class="page-inner">
            <!-- 标签行 -->
            <div class="p-tags">
              <span class="p-tag" :class="currentQuestion.source">
                {{ currentQuestion.source_label }}
              </span>
              <span class="p-difficulty" :class="currentQuestion.difficulty">
                {{ diffLabel(currentQuestion.difficulty) }}
              </span>
            </div>

            <!-- 题目内容 -->
            <div class="p-question" v-html="currentQuestion.content" />

            <!-- 选项 -->
            <div class="p-options" v-if="currentQuestion.options.length > 0">
              <div
                v-for="opt in currentQuestion.options"
                :key="opt.key"
                class="p-option"
                :class="{
                  'is-correct': opt.key === currentQuestion.correct_answer,
                  'is-wrong': opt.key === currentQuestion.user_answer && opt.key !== currentQuestion.correct_answer,
                }"
              >
                <span class="p-opt-key">{{ opt.key }}</span>
                <span class="p-opt-text">{{ opt.text }}</span>
              </div>
            </div>

            <!-- 装饰小元素 -->
            <img :src="iceCreamIcon" class="page-deco deco-left-top" alt="" />
            <img :src="polaroidIcon" class="page-deco deco-left-bot" alt="" />
          </div>
        </div>

        <!-- ====== 右页：答案对照 + 解析 ====== -->
        <div class="page page-right" ref="rightPageRef">
          <div class="page-inner">
            <!-- 你的答案 -->
            <div class="answer-section">
              <h4 class="section-title">
                <span class="section-icon wrong-icon">✗</span> 你的答案
              </h4>
              <div class="answer-display wrong-answer">
                {{ currentQuestion.user_answer || '(空)' }}
              </div>
            </div>

            <!-- 正确答案 -->
            <div class="answer-section">
              <h4 class="section-title">
                <span class="section-icon correct-icon">✓</span> 正确答案
              </h4>
              <div class="answer-display correct-answer">
                {{ currentQuestion.correct_answer }}
              </div>
            </div>

            <!-- 解析 -->
            <div class="explanation-section" v-if="currentQuestion.explanation">
              <h4 class="section-title">
                <span class="section-icon tip-icon">💡</span> 解析
              </h4>
              <div class="explanation-text" v-html="currentQuestion.explanation" />
            </div>

            <!-- 装饰 -->
            <img :src="coconutIcon" class="page-deco deco-right-top" alt="" />
          </div>
        </div>

        <!-- ====== 翻页动画层 ====== -->
        <div
          v-if="isAnimating"
          class="flip-overlay"
          :class="{ 'flip-forward': flipDir === 'forward', 'flip-backward': flipDir === 'backward' }"
        >
          <div class="flip-front">
            <div class="page-inner">
              <div class="flip-peek-label">{{ flipDir === 'forward' ? '正在翻页…' : '往回翻…' }}</div>
              <div class="flip-peek-hint" v-html="flipPeekContent" />
            </div>
          </div>
          <div class="flip-back">
            <div class="page-inner">
              <div class="flip-peek-label flip-next-label">{{ flipDir === 'forward' ? '即将看到' : '回到' }}</div>
              <div class="flip-peek-content" v-html="flipPeekNext" />
            </div>
          </div>
        </div>
      </div>

      <!-- 翻页热区按钮 -->
      <button class="nav-btn nav-prev" @click="flipBackward" :disabled="isAnimating || pageIndex <= 0" aria-label="上一题">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <button class="nav-btn nav-next" @click="flipForward" :disabled="isAnimating || pageIndex >= totalPages - 1" aria-label="下一题">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>

    <!-- 底部点状进度 -->
    <div class="book-dots">
      <button
        v-for="(q, i) in props.questions"
        :key="i"
        class="book-dot"
        :class="{
          active: i === pageIndex,
          reviewed: q.reviewed && i !== pageIndex,
        }"
        @click="goToPage(i)"
        :aria-label="`第 ${i + 1} 题${q.reviewed ? ' 已复习' : ''}`"
      />
    </div>

    <!-- 键盘提示 -->
    <div class="keyboard-hint">
      ← 键盘左右键翻页 →
    </div>

    <!-- 自测配置弹窗 -->
    <SelfTestModal
      :visible="showSelfTest"
      :topics="wrongBookStore.groups"
      @close="showSelfTest = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { WrongQuestionItem } from '@/stores/wrongBook'
import { useWrongBookStore } from '@/stores/wrongBook'
import SelfTestModal from '@/components/wrongbook/SelfTestModal.vue'
import iceCreamIcon from '@/assets/icons/summer/ice-cream-svgrepo-com.svg'
import polaroidIcon from '@/assets/icons/summer/polaroid-svgrepo-com.svg'
import coconutIcon from '@/assets/icons/summer/coconut-tree-svgrepo-com.svg'

const props = defineProps<{
  questions: WrongQuestionItem[]
  topicName: string
  initialPage?: number
}>()

const emit = defineEmits<{
  close: []
}>()

const wrongBookStore = useWrongBookStore()

const showSelfTest = ref(false)

const pageIndex = ref(props.initialPage ?? 0)
const isAnimating = ref(false)
const flipDir = ref<'forward' | 'backward'>('forward')
const stageRef = ref<HTMLElement | null>(null)

// Touch / drag state
let touchStartX = 0
let touchStartY = 0
let touchMoved = false

const totalPages = computed(() => props.questions.length)

const currentQuestion = computed(() =>
  props.questions[pageIndex.value] ?? props.questions[0] ?? ({} as WrongQuestionItem)
)

function diffLabel(d: string): string {
  const map: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' }
  return map[d] || d
}

// 翻页预览内容
const flipPeekContent = computed(() => {
  const q = currentQuestion.value
  if (!q || !q.content) return ''
  return q.content.length > 60 ? q.content.slice(0, 60) + '…' : q.content
})

const flipPeekNext = computed(() => {
  const targetIdx = flipDir.value === 'forward' ? pageIndex.value + 1 : pageIndex.value - 1
  const q = props.questions[targetIdx]
  if (!q || !q.content) return '（没有更多了）'
  return q.content.length > 60 ? q.content.slice(0, 60) + '…' : q.content
})

function flipForward() {
  if (isAnimating.value || pageIndex.value >= totalPages.value - 1) return
  flipDir.value = 'forward'
  isAnimating.value = true
  setTimeout(() => {
    pageIndex.value++
    isAnimating.value = false
  }, 450)
}

function flipBackward() {
  if (isAnimating.value || pageIndex.value <= 0) return
  flipDir.value = 'backward'
  isAnimating.value = true
  setTimeout(() => {
    pageIndex.value--
    isAnimating.value = false
  }, 450)
}

function goToPage(i: number) {
  if (isAnimating.value || i === pageIndex.value) return
  if (i < 0 || i >= totalPages.value) return
  flipDir.value = i > pageIndex.value ? 'forward' : 'backward'
  isAnimating.value = true
  setTimeout(() => {
    pageIndex.value = i
    isAnimating.value = false
  }, 450)
}

// Touch / swipe
function onTouchStart(e: TouchEvent) {
  if (isAnimating.value) return
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
  touchMoved = false
}

function onTouchMove(e: TouchEvent) {
  if (isAnimating.value) return
  const dx = e.touches[0].clientX - touchStartX
  const dy = e.touches[0].clientY - touchStartY
  if (Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) {
    touchMoved = true
    e.preventDefault()
  }
}

function onTouchEnd(e: TouchEvent) {
  if (isAnimating.value || !touchMoved) return
  const dx = e.changedTouches[0].clientX - touchStartX
  if (dx < -60) flipForward()
  else if (dx > 60) flipBackward()
}

// Mouse drag (desktop)
let mouseDown = false
let mouseStartX = 0

function onMouseDown(e: MouseEvent) {
  if (isAnimating.value) return
  mouseDown = true
  mouseStartX = e.clientX
}

function onMouseUp(e: MouseEvent) {
  if (!mouseDown || isAnimating.value) return
  mouseDown = false
  const dx = e.clientX - mouseStartX
  if (dx < -80) flipForward()
  else if (dx > 80) flipBackward()
}

// Keyboard
function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault()
    flipForward()
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault()
    flipBackward()
  }
}

// Watch initialPage changes
watch(() => props.initialPage, (v) => {
  if (v != null) pageIndex.value = v
})

// 翻页后自动标记当前题目为已复习
watch(pageIndex, () => {
  const q = props.questions[pageIndex.value]
  if (q && !q.reviewed) {
    wrongBookStore.markReviewed(q.question_id, q.source)
  }
})

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('mouseup', onMouseUp)
  // 标记初始页
  const q = props.questions[pageIndex.value]
  if (q && !q.reviewed) {
    wrongBookStore.markReviewed(q.question_id, q.source)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
/* ============================================================
   BookReader — K12 翻书模式
   使用 CSS 3D transforms 模拟真实翻页
   ============================================================ */

.book-reader-root {
  --c-mint:   #B4E8DD;
  --c-sky:    #B9E3F8;
  --c-cream:  #FFF6D9;
  --c-orange: #FFB957;
  --c-orange-deep: #FF8F38;
  --c-page:   #FFFEF8;
  --c-text:   #4A3020;
  --c-light:  #8B7355;

  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
  position: relative;
  overflow: hidden;
  min-height: 0;
}

/* ============================================================
   顶部导航
   ============================================================ */

.book-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: linear-gradient(180deg, rgba(180,232,221,0.95) 0%, rgba(180,232,221,0.7) 85%, transparent 100%);
  border-radius: 0 0 18px 18px;
  flex-shrink: 0;
  z-index: 10;
}

.back-to-list {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 16px;
  border: 1.5px solid rgba(255,255,255,0.5);
  background: rgba(255,255,255,0.6);
  color: #5A7A7A;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.back-to-list:hover {
  background: #fff;
  transform: translateX(-2px);
}

.book-topic-name {
  font-size: 15px;
  font-weight: 800;
  color: var(--c-text);
  text-shadow: 0 1px 0 rgba(255,255,255,0.5);
}

.book-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.book-action-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 4px 10px;
  border-radius: 14px;
  border: 1.5px solid rgba(255,255,255,0.5);
  background: rgba(255,255,255,0.6);
  color: #5A7A7A;
  font-size: 11px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.book-action-btn:hover {
  background: #fff;
  color: #4078B0;
}

.book-page-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  color: #6B5840;
  background: rgba(255,255,255,0.6);
  padding: 4px 10px;
  border-radius: 12px;
}

/* ============================================================
   书本主体舞台
   ============================================================ */

.book-stage {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  perspective: 1800px;
  perspective-origin: center center;
  padding: 10px 60px;
  min-height: 0;
}

/* ============================================================
   书本
   ============================================================ */

.book {
  width: 100%;
  max-width: 780px;
  aspect-ratio: 1.6;
  display: flex;
  position: relative;
  transform-style: preserve-3d;
  border-radius: 12px;
  box-shadow:
    6px 6px 24px rgba(0,0,0,0.08),
    2px 2px 8px rgba(0,0,0,0.04),
    inset 0 0 0 1px rgba(0,0,0,0.03);
}

/* 书脊 */
.book-spine {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 4px;
  transform: translateX(-50%);
  background: linear-gradient(90deg,
    rgba(0,0,0,0.03) 0%,
    rgba(0,0,0,0.06) 30%,
    rgba(0,0,0,0.08) 50%,
    rgba(0,0,0,0.04) 70%,
    rgba(0,0,0,0.01) 100%
  );
  z-index: 3;
  border-radius: 2px;
}

/* ============================================================
   书页
   ============================================================ */

.page {
  flex: 1;
  background: var(--c-page);
  position: relative;
  overflow: hidden;
  backface-visibility: hidden;
}

.page-left {
  border-radius: 12px 0 0 12px;
  border-right: none;
  box-shadow: inset -3px 0 6px rgba(0,0,0,0.02);
}

.page-right {
  border-radius: 0 12px 12px 0;
  box-shadow: inset 3px 0 6px rgba(0,0,0,0.02);
}

.page-inner {
  padding: 20px 22px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* ============================================================
   左页：题目内容
   ============================================================ */

.p-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.p-tag,
.p-difficulty {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 8px;
  line-height: 1.3;
}

.p-tag.exam       { background: #FFE8D0; color: #B06830; }
.p-tag.practice   { background: #D0E8FF; color: #4078B0; }

.p-difficulty.easy   { background: #C6EEDC; color: #408060; }
.p-difficulty.medium { background: #FFF0C8; color: #A08830; }
.p-difficulty.hard   { background: #FFD8D8; color: #C05050; }

.p-question {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
  line-height: 1.75;
  flex: 1;
}

.p-options {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: auto;
  padding-top: 10px;
}

.p-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 10px;
  border: 1.5px solid #E6DDD2;
  background: #FFFEFA;
  transition: all 0.15s;
}

.p-option.is-correct {
  border-color: #80D880;
  background: #F0FFF0;
}

.p-option.is-wrong {
  border-color: #F08080;
  background: #FFF0F0;
}

.p-opt-key {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.5px solid #D5CDC0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--c-light);
  flex-shrink: 0;
}

.is-correct .p-opt-key {
  border-color: #60B060;
  background: #E0FFE0;
  color: #408040;
}

.is-wrong .p-opt-key {
  border-color: #E06060;
  background: #FFE0E0;
  color: #C04040;
}

.p-opt-text {
  font-size: 13px;
  color: var(--c-text);
  line-height: 1.4;
}

/* ============================================================
   右页：答案对照 + 解析
   ============================================================ */

.answer-section {
  margin-bottom: 10px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--c-light);
  margin-bottom: 5px;
}

.section-icon {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

.wrong-icon {
  background: #FFE0E0;
  color: #D04040;
}

.correct-icon {
  background: #E0FFE0;
  color: #40A040;
}

.tip-icon {
  font-size: 13px;
}

.answer-display {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  word-break: break-all;
}

.wrong-answer {
  background: #FFF5F5;
  border: 1.5px solid #F0C0C0;
  color: #C04040;
}

.correct-answer {
  background: #F5FFF5;
  border: 1.5px solid #C0E0C0;
  color: #40A040;
}

.explanation-section {
  margin-top: auto;
  padding-top: 8px;
}

.explanation-text {
  padding: 10px 14px;
  border-radius: 10px;
  background: #FFFEFA;
  border: 1px dashed #E6DDC0;
  font-size: 12px;
  color: #8B7355;
  line-height: 1.6;
}

/* ============================================================
   翻页动画层
   ============================================================ */

.flip-overlay {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 50%;
  transform-origin: left center;
  transform-style: preserve-3d;
  z-index: 5;
  border-radius: 0 12px 12px 0;
}

.flip-overlay.flip-forward {
  animation: pageFlipForward 0.5s ease-in-out forwards;
}

.flip-overlay.flip-backward {
  animation: pageFlipBackward 0.5s ease-in-out forwards;
  transform: rotateY(-170deg);
}

.flip-front,
.flip-back {
  position: absolute;
  inset: 0;
  background: var(--c-page);
  backface-visibility: hidden;
  border-radius: 0 12px 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flip-front {
  box-shadow: inset 3px 0 6px rgba(0,0,0,0.02);
}

.flip-back {
  transform: rotateY(180deg);
  box-shadow: inset -3px 0 6px rgba(0,0,0,0.03);
}

.flip-peek-label {
  font-size: 10px;
  font-weight: 700;
  color: #B5A898;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.flip-peek-label.flip-next-label {
  color: #6B8FB0;
}

.flip-peek-hint,
.flip-peek-content {
  font-size: 13px;
  color: #8B7355;
  line-height: 1.6;
  opacity: 0.75;
}

.flip-peek-content {
  color: #5C4030;
  opacity: 0.85;
  font-weight: 500;
}

@keyframes pageFlipForward {
  0%   { transform: rotateY(0deg); }
  100% { transform: rotateY(-170deg); }
}

@keyframes pageFlipBackward {
  0%   { transform: rotateY(-170deg); }
  100% { transform: rotateY(0deg); }
}

/* ============================================================
   翻页按钮
   ============================================================ */

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1.5px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.85);
  color: #8B7355;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 8;
  backdrop-filter: blur(4px);
}

.nav-btn:hover:not(:disabled) {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  transform: translateY(-50%) scale(1.08);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.nav-prev { left: 8px; }

.nav-next { right: 8px; }

/* ============================================================
   底部点状进度
   ============================================================ */

.book-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  padding: 8px 0 2px;
  flex-shrink: 0;
}

.book-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background: #D5C8B5;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.book-dot.active {
  background: #5298D1;
  width: 22px;
  border-radius: 4px;
}

.book-dot.reviewed {
  background: #6BC070;
}

.book-dot:hover:not(.active) {
  background: #B5A890;
}

/* ============================================================
   键盘提示
   ============================================================ */

.keyboard-hint {
  text-align: center;
  font-size: 10px;
  color: #B5A898;
  padding: 4px 0 6px;
  flex-shrink: 0;
  opacity: 0.6;
}

/* ============================================================
   页面装饰
   ============================================================ */

.page-deco {
  position: absolute;
  pointer-events: none;
  user-select: none;
  opacity: 0.3;
}

.deco-left-top { top: 8px; right: 10px; width: 24px; height: 24px; }
.deco-left-bot { bottom: 8px; left: 10px; width: 20px; height: 20px; opacity: 0.25; }
.deco-right-top { top: 8px; right: 10px; width: 22px; height: 22px; }

/* ============================================================
   响应式
   ============================================================ */

@media (max-width: 640px) {
  .book-stage {
    padding: 4px 44px;
  }

  .book {
    aspect-ratio: auto;
    flex-direction: column;
    max-height: none;
  }

  .page-left {
    border-radius: 12px 12px 0 0;
    flex: 0 0 auto;
    min-height: 45%;
  }

  .page-right {
    border-radius: 0 0 12px 12px;
    flex: 1;
  }

  .book-spine {
    left: 0;
    right: 0;
    top: 50%;
    bottom: auto;
    width: 100%;
    height: 3px;
    transform: translateY(-50%);
  }

  .page-inner {
    padding: 14px 16px;
  }

  .nav-btn {
    width: 34px;
    height: 34px;
  }

  .book-topic-name {
    font-size: 13px;
  }

  .flip-overlay {
    left: 0;
    right: 0;
    top: 50%;
    bottom: 0;
    width: 100%;
    transform-origin: top center;
  }

  .flip-overlay.flip-forward {
    animation: pageFlipDown 0.45s ease-in-out forwards;
  }

  .flip-overlay.flip-backward {
    animation: pageFlipUp 0.45s ease-in-out forwards;
  }

  .flip-front,
  .flip-back {
    border-radius: 0 0 12px 12px;
  }

  .flip-back {
    transform: rotateX(180deg);
  }
}

@keyframes pageFlipDown {
  0%   { transform: rotateX(0deg); }
  100% { transform: rotateX(-170deg); }
}

@keyframes pageFlipUp {
  0%   { transform: rotateX(-170deg); }
  100% { transform: rotateX(0deg); }
}
</style>
