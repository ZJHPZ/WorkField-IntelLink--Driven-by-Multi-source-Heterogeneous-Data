<template>
  <div class="match-radar" :style="{ height: (height || 380) + 'px' }">
    <v-chart
      v-if="option"
      class="w-full h-full"
      :option="option"
      :autoresize="true"
      theme="dark"
      @click="onChartClick"
    />
    <div v-else class="flex items-center justify-center h-full" :style="{ color: 'var(--text-muted)' }">
      请选择对比岗位
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useEChartsTheme } from '@/composables/useEChartsTheme'

use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])
const { brand, brandLight, cyan, tooltipConfig, axisLabel, axisLine, splitLine } = useEChartsTheme()

export interface RadarDimension {
  name: string
  userScore: number
  targetScore: number
  max: number
}

const props = defineProps<{
  dimensions: RadarDimension[]
  userName?: string
  targetName?: string
  height?: number
}>()

const emit = defineEmits<{ (e: 'dimension-click', name: string): void }>()

function onChartClick(params: any) {
  if (params.componentType === 'radar' || params.dimensionName) {
    emit('dimension-click', params.dimensionName || params.name || '')
  }
}

const option = computed(() => {
  if (!props.dimensions.length) return null

  const indicators = props.dimensions.map(d => ({
    name: d.name,
    max: d.max,
  }))

  return {
    tooltip: {
      trigger: 'item' as const,
      ...tooltipConfig.value,
      textStyle: { ...tooltipConfig.value.textStyle, fontSize: 12 },
      formatter: (params: any) => {
        if (!params.value || !Array.isArray(params.value)) return ''
        const dims = props.dimensions
        const isUser = params.seriesName === (props.userName || '你的画像')
        let html = `<div style="font-weight:bold;margin-bottom:6px">${params.seriesName}</div>`
        dims.forEach((d, i) => {
          const val = params.value[i] ?? 0
          const other = isUser ? d.targetScore : d.userScore
          const diff = val - other
          const arrow = diff > 0 ? '▲' : diff < 0 ? '▼' : '='
          const diffColor = diff > 0 ? '#10b981' : diff < 0 ? '#f43f5e' : '#94a3b8'
          html += `<div style="display:flex;justify-content:space-between;gap:12px;font-size:11px">
            <span style="color:#94a3b8">${d.name}</span>
            <span><b>${val}</b> <span style="color:${diffColor}">${arrow}${Math.abs(diff)}</span></span>
          </div>`
        })
        return html
      },
    },
    legend: {
      data: [
        props.userName || '你的画像',
        props.targetName || '目标岗位要求',
      ],
      bottom: 0,
      selectedMode: 'toggle' as const,
      textStyle: { color: axisLabel.value, fontSize: 12 },
      itemGap: 24,
      icon: 'circle',
    },
    radar: {
      center: ['50%', '48%'],
      radius: '65%',
      indicator: indicators,
      axisName: {
        color: axisLabel.value,
        fontSize: 10,
        borderRadius: 3,
        padding: [3, 4],
        formatter: (name: string) => name.length > 8 ? name.slice(0, 7) + '…' : name,
      },
      shape: 'polygon' as const,
      splitNumber: 4,
      axisNameGap: 10,
      splitArea: {
        areaStyle: {
          color: [brand.value + '05', brand.value + '05', brand.value + '0a', brand.value + '0a'],
        },
      },
      axisLine: {
        lineStyle: { color: axisLine.value },
      },
      splitLine: {
        lineStyle: { color: splitLine.value },
      },
    },
    series: [
      {
        type: 'radar',
        name: props.userName || '你的画像',
        data: [
          {
            value: props.dimensions.map(d => d.userScore),
            name: props.userName || '你的画像',
          },
        ],
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: {
          color: brand.value,
          width: 2,
        },
        areaStyle: {
          color: brand.value + '33',
        },
        itemStyle: {
          color: brand.value,
        },
      },
      {
        type: 'radar',
        name: props.targetName || '目标岗位要求',
        data: [
          {
            value: props.dimensions.map(d => d.targetScore),
            name: props.targetName || '目标岗位要求',
          },
        ],
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: {
          color: '#06b6d4',
          width: 2,
        },
        areaStyle: {
          color: 'rgba(6,182,212,0.15)',
        },
        itemStyle: {
          color: '#06b6d4',
        },
      },
    ],
  }
})
</script>

<style scoped>
.match-radar {
  width: 100%;
  height: 380px; /* default, overridden by inline style when height prop is set */
}
</style>
