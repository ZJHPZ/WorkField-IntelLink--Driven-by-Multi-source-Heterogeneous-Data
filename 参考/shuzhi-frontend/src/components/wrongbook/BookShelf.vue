<template>
  <aside class="bookshelf-panel">
    <!-- 书架标题 -->
    <div class="shelf-header">
      <span class="shelf-title-icon">📚</span>
      <span class="shelf-title">错题绘本架</span>
      <span class="shelf-count">{{ books.length }}本</span>
    </div>

    <!-- 薄弱知识点排行 -->
    <div v-if="books.length > 0" class="weakness-rank">
      <div class="rank-title">
        <span>🎯</span>
        <span>薄弱排行</span>
      </div>
      <div class="rank-bars">
        <div
          v-for="(b, i) in topWeakBooks"
          :key="b.topic_id"
          class="rank-bar-row"
          @click="$emit('select', b.topic_id)"
        >
          <span class="rank-index">{{ i + 1 }}</span>
          <span class="rank-name">{{ b.topic_name }}</span>
          <div class="rank-bar-track">
            <div
              class="rank-bar-fill"
              :class="i === 0 ? 'danger' : i === 1 ? 'warn' : 'ok'"
              :style="{ width: b.error_rate + '%' }"
            />
          </div>
          <span class="rank-rate">{{ b.error_rate }}%</span>
        </div>
      </div>
    </div>

    <!-- 书架面板 -->
    <div class="shelf-board">
      <!-- 木质纹理底板 -->
      <div class="wood-grain" />

      <!-- 书本陈列 -->
      <div class="books-row" ref="booksRowRef">
        <div
          v-for="(book, i) in books"
          :key="book.topic_id"
          class="book-spine-wrapper"
          :class="{ active: book.topic_id === activeTopicId }"
          :style="spineWrapperStyle(i)"
          @click="$emit('select', book.topic_id)"
          @mouseenter="hoveredBook = book.topic_id"
          @mouseleave="hoveredBook = null"
        >
          <!-- 书本 -->
          <div
            class="book-spine"
            :style="spineStyle(book)"
          >
            <!-- 书脊标签 -->
            <div class="spine-label">
              <span class="spine-topic">{{ book.topic_name }}</span>
            </div>
            <!-- 书脊底部信息 -->
            <div class="spine-meta">
              <span class="spine-count">{{ book.wrong_count }}<small>/{{ book.total_attempts }}</small></span>
              <span class="spine-rate">{{ book.error_rate }}%</span>
            </div>
          </div>

          <!-- 书本装饰：复习贴纸 -->
          <div v-if="reviewedCount(book) === book.wrong_count && book.wrong_count > 0" class="spine-sticker sticker-sun">🌟</div>
          <div v-else-if="reviewedCount(book) > 0" class="spine-sticker sticker-progress">📖</div>
          <div v-else-if="book.wrong_count > 6" class="spine-sticker sticker-star">⭐</div>
          <div v-if="book.error_rate < 50" class="spine-sticker sticker-flower">🌸</div>

          <!-- Hover 气泡 -->
          <div v-if="hoveredBook === book.topic_id" class="spine-tooltip">
            <div class="tooltip-inner">
              <div class="tooltip-topic">{{ book.topic_name }}</div>
              <div class="tooltip-stats">
                <span>错题 {{ book.wrong_count }}/{{ book.total_attempts }}</span>
                <span>掌握 {{ 100 - book.error_rate }}%</span>
              </div>
              <div class="tooltip-review">
                已复习 {{ reviewedCount(book) }}/{{ book.wrong_count }}
              </div>
            </div>
          </div>
        </div>

        <!-- 空位：散落小书本 -->
        <div v-if="books.length < 5" class="book-spine-wrapper placeholder">
          <div class="book-spine ghost">📖</div>
        </div>
      </div>

      <!-- 书架底板 -->
      <div class="shelf-bottom" />
    </div>

    <!-- 散落装饰 -->
    <div class="shelf-decorations">
      <img :src="polaroidIcon" class="shelf-deco-img" alt="" />
      <img :src="mapIcon" class="shelf-deco-img" alt="" />
      <img :src="benchIcon" class="shelf-deco-img" alt="" />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { WrongTopicGroup } from '@/stores/wrongBook'
import polaroidIcon from '@/assets/icons/summer/polaroid-svgrepo-com.svg'
import mapIcon from '@/assets/icons/summer/map-svgrepo-com.svg'
import benchIcon from '@/assets/icons/summer/bench-svgrepo-com.svg'

