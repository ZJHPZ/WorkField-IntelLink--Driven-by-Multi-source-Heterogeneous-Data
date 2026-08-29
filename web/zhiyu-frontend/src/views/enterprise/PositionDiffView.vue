<template>
  <div class="space-y-4">
    <template v-if="position && hasMarket">
      <!-- ═══ 报告头 ═══ -->
      <header class="doc-masthead px-4 py-4">
        <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
          <div class="min-w-0">
            <h1 class="ent-title-serif text-lg font-bold leading-tight">市场对比报告 · {{ position.name }}</h1>
            <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
              MARKET VS STANDARD · {{ rows.length }} SKILLS · 近 90 天语料聚合 · 对齐度 {{ alignment }}%
            </p>
            <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-POS-{{ dossierNo }}-DIFF</span>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="suggestRows.length" class="seal-chip" style="color:#fff;border-color:#fff">● 需修订 {{ suggestRows.length }}</span>
            <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">REV 2026.08</span>
          </div>
        </div>
      </header>

      <!-- ═══ 文档操作栏 ═══ -->
      <div class="flex flex-wrap items-center gap-2">
        <button class="ent-btn ent-btn--coral" @click="generateDraft">生成修订建议</button>
        <button class="ent-btn ent-btn--ghost" @click="exportReport">导出对比报告</button>
        <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">标准 REV 2026.08 · 市场语料 352 条 JD · 更新 2026-08-03</span>
      </div>

      <NotificationBar
        :visible="showNotification"
        :message="notifyMessage"
        :detail="notifyDetail"
        @close="showNotification=false"
      />

      <!-- ═══ 摘要条：对齐读数 ═══ -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div class="stat-tile">
          <div class="stat-num" :class="alignment < 80 ? 'coral coral-glow' : ''"><CountUp :value="alignment" /><span class="text-sm">%</span></div>
          <div class="stat-label">对齐度</div>
          <div class="stat-sub">标准 ≈ 市场</div>
        </div>
        <div class="stat-tile">
          <div class="stat-num" :class="gapCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="gapCount" /></div>
          <div class="stat-label">缺口项</div>
          <div class="stat-sub">标准落后市场</div>
        </div>
        <div class="stat-tile">
          <div class="stat-num"><CountUp :value="overCount" /></div>
          <div class="stat-label">过载项</div>
          <div class="stat-sub">标准高于市场</div>
        </div>
        <div class="stat-tile">
          <div class="stat-num"><CountUp :value="suggestRows.length" /></div>
          <div class="stat-label">建议数</div>
          <div class="stat-sub">待生成草稿</div>
        </div>
      </div>

      <!-- ═══ 01 差异清单 ═══ -->
      <section class="panel-doc p-4">
        <span class="watermark-num">01</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">差异清单</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">按差异幅度排序 · 一致口径 ≤ 3pp</span>
          </div>
          <div class="diff-head">
            <span>技能</span>
            <span style="text-align:right">标准 · REV 2026.08</span>
            <span style="text-align:right">市场 · 语料聚合</span>
            <span style="text-align:right">差异</span>
            <span style="text-align:right">判定</span>
          </div>
          <div>
            <div v-for="r in rows" :key="r.name" class="diff-row" :class="{ 'diff-row--drop': r.kind === 'drop' }">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="diff-name" :title="r.name">{{ r.name }}</span>
                  <span v-if="r.kind !== 'aligned'" class="sk-change" :class="kindCls(r.kind)">{{ kindLabel(r.kind) }}</span>
                </div>
                <div v-if="r.suggestion" class="sk-reason" style="margin-top:2px">↳ {{ r.suggestion }}</div>
              </div>
              <span class="diff-cell" style="text-align:right">{{ cellText(r.std) }}</span>
              <span class="diff-cell" style="text-align:right">{{ cellText(r.mkt) }}</span>
              <span class="diff-gap" :class="gapCls(r)" style="text-align:right">{{ gapText(r) }}</span>
              <span class="diff-cell" style="text-align:right;color:var(--ent-ink-muted)">{{ noteText(r) }}</span>
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">市场侧由招聘 JD 语料聚合（近 90 天 · 352 条）· 标准侧为现行标准库 · <span class="src">差异 = 市场权重 − 标准权重（百分点）</span></div>
        </div>
      </section>

      <!-- ═══ 02 对齐口径 + 03 修订建议草稿 ═══ -->
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
        <section class="panel-doc p-4 lg:col-span-2 self-start">
          <span class="watermark-num">02</span>
          <div class="relative z-[1]">
            <div class="section-head">
              <span class="section-num">02</span>
              <span class="section-name">对齐口径</span>
              <span class="section-rule"></span>
            </div>
            <div class="leader-row"><span class="label">对齐度</span><span class="dots"></span><span class="val" :class="alignment < 80 ? 'coral' : ''">{{ alignment }}%</span></div>
            <div class="leader-row"><span class="label">一致项</span><span class="dots"></span><span class="val">{{ alignedCount }}</span></div>
            <div class="leader-row"><span class="label">缺口项</span><span class="dots"></span><span class="val coral">{{ gapCount }}</span></div>
            <div class="leader-row"><span class="label">过载项</span><span class="dots"></span><span class="val">{{ overCount }}</span></div>
            <div class="mt-3 p-3" style="background:rgba(0,9,76,0.02);border:1px dashed var(--ent-rule)">
              <div class="prop-label">口径说明</div>
              <p class="dossier-body">市场侧 = 招聘 JD 语料权重聚合（近 90 天）；标准侧 = 现行岗位标准。技能权重绝对差 ≤ 3pp 视为「一致」；标准权重低于市场 = 缺口；高于市场 = 过载。</p>
            </div>
            <div class="footnote" style="margin-top:10px">数据来源：<span class="src">招聘 JD 语料 352 条 · 行业报告 6 份 · 更新于 2026-08-03</span></div>
          </div>
        </section>

        <section class="panel-doc p-4 lg:col-span-3">
          <span class="watermark-num">03</span>
          <div class="relative z-[1]">
            <div class="section-head">
              <span class="section-num">03</span>
              <span class="section-name">修订建议草稿</span>
              <span class="section-rule"></span>
              <span class="footnote" style="margin:0">{{ draftGenerated ? draftItems.length + ' 条 · 待套用' : '未生成' }}</span>
            </div>

            <div v-if="draftGenerated" class="review-col">
              <div v-for="(it, i) in draftItems" :key="it.key" class="review-item" :class="{ 'draft-item--applied': applied.has(it.key) }">
                <div class="flex items-center gap-2">
                  <span class="flex-1 min-w-0">{{ it.suggestion }}</span>
                  <button v-if="!applied.has(it.key)" class="ent-btn ent-btn--ghost" style="flex:none;padding:2px 8px;font-size:9px" @click="applyDraft(it.key)">套用</button>
                  <span v-else class="review-qok">✓ 已套用</span>
                </div>
              </div>
            </div>
            <div v-else class="doc-empty">
              <div class="lines"><i></i><i></i><i></i></div>
              "点击「生成修订建议」汇总修订清单"
            </div>

            <div class="footnote" style="margin-top:10px">套用后进入标准修订草案 · 需审批后生效 · <span class="src">幻觉防控：建议均由数据差直接推导</span></div>
          </div>
        </section>
      </div>

      <!-- ═══ 页脚 ═══ -->
      <footer class="report-footer">
        <div>
          <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
          <div class="foot-label" style="margin-top:3px">对比 · 市场分析 Agent　审批 · 职域智联</div>
        </div>
        <div class="foot-label">数据截止 2026-08-03 · PAGE 07 / 08</div>
      </footer>
    </template>

    <!-- ═══ 空态 ═══ -->
    <template v-else>
      <section class="panel-doc p-8">
        <div class="doc-empty">
          <div class="lines"><i></i><i></i><i></i></div>
          "该岗位暂无市场语料 · 对比报告待生成"
        </div>
        <div class="text-center mt-3">
          <router-link to="/enterprise/positions" class="ent-link">← 返回岗位标准库</router-link>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useEnterpriseStore } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import CountUp from '@/components/enterprise/CountUp.vue'

