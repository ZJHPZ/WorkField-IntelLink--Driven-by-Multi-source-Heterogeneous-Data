<template>
  <div class="space-y-4">
    <!-- ═══ 报告头 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">人才需求预测 · 2026 Q3→Q4</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            TALENT FORECAST · 升温榜 {{ emerging.length }} · 降温榜 {{ cooling.length }} · 语料窗口 90 天
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-FCST-01 · 趋势外推模型 v2.4</span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="hotCount" class="seal-chip" style="color:#fff;border-color:#fff">● 高热 {{ hotCount }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">窗口 90 天</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="generateRec">生成招聘建议</button>
      <button class="ent-btn ent-btn--ghost" @click="exportReport">导出预测报告</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">语料 招聘JD 1250 条 · 行业报告 8 份 · 更新 2026-08-03</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num coral"><CountUp :value="emerging.length" /></div>
        <div class="stat-label">升温技能</div>
        <div class="stat-sub">趋势上行</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="cooling.length" /></div>
        <div class="stat-label">降温技能</div>
        <div class="stat-sub">需求收缩</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" style="font-size:15px;padding-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="topEmerging?.name">{{ topEmerging?.name || '—' }}</div>
        <div class="stat-label">高热榜首</div>
        <div class="stat-sub">新兴度 {{ topScore }}%</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="hotCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="hotCount" /></div>
        <div class="stat-label">建议扩招</div>
        <div class="stat-sub">高热+上升</div>
      </div>
    </div>

    <!-- ═══ 01 热力榜 + 02 降温榜 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <section class="panel-doc p-4 lg:col-span-3">
        <span class="watermark-num">01</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">热力榜 · 升温技能</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">按新兴度降序 · 前三珊瑚</span>
          </div>
          <div class="trend-row" style="grid-template-columns:28px 1.2fr 0.9fr 0.62fr;padding:2px 4px 6px;border-bottom:2px solid var(--ent-navy)">
            <span></span>
            <span class="footnote" style="margin:0">技能</span>
            <span class="footnote" style="margin:0;text-align:right">新兴度</span>
            <span class="footnote" style="margin:0;text-align:right">判定</span>
          </div>
          <div>
            <div v-for="(s, i) in emerging" :key="s.name" class="trend-row">
              <span class="rank-plate" :class="{ 'rank-plate--top': i < 3 }">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="trend-name" :title="s.name">{{ s.name }}</span>
              <div class="trend-heat">
                <div class="ink-bar"><i :class="{ coral: s.phase === 'hot' }" :style="{ width: (s.score * 100) + '%' }"></i></div>
                <span class="heat-val" :class="{ coral: s.phase === 'hot' }">{{ pct(s.score) }}%</span>
              </div>
              <span class="trend-tag" :class="phaseCls(s.phase)">{{ phaseLabel(s.phase) }}</span>
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">新兴度 = 90 天语料增量归一化 · <span class="src">上升/新增相位来自趋势分段</span></div>
        </div>
      </section>

      <section class="panel-doc p-4 lg:col-span-2 self-start">
        <span class="watermark-num">02</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">02</span>
            <span class="section-name">降温榜</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">按衰退度降序</span>
          </div>
          <div>
            <div v-for="(s, i) in cooling" :key="s.name" class="trend-row--slim">
              <span class="rank-plate">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="trend-name" :class="{ 'line-through': s.phase === 'fading' }" :title="s.name">{{ s.name }}</span>
              <span class="trend-tag" :class="phaseCls(s.phase)">{{ phaseLabel(s.phase) }}</span>
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">衰退度 = 语料份额回落速率 · <span class="src">褪色墨=衰退</span></div>
        </div>
      </section>
    </div>

    <!-- ═══ 03 研判建议 + 04 预测口径 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <section class="panel-doc p-4 lg:col-span-3">
        <span class="watermark-num">03</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">03</span>
            <span class="section-name">研判建议</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">招聘/培训批示</span>
          </div>
          <div class="rec-box mt-2">
            <span class="rec-stamp">研</span>
            <div class="min-w-0 flex-1">
              <div class="prop-label" style="margin:0">研判批示 · 建议优先招聘/培训</div>
              <p class="dossier-body">{{ store.forecast.recommendation }}</p>
              <div class="flex flex-wrap gap-2 mt-3">
                <button class="ent-btn ent-btn--coral" @click="adopt">采纳 · 转招聘计划</button>
                <button class="ent-btn ent-btn--ghost" @click="toTraining">转培训计划</button>
                <button class="ent-btn ent-btn--ghost" @click="ignore">忽略</button>
              </div>
              <div class="rec-meta">批示人 · 张明　待审批 · 招聘 COE</div>
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">建议由高热/上升技能直接推导 · 转岗培训承接降温技能人才 · <span class="src">幻觉防控：建议均来自指标计算</span></div>
        </div>
      </section>

      <section class="panel-doc p-4 lg:col-span-2 self-start">
        <span class="watermark-num">04</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">04</span>
            <span class="section-name">预测口径</span>
            <span class="section-rule"></span>
          </div>
          <div class="leader-row"><span class="label">预测模型</span><span class="dots"></span><span class="val">趋势外推 v2.4</span></div>
          <div class="leader-row"><span class="label">语料窗口</span><span class="dots"></span><span class="val">90 天</span></div>
          <div class="leader-row"><span class="label">语料规模</span><span class="dots"></span><span class="val">1250 条 JD</span></div>
          <div class="leader-row"><span class="label">置信下限</span><span class="dots"></span><span class="val coral">87%</span></div>
          <div class="mt-3 p-3" style="background:rgba(0,9,76,0.02);border:1px dashed var(--ent-rule)">
            <div class="prop-label">方法说明</div>
            <p class="dossier-body">新兴度 = 90 天内技能提及增量归一化；衰退度 = 语料份额回落速率。升/降温榜互为对照，供招聘与转岗双向排布。</p>
          </div>
          <div class="footnote" style="margin-top:10px">数据来源：<span class="src">招聘JD 1250 条 · 行业报告 8 份 · 学术论文 26 篇</span></div>
        </div>
      </section>
    </div>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">预测 · 趋势研判 Agent　审批 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-03 · PAGE 09 / 09</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { SkillTrend } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import CountUp from '@/components/enterprise/CountUp.vue'

const store = useEnterpriseStore()

const emerging = computed(() => store.forecast.emerging)
const cooling = computed(() => store.forecast.cooling)
const topEmerging = computed(() => emerging.value[0] || null)
const topScore = computed(() => (topEmerging.value ? Math.round(topEmerging.value.score * 100) : 0))
const hotCount = computed(() => emerging.value.filter((s) => s.phase === 'hot' || s.phase === 'rising').length)

// ── 相位映射 ──
const phaseMap: Record<string, { label: string; cls: string }> = {
  hot: { label: '高热', cls: 'trend-tag--hot' },
  rising: { label: '上升', cls: 'trend-tag--rising' },
  new: { label: '新增', cls: 'trend-tag--new' },
  cooling: { label: '降温', cls: 'trend-tag--cooling' },
  fading: { label: '衰退', cls: 'trend-tag--fading' },
}
function phaseLabel(p: string): string { return phaseMap[p]?.label || p }
function phaseCls(p: string): string { return phaseMap[p]?.cls || 'trend-tag--cooling' }
function pct(n: number): number { return Math.round(n * 100) }

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
function generateRec() {
  notify('招聘建议已生成', `优先招聘 ${hotCount.value} 项 · 覆盖 ${emerging.value.slice(0, 5).map((s) => s.name).join('、')}`)
}
function exportReport() {
  notify('预测报告已导出', `人才需求预测 · 升温榜 ${emerging.value.length} · 降温榜 ${cooling.value.length} · PDF 已生成`)
}
function adopt() {
  notify('批示已采纳', `已转招聘计划 · 建议招聘 ${hotCount.value} 项 · 待 COE 排期`)
}
function toTraining() {
  notify('已转培训计划', `转岗培训承接降温技能 · 覆盖 ${cooling.value.filter((s) => s.phase === 'fading').length} 项衰退技能`)
}
function ignore() {
  notify('已忽略批示', '本次研判建议未采纳 · 已归档')
}

onMounted(() => { store.fetchForecast() })
</script>
