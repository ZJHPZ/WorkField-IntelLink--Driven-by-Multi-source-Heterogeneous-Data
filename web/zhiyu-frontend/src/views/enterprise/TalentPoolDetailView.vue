<template>
  <div class="space-y-4">
    <!-- ═══ 报告头：候选人档案 ═══ -->
    <header class="doc-masthead px-4 py-4">
      <div class="relative z-[1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="ent-title-serif text-lg font-bold leading-tight">
            {{ profile?.name || '候选人' }} · {{ profile?.title || '' }}
          </h1>
          <p class="mt-0.5 text-[11px] font-mono tracking-wider text-white/55">
            CANDIDATE DOSSIER · 目标 {{ profile?.targetRole || '—' }} · {{ profile?.city || '—' }}
          </p>
          <span class="doc-meta inline-block mt-2">内部资料 · 档案编号 ZYZL-ENT-TAL-{{ docNo }}</span>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="seal-chip"
            :style="{ color: favorite ? '#fff' : 'rgba(255,255,255,0.6)', borderColor: favorite ? '#fff' : 'rgba(255,255,255,0.35)', cursor: 'pointer' }"
            @click="toggleFavorite"
          >{{ favorite ? '★ 已收藏' : '☆ 收藏' }}</button>
          <SealChip :status="hrStatus" />
        </div>
      </div>
    </header>

    <!-- ═══ 文档操作栏 ═══ -->
    <div class="flex flex-wrap items-center gap-2">
      <button class="ent-btn ent-btn--coral" @click="exportDossier">导出档案</button>
      <router-link to="/enterprise/talent-pool" class="ent-link">← 返回人才库</router-link>
      <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">档案由用户画像 + 岗位匹配自动沉淀</span>
    </div>

    <NotificationBar
      :visible="showNotification"
      :message="notifyMessage"
      :detail="notifyDetail"
      @close="showNotification=false"
    />

    <template v-if="profile">
      <!-- ═══ 01 人才画像 ═══ -->
      <section class="panel-doc p-4">
        <span class="watermark-num">01</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">01</span>
            <span class="section-name">人才画像</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">候选人公开档案 · 不可由 HR 标注修改</span>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div class="stat-tile">
              <div class="stat-num" :class="bestMatch >= 85 ? 'coral coral-glow' : ''"><CountUp :value="bestMatch" /></div>
              <div class="stat-label">最高匹配</div>
              <div class="stat-sub">岗位匹配 Top1</div>
            </div>
            <div class="stat-tile">
              <div class="stat-num"><CountUp :value="skills.length" /></div>
              <div class="stat-label">技能数</div>
              <div class="stat-sub">画像技能条</div>
            </div>
            <div class="stat-tile">
              <div class="stat-num" style="font-size:15px">{{ profile.experienceYears }}</div>
              <div class="stat-label">工作年限</div>
              <div class="stat-sub">{{ profile.education }}</div>
            </div>
            <div class="stat-tile">
              <div class="stat-num" style="font-size:15px">{{ profile.salaryMin }}-{{ profile.salaryMax }}K</div>
              <div class="stat-label">期望薪资</div>
              <div class="stat-sub">月薪范围</div>
            </div>
          </div>
          <div class="mt-2">
            <div class="archive-row"><span>现任岗位</span><b>{{ profile.title }}</b></div>
            <div class="archive-row"><span>目标方向</span><b>{{ profile.targetRole }}</b></div>
            <div class="archive-row"><span>所在城市</span><b>{{ profile.city }}</b></div>
            <div class="archive-row"><span>学历专业</span><b>{{ profile.education }} · {{ profile.major }}</b></div>
            <div class="archive-row"><span>工作年限</span><b>{{ profile.experienceYears }}</b></div>
            <div class="archive-row"><span>期望城市</span><b>{{ profile.targetCity }}</b></div>
            <div class="archive-row"><span>外语水平</span><b>{{ profile.englishLevel || '—' }}</b></div>
            <div class="archive-row"><span>工作模式</span><b>{{ workModeLabel }} · 可出差 {{ yn(profile.travelOk) }} · 可调岗 {{ yn(profile.relocateOk) }}</b></div>
          </div>
        </div>
      </section>

      <!-- ═══ 02 技能画像 ═══ -->
      <section class="panel-doc p-4">
        <span class="watermark-num">02</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">02</span>
            <span class="section-name">技能画像</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">×{{ skills.length }} · 熟练度 + 保鲜度 + 年限</span>
          </div>
          <div v-if="skills.length">
            <div v-for="s in skills" :key="s.name" class="doc-skill">
              <div class="sk-head">
                <span class="sk-name">{{ s.name }}</span>
                <span class="sk-level">{{ levelLabel(s.level) }}</span>
                <i class="ink-bar"><i :class="{ coral: s.freshness < 60 }" :style="{ width: s.freshness + '%' }"></i></i>
                <span class="sk-wt">保鲜 {{ s.freshness }}</span>
                <span class="sk-wt" style="color:var(--ent-ink-muted)">年限 {{ s.yearsOfExperience }}y</span>
                <span class="flex-1"></span>
                <span class="footnote" style="margin:0">市场需求 {{ s.marketDemand }}</span>
              </div>
              <div class="sk-reason" style="margin-top:2px">类别 · {{ s.category }}　|　状态 · {{ s.status }}</div>
            </div>
          </div>
          <div v-else class="doc-empty">
            <div class="lines"><i></i><i></i><i></i></div>
            "暂无技能画像 · NO SKILLS"
          </div>
        </div>
      </section>

      <!-- ═══ 03 匹配记录 ═══ -->
      <section class="panel-doc p-4">
        <span class="watermark-num">03</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">03</span>
            <span class="section-name">匹配记录</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">岗位匹配报告 · 已匹配 / 缺口技能</span>
          </div>
          <div v-if="matches.length">
            <div class="tbl-head--mt">
              <span>匹配岗位</span>
              <span>公司</span>
              <span style="text-align:right">匹配率</span>
              <span>已匹配技能</span>
              <span>缺口技能</span>
              <span style="text-align:right">薪资</span>
            </div>
            <div>
              <div v-for="m in matches" :key="m.positionId" class="tbl-row--mt">
                <span class="mt-pos">{{ m.positionName }}</span>
                <span class="mt-co">{{ m.company }}</span>
                <span class="t-match" :class="{ coral: m.matchRate >= 85 }"><CountUp :value="m.matchRate" /></span>
                <div class="t-skills">
                  <span v-for="s in m.matchedSkills" :key="s" class="skill-tag">{{ s }}</span>
                  <span v-if="!m.matchedSkills.length" class="t-sub">—</span>
                </div>
                <div class="t-skills">
                  <span v-for="s in m.missingSkills" :key="s" class="skill-tag skill-tag--miss">{{ s }}</span>
                  <span v-if="!m.missingSkills.length" class="t-sub">—</span>
                </div>
                <span class="mt-sal">{{ m.salaryRange }}</span>
              </div>
            </div>
          </div>
          <div v-else class="doc-empty">
            <div class="lines"><i></i><i></i><i></i></div>
            "暂无匹配记录 · NO MATCHES"
          </div>
        </div>
      </section>

      <!-- ═══ 04 标注面板 ═══ -->
      <section class="panel-doc p-4">
        <span class="watermark-num">04</span>
        <div class="relative z-[1]">
          <div class="section-head">
            <span class="section-num">04</span>
            <span class="section-name">HR 标注</span>
            <span class="section-rule"></span>
            <span class="footnote" style="margin:0">仅 HR 可见 · 不修改候选人公开画像</span>
          </div>
          <div class="rec-box space-y-3">
            <div class="flex flex-wrap items-center gap-2">
              <span class="footnote" style="margin:0;color:var(--ent-coral)">流程状态</span>
              <button
                v-for="h in HR_OPTIONS"
                :key="h.value"
                class="ent-chip"
                :class="{ 'ent-chip--active': draftStatus === h.value }"
                @click="draftStatus = h.value"
              >{{ h.label }}</button>
              <span class="flex-1"></span>
              <span class="footnote" style="margin:0">收藏 <span class="src">{{ favorite ? '已收藏' : '未收藏' }}</span></span>
            </div>
            <textarea
              v-model="draftNote"
              class="ent-input"
              rows="3"
              placeholder="填写跟进备注（仅 HR 可见）…"
            ></textarea>
            <div class="flex items-center gap-2">
              <button class="ent-btn ent-btn--coral" @click="saveAnnotation">盖章保存</button>
              <span class="doc-meta" style="color:var(--ent-ink-muted);border-color:var(--ent-rule)">上次更新 {{ updatedLabel }}</span>
            </div>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="panel-doc p-4">
      <div class="doc-empty">
        <div class="lines"><i></i><i></i><i></i></div>
        "候选人档案不存在 · DOSSIER NOT FOUND"
      </div>
    </div>

    <!-- ═══ 页脚 ═══ -->
    <footer class="report-footer">
      <div>
        <div class="foot-label">岗位标准智能管理中心 · 内部资料</div>
        <div class="foot-label" style="margin-top:3px">人才盘点 · 简历解析 Agent　审批 · 职域智联</div>
      </div>
      <div class="foot-label">数据截止 2026-08-30 · PAGE 10 / 10</div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useEnterpriseStore } from '@/stores/enterprise'
