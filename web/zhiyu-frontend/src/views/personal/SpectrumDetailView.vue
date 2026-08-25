<template>
  <div class="spectrum-detail space-y-4">
    <!-- 返回 -->
    <div class="view-section">
      <router-link to="/personal/spectrum" class="back-link" :style="{color:'var(--text-secondary)',borderColor:'var(--border-color)'}">
        ← 返回技能光谱
      </router-link>
    </div>

    <!-- 未找到空态 -->
    <div v-if="!skill" class="panel-asymmetric p-8 shadow-deep flex items-center justify-center view-section">
      <div class="text-center">
        <div class="text-3xl opacity-30 animate-glow-pulse mb-2" :style="{color:'var(--rose-500)'}">✕</div>
        <p class="text-xs font-mono mb-4" :style="{color:'var(--text-muted)'}">信号未找到 · SIGNAL LOST</p>
        <router-link to="/personal/spectrum" class="back-link" :style="{color:'var(--text-secondary)',borderColor:'var(--border-color)'}">
          ← 返回技能光谱
        </router-link>
      </div>
    </div>

    <template v-else>
      <!-- ═══ 头部 — 信号身份 ═══ -->
      <header class="panel-industrial p-4 noise-texture holo-overlay scan-line-fast view-section">
        <div class="rivet" style="top:8px;left:8px"></div>
        <div class="rivet" style="top:8px;right:8px"></div>
        <div class="rivet" style="bottom:8px;left:8px"></div>
        <div class="rivet" style="bottom:8px;right:8px"></div>
        <div class="relative z-[1] flex items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <span class="tag-plate" :style="{color:statusColor, borderColor:statusColor}">SIGNAL</span>
            <div class="min-w-0">
              <h1 class="text-lg font-bold tracking-wide uppercase truncate" :style="{color:'var(--text-primary)'}">{{ skill.skillName }}</h1>
              <div class="text-[10px] font-mono tracking-widest uppercase" :style="{color:'var(--text-muted)'}">{{ skill.category }}</div>
            </div>
          </div>
          <div class="flex items-center gap-4 shrink-0">
            <span class="status-pill" :style="{background:statusColor+'18',color:statusColor,borderColor:statusColor+'40'}">
              {{ skill.verificationStatus.toUpperCase() }}
            </span>
            <div class="text-right">
              <div class="text-[9px] font-mono tracking-[0.2em] uppercase" :style="{color:'var(--text-muted)'}">FUSION</div>
              <div class="data-giant text-3xl leading-none mt-0.5" :style="{color:statusColor}">
                {{ (skill.totalConfidence * 100).toFixed(0) }}<span class="text-base">%</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- ═══ 信号示波 — 单技能融合波形 ═══ -->
      <section class="view-section">
        <SpectrumOscilloscope :signal="skill" />
      </section>

      <!-- ═══ 多源证据链 ═══ -->
      <section class="panel-industrial p-4 shadow-deep view-section">
        <div class="rivet" style="top:8px;left:8px"></div>
        <div class="rivet" style="top:8px;right:8px"></div>
        <div class="relative z-[1]">
          <div class="flex items-center gap-2 mb-3">
            <span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">EVIDENCE</span>
            <h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">多源证据链</h3>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div
              v-for="src in orderedSources"
              :key="src.source"
              class="evidence-card"
              :style="{borderColor: srcColor(src.source)+'30', borderLeftColor: srcColor(src.source)}"
            >
              <div class="flex items-center justify-between gap-2 mb-1">
                <span class="flex items-center gap-1.5 text-[10px] font-bold font-mono uppercase" :style="{color:srcColor(src.source)}">
                  <span class="w-1.5 h-1.5 rounded-full" :style="{background:srcColor(src.source),boxShadow:'0 0 5px '+srcColor(src.source)}"></span>
                  {{ sourceLabels[src.source] }}
                </span>
                <span class="text-[10px] font-mono" :style="{color:'var(--text-muted)'}">×{{ src.frequency }} · {{ (src.confidence * 100).toFixed(0) }}%</span>
              </div>
              <div class="h-1.5 mb-1.5" :style="{background:'var(--bg-secondary)'}">
                <div class="h-full" :style="{width: src.confidence * 100 + '%', background: srcColor(src.source), boxShadow:'0 0 6px '+srcColor(src.source)}"></div>
              </div>
              <div v-if="src.examples.length" class="flex flex-wrap gap-1">
                <span v-for="ex in src.examples" :key="ex" class="ex-chip" :style="{color:srcColor(src.source)}">{{ ex }}</span>
              </div>
            </div>
          </div>

          <!-- 验证状态 + 融合公式 -->
          <div class="panel-dark-zone p-2 mt-3 text-[10px] font-mono">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <span :style="{color:statusColor}">STATUS · {{ skill.verificationStatus.toUpperCase() }}</span>
              <span>
                <span :style="{color:'var(--text-muted)'}">conf = sigmoid(</span>
                <span v-for="(src, i) in skill.sources" :key="src.source">
                  <span :style="{color:srcColor(src.source)}">{{ src.source }}</span>
                  <span v-if="i < skill.sources.length - 1" :style="{color:'var(--text-secondary)'}"> + </span>
                </span>
                <span :style="{color:'var(--text-secondary)'}">)</span>
              </span>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { usePersonalStore } from '@/stores/personal'
