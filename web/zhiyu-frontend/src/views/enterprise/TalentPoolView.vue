<template>
  <div class="space-y-4">
    <!-- ═══ 报告头：人才档案总览 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">人才库 · 人才档案总览</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            TALENT POOL DOSSIER · {{ store.talentCandidates.length }} CANDIDATES · 独立候选人资产池
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-TAL-001 · 简历解析 + 岗位匹配沉淀</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="seal-chip" style="color:#fff;border-color:#fff">● 收藏 {{ store.favoriteCount }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">HR 专属标注</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="exportPool">导出人才台账</button>
      <button class="ent-btn ent-btn--ghost" @click="refresh">刷新数据</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">候选人来自用户档案 · 标注仅 HR 可见</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条：人才池读数 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.talentCandidates.length" /></div>
        <div class="stat-label">在库候选人</div>
        <div class="stat-sub">可检索档案</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num coral coral-glow"><CountUp :value="store.highMatchCount" /></div>
        <div class="stat-label">高匹配</div>
        <div class="stat-sub">匹配率 ≥ 85%</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.favoriteCount" /></div>
        <div class="stat-label">已收藏</div>
        <div class="stat-sub">重点跟进池</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="store.activeHrCount ? 'coral coral-glow' : ''"><CountUp :value="store.activeHrCount" /></div>
        <div class="stat-label">进行中</div>
        <div class="stat-sub">筛选 / 面试 / Offer</div>
      </div>
    </div>

    <!-- ═══ 筛选工具条 ═══ -->
    <section class="panel-doc p-3 space-y-2">
      <div class="flex flex-wrap items-center gap-2">
        <input v-model="keyword" class="ent-input" placeholder="检索姓名 / 岗位 / 目标方向 / 技能…" />
        <span class="flex-1"></span>
        <span class="footnote" style="margin:0">共 <span class="src">{{ filtered.length }}</span> / {{ store.talentCandidates.length }} 条</span>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span class="footnote" style="margin:0">方向</span>
        <button
          v-for="d in directionOptions"
          :key="d"
          class="ent-chip"
          :class="{ 'ent-chip--active': directionFilter === d }"
          @click="directionFilter = directionFilter === d ? '' : d"
        >{{ d }}</button>
        <span class="footnote" style="margin:0;margin-left:8px">城市</span>
        <button
          v-for="c in cityOptions"
          :key="c"
          class="ent-chip"
          :class="{ 'ent-chip--active': cityFilter === c }"
          @click="cityFilter = cityFilter === c ? '' : c"
        >{{ c }}</button>
        <span class="footnote" style="margin:0;margin-left:8px">HR 状态</span>
        <button
          v-for="h in hrStatusOptions"
          :key="h.value"
          class="ent-chip"
          :class="{ 'ent-chip--active': hrStatusFilter === h.value }"
          @click="hrStatusFilter = hrStatusFilter === h.value ? 'all' : h.value"
        >{{ h.label }}</button>
      </div>
    </section>

    <!-- ═══ 01 人才台账 ═══ -->
    <section class="panel-doc p-4">
      <span class="watermark-num">01</span>
      <div class="relative z-[1]">
        <div class="section-head">
          <span class="section-num">01</span>
          <span class="section-name">人才台账</span>
          <span class="section-rule"></span>
          <span class="footnote" style="margin:0">按最高匹配降序 · 点击行查看档案 · 状态印章可盖章推进</span>
        </div>
        <div class="tbl-head--talent">
          <span>姓名岗位</span>
          <span>目标方向</span>
          <span>城市经验</span>
          <span style="text-align:right">期望薪资</span>
          <span>核心技能</span>
          <span style="text-align:right">最高匹配</span>
          <span>HR 状态</span>
          <span style="text-align:right">操作</span>
        </div>
        <div>
          <div
            v-for="c in filtered"
            :key="c.id"
            class="tbl-row--talent"
            @click="open(c)"
          >
            <div class="min-w-0">
              <div class="t-name">{{ c.name }}</div>
              <div class="t-sub" :title="c.title">{{ c.title }}</div>
            </div>
            <span class="t-dir">{{ c.targetRole }}</span>
            <div class="min-w-0">
              <div class="t-sub" style="color:var(--ent-ink)">{{ c.city }}</div>
              <div class="t-sub">{{ c.experienceYears }} · {{ c.education }}</div>
            </div>
            <span class="t-sal">{{ c.salaryMin }}-{{ c.salaryMax }}K</span>
            <div class="t-skills">
              <span v-for="s in c.topSkills" :key="s" class="skill-tag">{{ s }}</span>
            </div>
            <span class="t-match" :class="{ coral: c.bestMatchRate >= 85 }">
              <CountUp :value="c.bestMatchRate" />
            </span>
            <div class="t-seal">
              <SealChip
                :status="c.hrStatus"
                :style="{ cursor: 'pointer' }"
                :title="'点击盖章推进 → ' + nextLabel(c.hrStatus)"
                @click.stop="cycleStatus(c)"
              />
            </div>
            <div class="t-ops" @click.stop>
              <button
                class="fav-btn"
                :class="{ faved: c.favorite }"
                :title="c.favorite ? '取消收藏' : '收藏'"
                @click="toggleFavorite(c)"
              >{{ c.favorite ? '★' : '☆' }}</button>
              <button class="open-btn" @click="open(c)">→</button>
            </div>
          </div>
        </div>
        <div v-if="!filtered.length" class="doc-empty" style="margin-top:14px">
          <div class="lines"><i></i><i></i><i></i></div>
          "暂无匹配候选人 · NO CANDIDATES"
        </div>
        <div class="footnote" style="margin-top:10px">最高匹配为候选人岗位匹配记录 Top1 · 状态印章在未标注→已筛选→面试中→已Offer→已归档间循环 · <span class="src">标注落库 talent_pool_entries · 不修改候选人公开档案</span></div>
      </div>
    </section>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">人才盘点 · 简历解析 Agent　审批 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-30 · PAGE 09 / 09</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { TalentCandidate, HrStatus } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import CountUp from '@/components/enterprise/CountUp.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import { downloadCsv, today } from '@/utils/export'

const store = useEnterpriseStore()
const router = useRouter()

// ── 筛选状态 ──
const keyword = ref('')
const directionFilter = ref('')
const cityFilter = ref('')
const hrStatusFilter = ref<'all' | HrStatus>('all')

const HR_STATUS_LABELS: Record<string, string> = {
  '': '未标注', shortlisted: '已筛选', interviewing: '面试中', offered: '已Offer', archived: '已归档',
}
const HR_STATUS_OPTIONS: { value: 'all' | HrStatus; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: '', label: '未标注' },
  { value: 'shortlisted', label: '已筛选' },
  { value: 'interviewing', label: '面试中' },
  { value: 'offered', label: '已Offer' },
  { value: 'archived', label: '已归档' },
]
const hrStatusOptions = HR_STATUS_OPTIONS
const directionOptions = computed(() => Array.from(new Set(store.talentCandidates.map(c => c.targetRole))).filter(Boolean))
const cityOptions = computed(() => Array.from(new Set(store.talentCandidates.map(c => c.city))).filter(Boolean))

