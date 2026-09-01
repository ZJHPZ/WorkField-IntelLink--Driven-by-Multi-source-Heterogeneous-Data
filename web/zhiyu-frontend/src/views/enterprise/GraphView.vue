<template>
  <div class="graph-shell">
    <!-- ═══ HUD 指挥条 ═══ -->
    <header class="graph-hud">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="graph-hud-title">图谱蓝图 · 岗位-技能全景</h1>
          <p class="graph-hud-sub">GRAPH BLUEPRINT · {{ posCount }} POS · {{ skillCount }} SKILLS · {{ linkCount }} LINKS</p>
          <span class="doc-meta inline-block mt-1.5">ZYZL-ENT-GRAPH-01 · 快照 {{ store.snapshot.version }} · {{ store.snapshot.timestamp }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="hotCount" class="seal-chip" style="color:#fff;border-color:#fff">● 高热 {{ hotCount }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">力导布局 · 可拖拽</span>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2 mt-3">
        <div class="hud-chip-group">
          <button
            v-for="v in viewModes"
            :key="v.key"
            class="hud-chip"
            :class="{ 'hud-chip--on': view === v.key }"
            @click="view = v.key"
          >{{ v.label }}</button>
        </div>
        <span class="flex-1"></span>
        <input
          v-model="query"
          class="hud-search"
          type="text"
          placeholder="SEARCH SKILL · 检索技能"
        />
        <button class="hud-btn" @click="snapshotOpen = true">快照对比</button>
        <button class="hud-btn hud-btn--coral" @click="exportGraph">导出蓝图</button>
      </div>
    </header>

    <!-- ═══ 画布区 ═══ -->
    <div class="flex-1 relative min-h-0">
      <div class="absolute inset-0">
        <template v-if="store.graphNodes.length">
          <GraphCanvas
            :nodes="store.graphNodes"
            :links="store.graphLinks"
            :view="view"
            :hidden-rels="hiddenRels"
            :query="query"
            @node-click="selectNode"
          />
        </template>
        <div v-else class="doc-empty" style="padding-top:80px">
          <div class="lines"><i></i><i></i><i></i></div>
          "图谱数据为空 · 等待数据接入"
        </div>
      </div>

      <!-- 边过滤（左下） -->
      <div class="graph-overlay" style="left:12px;bottom:12px">
        <div class="graph-overlay-title">边过滤 · REL FILTER</div>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="r in relGroups"
            :key="r.key"
            class="graph-chip"
            :class="isRelOn(r.key) ? 'graph-chip--on' : ''"
            @click="toggleRel(r.key)"
          >{{ r.label }}</button>
        </div>
      </div>

      <!-- 图例（右下） -->
      <div class="graph-overlay" style="right:12px;bottom:12px">
        <div class="graph-overlay-title">图例 · LEGEND</div>
        <div class="space-y-1.5">
          <div class="graph-legend-item"><span class="graph-swatch graph-swatch--pos"></span>岗位节点</div>
          <div class="graph-legend-item"><span class="graph-swatch graph-swatch--skill"></span>技能节点</div>
          <div class="graph-legend-item"><span class="graph-swatch graph-swatch--stack"></span>技术栈</div>
          <div class="graph-legend-item"><span class="graph-swatch graph-swatch--ev"></span>证据</div>
          <div class="graph-legend-item" style="margin-top:2px"><span class="graph-line--req" style="width:18px;height:2px"></span>必备要求</div>
          <div class="graph-legend-item"><span class="graph-line--co" style="width:18px"></span>共现强度</div>
        </div>
      </div>

      <!-- 档案侧栏 -->
      <aside class="graph-inspect" :class="{ 'graph-inspect--open': !!selected }">
        <template v-if="selected">
          <div class="inspect-head">
            <div class="flex items-center gap-2">
              <span class="flex-1 min-w-0">
                <div class="section-name" style="white-space:normal;line-height:1.4">{{ selected.name }}</div>
                <div class="graph-overlay-title" style="margin:2px 0 0">档案 · DOSSIER · {{ kindLabel(selected.kind) }}</div>
              </span>
              <button class="ent-btn ent-btn--ghost" style="flex:none;padding:2px 8px;font-size:9px" @click="closeInspect">关闭</button>
            </div>
          </div>

          <div class="p-3 space-y-3">
            <!-- 技能档案 -->
            <template v-if="selected.kind === 'skill'">
              <div class="flex items-center gap-2">
                <span class="seal-chip" :class="verSealCls(selected)">{{ verLabel(selected) }}</span>
                <span v-if="selected._stack" class="diag-tag">{{ selected._stack }}</span>
                <span v-if="(selected._metrics?.emergence ?? 0) >= 0.7" class="sk-change sk-change--added" style="margin:0">高热</span>
              </div>
              <div class="review-head pro">指标 · METRICS <span class="flex-1"></span><span class="review-count">×6</span></div>
              <div class="leader-row"><span class="label">文档频率 df</span><span class="dots"></span><span class="val">{{ pct(selected._metrics?.df) }}</span></div>
              <div class="leader-row"><span class="label">置信度</span><span class="dots"></span><span class="val" :class="confCls(selected)">{{ pct(selected._metrics?.confidence) }}</span></div>
              <div class="leader-row"><span class="label">新兴度</span><span class="dots"></span><span class="val coral">{{ pct(selected._metrics?.emergence) }}</span></div>
              <div class="leader-row"><span class="label">衰退度</span><span class="dots"></span><span class="val faded-ink">{{ pct(selected._metrics?.decline) }}</span></div>
              <div class="leader-row"><span class="label">半衰期</span><span class="dots"></span><span class="val">{{ selected._metrics?.halfLife ?? '—' }} 月</span></div>
              <div class="leader-row"><span class="label">波动率</span><span class="dots"></span><span class="val">{{ pct(selected._metrics?.volatility) }}</span></div>

              <div class="review-head pro">关联岗位 <span class="flex-1"></span><span class="review-count">×{{ relatedPositions.length }}</span></div>
              <div v-if="relatedPositions.length">
                <button
                  v-for="p in relatedPositions"
                  :key="p.id"
                  class="ent-link block w-full text-left mt-1"
                  style="font-size:11px"
                  @click="goToPosition(p.id)"
                >↳ {{ p.name }} <span class="footnote" style="margin:0">· {{ p.level }} · {{ p.department }}</span></button>
              </div>

              <div class="review-head pro">关联技能 · 共现 <span class="flex-1"></span><span class="review-count">×{{ relatedSkills.length }}</span></div>
              <div v-if="relatedSkills.length" class="flex flex-wrap gap-1.5 mt-1">
                <span v-for="s in relatedSkills" :key="s.name" class="diag-tag">{{ s.name }} · {{ pct(s.strength) }}</span>
              </div>

              <div class="review-head pro">证据链 · EVIDENCE <span class="flex-1"></span><span class="review-count">×{{ evidenceList.length }}</span></div>
              <div v-if="evidenceList.length">
                <div v-for="(ev, i) in evidenceList" :key="i" class="ev-row">
                  <div class="ev-text">“{{ ev.text }}”</div>
                  <div class="ev-src">来源 · <b>{{ ev.source }}</b>　时间 · {{ ev.timestamp }}</div>
                </div>
              </div>
              <div v-else class="doc-empty" style="padding:10px 0">
                <div class="lines" style="max-width:150px"><i></i><i></i><i></i></div>
                "暂无证据接入"
              </div>

              <div class="flex gap-2 mt-2">
                <button class="ent-btn ent-btn--coral" style="flex:1" @click="adoptSkill">加入标准库</button>
              </div>
            </template>

            <!-- 岗位档案 -->
            <template v-else-if="selected.kind === 'position'">
              <div class="flex items-center gap-2">
                <span class="seal-chip" :class="selected._posType === '新兴' ? '' : 'seal-chip--navy'">{{ selected._posType }}</span>
                <span v-if="selected._level" class="diag-tag">{{ selected._level }}</span>
              </div>
              <div class="review-head pro">岗位指标 <span class="flex-1"></span><span class="review-count">×3</span></div>
              <div class="leader-row"><span class="label">等级</span><span class="dots"></span><span class="val">{{ selected._level || '—' }}</span></div>
              <div class="leader-row"><span class="label">市场需求</span><span class="dots"></span><span class="val coral">{{ pct(selected._metrics?.marketDemand) }}</span></div>
              <div class="leader-row"><span class="label">团队匹配</span><span class="dots"></span><span class="val">{{ pct(selected._metrics?.matchRate) }}</span></div>

              <div class="review-head pro">必备技能 <span class="flex-1"></span><span class="review-count">×{{ requiredSkills.length }}</span></div>
              <div>
                <div v-for="s in requiredSkills" :key="s.name" class="doc-skill">
                  <div class="sk-head">
                    <span class="sk-name" :title="s.name">{{ s.name }}</span>
                    <span class="sk-level">{{ levelLabel(s.level) }}</span>
                    <span class="flex-1"></span>
                    <span class="sk-wt">{{ Math.round(s.weight * 100) }}%</span>
                  </div>
                  <div class="ink-bar mt-1"><i :style="{ width: Math.round(s.weight * 100) + '%' }"></i></div>
                </div>
              </div>

              <div class="flex gap-2 mt-2">
                <button class="ent-btn ent-btn--coral" style="flex:1" @click="goToPosition(posIdFromNode)">查看岗位详情 →</button>
              </div>
            </template>

            <!-- 技术栈档案 -->
            <template v-else-if="selected.kind === 'stack'">
              <div class="review-head pro">技术栈 · {{ selected.name }} <span class="flex-1"></span><span class="review-count">×{{ stackMembers.length }}</span></div>
              <div v-if="stackMembers.length">
                <button
                  v-for="s in stackMembers"
                  :key="s.id"
                  class="ent-link block w-full text-left mt-1"
                  style="font-size:11px"
                  @click="selectNode(s)"
                >↳ {{ s.name }} <span class="footnote" style="margin:0">· 新兴度 {{ pct(s._metrics?.emergence) }}</span></button>
              </div>
              <div v-else class="doc-empty" style="padding:10px 0">
                <div class="lines" style="max-width:150px"><i></i><i></i><i></i></div>
                "暂无成员技能"
              </div>
            </template>
          </div>
        </template>
      </aside>

      <!-- 快照对比模态 -->
      <div v-if="snapshotOpen" class="graph-modal">
        <section class="panel-doc p-4">
          <div class="section-head">
            <span class="section-num">Δ</span>
            <span class="section-name">快照对比</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">V13 → {{ store.snapshot.version }}</span>
            <button class="ent-btn ent-btn--ghost" style="flex:none;padding:2px 8px;font-size:9px" @click="snapshotOpen = false">关闭</button>
          </div>
          <div class="leader-row"><span class="label">新增技能</span><span class="dots"></span><span class="val coral">{{ diff.added_skills.length }}</span></div>
          <div class="leader-row"><span class="label">删除技能</span><span class="dots"></span><span class="val faded-ink">{{ diff.removed_skills.length }}</span></div>
          <div class="leader-row"><span class="label">修改技能</span><span class="dots"></span><span class="val">{{ diff.modified_skills.length }}</span></div>
          <div class="leader-row"><span class="label">新增关系</span><span class="dots"></span><span class="val">{{ diff.added_relations.length }}</span></div>
          <div class="mt-3 p-3" style="background:rgba(0,9,76,0.02);border:1px dashed var(--ent-rule)">
            <div class="prop-label">变更明细</div>
            <div class="flex flex-wrap gap-1.5 mt-2">
              <span v-for="s in diff.added_skills" :key="s" class="diag-tag diag-tag--miss">+ {{ s }}</span>
            </div>
            <div class="flex flex-wrap gap-1.5 mt-2">
              <span v-for="s in diff.removed_skills" :key="s" class="diag-tag" style="color:var(--ent-dim);text-decoration:line-through">− {{ s }}</span>
            </div>
            <div class="mt-2">
              <div v-for="m in diff.modified_skills" :key="m.name" class="sk-reason">↳ {{ m.name }} 置信度 {{ pct(m.old_confidence) }} → <b style="color:var(--ent-coral)">{{ pct(m.new_confidence) }}</b></div>
            </div>
          </div>
          <div class="rec-box mt-3" style="padding:10px 12px">
            <span class="rec-stamp" style="width:30px;height:30px;font-size:12px">Δ</span>
            <div class="dossier-body" style="margin:0;flex:1">{{ diff.summary }}</div>
          </div>
          <div class="footnote" style="margin-top:10px">快照由 L4 管道按月生成 · <span class="src">skill_cooccurrence 网络密度 +18%</span></div>
        </section>
      </div>
    </div>

    <!-- ═══ 底栏 ═══ -->
    <footer class="graph-statusbar">
      <span class="dot" :class="store.graphSource === 'mysql' ? 'dot--live' : 'dot--ok'"></span>
      <span>节点 {{ store.graphNodes.length }} · 边 {{ store.graphLinks.length }}</span>
      <span class="graph-line--req" style="width:12px;height:2px;display:inline-block"></span>
      <span>数据源 · {{ store.graphSource === 'mysql' ? 'MYSQL 快照' : 'DEMO 推演' }}</span>
      <span class="flex-1"></span>
      <span>快照 {{ store.snapshot.version }} · {{ store.snapshot.description }}</span>
      <span>GRAPH-BLUEPRINT · PAGE 10/10</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { ChartNode } from '@/utils/graph'
import GraphCanvas from '@/components/enterprise/GraphCanvas.vue'
import { downloadCsv, today } from '@/utils/export'

const router = useRouter()
const store = useEnterpriseStore()

const viewModes = [
  { key: 'techstack', label: '技术栈' },
  { key: 'level', label: '级别' },
  { key: 'heat', label: '热度' },
] as const
const view = ref<'techstack' | 'level' | 'heat'>('techstack')
const query = ref('')

// ── 读数 ──
const posCount = computed(() => store.graphNodes.filter((n) => n.kind === 'position').length)
const skillCount = computed(() => store.graphNodes.filter((n) => n.kind === 'skill').length)
const linkCount = computed(() => store.graphLinks.length)
const hotCount = computed(() => store.graphNodes.filter((n) => n.kind === 'skill' && (n._metrics?.emergence ?? 0) >= 0.7).length)

// ── 边过滤 ──
const relGroups = [
  { key: 'REQUIRES', label: '岗位↔技能' },
  { key: 'CO_OCCURS', label: '共现' },
  { key: 'BELONGS_TO', label: '归属' },
  { key: 'SUPPORTED_BY', label: '证据' },
  { key: 'IN_STACK', label: '入栈' },
]
const hiddenRels = ref<string[]>(['BELONGS_TO', 'SUPPORTED_BY', 'IN_STACK'])
function isRelOn(key: string): boolean { return !hiddenRels.value.includes(key) }
function toggleRel(key: string) {
  hiddenRels.value = hiddenRels.value.includes(key)
    ? hiddenRels.value.filter((r) => r !== key)
    : [...hiddenRels.value, key]
}

// ── 档案侧栏 ──
const selected = ref<ChartNode | null>(null)
function selectNode(node: ChartNode) { selected.value = node }
function closeInspect() { selected.value = null }

function kindLabel(k: string): string {
  return { position: '岗位', skill: '技能', stack: '技术栈', evidence: '证据' }[k] || k
}
function verLabel(n: ChartNode): string {
  return n._verification === 'confirmed' ? '已验证' : n._verification === 'rejected' ? '已驳回' : '待核验'
}
function verSealCls(n: ChartNode): string {
  return n._verification === 'confirmed' ? 'seal-chip--navy' : n._verification === 'rejected' ? 'seal-chip--faded' : ''
}
function confCls(n: ChartNode): string {
  const c = n._metrics?.confidence ?? 0
  return c >= 0.85 ? '' : c >= 0.6 ? 'coral' : 'faded-ink'
}
function pct(v: any): string {
  return v === undefined || v === null ? '—' : Math.round(Number(v) * 100) + '%'
}

// 技能档案数据
const relatedPositions = computed(() => {
  if (selected.value?.kind !== 'skill') return []
  return store.positions.filter((p) => p.skills.some((s) => s.name === selected.value!.name))
})
const relatedSkills = computed(() => {
  const n = selected.value
  if (!n || n.kind !== 'skill') return []
  return store.graphLinks
    .filter((l) => l.rel === 'CO_OCCURS' && (l.source === n.id || l.target === n.id))
    .map((l) => {
      const otherId = l.source === n.id ? l.target : l.source
      const other = store.graphNodes.find((x) => x.id === otherId)
      return { name: other?.name || otherId, strength: l._strength }
    })
    .filter((s) => s.name !== n.name)
})
const evidenceList = computed(() => selected.value?._evidence || [])

// 岗位档案数据
const posIdFromNode = computed(() => (selected.value?.id || '').replace('pos::', ''))
const requiredSkills = computed(() => {
  if (selected.value?.kind !== 'position') return []
  const p = store.positions.find((x) => x.id === posIdFromNode.value)
  return p ? [...p.skills].sort((a, b) => b.weight - a.weight) : []
})

// 技术栈档案数据
const stackMembers = computed(() => {
  if (selected.value?.kind !== 'stack') return []
  return store.graphNodes.filter((n) => n.kind === 'skill' && n._stack === selected.value!.name)
})

// ── 快照对比 ──
const snapshotOpen = ref(false)
const diff = computed(() => store.snapshotDiff)

// ── 操作 ──
function goToPosition(id: string) { router.push(`/enterprise/positions/${id}`) }
function levelLabel(l: string): string {
  const m: Record<string, string> = { basic: '入门', intermediate: '中级', advanced: '高级', expert: '专家' }
  return m[l] || l
}
function adoptSkill() { notify('已加入标准库', `${selected.value?.name} · 进入岗位标准修订草稿（待审批）`) }
function exportGraph() {
  const headers = ['节点类型', '名称', '技术栈', '验证状态', '文档频率', '置信度', '新兴度', '衰退度', '半衰期(月)', '波动率']
  const rows: unknown[][] = store.graphNodes.map((n) => [
    kindLabel(n.kind),
    n.name,
    n._stack || '—',
    n.kind === 'skill' ? verLabel(n) : '—',
    pct(n._metrics?.df),
    pct(n._metrics?.confidence),
    pct(n._metrics?.emergence),
    pct(n._metrics?.decline),
    n._metrics?.halfLife ?? '—',
    pct(n._metrics?.volatility),
  ])
  downloadCsv(`图谱蓝图_${today()}.csv`, headers, rows)
  notify('蓝图已导出', `图谱蓝图 · ${store.graphNodes.length} 节点 · ${store.graphLinks.length} 边 · CSV 已下载`)
}

// ── 反馈 ──
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

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') { closeInspect(); snapshotOpen.value = false }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  store.fetchGraph()
  store.fetchSnapshotDiff()
})
onUnmounted(() => { window.removeEventListener('keydown', onKey) })
</script>

<style scoped>
/* HUD 内轻底芯片：navy 条上的白底黑字 / 激活=白底墨字 */
.hud-chip-group { display: flex; gap: 4px; }
.hud-chip {
  padding: 3px 12px;
  font-family: 'Courier New', monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}
.hud-chip:hover { border-color: rgba(255, 255, 255, 0.55); color: #fff; }
.hud-chip--on { color: var(--ent-navy); background: #fff; border-color: #fff; }
.hud-search {
  width: 180px;
  padding: 3px 10px;
  font-family: 'Courier New', monospace;
  font-size: 10px;
  letter-spacing: 0.04em;
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.28);
  outline: none;
}
.hud-search::placeholder { color: rgba(255, 255, 255, 0.4); }
.hud-search:focus { border-color: rgba(255, 255, 255, 0.6); }
.hud-btn {
  padding: 3px 12px;
  font-family: 'Courier New', monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.32);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}
.hud-btn:hover { border-color: rgba(255, 255, 255, 0.6); color: #fff; }
.hud-btn--coral { color: #fff; background: var(--ent-coral); border-color: var(--ent-coral); }
.hud-btn--coral:hover { box-shadow: 0 0 10px rgba(200, 92, 86, 0.4); }
</style>
