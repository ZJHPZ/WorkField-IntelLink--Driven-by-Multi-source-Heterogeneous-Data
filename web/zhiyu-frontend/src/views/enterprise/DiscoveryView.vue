<template>
  <div class="space-y-4">
    <!-- ═══ 文件抬头 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">新岗位评审纪要</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            NEW ROLE PROPOSAL REVIEW · SESSION 2026.08 · {{ store.candidates.length }} PROPOSALS
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-DIS-001</span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="pendingCount > 0" class="seal-chip" style="color:#fff;border-color:#fff">● 评审中 {{ pendingCount }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">REV 2026.08</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="startScan">发起市场扫描</button>
      <button class="ent-btn ent-btn--ghost" @click="viewHistory">查看扫描历史</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">最近扫描 · 2026-08-02 · 352 条 JD</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条：评审进度读数 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num" :class="pendingCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="pendingCount" /></div>
        <div class="stat-label">待评审</div>
        <div class="stat-sub">需盖章裁决</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="confirmedCount" /></div>
        <div class="stat-label">已立项</div>
        <div class="stat-sub">纳入标准库</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="rejectedCount" /></div>
        <div class="stat-label">已驳回</div>
        <div class="stat-sub">归档备查</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="avgConfidence" /><span class="text-sm">%</span></div>
        <div class="stat-label">平均置信度</div>
        <div class="stat-sub">Discovery × Judge</div>
      </div>
    </div>

    <!-- ═══ 主从式：评审目录 + 评审详情 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <!-- 01 评审目录 -->
      <section class="panel-doc p-4 lg:col-span-2 self-start">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">评审目录</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">{{ store.candidates.length }} 件</span>
          </div>
          <div>
            <button
              v-for="(c, idx) in store.candidates"
              :key="c.id"
              class="prop-row"
              :class="{ 'prop-row--active': selected?.id === c.id }"
              @click="selected = c"
            >
              <span class="prop-file-no">{{ 'DIS-2026-' + String(idx + 1).padStart(2, '0') }}</span>
              <span class="prop-row-title">{{ c.title }}</span>
              <span class="prop-row-conf" :class="confCls(c.confidence)">{{ c.confidence }}%</span>
              <SealChip :status="c.status" />
            </button>
          </div>
          <div class="footnote" style="margin-top:10px">数据来源：<span class="src">DiscoveryAgent 聚类 · Judge 反方审查</span></div>
        </div>
      </section>

      <!-- 02 评审详情 -->
      <section class="panel-doc p-4 lg:col-span-3">
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">02</span>
            <span class="section-name">评审详情</span>
            <span class="section-rule"></span>
            <span v-if="selected" class="prop-file-no">{{ caseNo }}</span>
          </div>

          <transition name="fade" mode="out-in">
            <div v-if="selected" :key="selected.id">
              <!-- 案卷头 -->
              <div class="flex flex-wrap items-center gap-2">
                <span class="card-title ent-title-serif" style="font-size:15px">{{ selected.title }}</span>
                <SealChip :status="selected.status" :key="selected.id + selected.status" />
              </div>
              <div class="card-meta mt-1">{{ selected.source }} · {{ selected.discoveredAt }} · 352 条 JD 聚类</div>

              <!-- 置信度 -->
              <div class="mt-3 p-3" style="background:rgba(0,9,76,0.02);border:1px dashed var(--ent-rule)">
                <div class="flex flex-wrap items-center gap-4">
                  <span class="prop-label">评审置信度</span>
                  <span class="prop-conf" :class="confCls(selected.confidence)"><CountUp :value="selected.confidence" />%</span>
                  <div class="ink-bar flex-1 min-w-[120px]" style="width:auto"><i :class="{ coral: confCls(selected.confidence) === 'coral' }" :style="{ width: selected.confidence + '%' }"></i></div>
                  <span class="footnote" style="margin:0">技能重叠 <span class="src">{{ selected.skillOverlap }}%</span> · 含反方审查</span>
                </div>
              </div>

              <!-- 评审意见 -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div class="review-col">
                  <div class="review-head pro">▲ 赞成意见 <span class="flex-1"></span><span class="review-count">×{{ selected.debatePoints.pro.length }}</span></div>
                  <div v-for="(a, i) in selected.debatePoints.pro" :key="'pro' + i" class="review-item">{{ a }}</div>
                </div>
                <div class="review-col">
                  <div class="review-head con">— 异议 <span class="flex-1"></span><span class="review-count">×{{ selected.debatePoints.con.length }}</span></div>
                  <div v-for="(a, i) in selected.debatePoints.con" :key="'con' + i" class="review-item review-item--con">{{ a }}</div>
                </div>
              </div>

              <!-- 裁决 -->
              <div v-if="selected.status === 'candidate'" class="prop-actions">
                <button class="ent-btn ent-btn--coral" @click="approve(selected)">批准立项</button>
                <button class="ent-btn ent-btn--ghost prop-reject" @click="reject(selected)">驳回提案</button>
                <span class="flex-1"></span>
                <span class="footnote" style="margin:0">裁决将记入岗位标准库演化记录</span>
              </div>
              <div v-else class="prop-decided-note">
                已裁决 · <span :style="{ color: selected.status === 'confirmed' ? 'var(--ent-coral)' : 'var(--ent-dim)' }">{{ selected.status === 'confirmed' ? '纳入岗位标准库，印章确认' : '归档备查，标准不进入生效清单' }}</span>
              </div>
            </div>

            <div v-else class="doc-empty">
              <div class="lines"><i></i><i></i><i></i></div>
              "从左侧目录选择提案 · NO SELECTION"
            </div>
          </transition>
        </div>
      </section>
    </div>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">裁决人 · 张明　复核 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-02 · PAGE 03 / 08</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { RoleCandidate } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import CountUp from '@/components/enterprise/CountUp.vue'

const store = useEnterpriseStore()

// ── 评审进度读数 ──
const pendingCount = computed(() => store.candidates.filter((c) => c.status === 'candidate').length)
const confirmedCount = computed(() => store.candidates.filter((c) => c.status === 'confirmed').length)
const rejectedCount = computed(() => store.candidates.filter((c) => c.status === 'rejected').length)
const avgConfidence = computed(() =>
  Math.round(store.candidates.reduce((s, c) => s + c.confidence, 0) / Math.max(store.candidates.length, 1))
)

function confCls(v: number): string {
  return v >= 85 ? 'navy' : v >= 60 ? 'coral' : 'faded'
}

// ── 主从选择 ──
const selected = ref<RoleCandidate | null>(null)
const caseNo = computed(() => {
  if (!selected.value) return ''
  const idx = store.candidates.findIndex((c) => c.id === selected.value?.id)
  return idx >= 0 ? 'DIS-2026-' + String(idx + 1).padStart(2, '0') : ''
})

// ── 裁决：盖章动作 ──
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

function approve(c: RoleCandidate) {
  store.setCandidateStatus(c.id, 'confirmed')
  notify('立项批准', `${c.title} 已盖章确认 · 标准将纳入岗位标准库`)
}
function reject(c: RoleCandidate) {
  store.setCandidateStatus(c.id, 'rejected')
  notify('提案驳回', `${c.title} 已驳回 · 归档备查`)
}
function startScan() {
  notify('市场扫描启动', '正在采集 352 条 JD · DiscoveryAgent 聚类分析中')
}
function viewHistory() {
  notify('扫描历史', 'SESSION 2026.07 → 发现 5 个候选 · 已立项 2 · 驳回 3')
}

onMounted(async () => {
  await store.fetchCandidates()
  if (!selected.value && store.candidates.length) selected.value = store.candidates[0]
})
</script>
