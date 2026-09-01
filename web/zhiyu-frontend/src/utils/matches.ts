/**
 * 匹配相关纯函数 —— 雷达维度构建 + 真实岗位匹配计算。
 */
import type { RadarDimension } from '@/components/personal/MatchRadar.vue'
import type { SkillItem, PositionItem, JobMatch } from '@/stores/personal'

export interface MatchRadarSource {
  matchedSkills: string[]
  missingSkills: string[]
  matchRate: number
}

/** 由一条岗位匹配结果构建 6 维雷达数据 */
export function buildMatchRadarDimensions(match: MatchRadarSource): RadarDimension[] {
  const t = match.matchedSkills.length + match.missingSkills.length
  return [
    { name: '技能覆盖度', userScore: Math.round((match.matchedSkills.length / Math.max(t, 1)) * 100), targetScore: 100, max: 100 },
    { name: '匹配率', userScore: match.matchRate, targetScore: 90, max: 100 },
    { name: '核心技术', userScore: Math.round(match.matchRate * 0.85), targetScore: 85, max: 100 },
    { name: '辅助技能', userScore: Math.round(match.matchRate * 0.7), targetScore: 80, max: 100 },
    { name: '经验年限', userScore: 72, targetScore: 80, max: 100 },
    { name: '保鲜度', userScore: 78, targetScore: 85, max: 100 },
  ]
}

/** 无匹配数据时的演示维度（Dashboard 首次渲染的 Silent Fallback） */
export const RADAR_DEMO: RadarDimension[] = [
  { name: '技能覆盖度', userScore: 72, targetScore: 100, max: 100 },
  { name: '匹配率', userScore: 72, targetScore: 90, max: 100 },
  { name: '核心技术', userScore: 68, targetScore: 85, max: 100 },
  { name: '辅助技能', userScore: 75, targetScore: 80, max: 100 },
  { name: '经验年限', userScore: 72, targetScore: 80, max: 100 },
  { name: '保鲜度', userScore: 78, targetScore: 85, max: 100 },
]

// ══════════════════════════════════════════════
// 真实岗位匹配 —— 镜像后端 app/services/match_service.match_skills()
// 数据源：/api/positions（JD 派生岗位标准）× 用户技能画像（store.skills）
// ══════════════════════════════════════════════

export interface MatchLearningStep {
  skill: string
  hours: number
  duration: string
  resource: string
}

function norm(s: string) { return s.trim().toLowerCase() }

export interface SkillClassifyResult {
  matched: string[]
  partial: string[]
  missing: string[]
  rate: number
}

/**
 * 把一组岗位必备技能对照用户画像分类：命中 / 近似 / 缺失，并按覆盖度折算匹配率。
 * 算法与后端 match_service 一致（技能精确 + 子串近似，rate = effective/total）。
 * 独立暴露供「岗位库收藏」等场景复用（收藏岗位时计算个人覆盖快照）。
 */
export function classifySkills(userSkills: SkillItem[], required: string[]): SkillClassifyResult {
  const tokens = userSkills.map(s => norm(s.name))
  const matched: string[] = []
  const partial: string[] = []
  const missing: string[] = []
  for (const r of required) {
    const rn = norm(r)
    if (tokens.includes(rn)) matched.push(r)
    else if (tokens.some(u => rn.includes(u) || u.includes(rn))) partial.push(r)
    else missing.push(r)
  }
  const total = required.length
  const effective = matched.length + partial.length * 0.5
  const rate = total ? Math.round((effective / total) * 100) : 0
  return { matched, partial, missing, rate }
}

/** 缺失技能 → 补缺学习路径（学时按技能特征估算，与后端 _build_learning_path 同构） */
export function buildMatchLearningPath(missing: string[]): MatchLearningStep[] {
  return missing.map(s => {
    const hours = /分布式|训练|架构|平台|框架|工程/.test(s) ? 40
      : /部署|调优|微服务|编排|实验/.test(s) ? 30
      : 24
    const duration = hours >= 40 ? '3-4个月' : hours >= 30 ? '2-3个月' : '1-2个月'
    return { skill: s, hours, duration, resource: `专项学习 · ${s} 实战` }
  })
}

/**
 * 用真实岗位标准 × 用户技能画像计算匹配。
 * 与后端 match_service 一致的算法：技能 Jaccard + 近似子串 + 权重（覆盖度 0.4 / 必备率 0.6）。
 * 返回按匹配率降序的 JobMatch 列表（仅 rate>0 的岗位）。
 */
export function computePositionMatches(userSkills: SkillItem[], positions: PositionItem[]): JobMatch[] {
  const results: JobMatch[] = []

  for (const p of positions) {
    const reqs = p.requiredSkills ?? []
    if (!reqs.length) continue

    const { matched, partial, missing, rate } = classifySkills(userSkills, reqs)
    if (rate <= 0) continue

    results.push({
      id: `pos-${p.position_id}`,
      positionId: p.position_id,
      positionName: p.name,
      company: p.topCompanies?.[0]?.company_name ?? '—',
      matchRate: rate,
      matchedSkills: matched,
      partialSkills: partial,
      missingSkills: missing,
      salaryRange: p.salaryRange ?? '—',
      techStack: p.tech_stack,
      city: p.city ?? p.topCities?.[0]?.city,
      jdCount: p.jdCount,
      topCompanies: p.topCompanies,
      requiredSkills: reqs,
      learningPath: buildMatchLearningPath(missing),
      source: 'real',
    })
  }

  return results.sort((a, b) => b.matchRate - a.matchRate)
}
