<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">PROFILE</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">技能画像</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ store.skillCount }} SKILLS · +{{ growthNetGain }} SINCE {{ startLabel }}</span>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- 用户身份 + 成长曲线 -->
      <div class="lg:col-span-2 space-y-4">
        <div class="panel-bridge p-5 shadow-deep">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-14 h-14 rounded-sm bg-brand-gradient flex items-center justify-center text-white font-bold text-xl shadow-lg" style="box-shadow:0 6px 20px color-mix(in srgb, var(--brand-500) 30%, transparent)">{{ userName.charAt(0) }}</div>
            <div>
              <div class="flex items-center gap-2"><span class="tag-plate">ID</span><h2 class="text-base font-bold" :style="{color:'var(--text-primary)'}">{{ userName }}</h2></div>
              <p class="text-sm" :style="{color:'var(--text-secondary)'}">{{ userTitle }}</p>
              <div class="flex items-center gap-3 mt-1 text-xs font-mono" :style="{color:'var(--text-muted)'}"><span class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-brand-400"></span>{{ userWorkYears }}</span><span class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-cyan-400"></span>{{ userEducation }}</span><span class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-mint-400"></span>{{ userLocation }}</span></div>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--brand-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--brand-500) 10%, transparent)"><div class="data-giant text-xl text-brand-500 data-segment">{{ store.skillCount }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">SKILLS</div></div>
            <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--mint-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--mint-500) 10%, transparent)"><div class="data-giant text-xl text-mint-500 data-segment">{{ store.healthySkillCount }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">HEALTHY</div></div>
            <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--brand-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--brand-500) 10%, transparent)"><div class="data-giant text-xl text-brand-500">{{ topCategory }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">TOP CAT</div></div>
            <div class="p-3 text-center rounded-sm" style="background:color-mix(in srgb, var(--cyan-500) 04%, transparent);border:1px solid color-mix(in srgb, var(--cyan-500) 10%, transparent)"><div class="data-giant text-xl text-cyan-500 data-segment">+{{ growthNetGain }}</div><div class="text-xs font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">GROWTH</div></div>
          </div>
          <!-- 简历上传 → 跳转简历解析页 -->
          <div class="border-2 border-dashed rounded-sm p-4 text-center transition-all cursor-pointer group hover:border-brand-400" :style="{borderColor:'var(--border-color)'}" @click="goResume">
            <svg class="w-8 h-8 mx-auto mb-1.5 opacity-30 group-hover:opacity-60 transition-opacity" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-linecap="round"/><polyline points="14 2 14 8 20 8" stroke-linecap="round"/><line x1="12" y1="18" x2="12" y2="12" stroke-linecap="round"/><line x1="9" y1="15" x2="15" y2="15" stroke-linecap="round"/></svg>
            <p class="text-xs font-bold font-mono" :style="{color:'var(--text-secondary)'}">上传简历</p>
            <p class="text-xs mt-0.5 font-mono" :style="{color:'var(--text-muted)'}">前往简历解析 · PDF · WORD</p>
          </div>
        </div>
        <!-- 成长曲线 -->
        <div class="panel-bridge p-4 shadow-deep">
          <div class="flex items-center justify-between mb-2">
            <PanelHeader label="CURVE" title="技能增长曲线" color="brand" margin="none" />
            <span class="text-[9px] font-mono tracking-widest flex items-center gap-3" :style="{color:'var(--text-muted)'}">
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm" style="background:var(--brand-500)"></span>本期新增</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full" style="background:var(--cyan-500)"></span>累计技能</span>
            </span>
          </div>
          <div style="height:150px">
            <v-chart v-if="growthChartOption" class="w-full h-full" :option="growthChartOption" :autoresize="true" theme="dark" />
          </div>
          <!-- 最新一期新增技能 -->
          <div class="mt-2.5 pt-2.5 flex items-start gap-2" style="border-top:1px dashed var(--border-color)">
            <span class="text-[9px] font-mono tracking-widest mt-1.5 shrink-0" :style="{color:'var(--text-muted)'}">NEWEST</span>
            <div class="flex flex-wrap gap-1">
              <span v-for="s in latestSkills" :key="s" class="tag-plate" style="font-size:9px;padding:2px 7px;color:var(--mint-500);border-color:color-mix(in srgb, var(--mint-500) 35%, transparent)">{{ s }}</span>
              <span v-if="!latestSkills.length" class="text-xs font-mono" :style="{color:'var(--text-muted)'}">—</span>
            </div>
          </div>
          <!-- 增长速率 readouts -->
          <div class="grid grid-cols-2 gap-2 mt-2.5">
            <div class="p-2 text-center rounded-sm" style="background:color-mix(in srgb, var(--brand-500) 05%, transparent);border:1px solid color-mix(in srgb, var(--brand-500) 12%, transparent)">
              <div class="data-giant text-base text-brand-500 data-segment">{{ avgGain }}/期</div>
              <div class="text-[9px] font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">AVG GAIN</div>
            </div>
            <div class="p-2 text-center rounded-sm" style="background:color-mix(in srgb, var(--cyan-500) 05%, transparent);border:1px solid color-mix(in srgb, var(--cyan-500) 12%, transparent)">
              <div class="data-giant text-base text-cyan-500 data-segment">{{ peakGain }}</div>
              <div class="text-[9px] font-mono tracking-widest mt-0.5" :style="{color:'var(--text-muted)'}">PEAK · {{ peakLabel }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 技能遥测矩阵 -->
      <SkillMatrix :skills="store.skills" class="lg:col-span-3" />
    </div>

    <!-- 技能详情卡片 — 清除网格背景，用阴影+色条+交错层次区分 -->
    <div class="panel-industrial p-5 shadow-deep view-section">
      <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
      <div class="relative z-[1]">
      <div class="flex items-center justify-between mb-5">
        <PanelHeader label="DETAIL" title="技能详情" margin="none" />
        <div class="flex gap-2">
          <button v-for="f in skillFilters" :key="f.key" class="text-xs px-3 py-1.5 font-mono transition-all rounded-sm" :class="activeFilter===f.key?'bg-brand-500 text-white':''" :style="activeFilter===f.key?{}:{color:'var(--text-muted)',border:'1px solid var(--border-color)'}" @click="activeFilter=f.key">{{ f.label }}</button>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(skill, idx) in filteredSkills" :key="skill.id"
          class="p-4 transition-all lift-on-hover relative overflow-hidden shadow-deep"
          :class="selectedSkillId===skill.id?'panel-neon':''"
          :style="{
            background: 'var(--bg-card)',
            border: `2px solid transparent`,
            borderImage: `linear-gradient(135deg, ${getStatusColor(skill.status)}60, transparent 60%, transparent 80%, ${getStatusColor(skill.status)}30) 1`,
            outline: `1px solid ${getStatusColor(skill.status)}20`,
            outlineOffset: '-4px',
            filter: skill.level==='expert' ? `drop-shadow(0 0 6px ${getStatusColor(skill.status)}40)` : 'none',
          }">
          <!-- 模块铆钉 -->
          <div class="absolute top-2 left-2 w-1.5 h-1.5 rounded-full" style="background:radial-gradient(circle at 35% 35%, rgba(255,255,255,0.5), rgba(0,0,0,0.3));box-shadow:0 1px 2px rgba(0,0,0,0.2)"></div>
          <div class="absolute top-2 right-2 w-1.5 h-1.5 rounded-full" style="background:radial-gradient(circle at 35% 35%, rgba(255,255,255,0.5), rgba(0,0,0,0.3));box-shadow:0 1px 2px rgba(0,0,0,0.2)"></div>
          <!-- 微电路纹 — 右上角 -->
          <div class="absolute inset-0 pointer-events-none" style="opacity:0.05">
            <div class="absolute top-3 right-3 w-5 h-px" :style="{background:getStatusColor(skill.status)}"></div>
            <div class="absolute top-3 right-3 w-px h-5" :style="{background:getStatusColor(skill.status)}"></div>
            <div class="absolute top-[13px] right-[13px] w-1 h-1 rounded-full" :style="{background:getStatusColor(skill.status)}"></div>
          </div>
          <!-- 状态色条 -->
          <div class="absolute top-0 left-0 right-0 h-0.5" :style="{background: getStatusColor(skill.status)}"></div>

          <!-- 头部：名称 + 类别 + 状态 -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <!-- 等级点 — 大小代表水平 -->
                <span class="shrink-0 rounded-full" :style="{width:getLevelDot(skill.level)+'px',height:getLevelDot(skill.level)+'px',background:getStatusColor(skill.status),boxShadow:'0 0 6px '+getStatusColor(skill.status)}"></span>
                <h4 class="text-sm font-bold truncate" :style="{color:'var(--text-primary)'}">{{ skill.name }}</h4>
              </div>
              <span class="text-xs font-mono ml-[22px]" :style="{color:'var(--text-muted)'}">{{ skill.category }} · {{ skill.yearsOfExperience }}年</span>
            </div>
            <span class="tag-tilted shrink-0 ml-2"
              :style="{color:getStatusColor(skill.status),borderColor:getStatusColor(skill.status)+'40',fontSize:'10px'}">
              {{ getStatusLabel(skill.status) }}
            </span>
          </div>

          <!-- 三条指标 — 交替视觉比重 -->
          <div class="space-y-2.5">
            <!-- 掌握程度 — 最粗的条 -->
            <div>
              <div class="flex justify-between text-xs font-mono mb-0.5">
                <span :style="{color:'var(--text-muted)'}">LEVEL</span>
                <span class="font-bold" :style="{color:'var(--text-primary)'}">{{ skill.level==='expert'?'EXPERT':skill.level==='advanced'?'ADVANCED':skill.level==='intermediate'?'INTERMEDIATE':'BASIC' }}</span>
              </div>
              <div class="h-2 progress-track-dark rounded-sm" style="background:var(--bg-secondary)">
                <div class="h-full rounded-sm transition-all duration-700" :style="{width:getLevelPct(skill.level)+'%',background:'linear-gradient(90deg,var(--brand-400),var(--brand-600))',boxShadow:'0 0 8px color-mix(in srgb, var(--brand-500) 20%, transparent)'}"></div>
              </div>
            </div>
            <!-- 市场需求 — 中等条 -->
            <div>
              <div class="flex justify-between text-xs font-mono mb-0.5">
                <span :style="{color:'var(--text-muted)'}">DEMAND</span>
                <span class="font-bold" :style="{color:'var(--text-primary)'}">{{ skill.marketDemand }}/100</span>
              </div>
              <div class="h-1.5 progress-track-dark rounded-sm" style="background:var(--bg-secondary)">
                <div class="h-full rounded-sm transition-all duration-700" :style="{width:skill.marketDemand+'%',background:'linear-gradient(90deg,var(--cyan-400),var(--cyan-600))'}"></div>
              </div>
            </div>
            <!-- 保鲜度 — 细条 + 颜色编码 -->
            <div>
              <div class="flex justify-between text-xs font-mono mb-0.5">
                <span :style="{color:'var(--text-muted)'}">FRESH</span>
                <span class="font-bold" :style="{color:skill.freshness>=70?'var(--mint-500)':skill.freshness>=40?'#f59e0b':'#f43f5e'}">{{ skill.freshness }}%</span>
              </div>
              <div class="h-1 progress-track-dark rounded-sm" style="background:var(--bg-secondary)">
                <div class="h-full rounded-sm transition-all duration-700" :style="{width:skill.freshness+'%',background:skill.freshness>=70?'linear-gradient(90deg,var(--mint-400),var(--mint-600))':skill.freshness>=40?'linear-gradient(90deg,#fbbf24,#f59e0b)':'linear-gradient(90deg,#fb7185,#f43f5e)'}"></div>
              </div>
            </div>
          </div>

          <button class="w-full mt-3 pt-2 text-xs font-mono transition-all hover:text-brand-500 text-center" style="border-top:1px solid var(--border-color);color:var(--text-muted)" @click.stop="selectedSkillId=selectedSkillId===skill.id?null:skill.id">
            {{ selectedSkillId===skill.id?'— COLLAPSE —':'— EXPAND —' }}
          </button>
          <!-- 展开面板：市场热度 + 相关岗位 -->
          <Transition name="slide-up">
            <div v-if="selectedSkillId===skill.id" class="mt-3 pt-3 space-y-2.5" style="border-top:1px dashed var(--border-color)">
              <div class="flex items-center justify-between text-xs">
                <span class="font-mono" :style="{color:'var(--text-muted)'}">MARKET DF</span>
                <span class="font-mono font-bold" :style="{color:'var(--text-primary)'}">{{ skill.marketDf }} 次/千JD</span>
              </div>
              <div class="h-1.5 rounded-sm" style="background:var(--bg-secondary)">
                <div class="h-full rounded-sm transition-all duration-700" :style="{width:Math.min(skill.marketDf/3,100)+'%',background:'linear-gradient(90deg,var(--cyan-400),var(--brand-500))'}"></div>
              </div>
              <div class="flex items-center justify-between text-xs">
                <span class="font-mono" :style="{color:'var(--text-muted)'}">EMERGENCE</span>
                <span class="font-mono font-bold" :class="skill.emergence>0.5?'text-mint-500':skill.emergence>0.2?'text-amber-500':'text-rose-500'">{{ (skill.emergence*100).toFixed(0) }}%</span>
              </div>
              <div class="flex items-center justify-between text-xs">
                <span class="font-mono" :style="{color:'var(--text-muted)'}">CONFIDENCE</span>
                <span class="font-mono font-bold" :style="{color:'var(--text-primary)'}">{{ (skill.confidence*100).toFixed(0) }}%</span>
              </div>
              <div class="flex items-center justify-between text-xs">
                <span class="font-mono" :style="{color:'var(--text-muted)'}">FIRST SEEN</span>
                <span class="font-mono" :style="{color:'var(--text-secondary)'}">{{ skill.firstSeen }}</span>
              </div>
              <div class="flex flex-wrap gap-1 mt-1">
                <span v-for="tag in getRelatedPositions(skill)" :key="tag" class="text-xs px-2 py-0.5 font-mono rounded-sm" style="background:color-mix(in srgb, var(--brand-500) 06%, transparent);color:var(--brand-400);border:1px solid color-mix(in srgb, var(--brand-500) 15%, transparent)">{{ tag }}</span>
              </div>
            </div>
          </Transition>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePersonalStore } from '@/stores/personal'
