<template>
  <div class="space-y-4">
    <!-- 头部 — 告警斜纹装饰 -->
    <div class="panel-industrial p-5 noise-texture panel-hazard">
      <div class="relative z-[1] flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="tag-plate" style="color:#f59e0b;border-color:#f59e0b">EVOLUTION</span>
          <h1 class="text-lg font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">岗位演化剧场</h1>
        </div>
        <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ store.evolutionSnapshots.length }} SNAPSHOTS · {{ selectedPosition }}</span>
      </div>
    </div>

    <!-- 岗位选择器 — 工业旋钮 -->
    <div class="panel-neon p-5 shadow-deep relative overflow-hidden">
      <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
      <div class="relative z-[1]">
        <div class="flex items-center gap-2 mb-4">
          <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">SELECT</span>
          <h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">目标岗位</h3>
        </div>
        <div class="flex items-center gap-4">
          <!-- 旋钮 -->
          <div class="relative shrink-0" style="width:80px;height:80px">
            <svg viewBox="0 0 80 80" class="w-full h-full">
              <circle cx="40" cy="40" r="36" fill="none" stroke="var(--border-color)" stroke-width="2" />
              <circle cx="40" cy="40" r="28" fill="var(--bg-card)" stroke="var(--brand-500)" stroke-width="1" />
              <!-- 刻度 -->
              <g v-for="i in 12" :key="i">
                <line x1="40" y1="6" x2="40" y2="12" stroke="var(--border-color)" stroke-width="1"
                  :transform="`rotate(${i * 30} 40 40)`" />
              </g>
              <!-- 指针 -->
              <line x1="40" y1="40" x2="40" y2="16" stroke="var(--brand-400)" stroke-width="2" stroke-linecap="round"
                :transform="`rotate(${positionIndex * 120} 40 40)`" class="transition-transform duration-500" />
              <circle cx="40" cy="40" r="4" fill="var(--brand-500)" />
            </svg>
          </div>
          <!-- 岗位列表 -->
          <div class="flex-1 flex flex-wrap gap-2">
            <button v-for="(pos, i) in positions" :key="pos"
              class="px-4 py-2 text-xs font-mono font-bold transition-all"
              :class="positionIndex === i ? 'text-white' : ''"
              :style="{
                background: positionIndex === i ? 'var(--brand-500)' : 'var(--bg-secondary)',
                border: '1px solid ' + (positionIndex === i ? 'var(--brand-500)' : 'var(--border-color)'),
                clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 100%, 0 100%)',
              }"
              @click="positionIndex = i">
              {{ pos }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 机械齿轨时间轴 -->
    <div class="panel-bridge p-5 shadow-deep view-section">
      <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
      <div class="relative z-[1]">
        <div class="flex items-center gap-2 mb-4">
          <span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">TIMELINE</span>
          <h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">演化时间轴</h3>
        </div>

        <!-- 齿轨 -->
        <div class="relative" style="height:80px">
          <svg class="w-full h-full" :viewBox="`0 0 ${timelineWidth} 80`">
            <!-- 齿轨基线 -->
            <rect x="0" y="36" :width="timelineWidth" height="8" rx="2" fill="var(--bg-secondary)" stroke="var(--border-color)" stroke-width="0.5" />
            <!-- 齿轮齿 -->
            <g v-for="(snap, i) in filteredSnapshots" :key="snap.snapshotId">
              <rect :x="getTickX(i) - 4" y="32" width="8" height="16" rx="1"
                :fill="i === selectedSnapshotIdx ? 'var(--brand-500)' : 'var(--border-color)'"
                :stroke="i === selectedSnapshotIdx ? 'var(--brand-400)' : 'var(--border-color)'" stroke-width="0.5" />
            </g>
            <!-- 时间标签 -->
            <g v-for="(snap, i) in filteredSnapshots" :key="'label-' + snap.snapshotId">
              <text :x="getTickX(i)" y="60" text-anchor="middle" font-size="9" font-family="Courier New, monospace" font-weight="700"
                :fill="i === selectedSnapshotIdx ? 'var(--brand-400)' : 'var(--text-muted)'">
                {{ snap.timestamp.substring(0, 7) }}
              </text>
              <text :x="getTickX(i)" y="72" text-anchor="middle" font-size="8" font-family="Courier New, monospace"
                fill="var(--text-muted)">
                {{ snap.changes.length }} CHANGES
              </text>
            </g>
            <!-- 选中指示器 -->
            <circle :cx="getTickX(selectedSnapshotIdx)" cy="40" r="6" fill="var(--brand-500)"
              stroke="var(--bg-card)" stroke-width="2" class="animate-node-ring" />
          </svg>
        </div>

        <!-- 快照选择按钮 -->
        <div class="flex items-center justify-center gap-2 mt-2">
          <button v-for="(snap, i) in filteredSnapshots" :key="snap.snapshotId"
            class="px-3 py-1 text-xs font-mono transition-all"
            :class="i === selectedSnapshotIdx ? 'bg-brand-500 text-white' : ''"
            :style="i === selectedSnapshotIdx ? {} : { color: 'var(--text-muted)', border: '1px solid var(--border-color)' }"
            @click="selectedSnapshotIdx = i">
            {{ snap.description }}
          </button>
        </div>
      </div>
    </div>

    <!-- 剧场主体 — 幕布展开 -->
    <div class="panel-industrial p-0 shadow-deep overflow-hidden view-section">
      <!-- 幕布装饰条 -->
      <div style="height:4px;background:linear-gradient(90deg,var(--brand-500),var(--cyan-500),var(--brand-500))"></div>

      <div class="p-5">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">SCENE</span>
            <h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">{{ currentSnapshot?.description || '—' }}</h3>
          </div>
          <div class="flex items-center gap-4 text-xs font-mono" :style="{color:'var(--text-muted)'}">
            <span>{{ currentSnapshot?.dataSources.join(' · ') }}</span>
            <span class="data-segment text-sm font-bold" style="color:var(--brand-400)">{{ currentSnapshot?.skillCount }} SKILLS</span>
          </div>
        </div>

        <!-- 变化卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 spring-list">
          <div v-for="change in currentSnapshot?.changes" :key="change.skillName"
            class="p-4 transition-all lift-on-hover relative overflow-hidden"
            :style="{
              background: 'var(--bg-card)',
              border: '1.5px solid ' + getChangeBorderColor(change.type),
              borderLeft: '4px solid ' + getChangeBorderColor(change.type),
            }">
            <!-- 变化类型标识 -->
            <div class="absolute top-0 right-0 px-2 py-0.5 text-xs font-mono font-bold"
              :style="{background:getChangeBg(change.type),color:getChangeColor(change.type)}">
              {{ getChangeLabel(change.type) }}
            </div>

            <div class="flex items-start gap-3 mb-2">
              <!-- 图标 -->
              <div class="w-8 h-8 flex items-center justify-center rounded-sm shrink-0"
                :style="{background:getChangeBg(change.type)}">
                <span class="text-sm">{{ getChangeIcon(change.type) }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-bold" :style="{color:'var(--text-primary)'}">{{ change.skillName }}</h4>
                <div v-if="change.type === 'upgraded' || change.type === 'downgraded'" class="text-xs font-mono mt-0.5" :style="{color:'var(--text-muted)'}">
                  {{ change.oldLevel }} → {{ change.newLevel }}
                </div>
              </div>
            </div>

            <!-- 证据 -->
            <div class="panel-dark-zone p-2 rounded-sm mb-2">
              <p class="text-xs leading-relaxed font-mono" :style="{color:'var(--text-secondary)'}">{{ change.evidence }}</p>
            </div>

            <!-- 数据来源 -->
            <div class="flex items-center gap-2">
              <span class="tag-plate" style="font-size:8px;padding:1px 5px">{{ change.source }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 变化统计 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 view-section">
      <!-- 变化计数 -->
      <div class="panel-asymmetric p-4 shadow-deep">
        <div class="text-xs font-bold tracking-wide mb-3" style="color:var(--text-muted)">CHANGE SUMMARY</div>
        <div class="grid grid-cols-2 gap-2">
          <div class="text-center p-2 rounded-sm" style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15)">
            <div class="data-giant text-xl text-mint-500 data-segment">{{ changeCount('added') }}</div>
            <div class="text-xs font-mono" style="color:var(--text-muted)">ADDED</div>
          </div>
          <div class="text-center p-2 rounded-sm" style="background:rgba(244,63,94,0.06);border:1px solid rgba(244,63,94,0.15)">
            <div class="data-giant text-xl text-rose-500 data-segment">{{ changeCount('removed') }}</div>
            <div class="text-xs font-mono" style="color:var(--text-muted)">REMOVED</div>
          </div>
          <div class="text-center p-2 rounded-sm" style="background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.15)">
            <div class="data-giant text-xl text-cyan-500 data-segment">{{ changeCount('upgraded') }}</div>
            <div class="text-xs font-mono" style="color:var(--text-muted)">UPGRADED</div>
          </div>
          <div class="text-center p-2 rounded-sm" style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15)">
            <div class="data-giant text-xl text-amber-500 data-segment">{{ changeCount('downgraded') }}</div>
            <div class="text-xs font-mono" style="color:var(--text-muted)">DOWNGRADED</div>
          </div>
        </div>
      </div>

      <!-- 技能数量趋势 -->
      <div class="panel-bridge p-4 shadow-deep">
        <div class="text-xs font-bold tracking-wide mb-3" style="color:var(--text-muted)">SKILL COUNT TREND</div>
        <div class="flex items-end gap-1" style="height:80px">
          <div v-for="(snap, i) in filteredSnapshots" :key="snap.snapshotId"
            class="flex-1 rounded-t-sm transition-all duration-500 cursor-pointer"
            :style="{
              height: (snap.skillCount / maxSkillCount * 100) + '%',
              background: i === selectedSnapshotIdx ? 'var(--brand-500)' : 'var(--brand-400)',
              opacity: i === selectedSnapshotIdx ? 1 : 0.5,
            }"
            @click="selectedSnapshotIdx = i"></div>
        </div>
        <div class="flex justify-between mt-1 text-xs font-mono" style="color:var(--text-muted)">
          <span v-for="snap in filteredSnapshots" :key="snap.snapshotId">{{ snap.skillCount }}</span>
        </div>
      </div>

      <!-- 数据源覆盖 -->
      <div class="panel-asymmetric p-4 shadow-deep">
        <div class="text-xs font-bold tracking-wide mb-3" style="color:var(--text-muted)">DATA SOURCES</div>
        <div class="space-y-2">
          <div v-for="src in dataSourceStats" :key="src.name" class="flex items-center gap-2">
            <span class="text-xs font-mono w-16" :style="{color:'var(--text-secondary)'}">{{ src.name }}</span>
            <div class="flex-1 h-2 progress-track-dark" style="background:var(--bg-secondary)">
              <div class="h-full rounded-sm transition-all duration-700" :style="{width:src.percent+'%',background:src.color}"></div>
            </div>
            <span class="text-xs font-mono font-bold w-8 text-right" :style="{color:'var(--text-secondary)'}">{{ src.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import type { EvolutionSnapshot } from '@/stores/personal'
import { useScrollReveal } from '@/composables/useScrollReveal'

const store = usePersonalStore()
useScrollReveal()

const positions = computed(() => [...new Set(store.evolutionSnapshots.map(s => s.positionName))])
const positionIndex = ref(0)
const selectedPosition = computed(() => positions.value[positionIndex.value] || '—')
const selectedSnapshotIdx = ref(0)

const filteredSnapshots = computed(() =>
  store.evolutionSnapshots.filter(s => s.positionName === selectedPosition.value)
)

const currentSnapshot = computed(() => filteredSnapshots.value[selectedSnapshotIdx.value])

const timelineWidth = computed(() => Math.max(filteredSnapshots.value.length * 120, 400))

const maxSkillCount = computed(() => Math.max(...filteredSnapshots.value.map(s => s.skillCount), 1))

function getTickX(i: number): number {
  const gap = timelineWidth.value / (filteredSnapshots.value.length + 1)
  return gap * (i + 1)
}

function changeCount(type: string): number {
  return currentSnapshot.value?.changes.filter(c => c.type === type).length || 0
}

const dataSourceStats = computed(() => {
  const src = currentSnapshot.value?.dataSources || []
  const colors = ['#818cf8', '#06b6d4', '#a855f7', '#10b981']
  return src.map((s, i) => {
    const match = s.match(/(\d+)/)
    const count = match ? parseInt(match[1]) : 0
    return { name: s.split('×')[0], count, percent: Math.min(count / 3, 100), color: colors[i] || '#6b7280' }
  })
})

function getChangeColor(type: string): string {
  const m: Record<string, string> = { added: '#10b981', removed: '#f43f5e', upgraded: '#06b6d4', downgraded: '#f59e0b' }
  return m[type] || '#6b7280'
}
function getChangeBg(type: string): string {
  return getChangeColor(type) + '15'
}
function getChangeBorderColor(type: string): string {
  return getChangeColor(type) + '60'
}
function getChangeLabel(type: string): string {
  const m: Record<string, string> = { added: 'NEW', removed: 'DROP', upgraded: 'UP', downgraded: 'DOWN' }
  return m[type] || type
}
function getChangeIcon(type: string): string {
  const m: Record<string, string> = { added: '✦', removed: '✕', upgraded: '↑', downgraded: '↓' }
  return m[type] || '•'
}

onMounted(() => { store.fetchEvolution() })
</script>
