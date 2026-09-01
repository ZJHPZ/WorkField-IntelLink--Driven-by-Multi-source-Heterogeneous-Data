<template>
  <div class="space-y-4">
    <!-- ═══ 文件抬头：质检报告中心 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">JD 质量诊断</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            JD QUALITY DIAGNOSIS · REV 2026.08 · {{ store.diagnoses.length }} REPORTS
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-DIAG-001</span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="reviewCount > 0" class="seal-chip" style="color:#fff;border-color:#fff">● 待复核 {{ reviewCount }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">REV 2026.08</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="analyzeOne">单条诊断</button>
      <button class="ent-btn ent-btn--ghost" @click="importBatch">批量导入</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">最近批次 · 2026-08-01 · 5 份</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条：质检进度读数 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.diagnoses.length" /></div>
        <div class="stat-label">诊断总数</div>
        <div class="stat-sub">质检入库</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="healthyCount" /></div>
        <div class="stat-label">健康</div>
        <div class="stat-sub">无需修订</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="warningCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="warningCount" /></div>
        <div class="stat-label">预警</div>
        <div class="stat-sub">需微调</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="criticalCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="criticalCount" /></div>
        <div class="stat-label">严重</div>
        <div class="stat-sub">需打回重写</div>
      </div>
    </div>

    <!-- ═══ 主从式：诊断目录 + 质检报告 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <!-- 01 诊断目录 -->
      <section class="panel-doc p-4 lg:col-span-2 self-start">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">诊断目录</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">{{ store.diagnoses.length }} 份</span>
          </div>
          <div>
            <button
              v-for="(d, idx) in sorted"
              :key="d.id"
              class="prop-row"
              :class="{ 'prop-row--active': selected?.id === d.id }"
              @click="selected = d"
            >
              <span class="prop-file-no">{{ 'DIAG-2026-' + String(idx + 1).padStart(2, '0') }}</span>
              <span class="prop-row-title">{{ d.positionName }}</span>
              <span class="prop-row-conf" :class="scoreCls(d.overallScore)">{{ d.overallScore }}</span>
              <SealChip :status="d.status" />
            </button>
          </div>
          <div class="footnote" style="margin-top:10px">按评分升序 · 最差置顶 · 数据来源：<span class="src">JD 诊断 Agent · 通胀 / 缺失 / 冗余</span></div>
        </div>
      </section>

      <!-- 02 质检报告 -->
      <section class="panel-doc p-4 lg:col-span-3">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">02</span>
            <span class="section-name">质检报告</span>
            <span class="section-rule"></span>
            <span v-if="selected" class="prop-file-no">{{ reportNo }}</span>
          </div>

          <transition name="fade" mode="out-in">
            <div v-if="selected" :key="selected.id">
              <!-- 报告头 -->
              <div class="flex flex-wrap items-center gap-2">
                <span class="card-title ent-title-serif" style="font-size:15px">{{ selected.positionName }}</span>
                <SealChip :status="selected.status" :key="selected.id + selected.status" />
              </div>
              <div class="card-meta mt-1">{{ selected.jdTitle }} · 提交 {{ selected.submittedAt }} · 关键词 {{ selected.missingKeywords.length + selected.redundantKeywords.length }} 处</div>

              <!-- 总检区：总分 + 通胀指数 -->
              <div class="mt-3 p-3" style="background:rgba(0,9,76,0.02);border:1px dashed var(--ent-rule)">
                <div class="flex flex-wrap items-center gap-4">
                  <span class="prop-label">质检总分</span>
                  <span class="prop-conf" :class="scoreCls(selected.overallScore)"><CountUp :value="selected.overallScore" /><span class="text-sm"> / 100</span></span>
                  <span class="flex-1"></span>
                  <span class="prop-label">通胀指数</span>
                  <span class="prop-conf" :class="inflCls(selected.inflationIndex)" style="font-size:16px"><CountUp :value="inflPct(selected.inflationIndex)" /><span class="text-sm">%</span></span>
                </div>
                <div class="mt-3">
                  <div class="ink-bar flex-1 min-w-[120px]" style="width:auto"><i :class="inflBarCls(selected.inflationIndex)" :style="{ width: inflPct(selected.inflationIndex) + '%' }"></i></div>
                </div>
                <div class="gauge-scale">
                  <span>健康 &lt; 30%</span>
                  <span>预警 30–50%</span>
                  <span>严重 &gt; 50%</span>
                </div>
              </div>

              <!-- 发现明细：缺失 + 冗余 -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div>
                  <div class="review-head pro">▲ 缺失技能 <span class="flex-1"></span><span class="review-count">×{{ selected.missingKeywords.length }}</span></div>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <span v-for="kw in selected.missingKeywords" :key="kw" class="diag-tag diag-tag--miss">{{ kw }}</span>
                    <span v-if="!selected.missingKeywords.length" class="footnote" style="margin:0">无缺失 · 覆盖完整</span>
                  </div>
                </div>
                <div>
                  <div class="review-head con">— 冗余技能 <span class="flex-1"></span><span class="review-count">×{{ selected.redundantKeywords.length }}</span></div>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <span v-for="kw in selected.redundantKeywords" :key="kw" class="diag-tag diag-tag--redundant">{{ kw }}</span>
                    <span v-if="!selected.redundantKeywords.length" class="footnote" style="margin:0">无冗余 · 无注水</span>
                  </div>
                </div>
              </div>

              <!-- AI 修订建议 -->
              <div class="mt-4">
                <div class="review-col">
                  <div class="review-head pro">◆ AI 修订建议 <span class="flex-1"></span><span class="review-count">×{{ suggestions(selected).length }}</span></div>
                  <div v-for="(s, i) in suggestions(selected)" :key="i" class="review-item">{{ s }}</div>
                </div>
              </div>

              <!-- 质检动作 -->
              <div class="prop-actions">
                <button class="ent-btn ent-btn--coral" @click="exportReport(selected)">导出质检单</button>
                <button class="ent-btn ent-btn--ghost" @click="applyFix(selected)">应用修订</button>
                <span class="flex-1"></span>
                <span class="footnote" style="margin:0">诊断模型 v3 · 幻觉防控已启用</span>
              </div>
            </div>

            <div v-else class="doc-empty">
              <div class="lines"><i></i><i></i><i></i></div>
              "从左侧目录选择报告 · NO SELECTION"
            </div>
          </transition>
        </div>
      </section>
    </div>

    <!-- ═══ 附页：诊断能力基线 + 批次审计 ═══ -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <section class="panel-doc p-4">
        <div class="section-head">
          <span class="section-num">附</span>
          <span class="section-name">诊断能力基线</span>
          <span class="section-rule"></span>
        </div>
        <div class="leader-row"><span class="label">AI 生成标记率</span><span class="dots"></span><span class="val">100%</span></div>
        <div class="leader-row"><span class="label">多源交叉验证</span><span class="dots"></span><span class="val">92%</span></div>
        <div class="leader-row"><span class="label">人工复核通过率</span><span class="dots"></span><span class="val">96%</span></div>
        <div class="leader-row"><span class="label">数据源覆盖</span><span class="dots"></span><span class="val">3 类</span></div>
      </section>
      <section class="panel-doc p-4">
        <div class="section-head">
          <span class="section-num">附</span>
          <span class="section-name">批次审计</span>
          <span class="section-rule"></span>
        </div>
        <div class="leader-row"><span class="label">本批进度</span><span class="dots"></span><span class="val">3 / 5</span></div>
        <div class="leader-row"><span class="label">解析准确率</span><span class="dots"></span><span class="val">≥ 94%</span></div>
        <div class="leader-row"><span class="label">幻觉标注率</span><span class="dots"></span><span class="val">100%</span></div>
        <div class="leader-row"><span class="label">平均通胀指数</span><span class="dots"></span><span class="val coral">{{ avgInflation }}%</span></div>
      </section>
    </div>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">质检 · 诊断 Agent　复核 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-01 · PAGE 04 / 08</div>
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

// ── 质检读数 ──
const healthyCount = computed(() => store.diagnoses.filter((d) => d.status === 'healthy').length)
const warningCount = computed(() => store.diagnoses.filter((d) => d.status === 'warning').length)
const criticalCount = computed(() => store.diagnoses.filter((d) => d.status === 'critical').length)
const reviewCount = computed(() => warningCount.value + criticalCount.value)
const avgInflation = computed(() =>
  Math.round((store.diagnoses.reduce((s, d) => s + d.inflationIndex, 0) / Math.max(store.diagnoses.length, 1)) * 100)
)

// ── 评分 / 通胀分级 ──
function scoreCls(v: number): string {
  return v >= 80 ? 'navy' : v >= 60 ? 'coral' : 'faded'
}
function inflCls(v: number): string {
  return v < 0.3 ? 'navy' : v < 0.5 ? 'coral' : 'faded'
}
function inflBarCls(v: number): string {
  if (v >= 0.3 && v < 0.5) return 'coral'
  if (v >= 0.5) return 'faded'
  return ''
}
function inflPct(v: number): number {
  return Math.round(v * 100)
}

// ── 主从选择：按评分升序，最差置顶 ──
const selected = ref<JDDiagnosis | null>(null)
const sorted = computed(() => [...store.diagnoses].sort((a, b) => a.overallScore - b.overallScore))
const reportNo = computed(() => {
  if (!selected.value) return ''
  const idx = sorted.value.findIndex((d) => d.id === selected.value?.id)
  return idx >= 0 ? 'DIAG-2026-' + String(idx + 1).padStart(2, '0') : ''
})

// ── AI 修订建议（由诊断数据生成）──
function suggestions(d: JDDiagnosis): string[] {
  const s: string[] = []
  if (d.missingKeywords.length) s.push(`补充市场高频技能：${d.missingKeywords.join('、')}，纳入“必需”条目`)
  if (d.redundantKeywords.length) s.push(`删除过时或无关关键词：${d.redundantKeywords.join('、')}`)
  if (d.inflationIndex > 0.3) s.push(d.inflationIndex > 0.5 ? '注水严重：剥离堆砌性技能，仅保留真实必需项' : '通胀偏高：压缩“加分 / 了解”类技能堆砌')
  if (!s.length) s.push('JD 质量良好：技能覆盖与市场一致，无需修订')
  return s
}

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

function exportReport(d: JDDiagnosis) {
  const headers = ['指标', '数值']
  const rows: unknown[][] = [
    ['质检编号', reportNo.value],
    ['岗位名称', d.positionName],
    ['JD 标题', d.jdTitle],
    ['提交时间', d.submittedAt],
    ['质检总分', `${d.overallScore} / 100`],
    ['通胀指数', `${Math.round(d.inflationIndex * 100)}%`],
    ['诊断状态', d.status],
    ['缺失技能', d.missingKeywords.join('、') || '—'],
    ['冗余技能', d.redundantKeywords.join('、') || '—'],
    ['AI 修订建议', suggestions(d).join('；') || '—'],
  ]
  downloadCsv(`质检单_${d.positionName}_${today()}.csv`, headers, rows)
  notify('质检单已导出', `${reportNo.value} · ${d.positionName} · CSV 已下载`)
}
function applyFix(d: JDDiagnosis) {
  notify('修订已应用', `${d.positionName} 已生成修订版 JD 建议稿 · 可在诊断记录中追溯`)
}
function analyzeOne() {
  notify('单条诊断就绪', '粘贴 JD 文本 → 通胀 / 缺失 / 冗余检测 → 生成质检报告')
}
function importBatch() {
  notify('批量导入启动', '解析 5 份 JD · JD 诊断 Agent 批次审计中')
}

onMounted(async () => {
  await store.fetchDiagnoses()
  if (!selected.value && sorted.value.length) selected.value = sorted.value[0]
})
</script>