import type { SkillItem } from '@/stores/personal'
import { useScrollReveal } from '@/composables/useScrollReveal'
import SkillMatrix from '@/components/personal/SkillMatrix.vue'
import PanelHeader from '@/components/common/PanelHeader.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useEChartsTheme } from '@/composables/useEChartsTheme'
use([LineChart, BarChart, GridComponent, TooltipComponent, CanvasRenderer])
const { brand, brandDark, cyan, tooltipConfig, axisLabel, axisLine, splitLine } = useEChartsTheme()
const store = usePersonalStore()
useScrollReveal()

const userName = ref('张明'); const userTitle = ref('高级前端开发工程师')
const userWorkYears = ref('6Y'); const userEducation = ref('本科'); const userLocation = ref('北京')

const router = useRouter()
function goResume(){ router.push('/personal/resume') }

const activeFilter = ref('all')
const skillFilters = [{key:'all',label:'ALL'},{key:'healthy',label:'HEALTHY'},{key:'alert',label:'ALERT'},{key:'expert',label:'EXPERT'}]
const filteredSkills = computed(()=>{const a=store.skills;switch(activeFilter.value){case'healthy':return a.filter(s=>s.status==='healthy'||s.status==='matched');case'alert':return a.filter(s=>s.status==='alert');case'expert':return a.filter(s=>s.level==='expert'||s.level==='advanced');default:return a}})
const selectedSkillId = ref<string|null>(null)