import type { SignalSource } from '@/stores/personal'
import SpectrumOscilloscope from '@/components/personal/SpectrumOscilloscope.vue'
import { useScrollReveal } from '@/composables/useScrollReveal'

const route = useRoute()
const store = usePersonalStore()

const skill = computed(() => store.signalByName(route.params.skill as string))

useScrollReveal()

const sourceLabels: Record<string, string> = { jd: '招聘JD', github: 'GitHub Trending', arxiv: 'arXiv 论文', standard: '行业标准' }
const sourceColors: Record<string, string> = { jd: '#818cf8', github: '#06b6d4', arxiv: '#a855f7', standard: '#10b981' }
const statusColors: Record<string, string> = { confirmed: '#10b981', candidate: '#f59e0b', unverified: '#64748b' }

const statusColor = computed(() =>
  skill.value ? statusColors[skill.value.verificationStatus] || '#64748b' : '#64748b'
)

const orderedSources = computed<SignalSource[]>(() =>
  skill.value ? [...skill.value.sources].sort((a, b) => b.confidence - a.confidence) : []
)

function srcColor(src: string) { return sourceColors[src] || '#6b7280' }

/** 动态标题：技能名 · 技能信号示波 */
watchEffect(() => {
  if (skill.value) document.title = `${skill.value.skillName} · 技能信号示波 - 职域智联`
})

// 信号数据无独立端点，诚实保留 demo 数据（Silent Fallback）
</script>

<style scoped>
.spectrum-detail { background: var(--bg-primary); }

/* ── 返回链接 ── */
.back-link {
  display: inline-block;
  padding: 5px 12px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  border: 1px solid;
  transition: all 0.25s ease;
  clip-path: polygon(0 3px, 3px 0, 100% 0, 100% calc(100% - 3px), calc(100% - 3px) 100%, 0 100%);
  background: var(--bg-card);
}
.back-link:hover { color: var(--brand-400) !important; border-color: var(--brand-500) !important; }

/* ── 状态胶囊 ── */
.status-pill {
  display: inline-block;
  padding: 3px 10px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  border: 1px solid;
}

/* ── 证据链卡片 ── */
.evidence-card {
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid;
  border-left-width: 3px;
  transition: all 0.25s ease;
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 5px), calc(100% - 5px) 100%, 0 100%);
}
.evidence-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.2); }
.ex-chip {
  font-family: 'Courier New', monospace;
  font-size: 9px;
  padding: 1px 6px;
  border: 1px solid currentColor;
  opacity: 0.6;
  white-space: nowrap;
}
.evidence-card:hover .ex-chip { opacity: 0.9; }
</style>
