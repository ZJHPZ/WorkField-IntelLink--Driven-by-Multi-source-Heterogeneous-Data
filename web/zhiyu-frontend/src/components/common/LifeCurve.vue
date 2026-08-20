<template>
  <div class="life-curve">
    <!-- 阶段图例 -->
    <div class="flex items-center gap-4 mb-3 text-xs" :style="{ color: 'var(--text-muted)' }">
      <span class="flex items-center gap-1"><span class="w-3 h-1 rounded-full" style="background:#22d3ee"></span> 萌芽期</span>
      <span class="flex items-center gap-1"><span class="w-3 h-1 rounded-full" style="background:#818cf8"></span> 爆发期</span>
      <span class="flex items-center gap-1"><span class="w-3 h-1 rounded-full" style="background:#10b981"></span> 成熟期</span>
      <span class="flex items-center gap-1"><span class="w-3 h-1 rounded-full" style="background:#f59e0b"></span> 转型期</span>
    </div>

    <!-- ECharts 曲线 -->
    <v-chart
      v-if="chartOption"
      ref="chartRef"
      class="w-full"
      style="height: 420px"
      :option="chartOption"
      :autoresize="true"
      @click="onChartClick"
    />

    <!-- 播放控件 -->
    <div class="flex items-center gap-3 mt-3">
      <button class="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition-all"
        :style="{ color:'var(--text-secondary)', borderColor:'var(--border-color)' }"
        @click="togglePlay">
        <span>{{ playing ? '⏸' : '▶' }}</span> {{ playing ? '暂停' : '播放轨迹' }}
      </button>
      <span v-if="playing" class="text-xs" :style="{ color:'var(--text-muted)' }">
        正在播放: {{ timeline[playIndex]?.date }} / {{ timeline[timeline.length-1]?.date }}
      </span>
      <button class="text-xs px-3 py-1.5 rounded-lg border ml-auto transition-all"
        :style="{ color:'var(--text-secondary)', borderColor:'var(--border-color)' }"
        @click="$emit('toggle-diff')">
        📊 对比模式
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart, ScatterChart, EffectScatterChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, GraphicComponent, MarkAreaComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { TimelineEvent } from '@/stores/enterprise'

use([LineChart, ScatterChart, EffectScatterChart, TooltipComponent, GridComponent, GraphicComponent, MarkAreaComponent, CanvasRenderer])

const props = defineProps<{
  timeline: TimelineEvent[]
  selectedIndex?: number
}>()

const emit = defineEmits<{
  (e: 'select', index: number): void
  (e: 'toggle-diff'): void
}>()

const chartRef = ref()
const playing = ref(false)
const playIndex = ref(0)
let playTimer: ReturnType<typeof setInterval> | null = null

// ===== ECharts 配置 =====
const chartOption = computed(() => {
  const tl = props.timeline
  if (!tl.length) return null

  const dates = tl.map(t => t.date)
  const demands = tl.map(t => t.marketDemand)
  const adoptions = tl.map(t => t.adoptionRate)

  // 高亮当前选中
  const selIdx = props.selectedIndex ?? 0

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: 'rgba(99, 102, 241, 0.4)',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex
        if (idx === undefined) return ''
        const t = tl[idx]
        return `<div style="font-weight:bold;font-size:14px;margin-bottom:4px">${t.label}</div>
          <div>📈 市场需求: <b style="color:#818cf8">${t.marketDemand}%</b></div>
          <div>🏢 企业采用: <b style="color:#06b6d4">${t.adoptionRate}%</b></div>
          <div>💰 薪资: <b style="color:#10b981">${t.salaryRange}</b></div>
          <div style="margin-top:4px;color:#94a3b8;font-size:11px">${t.summary}</div>`
      },
    },
    grid: { top: 30, bottom: 50, left: 50, right: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(99,102,241,0.3)' } },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', fontSize: 12, fontWeight: 'bold' },
    },
    yAxis: [{
      type: 'value', name: '市场需求 (%)', max: 100,
      nameTextStyle: { color: '#94a3b8', fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: 'rgba(99,102,241,0.1)' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    }, {
      type: 'value', name: '采用率 (%)', max: 100,
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 10 },
    }],
    series: [
      // 1. 面积填充 (市场需求)
      {
        type: 'line', data: demands, smooth: true, symbol: 'none',
        lineStyle: { width: 0 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(99,102,241,0.25)' },
              { offset: 0.5, color: 'rgba(99,102,241,0.08)' },
              { offset: 1, color: 'rgba(15,23,42,0)' },
            ],
          },
        },
        z: 1,
      },
      // 2. 主线 (市场需求) — 发光渐变
      {
        type: 'line', data: demands, smooth: true, symbol: 'none',
        lineStyle: { width: 3, color: '#818cf8', shadowBlur: 12, shadowColor: 'rgba(99,102,241,0.6)' },
        z: 3,
      },
      // 3. 第二线 (采用率) — 虚线
      {
        type: 'line', data: adoptions, smooth: true, symbol: 'none',
        yAxisIndex: 1,
        lineStyle: { width: 1.5, color: '#22d3ee', type: 'dashed', shadowBlur: 4, shadowColor: 'rgba(6,182,212,0.3)' },
        z: 2,
      },
      // 4. 节点 — 涟漪脉冲效果
      {
        type: 'effectScatter',
        data: demands.map((v, i) => ({
          value: [dates[i], v],
          symbolSize: i === selIdx ? 28 : 14,
          itemStyle: {
            color: i === selIdx ? '#fff' : getNodeColor(tl[i]),
            shadowBlur: i === selIdx ? 30 : 12,
            shadowColor: i === selIdx ? 'rgba(255,255,255,0.9)' : getNodeGlow(tl[i]),
          },
        })),
        rippleEffect: {
          brushType: 'stroke',
          scale: 3.5,
          period: 3,
          color: getNodeColor(tl[selIdx]),
        },
        showEffectOn: 'render',
        z: 10,
        zlevel: 1,
      },
    ],
    // 阶段背景
    graphic: buildPhaseGraphics(tl, dates),
  }
})