const route = useRoute()
const store = useEnterpriseStore()

const id = computed(() => route.params.id as string)
const position = computed(() => store.positions.find((p) => p.id === id.value))
const hasMarket = computed(() => !!store.market[id.value]?.length)

const dossierNo = computed(() => {
  const n = Number(String(id.value).split('-')[1])
  return (Number.isFinite(n) ? n : 1).toString().padStart(2, '0')
})

// ── 差异计算 ──
type DiffKind = 'aligned' | 'under' | 'over' | 'new' | 'drop'
interface Cell { weight: number; level: string }
interface DiffRow {
  name: string
  std: Cell | null
  mkt: Cell | null
  gap: number      // 市场 − 标准（pp）；new=+整权重；drop=−整权重
  kind: DiffKind
  suggestion: string
}

const rows = computed<DiffRow[]>(() => {
  const std = position.value?.skills || []
  const mkt = store.market[id.value] || []
  const m = new Map(mkt.map((s) => [s.name, s]))
  const names = [...new Set([...std.map((s) => s.name), ...mkt.map((s) => s.name)])]

  return names
    .map((name): DiffRow => {
      const st = std.find((x) => x.name === name)
      const mk = m.get(name)
      if (!mk) return { name, std: { weight: st!.weight, level: st!.level }, mkt: null, gap: Math.round(-(st!.weight * 100)), kind: 'drop', suggestion: '' }
      if (!st) return { name, std: null, mkt: { weight: mk.weight, level: mk.level }, gap: Math.round(mk.weight * 100), kind: 'new', suggestion: '' }
      const gap = Math.round((mk.weight - st.weight) * 100)
      const kind: DiffKind = gap >= 4 ? 'under' : gap <= -4 ? 'over' : 'aligned'
      return { name, std: { weight: st.weight, level: st.level }, mkt: { weight: mk.weight, level: mk.level }, gap, kind, suggestion: '' }
    })
    .sort((a, b) => Math.abs(b.gap) - Math.abs(a.gap))
    .map((r) => ({ ...r, suggestion: suggestionFor(r) }))
})

