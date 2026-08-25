<template>
  <div class="space-y-4" style="font-family: 'Inter', system-ui, sans-serif">
    <!-- ===== Row 1: 欢迎面板 — 工业舰桥切角 + 超大数字 ===== -->
    <div class="panel-industrial p-0 overflow-hidden noise-texture holo-overlay scan-line-fast">
      <div class="relative z-[1] flex flex-col lg:flex-row">
        <!-- 左侧: 身份信息区 -->
        <div class="flex-1 p-6">
          <div class="flex items-center gap-4 mb-4">
            <!-- 头像 — 六角形切割 -->
            <HexAvatar :letter="userName.charAt(0)" :size="56" />
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="tag-plate">ACTIVE</span>
                <h1 class="text-xl font-bold tracking-tight" :style="{color:'var(--text-primary)'}">{{ userName }}</h1>
              </div>
              <p class="text-sm text-brand-400 font-medium">{{ userTitle }}</p>
              <div class="flex items-center gap-3 mt-1.5 text-xs" :style="{color:'var(--text-muted)'}">
                <span class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-brand-400"></span>{{ userWorkYears }}</span>
                <span class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-cyan-400"></span>{{ userEducation }}</span>
                <span class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-mint-400"></span>{{ userLocation }}</span>
              </div>
            </div>
          </div>
          <!-- 技能标签 — 倾斜便签风 -->
          <div class="flex flex-wrap gap-2">
            <span v-for="(tag, i) in userTags" :key="tag"
              class="tag-tilted"
              :style="{
                background: i===0?'color-mix(in srgb, var(--brand-500) 08%, transparent)':'var(--bg-secondary)',
                color: i===0?'var(--brand-500)':'var(--text-secondary)',
                borderColor: i===0?'color-mix(in srgb, var(--brand-500) 30%, transparent)':'var(--border-color)'
              }">
              {{ tag }}
            </span>
          </div>
        </div>

        <!-- 右侧: 巨型数据读数区（HudCell count-up 动画） -->
        <div class="lg:w-80 p-4 grid grid-cols-3 gap-2 panel-dark-zone" style="border-left:1px solid var(--border-color)">
          <HudCell :value="store.bestMatch?.matchRate || 0" label="Match" icon="⌖" suffix="%" value-class="text-brand-500" />
          <HudCell :value="competitionScore" label="Compete" icon="▲" suffix="%" value-class="text-mint-500" />
          <HudCell :value="store.skillCount" label="Skills" icon="◆" value-class="text-cyan-500" />
        </div>
      </div>
    </div>

    <!-- ===== Row 2: 技能雷达 + AI顾问 — 不对称布局 ===== -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4" style="align-items:start">
      <!-- 技能雷达图 — 舰桥面板 -->
      <div class="lg:col-span-3 panel-bridge panel-circuit p-5 shadow-deep">
        <!-- 铆钉 -->
        <div class="rivet" style="top:8px;left:8px"></div>
        <div class="rivet" style="top:8px;right:8px"></div>
        <div class="rivet" style="bottom:8px;left:8px"></div>
        <div class="rivet" style="bottom:8px;right:8px"></div>

        <div class="flex items-center justify-between mb-3">
          <PanelHeader label="RADAR" title="技能能力图谱" margin="none" />
          <span class="text-xs flex items-center gap-2" :style="{color:'var(--text-muted)'}">
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full" style="background:var(--brand-500)"></span> 你</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full" style="background:var(--cyan-500)"></span> {{ store.bestMatch?.positionName || '目标' }}</span>
          </span>
        </div>
        <MatchRadar v-if="radarDimensions.length" :dimensions="radarDimensions" user-name="你的画像" :target-name="store.bestMatch?.positionName || '目标岗位'" />
        <div class="panel-divider mt-2"></div>
      </div>

      <!-- 右侧: AI 顾问 — 霓虹面板 + 扫描线 -->
      <div class="lg:col-span-2 panel-neon p-5 relative overflow-hidden lift-on-hover"
        style="border-radius: 2px 24px 2px 24px; background:linear-gradient(160deg, color-mix(in srgb, var(--brand-500) 08%, transparent), color-mix(in srgb, var(--purple-500) 04%, transparent))">
        <!-- 扫描线 -->
        <div class="absolute left-0 right-0 h-px pointer-events-none animate-scan-line z-10" style="background:linear-gradient(90deg,transparent,var(--brand-400),transparent)"></div>

        <div class="relative">
          <div class="flex items-center gap-2 mb-4">
            <div class="w-10 h-10 flex items-center justify-center rounded-sm relative"
              style="background:linear-gradient(135deg, var(--brand-600), var(--brand-400)); clip-path:polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)">
              <svg class="w-5 h-5 text-white relative z-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="8" width="18" height="12" rx="3" stroke-linecap="round"/><circle cx="8" cy="15" r="1.5"/><circle cx="16" cy="15" r="1.5"/><line x1="10" y1="20" x2="14" y2="20" stroke-linecap="round"/><path d="M8 4l2-2h4l2 2" stroke-linecap="round"/><circle cx="12" cy="5" r="1"/>
              </svg>
            </div>
            <div>
              <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">AI</span>
              <h3 class="text-sm font-bold mt-1" :style="{color:'var(--text-primary)'}">职业顾问</h3>
            </div>
          </div>
          <p class="text-xs leading-relaxed mb-4" :style="{color:'var(--text-secondary)'}">{{ aiSummary }}</p>

          <div class="space-y-2 mb-4">
            <div v-for="(insight, i) in aiInsights" :key="i"
              class="flex items-center gap-2 p-2.5 text-xs transition-all hover:translate-x-1 panel-dark-zone"
              style="border-left:2px solid"
              :style="{ borderLeftColor: insight.dotColor }">
              <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ background: insight.dotColor }"></span>
              <span :style="{color:'var(--text-primary)'}">{{ insight.label }}</span>
              <span :style="{color:'var(--text-secondary)'}">{{ insight.text }}</span>
            </div>
          </div>

          <router-link to="/personal/match"
            class="inline-flex items-center gap-2 text-xs font-bold px-5 py-2 text-white transition-all hover:gap-3"
            style="background:linear-gradient(135deg, var(--brand-600), var(--brand-500)); clip-path:polygon(0 0, calc(100% - 10px) 0, 100% 100%, 0 100%)">
            查看详细分析 <span class="text-base">→</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- ===== Row 3: 岗位匹配轨道 (宽) + 保鲜预警 (窄) — 错位布局 ===== -->
    <div class="grid grid-cols-1 lg:grid-cols-7 gap-4 view-section" style="align-items:start">
      <!-- 匹配轨道 — 占据 4/7，工业面板 -->
      <div class="lg:col-span-4 panel-industrial p-5 overflow-hidden">
        <div class="rivet" style="top:8px;left:8px"></div>
        <div class="rivet" style="top:8px;right:8px"></div>
        <div class="flex items-center justify-between mb-2">
          <PanelHeader label="ORBIT" title="岗位匹配轨道" margin="none" />
          <router-link to="/personal/match" class="text-xs font-mono tracking-wider" style="color:var(--brand-400)">[ VIEW ALL ]</router-link>
        </div>
        <MatchOrbit
          :matches="store.matches"
          :user-name="userName"
          :avatar-letter="userName.charAt(0)"
          :skill-count="store.skillCount"
          :height="280"
          @match-click="(m) => {}" />
      </div>

      <!-- 保鲜预警 + 学习概览 — 占据 3/7，两个叠加面板 -->
      <div class="lg:col-span-3 flex flex-col gap-4">
        <!-- 保鲜卡片 — 不对称面板 + 浮动效果 -->
        <div class="panel-asymmetric p-4 relative overflow-hidden"
          style="border-color:color-mix(in srgb, var(--rose-500) 20%, transparent)">
          <div class="flex items-center justify-between mb-3">
            <PanelHeader label="ALERT" title="技能保鲜" color="rose" margin="none" />
            <span class="text-xs font-mono font-bold px-2 py-0.5" style="background:color-mix(in srgb, var(--rose-500) 10%, transparent); color:#f87171"
              :style="store.alertSkillCount>0?{animation:'heartbeat-pulse 2s ease-in-out infinite'}:{}">
              {{ store.alertSkillCount }} ITEM{{ store.alertSkillCount!==1?'S':'' }}
            </span>
          </div>
          <div v-for="alert in store.alerts" :key="alert.skillName" class="mb-2 last:mb-0">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-bold flex items-center gap-1.5" :style="{color:'var(--text-primary)'}">
                <span class="w-1.5 h-1.5 rounded-full" :style="{background:alert.urgency==='high'?'#f43f5e':'#f59e0b', boxShadow:alert.urgency==='high'?'0 0 6px color-mix(in srgb, var(--rose-500) 60%, transparent)':'none'}"></span>
                {{ alert.skillName }}
              </span>
              <span class="font-mono font-bold" :style="{color:alert.urgency==='high'?'#f87171':'#fbbf24'}">{{ alert.currentFreshness }}%</span>
            </div>
            <div class="h-1.5 progress-track-dark" style="background:var(--bg-secondary)">
              <div class="h-full transition-all duration-700" :style="{
                width:alert.currentFreshness+'%',
                background:alert.currentFreshness<40?'linear-gradient(90deg,#f43f5e,#fb923c)':'linear-gradient(90deg,#f59e0b,#fbbf24)'
              }"></div>
            </div>
          </div>
          <router-link to="/personal/freshness" class="text-xs font-mono tracking-wider mt-3 inline-block" style="color:var(--brand-400)">[ DETAILS ]</router-link>
        </div>

        <!-- 学习路径迷你卡 — 更小巧 -->
        <div class="panel-bridge p-4" style="border-color:color-mix(in srgb, var(--brand-500) 20%, transparent)">
          <div class="flex items-center justify-between mb-3">
            <PanelHeader label="PATH" title="学习路径" color="brand" margin="none" />
            <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ completedSteps }}/{{ store.learningPath.length }}</span>
          </div>
          <!-- 流动进度条 -->
          <div class="h-1.5 mb-3 progress-track-dark" style="background:var(--bg-secondary)">
            <div class="h-full animate-progress-flow transition-all duration-700"
              style="background:linear-gradient(90deg,var(--brand-500),#a855f7,var(--brand-500)); background-size:200% 100%"
              :style="{width:overallProgress+'%'}"></div>
          </div>
          <div class="flex items-end gap-1" style="height:32px">
            <div v-for="(step, idx) in store.learningPath" :key="step.id"
              class="flex-1 transition-all"
              :style="{
                height:(step.progress||5)+'%',
                background:step.status==='completed'?'var(--mint-500)':step.status==='in_progress'?'var(--brand-500)':step.status==='available'?'var(--bg-secondary)':'var(--bg-secondary)',
                opacity:step.status==='locked'?0.3:1
              }"
              :title="step.title"></div>
          </div>
          <router-link to="/personal/learning-path" class="text-xs font-mono tracking-wider mt-3 inline-block" style="color:var(--brand-400)">[ FULL PATH ]</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import ProgressRing from '@/components/common/ProgressRing.vue'
