<template>
  <div class="space-y-4">
    <template v-if="hasEvo && evo">
      <!-- ═══ 档案头 ═══ -->
      <header class="doc-masthead px-4 py-4">
        <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
          <div class="min-w-0">
            <h1 class="ent-title-serif text-lg font-bold leading-tight">{{ position?.name || evo.positionName }}</h1>
            <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
              POSITION DOSSIER · {{ evo.timeline[0]?.date }} → {{ lastDate }} · {{ evo.timeline.length }} NODES · 需求增长 +{{ demandGrowth }}%
            </p>
            <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-POS-{{ dossierNo }} · {{ position?.department }} · {{ position?.level }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="seal-chip" style="color:#fff;border-color:#fff">● 现行生效</span>
            <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">REV 2026.08</span>
          </div>
        </div>
      </header>

      <!-- ═══ 文档操作栏 ═══ -->
      <div class="flex flex-wrap items-center gap-2">
        <button class="ent-btn ent-btn--coral" @click="exportDossier">导出档案</button>
        <button class="ent-btn ent-btn--ghost" @click="exportReport">导出演化报告</button>
        <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">最近核验 · 2026-08-03 · 全量更新</span>
      </div>

      <NotificationBar
        :visible="showNotification"
        :message="notifyMessage"
        :detail="notifyDetail"
        @close="showNotification=false"
      />

      <!-- ═══ 01 演化曲线 ═══ -->
      <section class="panel-doc p-4">
        <span class="watermark-num">01</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">演化曲线</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">实线=市场需求 · 虚线=企业采用 · 珊瑚点=当前节点</span>
            <button
              class="ent-btn ent-btn--ghost"
              style="padding:3px 10px;font-size:10px;margin-left:10px"
              @click="toggleDiff"
            >{{ showDiff ? '退出对比' : '对比模式' }}</button>
          </div>

          <EnterpriseLifeCurve :timeline="evo.timeline" :selected-index="selectedIndex" @select="pickNode" />

          <!-- 卷内目录：时间节点图章条 -->
          <div class="flex flex-wrap items-center gap-2 mt-2">
            <div class="tl-strip">
              <button
                v-for="(t, i) in evo.timeline"
                :key="t.date"
                class="tl-stamp"
                :class="{ 'tl-stamp--active': i === selectedIndex }"
                @click="pickNode(i)"
              ><span class="tl-dot"></span>{{ t.date }}</button>
            </div>
            <span class="flex-1"></span>
            <button class="ent-btn ent-btn--ghost" style="flex:none;padding:3px 10px;font-size:10px" @click="togglePlay">
              {{ playing ? '暂停翻阅' : '▶ 播放轨迹' }}
            </button>
          </div>
          <div v-if="showDiff" class="footnote" style="margin-top:8px;color:var(--ent-coral)">
            ▲ 对比模式 · 点击曲线节点或时间戳设定对比基准（当前 <span class="src">{{ cur?.date }}</span> 为对比目标）
          </div>
        </div>
      </section>

      <!-- ═══ 02 节点读数 + 03 技能定级表 ═══ -->
      <div v-if="cur" class="grid grid-cols-1 lg:grid-cols-5 gap-3">
        <!-- 02 节点读数 -->
        <section class="panel-doc p-4 lg:col-span-2 self-start">
          <span class="watermark-num">02</span>
          <div class="relative z-[1]">
            <div class="section-head">
              <span class="section-num">02</span>
              <span class="section-name">节点读数</span>
              <span class="section-rule"></span>
              <span class="prop-file-no">{{ cur.date }}</span>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div class="stat-tile">
                <div class="stat-num"><CountUp :value="cur.marketDemand" /><span class="text-sm">%</span></div>
                <div class="stat-label">市场需求</div>
              </div>
              <div class="stat-tile">
                <div class="stat-num"><CountUp :value="cur.adoptionRate" /><span class="text-sm">%</span></div>
                <div class="stat-label">企业采用</div>
              </div>
              <div class="stat-tile">
                <div class="stat-num" :class="cur.matchRate < 70 ? 'coral' : ''"><CountUp :value="cur.matchRate" /><span class="text-sm">%</span></div>
                <div class="stat-label">团队匹配</div>
              </div>
              <div class="stat-tile">
                <div class="stat-num" style="font-size:18px;padding-top:3px">{{ cur.salaryRange }}</div>
                <div class="stat-label">薪资范围</div>
              </div>
            </div>

            <div class="mt-3 p-3" style="background:rgba(0,9,76,0.02);border:1px dashed var(--ent-rule)">
              <div class="prop-label">市场背景</div>
              <p class="dossier-body">{{ cur.marketContext }}</p>
            </div>

            <div class="mt-3">
              <div class="review-head pro">▲ 行业催化事件 <span class="flex-1"></span><span class="review-count">×{{ cur.industryEvents.length }}</span></div>
              <div class="flex flex-wrap gap-1.5 mt-2">
                <span v-for="e in cur.industryEvents" :key="e" class="diag-tag">{{ e }}</span>
              </div>
            </div>

            <div class="footnote" style="margin-top:12px">数据来源：<span class="src">{{ cur.dataSources.join(' · ') }}</span></div>
          </div>
        </section>

        <!-- 03 技能定级表 -->
        <section class="panel-doc p-4 lg:col-span-3">
          <span class="watermark-num">03</span>
          <div class="relative z-[1]">
            <div class="section-head">
              <span class="section-num">03</span>
              <span class="section-name">技能定级表</span>
              <span class="section-rule"></span>
              <span
                v-for="ch in changeLegend"
                :key="ch.key"
                class="sk-change"
                :class="ch.cls"
                style="margin:0 0 0 6px"
              >{{ ch.icon }} {{ ch.label }} {{ stats[ch.key as keyof typeof stats] }}</span>
            </div>

            <div>
              <div
                v-for="s in cur.skills"
                :key="s.name"
                class="doc-skill"
                :class="{ 'doc-skill--removed': s.change === 'removed' }"
              >
                <div class="sk-head">
                  <span v-if="s.change !== 'unchanged'" class="sk-change" :class="changeCls(s.change)">{{ changeLabel(s.change) }}</span>
                  <span class="sk-name" :title="s.name">{{ s.name }}</span>
                  <span class="sk-level">{{ levelLabel(s.level) }}</span>
                  <span class="flex-1"></span>
                  <span class="sk-wt" :title="'权重 ' + Math.round(s.weight * 100) + '%'">{{ Math.round(s.weight * 100) }}%</span>
                </div>
                <div class="ink-bar mt-1"><i :style="{ width: (s.weight * 100) + '%' }"></i></div>
                <div class="flex items-center gap-2 mt-1">
                  <span class="footnote" style="margin:0">保鲜度 <span class="src" :style="{ color: freshColor(s.freshness) }">{{ s.freshness }}</span></span>
                  <span v-if="s.changeReason" class="sk-reason">· {{ s.changeReason }}</span>
                </div>
              </div>
            </div>

            <div class="footnote" style="margin-top:10px">权重=技能占比 · 保鲜度=与市场匹配新鲜度 · <span class="src">数据来源：招聘JD + 行业报告 + 学术论文</span></div>
          </div>
        </section>
      </div>

      <!-- ═══ 04 工具栈 + 05 典型项目 ═══ -->
      <div v-if="cur" class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <section class="panel-doc p-4">
          <div class="section-head">
            <span class="section-num">04</span>
            <span class="section-name">常用工具栈</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">{{ cur.date }}</span>
          </div>
          <div class="flex flex-wrap gap-1.5 mt-2">
            <span v-for="t in cur.tools" :key="t" class="diag-tag">{{ t }}</span>
          </div>
        </section>
        <section class="panel-doc p-4">
          <div class="section-head">
            <span class="section-num">05</span>
            <span class="section-name">典型项目</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">×{{ cur.typicalProjects.length }}</span>
          </div>
          <div class="flex flex-wrap gap-1.5 mt-2">
            <span v-for="p in cur.typicalProjects" :key="p" class="diag-tag">{{ p }}</span>
          </div>
        </section>
      </div>

      <!-- ═══ 06 版本对比 ═══ -->
      <section v-if="showDiff && diffBase !== null" class="panel-doc p-4">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">06</span>
            <span class="section-name">版本对比</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">基准 <span class="src">{{ evo.timeline[diffBase].date }}</span> ←→ 当前 <span class="src">{{ cur?.date }}</span></span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mt-2">
            <div v-for="(side, si) in diffSides" :key="si">
              <div class="review-head" :class="si === 0 ? 'con' : 'pro'">
                {{ si === 0 ? '— 基准 ' + evo.timeline[diffBase].date : '▲ 当前 ' + cur?.date }}
                <span class="flex-1"></span>
                <span class="review-count">×{{ side.skills.length }}</span>
              </div>
              <div
                v-for="s in side.skills"
                :key="s.name"
                class="doc-skill"
                :class="{ 'doc-skill--removed': s.change === 'removed' }"
              >
                <div class="sk-head">
                  <span v-if="s.change !== 'unchanged'" class="sk-change" :class="changeCls(s.change)">{{ changeLabel(s.change) }}</span>
                  <span class="sk-name" :title="s.name">{{ s.name }}</span>
                  <span class="sk-level">{{ levelLabel(s.level) }}</span>
                  <span class="flex-1"></span>
                  <span class="sk-wt">{{ Math.round(s.weight * 100) }}%</span>
                </div>
                <div class="ink-bar mt-1"><i :style="{ width: (s.weight * 100) + '%' }"></i></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══ 页脚 ═══ -->
      <footer class="report-footer">
        <div>
          <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
          <div class="foot-label" style="margin-top:3px">编制 · 张明　复核 · 职域智联</div>
        </div>
        <div class="foot-label">数据截止 2026-08-03 · PAGE 06 / 08</div>
      </footer>
    </template>

    <!-- ═══ 空态：无演化档案 ═══ -->
    <template v-else>
      <section class="panel-doc p-8">
        <div class="doc-empty">
          <div class="lines"><i></i><i></i><i></i></div>
          "该岗位暂无演化档案 · 数据源待接入"
        </div>
        <div class="text-center mt-3">
          <router-link to="/enterprise/positions" class="ent-link">← 返回岗位标准库</router-link>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useEnterpriseStore } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import CountUp from '@/components/enterprise/CountUp.vue'