function suggestionFor(r: DiffRow): string {
  if (r.kind === 'under') return `提升权重至市场水平：${(r.std!.weight * 100).toFixed(0)}% → ${(r.mkt!.weight * 100).toFixed(0)}%`
  if (r.kind === 'new') return `新增技能（市场要求 ${(r.mkt!.weight * 100).toFixed(0)}%，标准未覆盖）`
  if (r.kind === 'over') return `削减权重：${(r.std!.weight * 100).toFixed(0)}% → ${(r.mkt!.weight * 100).toFixed(0)}%（市场已降温）`
  if (r.kind === 'drop') return '标准保留但市场不再要求，考虑移出必需项'
  return ''
}

// ── 读数 ──
const gapCount = computed(() => rows.value.filter((r) => r.kind === 'under' || r.kind === 'new').length)
const overCount = computed(() => rows.value.filter((r) => r.kind === 'over' || r.kind === 'drop').length)
const alignedCount = computed(() => rows.value.filter((r) => r.kind === 'aligned').length)
const suggestRows = computed(() => rows.value.filter((r) => r.suggestion))

const alignment = computed(() => {
  if (!rows.value.length) return 0
  const penalty = rows.value.reduce((s, r) => s + Math.abs(r.gap), 0) * 0.6
  return Math.max(0, Math.min(100, Math.round(100 - penalty)))
})

// ── 单元格渲染 ──
function cellText(c: Cell | null): string {
  return c ? `${levelLabel(c.level)} ${(c.weight * 100).toFixed(0)}%` : '—'
}
function levelLabel(l: string): string {
  const m: Record<string, string> = { basic: '入门', intermediate: '中级', advanced: '高级', expert: '专家' }
  return m[l] || l
}
function gapText(r: DiffRow): string {
  if (r.kind === 'new') return '+' + r.gap
  if (r.kind === 'drop') return '-' + Math.abs(r.gap)
  if (r.gap === 0) return '±0'
  return r.gap > 0 ? '+' + r.gap : String(r.gap)
}
function gapCls(r: DiffRow): string {
  if (r.kind === 'under' || r.kind === 'new') return 'coral'
  if (r.kind === 'over' || r.kind === 'drop') return 'faded'
  return 'dim'
}
const kindMap: Record<DiffKind, { label: string; cls: string }> = {
  aligned: { label: '一致', cls: '' },
  under: { label: '缺口', cls: 'sk-change--added' },
  over: { label: '过载', cls: 'sk-change--downgraded' },
  new: { label: '新增', cls: 'sk-change--added' },
  drop: { label: '裁撤', cls: 'sk-change--removed' },
}
function kindLabel(k: DiffKind): string { return kindMap[k].label }
function kindCls(k: DiffKind): string { return kindMap[k].cls }
function noteText(r: DiffRow): string { return kindMap[r.kind].label }

// ── 修订建议草稿 ──
const draftGenerated = ref(false)
const applied = ref<Set<string>>(new Set())
const draftItems = computed(() => suggestRows.value.map((r) => ({ key: r.name, suggestion: r.suggestion })))

function generateDraft() {
  draftGenerated.value = true
  notify('修订建议已生成', `已汇总 ${draftItems.value.length} 条建议 · 生成标准修订草稿`)
}
function applyDraft(key: string) {
  applied.value = new Set(applied.value).add(key)
  notify('已套用修订', `${key} · 修订进入标准草案（待审批生效）`)
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
function exportReport() {
  notify('对比报告已导出', `${position.value?.name} · 含差异清单 ${rows.value.length} 项 · PDF 已生成`)
}

onMounted(() => { store.fetchPositions(); store.fetchMarket(id.value) })
</script>
