<template>
  <aside class="summer-sidebar">
    <!-- 标题 -->
    <div class="sidebar-header">
      <img :src="surfIcon" class="header-icon-img" alt="" />
      <h2 class="header-title">暑假错题<br>打卡手册</h2>
      <img :src="iceCreamIcon" class="header-icon-img" alt="" />
    </div>

    <!-- 4 张便签统计卡 -->
    <div class="sticky-notes">
      <div class="sticky-note note-pink">
        <span class="note-emoji">❌</span>
        <span class="note-value">{{ totalWrong }}</span>
        <span class="note-label">总错题数</span>
        <div class="note-tape" />
      </div>
      <div class="sticky-note note-mint">
        <span class="note-emoji">✅</span>
        <span class="note-value">{{ reviewedCount }}</span>
        <span class="note-label">已复习</span>
        <div class="note-tape" />
      </div>
      <div class="sticky-note note-lavender">
        <span class="note-emoji">📊</span>
        <span class="note-value">{{ totalTopics }}</span>
        <span class="note-label">涉及知识点</span>
        <div class="note-tape" />
      </div>
      <div class="sticky-note note-purple">
        <span class="note-emoji">📈</span>
        <span class="note-value">{{ masterRate }}%</span>
        <span class="note-label">掌握率</span>
        <div class="note-tape" />
      </div>
    </div>

    <!-- 夏日闯关进度 -->
    <div class="progress-section">
      <div class="progress-header">
        <img :src="surfIcon" class="progress-icon-img" alt="" />
        <span class="progress-title">夏日闯关进度</span>
      </div>
      <!-- 沙滩小路进度条 -->
      <div class="beach-path">
        <div class="beach-track">
          <div class="beach-fill" :style="{ width: reviewProgress + '%' }">
            <span class="beach-runner">🐚</span>
          </div>
          <div class="beach-dots">
            <span v-for="i in 5" :key="i" class="beach-dot" :class="{ reached: (i / 5) * 100 <= reviewProgress }">🪨</span>
          </div>
        </div>
        <span class="beach-goal"><img :src="cocktailIcon" class="goal-icon" alt="" /> 西瓜勋章</span>
      </div>
      <p class="progress-text">{{ reviewProgress >= 100 ? '🎉 全部通关！' : `已复习 ${reviewedCount}/${totalWrong} 道错题` }}</p>
    </div>

    <!-- IP 机器人（夏日限定版） -->
    <div class="robot-corner">
      <div class="robot-figure">
        <div class="robot-body">
          <div class="robot-hat">🧢</div>
          <div class="robot-face">
            <span class="robot-eye left" />
            <span class="robot-eye right" />
            <span class="robot-mouth" />
          </div>
        </div>
        <div class="robot-shadow" />
      </div>
      <span class="robot-bubble">加油！</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import surfIcon from '@/assets/icons/summer/surf-svgrepo-com.svg'
import cocktailIcon from '@/assets/icons/summer/cocktail-svgrepo-com.svg'
import iceCreamIcon from '@/assets/icons/summer/ice-cream-svgrepo-com.svg'

const props = defineProps<{
  totalWrong: number
  reviewedCount: number
  totalTopics: number
  masterRate: number
}>()

const reviewProgress = computed(() => {
  if (props.totalWrong === 0) return 0
  return Math.round((props.reviewedCount / props.totalWrong) * 100)
})
</script>

<style scoped>
.summer-sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  background: linear-gradient(180deg,
    rgba(255,246,217,0.5) 0%,
    rgba(255,246,217,0.25) 40%,
    rgba(180,232,221,0.15) 70%,
    rgba(180,232,221,0.1) 100%);
  border-right: 1px solid rgba(180,200,190,0.25);
  overflow-y: auto;
  gap: 16px;
  height: 100%;
}

/* ======= 标题 ======= */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding-bottom: 8px;
  border-bottom: 1.5px dashed #E0D5C0;
}

.header-icon-img {
  width: 28px;
  height: 28px;
  animation: wiggle 2s ease-in-out infinite;
}

.header-icon-img:last-child {
  animation-delay: 0.5s;
}

@keyframes wiggle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-8deg); }
  75% { transform: rotate(8deg); }
}

.header-title {
  font-size: 15px;
  font-weight: 900;
  color: #5C4030;
  text-align: center;
  line-height: 1.3;
  letter-spacing: 1px;
}