// ── 技能增长曲线（Silent Fallback：store.growth 真实时间线优先，demo 兜底）──
interface GrowthPoint { date: string; skillsGained: number; skills: string[]; cumulativeCount: number; description: string }
const demoGrowth: GrowthPoint[] = [
  { date: '2022H1', skillsGained: 3, skills: ['Python', 'SQL', 'HTML/CSS'], cumulativeCount: 3, description: '初识编程 — 建立 Web 基础' },
  { date: '2022H2', skillsGained: 1, skills: ['JavaScript'], cumulativeCount: 4, description: '补齐前端脚本基础' },
  { date: '2023H1', skillsGained: 2, skills: ['Vue', 'Node.js'], cumulativeCount: 6, description: '进入工程化前端开发' },
  { date: '2023H2', skillsGained: 2, skills: ['React', 'TypeScript'], cumulativeCount: 8, description: '类型化与组件化双线推进' },
  { date: '2024H1', skillsGained: 1, skills: ['SQL 进阶'], cumulativeCount: 9, description: '打通数据链路' },
  { date: '2024H2', skillsGained: 2, skills: ['深度学习', 'NLP'], cumulativeCount: 11, description: '切入 AI/ML 方向' },
  { date: '2025H1', skillsGained: 1, skills: ['Docker/K8s'], cumulativeCount: 12, description: '补齐工程化交付能力' },
  { date: '2025H2', skillsGained: 2, skills: ['系统设计', 'Go'], cumulativeCount: 14, description: '架构视野扩展' },
  { date: '2026H1', skillsGained: 2, skills: ['MLOps', 'Kubernetes'], cumulativeCount: 16, description: 'ML 工程化深入' },
]
const growthTimeline = computed<GrowthPoint[]>(() =>
  store.growth?.timeline?.length ? (store.growth.timeline as GrowthPoint[]) : demoGrowth,
)
const growthNetGain = computed(() => {
  const t = growthTimeline.value
  return t.length ? t[t.length - 1].cumulativeCount - t[0].cumulativeCount : 0
})
const startLabel = computed(() => growthTimeline.value[0]?.date || '2022')
const latestSkills = computed(() => growthTimeline.value[growthTimeline.value.length - 1]?.skills || [])
const avgGain = computed(() => {
  const t = growthTimeline.value
  return t.length ? (t.reduce((a, p) => a + p.skillsGained, 0) / t.length).toFixed(1) : '0.0'
})
const peakGain = computed(() => growthTimeline.value.reduce((b, p) => Math.max(b, p.skillsGained), 0))
const peakLabel = computed(() => growthTimeline.value.find(p => p.skillsGained === peakGain.value)?.date || '—')
const maxCumulative = computed(() => growthTimeline.value.reduce((b, p) => Math.max(b, p.cumulativeCount), 1))

const growthChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis' as const,
    ...tooltipConfig.value,
    formatter: (params: any) => {
      const arr = Array.isArray(params) ? params : [params]
      const first = arr[0]
      const pt = growthTimeline.value[first?.dataIndex] || null
      const rows = arr.map((p: any) =>
        `<div style="display:flex;align-items:center;gap:6px;margin:2px 0"><span style="display:inline-block;width:8px;height:8px;background:${p.color}"></span>${p.seriesName}: <b>${p.value}</b></div>`,
      ).join('')
      const chips = pt?.skills?.length
        ? `<div style="margin-top:4px;color:#94a3b8">↳ ${pt.skills.join(' · ')}</div>`
        : ''
      const desc = pt?.description
        ? `<div style="margin-top:2px;font-size:10px;color:#64748b">${pt.description}</div>`
        : ''
      return `<div style="font-weight:bold;margin-bottom:4px">${first?.name || ''}</div>${rows}${chips}${desc}`
    },
  },
  grid: { left: 30, right: 10, top: 8, bottom: 24 },
  xAxis: {
    type: 'category' as const,
    data: growthTimeline.value.map(p => p.date),
    axisLabel: { color: axisLabel.value, fontSize: 9, rotate: 30 },
    axisLine: { lineStyle: { color: axisLine.value } },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value' as const,
    max: maxCumulative.value + 1,
    axisLabel: { color: axisLabel.value, fontSize: 9 },
    splitLine: { lineStyle: { color: splitLine.value } },
    axisLine: { show: false },
  },
  series: [
    {
      type: 'bar',
      name: '本期新增',
      data: growthTimeline.value.map(p => p.skillsGained),
      barWidth: '42%',
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: brand.value },
            { offset: 1, color: brandDark.value },
          ],
        },
        borderRadius: [2, 2, 0, 0],
      },
    },
    {
      type: 'line',
      name: '累计技能数',
      data: growthTimeline.value.map(p => p.cumulativeCount),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: cyan.value, width: 2, shadowBlur: 6, shadowColor: cyan.value + '66' },
      itemStyle: { color: cyan.value, borderColor: '#0e7490', borderWidth: 1 },
      markPoint: {
        symbol: 'circle',
        symbolSize: 9,
        itemStyle: {
          color: cyan.value,
          borderColor: '#fff',
          borderWidth: 1.5,
          shadowBlur: 10,
          shadowColor: cyan.value + 'aa',
        },
        data: [{ type: 'max', name: '当前' }],
        label: { show: true, color: cyan.value, fontSize: 9, position: 'top', formatter: '当前 {c}' },
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: cyan.value + '26' },
            { offset: 1, color: cyan.value + '00' },
          ],
        },
      },
    },
  ],
}))
const topCategory = computed(()=>store.topSkillCategory)