import type { TalentDetail, HrStatus } from '@/stores/enterprise'
import NotificationBar from '@/components/common/NotificationBar.vue'
import CountUp from '@/components/enterprise/CountUp.vue'
import SealChip from '@/components/enterprise/SealChip.vue'
import { downloadCsv, today } from '@/utils/export'

const store = useEnterpriseStore()
const route = useRoute()
const id = route.params.id as string

const detail = computed<TalentDetail | null>(() => store.talentDetails[id] ?? null)
const row = computed(() => store.talentCandidates.find(c => c.id === id))

// 列表行兜底（详情尚未拉取时仍可渲染画像骨架）
const profile = computed(() => {
  if (detail.value?.profile) return detail.value.profile
  if (row.value) {
    return {
      name: row.value.name, title: row.value.title, targetRole: row.value.targetRole,
      targetCity: '', city: row.value.city, industry: '', experienceYears: row.value.experienceYears,
      education: row.value.education, major: '', englishLevel: '', salaryMin: row.value.salaryMin,
      salaryMax: row.value.salaryMax, workMode: '', relocateOk: false, travelOk: false, avatarEmoji: '🧑‍💻',
    }
  }
  return null
})
const skills = computed(() => detail.value?.skills ?? [])
const matches = computed(() => detail.value?.matches ?? [])
const annotation = computed(() => {
  const d = detail.value?.annotation
  if (d) return d
  if (row.value) {
    return { favorite: row.value.favorite, hrStatus: row.value.hrStatus, note: row.value.note, updatedAt: row.value.updatedAt }
  }
  return { favorite: false, hrStatus: '' as HrStatus, note: '', updatedAt: null }
})

