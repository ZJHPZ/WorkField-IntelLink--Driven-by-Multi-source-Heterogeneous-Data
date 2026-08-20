<template>
  <div class="space-y-6 animate-fade-in-up">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-space-800"><img :src="iconPlanet" class="title-icon" alt="" /> 知识星系</h1>
        <p class="text-gray-400 text-sm mt-1">每颗星都是一个知识点 — 星云汇聚，连线成座</p>
      </div>
      <!-- 图例 -->
      <div class="flex flex-wrap gap-3 text-xs">
        <span class="flex items-center gap-1.5 px-2.5 py-1.5 bg-mint-50 text-mint-700 rounded-full font-medium">
          <span class="w-3 h-3 rounded-full bg-mint-500 shadow-sm shadow-mint-500/40"></span> 基础模块
        </span>
        <span class="flex items-center gap-1.5 px-2.5 py-1.5 bg-brand-50 text-brand-700 rounded-full font-medium">
          <span class="w-3 h-3 rounded-full bg-brand-500 shadow-sm shadow-brand-500/40"></span> 核心模块
        </span>
        <span class="flex items-center gap-1.5 px-2.5 py-1.5 bg-cyan-50 text-cyan-700 rounded-full font-medium">
          <span class="w-3 h-3 rounded-full bg-cyan-500 shadow-sm shadow-cyan-500/40"></span> 进阶模块
        </span>
        <span class="flex items-center gap-1.5 px-2.5 py-1.5 text-gray-400 text-xs">
          <span class="w-2 h-2 rounded-full bg-white/40"></span> 实线=前置依赖 · 虚线=关联
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 星系可视化区 -->
      <div class="lg:col-span-2">
        <div class="glass-card rounded-2xl p-2 relative overflow-hidden">
          <!-- 钻取模式返回按钮 -->
          <transition name="popover">
            <button
              v-if="drillFocus"
              @click="exitDrill"
              class="absolute top-4 left-4 z-20 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 shadow-2xl border border-white/20"
              style="background: rgba(15, 23, 42, 0.9); color: #e2e8f0; backdrop-filter: blur(20px);"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
              返回星系总览
            </button>
          </transition>
          <!-- 钻取标题 -->
          <transition name="popover">
            <div
              v-if="drillFocus"
              class="absolute top-4 left-1/2 -translate-x-1/2 z-10 px-5 py-2 rounded-full text-sm font-bold shadow-2xl border border-white/10"
              style="background: rgba(15, 23, 42, 0.85); color: #e2e8f0; backdrop-filter: blur(20px);"
            >
              <img :src="iconTelescope" class="drill-icon" alt="" /> 正在探索：{{ drillFocus.name }}
            </div>
          </transition>
          <div ref="galaxyContainer" class="w-full rounded-xl overflow-hidden relative" style="height: 520px; background: radial-gradient(ellipse at 50% 40%, #12122a 0%, #0a0a18 50%, #050510 100%);">
            <!-- 星云底色 — 三大模块的柔和光晕 -->
            <div class="absolute inset-0 pointer-events-none" style="background:
              radial-gradient(ellipse 260px 200px at 25% 35%, rgba(16,185,129,0.13) 0%, transparent 65%),
              radial-gradient(ellipse 280px 220px at 55% 48%, rgba(99,102,241,0.11) 0%, transparent 65%),
              radial-gradient(ellipse 300px 240px at 75% 62%, rgba(6,182,212,0.10) 0%, transparent 65%);
            " />
            <!-- 背景星点（用 i 生成确定性值，避免随机重绘闪烁） -->
            <div class="absolute inset-0 pointer-events-none">
              <div v-for="i in 50" :key="i" class="absolute rounded-full animate-twinkle"
                :style="{
                  width: (0.6 + (i % 3) * 0.5) + 'px',
                  height: (0.6 + (i % 3) * 0.5) + 'px',
                  backgroundColor: ['rgba(255,255,255,0.7)','rgba(203,213,225,0.5)','rgba(16,185,129,0.35)','rgba(99,102,241,0.35)','rgba(6,182,212,0.35)'][i % 5],
                  top: ((i * 17 + (i % 7) * 3) % 100) + '%',
                  left: ((i * 31 + (i % 11) * 5) % 100) + '%',
                  animationDelay: ((i * 0.13) % 4).toFixed(2) + 's',
                  animationDuration: (2.5 + (i % 4) * 0.8).toFixed(1) + 's',
                }" />
            </div>
            <div v-if="!graphReady" class="flex items-center justify-center h-full relative z-10">
              <div class="text-center">
                <div class="text-4xl mb-3 animate-float"><img :src="iconGalaxy" class="loading-icon" alt="" /></div>
                <p class="text-gray-400 text-sm">正在生成星图...</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 详情面板 -->
      <div class="glass-card rounded-2xl p-5">
        <template v-if="selectedTopic">
          <div class="space-y-4">
            <div class="flex items-start gap-3">
              <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shrink-0"
                :class="[catStyle(selectedTopic.category).bg]">
                {{ catStyle(selectedTopic.category).icon }}
              </div>
              <div>
                <h3 class="text-lg font-bold text-space-800">{{ selectedTopic.name }}</h3>
                <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                  :class="selectedTopic.status === 'mastered' ? 'bg-mint-100 text-mint-700' : selectedTopic.status === 'learning' ? 'bg-brand-100 text-brand-700' : 'bg-gray-100 text-gray-500'">
                  {{ selectedTopic.status === 'mastered' ? '✨ 已掌握' : selectedTopic.status === 'learning' ? '🚀 学习中' : '🔒 待解锁' }}
                </span>
              </div>
            </div>

            <!-- 掌握度 -->
            <div>
              <div class="flex justify-between text-sm mb-1.5">
                <span class="text-gray-500">掌握度</span>
                <span class="font-bold" :class="catStyle(selectedTopic.category).text">{{ Math.round(selectedTopic.masteryLevel * 100) }}%</span>
              </div>
              <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-700"
                  :style="{ width: (selectedTopic.masteryLevel * 100) + '%', background: catStyle(selectedTopic.category).fill }" />
              </div>
            </div>

            <div class="text-sm text-gray-500 space-y-1.5 pt-1">
              <p class="flex items-center gap-2"><span class="text-xs">🏷️</span> 分类: {{ categoryName(selectedTopic.category) }}</p>
              <p v-if="selectedTopic.masteryLevel >= 0.85" class="flex items-center gap-2 text-mint-600">
                <span class="text-xs">🌟</span> 已达标，可进入下一阶段
              </p>
              <p v-else-if="selectedTopic.masteryLevel > 0" class="flex items-center gap-2 text-brand-600">
                <span class="text-xs">📖</span> 继续探索以掌握此星
              </p>
              <p v-else class="flex items-center gap-2 text-gray-400">
                <span class="text-xs">🔒</span> 完成前置知识后可解锁
              </p>
            </div>

            <!-- 操作 -->
            <div class="space-y-2 pt-2 border-t border-gray-100">
              <button class="w-full py-2.5 bg-brand-500 text-white rounded-xl text-sm font-medium hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/20 active:scale-[0.98]">
                🚀 开始探索
              </button>
              <button class="w-full py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                🎯 做练习题
              </button>
            </div>

            <!-- 关联星球 -->
            <div v-if="relatedTopics.length" class="pt-2 border-t border-gray-100">
              <p class="text-xs text-gray-400 mb-2">🔗 关联星座</p>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="rt in relatedTopics" :key="rt"
                  class="text-xs px-2.5 py-1 bg-gray-50 text-gray-600 rounded-full cursor-pointer hover:bg-brand-50 hover:text-brand-600 transition-colors"
                  @click="selectTopicById(rt)">
                  {{ rt }}
                </span>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="py-14 text-center">
            <div class="text-5xl mb-4 animate-float"><img :src="iconGalaxy" class="empty-icon" alt="" /></div>
            <p class="text-gray-400 text-sm">点击星图中的星球<br/>查看知识详情</p>
            <p class="text-xs text-gray-300 mt-2">拖拽以平移视角 · 滚轮缩放</p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useLearningStore } from '@/stores/learning'
