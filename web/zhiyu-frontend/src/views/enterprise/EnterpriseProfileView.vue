<template>
  <div class="space-y-4">
    <!-- ═══ 报告头：企业档案 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">
            {{ profile.name || '企业资料' }} · 企业档案总览
          </h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            ENTERPRISE DOSSIER · {{ profile.shortName || '—' }} · {{ profile.industry || '—' }}
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · 档案编号 ZYZL-ENT-COR-001 · 当前登录企业</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="seal-chip" style="color:#fff;border-color:#fff">{{ profile.logoEmoji }} {{ profile.shortName || '企业' }}</span>
          <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">HR 可编辑档案</span>
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="save">盖章保存</button>
      <button class="ent-btn" @click="exportDossier">导出档案</button>
      <router-link to="/enterprise" class="ent-link">← 返回工作台</router-link>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">最近更新 {{ updatedLabel }} · 企业资料由 HR 维护</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <!-- ═══ KPI：派生自人才库 / 岗位标准（零额外 API）═══ -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.positions.length" /></div>
        <div class="stat-label">在库岗位</div>
        <div class="stat-sub">岗位标准在案</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.talentCandidates.length" /></div>
        <div class="stat-label">人才库规模</div>
        <div class="stat-sub">候选人资产池</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num coral coral-glow"><CountUp :value="store.highMatchCount" /></div>
        <div class="stat-label">高匹配人才</div>
        <div class="stat-sub">匹配 ≥85</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num"><CountUp :value="store.activeHrCount" /></div>
        <div class="stat-label">进行中流程</div>
        <div class="stat-sub">筛选 / 面试 / Offer</div>
      </div>
    </div>

    <!-- ═══ 01 企业基本信息 ═══ -->
    <section class="panel-doc p-4">
      <span class="watermark-num">01</span>
      <div class="relative z-[1]">
        <div class="section-head">
          <span class="section-num">01</span>
          <span class="section-name">企业基本信息</span>
          <span class="section-rule"></span>
          <span class="footnote" style="margin:0">企业标识 · 组织属性</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 mt-3">
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">企业名称</span>
            <input v-model="draft.name" class="ent-input w-full" placeholder="企业全称" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">简称</span>
            <input v-model="draft.shortName" class="ent-input w-full" placeholder="对外简称" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">所属行业</span>
            <input v-model="draft.industry" class="ent-input w-full" placeholder="人工智能 · 企业服务" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">总部城市</span>
            <input v-model="draft.city" class="ent-input w-full" placeholder="北京" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">成立年份</span>
            <input v-model.number="draft.foundedYear" type="number" class="ent-input w-full" placeholder="2015" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">统一社会信用代码</span>
            <input v-model="draft.uscc" class="ent-input w-full" placeholder="18 位代码" />
          </label>
          <label class="flex flex-col gap-1 md:col-span-2">
            <span class="footnote" style="margin:0">办公地址</span>
            <input v-model="draft.address" class="ent-input w-full" placeholder="办公地址" />
          </label>
          <label class="flex flex-col gap-1 md:col-span-2">
            <span class="footnote" style="margin:0">官网</span>
            <input v-model="draft.website" class="ent-input w-full" placeholder="https://" />
          </label>
          <label class="flex flex-col gap-1 md:col-span-2">
            <span class="footnote" style="margin:0">企业性质</span>
            <div class="flex flex-wrap gap-2">
              <button v-for="n in NATURES" :key="n" class="ent-chip" :class="{ 'ent-chip--active': draft.nature === n }" @click="draft.nature = n">{{ n }}</button>
            </div>
          </label>
          <label class="flex flex-col gap-1 md:col-span-2">
            <span class="footnote" style="margin:0">员工规模</span>
            <div class="flex flex-wrap gap-2">
              <button v-for="h in HEADCOUNTS" :key="h" class="ent-chip" :class="{ 'ent-chip--active': draft.headcount === h }" @click="draft.headcount = h">{{ h }}</button>
            </div>
          </label>
          <label class="flex flex-col gap-1 md:col-span-2">
            <span class="footnote" style="margin:0">融资阶段</span>
            <div class="flex flex-wrap gap-2">
              <button v-for="f in FINANCINGS" :key="f" class="ent-chip" :class="{ 'ent-chip--active': draft.financing === f }" @click="draft.financing = f">{{ f }}</button>
            </div>
          </label>
        </div>
      </div>
    </section>

    <!-- ═══ 02 业务与标签 ═══ -->
    <section class="panel-doc p-4">
      <span class="watermark-num">02</span>
      <div class="relative z-[1]">
        <div class="section-head">
          <span class="section-num">02</span>
          <span class="section-name">业务与标签</span>
          <span class="section-rule"></span>
          <span class="footnote" style="margin:0">企业简介 · 技术栈 · 雇主品牌</span>
        </div>
        <label class="flex flex-col gap-1 mt-3">
          <span class="footnote" style="margin:0">企业简介</span>
          <textarea v-model="draft.description" class="ent-input w-full" rows="3" placeholder="企业简介（对外展示 / 招聘页引用）…"></textarea>
        </label>
        <div v-for="g in CHIP_GROUPS" :key="g.key" class="mt-3">
          <div class="flex items-center gap-2">
            <span class="footnote" style="margin:0;color:var(--ent-coral)">{{ g.label }}</span>
            <button v-for="p in g.presets" :key="p" class="ent-chip" :class="{ 'ent-chip--active': draft[g.key].includes(p) }" @click="toggleItem(g.key, p)">{{ p }}</button>
            <input v-model="g.draft" class="ent-input w-full max-w-[160px]" :placeholder="g.addPlaceholder" @keydown.enter.prevent="addItem(g.key, g.draft)" />
            <button class="ent-btn" @click="addItem(g.key, g.draft)">追加</button>
          </div>
          <div class="mt-2 flex flex-wrap gap-2">
            <span v-for="v in draft[g.key]" :key="v" class="skill-tag" @click="toggleItem(g.key, v)">{{ v }} ✕</span>
            <span v-if="!draft[g.key].length" class="t-sub">— 暂无，点上方芯片或输入追加</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ 03 组织与招聘 ═══ -->
    <section class="panel-doc p-4">
      <span class="watermark-num">03</span>
      <div class="relative z-[1]">
        <div class="section-head">
          <span class="section-num">03</span>
          <span class="section-name">组织与招聘</span>
          <span class="section-rule"></span>
          <span class="footnote" style="margin:0">HR 联系窗口 · 招聘渠道</span>
        </div>
        <div class="mt-3">
          <div class="archive-row"><span>企业性质</span><b>{{ draft.nature || '—' }}</b></div>
          <div class="archive-row"><span>员工规模</span><b>{{ draft.headcount || '—' }}</b></div>
          <div class="archive-row"><span>融资阶段</span><b>{{ draft.financing || '—' }}</b></div>
          <div class="archive-row"><span>成立年份</span><b>{{ draft.foundedYear || '—' }}</b></div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 mt-3">
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">HR 联系人</span>
            <input v-model="draft.hrName" class="ent-input w-full" placeholder="姓名" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">招聘职位</span>
            <input v-model="draft.hrTitle" class="ent-input w-full" placeholder="招聘总监" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">联系电话</span>
            <input v-model="draft.hrPhone" class="ent-input w-full" placeholder="010-…" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="footnote" style="margin:0">联系邮箱</span>
            <input v-model="draft.hrEmail" class="ent-input w-full" placeholder="hr@…" />
          </label>
        </div>
        <div class="mt-3 flex items-center gap-2">
          <button class="ent-btn ent-btn--coral" @click="save">盖章保存</button>
          <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">上次更新 {{ updatedLabel }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">企业档案 · 企业资料模块　维护 · 云启智能 HR</div>
      </div>
      <div class="foot-label">数据截止 2026-08-30 · PAGE 10 / 10</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, watch, onMounted, ref } from 'vue'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { EnterpriseProfile } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import CountUp from '@/components/enterprise/CountUp.vue'