import EnterpriseLifeCurve from '@/components/enterprise/EnterpriseLifeCurve.vue'

const route = useRoute()
const store = useEnterpriseStore()

const id = computed(() => route.params.id as string)
const position = computed(() => store.positions.find((p) => p.id === id.value))
const hasEvo = computed(() => !!store.evolutions[id.value])
const evo = computed(() => (hasEvo.value ? store.currentEvolution : null))
const lastDate = computed(() => {
  const tl = evo.value?.timeline
  return tl?.length ? tl[tl.length - 1].date : '—'
})

const selectedIndex = ref(0)
const showDiff = ref(false)
const diffBase = ref<number | null>(null)

const cur = computed(() => evo.value?.timeline[selectedIndex.value])

const dossierNo = computed(() => {
  const n = Number(String(id.value).split('-')[1])
  return (Number.isFinite(n) ? n : 1).toString().padStart(2, '0')
})

const demandGrowth = computed(() => {
  if (!evo.value) return '—'
  const first = evo.value.timeline[0]?.marketDemand || 0
  const last = evo.value.timeline[evo.value.timeline.length - 1]?.marketDemand || 0
  return (last - first).toFixed(0)
})

const stats = computed(() => {
  const s = cur.value?.skills || []
  return {
    added: s.filter((x) => x.change === 'added').length,
    removed: s.filter((x) => x.change === 'removed').length,
    upgraded: s.filter((x) => x.change === 'upgraded').length,
    downgraded: s.filter((x) => x.change === 'downgraded').length,
  }
})

