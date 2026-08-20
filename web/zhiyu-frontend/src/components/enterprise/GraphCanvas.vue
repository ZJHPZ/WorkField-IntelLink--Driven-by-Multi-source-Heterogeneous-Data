<template>
  <div class="ent-curve h-full">
    <v-chart
      v-if="chartOption"
      class="w-full h-full"
      :option="chartOption"
      :autoresize="true"
      @click="onClick"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ChartNode, ChartLink } from '@/utils/graph'

use([GraphChart, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  nodes: ChartNode[]
  links: ChartLink[]
  view: 'techstack' | 'level' | 'heat'
  hiddenRels: string[]
  query: string
}>()

const emit = defineEmits<{ (e: 'node-click', node: ChartNode): void }>()

// 蓝皮书三色 + 结构灰阶
const NAVY = '#00094C'
const NAVY_900 = '#121A57'
const NAVY_700 = '#1E2A5A'
const CORAL = '#C85C56'
const INK = '#16213E'
const INK_MUTED = '#5B6478'
const DIM = '#9AA1B1'
const RULE = '#D9DDE7'
const MONO = "'Courier New', monospace"

// 技术栈视图：栈内暗哑描边色（蓝皮书族内，珊瑚仅作高亮不参与）
const STACK_COLORS: Record<string, string> = {
  'AI': NAVY,
  '前端': '#D68984',
  '后端': NAVY_700,
  '数据': INK_MUTED,
  'DevOps': DIM,
  '质量': '#C8CDD9',
}

const chartOption = computed(() => {
  const view = props.view
  const q = (props.query || '').trim().toLowerCase()
  const hidden = new Set(props.hiddenRels)

  const data = props.nodes.map((n) => {
    let itemStyle = { ...n.itemStyle }
    let label = { ...n.label }
    let size = n.symbolSize

    // 搜索：未命中淡化
    if (q && !n.name.toLowerCase().includes(q)) {
      itemStyle = { ...itemStyle, opacity: 0.12 }
    }

    if (n.kind === 'skill') {
      const em = n._metrics?.emergence ?? 0.5
      if (view === 'techstack') {
        const c = STACK_COLORS[n._stack ?? ''] || NAVY
        itemStyle = { ...itemStyle, borderColor: c, borderWidth: 1.8 }
      } else if (view === 'level') {
        itemStyle = { ...itemStyle, borderWidth: 1, opacity: (itemStyle.opacity ?? 1) * 0.55 }
        label = { ...label, color: INK_MUTED, fontSize: 9 }
      } else {
        // heat：新兴度驱动
        if (em >= 0.7) {
          itemStyle = { ...itemStyle, borderColor: CORAL, borderWidth: 2, shadowColor: 'rgba(200,92,86,0.55)', shadowBlur: 12 }
          size = n.symbolSize * 1.15
        } else if (em >= 0.45) {
          itemStyle = { ...itemStyle, borderColor: NAVY, borderWidth: 1.8 }
        } else {
          itemStyle = { ...itemStyle, borderColor: DIM, borderWidth: 1 }
        }
      }
    } else if (n.kind === 'position') {
      if (view === 'level') {
        const lv = parseInt(String(n._level || 'P6').replace('P', '')) || 6
        const grad = ['#9AA1B1', NAVY_700, NAVY_900, NAVY]
        itemStyle = { ...itemStyle, color: grad[Math.min(3, Math.max(0, lv - 5))] }
      } else if (view === 'heat') {
        itemStyle = { ...itemStyle, color: NAVY_900 }
      }
    }

    return { id: n.id, name: n.name, symbolSize: size, itemStyle, label, value: n.kind }
  })

  const links = props.links
    .filter((l) => !hidden.has(l.rel))
    .map((l) => ({ source: l.source, target: l.target, lineStyle: l.lineStyle }))

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF',
      borderColor: RULE,
      borderWidth: 1,
      padding: [10, 14],
      textStyle: { color: INK, fontSize: 12, fontFamily: MONO },
      extraCssText: 'box-shadow:0 4px 14px rgba(0,9,76,0.12);',
      formatter: (params: any) => {
        if (params.dataType === 'edge' || !params.data) return ''
        const n = params.data as ChartNode
        const m = n._metrics || {}
        if (n.kind === 'skill') {
          const ver = n._verification === 'confirmed' ? '已验证' : n._verification === 'rejected' ? '已驳回' : '待核验'
          const verColor = n._verification === 'confirmed' ? NAVY : n._verification === 'rejected' ? DIM : CORAL
          return `<div style="font-weight:700;font-size:13px;letter-spacing:0.04em;margin-bottom:6px;border-bottom:1px solid ${RULE};padding-bottom:4px">${n.name}</div>
            <div>技能 · <span style="color:${verColor}">${ver}</span></div>
            <div style="margin-top:2px">置信度 · <b>${fmtPct(m.confidence)}</b></div>
            <div style="margin-top:2px">新兴度 · <b style="color:${CORAL}">${fmtPct(m.emergence)}</b></div>
            <div style="margin-top:2px">半衰期 · <b>${m.halfLife ?? '—'} 月</b></div>
            <div style="margin-top:2px">所属栈 · <b>${n._stack || '—'}</b></div>`
        }
        if (n.kind === 'position') {
          return `<div style="font-weight:700;font-size:13px;letter-spacing:0.04em;margin-bottom:6px;border-bottom:1px solid ${RULE};padding-bottom:4px">${n.name}</div>
            <div>岗位 · <span style="color:${n._posType === '新兴' ? CORAL : NAVY}">${n._posType}</span></div>
            <div style="margin-top:2px">等级 · <b>${n._level || '—'}</b></div>
            <div style="margin-top:2px">市场需求 · <b style="color:${CORAL}">${fmtPct(m.marketDemand)}</b></div>
            <div style="margin-top:2px">匹配率 · <b>${fmtPct(m.matchRate)}</b></div>`
        }
        if (n.kind === 'stack') {
          return `<div style="font-weight:700;font-size:13px;letter-spacing:0.04em;margin-bottom:6px;border-bottom:1px solid ${RULE};padding-bottom:4px">技术栈</div>
            <div>${n.name}</div>`
        }
        return `<div>${n.name}</div>`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data,
        links,
        roam: true,
        draggable: true,
        force: { repulsion: 300, gravity: 0.08, edgeLength: [120, 250], friction: 0.6, layoutAnimation: true },
        emphasis: { focus: 'adjacency', itemStyle: { shadowColor: 'rgba(0,9,76,0.18)', shadowBlur: 14 } },
        lineStyle: { color: 'source' },
        label: { show: true, position: 'bottom', distance: 6, overflow: 'truncate', width: 90 },
        animationDurationUpdate: 800,
        animationEasingUpdate: 'cubicInOut',
      },
    ],
  }
})

function fmtPct(v: any): string {
  return v === undefined || v === null ? '—' : Math.round(Number(v) * 100) + '%'
}

function onClick(params: any) {
  if (params.dataType === 'edge' || !params.data) return
  const n = params.data as ChartNode
  if (n.kind === 'evidence') return
  emit('node-click', n)
}
</script>