import { downloadCsv, today } from '@/utils/export'

const store = useEnterpriseStore()

const profile = computed(() => store.enterpriseProfile)
const updatedLabel = computed(() => (profile.value.updatedAt ? String(profile.value.updatedAt).slice(0, 16).replace('T', ' ') : '—'))

// ── 可编辑草稿：表单直接改 draft，盖章保存才写回 store ──
function snapshot(p: EnterpriseProfile): EnterpriseProfile {
  return JSON.parse(JSON.stringify(p)) as EnterpriseProfile
}
const draft = reactive<EnterpriseProfile>(snapshot(store.enterpriseProfile))

watch(() => store.enterpriseProfile, (v) => {
  const d = snapshot(v)
  Object.keys(d).forEach((k) => { (draft as any)[k] = (d as any)[k] })
}, { deep: true })

// ── 单选 preset ──
const NATURES = ['民营', '国企', '央企', '外资', '合资', '事业单位']
const HEADCOUNTS = ['50-200人', '200-500人', '500-999人', '1000-4999人', '5000人以上']
const FINANCINGS = ['未融资', '天使轮', 'A 轮', 'B 轮', 'C 轮', 'D 轮及以后', '已上市']

// ── 多选 chip 组（preset + 自定义追加）──
type ChipGroupKey = 'techStack' | 'tags' | 'hiringChannels'
const CHIP_GROUPS: { key: ChipGroupKey; label: string; presets: string[]; addPlaceholder: string; draft: string }[] = [
  { key: 'techStack', label: '技术栈', presets: ['Go', 'Java', 'Python', 'TypeScript', 'Kubernetes', 'RAG / LLM', '大数据', '微服务', 'React', 'Vue'], addPlaceholder: '自定义技术', draft: '' },
  { key: 'tags', label: '企业标签', presets: ['弹性工作', '六险一金', '扁平管理', '股票期权', '免费三餐', '年度体检', '双休'], addPlaceholder: '自定义标签', draft: '' },
  { key: 'hiringChannels', label: '招聘渠道', presets: ['BOSS 直聘', '猎聘', '智联招聘', '校招官网', '内推渠道', '猎头'], addPlaceholder: '自定义渠道', draft: '' },
]