/* ======= 便签卡片 ======= */
.sticky-notes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sticky-note {
  position: relative;
  padding: 10px 10px 8px;
  border-radius: 3px 12px 3px 12px;
  text-align: center;
  box-shadow: 1px 2px 4px rgba(0,0,0,0.06);
  transition: transform 0.2s;
}

.sticky-note:hover {
  transform: rotate(-1deg) scale(1.03);
}

.note-pink     { background: #F8D3D3; }
.note-mint     { background: #C8F0E2; }
.note-lavender { background: #E0D9F8; }
.note-purple   { background: #F2DFF7; }

.note-tape {
  position: absolute;
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 10px;
  background: rgba(255,255,255,0.55);
  border-radius: 2px;
}

.note-emoji {
  font-size: 18px;
  display: block;
  margin-bottom: 2px;
}

.note-value {
  font-size: 20px;
  font-weight: 900;
  color: #3D2A1A;
  display: block;
  line-height: 1.1;
}

.note-label {
  font-size: 10px;
  color: #8B7B6A;
  font-weight: 600;
}

/* ======= 闯关进度 ======= */
.progress-section {
  background: rgba(255,255,255,0.5);
  border-radius: 14px;
  padding: 12px 10px;
  border: 1px solid #E6DDD0;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 8px;
}

.progress-icon-img {
  width: 20px;
  height: 20px;
}

.progress-title {
  font-size: 12px;
  font-weight: 700;
  color: #5C4030;
}

/* 沙滩小路进度条 */
.beach-path {
  margin-bottom: 6px;
}

.beach-track {
  position: relative;
  height: 22px;
  background: linear-gradient(180deg, #F5E6C8 0%, #E8D5A8 100%);
  border-radius: 11px;
  overflow: hidden;
  border: 1px solid #DDD0B0;
}

.beach-fill {
  height: 100%;
  background: linear-gradient(90deg, #C8E8D0 0%, #A0D8B8 50%, #80D0A0 100%);
  border-radius: 11px;
  position: relative;
  transition: width 0.8s cubic-bezier(0.25, 0.1, 0.25, 1);
  min-width: 0;
}

.beach-runner {
  position: absolute;
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
}

.beach-dots {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: space-evenly;
  align-items: center;
  padding: 0 4px;
  pointer-events: none;
}

.beach-dot {
  font-size: 10px;
  opacity: 0.35;
  transition: opacity 0.3s;
}

.beach-dot.reached {
  opacity: 0.8;
}

.beach-goal {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
  font-size: 10px;
  font-weight: 700;
  color: #E8A840;
  margin-top: 3px;
}

.goal-icon {
  width: 14px;
  height: 14px;
}

.progress-text {
  font-size: 10px;
  color: #8B7355;
  text-align: center;
  font-weight: 600;
}

/* ======= IP机器人 ======= */
.robot-corner {
  margin-top: auto;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding-top: 8px;
}

.robot-figure {
  position: relative;
}

.robot-body {
  width: 48px;
  height: 56px;
  background: linear-gradient(180deg, #C8E0F8 0%, #A0C8E8 100%);
  border-radius: 16px 16px 8px 8px;
  border: 2px solid #90B8D8;
  position: relative;
  animation: robotFloat 3s ease-in-out infinite;
}

.robot-hat {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 20px;
  animation: hatSway 4s ease-in-out infinite;
}

@keyframes hatSway {
  0%, 100% { transform: translateX(-50%) rotate(0deg); }
  25% { transform: translateX(-50%) rotate(-5deg); }
  75% { transform: translateX(-50%) rotate(5deg); }
}

.robot-face {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.robot-eye {
  width: 8px;
  height: 8px;
  background: #FFE880;
  border-radius: 50%;
  border: 1px solid #D0B840;
}

.robot-mouth {
  width: 12px;
  height: 3px;
  background: #90B8D8;
  border-radius: 2px;
}

@keyframes robotFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.robot-shadow {
  width: 36px;
  height: 6px;
  background: rgba(0,0,0,0.06);
  border-radius: 50%;
  margin: 2px auto 0;
  animation: shadowPulse 3s ease-in-out infinite;
}

@keyframes shadowPulse {
  0%, 100% { transform: scaleX(1); opacity: 0.6; }
  50% { transform: scaleX(0.7); opacity: 0.3; }
}

.robot-bubble {
  background: #FFFEF5;
  border: 1.5px solid #E0D5C0;
  border-radius: 12px 12px 12px 3px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
  color: #8B7355;
  white-space: nowrap;
  animation: bubblePop 2.5s ease-in-out infinite;
}

@keyframes bubblePop {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>