const filtered = computed<TalentCandidate[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  return [...store.talentCandidates]
    .filter((c) => {
      if (kw) {
        const hay = [c.name, c.title, c.targetRole, c.city, ...c.topSkills].join(' ').toLowerCase()
        if (!hay.includes(kw)) return false
      }
      if (directionFilter.value && c.targetRole !== directionFilter.value) return false
      if (cityFilter.value && c.city !== cityFilter.value) return false
      if (hrStatusFilter.value !== 'all' && c.hrStatus !== hrStatusFilter.value) return false
      return true
    })
    .sort((a, b) => b.bestMatchRate - a.bestMatchRate)
})

// ── 盖章推进 ──
const HR_CYCLE: HrStatus[] = ['', 'shortlisted', 'interviewing', 'offered', 'archived']
function nextStatus(s: HrStatus): HrStatus {
  return HR_CYCLE[(HR_CYCLE.indexOf(s) + 1) % HR_CYCLE.length]
}
function nextLabel(s: HrStatus): string {
  return HR_STATUS_LABELS[nextStatus(s)]
}
function cycleStatus(c: TalentCandidate) {
  const next = nextStatus(c.hrStatus)
  store.updateTalentAnnotation(c.id, { hrStatus: next }).then(() => {
    notify('状态已盖章', `${c.name} → ${HR_STATUS_LABELS[next]}（已写入人才库标注）`)
  })
}
function toggleFavorite(c: TalentCandidate) {
  const next = !c.favorite
  store.updateTalentAnnotation(c.id, { favorite: next }).then(() => {
    notify(next ? '已收藏' : '已取消收藏', `${c.name} · ${next ? '进入重点跟进池' : '移出重点跟进池'}`)
  })
}

// ── 跳转 / 操作 ──
function open(c: TalentCandidate) {
  router.push('/enterprise/talent-pool/' + c.id)
}
function refresh() {
  store.fetchTalentPool()
  notify('已刷新', `人才库 ${store.talentCandidates.length} 名候选人已从服务端同步`)
}
function exportPool() {
  const headers = ['姓名', '现任岗位', '目标方向', '城市', '经验', '学历', '期望薪资', '核心技能', '最高匹配', 'HR状态', '收藏']
  const rows: unknown[][] = filtered.value.map((c) => [
    c.name, c.title, c.targetRole, c.city, c.experienceYears, c.education,
    `${c.salaryMin}-${c.salaryMax}K`, c.topSkills.join('、'), `${c.bestMatchRate}%`,
    HR_STATUS_LABELS[c.hrStatus] || '未标注', c.favorite ? '★' : '—',
  ])
  downloadCsv(`人才台账_${today()}.csv`, headers, rows)
  notify('人才台账已导出', `人才库 · 台账 ${filtered.value.length} 条 · CSV 已下载`)
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

onMounted(() => { store.fetchTalentPool() })
</script>
