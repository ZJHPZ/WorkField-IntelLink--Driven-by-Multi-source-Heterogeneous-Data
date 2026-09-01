<template>
  <div class="space-y-4">
    <!-- ═══ 文件抬头：批次批阅 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">批量审计</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            JD BATCH AUDIT · BATCH 2026-08-01 · {{ total }} ITEMS · {{ completed }} COMPLETED
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-DIAG-B001</span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="pendingReview > 0" class="seal-chip" style="color:#fff;border-color:#fff">● 待复核 {{ pendingReview }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">REV 2026.08</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="rerun">重新审计</button>
      <button class="ent-btn ent-btn--ghost" @click="exportReport">导出审计报告</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">批次 2026-08-01 · 8 条目 · 解析完成 100%</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条：批次读数 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="total" /></div>
        <div class="stat-label">批次条目</div>
        <div class="stat-sub">BATCH 2026-08-01</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="completed" /></div>
        <div class="stat-label">已完成</div>
        <div class="stat-sub">评分入库</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="pendingReview > 0 ? 'coral coral-glow' : ''"><CountUp :value="pendingReview" /></div>
        <div class="stat-label">待复核</div>
        <div class="stat-sub">幻觉标注确认</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="avgScore" /></div>
        <div class="stat-label">平均评分</div>
        <div class="stat-sub">已完成条目</div>
      </div>
    </div>

    <!-- ═══ 流水线 + 待复核 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <!-- 01 审计流水线 -->
      <section class="panel-doc p-4 lg:col-span-2 self-start">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">审计流水线</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">5 STATIONS</span>
          </div>
          <div class="pipeline-rail mt-1">
            <div
              v-for="st in stationStats"
              :key="st.no"
              class="pipeline-stage"
              :class="{ 'pipeline-stage--active': st.active }"
            >
              <span class="pipeline-dot"></span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <span class="pipeline-name">{{ st.no }} · {{ st.name }}</span>
                  <span class="pipeline-count">{{ st.done }}/{{ st.total }}</span>
                </div>
                <div class="ink-bar mt-1"><i :class="st.active ? 'coral' : ''" :style="{ width: st.pct + '%' }"></i></div>
              </div>
              <span v-if="st.active" class="pipeline-mark" style="margin-left:10px">● 流转中</span>
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">批次节拍：<span class="src">平均单条 0.8s · 预计全批 12s</span></div>
        </div>
      </section>

      <!-- 02 待复核清单 -->
      <section class="panel-doc p-4 lg:col-span-3">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">02</span>
            <span class="section-name">待复核清单</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">{{ reviewQueue.length }} 条 · 幻觉防控门控</span>
          </div>
          <div>
            <div
              v-for="r in reviewQueue"
              :key="r.id"
              class="review-qrow"
              :class="{ 'review-qrow--done': reviewed.has(r.id) }"
            >
              <span class="review-qname">{{ r.name }}</span>
              <span class="review-qwhy">{{ r.reason }}</span>
              <span class="flex-1"></span>
              <template v-if="!reviewed.has(r.id)">
                <SealChip :status="r.status" />
                <button class="ent-btn ent-btn--ghost review-qbtn" @click="confirmReview(r)">人工复核</button>
              </template>
              <span v-else class="review-qok">✓ 已复核</span>
            </div>
            <div v-if="!reviewQueue.length" class="doc-empty">
              <div class="lines"><i></i><i></i><i></i></div>
              "本批无待复核标注 · 幻觉防控全绿"
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">复核记录将写入审计日志 · <span class="src">幻觉标注率 100%</span></div>
        </div>
      </section>
    </div>

    <!-- ═══ 03 条目审计台账 ═══ -->
    <section class="panel-doc p-4">
      <div class="relative z-[1]">
        <div class="section-head">
          <span class="section-num">03</span>
          <span class="section-name">条目审计台账</span>
          <span class="section-rule"></span>
          <span class="footnote" style="margin:0">按评分升序 · 最差置顶</span>
        </div>
        <div class="tbl-head tbl-head--audit">
          <span>JD No.</span>
          <span>岗位 / 文件名</span>
          <span style="text-align:right">通胀</span>
          <span style="text-align:right">缺×</span>
          <span style="text-align:right">冗×</span>
          <span style="text-align:right">评分</span>
          <span style="text-align:right">状态</span>
          <span style="text-align:center">复核</span>
        </div>
        <div>
          <div
            v-for="(r, idx) in ledger"
            :key="r.id"
            class="tbl-row tbl-row--audit"
            :class="{ 'tbl-row--run': !r.done }"
          >
            <span class="cell-dim">{{ r.fileNo }}</span>
            <span class="min-w-0">
              <router-link v-if="r.done" :to="'/enterprise/diagnose'" class="cell-name block truncate">{{ r.name }}</router-link>
              <span v-else class="cell-name block truncate" style="color:var(--ent-dim)">{{ r.name }}</span>
              <span class="cell-dim block truncate" style="font-size:9px;margin-top:1px">{{ r.sub }}</span>
            </span>
            <span class="cell-num justify-end" :class="r.done ? inflCls(r.inflation) : ''">{{ r.done ? r.inflation + '%' : '—' }}</span>
            <span class="cell-num justify-end">{{ r.done ? r.missing : '—' }}</span>
            <span class="cell-num justify-end">{{ r.done ? r.redundant : '—' }}</span>
            <span class="cell-num justify-end">{{ r.done ? r.score : '—' }}</span>
            <span class="cell-status">
              <SealChip v-if="r.done" :status="r.status" :style="{ animationDelay: (idx * 0.05) + 's' }" />
              <span v-else class="run-chip">S{{ r.stage }} 流转中</span>
            </span>
            <span class="text-center">
              <span v-if="!r.done" class="audit-flag audit-flag--ok">—</span>
              <span v-else-if="r.flagged" class="audit-flag" :class="{ 'audit-flag--ok': reviewed.has(r.id) }">{{ reviewed.has(r.id) ? '✓' : '●' }}</span>
              <span v-else class="audit-flag audit-flag--ok">—</span>
            </span>
          </div>
        </div>
        <div class="footnote" style="margin-top:10px">审计维度：<span class="src">通胀=虚高技能占比 · 缺失=市场缺口 · 冗余=过时无关词 · 幻觉=AI 标注复核标记</span>　点击已入库条目进入单份质检报告</div>
      </div>
    </section>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">批审 · JD 诊断 Agent　复核 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-01 · PAGE 05 / 08</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { JDDiagnosis } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import CountUp from '@/components/enterprise/CountUp.vue'
import { downloadCsv, today } from '@/utils/export'

const store = useEnterpriseStore()

// ── 审计条目模型 ──
interface AuditRow {
  id: string
  name: string
  sub: string
  fileNo: string
  done: boolean
  stage: number        // 1-5 当前站台；5 = 已完成入库
  inflation: number
  missing: number
  redundant: number
  score: number
  status: 'healthy' | 'warning' | 'critical'
  flagged: boolean     // 幻觉标注待复核
}

// 已完成条目 = 诊断库（含待复核标记）
const doneRows = computed<AuditRow[]>(() =>
  store.diagnoses.map((d: JDDiagnosis) => ({
    id: d.id,
    name: d.positionName,
    sub: d.jdTitle,
    fileNo: '',
    done: true,
    stage: 5,
    inflation: Math.round(d.inflationIndex * 100),
    missing: d.missingKeywords.length,
    redundant: d.redundantKeywords.length,
    score: d.overallScore,
    status: d.status,
    flagged: d.status === 'critical' || (d.status === 'warning' && d.inflationIndex >= 0.35),
  }))
)

// 流转中条目（流水线节点）
const runRows: AuditRow[] = [
  { id: 'run-1', name: '数据开发工程师', sub: '资深数据开发', fileNo: 'RUN-01', done: false, stage: 3, inflation: 0, missing: 0, redundant: 0, score: 0, status: 'warning', flagged: false },
  { id: 'run-2', name: '算法工程师 · 校招', sub: '2026 校招 JD', fileNo: 'RUN-02', done: false, stage: 4, inflation: 0, missing: 0, redundant: 0, score: 0, status: 'warning', flagged: false },
]

// ── 台账：已完成按评分升序 + 流转中 ──
const ledger = computed<AuditRow[]>(() => {
  const done = [...doneRows.value]
    .sort((a, b) => a.score - b.score)
    .map((r, i) => ({ ...r, fileNo: 'DIAG-' + String(i + 1).padStart(2, '0') }))
  return [...done, ...runRows]
})

const total = computed(() => ledger.value.length)
const completed = computed(() => doneRows.value.length)
const avgScore = computed(() => Math.round(doneRows.value.reduce((s, r) => s + r.score, 0) / Math.max(doneRows.value.length, 1)))

function inflCls(v: number): string {
  return v < 30 ? '' : v < 50 ? 'coral' : 'faded'
}

// ── 流水线站台统计 ──
const stations = [
  { no: 'S1', name: 'JD 解析' },
  { no: 'S2', name: '通胀检测' },
  { no: 'S3', name: '缺失/冗余提取' },
  { no: 'S4', name: '幻觉标注' },
  { no: 'S5', name: '评分入库' },
]
const stationStats = computed(() => {
  const rowsAll = [...doneRows.value, ...runRows]
  const totalCount = rowsAll.length
  let frontierIdx = stations.findIndex((_, i) => {
    const need = i + 1
    return rowsAll.filter((r) => r.stage >= need).length < totalCount
  })
  if (frontierIdx < 0) frontierIdx = stations.length - 1
  return stations.map((st, i) => {
    const done = rowsAll.filter((r) => r.stage >= i + 1).length
    return { ...st, done, total: totalCount, pct: Math.round((done / totalCount) * 100), active: i === frontierIdx }
  })
})

// ── 待复核队列 ──
const reviewQueue = computed(() =>
  doneRows.value
    .filter((r) => r.flagged)
    .map((r) => ({
      id: r.id,
      name: r.name,
      status: r.status,
      reason: r.status === 'critical'
        ? `注水 ${r.inflation}% · 标注需人工确认`
        : `通胀 ${r.inflation}% · 缺失/冗余标注待确认`,
    }))
)
const reviewed = ref<Set<string>>(new Set())
const pendingReview = computed(() => reviewQueue.value.filter((r) => !reviewed.value.has(r.id)).length)

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

function confirmReview(r: { id: string; name: string }) {
  reviewed.value = new Set(reviewed.value).add(r.id)
  notify('复核确认', `${r.name} · 幻觉标注已确认 · 记录写入审计日志`)
}
function rerun() {
  notify('批次重跑启动', 'BATCH 2026-08-01 · 正在重跑 8 条目审计流水线…')
  store.fetchDiagnoses()
  setTimeout(() => notify('批次审计完成', '8 条目全部通过流水线 · 评分已更新'), 2000)
}
function exportReport() {
  const headers = ['JD No.', '岗位/文件名', '通胀', '缺失', '冗余', '评分', '状态', '复核']
  const rows: unknown[][] = ledger.value.map((r) => [
    r.fileNo || r.id,
    r.sub ? `${r.name} · ${r.sub}` : r.name,
    r.done ? r.inflation + '%' : '—',
    r.done ? r.missing : '—',
    r.done ? r.redundant : '—',
    r.done ? r.score : '—',
    r.status,
    !r.done ? '流转中' : r.flagged ? (reviewed.value.has(r.id) ? '已复核' : '待复核') : '—',
  ])
  downloadCsv(`批量审计报告_${today()}.csv`, headers, rows)
  notify('审计报告已导出', `BATCH 2026-08-01 · ${total.value} 条目 · CSV 已下载`)
}

onMounted(() => { store.fetchDiagnoses() })
</script>