const diffSides = computed(() => {
  if (!evo.value || diffBase.value === null) return []
  return [
    { skills: evo.value.timeline[diffBase.value].skills },
    { skills: cur.value?.skills || [] },
  ]
})

// ── 变更标记映射 ──
const changeMap: Record<string, { icon: string; label: string; cls: string }> = {
  added: { icon: '+', label: '新增', cls: 'sk-change--added' },
  upgraded: { icon: '↑', label: '升级', cls: 'sk-change--upgraded' },
  downgraded: { icon: '↓', label: '降级', cls: 'sk-change--downgraded' },
  removed: { icon: '−', label: '删除', cls: 'sk-change--removed' },
}
const changeLegend = ['added', 'upgraded', 'downgraded', 'removed'].map((k) => ({ key: k, ...changeMap[k] }))

function changeCls(c: string): string { return changeMap[c]?.cls || '' }
function changeLabel(c: string): string { return changeMap[c] ? changeMap[c].icon + ' ' + changeMap[c].label : '' }
function levelLabel(l: string): string {
  const m: Record<string, string> = { basic: '入门', intermediate: '中级', advanced: '高级', expert: '专家' }
  return m[l] || l
}
function freshColor(f: number): string {
  return f >= 80 ? 'var(--ent-navy)' : f >= 60 ? 'var(--ent-coral)' : 'var(--ent-dim)'
}

