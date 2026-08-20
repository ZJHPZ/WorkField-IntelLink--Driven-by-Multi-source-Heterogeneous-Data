<template>
  <!-- ================================================================
       暑假绘本式错题本 — 三栏永久布局
       左：打卡侧边栏 | 中：书本阅览画布 | 右：绘本书架
       ================================================================ -->
  <div class="wrong-book-scene">
    <!-- 全局背景装饰 — 夏日主题漂浮元素 -->
    <div class="global-decorations">
      <span class="g-deco g-cloud" v-for="i in 4" :key="'c'+i" :style="cloudStyle(i)">☁️</span>
      <span class="g-deco g-sun" style="top:4%;right:8%;">🌤️</span>
      <img class="g-deco g-popsicle" style="bottom:10%;left:24%;animation-delay:1.5s;" :src="iceCreamIcon" alt="" />
      <img class="g-deco g-popsicle" style="bottom:18%;right:30%;animation-delay:0.8s;" :src="coconutTreeIcon" alt="" />
    </div>

    <!-- ====== 加载骨架 ====== -->
    <template v-if="store.loading && store.groups.length === 0">
      <aside class="summer-sidebar skeleton-sidebar">
        <div class="sk-header"><div class="sk-line sk-title" /><div class="sk-line sk-sub" /></div>
        <div class="sk-notes">
          <div class="sk-note" v-for="i in 4" :key="i"><div class="sk-val" /><div class="sk-label" /></div>
        </div>
        <div class="sk-bar"><div class="sk-bar-fill" /></div>
      </aside>
      <main class="center-canvas">
        <div class="canvas-empty">
          <div class="sk-book"><div class="sk-book-page left" /><div class="sk-book-spine" /><div class="sk-book-page right" /></div>
          <p class="sk-loading-text">正在打开错题本…</p>
        </div>
      </main>
      <aside class="bookshelf-panel skeleton-shelf">
        <div class="sk-shelf-header" />
        <div class="sk-shelf-books">
          <div class="sk-spine" v-for="i in 4" :key="i" :style="{ height: 120 + i * 15 + 'px' }" />
        </div>
      </aside>
    </template>

    <!-- ====== 左侧：暑假打卡侧边栏 ====== -->
    <SummerSidebar
      v-if="!store.loading || store.groups.length > 0"
      :total-wrong="store.totalWrong"
      :reviewed-count="reviewedCount"
      :total-topics="store.stats?.total_topics ?? 0"
      :master-rate="masterRate"
    />

    <!-- ====== 中间：书本阅览画布 ====== -->
    <main v-if="!store.loading || store.groups.length > 0" class="center-canvas">
      <!-- 空态：夏日装饰 + 提示 -->
      <div v-if="!store.bookTopic" class="canvas-empty">
        <div class="empty-clouds">
          <span class="empty-cloud c1">☁️</span>
          <span class="empty-cloud c2">☁️</span>
          <span class="empty-cloud c3">☁️</span>
        </div>
        <div class="empty-sun">🌤️</div>
        <div class="empty-message">
          <div class="empty-icon">📖</div>
          <h3 class="empty-title">从右侧书架选一本书吧</h3>
          <p class="empty-desc">点击书架上的错题绘本，开始暑假复习之旅 ~</p>
        </div>
        <div class="empty-ground">
          <img :src="lighthouseIcon" class="ground-icon" alt="" />
          <img :src="surfIcon" class="ground-icon" alt="" />
          <img :src="coconutTreeIcon" class="ground-icon" alt="" />
          <img :src="sunbathingIcon" class="ground-icon" alt="" />
          <img :src="iceCreamIcon" class="ground-icon" alt="" />
        </div>
      </div>

      <!-- 书本展开态 — 无题目保护 -->
      <div v-else-if="store.bookTopic && store.bookQuestions.length === 0" class="canvas-empty">
        <div class="empty-message">
          <div class="empty-icon">📭</div>
          <h3 class="empty-title">该知识点暂无错题</h3>
          <p class="empty-desc">太棒了，这个知识点你已经全部掌握啦 ~</p>
        </div>
      </div>

      <Transition name="book-open">
        <BookReader
          v-if="store.bookTopic && store.bookQuestions.length > 0"
          :key="store.bookTopicId ?? ''"
          :questions="store.bookQuestions"
          :topic-name="store.bookTopic.topic_name"
          :initial-page="store.bookPageIndex"
          @close="store.closeBook()"
        />
      </Transition>
    </main>

    <!-- ====== 右侧：绘本书架 ====== -->
    <BookShelf
      v-if="!store.loading || store.groups.length > 0"
      :books="store.filteredGroups"
      :active-topic-id="store.bookTopicId"
      @select="store.openBook"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useWrongBookStore } from '@/stores/wrongBook'
