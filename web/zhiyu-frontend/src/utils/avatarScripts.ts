/**
 * avatarScripts — 企业侧数字人汇报脚本，从 enterprise store 实时派生。
 *
 * 每条脚本是给数字人朗读的自然段落（真实数字）：报表/缺口/预测都来自当前数据，
 * 数据为空时降级为「—」，避免念出空洞内容。
 */
import type { useEnterpriseStore } from '@/stores/enterprise'

export interface AvatarScript {
  id: string
  title: string
  text: string
}

function pct(score: number | undefined | null): string {
  return `${Math.round((score ?? 0) * 100)}%`
}

function join(list: string[] | undefined, max: number): string {
  return (list ?? []).slice(0, max).join('、') || '—'
}

export function buildAvatarScripts(store: ReturnType<typeof useEnterpriseStore>): AvatarScript[] {
  const scripts: AvatarScript[] = []

  // ── 1 企业工作台周报 ──
  {
    const pos = store.positions
    const diag = store.diagnoses
    const warns = diag.filter((d) => d.status !== 'healthy').length
    const tal = store.talentCandidates
    const highMatch = tal.filter((c) => c.bestMatchRate >= 85).length
    const highGap = store.teamGaps.filter((g) => g.priority === 'high').length
    scripts.push({
      id: 'weekly',
      title: '企业工作台周报',
      text:
        `本周汇报。在管岗位标准共 ${pos.length} 项，` +
        (pos.length ? `其中确认发布 ${pos.filter((p) => p.status === 'confirmed').length} 项；` : '') +
        `JD 质量诊断 ${diag.length} 份，其中 ${warns} 份需要关注；` +
        `人才库在库 ${tal.length} 名候选人，高匹配 ${highMatch} 名；` +
        `团队技能高优缺口 ${highGap} 项。总体运行平稳，重点推进高优缺口处置。`,
    })
  }

  // ── 2 人才需求预测 ──
  {
    const f = store.forecast
    const hot = f.emerging.slice(0, 3).map((s) => `${s.name}${pct(s.score)}`).join('、')
    const cool = f.cooling.slice(0, 2).map((s) => s.name).join('、')
    scripts.push({
      id: 'forecast',
      title: '人才需求预测',
      text:
        `基于近九十天市场语料的人才需求预测。` +
        (hot ? `升温技能排名靠前的是：${hot}；` : '暂无升温技能数据；') +
        (cool ? `降温技能包括：${cool}。` : '') +
        (f.recommendation ? f.recommendation : ''),
    })
  }

  // ── 3 团队技能缺口盘点 ──
  {
    const gaps = [...store.teamGaps]
      .sort((a, b) => (a.priority === 'high' ? -1 : 1) - (b.priority === 'high' ? -1 : 1) || b.gap - a.gap)
      .slice(0, 3)
    scripts.push({
      id: 'gaps',
      title: '团队技能缺口盘点',
      text: gaps.length
        ? gaps
            .map(
              (g) =>
                `${g.skillName}当前覆盖${g.currentAvg}%，距达标线差${Math.max(0, 80 - g.currentAvg)}个百分点，` +
                `影响${g.affectedPositions}个岗位${g.priority === 'high' ? '，列为高优处置' : ''}`,
            )
            .join('；') + '。建议优先领办培训。'
        : '团队技能盘点暂无缺口数据。',
    })
  }

  // ── 4 市场岗位对比 ──
  {
    const pos = store.positions[0]
    const mkt = pos ? store.market[pos.id] || [] : []
    scripts.push({
      id: 'market',
      title: '市场岗位对比',
      text: pos
        ? `岗位标准与市场对比。${pos.name}当前标准含${pos.skills.length}项技能，市场需求语料聚合出${mkt.length}项技能` +
          (mkt.length ? `，权重靠前的是：${mkt.slice(0, 3).map((s) => s.name).join('、')}` : '') +
          `。岗位市场匹配度${pos.matchRate}%，建议按差异清单持续校准标准。`
        : '暂无可对比的岗位标准。',
    })
  }

  // ── 5 新岗位发现 ──
  {
    const cands = store.candidates.filter((c) => c.status !== 'rejected').slice(0, 3)
    scripts.push({
      id: 'discovery',
      title: '新岗位发现',
      text: cands.length
        ? cands
            .map((c) => `${c.title}，置信度${pct(c.confidence)}，与现有标准技能重合度${c.skillOverlap}%`)
            .join('；') + '。建议评审立项。'
        : '暂无待评审的新岗位。',
    })
  }

  // ── 6 企业资料 ──
  {
    const p = store.enterpriseProfile
    scripts.push({
      id: 'company',
      title: '企业资料',
      text:
        `企业资料。${p.name || '—'}，${p.industry || '—'}行业，` +
        `${p.headcount || '—'}规模，${p.financing || '—'}阶段，总部${p.city || '—'}。` +
        (p.techStack?.length ? `核心技术栈包括：${join(p.techStack, 4)}。` : '') +
        (p.description ? p.description : ''),
    })
  }

  return scripts
}