import HudCell from '@/components/common/HudCell.vue'
import HexAvatar from '@/components/common/HexAvatar.vue'
import PanelHeader from '@/components/common/PanelHeader.vue'
import MatchRadar from '@/components/personal/MatchRadar.vue'
import MatchOrbit from '@/components/personal/MatchOrbit.vue'
import { buildMatchRadarDimensions, RADAR_DEMO } from '@/utils/matches'
import { useScrollReveal } from '@/composables/useScrollReveal'
useScrollReveal()

const store = usePersonalStore()

const userName = ref('张明')
const userTitle = ref('高级前端开发工程师')
const userTags = ref(['React', 'TypeScript', 'Node.js', 'AI应用'])
const userWorkYears = ref('6年经验')
const userEducation = ref('本科')
const userLocation = ref('北京')

const competitionScore = computed(() => store.bestMatch ? Math.min(store.bestMatch.matchRate + 10, 98) : 0)

const aiSummary = computed(() => {
  const m = store.bestMatch; const a = store.alertSkillCount
  if (!m) return '正在分析你的技能画像...'
  return `基于 ${store.skillCount} 项技能画像分析，你在 ${store.topSkillCategory} 领域具备较强竞争力。与 ${m.positionName} 岗位匹配度达 ${m.matchRate}%，补充 ${m.missingSkills.length} 项关键技能后可达 ${Math.min(m.matchRate + m.missingSkills.length*8, 98)}%。`
})

const aiInsights = computed(() => {
  const m = store.bestMatch
  return [
    { dotColor:'var(--mint-500)', label:'优势方向: ', text:`${store.topSkillCategory} 领域积累深厚` },
    { dotColor:'var(--amber-500)', label:'待提升: ', text:`${m?.missingSkills.slice(0,2).join('、') || '—'} 需补充` },
    { dotColor:'var(--rose-500)', label:'保鲜预警: ', text:`${store.alerts.length} 项技能保鲜度偏低` },
    { dotColor:'var(--brand-500)', label:'建议: ', text:`优先学习 ${store.learningPath.find(s=>s.status==='available')?.skill || '—'}` },
  ]
})

const radarDimensions = computed(() =>
  store.bestMatch ? buildMatchRadarDimensions(store.bestMatch) : RADAR_DEMO
)

const completedSteps = computed(() => store.learningPath.filter(s=>s.status==='completed').length)
const overallProgress = computed(() => store.learningPath.length ? Math.round(store.learningPath.reduce((s,x)=>s+x.progress,0)/store.learningPath.length) : 0)

onMounted(() => { store.fetchSkills(); store.fetchMatches(); store.fetchLearningPath(); store.fetchFreshness() })
</script>