function getNodeColor(t: TimelineEvent): string {
  if (t.marketDemand >= 85) return '#818cf8'
  if (t.marketDemand >= 70) return '#10b981'
  if (t.marketDemand >= 50) return '#22d3ee'
  return '#f59e0b'
}

function getNodeGlow(t: TimelineEvent): string {
  if (t.marketDemand >= 85) return 'rgba(99,102,241,0.8)'
  if (t.marketDemand >= 70) return 'rgba(16,185,129,0.6)'
  if (t.marketDemand >= 50) return 'rgba(6,182,212,0.5)'
  return 'rgba(245,158,11,0.5)'
}

function buildPhaseGraphics(timeline: TimelineEvent[], dates: string[]) {
  if (timeline.length < 2) return []
  const graphics: any[] = []
  let phase = getPhase(timeline[0].marketDemand)
  let phaseStart = 0

  for (let i = 1; i <= timeline.length; i++) {
    const newPhase = i < timeline.length ? getPhase(timeline[i].marketDemand) : null
    if (newPhase !== phase || i === timeline.length) {
      const phaseColors: Record<string, string> = {
        'emerging': 'rgba(34,211,238,0.06)',
        'growing': 'rgba(99,102,241,0.06)',
        'mature': 'rgba(16,185,129,0.04)',
        'shifting': 'rgba(245,158,11,0.04)',
      }
      const phaseLabels: Record<string, string> = {
        'emerging': '萌芽期',
        'growing': '爆发期',
        'mature': '成熟期',
        'shifting': '转型期',
      }
      if (i - phaseStart >= 1) {
        graphics.push({
          type: 'rect',
          left: ((phaseStart / (timeline.length - 1)) * 90 + 5) + '%',
          top: '8%',
          width: (((i - phaseStart) / (timeline.length - 1)) * 90) + '%',
          height: '75%',
          style: { fill: phaseColors[phase] || 'transparent' },
          z: 0,
        })
        graphics.push({
          type: 'text',
          left: ((phaseStart / (timeline.length - 1)) * 90 + 5 + ((i - phaseStart) / (timeline.length - 1)) * 45) + '%',
          top: '2%',
          style: { text: phaseLabels[phase] || '', fill: '#64748b', fontSize: 10, textAlign: 'center' },
          z: 1,
        })
      }
      phase = newPhase || 'mature'
      phaseStart = i
    }
  }
  return graphics
}

function getPhase(demand: number): string {
  if (demand < 55) return 'emerging'
  if (demand < 75) return 'growing'
  if (demand < 88) return 'mature'
  return 'shifting'
}

// ===== 点击事件 =====
function onChartClick(params: any) {
  if (params.seriesType === 'effectScatter' && params.dataIndex !== undefined) {
    emit('select', params.dataIndex)
  }
}

// ===== 自动播放 =====
function togglePlay() {
  playing.value = !playing.value
  if (playing.value) startPlay()
  else stopPlay()
}

function startPlay() {
  stopPlay()
  playTimer = setInterval(() => {
    playIndex.value = (playIndex.value + 1) % props.timeline.length
    emit('select', playIndex.value)
    if (playIndex.value === 0) { playing.value = false; stopPlay() }
  }, 2000)
}

function stopPlay() {
  if (playTimer) { clearInterval(playTimer); playTimer = null }
}

watch(() => props.selectedIndex, (v) => { if (v !== undefined) playIndex.value = v })

onUnmounted(() => stopPlay())
</script>
