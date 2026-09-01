<template>
  <div class="space-y-4">
    <!-- ═══ 深蓝文件抬头 + 珊瑚印章 + 文件编号 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">岗位标准智能管理平台</h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            POSITION STANDARD RULES · REV 2026.08 · {{ store.positionCount }} POSITIONS
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · ZYZL-ENT-2026-083</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="seal-chip seal-chip--on-navy">● 现行生效</span>
          <span class="seal-chip seal-chip--on-navy--dim">REV 2026.08</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏：盖章式按钮（按压墨晕）═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="exportReport">导出周报</button>
      <button class="ent-btn ent-btn--ghost" @click="reVerify">重新核验数据</button>
      <span class="doc-meta doc-meta--muted">最近核验 · {{ lastVerified }}</span>
    </div>

    <!-- ═══ KPI 瓷砖：深蓝读数 + 珊瑚稀缺辉光 + 趋势 ═══ -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.positionCount" /><span class="trend">▲2</span></div>
        <div class="stat-label">管理岗位</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num coral coral-glow"><CountUp :value="store.candidateCount" /></div>
        <div class="stat-label">待验证新岗</div>
        <div class="stat-sub">▲ 需决策</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.avgMatchRate" /><span class="text-sm">%</span><span class="trend">▲3.2</span></div>
        <div class="stat-label">平均匹配率</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num" :class="store.warningCount > 0 ? 'coral coral-glow' : ''"><CountUp :value="store.warningCount" /></div>
        <div class="stat-label">市场预警</div>
        <div class="stat-sub" v-if="store.warningCount > 0">▲ 待处理</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.highPriorityGaps" /></div>
        <div class="stat-label">高优缺口</div>
        <div class="stat-sub">▲ 需跟进</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num stat-num--date">{{ reportDate.slice(5) }}</div>
        <div class="stat-label">数据更新</div>
        <div class="stat-sub">已同步</div>
      </div>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ 章节报表：双栏 ═══ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
      <!-- 01 岗位状态 -->
      <section class="panel-doc p-4 lg:col-span-3">
        <span class="watermark-num">01</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">岗位状态</span>
            <span class="section-rule"></span>
            <router-link to="/enterprise/positions" class="ent-link">全部 →</router-link>
          </div>
          <div class="table-head">
            <span class="col-name">岗位名称</span>
            <span class="flex-1"></span>
            <span>匹配率</span>
            <span class="col-status">状态</span>
          </div>
          <div>
            <router-link
              v-for="(pos, idx) in store.positions"
              :key="pos.id"
              :to="'/enterprise/positions/'+pos.id"
              class="leader-row leader-row--link"
            >
              <span class="label">{{ pos.name }}</span>
              <span class="dots"></span>
              <span class="val">{{ pos.matchRate }}%</span>
              <span class="ml-1 shrink-0"><SealChip :status="pos.status" :style="{ animationDelay: (idx * 0.07) + 's' }" /></span>
              <span class="arrow">→</span>
            </router-link>
          </div>
          <div class="footnote">数据来源：<span class="src">岗位标准库 v8 · 更新于 {{ reportDate }} 10:00</span></div>
        </div>
      </section>

      <!-- 右栏 -->
      <div class="lg:col-span-2 space-y-3">
        <!-- 02 新岗位发现 -->
        <section class="panel-doc p-4">
          <span class="watermark-num">02</span>
          <div class="relative z-[1]">
            <div class="section-head">
              <span class="section-num">02</span>
              <span class="section-name">新岗位发现</span>
              <span class="section-rule"></span>
            </div>
            <div class="table-head">
              <span class="col-name">候选岗位</span>
              <span class="flex-1"></span>
              <span>置信度</span>
              <span class="col-status">状态</span>
            </div>
            <div>
              <div v-for="(c, idx) in store.candidates" :key="c.id" class="leader-row">
                <span class="label">{{ c.title }}</span>
                <span class="dots"></span>
                <span class="val" :class="c.status === 'candidate' ? 'coral' : ''">{{ c.confidence }}%</span>
                <span class="ml-1 shrink-0"><SealChip :status="c.status" :style="{ animationDelay: (idx * 0.07) + 's' }" /></span>
              </div>
            </div>
            <div class="footnote">数据来源：<span class="src">DiscoveryAgent · 12 条 JD 聚类 · 置信度含反方审查</span></div>
          </div>
        </section>

        <!-- 03 JD 诊断 -->
        <section class="panel-doc p-4">
          <span class="watermark-num">03</span>
          <div class="relative z-[1]">
            <div class="section-head">
              <span class="section-num">03</span>
              <span class="section-name">JD 诊断</span>
              <span class="section-rule"></span>
            </div>
            <div class="table-head">
              <span class="col-name">目标岗位</span>
              <span class="flex-1"></span>
              <span>评分</span>
              <span class="col-status">状态</span>
            </div>
            <div>
              <div v-for="(d, idx) in store.diagnoses" :key="d.id" class="leader-row">
                <span class="label">{{ d.positionName }}</span>
                <span class="dots"></span>
                <span class="val" :class="d.status === 'warning' || d.status === 'critical' ? 'coral' : ''">{{ d.overallScore }}</span>
                <span class="ml-1 shrink-0"><SealChip :status="d.status" :style="{ animationDelay: (idx * 0.07) + 's' }" /></span>
              </div>
            </div>
            <div class="footnote">数据来源：<span class="src">JD 质量诊断 Agent · 通胀指数 / 泛化软技能 / 套话占比</span></div>
          </div>
        </section>
      </div>
    </div>

    <!-- ═══ 页脚：双线 + 签发栏 + 页码 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label">审核 · 张明　批准 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 {{ reportDate }} · PAGE 01</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import CountUp from '@/components/enterprise/CountUp.vue'
import { downloadCsv, today } from '@/utils/export'

const store = useEnterpriseStore()
const showNotification = ref(false)
const notifyMessage = ref('')
const notifyDetail = ref('')
const lastVerified = ref('10 分钟前')
const reportDate = '2026-08-03'
let notifyTimer = 0

function notify(msg: string, detail: string) {
  notifyMessage.value = msg
  notifyDetail.value = detail
  showNotification.value = true
  window.clearTimeout(notifyTimer)
  notifyTimer = window.setTimeout(() => { showNotification.value = false }, 6000)
}

function exportReport() {
  const headers = ['模块', '名称', '指标', '状态']
  const rows: unknown[][] = [
    ...store.positions.map((p) => ['岗位状态', p.name, `${p.matchRate}%`, p.status]),
    ...store.candidates.map((c) => ['新岗位发现', c.title, `${c.confidence}%`, c.status]),
    ...store.diagnoses.map((d) => ['JD 诊断', d.positionName, d.overallScore, d.status]),
  ]
  downloadCsv(`岗位标准周报_${today()}.csv`, headers, rows)
  notify('岗位标准周报已生成', `已下载 CSV · 岗位 ${store.positions.length} · 新岗 ${store.candidates.length} · 诊断 ${store.diagnoses.length}`)
}

async function reVerify() {
  notify('重新核验启动', '正在同步岗位标准 · JD 诊断 · 市场预警…')
  await Promise.all([store.fetchPositions(), store.fetchCandidates(), store.fetchDiagnoses(), store.fetchTeamGaps()])
  lastVerified.value = '刚刚'
  notify('核验完成', '全部数据源已同步至最新')
}

onMounted(async () => {
  await Promise.all([store.fetchPositions(), store.fetchCandidates(), store.fetchDiagnoses(), store.fetchTeamGaps()])
})
</script>
