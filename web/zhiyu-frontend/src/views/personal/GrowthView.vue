<template>
  <div class="space-y-4">
    <!-- 头部 -->
    <div class="panel-industrial p-5 noise-texture">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:#f59e0b;border-color:#f59e0b">GROWTH</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">职业成长轨迹</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ currentLevelName }} · {{ store.skillCount }} SKILLS</span>
      </div>
    </div>

    <!-- 技能等级 — 推进器阵列（垂直能量柱） -->
    <div class="panel-bridge p-5 shadow-deep">
      <div class="flex items-center justify-between mb-5">
        <PanelHeader label="LEVELS" title="技能等级" color="mint" margin="none" />
        <div class="text-right">
          <div class="text-sm font-bold" :style="{color:'var(--mint-400)'}">{{ currentLevelName }}</div>
          <div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">CURRENT LEVEL</div>
        </div>
      </div>
      <div class="flex items-end justify-between gap-2 md:gap-3 spring-list">
        <div v-for="row in levelRows" :key="row.name" class="flex-1 flex flex-col items-center gap-2">
          <!-- 状态灯 + 等级名 -->
          <span class="fuel-led" :style="{ background: row.ledColor, boxShadow: '0 0 6px ' + row.ledColor }"></span>
          <span class="text-xs font-mono font-bold tracking-wide" :style="{ color: row.current ? 'var(--mint-400)' : 'var(--text-secondary)' }">{{ row.name }}</span>
          <!-- 能量柱 -->
          <div class="fuel-rod" :class="row.current ? 'animate-glow-pulse-mint' : ''" :style="{ borderColor: row.current ? 'color-mix(in srgb, var(--mint-500) 55%, transparent)' : 'color-mix(in srgb, ' + row.color + ' 30%, transparent)' }">
            <div v-if="row.current" class="fuel-scan"></div>
            <div v-for="cell in ROD_CELLS" :key="cell" class="fuel-cell" :style="cellStyle(row, cell)"></div>
          </div>
          <!-- 读数 -->
          <div class="text-sm font-mono font-bold" :style="{ color: row.color }">{{ row.progress }}%</div>
          <div class="text-[10px] font-mono" :style="{ color:'var(--text-muted)' }">≥{{ row.minSkills }}项</div>
          <div class="h-4 flex items-center">
            <span v-if="row.current" class="tag-plate text-[10px]" style="color:var(--mint-400);border-color:var(--mint-400)">CURRENT</span>
            <span v-else-if="row.isNext" class="text-[10px] font-mono" :style="{ color:'var(--amber-400)' }">NEXT ▸</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 时间轴 + 下一等级 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 view-section">
      <div class="panel-industrial p-5 shadow-deep">
        <div class="rivet" style="top:8px;left:8px"></div>
        <PanelHeader label="HISTORY" title="技能增长时间轴" color="cyan" />
        <div v-if="skillTimeline.length" class="relative pl-8">
          <div class="absolute left-4 top-0 bottom-0 w-0.5" style="background:linear-gradient(180deg,var(--brand-500),#a855f7,var(--cyan-500),var(--mint-500))"></div>
          <div v-for="(event,idx) in skillTimeline" :key="idx" class="relative pb-5 last:pb-0">
            <div class="absolute left-[-17px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-white" :style="{background:event.color,boxShadow:'0 0 8px '+event.color}"></div>
            <div class="p-3 panel-asymmetric" :style="{borderLeft:'3px solid '+event.color}">
              <div class="flex items-center justify-between mb-1"><span class="text-xs font-mono font-bold" :style="{color:event.color}">{{ event.date }}</span><span class="text-xs px-1.5 py-0.5 rounded-sm font-mono font-bold" :style="{background:event.badgeBg,color:event.badgeColor}">+{{ event.skillsGained }}</span></div>
              <p class="text-xs leading-relaxed mb-1.5" :style="{color:'var(--text-secondary)'}">{{ event.description }}</p>
              <div class="flex flex-wrap gap-1"><span v-for="skill in event.skills" :key="skill" class="text-xs px-1.5 py-0.5 rounded-sm font-mono" :style="{background:event.color+'15',color:event.color}">{{ skill }}</span></div>
              <div class="text-xs mt-1.5 font-mono" :style="{color:'var(--text-muted)'}">累计: <span class="font-bold" :style="{color:'var(--text-primary)'}">{{ event.cumulativeCount }}</span> SKILLS</div>
            </div>
          </div>
        </div>
        <div v-else class="p-6 text-center panel-dark-zone">
          <div class="text-2xl mb-2" :style="{color:'var(--text-muted)'}">◌</div>
          <p class="text-sm" :style="{color:'var(--text-secondary)'}">暂无技能成长记录</p>
          <p class="text-xs mt-1 font-mono" :style="{color:'var(--text-muted)'}">上传简历后自动生成技能画像时间轴</p>
        </div>
      </div>

      <div class="panel-bridge p-5 shadow-deep">
        <PanelHeader label="NEXT" :title="nextLevelTitle" color="purple" />
        <template v-if="atMaxLevel">
          <div class="p-6 text-center panel-asymmetric" style="border:1px solid color-mix(in srgb, var(--mint-500) 40%, transparent)">
            <div class="text-3xl mb-2" :style="{color:'var(--mint-400)'}">★</div>
            <div class="text-base font-bold" :style="{color:'var(--mint-400)'}">已达最高等级「专家」</div>
            <div class="text-xs mt-1 font-mono" :style="{color:'var(--text-muted)'}">当前 {{ store.skillCount }} SKILLS</div>
          </div>
        </template>
        <template v-else-if="nextRow">
          <div class="flex items-center gap-3 p-4 panel-asymmetric" style="border:1px solid color-mix(in srgb, var(--amber-400) 40%, transparent);background:linear-gradient(135deg, color-mix(in srgb, var(--amber-400) 12%, transparent), transparent)">
            <div class="text-3xl font-bold" :style="{color:'var(--amber-400)'}">{{ nextRow.name }}</div>
            <div>
              <div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">NEXT LEVEL</div>
              <div class="text-xs mt-0.5 font-mono" :style="{color:'var(--text-secondary)'}">累计掌握 ≥{{ nextRow.minSkills }} 项技能</div>
            </div>
            <div class="ml-auto text-right">
              <div class="data-giant text-2xl" :style="{color:'var(--amber-400)'}">{{ nextRow.progress }}%</div>
              <div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">PROGRESS</div>
            </div>
          </div>
          <div class="mt-4 space-y-3">
            <div>
              <div class="flex justify-between text-xs font-mono mb-1">
                <span :style="{color:'var(--text-secondary)'}">{{ store.skillCount }} / {{ nextRow.minSkills }} 技能</span>
                <span :style="{color:'var(--text-muted)'}">差 {{ skillsToNext }} 项</span>
              </div>
              <div class="h-2 progress-track-dark" style="background:var(--bg-secondary)">
                <div class="h-full transition-all duration-700" :style="{ width: nextRow.progress + '%', background: 'linear-gradient(90deg, var(--amber-400), var(--amber-300))' }"></div>
              </div>
            </div>
            <div class="p-3 text-center text-xs panel-dark-zone" :style="{color:'var(--text-secondary)'}">按当前学习节奏，预计 <span class="font-bold font-mono" :style="{color:'var(--amber-400)'}">{{ estMonthsToNext }} MONTHS</span> 后达到「{{ nextRow.name }}」</div>
          </div>
        </template>
      </div>
    </div>

    <!-- 职业里程碑 -->
    <div class="panel-asymmetric p-5 shadow-deep">
      <div class="flex items-center justify-between mb-4">
        <PanelHeader label="MILESTONES" title="职业里程碑" color="amber" margin="none" />
        <div class="text-xs font-mono" :style="{color:'var(--text-muted)'}">已解锁 <span class="font-bold" :style="{color:'var(--amber-400)'}">{{ unlockedCount }}</span> / {{ milestoneRows.length }}</div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div v-for="m in milestoneRows" :key="m.name" class="p-3 panel-bridge transition-all"
          :style="{ border: '1px solid ' + (m.unlocked ? m.color + '44' : 'var(--border-color)'), opacity: m.unlocked ? 1 : 0.65 }">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-lg" :style="{ color: m.color }">{{ m.icon }}</span>
            <span class="text-xs font-bold tracking-wide" :style="{ color: m.unlocked ? m.color : 'var(--text-secondary)' }">{{ m.name }}</span>
            <span class="ml-auto text-[10px] font-mono" :style="{ color: m.unlocked ? 'var(--mint-400)' : 'var(--text-muted)' }">{{ m.unlocked ? 'UNLOCKED' : '未解锁' }}</span>
          </div>
          <p class="text-xs mb-2" :style="{color:'var(--text-muted)'}">{{ m.description }}</p>
          <div class="flex items-center gap-2">
            <div class="flex-1 h-1.5 progress-track-dark" style="background:var(--bg-secondary)">
              <div class="h-full transition-all duration-700" :style="{ width: m.progress + '%', background: m.color }"></div>
            </div>
            <span class="text-[10px] font-mono" :style="{ color: m.color }">{{ m.progress }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import { PALETTE } from '@/utils/color'
import { useScrollReveal } from '@/composables/useScrollReveal'
import PanelHeader from '@/components/common/PanelHeader.vue'
useScrollReveal()
const store = usePersonalStore()

// ── 技能等级 — 5 级进度条（后端 /api/personal/growth.levels 优先，空则回退固定阈值）──
const GROWTH_LEVELS = [
  { level: 1, name: '新手', minSkills: 0 },
  { level: 10, name: '初级', minSkills: 3 },
  { level: 30, name: '中级', minSkills: 8 },
  { level: 60, name: '高级', minSkills: 15 },
  { level: 90, name: '专家', minSkills: 25 },
]
const growthLevels = computed(() => store.growth?.levels?.length ? store.growth.levels : GROWTH_LEVELS)

/** 当前等级 = 最后一个技能数达标的等级 */
const currentIdx = computed(() => {
  let idx = 0
  growthLevels.value.forEach((l, i) => { if (store.skillCount >= l.minSkills) idx = i })
  return idx
})
const currentLevelName = computed(() => growthLevels.value[currentIdx.value]?.name ?? '新手')

interface LevelRow { name: string; minSkills: number; progress: number; achieved: boolean; current: boolean; isNext: boolean; color: string; ledColor: string }
const ROD_CELLS = 8
const levelRows = computed<LevelRow[]>(() =>
  growthLevels.value.map((l, i) => {
    const progress = l.minSkills <= 0 ? 100 : Math.min(100, Math.round((store.skillCount / l.minSkills) * 100))
    const achieved = store.skillCount >= l.minSkills
    const color = achieved ? 'var(--mint-500)' : i === currentIdx.value + 1 ? 'var(--amber-400)' : '#52525b'
    return {
      name: l.name,
      minSkills: l.minSkills,
      progress,
      achieved,
      current: i === currentIdx.value,
      isNext: i === currentIdx.value + 1,
      color,
      ledColor: i === currentIdx.value ? 'var(--mint-400)' : color,
    }
  })
)
/** 能量柱单格：自下而上充能，已充格带渐变亮面 + 光晕，隔格微暗营造燃料棒质感 */
function cellStyle(row: LevelRow, cell: number) {
  const filled = cell <= Math.round((row.progress / 100) * ROD_CELLS)
  if (!filled) return { background: 'color-mix(in srgb, var(--text-muted) 14%, transparent)' }
  return {
    background: `linear-gradient(180deg, color-mix(in srgb, ${row.color} 55%, #fff), ${row.color})`,
    boxShadow: `0 0 6px color-mix(in srgb, ${row.color} 50%, transparent)`,
    opacity: cell % 2 === 0 ? 0.85 : 1,
  }
}

// ── 下一等级 — 真实缺口推导（对齐后端 level-requirements 公式：(target - total) * 2）──
const atMaxLevel = computed(() => currentIdx.value >= growthLevels.value.length - 1)
const nextRow = computed(() => levelRows.value[currentIdx.value + 1] ?? null)
const skillsToNext = computed(() => nextRow.value ? Math.max(0, nextRow.value.minSkills - store.skillCount) : 0)
const estMonthsToNext = computed(() => skillsToNext.value * 2)
const nextLevelTitle = computed(() => atMaxLevel.value ? '已达最高等级' : '下一等级要求')

// ── 技能增长时间轴 — 按技能 firstSeen 首现月份分组推导（后端 growth.timeline 非空时优先）──
interface TimelineEvent { date: string; color: string; badgeBg: string; badgeColor: string; skillsGained: number; skills: string[]; cumulativeCount: number; description: string }
const timelineColors = [PALETTE.mint, PALETTE.cyan, PALETTE.purple, PALETTE.amber, PALETTE.rose]
const derivedSkillTimeline = computed<TimelineEvent[]>(() => {
  const byMonth = new Map<string, string[]>()
  store.skills.forEach(s => {
    const d = String(s.firstSeen || '').trim()
    if (!d) return
    const m = d.slice(0, 7)
    if (!byMonth.has(m)) byMonth.set(m, [])
    byMonth.get(m)!.push(s.name)
  })
  const months = [...byMonth.keys()].sort()
  let cum = 0
  return months.map((m, i) => {
    const skills = byMonth.get(m)!
    cum += skills.length
    const c = timelineColors[i % timelineColors.length]
    return {
      date: m,
      color: c, badgeBg: c + '1a', badgeColor: c,
      skillsGained: skills.length,
      skills: skills.slice(0, 8),
      cumulativeCount: cum,
      description: `新增 ${skills.length} 项技能：${skills.join('、')}${skills.length > 8 ? ' 等' : ''}`,
    }
  })
})
const skillTimeline = computed<TimelineEvent[]>(() => {
  const real = store.growth?.timeline
  if (real?.length) {
    return real.map((ev, i) => {
      const c = timelineColors[i % timelineColors.length]
      return {
        date: String(ev.date).slice(0, 10),
        color: c, badgeBg: c + '1a', badgeColor: c,
        skillsGained: ev.skillsGained, skills: ev.skills,
        cumulativeCount: ev.cumulativeCount, description: ev.description,
      }
    })
  }
  return derivedSkillTimeline.value
})

// ── 职业里程碑 — 后端 /api/personal/milestones 非空直接采用；否则展示定义型里程碑（进度从真实数据推导）──
interface MilestoneRow { name: string; description: string; icon: string; rarity: string; unlocked: boolean; progress: number; target: number; color: string }
const RARITY_COLOR: Record<string, string> = {
  common: '#71717a',
  uncommon: 'var(--brand-400)',
  epic: 'var(--purple-500)',
  legendary: 'var(--amber-400)',
  gold: 'var(--amber-400)',
}
function rarityColor(r: string): string {
  return RARITY_COLOR[r?.toLowerCase()] ?? 'var(--brand-400)'
}
const milestoneRows = computed<MilestoneRow[]>(() => {
  if (store.milestones?.length) {
    return store.milestones.map(m => ({
      name: m.name, description: m.description,
      icon: m.icon || '◈', rarity: m.rarity || 'common',
      unlocked: m.unlocked, progress: m.progress, target: m.target,
      color: rarityColor(m.rarity || 'common'),
    }))
  }
  const total = store.skillCount
  const completed = store.learningPath.filter(s => s.status === 'completed').length
  return [
    { name: '首份技能画像', description: '上传简历生成技能画像', icon: '▣', rarity: 'common', unlocked: total > 0, progress: total > 0 ? 100 : 0, target: 100 },
    { name: '技能储备 · 10', description: '累计掌握 10 项技能', icon: '◈', rarity: 'uncommon', unlocked: total >= 10, progress: Math.min(100, Math.round(total / 10 * 100)), target: 100 },
    { name: '首条学习路径', description: '完成 1 条学习路径', icon: '⬢', rarity: 'epic', unlocked: completed > 0, progress: Math.min(100, Math.round(completed / 1 * 100)), target: 100 },
    { name: '技能储备 · 25', description: '累计掌握 25 项技能', icon: '★', rarity: 'legendary', unlocked: total >= 25, progress: Math.min(100, Math.round(total / 25 * 100)), target: 100 },
  ].map(d => ({ ...d, color: rarityColor(d.rarity) }))
})
const unlockedCount = computed(() => milestoneRows.value.filter(m => m.unlocked).length)

onMounted(() => { store.fetchSkills(); store.fetchGrowth(); store.fetchMilestones() })
</script>

<style scoped>
/* ── 推进器能量柱 ── */
.fuel-rod {
  position: relative;
  display: flex;
  flex-direction: column-reverse;   /* 单元格自下而上充能 */
  gap: 3px;
  padding: 5px;
  width: clamp(3.25rem, 5.5vw, 4.5rem);
  height: 8.5rem;
  overflow: hidden;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px); /* 工业斜切角 */
}
.fuel-cell {
  flex: 1 1 0;
  transition: background 0.5s ease, box-shadow 0.5s ease, opacity 0.5s ease;
}
/* 当前级：自下而上扫描线 */
.fuel-scan {
  position: absolute;
  left: 2px;
  right: 2px;
  height: 26px;
  top: calc(100% + 4px);
  background: linear-gradient(180deg, transparent, color-mix(in srgb, var(--mint-500) 50%, transparent), transparent);
  animation: fuel-scan-up 2.8s linear infinite;
  pointer-events: none;
}
@keyframes fuel-scan-up {
  0% { top: calc(100% + 4px); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: -30px; opacity: 0; }
}
/* 状态灯 */
.fuel-led {
  width: 8px;
  height: 8px;
  border-radius: 1px;
}
</style>