import SummerSidebar from '@/components/wrongbook/SummerSidebar.vue'
import BookShelf from '@/components/wrongbook/BookShelf.vue'
import BookReader from '@/components/wrongbook/BookReader.vue'
import iceCreamIcon from '@/assets/icons/summer/ice-cream-svgrepo-com.svg'
import coconutTreeIcon from '@/assets/icons/summer/coconut-tree-svgrepo-com.svg'
import lighthouseIcon from '@/assets/icons/summer/lighthouse-svgrepo-com.svg'
import surfIcon from '@/assets/icons/summer/surf-svgrepo-com.svg'
import sunbathingIcon from '@/assets/icons/summer/sunbathing-svgrepo-com.svg'

const store = useWrongBookStore()

const reviewedCount = computed(() =>
  store.groups.reduce((sum, g) => sum + g.questions.filter(q => q.reviewed).length, 0)
)

const masterRate = computed(() => {
  if (!store.stats || store.stats.total_questions === 0) return 0
  return Math.round((1 - store.stats.total_wrong / store.stats.total_questions) * 100)
})

function cloudStyle(i: number): Record<string, string> {
  const top = 5 + i * 18
  const left = 35 + i * 15 + (i % 2) * 8
  const delay = i * 1.2
  const size = 20 + i * 5
  const opacity = 0.25 + i * 0.06
  return {
    top: `${top}%`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    fontSize: `${size}px`,
    opacity: `${opacity}`,
  }
}

onMounted(() => {
  store.fetchWrongBook()
  store.fetchStats()
})
</script>

<style scoped>
/* ============================================================
   三栏布局容器
   ============================================================ */

.wrong-book-scene {
  display: flex;
  height: 100%;
  overflow: hidden;
  /* 原版渐变底色 */
  background: linear-gradient(180deg,
    #B4E8DD 0%,
    #B9E3F8 28%,
    #FFF6D9 65%,
    #FFF8E7 100%);
  position: relative;
  font-family: 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', 'Comic Sans MS', cursive, sans-serif;
  color: #5C4030;
}

/* ============================================================
   全局背景装饰 — 夏日元素
   ============================================================ */

.global-decorations {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.g-deco {
  position: absolute;
  user-select: none;
  animation: floatDeco 5s ease-in-out infinite;
}

.g-cloud {
  animation: cloudDrift 12s linear infinite;
}

@keyframes cloudDrift {
  0%   { transform: translateX(0); }
  50%  { transform: translateX(30px); }
  100% { transform: translateX(0); }
}

.g-sun {
  font-size: 28px;
  animation: sunBounce 3s ease-in-out infinite;
}

@keyframes sunBounce {
  0%, 100% { transform: translateY(0) scale(1); }
  50%      { transform: translateY(-8px) scale(1.08); }
}

.g-popsicle {
  width: 36px;
  height: 36px;
  animation: popsicleSpin 6s ease-in-out infinite;
}

@keyframes popsicleSpin {
  0%, 100% { transform: rotate(0deg); }
  25%      { transform: rotate(-8deg); }
  75%      { transform: rotate(8deg); }
}

@keyframes floatDeco {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-6px); }
}

/* ============================================================
   中间画布 — 自适应
   ============================================================ */

.center-canvas {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
  min-width: 0;
  overflow: hidden;
}

/* ——— 空态：夏日装饰 ——— */
.canvas-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.empty-clouds {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.empty-cloud {
  position: absolute;
  font-size: 32px;
  opacity: 0.3;
  animation: cloudFloat 8s ease-in-out infinite;
}

.empty-cloud.c1 { top: 12%; left: 18%; animation-delay: 0s; font-size: 34px; }
.empty-cloud.c2 { top: 22%; left: 55%; animation-delay: 2.5s; font-size: 28px; opacity: 0.22; }
.empty-cloud.c3 { top: 8%;  left: 72%; animation-delay: 5s; font-size: 24px; opacity: 0.25; }

@keyframes cloudFloat {
  0%, 100% { transform: translateX(0); }
  33%      { transform: translateX(20px); }
  66%      { transform: translateX(-15px); }
}

.empty-sun {
  position: absolute;
  top: 8%;
  right: 14%;
  font-size: 36px;
  opacity: 0.5;
  animation: sunBounce 3s ease-in-out infinite;
}

.empty-message {
  text-align: center;
  z-index: 1;
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 12px;
  animation: bookPulse 2.5s ease-in-out infinite;
}

@keyframes bookPulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.06); }
}

.empty-title {
  font-size: 18px;
  font-weight: 800;
  color: #5C4030;
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 13px;
  color: #9B8B7A;
  font-weight: 500;
}

