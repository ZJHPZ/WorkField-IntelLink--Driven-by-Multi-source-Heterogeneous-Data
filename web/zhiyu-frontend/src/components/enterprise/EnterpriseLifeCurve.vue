<template>
  <div class="ent-curve">
    <v-chart
      v-if="chartOption"
      class="w-full"
      style="height: 320px"
      :option="chartOption"
      :autoresize="true"
      @click="onChartClick"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart, EffectScatterChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, GraphicComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { TimelineEvent } from '@/stores/enterprise'

use([LineChart, EffectScatterChart, TooltipComponent, GridComponent, GraphicComponent, CanvasRenderer])

const props = defineProps<{
  timeline: TimelineEvent[]
  selectedIndex?: number
}>()

const emit = defineEmits<{ (e: 'select', index: number): void }>()

// 蓝皮书三色：墨蓝结构线 / 珊瑚当前节点 / 褪色墨次线
const NAVY = '#00094C'
const CORAL = '#C85C56'
const DIM = '#9AA1B1'
const INK_MUTED = '#6B7A99'
const MONO = "'Courier New', monospace"

const chartOption = computed(() => {
  const tl = props.timeline
  if (!tl.length) return null
  const dates = tl.map((t) => t.date)
  const selIdx = props.selectedIndex ?? 0
  const demands = tl.map((t) => t.marketDemand)
  const adoptions = tl.map((t) => t.adoptionRate)

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#D9DDE7',
      borderWidth: 1,
      padding: [10, 14],
      textStyle: { color: '#16213E', fontSize: 12, fontFamily: MONO },
      extraCssText: 'box-shadow:0 4px 14px rgba(0,9,76,0.10);',
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex
        if (idx === undefined) return ''
        const t = tl[idx]
        return `<div style="font-weight:700;font-size:13px;letter-spacing:0.05em;margin-bottom:6px;border-bottom:1px solid #D9DDE7;padding-bottom:4px">${t.label}</div>
          <div>市场需求 · <b style="color:${CORAL}">${t.marketDemand}%</b></div>
          <div style="margin-top:2px">企业采用 · <b>${t.adoptionRate}%</b></div>
          <div style="margin-top:2px">薪资 · <b>${t.salaryRange}</b></div>
          <div style="margin-top:5px;color:#9AA1B1;font-size:11px;max-width:240px">${t.summary}</div>`
      },
    },
    grid: { top: 26, bottom: 32, left: 46, right: 18 },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#D9DDE7' } },
      axisTick: { show: false },
      axisLabel: { color: INK_MUTED, fontSize: 11, fontFamily: MONO, fontWeight: 'bold' },
    },
    yAxis: [
      {
        type: 'value', name: '市场需求 (%)', max: 100,
        nameTextStyle: { color: DIM, fontSize: 9, fontFamily: MONO },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: 'rgba(0,9,76,0.07)' } },
        axisLabel: { color: INK_MUTED, fontSize: 10, fontFamily: MONO },
      },
      {
        type: 'value', name: '采用率 (%)', max: 100,
        nameTextStyle: { color: DIM, fontSize: 9, fontFamily: MONO },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: INK_MUTED, fontSize: 10, fontFamily: MONO },
      },
    ],
    series: [
      // 1. 市场需求 · 面积底
      {
        type: 'line', data: demands, smooth: true, symbol: 'none', lineStyle: { width: 0 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,9,76,0.14)' },
              { offset: 0.6, color: 'rgba(0,9,76,0.03)' },
              { offset: 1, color: 'rgba(0,9,76,0)' },
            ],
          },
        },
        z: 1,
      },
      // 2. 市场需求 · 墨蓝主线
      { type: 'line', data: demands, smooth: true, symbol: 'none', lineStyle: { width: 2.5, color: NAVY }, z: 3 },
      // 3. 企业采用 · 褪色虚线
      {
        type: 'line', data: adoptions, smooth: true, symbol: 'none', yAxisIndex: 1,
        lineStyle: { width: 1.5, color: DIM, type: 'dashed' }, z: 2,
      },
      // 4. 节点：当前=珊瑚印章涟漪 / 其余=墨蓝暗点
      {
        type: 'effectScatter',
        data: demands.map((v, i) => ({
          value: [dates[i], v],
          symbolSize: i === selIdx ? 12 : 6,
          itemStyle: i === selIdx
            ? { color: CORAL, borderColor: '#FFFFFF', borderWidth: 2, shadowBlur: 8, shadowColor: 'rgba(200,92,86,0.5)' }
            : { color: NAVY, opacity: 0.45 },
        })),
        rippleEffect: { brushType: 'stroke', scale: 3, period: 3, color: CORAL },
        showEffectOn: 'render',
        z: 10,
        zlevel: 1,
      },
    ],
    graphic: buildPhaseGraphics(tl, dates),
  }
})

function getPhase(demand: number): string {
  if (demand < 55) return 'emerging'
  if (demand < 75) return 'growing'
  if (demand < 88) return 'mature'
  return 'shifting'
}

function buildPhaseGraphics(timeline: TimelineEvent[], dates: string[]) {
  if (timeline.length < 2) return []
  const graphics: any[] = []
  let phase = getPhase(timeline[0].marketDemand)
  let phaseStart = 0
  for (let i = 1; i <= timeline.length; i++) {
    const newPhase = i < timeline.length ? getPhase(timeline[i].marketDemand) : null
    if (newPhase !== phase || i === timeline.length) {
      const labels: Record<string, string> = { emerging: '萌芽期', growing: '爆发期', mature: '成熟期', shifting: '转型期' }
      if (i - phaseStart >= 1) {
        graphics.push({
          type: 'rect',
          left: ((phaseStart / (timeline.length - 1)) * 90 + 5) + '%',
          top: '8%',
          width: (((i - phaseStart) / (timeline.length - 1)) * 90) + '%',
          height: '78%',
          style: { fill: 'rgba(0,9,76,0.03)' },
          z: 0,
        })
        graphics.push({
          type: 'text',
          left: ((phaseStart / (timeline.length - 1)) * 90 + 5 + ((i - phaseStart) / (timeline.length - 1)) * 45) + '%',
          top: '1%',
          style: { text: labels[phase], fill: DIM, fontSize: 9, textAlign: 'center', fontFamily: MONO },
          z: 1,
        })
      }
      phase = newPhase || 'mature'
      phaseStart = i
    }
  }
  return graphics
}

function onChartClick(params: any) {
  if (params.seriesType === 'effectScatter' && params.dataIndex !== undefined) {
    emit('select', params.dataIndex)
  }
}
</script>
