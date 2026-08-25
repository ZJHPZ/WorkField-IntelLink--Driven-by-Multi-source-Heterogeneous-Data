/**
 * 匹配相关纯函数 —— 雷达维度构建（去重 DashboardView / MatchView 两处重复逻辑）。
 */
import type { RadarDimension } from '@/components/personal/MatchRadar.vue'

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
