<template>
  <div class="space-y-4">
    <!-- ═══════════════════════ 指挥台头部 ═══════════════════════ -->
    <div class="panel-hazard p-4 shadow-deep relative overflow-hidden">
      <div class="relative z-[3] flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1.5">
            <div class="w-8 h-8 panel-neon flex items-center justify-center" style="border-color:var(--brand-500)">
              <span class="text-xs font-bold" style="color:var(--brand-400)">A</span>
            </div>
            <span class="text-[10px] font-mono" style="color:var(--text-muted)">VS</span>
            <div class="w-8 h-8 panel-neon flex items-center justify-center" style="border-color:var(--cyan-500)">
              <span class="text-xs font-bold" style="color:var(--cyan-400)">B</span>
            </div>
          </div>
          <div>
            <h1 class="text-sm font-bold tracking-[0.15em] uppercase" style="color:var(--text-primary)">Position Battle Station</h1>
            <p class="text-[9px] tracking-wider" style="color:var(--text-muted)">多维度对峙分析 · 选择 2 个岗位开始</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <span class="tag-plate" style="color:var(--amber-400);border-color:var(--amber-500)">{{ selectedPositions.length }} PICKED</span>
          <button v-if="selectedPositions.length" @click="clearSelection" class="text-[9px] font-mono tracking-wider hover:text-rose-400" style="color:var(--text-muted)">[ RESET ]</button>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ 岗位选择条 ═══════════════════════ -->
    <div class="panel-bridge p-3 shadow-deep">
      <div class="flex items-center gap-3 overflow-x-auto">
        <span class="text-[8px] tracking-widest shrink-0" style="color:var(--text-muted)">SELECT:</span>
        <button v-for="pos in allPositions" :key="pos.id" @click="togglePosition(pos)"
          class="shrink-0 text-[10px] px-3 py-1.5 font-mono transition-all"
          :style="isSelected(pos)
            ? {background: getPositionColor(getIndex(pos)), color:'white', boxShadow:'0 0 10px '+getPositionColor(getIndex(pos))+'60'}
            : {background:'var(--bg-secondary)',color:'var(--text-muted)',border:'1px solid var(--border-color)'}">
          {{ pos.name }}
          <span v-if="isSelected(pos)" class="ml-1 text-[8px]">✓</span>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════ 对峙主区 ═══════════════════════ -->
    <!-- 默认展示前两个 demo 岗位的对比 -->
    <div class="space-y-4">

      <!-- 对峙卡片行 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-0">
        <!-- 岗位 A -->
        <div class="panel-industrial shadow-deep p-5 relative" style="border-top:3px solid var(--brand-500)">
          <div class="rivet" style="top:6px;left:6px"></div>
          <div class="relative z-[1]">
            <div class="flex items-center gap-2 mb-2">
              <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">A</span>
              <span class="text-xs font-bold" style="color:var(--text-primary)">{{ posA.name }}</span>
            </div>
            <div class="data-segment text-3xl mb-1" style="color:var(--brand-500);text-shadow:0 0 15px rgba(99,102,241,0.3)">{{ posA.matchRate }}%</div>
            <div class="text-[9px] font-mono" style="color:var(--text-muted)">{{ posA.salary }} · {{ posA.skills.length }} skills</div>
            <div class="flex flex-wrap gap-1 mt-2">
              <span v-for="s in posA.matchedSkills.slice(0,4)" :key="s" class="text-[8px] px-1.5 py-0.5 font-mono" style="background:rgba(16,185,129,0.08);color:var(--mint-500);border:1px solid rgba(16,185,129,0.2)">{{ s }}</span>
            </div>
          </div>
        </div>

        <!-- 中央对决区 -->
        <div class="panel-neon panel-circuit shadow-deep p-5 flex flex-col items-center justify-center relative">
          <div class="holo-overlay absolute inset-0 z-0 opacity-15"></div>
          <div class="relative z-[3] text-center">
            <div class="text-[8px] tracking-widest mb-2" style="color:var(--text-muted)">DIFFERENCE</div>
            <div class="data-segment text-2xl mb-1" :style="{color: posA.matchRate > posB.matchRate ? 'var(--brand-500)' : 'var(--cyan-500)'}">
              {{ Math.abs(posA.matchRate - posB.matchRate) }}%
            </div>
            <div class="text-[9px] font-mono" style="color:var(--text-muted)">
              {{ posA.matchRate > posB.matchRate ? posA.name : posB.name }} 领先
            </div>
            <!-- 技能重叠数 -->
            <div class="mt-3 pt-3" style="border-top:1px dashed var(--border-color)">
              <div class="data-segment text-lg text-mint-500">{{ commonSkills.length }}</div>
              <div class="text-[8px] tracking-widest" style="color:var(--text-muted)">共同技能</div>
            </div>
          </div>
        </div>

        <!-- 岗位 B -->
        <div class="panel-industrial shadow-deep p-5 relative" style="border-top:3px solid var(--cyan-500)">
          <div class="rivet" style="top:6px;left:6px"></div>
          <div class="relative z-[1]">
            <div class="flex items-center gap-2 mb-2">
              <span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">B</span>
              <span class="text-xs font-bold" style="color:var(--text-primary)">{{ posB.name }}</span>
            </div>
            <div class="data-segment text-3xl mb-1" style="color:var(--cyan-500);text-shadow:0 0 15px rgba(6,182,212,0.3)">{{ posB.matchRate }}%</div>
            <div class="text-[9px] font-mono" style="color:var(--text-muted)">{{ posB.salary }} · {{ posB.skills.length }} skills</div>
            <div class="flex flex-wrap gap-1 mt-2">
              <span v-for="s in posB.matchedSkills.slice(0,4)" :key="s" class="text-[8px] px-1.5 py-0.5 font-mono" style="background:rgba(16,185,129,0.08);color:var(--mint-500);border:1px solid rgba(16,185,129,0.2)">{{ s }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 多维度对冲评分条 -->
      <div class="panel-industrial p-5 shadow-deep relative">
        <div class="rivet" style="top:6px;left:6px"></div>
        <div class="rivet" style="top:6px;right:6px"></div>
        <div class="relative z-[1]">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <span class="tag-plate">SCORING</span>
              <h3 class="text-xs font-bold tracking-wide uppercase" style="color:var(--text-primary)">多维度对冲</h3>
            </div>
            <div class="flex items-center gap-4 text-[8px] font-mono tracking-widest">
              <span style="color:var(--brand-500)">● {{ posA.name }}</span>
              <span style="color:var(--text-muted)">VS</span>
              <span style="color:var(--cyan-500)">{{ posB.name }} ●</span>
            </div>
          </div>
          <div class="space-y-4">
            <div v-for="dim in scoringDimensions" :key="dim.key">
              <div class="text-center text-[8px] tracking-widest mb-1.5" style="color:var(--text-muted)">{{ dim.label }}</div>
              <!-- 对冲条：A 从左往右，B 从右往左 -->
              <div class="flex items-center gap-0">
                <span class="data-segment text-[10px] w-10 text-right shrink-0" style="color:var(--brand-500)">{{ dim.valA }}{{ dim.unit }}</span>
                <div class="flex-1 h-3 relative mx-2">
                  <!-- A 从左往右 -->
                  <div class="absolute top-0 left-0 h-full transition-all duration-500"
                    :style="{width: dim.pctA/2+'%', background:'var(--brand-500)', clipPath:'polygon(0 0,100% 0,100% 100%,3px 100%)'}"></div>
                  <!-- 中线 -->
                  <div class="absolute top-0 left-1/2 w-px h-full" style="background:var(--border-color);transform:translateX(-0.5px)"></div>
                  <!-- B 从右往左 -->
                  <div class="absolute top-0 right-0 h-full transition-all duration-500"
                    :style="{width: dim.pctB/2+'%', background:'var(--cyan-500)', clipPath:'polygon(0 0,calc(100% - 3px) 0,100% 100%,0 100%)'}"></div>
                </div>
                <span class="data-segment text-[10px] w-10 shrink-0" style="color:var(--cyan-500)">{{ dim.valB }}{{ dim.unit }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 雷达图 + 维度详情 -->
      <div class="panel-bridge panel-circuit p-5 shadow-deep relative">
        <div class="rivet" style="top:6px;left:6px"></div>
        <div class="rivet" style="top:6px;right:6px"></div>
        <div class="relative z-[1]">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <span class="tag-plate">RADAR</span>
              <h3 class="text-xs font-bold tracking-wide uppercase" style="color:var(--text-primary)">技能维度对峙</h3>
            </div>
            <div class="flex items-center gap-3 text-[8px] font-mono tracking-widest">
              <span style="color:var(--brand-500)">● {{ posA.name }}</span>
              <span style="color:var(--cyan-500)">● {{ posB.name }}</span>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">
            <!-- 左侧：雷达图 -->
            <div class="lg:col-span-3">
              <div style="height:300px">
                <MatchRadar v-if="radarDimensions.length" :dimensions="radarDimensions" :user-name="posA.name" :target-name="posB.name" />
              </div>
            </div>

            <!-- 右侧：维度详情表（固定高度 + 滚动） -->
            <div class="lg:col-span-2">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[8px] tracking-widest" style="color:var(--text-muted)">DIMENSION DETAIL</span>
                <span class="text-[8px] font-mono" style="color:var(--text-muted)">{{ radarDimensions.length }} AXIS</span>
              </div>
              <div class="space-y-1 overflow-y-auto pr-1" style="height:280px;scrollbar-width:thin;scrollbar-color:var(--brand-500) transparent">
                <div v-for="(dim, i) in radarDimensions" :key="dim.name"
                  class="flex items-center gap-2 px-2 py-1.5 text-[10px] font-mono transition-all hover:brightness-110 cursor-default"
                  :title="dim.name + ': ' + posA.name + ' ' + dim.userScore + ' vs ' + posB.name + ' ' + dim.targetScore"
                  :style="{background: dim.userScore > dim.targetScore ? 'rgba(99,102,241,0.06)' : dim.userScore < dim.targetScore ? 'rgba(6,182,212,0.06)' : 'var(--bg-secondary)'}">
                  <!-- 序号 -->
                  <span class="w-4 text-[8px] text-center flex-shrink-0" style="color:var(--text-muted)">{{ String(i+1).padStart(2,'0') }}</span>
                  <!-- 技能名 -->
                  <span class="flex-1 truncate" style="color:var(--text-primary)">{{ dim.name }}</span>
                  <!-- A 值 -->
                  <span class="w-7 text-right flex-shrink-0" :style="{color: dim.userScore >= 60 ? 'var(--brand-500)' : 'var(--text-muted)'}">{{ dim.userScore }}</span>
                  <!-- 对比条（加宽） -->
                  <div class="w-20 h-2 flex-shrink-0 relative rounded-sm overflow-hidden" style="background:rgba(255,255,255,0.04)">
                    <div class="absolute top-0 left-0 h-full transition-all duration-500" :style="{width: dim.userScore+'%', background:'linear-gradient(90deg,#6366f1,#818cf8)', opacity:0.7}"></div>
                    <div class="absolute top-0 left-0 h-full transition-all duration-500" :style="{width: dim.targetScore+'%', background:'linear-gradient(90deg,#0891b2,#06b6d4)', opacity:0.4}"></div>
                  </div>
                  <!-- B 值 -->
                  <span class="w-7 flex-shrink-0" :style="{color: dim.targetScore >= 60 ? 'var(--cyan-500)' : 'var(--text-muted)'}">{{ dim.targetScore }}</span>
                  <!-- 胜负（带背景色） -->
                  <span class="w-5 text-center text-[8px] flex-shrink-0 rounded-sm px-0.5 font-bold"
                    :style="{
                      color: dim.userScore > dim.targetScore ? '#10b981' : dim.userScore < dim.targetScore ? '#f43f5e' : 'var(--text-muted)',
                      background: dim.userScore > dim.targetScore ? 'rgba(16,185,129,0.1)' : dim.userScore < dim.targetScore ? 'rgba(244,63,94,0.1)' : 'transparent'
                    }">
                    {{ dim.userScore > dim.targetScore ? '▲' : dim.userScore < dim.targetScore ? '▼' : '=' }}
                  </span>
                </div>
              </div>
              <!-- 底部渐变遮罩（提示可滚动） -->
              <div v-if="radarDimensions.length > 8" class="text-center mt-1">
                <span class="text-[7px] font-mono tracking-widest" style="color:var(--text-muted)">▼ SCROLL ▼</span>
              </div>
            </div>
          </div>

          <!-- 底部统计摘要 -->
          <div class="grid grid-cols-4 gap-3 mt-4 pt-4" style="border-top:1px dashed var(--border-color)">
            <div class="text-center">
              <div class="data-segment text-sm" style="color:var(--brand-500)">{{ radarWinA }}</div>
              <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">{{ posA.name }} 胜</div>
            </div>
            <div class="text-center">
              <div class="data-segment text-sm" style="color:var(--text-muted)">{{ radarDraw }}</div>
              <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">平局</div>
            </div>
            <div class="text-center">
              <div class="data-segment text-sm" style="color:var(--cyan-500)">{{ radarWinB }}</div>
              <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">{{ posB.name }} 胜</div>
            </div>
            <div class="text-center">
              <div class="data-segment text-sm" :style="{color: radarWinA > radarWinB ? 'var(--brand-500)' : radarWinA < radarWinB ? 'var(--cyan-500)' : 'var(--mint-500)'}">
                {{ radarWinA > radarWinB ? 'A' : radarWinA < radarWinB ? 'B' : 'TIE' }}
              </div>
              <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">WINNER</div>
            </div>
          </div>
        </div>
      </div>

    <!-- 技能交集矩阵 -->
    <div class="panel-circuit p-5 shadow-deep relative">
        <div class="holo-overlay absolute inset-0 z-0 opacity-10"></div>
        <div class="relative z-[3]">
          <div class="flex items-center gap-2 mb-4">
            <span class="tag-plate">MATRIX</span>
            <h3 class="text-xs font-bold tracking-wide uppercase" style="color:var(--text-primary)">技能交集分析</h3>
          </div>
          <div class="grid grid-cols-3 gap-4">
            <!-- 共有 -->
            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="w-2 h-2 rounded-full bg-mint-500" style="box-shadow:0 0 4px var(--mint-500)"></span>
                <span class="text-[9px] tracking-widest" style="color:var(--mint-400)">共同技能 ({{ commonSkills.length }})</span>
              </div>
              <div class="space-y-1">
                <div v-for="s in commonSkills" :key="s" class="flex items-center gap-2 px-2 py-1 text-[10px] font-mono" style="background:rgba(16,185,129,0.06);border-left:2px solid var(--mint-500)">
                  <span style="color:var(--mint-500)">{{ s }}</span>
                </div>
                <div v-if="!commonSkills.length" class="text-[9px] text-center py-2" style="color:var(--text-muted)">—</div>
              </div>
            </div>
            <!-- A 独有 -->
            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="w-2 h-2 rounded-full bg-brand-500" style="box-shadow:0 0 4px var(--brand-500)"></span>
                <span class="text-[9px] tracking-widest" style="color:var(--brand-400)">A 独有 ({{ uniqueSkillsA.length }})</span>
              </div>
              <div class="space-y-1">
                <div v-for="s in uniqueSkillsA" :key="s" class="flex items-center gap-2 px-2 py-1 text-[10px] font-mono" style="background:rgba(99,102,241,0.06);border-left:2px solid var(--brand-500)">
                  <span style="color:var(--brand-400)">{{ s }}</span>
                </div>
                <div v-if="!uniqueSkillsA.length" class="text-[9px] text-center py-2" style="color:var(--text-muted)">—</div>
              </div>
            </div>
            <!-- B 独有 -->
            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="w-2 h-2 rounded-full bg-cyan-500" style="box-shadow:0 0 4px var(--cyan-500)"></span>
                <span class="text-[9px] tracking-widest" style="color:var(--cyan-400)">B 独有 ({{ uniqueSkillsB.length }})</span>
              </div>
              <div class="space-y-1">
                <div v-for="s in uniqueSkillsB" :key="s" class="flex items-center gap-2 px-2 py-1 text-[10px] font-mono" style="background:rgba(6,182,212,0.06);border-left:2px solid var(--cyan-500)">
                  <span style="color:var(--cyan-400)">{{ s }}</span>
                </div>
                <div v-if="!uniqueSkillsB.length" class="text-[9px] text-center py-2" style="color:var(--text-muted)">—</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import MatchRadar from '@/components/personal/MatchRadar.vue'
import type { RadarDimension } from '@/components/personal/MatchRadar.vue'

const store = usePersonalStore()

interface Pos { id:string; name:string; skills:string[]; matchRate:number; matchedSkills:string[]; missingSkills:string[]; salary:string }

const POSITION_COLORS = ['var(--brand-500)', 'var(--cyan-500)', '#a855f7']

const allPositions = computed<Pos[]>(() => {
  if (store.matches.length) {
    return store.matches.map(m => ({ id:m.id, name:m.positionName, skills:m.matchedSkills.concat(m.missingSkills), matchRate:m.matchRate, matchedSkills:m.matchedSkills, missingSkills:m.missingSkills, salary:m.salaryRange }))
  }
  return [
    { id:'d1', name:'AI 算法工程师', skills:['Python','PyTorch','Transformer','RAG','DeepSpeed','MLOps','NLP'], matchRate:72, matchedSkills:['Python','PyTorch','NLP'], missingSkills:['MLOps','DeepSpeed','Transformer','RAG'], salary:'40-70K' },
    { id:'d2', name:'全栈开发工程师', skills:['TypeScript','React','Node.js','SQL','Docker','AWS'], matchRate:85, matchedSkills:['TypeScript','React','SQL','Docker'], missingSkills:['Node.js','AWS'], salary:'30-50K' },
    { id:'d3', name:'大数据工程师', skills:['Spark','Flink','Kafka','Hadoop','SQL','Python','ClickHouse'], matchRate:52, matchedSkills:['SQL','Python'], missingSkills:['Spark','Flink','Kafka','Hadoop','ClickHouse'], salary:'35-60K' },
  ]
})

const selectedPositions = ref<Pos[]>([])

const posA = computed(() => selectedPositions.value[0] || allPositions.value[0])
const posB = computed(() => selectedPositions.value[1] || allPositions.value[1])

function getPositionColor(i:number){ return POSITION_COLORS[i%POSITION_COLORS.length] }
function isSelected(p:Pos){ return selectedPositions.value.some(s=>s.id===p.id) }
function getIndex(p:Pos){ return selectedPositions.value.findIndex(s=>s.id===p.id) }
function togglePosition(p:Pos){
  const i=selectedPositions.value.findIndex(s=>s.id===p.id)
  if(i>=0) selectedPositions.value.splice(i,1)
  else if(selectedPositions.value.length<3) selectedPositions.value.push(p)
}
function clearSelection(){ selectedPositions.value=[] }

const radarDimensions = computed<RadarDimension[]>(() => {
  const a=posA.value, b=posB.value
  // 取并集，按重要性排序：matchedSkills（已掌握）优先，然后 missingSkills
  const allSkills = [...new Set([...a.skills,...b.skills])]
  // 排序：双方都有的排前面 > 一方有的排后面
  const aSet=new Set(a.matchedSkills.map(s=>s.toLowerCase()))
  const bSet=new Set(b.matchedSkills.map(s=>s.toLowerCase()))
  const sorted = allSkills.sort((x,y) => {
    const xa=aSet.has(x.toLowerCase())?1:0, ya=aSet.has(y.toLowerCase())?1:0
    const xb=bSet.has(x.toLowerCase())?1:0, yb=bSet.has(y.toLowerCase())?1:0
    return (yb+ya)-(xb+xa)  // 双方共有的优先
  })
  // 最多取10个轴（ECharts雷达超过10个轴会拥挤）
  const limited = sorted.slice(0, 10)
  // 截断长技能名（防重叠）
  const truncate = (s:string) => s.length > 10 ? s.slice(0,9)+'…' : s
  return limited.map(s=>({
    name: truncate(s),
    userScore: aSet.has(s.toLowerCase()) ? 85 : 15,
    targetScore: bSet.has(s.toLowerCase()) ? 85 : 15,
    max: 100,
  }))
})

const radarWinA = computed(() => radarDimensions.value.filter(d => d.userScore > d.targetScore).length)
const radarWinB = computed(() => radarDimensions.value.filter(d => d.userScore < d.targetScore).length)
const radarDraw = computed(() => radarDimensions.value.filter(d => d.userScore === d.targetScore).length)

const scoringDimensions = computed(()=>{
  const a=posA.value, b=posB.value
  const sa=parseInt(a.salary)||40, sb=parseInt(b.salary)||40
  return [
    { key:'salary', label:'SALARY RANGE', unit:'K', valA:sa, valB:sb, pctA:sa/80*100, pctB:sb/80*100 },
    { key:'match', label:'MATCH RATE', unit:'%', valA:a.matchRate, valB:b.matchRate, pctA:a.matchRate, pctB:b.matchRate },
    { key:'gaps', label:'SKILL GAPS', unit:'', valA:a.missingSkills.length, valB:b.missingSkills.length, pctA:a.missingSkills.length/8*100, pctB:b.missingSkills.length/8*100 },
    { key:'learn', label:'LEARN COST', unit:'h', valA:a.missingSkills.length*15, valB:b.missingSkills.length*15, pctA:a.missingSkills.length*15, pctB:b.missingSkills.length*15 },
  ]
})

const commonSkills = computed(()=>{
  const a=posA.value, b=posB.value
  const bs=new Set(b.skills.map(s=>s.toLowerCase()))
  return a.skills.filter(s=>bs.has(s.toLowerCase()))
})
const uniqueSkillsA = computed(()=>{
  const a=posA.value, b=posB.value
  const bs=new Set(b.skills.map(s=>s.toLowerCase()))
  return a.skills.filter(s=>!bs.has(s.toLowerCase()))
})
const uniqueSkillsB = computed(()=>{
  const a=posA.value, b=posB.value
  const as=new Set(a.skills.map(s=>s.toLowerCase()))
  return b.skills.filter(s=>!as.has(s.toLowerCase()))
})
</script>
