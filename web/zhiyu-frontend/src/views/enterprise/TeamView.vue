<template>
  <div class="space-y-4">
    <!-- ═══ 报告头 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">团队技能盘点 · 技术部</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            TEAM SKILL INVENTORY · {{ gaps.length }} GAPS · 达标线 80% · 覆盖 {{ store.positions.length }} 岗位
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-TEAM-01 · 盘点周期 2026 H1</span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="highGapCount" class="seal-chip" style="color:#fff;border-color:#fff">● 高优 {{ highGapCount }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">达标线 80%</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="generatePlans">生成培训计划</button>
      <button class="ent-btn ent-btn--ghost" @click="exportReport">导出盘点表</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">盘点基准 · 全员技能评估 · 更新 2026-08-03</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="gaps.length" /></div>
        <div class="stat-label">盘点技能</div>
        <div class="stat-sub">未达标技能项</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="highGapCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="highGapCount" /></div>
        <div class="stat-label">高优缺口</div>
        <div class="stat-sub">需立即处置</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="affectedCount" /></div>
        <div class="stat-label">影响岗位</div>
        <div class="stat-sub">缺口波及范围</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="avgGap > 40 ? 'coral coral-glow' : ''"><CountUp :value="avgGap" /><span class="text-sm">%</span></div>
        <div class="stat-label">平均差距</div>
        <div class="stat-sub">vs 达标线</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="passRate === 0 ? 'faded' : ''"><CountUp :value="passRate" /><span class="text-sm">/{{ gaps.length }}</span></div>
        <div class="stat-label">达标项</div>
        <div class="stat-sub">已达 80% 线</div>
      </div>
    </div>

    <!-- ═══ 01 缺口台账 ═══ -->
    <section class="panel-doc p-4">
      <span class="watermark-num">01</span>
      <div class="relative z-[1]">
        <div class="section-head">
          <span class="section-num">01</span>
          <span class="section-name">缺口台账</span>
          <span class="section-rule"></span>
          <span class="footnote" style="margin:0">按差距降序 · 达标线 80% · 珊瑚刻线=目标</span>
        </div>
        <div class="tbl-head--team">
          <span>技能</span>
          <span>要求等级</span>
          <span>当前覆盖</span>
          <span style="text-align:right">差距</span>
          <span>覆盖岗位</span>
          <span>优先级</span>
          <span style="text-align:right">处置</span>
        </div>
        <div>
          <div v-for="g in gaps" :key="g.skillName" class="tbl-row--team">
            <div class="min-w-0">
              <div class="t-team-name" :title="g.skillName">{{ g.skillName }}</div>
            </div>
            <span class="t-team-level">{{ levelLabel(g.requiredLevel) }}</span>
            <div class="team-gauge">
              <div class="ink-bar"><i :class="{ coral: g.currentAvg < 80 }" :style="{ width: Math.min(g.currentAvg, 100) + '%' }"></i></div>
              <span class="gauge-val" :class="g.currentAvg < 80 ? 'coral' : ''">{{ g.currentAvg }}%</span>
              <span class="gauge-miss">差 {{ Math.max(0, 80 - g.currentAvg) }}</span>
            </div>
            <span class="t-gap" :class="gapCls(g.gap)">{{ g.gap }}%</span>
            <div class="t-cover">
              <span v-for="p in coveredNames(g)" :key="p">{{ p }}</span>
            </div>
            <span class="prio-chip" :class="prioCls(g.priority)">{{ prioLabel(g.priority) }}</span>
            <button class="t-dispose" @click="dispose(g)">
              {{ disposeFor(g.priority) }}<span class="arrow">→</span>
            </button>
          </div>
        </div>
        <div class="footnote" style="margin-top:10px">覆盖岗位按受缺口影响岗位数摘列 · 处置动作进入培训计划登记 · <span class="src">盘点基准：员工技能评估 + 岗位标准匹配</span></div>
      </div>
    </section>

    <!-- ═══ 02 培训计划 + 03 派单登记 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <section class="panel-doc p-4 lg:col-span-3">
        <span class="watermark-num">02</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">02</span>
            <span class="section-name">培训计划</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">×{{ planItems.length }} · 按差距排序</span>
          </div>
          <div class="review-col">
            <div v-for="(p, i) in planItems" :key="p.key" class="review-item">
              <div class="flex items-start gap-3">
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="sk-name" style="font-weight:700;font-size:12px;color:var(--ent-ink)">{{ p.title }}</span>
                    <span class="prio-chip" :class="prioCls(p.priority)" style="flex:none">{{ prioLabel(p.priority) }}</span>
                  </div>
                  <div class="dossier-body">{{ p.reason }}</div>
                  <div class="footnote" style="margin:0;margin-top:4px">涉及 <span class="src">{{ p.scope }}</span></div>
                </div>
                <button class="ent-btn ent-btn--ghost" style="flex:none;padding:3px 10px;font-size:10px" @click="createPlan(p)">
                  {{ p.action }}
                </button>
              </div>
            </div>
          </div>
          <div class="footnote" style="margin-top:10px">计划由盘点缺口直接推导 · 创建后进入培训排期 · <span class="src">处置建议非人工编造</span></div>
        </div>
      </section>

      <section class="panel-doc p-4 lg:col-span-2 self-start">
        <span class="watermark-num">03</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">03</span>
            <span class="section-name">派单登记</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">领办台账</span>
          </div>
          <div v-if="assigns.length">
            <div v-for="a in assigns" :key="a.skill" class="assign-row">
              <span class="assign-stamp">{{ a.initials }}</span>
              <div class="min-w-0">
                <div class="assign-title">{{ a.skill }} · {{ a.owner }}</div>
                <div class="assign-body">领办期限 {{ a.deadline }} · 目标 {{ a.target }} · {{ a.dept }}</div>
              </div>
            </div>
          </div>
          <div v-else class="doc-empty">
            <div class="lines"><i></i><i></i><i></i></div>
            "暂无领办登记 · 高优缺口待派单"
          </div>
          <div class="footnote" style="margin-top:10px">派单对象为技能负责人 · <span class="src">高优缺口自动进入派单队列</span></div>
        </div>
      </section>
    </div>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">盘点 · 技能评估 Agent　审批 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-03 · PAGE 08 / 08</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { TeamGap } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import CountUp from '@/components/enterprise/CountUp.vue'

const store = useEnterpriseStore()

// ── 读数 ──
const gaps = computed(() => [...store.teamGaps].sort((a, b) => b.gap - a.gap))
const highGapCount = computed(() => store.highPriorityGaps)
const affectedCount = computed(() => {
  const s = new Set<string>()
  gaps.value.forEach((g) => store.positions.slice(0, g.affectedPositions).forEach((p) => s.add(p.id)))
  return s.size
})
const avgGap = computed(() => (gaps.value.length ? Math.round(gaps.value.reduce((s, g) => s + g.gap, 0) / gaps.value.length) : 0))
const passRate = computed(() => gaps.value.filter((g) => g.currentAvg >= 80).length)

// ── 单元格渲染 ──
function levelLabel(l: string): string {
  const m: Record<string, string> = { basic: '入门', intermediate: '中级', advanced: '高级', expert: '专家' }
  return m[l] || l
}
function coveredNames(g: TeamGap): string[] {
  return store.positions.slice(0, g.affectedPositions).map((p) => p.name)
}
function gapCls(gap: number): string {
  return gap >= 60 ? 'coral' : gap >= 40 ? 'dim' : 'faded'
}
const prioMap: Record<string, { label: string; cls: string }> = {
  high: { label: '高优', cls: 'prio-chip--high' },
  medium: { label: '中优', cls: 'prio-chip--medium' },
  low: { label: '低优', cls: 'prio-chip--low' },
}
function prioLabel(p: string): string { return prioMap[p]?.label || p }
function prioCls(p: string): string { return prioMap[p]?.cls || 'prio-chip--low' }
const disposeMap: Record<string, string> = { high: '领办培训', medium: '补强计划', low: '招贤补位' }
function disposeFor(p: string): string { return disposeMap[p] || '补强' }

// ── 培训计划（由缺口推导）──
interface PlanItem { key: string; title: string; reason: string; scope: string; action: string; priority: string }
const planItems = computed<PlanItem[]>(() =>
  gaps.value.slice(0, 3).map((g) => ({
    key: g.skillName,
    title: `${g.skillName} ${disposeFor(g.priority)}`,
    reason: `团队当前覆盖 ${g.currentAvg}%，距离达标线 80% 尚差 ${Math.max(0, 80 - g.currentAvg)}pp；受缺口影响的岗位 ${g.affectedPositions} 个。`,
    scope: `${g.affectedPositions} 岗位 · 差距 ${g.gap}% · 要求 ${levelLabel(g.requiredLevel)}`,
    action: '创建计划 →',
    priority: g.priority,
  })),
)

// ── 派单登记（高优缺口自动入队）──
interface Assign { skill: string; owner: string; initials: string; deadline: string; target: string; dept: string }
const ASSIGNEES: Record<string, { owner: string; initials: string; dept: string }> = {
  'Kubernetes': { owner: '王磊', initials: 'WL', dept: '云平台组' },
  '联邦学习': { owner: '赵敏', initials: 'ZM', dept: '算法研究组' },
  'Terraform': { owner: '陈晨', initials: 'CC', dept: '基础设施组' },
  '性能优化': { owner: '刘洋', initials: 'LY', dept: '性能工程组' },
  '安全测试': { owner: '孙悦', initials: 'SY', dept: '质量安全组' },
}
const assigns = computed<Assign[]>(() =>
  gaps.value
    .filter((g) => g.priority === 'high' || g.priority === 'medium')
    .slice(0, 3)
    .map((g) => {
      const a = ASSIGNEES[g.skillName] || { owner: '待定', initials: '—', dept: '—' }
      return {
        skill: g.skillName,
        owner: a.owner,
        initials: a.initials,
        deadline: g.priority === 'high' ? '2026-08-30' : '2026-09-30',
        target: `覆盖 ≥ ${Math.min(100, g.currentAvg + 20)}%`,
        dept: a.dept,
      }
    }),
)

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
function dispose(g: TeamGap) {
  notify(`${disposeFor(g.priority)}已登记`, `${g.skillName} · 进入培训计划队列（差距 ${g.gap}%）`)
}
function createPlan(p: PlanItem) {
  notify('培训计划已创建', `${p.title} · 已排入 ${new Date().getFullYear()} 下半年培训日历`)
}
function generatePlans() {
  notify('培训计划已生成', `汇总 ${planItems.value.length} 项 · 覆盖 ${affectedCount.value} 岗位 · 估算 ${planItems.value.length * 8} 人·课时`)
}
function exportReport() {
  notify('盘点表已导出', `团队技能盘点 · 台账 ${gaps.value.length} 项 · PDF 已生成`)
}

onMounted(() => { store.fetchTeamGaps() })
</script>