const props = defineProps<{
  books: WrongTopicGroup[]
  activeTopicId: string | null
}>()

defineEmits<{
  select: [topicId: string]
}>()

const hoveredBook = ref<string | null>(null)

// 薄弱排行：按错误率降序取前3
const topWeakBooks = computed(() =>
  [...props.books].sort((a, b) => b.error_rate - a.error_rate).slice(0, 3)
)

function reviewedCount(book: WrongTopicGroup): number {
  return book.questions.filter(q => q.reviewed).length
}

function subjectColor(name: string): string {
  const n = name.toLowerCase()
  if (/spark/.test(n) && /ml|lib/.test(n)) return '#5298D1'
  if (/spark/.test(n) && /sql/.test(n)) return '#C090C8'
  if (/spark/.test(n) && /graph/i.test(n)) return '#68B8A8'
  if (/spark/.test(n) && /streaming/.test(n)) return '#5BA0D0'
  if (/spark/.test(n) && /rdd/.test(n)) return '#5080B0'
  if (/spark/.test(n) && /基础/.test(n)) return '#E8A840'
  if (/spark/.test(n) && /部署|平台/.test(n)) return '#8898B0'
  if (/mapreduce/.test(n)) return '#E8B840'
  if (/hdfs/.test(n)) return '#6090B0'
  if (/hive/.test(n)) return '#D0A040'
  if (/hbase/.test(n)) return '#70A080'
  if (/kafka/.test(n)) return '#B08090'
  return '#68B8A8'
}

function spineStyle(book: WrongTopicGroup) {
  const color = subjectColor(book.topic_name)
  // 书本厚度基于错题数：最少 22px，最多 44px
  const thickness = Math.min(44, Math.max(22, 18 + book.wrong_count * 2))
  return {
    width: `${thickness}px`,
    background: `linear-gradient(180deg,
      ${color} 0%,
      ${color}DD 15%,
      ${color} 50%,
      ${color}CC 85%,
      ${color}EE 100%)`,
    borderColor: `${color}99`,
  }
}

function spineWrapperStyle(i: number): Record<string, string> {
  // 轻微错落摆放 (±3px)
  const tilt = (i % 3 - 1) * 2.5
  return {
    transform: `rotate(${tilt}deg)`,
  }
}
</script>

<style scoped>
.bookshelf-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 14px;
  background: linear-gradient(180deg,
    rgba(255,246,217,0.45) 0%,
    rgba(255,246,217,0.2) 50%,
    rgba(180,232,221,0.1) 100%);
  border-left: 1px solid rgba(180,200,190,0.25);
  overflow-y: auto;
  height: 100%;
}

/* ======= 标题 ======= */
.shelf-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 10px;
  margin-bottom: 12px;
  border-bottom: 1.5px dashed #E0D5C0;
}

.shelf-title-icon { font-size: 20px; }

.shelf-title {
  flex: 1;
  font-size: 14px;
  font-weight: 800;
  color: #5C4030;
}

.shelf-count {
  font-size: 11px;
  font-weight: 600;
  color: #A09080;
  background: rgba(255,255,255,0.5);
  padding: 2px 8px;
  border-radius: 10px;
}

/* ======= 薄弱排行 ======= */
.weakness-rank {
  margin-bottom: 10px;
  padding: 10px;
  background: rgba(255,255,255,0.55);
  border-radius: 12px;
  border: 1px solid #EBE3D6;
}

.rank-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: #8B7355;
  margin-bottom: 8px;
}