import type { TopicMastery, KnowledgeEdge } from '@/stores/learning'
import * as echarts from 'echarts'
import iconPlanet from '@/assets/icons/star/the-planet-svgrepo-com.svg'
import iconGalaxy from '@/assets/icons/star/galaxy-svgrepo-com.svg'
import iconTelescope from '@/assets/icons/star/telescope-svgrepo-com.svg'

const learningStore = useLearningStore()
const galaxyContainer = ref<HTMLElement | null>(null)
const graphReady = ref(false)
const selectedTopic = ref<TopicMastery | null>(null)
const drillFocus = ref<TopicMastery | null>(null)
const topicMap = ref<Record<string, TopicMastery>>({})
let chartInstance: any = null

const relatedTopics = computed(() => {
  if (!selectedTopic.value) return []
  const edges = learningStore.knowledgeEdges
  const tid = selectedTopic.value.topicId
  const linked = edges
    .filter(e => e.fromTopic === tid || e.toTopic === tid)
    .map(e => e.fromTopic === tid ? e.toTopic : e.fromTopic)
  const names = linked
    .map(id => learningStore.topicMasteryList.find(t => t.topicId === id)?.name)
    .filter(Boolean) as string[]
  return [...new Set(names)].slice(0, 5)
})

const categoryColors: Record<string, { fill: string; bg: string; text: string; icon: string }> = {
  foundation: { fill: '#10b981', bg: 'bg-mint-100', text: 'text-mint-700', icon: '🟢' },
  core:       { fill: '#6366f1', bg: 'bg-brand-100', text: 'text-brand-700', icon: '🟣' },
  advanced:   { fill: '#06b6d4', bg: 'bg-cyan-100', text: 'text-cyan-700', icon: '🔵' },
}

