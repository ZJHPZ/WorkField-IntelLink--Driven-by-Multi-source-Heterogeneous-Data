<template>
  <div class="space-y-4">
    <!-- ═══ 文件抬头：岗位标准目录 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">岗位标准库</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            POSITION STANDARD CATALOG · REV 2026.08 · {{ store.positions.length }} POSITIONS
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-POS-001</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="seal-chip" style="color:#fff;border-color:#fff">● 现行生效</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">REV 2026.08</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="addStandard">新增岗位标准</button>
      <button class="ent-btn ent-btn--ghost" @click="importJD">导入 JD 定义</button>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">最近更新 · 2026-08-03</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 摘要条：全库读数 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.positions.length" /></div>
        <div class="stat-label">岗位总数</div>
        <div class="stat-sub">已生效标准</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.confirmedCount" /></div>
        <div class="stat-label">已确认</div>
        <div class="stat-sub">权威定稿</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num coral coral-glow"><CountUp :value="highDemand" /></div>
        <div class="stat-label">高需求岗位</div>
        <div class="stat-sub">市场指数 ≥ 85</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="gapCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="gapCount" /></div>
        <div class="stat-label">缺口岗位</div>
        <div class="stat-sub">匹配率 &lt; 70 · 需补技能</div>
      </div>
    </div>

    <!-- ═══ 筛选工具条 ═══ -->
    <section class="panel-doc p-3 flex flex-wrap items-center gap-2">
      <input v-model="search" class="ent-input" placeholder="检索岗位 / 部门 / 技能…" />
      <button
        v-for="f in statusOptions"
        :key="f.value"
        class="ent-chip"
        :class="{ 'ent-chip--active': statusFilter === f.value }"
        @click="statusFilter = f.value"
      >{{ f.label }}</button>
      <span class="flex-1"></span>
      <span class="footnote" style="margin:0">共 <span class="src">{{ filtered.length }}</span> / {{ store.positions.length }} 条</span>
      <select v-model="sortKey" class="ent-input" style="width:auto;cursor:pointer">
        <option value="default">默认排序</option>
        <option value="demand">市场指数 ↓</option>
        <option value="match">匹配率 ↑</option>
        <option value="updated">最近更新</option>
      </select>
    </section>

    <!-- ═══ 岗位标准卡片 ═══ -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-3">
      <section
        v-for="(p, idx) in filtered"
        :key="p.id"
        class="panel-doc p-4 std-card"
      >
        <div class="relative z-[1] flex-1 flex flex-col">
          <!-- 卡头：岗位名 + 印章 + 元数据 -->
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <router-link :to="'/enterprise/positions/' + p.id" class="card-title">{{ p.name }}</router-link>
                <SealChip :status="p.status" :style="{ animationDelay: (idx * 0.04) + 's' }" />
              </div>
              <div class="card-meta">{{ p.department }} · {{ p.level }} · 更新 {{ p.lastUpdated }}</div>
            </div>
          </div>

          <!-- 技能标准：等级 + 权重墨条 + 趋势 + 保鲜度 -->
          <div class="skill-standard">
            <div v-for="s in p.skills" :key="s.name" class="skill-row">
              <span class="skill-name" :title="s.name">{{ s.name }}</span>
              <span class="skill-level">{{ levelLabels[s.level] }}</span>
              <i class="ink-bar"><i :style="{ width: (s.weight * 100) + '%' }"></i></i>
              <span class="skill-trend" :class="trendMap[s.trend].cls" :title="trendMap[s.trend].title">{{ trendMap[s.trend].icon }}</span>
              <span class="skill-fresh" :class="freshCls(s.freshness)" :title="'保鲜度 ' + s.freshness">{{ s.freshness }}</span>
            </div>
          </div>

          <!-- 底栏：市场/匹配 + 详情 -->
          <div class="card-foot">
            <span class="kpi">市场指数 <b :class="{ coral: p.marketDemand >= 85 }"><CountUp :value="p.marketDemand" /></b></span>
            <span class="kpi">团队匹配 <b :class="{ coral: p.matchRate < 70 }"><CountUp :value="p.matchRate" /></b></span>
            <span class="flex-1"></span>
            <router-link :to="'/enterprise/positions/' + p.id" class="ent-link">查看标准 →</router-link>
          </div>
        </div>
      </section>
    </div>

    <div v-if="!filtered.length" class="panel-doc p-4">
      <div class="doc-empty">
        <div class="lines"><i></i><i></i><i></i></div>
        "本库无匹配岗位 · NO ENTRIES"
      </div>
    </div>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">审核 · 张明　批准 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-03 · PAGE 02 / 08</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import CountUp from '@/components/enterprise/CountUp.vue'

const store = useEnterpriseStore()

// ── 检索 / 状态筛选 / 排序 ──
const search = ref('')
const statusFilter = ref<string>('all')
const sortKey = ref<'default' | 'demand' | 'match' | 'updated'>('default')

const statusOptions = [
  { value: 'all', label: '全部' },
  { value: 'confirmed', label: '已确认' },
  { value: 'emerging', label: '新兴' },
  { value: 'stable', label: '稳定' },
  { value: 'declining', label: '衰退' },
]

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  const arr = store.positions.filter((p) => {
    if (statusFilter.value !== 'all' && p.status !== statusFilter.value) return false
    if (q) {
      const haystack = `${p.name}${p.department}${p.skills.map((s) => s.name).join('')}`.toLowerCase()
      if (!haystack.includes(q)) return false
    }
    return true
  })
  if (sortKey.value === 'demand') return [...arr].sort((a, b) => b.marketDemand - a.marketDemand)
  if (sortKey.value === 'match') return [...arr].sort((a, b) => a.matchRate - b.matchRate)
  if (sortKey.value === 'updated') return [...arr].sort((a, b) => b.lastUpdated.localeCompare(a.lastUpdated))
  return arr
})

// ── 摘要读数 ──
const highDemand = computed(() => store.positions.filter((p) => p.marketDemand >= 85).length)
const gapCount = computed(() => store.positions.filter((p) => p.matchRate < 70).length)

// ── 技能标准展示映射 ──
const levelLabels: Record<string, string> = {
  basic: '基础', intermediate: '中级', advanced: '高级', expert: '专家',
}
const trendMap: Record<string, { icon: string; cls: string; title: string }> = {
  rising: { icon: '▲', cls: 't-rise', title: '需求上升' },
  stable: { icon: '●', cls: 't-keep', title: '需求平稳' },
  declining: { icon: '▼', cls: 't-fall', title: '需求下降' },
}
function freshCls(f: number): string {
  return f >= 80 ? 'f-hi' : f >= 60 ? 'f-mid' : 'f-low'
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

function addStandard() {
  notify('岗位标准新建入口', '完整表单将在 /enterprise/positions 详情页体系内开放')
}
function importJD() {
  notify('JD 导入通道就绪', '粘贴 JD 文本 → 技能解析 → 生成标准建议（后端 /api/enterprise/positions）')
}

onMounted(() => { store.fetchPositions() })
</script>