.empty-ground {
  position: absolute;
  bottom: 8%;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  align-items: flex-end;
  opacity: 0.4;
}

.ground-icon {
  width: 28px;
  height: 28px;
  animation: floatDeco 4s ease-in-out infinite;
}

.ground-icon:nth-child(2) { animation-delay: 0.6s; width: 24px; height: 24px; }
.ground-icon:nth-child(3) { animation-delay: 1.2s; width: 32px; height: 32px; }
.ground-icon:nth-child(4) { animation-delay: 1.8s; width: 22px; height: 22px; }
.ground-icon:nth-child(5) { animation-delay: 2.4s; width: 26px; height: 26px; }

/* ============================================================
   书架 → 翻书过渡动画
   ============================================================ */

.book-open-enter-active {
  animation: bookScaleIn 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.book-open-leave-active {
  animation: bookScaleOut 0.25s ease-in forwards;
}

@keyframes bookScaleIn {
  0% {
    opacity: 0;
    transform: scale(0.6) translateX(80px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateX(0);
  }
}

@keyframes bookScaleOut {
  0% {
    opacity: 1;
    transform: scale(1) translateX(0);
  }
  100% {
    opacity: 0;
    transform: scale(0.6) translateX(80px);
  }
}

/* ============================================================
   加载骨架屏
   ============================================================ */

.skeleton-sidebar {
  width: 220px;
  flex-shrink: 0;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sk-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 12px;
}

.sk-line {
  height: 14px;
  border-radius: 7px;
  background: linear-gradient(90deg, #E8DDD0 25%, #F0E8DC 50%, #E8DDD0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.sk-line.sk-title { width: 70%; height: 18px; }
.sk-line.sk-sub   { width: 45%; }

.sk-notes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sk-note {
  height: 62px;
  border-radius: 3px 12px 3px 12px;
  background: linear-gradient(90deg, #F0E8DC 25%, #F8F0E8 50%, #F0E8DC 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
}

.sk-val {
  width: 40%;
  height: 18px;
  border-radius: 4px;
  background: #E8DDD0;
}

.sk-label {
  width: 55%;
  height: 10px;
  border-radius: 3px;
  background: #EBE3D6;
}

.sk-bar {
  height: 22px;
  border-radius: 11px;
  background: linear-gradient(90deg, #F0E8DC 25%, #F8F0E8 50%, #F0E8DC 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.sk-book {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 16px;
}

.sk-book-page {
  width: 140px;
  height: 200px;
  border-radius: 8px;
  background: linear-gradient(90deg, #F0E8DC 25%, #F8F0E8 50%, #F0E8DC 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.sk-book-page.left { border-radius: 8px 0 0 8px; }
.sk-book-page.right { border-radius: 0 8px 8px 0; }

.sk-book-spine {
  width: 4px;
  height: 200px;
  background: #E0D5C5;
}

.sk-loading-text {
  font-size: 14px;
  font-weight: 700;
  color: #B5A898;
  text-align: center;
  animation: pulse 1.8s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50%      { opacity: 1; }
}

.skeleton-shelf {
  width: 280px;
  flex-shrink: 0;
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
}

.sk-shelf-header {
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(90deg, #E8DDD0 25%, #F0E8DC 50%, #E8DDD0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  margin-bottom: 12px;
}

.sk-shelf-books {
  display: flex;
  gap: 6px;
  align-items: flex-end;
  min-height: 180px;
  padding: 0 4px;
  background: rgba(210,180,140,0.1);
  border-radius: 14px;
  padding: 16px 10px;
}

.sk-spine {
  width: 28px;
  border-radius: 5px 3px 3px 5px;
  background: linear-gradient(180deg, #E8DDD0 25%, #F0E8DC 50%, #E8DDD0 75%);
  background-size: 100% 200%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ============================================================
   响应式 — 小屏纵向堆叠
   ============================================================ */

@media (max-width: 900px) {
  .wrong-book-scene {
    flex-direction: column;
  }

  /* 左侧栏 → 顶部横向 */
  .wrong-book-scene :deep(.summer-sidebar) {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
    padding: 10px;
    gap: 8px;
    max-height: 140px;
    overflow-x: auto;
    border-right: none;
    border-bottom: 1px solid rgba(180,200,190,0.25);
  }

  /* 右侧书架 → 底部横向滚动 */
  .wrong-book-scene :deep(.bookshelf-panel) {
    width: 100%;
    flex-direction: row;
    padding: 10px;
    border-left: none;
    border-top: 1px solid rgba(180,200,190,0.25);
    max-height: 120px;
    overflow-x: auto;
  }

  .center-canvas {
    min-height: 400px;
  }
}
</style>