// ── 节点选择 / 对比 ──
function pickNode(i: number) {
  if (showDiff.value) diffBase.value = i
  else selectedIndex.value = i
}
function toggleDiff() {
  showDiff.value = !showDiff.value
  diffBase.value = null
}

// ── 播放轨迹（自动翻阅）──
const playing = ref(false)
let playTimer = 0
function togglePlay() {
  playing.value = !playing.value
  if (playing.value) {
    stopPlay()
    playTimer = window.setInterval(() => {
      if (!evo.value?.timeline.length) return
      selectedIndex.value = selectedIndex.value >= evo.value.timeline.length - 1 ? 0 : selectedIndex.value + 1
    }, 1800)
  } else stopPlay()
}
function stopPlay() { window.clearInterval(playTimer) }

// ── 操作反馈 ──
const showNotification = ref(false)
const notifyMessage = ref('')
const notifyDetail = ref('')
let notifyTimer = 0

function notify(msg: string, detail: string) {
  notifyMessage.value = msg
  notifyDetail.value = detail
  showNotification.value = true
  window.clearTimeout(notifyTimer)
  notifyTimer = window.setTimeout(() => { showNotification.value = false }, 6000)
}
function exportDossier() {
  notify('岗位档案已导出', `${position.value?.name || evo.value?.positionName} · PDF 含演化曲线与技能定级表`)
}
function exportReport() {
  notify('演化报告已生成', `${position.value?.name || evo.value?.positionName} · 覆盖 ${evo.value?.timeline[0]?.date} → ${lastDate.value}`)
}

// ── 同步 + 加载演化档案（T3，/api/enterprise/positions/{id}/evolution）──
function sync() {
  store.setCurrentPosition(id.value)
  stopPlay()
  playing.value = false
  showDiff.value = false
  diffBase.value = null
  selectedIndex.value = (evo.value?.timeline.length || 1) - 1
}
async function load() {
  sync()
  await store.fetchEvolution(id.value)
  // 真实 T3 时间轴到位后，快照到最新节点
  selectedIndex.value = (evo.value?.timeline.length || 1) - 1
}
watch(id, load)
onMounted(() => {
  load()
  store.fetchPositions()
})
onUnmounted(() => stopPlay())
</script>