function toggleItem(key: ChipGroupKey, item: string) {
  const list = draft[key]
  const i = list.indexOf(item)
  if (i >= 0) list.splice(i, 1)
  else list.push(item)
}
function addItem(key: ChipGroupKey, input: string) {
  const v = (input || '').trim()
  if (v && !draft[key].includes(v)) draft[key].push(v)
  const g = CHIP_GROUPS.find((x) => x.key === key)
  if (g) g.draft = ''
}

// ── 保存 / 导出 ──
async function save() {
  await store.updateEnterpriseProfile(snapshot(draft))
  notify('企业资料已更新', `${profile.value.shortName || profile.value.name} · 档案已盖章保存`)
}
function exportDossier() {
  const p = profile.value
  const headers = ['项目', '内容']
  const rows: unknown[][] = [
    ['企业名称', p.name], ['简称', p.shortName], ['所属行业', p.industry],
    ['总部城市', p.city], ['成立年份', p.foundedYear], ['统一社会信用代码', p.uscc],
    ['办公地址', p.address], ['官网', p.website], ['企业性质', p.nature],
    ['员工规模', p.headcount], ['融资阶段', p.financing],
    ['技术栈', p.techStack.join('、')], ['企业标签', p.tags.join('、')], ['招聘渠道', p.hiringChannels.join('、')],
    ['企业简介', p.description],
    ['HR 联系人', `${p.hrName} · ${p.hrTitle}`], ['HR 电话', p.hrPhone], ['HR 邮箱', p.hrEmail],
  ]
  downloadCsv(`企业档案_${p.shortName || p.name || '企业'}_${today()}.csv`, headers, rows)
  notify('档案已导出', `${p.shortName || p.name} · 企业档案卷宗 CSV 已下载`)
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

onMounted(() => { store.fetchEnterpriseProfile() })
</script>