function categoryName(c: string) {
  const map: Record<string, string> = { foundation: '基础模块', core: '核心模块', advanced: '进阶模块' }
  return map[c] || c
}

function catStyle(c: string) {
  return categoryColors[c] || categoryColors.advanced
}

function selectTopicById(name: string) {
  const t = learningStore.topicMasteryList.find(t => t.name === name)
  if (t) selectedTopic.value = t
}

onMounted(async () => {
  await Promise.all([
    learningStore.fetchTopicMastery(),
    learningStore.fetchKnowledgeEdges(),
  ])
  topicMap.value = {}
  learningStore.topicMasteryList.forEach(t => { topicMap.value[t.topicId] = t })
  await nextTick()
  renderGalaxy()
})

function enterDrill(topic: TopicMastery) {
  drillFocus.value = topic
  setTimeout(() => renderGalaxy(), 50)
}

function exitDrill() {
  drillFocus.value = null
  selectedTopic.value = null
  setTimeout(() => renderGalaxy(), 50)
}

function renderGalaxy() {
  if (!galaxyContainer.value) return
  const chart = echarts.init(galaxyContainer.value)
  const topics = learningStore.topicMasteryList
  const edges = learningStore.knowledgeEdges

  // 模块配色
  const categoryBase: Record<string, { fill: string; glow: string; dim: string; label: string }> = {
    foundation: { fill: '#10b981', glow: 'rgba(16,185,129,0.8)', dim: 'rgba(16,185,129,0.35)', label: '基础模块' },
    core:       { fill: '#6366f1', glow: 'rgba(99,102,241,0.8)',   dim: 'rgba(99,102,241,0.35)',   label: '核心模块' },
    advanced:   { fill: '#06b6d4', glow: 'rgba(6,182,212,0.8)',    dim: 'rgba(6,182,212,0.35)',    label: '进阶模块' },
  }

  const catOrder = ['foundation', 'core', 'advanced']

  function statusParams(t: TopicMastery) {
    switch (t.status) {
      case 'mastered':
        return { size: 22 + t.masteryLevel * 18, blur: 18, opacity: 1, borderW: 2, shade: 'fill' as const }
      case 'learning':
        return { size: 16 + t.masteryLevel * 12, blur: 10, opacity: 0.88, borderW: 1.5, shade: 'fill' as const }
      default:
        return { size: 14, blur: 2, opacity: 0.55, borderW: 1, shade: 'dim' as const }
    }
  }

  // 使用后端存储的坐标，如果没有则用类别默认位置 + 噪声
  function getNodePos(t: TopicMastery): { x: number; y: number } {
    if (t.positionX !== 0 || t.positionY !== 0) {
      return { x: t.positionX, y: t.positionY }
    }
    // 回退：按类别生成默认位置
    const defaults: Record<string, { cx: number; cy: number; spread: number }> = {
      foundation: { cx: -130, cy: -70, spread: 50 },
      core: { cx: 30, cy: 10, spread: 60 },
      advanced: { cx: 140, cy: 90, spread: 70 },
    }
    const d = defaults[t.category] || defaults.advanced
    const hash = t.topicId.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
    const angle = (hash % 360) * Math.PI / 180
    const radius = (hash % 100) / 100 * d.spread
    return { x: d.cx + Math.cos(angle) * radius, y: d.cy + Math.sin(angle) * radius }
  }

  // 钻取模式: 重新计算可见节点和位置
  const visibleTopicIds = new Set<string>()
  if (drillFocus.value) {
    const focusId = drillFocus.value.topicId
    visibleTopicIds.add(focusId)
    edges.forEach(e => {
      if (e.fromTopic === focusId) visibleTopicIds.add(e.toTopic)
      if (e.toTopic === focusId) visibleTopicIds.add(e.fromTopic)
    })
  }
  const isDrillMode = drillFocus.value !== null && visibleTopicIds.size > 0

  const nodes: any[] = []
  topics.forEach(t => {
    // 钻取模式下过滤节点
    if (isDrillMode && !visibleTopicIds.has(t.topicId)) return

    const cat = categoryBase[t.category] || categoryBase.advanced
    const catIdx = catOrder.indexOf(t.category)
    let pos = getNodePos(t)

    // 钻取模式: 重新计算布局 — 焦点居中，前置在左，后置在右
    if (isDrillMode) {
      const focusId = drillFocus.value!.topicId
      if (t.topicId === focusId) {
        pos = { x: 0, y: 0 }
      } else {
        // 判断是前置还是后置
        const isPrereq = edges.some(e => e.fromTopic === t.topicId && e.toTopic === focusId)
        const isUnlock = edges.some(e => e.fromTopic === focusId && e.toTopic === t.topicId)
        const sideCount = Math.max(visibleTopicIds.size - 1, 1)
        const idx = Array.from(visibleTopicIds).indexOf(t.topicId)
        const xBase = isPrereq ? -180 : isUnlock ? 180 : 0
        const yOff = (idx - (sideCount - 1) / 2) * 90
        pos = { x: xBase || (idx % 2 === 0 ? -140 : 140), y: yOff || (idx - 1) * 80 - 60 }
      }
    }

    const sp = statusParams(t)
    // 钻取模式下节点更大
    const sizeMultiplier = drillFocus.value ? 1.4 : 1

    nodes.push({
      id: t.topicId,
      name: t.name,
      symbolSize: sp.size * sizeMultiplier,
      x: pos.x,
      y: pos.y,
      category: catIdx,
      symbol: 'circle',
      itemStyle: {
        color: sp.shade === 'dim' ? cat.dim : cat.fill,
        borderColor: sp.shade === 'dim' ? cat.dim : cat.glow,
        borderWidth: sp.borderW,
        shadowBlur: sp.blur * (drillFocus.value ? 2 : 1),
        shadowColor: sp.shade === 'dim' ? 'transparent' : cat.glow,
        opacity: sp.opacity,
      },
      label: {
        show: sp.size >= 14 || !!drillFocus.value,
        fontSize: (sp.size >= 36 ? 10 : 8) * (drillFocus.value ? 1.3 : 1),
        fontWeight: 'bold',
        color: sp.shade === 'dim' ? '#64748b' : '#cbd5e1',
        formatter: t.name.length > 6 ? t.name.substring(0, 5) + '…' : t.name,
        position: 'bottom',
        distance: 4,
      },
      data: t,
    })
  })

  // 用真实边数据连线（星座线）
  const nodeIds = new Set(nodes.map(n => n.id))
  const links: any[] = []
  edges.forEach(e => {
    if (!nodeIds.has(e.fromTopic) || !nodeIds.has(e.toTopic)) return
    const isPrereq = e.relationType === 'prerequisite'
    const fromNode = nodes.find(n => n.id === e.fromTopic)
    const toNode = nodes.find(n => n.id === e.toTopic)
    const fromTopic = fromNode?.data as TopicMastery | undefined
    const toTopic = toNode?.data as TopicMastery | undefined
    const bothLocked = fromTopic?.status === 'locked' && toTopic?.status === 'locked'
    const catColor = categoryBase[fromTopic?.category || 'core']?.fill || '#64748b'

    links.push({
      source: e.fromTopic,
      target: e.toTopic,
      lineStyle: {
        color: bothLocked ? 'rgba(100,116,139,0.2)' : isPrereq ? catColor : 'rgba(255,255,255,0.22)',
        width: bothLocked ? 1.4 : isPrereq ? 2.5 : 1.8,
        opacity: bothLocked ? 0.22 : isPrereq ? 0.55 : 0.35,
        curveness: isPrereq ? 0.1 : 0.25,
        type: isPrereq ? 'solid' : 'dashed',
      },
    })
  })

  const categories = catOrder.map((c, i) => ({
    name: categoryBase[c]?.label || c,
    itemStyle: { color: categoryBase[c]?.fill || '#94a3b8' },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    animationDuration: 800,
    animationDurationUpdate: 600,
    animationEasing: 'cubicInOut',
    animationEasingUpdate: 'cubicInOut',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10,10,26,0.94)',
      borderColor: 'rgba(99,102,241,0.4)',
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (p: any) => {
        const d = p.data?.data as TopicMastery | undefined
        if (!d) return p.name
        const statusText = d.status === 'mastered' ? '✨ 已掌握' : d.status === 'learning' ? '🚀 学习中' : '🔒 待解锁'
        return `<b>${d.name}</b><br/>掌握度: ${Math.round(d.masteryLevel * 100)}%<br/>${statusText}<br/>分类: ${categoryName(d.category)}`
      },
    },
    legend: {
      data: categories.map(c => c.name),
      bottom: 8,
      textStyle: { color: '#94a3b8', fontSize: 11 },
      itemGap: 20,
    },
    series: [{
      type: 'graph',
      layout: 'none',
      roam: true,
      draggable: true,
      categories,
      nodes,
      links,
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 5, opacity: 0.9 },
        itemStyle: { shadowBlur: 35, shadowColor: 'rgba(255,255,255,0.6)' },
        label: { fontSize: 12, fontWeight: 'bold', color: '#fff' },
      },
      scaleLimit: { min: 0.35, max: 4 },
    }],
    graphic: [
      { type: 'circle', left: 'center', top: 'center', z: 0,
        shape: { r: 10 },
        style: { fill: 'rgba(255,255,255,0.04)', stroke: 'rgba(255,255,255,0.06)', lineWidth: 1 } },
    ],
  })

  chart.on('click', (params: any) => {
    if (params.data?.data) {
      const topic = params.data.data as TopicMastery
      selectedTopic.value = topic
      enterDrill(topic)
    }
  })

  // 双击空白处退出钻取
  chart.on('dblclick', () => {
    if (drillFocus.value) exitDrill()
  })

  chartInstance = chart
  graphReady.value = true
  window.addEventListener('resize', () => chart.resize())
}
</script>

<style scoped>
.title-icon {
  width: 26px;
  height: 26px;
  display: inline-block;
  vertical-align: middle;
}

.loading-icon {
  width: 44px;
  height: 44px;
}

.empty-icon {
  width: 52px;
  height: 52px;
}

.drill-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  vertical-align: middle;
}
</style>