.rank-bars {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.rank-bar-row {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 6px;
  transition: background 0.15s;
}

.rank-bar-row:hover {
  background: rgba(255,185,87,0.1);
}

.rank-index {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #E8DDD0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 800;
  color: #8B7355;
  flex-shrink: 0;
}

.rank-bar-row:nth-child(1) .rank-index { background: #FFD8D8; color: #C05050; }
.rank-bar-row:nth-child(2) .rank-index { background: #FFE8C8; color: #B08030; }
.rank-bar-row:nth-child(3) .rank-index { background: #FFF0C8; color: #A08830; }

.rank-name {
  width: 60px;
  font-size: 10px;
  font-weight: 600;
  color: #5C4030;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 0;
}

.rank-bar-track {
  flex: 1;
  height: 8px;
  background: #F0EBE2;
  border-radius: 4px;
  overflow: hidden;
}

.rank-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease-out;
}

.rank-bar-fill.danger { background: linear-gradient(90deg, #F08080, #E06060); }
.rank-bar-fill.warn   { background: linear-gradient(90deg, #F0C080, #E0A850); }
.rank-bar-fill.ok     { background: linear-gradient(90deg, #E8C860, #D0A830); }

.rank-rate {
  font-size: 10px;
  font-weight: 700;
  color: #8B7355;
  width: 32px;
  text-align: right;
  flex-shrink: 0;
}

/* ======= 书架面板 ======= */
.shelf-board {
  position: relative;
  background: linear-gradient(180deg,
    rgba(210,180,140,0.2) 0%,
    rgba(200,170,130,0.15) 100%);
  border-radius: 14px;
  padding: 16px 10px 8px;
  border: 1px solid rgba(180,160,130,0.2);
}

.wood-grain {
  position: absolute;
  inset: 0;
  border-radius: 14px;
  background: repeating-linear-gradient(
    90deg,
    transparent,
    transparent 20px,
    rgba(180,150,110,0.06) 20px,
    rgba(180,150,110,0.06) 21px
  );
  pointer-events: none;
}

/* 书本行 */
.books-row {
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 6px;
  min-height: 180px;
  padding: 0 4px;
  position: relative;
  z-index: 1;
  flex-wrap: wrap;
}

/* 书架底板 */
.shelf-bottom {
  height: 6px;
  background: linear-gradient(180deg,
    rgba(180,140,100,0.4) 0%,
    rgba(160,120,80,0.35) 50%,
    rgba(140,100,60,0.25) 100%);
  border-radius: 0 0 10px 10px;
  margin: 4px 4px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
}

/* ======= 书脊 ======= */
.book-spine-wrapper {
  position: relative;
  cursor: pointer;
  transition: transform 0.25s cubic-bezier(0.25, 0.1, 0.25, 1);
  animation: bookFloat 3s ease-in-out infinite;
  z-index: 1;
}

.book-spine-wrapper:nth-child(2) { animation-delay: 0.2s; }
.book-spine-wrapper:nth-child(3) { animation-delay: 0.5s; }
.book-spine-wrapper:nth-child(4) { animation-delay: 0.8s; }
.book-spine-wrapper:nth-child(5) { animation-delay: 1.1s; }

@keyframes bookFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.book-spine-wrapper:hover {
  transform: translateY(-8px) scale(1.04) !important;
  z-index: 5;
}

.book-spine-wrapper.active {
  z-index: 3;
}

.book-spine-wrapper.active .book-spine {
  box-shadow: 0 0 0 3px rgba(255,185,87,0.5), 3px 4px 12px rgba(0,0,0,0.12);
}

.book-spine-wrapper.placeholder {
  opacity: 0.3;
  cursor: default;
}

/* 书本实体 */
.book-spine {
  min-height: 160px;
  border-radius: 5px 3px 3px 5px;
  border: 1.5px solid;
  border-right: 2px solid rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px;
  box-shadow:
    2px 3px 8px rgba(0,0,0,0.08),
    inset -2px 0 3px rgba(0,0,0,0.04);
  position: relative;
  transition: box-shadow 0.25s;
}

.book-spine-wrapper:hover .book-spine {
  box-shadow:
    3px 6px 16px rgba(0,0,0,0.14),
    inset -2px 0 3px rgba(0,0,0,0.04);
}

/* 书脊标签 */
.spine-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  padding: 4px 0;
}

.spine-topic {
  font-size: 12px;
  font-weight: 800;
  color: #FFFEF8;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
  letter-spacing: 1px;
  line-height: 1.3;
}

.spine-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}

.spine-count {
  font-size: 10px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  line-height: 1;
}

.spine-count small {
  font-size: 8px;
  opacity: 0.7;
  font-weight: 400;
}

.spine-rate {
  font-size: 9px;
  font-weight: 800;
  color: rgba(255,255,255,0.85);
  background: rgba(0,0,0,0.1);
  padding: 1px 4px;
  border-radius: 4px;
}

/* 贴纸 */
.spine-sticker {
  position: absolute;
  font-size: 14px;
  pointer-events: none;
  filter: drop-shadow(0 1px 1px rgba(0,0,0,0.15));
}

.sticker-star {
  top: 8px;
  right: -6px;
  transform: rotate(15deg);
}

.sticker-flower {
  bottom: 20px;
  right: -4px;
  transform: rotate(-10deg);
}

.sticker-sun {
  top: 6px;
  right: -6px;
  font-size: 16px;
  animation: sunGlow 1.5s ease-in-out infinite;
}

@keyframes sunGlow {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 2px rgba(255,200,50,0.6)); }
  50%      { transform: scale(1.2); filter: drop-shadow(0 0 6px rgba(255,200,50,0.9)); }
}

.sticker-progress {
  top: 6px;
  right: -4px;
  font-size: 12px;
  opacity: 0.8;
}

/* 幽灵书本 */
.book-spine.ghost {
  background: rgba(200,190,170,0.25) !important;
  border: 1.5px dashed rgba(180,170,150,0.3) !important;
  min-width: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  opacity: 0.5;
}

/* ======= Hover气泡 ======= */
.spine-tooltip {
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%);
  z-index: 20;
  white-space: nowrap;
  animation: tooltipIn 0.2s ease-out;
}

@keyframes tooltipIn {
  from { opacity: 0; transform: translateY(-50%) translateX(-8px); }
  to   { opacity: 1; transform: translateY(-50%) translateX(0); }
}

.tooltip-inner {
  background: #FFFEF5;
  border: 1.5px solid #E0D5C0;
  border-radius: 14px 14px 14px 4px;
  padding: 8px 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.tooltip-topic {
  font-size: 13px;
  font-weight: 700;
  color: #5C4030;
  margin-bottom: 4px;
}

.tooltip-stats {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #8B7355;
  font-weight: 600;
}

.tooltip-review {
  margin-top: 4px;
  font-size: 10px;
  color: #5298D1;
  font-weight: 600;
  padding-top: 4px;
  border-top: 1px dashed #E0D5C0;
}

/* ======= 散落装饰 ======= */
.shelf-decorations {
  display: flex;
  gap: 8px;
  justify-content: center;
  padding-top: 8px;
  opacity: 0.4;
}

.shelf-deco-img {
  width: 22px;
  height: 22px;
  opacity: 0.55;
  animation: decoTilt 3s ease-in-out infinite;
}

.shelf-deco-img:nth-child(2) { animation-delay: 0.6s; width: 18px; height: 18px; }
.shelf-deco-img:nth-child(3) { animation-delay: 1.2s; width: 20px; height: 20px; }

@keyframes decoTilt {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(10deg); }
}

/* ============================================================
   响应式 — 小屏横放绘本封面
   ============================================================ */

@media (max-width: 900px) {
  .bookshelf-panel {
    width: 100%;
    flex-direction: row;
    padding: 10px;
    border-left: none;
    border-top: 1px solid rgba(180,200,190,0.25);
    overflow-x: auto;
    overflow-y: hidden;
    max-height: 140px;
    gap: 0;
  }

  .shelf-header {
    flex-shrink: 0;
    flex-direction: column;
    gap: 2px;
    padding-bottom: 0;
    padding-right: 10px;
    margin-bottom: 0;
    border-bottom: none;
    border-right: 1.5px dashed #E0D5C0;
    align-items: center;
    min-width: 50px;
  }

  .shelf-board {
    flex: 1;
    overflow-x: auto;
    padding: 6px 8px;
    display: flex;
    align-items: center;
  }

  .wood-grain {
    display: none;
  }

  .books-row {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 8px;
    min-height: auto;
    align-items: center;
  }

  .book-spine-wrapper {
    flex-shrink: 0;
    animation: none;
  }

  .book-spine-wrapper:hover {
    transform: translateY(-4px) scale(1.05) !important;
  }

  .book-spine {
    width: 90px !important;
    min-height: auto;
    height: 90px;
    border-radius: 6px 6px 6px 6px;
    padding: 6px 8px;
    flex-direction: column;
    justify-content: center;
  }

  .spine-label {
    writing-mode: horizontal-tb;
    text-orientation: mixed;
    padding: 0;
    text-align: center;
  }

  .spine-topic {
    font-size: 11px;
    letter-spacing: 0.5px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .spine-meta {
    flex-direction: row;
    gap: 6px;
  }

  .shelf-bottom {
    display: none;
  }

  .shelf-decorations {
    display: none;
  }

  .spine-sticker {
    font-size: 10px;
  }

  .sticker-star { top: -4px; right: -4px; }
  .sticker-flower { bottom: -4px; right: -2px; }
  .sticker-sun { top: -6px; right: -4px; font-size: 12px; }
  .sticker-progress { top: -2px; right: -2px; font-size: 9px; }

  .spine-tooltip {
    left: auto;
    top: auto;
    bottom: calc(100% + 8px);
    transform: none;
  }

  @keyframes tooltipIn {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }
}
</style>