const bestMatch = computed(() => matches.value.length ? Math.max(...matches.value.map(m => m.matchRate)) : 0)
const favorite = computed(() => annotation.value.favorite)
const hrStatus = computed(() => annotation.value.hrStatus)
const updatedLabel = computed(() => annotation.value.updatedAt ? String(annotation.value.updatedAt).slice(0, 16).replace('T', ' ') : '—')
const docNo = computed(() => id.replace('cand_', '').toUpperCase() || '—')

// ── 标注草稿 ──
const HR_OPTIONS: { value: HrStatus; label: string }[] = [
  { value: '', label: '未标注' },
  { value: 'shortlisted', label: '已筛选' },
  { value: 'interviewing', label: '面试中' },
  { value: 'offered', label: '已Offer' },
  { value: 'archived', label: '已归档' },
]
const draftStatus = ref<HrStatus>('')
const draftNote = ref('')

watch(annotation, (a) => {
  if (a) { draftStatus.value = a.hrStatus; draftNote.value = a.note }
}, { immediate: true })

function toggleFavorite() {
  store.updateTalentAnnotation(id, { favorite: !favorite.value }).then(() => {
    notify(favorite.value ? '已收藏' : '已取消收藏', `${profile.value?.name || id} · 标注已更新`)
  })
}
function saveAnnotation() {
  store.updateTalentAnnotation(id, { hrStatus: draftStatus.value, note: draftNote.value }).then(() => {
    notify('标注已盖章', `${profile.value?.name || id} · ${HR_OPTIONS.find(h => h.value === draftStatus.value)?.label} · 备注已保存`)
  })
}
function exportDossier() {
  const p = profile.value
  const headers = ['栏目', '项目', '内容']
  const rows: unknown[][] = []
  if (p) {
    rows.push(
      ['人才画像', '姓名', p.name],
      ['人才画像', '现任岗位', p.title],
      ['人才画像', '目标方向', p.targetRole],
      ['人才画像', '城市 → 期望城市', `${p.city} → ${p.targetCity || '—'}`],
      ['人才画像', '学历专业', `${p.education} · ${p.major || '—'}`],
      ['人才画像', '工作年限', p.experienceYears],
      ['人才画像', '期望薪资', `${p.salaryMin}-${p.salaryMax}K`],
      ['人才画像', '外语 · 工作模式', `${p.englishLevel || '—'} · ${workModeLabel.value}`],
    )
  }
  for (const s of skills.value) {
    rows.push(['技能画像', s.name, `${levelLabel(s.level)} · 保鲜 ${s.freshness} · ${s.yearsOfExperience}y · 市场需求 ${s.marketDemand} · ${s.status}`])
  }
  for (const m of matches.value) {
    rows.push(['匹配记录', m.positionName, `${m.company} · 匹配率 ${m.matchRate}% · 已匹配 ${m.matchedSkills.join('、') || '—'} · 缺口 ${m.missingSkills.join('、') || '—'} · ${m.salaryRange}`])
  }
  rows.push(['HR 标注', '流程状态', hrStatus.value || '未标注'])
  rows.push(['HR 标注', '收藏', favorite.value ? '已收藏' : '未收藏'])
  rows.push(['HR 标注', '备注', annotation.value.note || '—'])
  downloadCsv(`人才档案_${p?.name || id}_${today()}.csv`, headers, rows)
  notify('档案已导出', `${p?.name || id} · 人才档案卷宗 CSV 已下载`)
}

const levelMap: Record<string, string> = { basic: '入门', intermediate: '中级', advanced: '高级', expert: '专家' }
function levelLabel(l: string): string { return levelMap[l] || l }
const workModeMap: Record<string, string> = { onsite: '到岗', remote: '远程', hybrid: '混合' }
const workModeLabel = computed(() => workModeMap[profile.value?.workMode || ''] || profile.value?.workMode || '—')
function yn(v: boolean): string { return v ? '可' : '否' }

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

onMounted(() => { store.fetchTalentDetail(id) })
</script>