function getStatusColor(s:string){const m:Record<string,string>={healthy:'#10b981',matched:'var(--brand-500)',alert:'#f59e0b',missing_high:'#f43f5e',missing_low:'#f97316'};return m[s]||'#6b7280'}
function getStatusBg(s:string){const m:Record<string,string>={healthy:'color-mix(in srgb, var(--mint-500) 06%, transparent)',matched:'color-mix(in srgb, var(--brand-500) 06%, transparent)',alert:'color-mix(in srgb, var(--amber-500) 06%, transparent)',missing_high:'color-mix(in srgb, var(--rose-500) 06%, transparent)',missing_low:'rgba(249,115,22,0.06)'};return m[s]||'rgba(107,114,128,0.06)'}
function getStatusLabel(s:string){const m:Record<string,string>={healthy:'HEALTHY',matched:'MATCHED',alert:'ALERT',missing_high:'HIGH GAP',missing_low:'LOW GAP'};return m[s]||s}
function getLevelPct(l:string){const m:Record<string,number>={expert:95,advanced:78,intermediate:50,basic:25};return m[l]||30}
function getLevelDot(l:string){const m:Record<string,number>={expert:10,advanced:8,intermediate:6,basic:4};return m[l]||5}
function getRelatedPositions(skill:SkillItem):string[]{const posMap:Record<string,string[]>={'编程语言':['全栈开发','后端工程师','AI工程师'],'AI/ML':['AI工程师','ML Engineer','算法工程师'],'前端':['前端开发','全栈开发'],'数据':['数据分析师','大数据工程师'],'DevOps':['DevOps工程师','SRE'],'架构':['技术总监','架构师']};return posMap[skill.category]||['相关岗位']}

onMounted(() => { store.fetchSkills(); store.fetchGrowth() })
</script>
