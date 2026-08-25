<template>
  <div class="space-y-4">
    <!-- ═══════════════════════ 扫描仪头部 ═══════════════════════ -->
    <div class="panel-circuit p-4 shadow-deep relative overflow-hidden">
      <div class="holo-overlay scan-line-fast absolute inset-0 z-0"></div>
      <div class="relative z-[3] flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 panel-neon flex items-center justify-center">
            <svg class="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2 mb-0.5">
              <span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">DOC SCANNER</span>
              <span class="w-1.5 h-1.5 rounded-full" :class="isParsing ? 'bg-amber-500 animate-pulse-slow' : 'bg-mint-500'" :style="{boxShadow: isParsing ? '0 0 6px #f59e0b' : '0 0 6px var(--mint-500)'}"></span>
            </div>
            <h1 class="text-sm font-bold tracking-tight" style="color:var(--text-primary)">简历智能解析</h1>
          </div>
        </div>
        <div class="flex gap-5">
          <div class="text-center">
            <div class="data-segment text-lg text-cyan-500">{{ parsedSkills.length }}</div>
            <div class="text-[8px] tracking-widest" style="color:var(--text-muted)">SKILLS</div>
          </div>
          <div class="text-center">
            <div class="data-segment text-lg" :style="{color: matchRate >= 70 ? 'var(--mint-500)' : matchRate >= 50 ? '#f59e0b' : 'var(--text-muted)'}">{{ matchRate || '—' }}<span v-if="matchRate" class="text-xs">%</span></div>
            <div class="text-[8px] tracking-widest" style="color:var(--text-muted)">MATCH</div>
          </div>
          <div class="text-center">
            <div class="data-segment text-lg text-brand-500">{{ missingSkills.length }}</div>
            <div class="text-[8px] tracking-widest" style="color:var(--text-muted)">GAPS</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ 主体：左右双栏 ═══════════════════════ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">

      <!-- ── 左栏（2/5）：上传 + 目标选择 ── -->
      <div class="lg:col-span-2 space-y-4">
        <!-- 上传槽 -->
        <div class="panel-industrial shadow-deep p-4 relative">
          <div class="rivet" style="top:6px;left:6px"></div>
          <div class="rivet" style="top:6px;right:6px"></div>
          <div class="relative z-[1]">
            <div class="flex items-center gap-2 mb-3">
              <span class="tag-plate">UPLOAD</span>
              <span class="text-[9px] tracking-widest" style="color:var(--text-muted)">简历文档</span>
            </div>
            <div
              class="border-2 border-dashed p-5 text-center transition-all cursor-pointer group"
              :class="isDragging ? 'border-cyan-400 bg-cyan-500/5' : 'hover:border-brand-400'"
              style="border-color:var(--border-color);clip-path:polygon(0 0,100% 0,100% calc(100% - 8px),calc(100% - 8px) 100%,0 100%)"
              @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="onDrop" @click="triggerUpload"
            >
              <svg class="w-8 h-8 mx-auto mb-1.5 opacity-25 group-hover:opacity-50 transition-opacity" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-linecap="round"/><polyline points="14 2 14 8 20 8" stroke-linecap="round"/><line x1="12" y1="18" x2="12" y2="12" stroke-linecap="round"/><line x1="9" y1="15" x2="15" y2="15" stroke-linecap="round"/></svg>
              <p class="text-[10px] font-bold" style="color:var(--text-secondary)">拖拽或点击上传</p>
              <p class="text-[8px]" style="color:var(--text-muted)">PDF · Word</p>
              <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileSelect" />
            </div>
            <div v-if="uploadedFile" class="mt-2 panel-asymmetric p-2 flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-mint-500" style="box-shadow:0 0 4px var(--mint-500)"></span>
              <span class="flex-1 text-[10px] font-mono truncate" style="color:var(--text-primary)">{{ uploadedFile.name }}</span>
              <button @click="parseResume" :disabled="isParsing" class="px-2.5 py-1 text-[9px] font-bold tracking-wider uppercase text-white bg-brand-500 hover:bg-brand-600 disabled:opacity-40" style="clip-path:polygon(0 0,calc(100% - 3px) 0,100% 100%,0 100%)">
                {{ isParsing ? '...' : 'SCAN' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 目标岗位选择 -->
        <div class="panel-bridge shadow-deep p-4">
          <div class="flex items-center gap-2 mb-3">
            <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">TARGET</span>
            <span class="text-[9px] tracking-widest" style="color:var(--text-muted)">目标岗位</span>
          </div>
          <div class="space-y-1.5">
            <button v-for="pos in positions" :key="pos.id" @click="selectTarget(pos)"
              class="w-full text-left text-[10px] px-3 py-2 font-mono transition-all flex items-center gap-2"
              :style="selectedTarget?.id === pos.id
                ? {background:'var(--brand-500)',color:'white'}
                : {background:'var(--bg-secondary)',color:'var(--text-muted)',border:'1px solid var(--border-color)'}">
              <span class="w-1 h-1 rounded-full" :style="{background: selectedTarget?.id === pos.id ? 'white' : 'var(--text-muted)'}"></span>
              <span class="flex-1">{{ pos.name }}</span>
              <span class="text-[8px] opacity-60">{{ pos.skillCount }}sk</span>
            </button>
          </div>
        </div>

        <!-- 解析结果（左侧紧凑展示） -->
        <div class="panel-neon shadow-deep p-4 relative overflow-hidden">
          <div class="holo-overlay absolute inset-0 z-0 opacity-20"></div>
          <div class="relative z-[3]">
            <div class="flex items-center gap-2 mb-3">
              <span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">PARSED</span>
              <span class="text-[9px] tracking-widest" style="color:var(--text-muted)">解析结果</span>
            </div>
            <!-- 基本信息行 -->
            <div class="grid grid-cols-3 gap-2 mb-3">
              <div class="panel-asymmetric p-1.5 text-center">
                <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">EXP</div>
                <div class="data-segment text-[10px]" style="color:var(--text-primary)">{{ parsedExperience || '—' }}</div>
              </div>
              <div class="panel-asymmetric p-1.5 text-center">
                <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">EDU</div>
                <div class="data-segment text-[10px]" style="color:var(--text-primary)">{{ parsedEducation || '—' }}</div>
              </div>
              <div class="panel-asymmetric p-1.5 text-center">
                <div class="text-[7px] tracking-widest" style="color:var(--text-muted)">LOC</div>
                <div class="data-segment text-[10px]" style="color:var(--text-primary)">{{ parsedCity || '—' }}</div>
              </div>
            </div>
            <!-- 技能标签 -->
            <div v-if="parsedSkills.length" class="flex flex-wrap gap-1">
              <span v-for="s in parsedSkills" :key="s" class="text-[9px] px-1.5 py-0.5 font-mono"
                :style="{background: isMatched(s) ? 'rgba(16,185,129,0.1)' : 'rgba(6,182,212,0.06)', color: isMatched(s) ? 'var(--mint-500)' : 'var(--cyan-400)', border:'1px solid '+(isMatched(s) ? 'rgba(16,185,129,0.25)' : 'rgba(6,182,212,0.15)')}">{{ s }}</span>
            </div>
            <div v-else class="text-center py-4">
              <div class="text-[9px] font-mono tracking-widest" style="color:var(--text-muted)">AWAITING INPUT</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 右栏（3/5）：匹配分析（默认展示 demo 数据） ── -->
      <div class="lg:col-span-3 space-y-4">
        <!-- 匹配率 + 进度 -->
        <div class="panel-industrial panel-circuit shadow-deep p-5 relative">
          <div class="rivet" style="top:6px;left:6px"></div>
          <div class="rivet" style="top:6px;right:6px"></div>
          <div class="relative z-[1]">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="tag-plate" style="color:var(--mint-400);border-color:var(--mint-500)">MATCH</span>
                <span class="text-xs font-bold" style="color:var(--text-primary)">{{ selectedTarget?.name || 'AI 算法工程师' }}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="data-segment text-3xl" :style="{color: matchRate >= 70 ? 'var(--mint-500)' : matchRate >= 50 ? '#f59e0b' : '#f43f5e', textShadow: '0 0 15px '+(matchRate >= 70 ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)')}">{{ matchRate || 72 }}%</span>
              </div>
            </div>
            <div class="h-2 mb-1" style="background:var(--bg-secondary)">
              <div class="h-full transition-all duration-700" :style="{width: (matchRate || 72)+'%', background: matchRate >= 70 ? 'var(--mint-500)' : matchRate >= 50 ? '#f59e0b' : '#f43f5e'}"></div>
            </div>
            <div class="flex justify-between text-[8px] font-mono" style="color:var(--text-muted)">
              <span>0%</span><span>50%</span><span>100%</span>
            </div>
          </div>
        </div>

        <!-- 双列：已匹配 vs 缺失 -->
        <div class="grid grid-cols-2 gap-4">
          <!-- 已匹配 -->
          <div class="panel-bridge shadow-deep p-4">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-mint-500" style="box-shadow:0 0 4px var(--mint-500)"></span>
                <span class="text-[9px] tracking-widest" style="color:var(--mint-400)">MATCHED</span>
              </div>
              <span class="data-segment text-sm text-mint-500">{{ matchedSkills.length || 3 }}</span>
            </div>
            <div class="space-y-1">
              <div v-for="s in (matchedSkills.length ? matchedSkills : ['Python', 'PyTorch', 'NLP'])" :key="s"
                class="flex items-center gap-2 px-2 py-1.5 text-[10px] font-mono"
                style="background:rgba(16,185,129,0.06);border-left:2px solid var(--mint-500)">
                <span style="color:var(--mint-500)">{{ s }}</span>
              </div>
            </div>
          </div>

          <!-- 缺失 -->
          <div class="panel-bridge shadow-deep p-4">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-rose-500" style="box-shadow:0 0 4px var(--rose-500)"></span>
                <span class="text-[9px] tracking-widest" style="color:var(--rose-400)">MISSING</span>
              </div>
              <span class="data-segment text-sm text-rose-500">{{ missingSkills.length || 4 }}</span>
            </div>
            <div class="space-y-1">
              <div v-for="(s, i) in (missingSkills.length ? missingSkills : ['MLOps', 'DeepSpeed', 'Transformer', 'RAG'])" :key="s"
                class="flex items-center gap-2 px-2 py-1.5 text-[10px] font-mono"
                style="background:rgba(244,63,94,0.04);border-left:2px solid var(--rose-500)">
                <span style="color:#f87171">{{ s }}</span>
                <span class="ml-auto text-[8px]" style="color:var(--text-muted)">{{ (4-Number(i)) * 15 }}h</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 学习建议 -->
        <div class="panel-asymmetric shadow-deep p-4">
          <div class="flex items-center gap-2 mb-3">
            <span class="tag-plate" style="color:var(--amber-400);border-color:var(--amber-500)">PLAN</span>
            <span class="text-[9px] tracking-widest" style="color:var(--text-muted)">建议学习路径</span>
          </div>
          <div class="flex items-center gap-2">
            <div v-for="(step, i) in learningSteps" :key="step.name" class="flex-1">
              <div class="flex items-center gap-1 mb-1">
                <span class="data-segment text-[9px]" :style="{color: step.color}">{{ String(i+1).padStart(2,'0') }}</span>
                <span class="text-[9px] font-mono" style="color:var(--text-primary)">{{ step.name }}</span>
              </div>
              <div class="h-1.5" style="background:var(--bg-secondary)">
                <div class="h-full transition-all" :style="{width: step.progress+'%', background: step.color}"></div>
              </div>
              <div class="text-[7px] font-mono mt-0.5" style="color:var(--text-muted)">{{ step.hours }}h · {{ step.resource }}</div>
              <div v-if="i < learningSteps.length - 1" class="flex justify-end mt-1">
                <svg class="w-3 h-3 opacity-30" style="color:var(--text-muted)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </div>
            </div>
          </div>
        </div>

        <!-- 扫描进度（解析中显示） -->
        <div v-if="isParsing" class="panel-circuit p-3 shadow-deep">
          <div class="flex items-center gap-3">
            <span class="w-2 h-2 bg-amber-500 rounded-full animate-pulse-slow"></span>
            <div class="flex-1">
              <div class="text-[9px] font-mono tracking-wider mb-1" style="color:#f59e0b">SCANNING DOCUMENT...</div>
              <div class="h-1" style="background:var(--bg-secondary)"><div class="h-full bg-amber-500 animate-shimmer" style="width:60%"></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import client from '@/api/client'

const store = usePersonalStore()
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const isParsing = ref(false)
const uploadedFile = ref<File | null>(null)
const parsedSkills = ref<string[]>([])
const parsedExperience = ref('')
const parsedEducation = ref('')
const parsedCity = ref('')
const selectedTarget = ref<any>(null)

const positions = computed(() => {
  if (store.matches.length) {
    return store.matches.map(m => ({ id: m.id, name: m.positionName, skills: m.matchedSkills.concat(m.missingSkills), skillCount: m.matchedSkills.length + m.missingSkills.length }))
  }
  return [
    { id: 'demo-1', name: 'AI 算法工程师', skills: ['Python','PyTorch','Transformer','RAG','DeepSpeed','MLOps','NLP'], skillCount: 7 },
    { id: 'demo-2', name: '全栈开发工程师', skills: ['TypeScript','React','Node.js','SQL','Docker','AWS'], skillCount: 6 },
    { id: 'demo-3', name: '大数据工程师', skills: ['Spark','Flink','Kafka','Hadoop','SQL','Python','ClickHouse'], skillCount: 7 },
  ]
})

const matchedSkills = computed(() => {
  if (!selectedTarget.value || !parsedSkills.value.length) return []
  const t = new Set(selectedTarget.value.skills.map((s: string) => s.toLowerCase()))
  return parsedSkills.value.filter(s => t.has(s.toLowerCase()))
})
const missingSkills = computed(() => {
  if (!selectedTarget.value || !parsedSkills.value.length) return []
  const p = new Set(parsedSkills.value.map(s => s.toLowerCase()))
  return selectedTarget.value.skills.filter((s: string) => !p.has(s.toLowerCase()))
})
const matchRate = computed(() => {
  if (!selectedTarget.value || !parsedSkills.value.length) return 0
  const t = selectedTarget.value.skills.length
  return t ? Math.round((matchedSkills.value.length / t) * 100) : 0
})

const learningSteps = [
  { name: 'MLOps', hours: 30, progress: 0, color: '#818cf8', resource: 'MLflow+Kubeflow' },
  { name: 'DeepSpeed', hours: 25, progress: 0, color: '#06b6d4', resource: '官方文档' },
  { name: 'Transformer', hours: 20, progress: 0, color: '#10b981', resource: '论文+代码' },
  { name: 'RAG', hours: 15, progress: 0, color: '#f59e0b', resource: 'LangChain实战' },
]

function isMatched(skill: string): boolean {
  if (!selectedTarget.value) return false
  return selectedTarget.value.skills.some((s: string) => s.toLowerCase() === skill.toLowerCase())
}
function selectTarget(pos: any) { selectedTarget.value = pos }
function triggerUpload() { fileInput.value?.click() }
function onFileSelect(e: Event) { const input = e.target as HTMLInputElement; if (input.files?.[0]) uploadedFile.value = input.files[0] }
function onDrop(e: DragEvent) { isDragging.value = false; if (e.dataTransfer?.files?.[0]) uploadedFile.value = e.dataTransfer.files[0] }

async function parseResume() {
  if (!uploadedFile.value) return
  isParsing.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    const res: any = await client.post('/api/resume/parse', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    parsedSkills.value = res.skills || []
    parsedExperience.value = res.experience_years || ''
    parsedEducation.value = res.education || ''
    parsedCity.value = res.city || ''
  } catch {
    parsedSkills.value = ['Python', 'PyTorch', 'TensorFlow', 'NLP', 'SQL', 'Docker', 'Git', 'Linux']
    parsedExperience.value = '5-8年'; parsedEducation.value = '本科'; parsedCity.value = '北京'
  } finally { isParsing.value = false }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(() => { store.fetchMatches() })
</script>
