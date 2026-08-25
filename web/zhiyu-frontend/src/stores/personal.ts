import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

// ── 类型定义 ──

export interface SkillItem {
  id: string
  name: string
  category: string
  level: 'basic' | 'intermediate' | 'advanced' | 'expert'
  marketDemand: number       // 0-100
  marketDf: number           // 市场文档频率
  emergence: number          // 新兴度 0-1 (增长率)
  decline: number            // 衰退率 0-1
  freshness: number          // 0-100
  yearsOfExperience: number
  confidence: number         // 技能识别置信度 0-1
  firstSeen: string          // 首次识别日期
  status: 'healthy' | 'alert' | 'missing_high' | 'missing_low' | 'matched'
}

export interface JobMatch {
  id: string
  positionName: string
  company: string
  matchRate: number
  matchedSkills: string[]
  missingSkills: string[]
  salaryRange: string
}

export interface LearningStep {
  id: string
  title: string
  skill: string
  resource: string
  estimatedHours: number
  status: 'locked' | 'available' | 'in_progress' | 'completed'
  progress: number
}

export interface FreshnessAlert {
  skillName: string
  halfLife: number       // 月
  currentFreshness: number
  suggestedAction: string
  urgency: 'high' | 'medium' | 'low'
}

export interface CareerSwitchOption {
  targetRole: string
  transferabilityScore: number
  skillOverlap: string[]
  skillGaps: string[]
  estimatedTransitionMonths: number
  marketDemand: number
}

// ── 信号光谱 ──

export interface SignalSource {
  source: 'jd' | 'github' | 'arxiv' | 'standard'
  frequency: number        // 提及次数
  confidence: number       // 0-1
  examples: string[]       // 具体来源示例
}

export interface SignalDetail {
  skillName: string
  category: string
  totalConfidence: number  // 融合置信度 0-1
  sources: SignalSource[]
  verificationStatus: 'confirmed' | 'candidate' | 'unverified'
}

// ── 用户档案 / 成长 / 里程碑（来自 /api/personal/*） ──

export interface ProfileData {
  userId?: string
  name?: string
  title?: string
  phone?: string
  email?: string
  birthYear?: number
  status?: string
  industry?: string
  education?: string
  major?: string
  englishLevel?: string
  experienceYears?: number
  city?: string
  targetRole?: string
  targetCity?: string
  targetIndustry?: string
  salaryMin?: number
  salaryMax?: number
  priority?: string
  travelOk?: boolean
  relocateOk?: boolean
  workMode?: string
  resumeUrl?: string
  resumeParsedAt?: string | null
  avatarEmoji?: string
  level?: string
  createdAt?: string
  updatedAt?: string
}

export interface GrowthEvent {
  date: string
  skillsGained: number
  skills: string[]
  cumulativeCount: number
  description: string
}

export interface CareerMilestone {
  id: number
  name: string
  description: string
  icon?: string
  rarity?: string
  unlocked: boolean
  unlockedAt?: string | null
  progress: number
  target: number
}

// ── 岗位列表（来自 /api/positions，演化/探索复用） ──

export interface PositionItem {
  position_id: string
  name: string
  tech_stack: string
  position_type: string
  skill_count: number
}

// ── 岗位演化 ──

export interface EvolutionChange {
  type: 'added' | 'removed' | 'upgraded' | 'downgraded'
  skillName: string
  oldLevel?: string
  newLevel?: string
  evidence: string
  source: string
}

export interface EvolutionSnapshot {
  snapshotId: string
  positionName: string
  timestamp: string
  description: string
  skillCount: number
  changes: EvolutionChange[]
  dataSources: string[]
}

// ── Demo 数据 ──

const demoSkills: SkillItem[] = [
  { id: 'sk-1', name: 'Python', category: '编程语言', level: 'expert', marketDemand: 92, marketDf: 245, emergence: 0.05, decline: 0.02, freshness: 90, yearsOfExperience: 6, confidence: 0.98, firstSeen: '2022-03-15', status: 'healthy' },
  { id: 'sk-2', name: '深度学习', category: 'AI/ML', level: 'advanced', marketDemand: 95, marketDf: 210, emergence: 0.80, decline: 0.01, freshness: 88, yearsOfExperience: 4, confidence: 0.92, firstSeen: '2024-03-20', status: 'healthy' },
  { id: 'sk-3', name: 'TypeScript', category: '前端', level: 'advanced', marketDemand: 80, marketDf: 178, emergence: 0.15, decline: 0.03, freshness: 76, yearsOfExperience: 3, confidence: 0.90, firstSeen: '2024-09-01', status: 'healthy' },
  { id: 'sk-4', name: 'React', category: '前端', level: 'advanced', marketDemand: 78, marketDf: 195, emergence: 0.08, decline: 0.05, freshness: 82, yearsOfExperience: 4, confidence: 0.95, firstSeen: '2023-06-15', status: 'matched' },
  { id: 'sk-5', name: 'SQL', category: '数据', level: 'expert', marketDemand: 75, marketDf: 320, emergence: 0.02, decline: 0.01, freshness: 92, yearsOfExperience: 7, confidence: 0.99, firstSeen: '2022-03-15', status: 'healthy' },
  { id: 'sk-6', name: 'Docker/K8s', category: 'DevOps', level: 'intermediate', marketDemand: 85, marketDf: 230, emergence: 0.12, decline: 0.04, freshness: 65, yearsOfExperience: 2, confidence: 0.85, firstSeen: '2025-01-10', status: 'alert' },
  { id: 'sk-7', name: 'NLP', category: 'AI/ML', level: 'intermediate', marketDemand: 88, marketDf: 165, emergence: 0.70, decline: 0.02, freshness: 80, yearsOfExperience: 3, confidence: 0.88, firstSeen: '2024-06-01', status: 'healthy' },
  { id: 'sk-8', name: '系统设计', category: '架构', level: 'intermediate', marketDemand: 82, marketDf: 140, emergence: 0.10, decline: 0.03, freshness: 70, yearsOfExperience: 3, confidence: 0.82, firstSeen: '2024-09-15', status: 'healthy' },
  { id: 'sk-9', name: 'Go', category: '编程语言', level: 'basic', marketDemand: 72, marketDf: 130, emergence: 0.25, decline: 0.02, freshness: 45, yearsOfExperience: 1, confidence: 0.75, firstSeen: '2025-06-01', status: 'missing_low' },
  { id: 'sk-10', name: 'Kubernetes', category: 'DevOps', level: 'basic', marketDemand: 85, marketDf: 185, emergence: 0.30, decline: 0.01, freshness: 35, yearsOfExperience: 0.5, confidence: 0.70, firstSeen: '2025-09-01', status: 'missing_high' },
  { id: 'sk-11', name: 'MLOps', category: 'AI/ML', level: 'basic', marketDemand: 78, marketDf: 95, emergence: 0.65, decline: 0.01, freshness: 40, yearsOfExperience: 1, confidence: 0.72, firstSeen: '2025-03-15', status: 'alert' },
  { id: 'sk-12', name: '数据分析', category: '数据', level: 'intermediate', marketDemand: 70, marketDf: 155, emergence: 0.08, decline: 0.06, freshness: 85, yearsOfExperience: 4, confidence: 0.90, firstSeen: '2023-03-15', status: 'healthy' },
]

const demoMatches: JobMatch[] = [
  { id: 'm-1', positionName: 'AI 算法工程师', company: '某头部科技公司', matchRate: 72, matchedSkills: ['Python', '深度学习', 'NLP'], missingSkills: ['MLOps', '分布式训练'], salaryRange: '40-70K' },
  { id: 'm-2', positionName: '全栈开发工程师', company: '某互联网公司', matchRate: 85, matchedSkills: ['TypeScript', 'React', 'SQL'], missingSkills: ['AWS'], salaryRange: '30-50K' },
  { id: 'm-3', positionName: 'ML Engineer', company: '某AI创业公司', matchRate: 68, matchedSkills: ['Python', '深度学习'], missingSkills: ['MLOps', 'Kubernetes', '联邦学习'], salaryRange: '45-80K' },
]

const demoLearningPath: LearningStep[] = [
  { id: 'ls-1', title: 'Kubernetes 基础', skill: 'Kubernetes', resource: 'K8s 官方教程 + CKAD 认证', estimatedHours: 40, status: 'available', progress: 0 },
  { id: 'ls-2', title: 'MLOps 实践', skill: 'MLOps', resource: 'MLflow + Kubeflow 实战', estimatedHours: 30, status: 'available', progress: 0 },
  { id: 'ls-3', title: 'Go 语言进阶', skill: 'Go', resource: 'Go 高级编程 + 并发模式', estimatedHours: 25, status: 'in_progress', progress: 35 },
  { id: 'ls-4', title: '系统设计面试', skill: '系统设计', resource: 'DDIA + 案例分析', estimatedHours: 20, status: 'in_progress', progress: 60 },
  { id: 'ls-5', title: 'React 性能优化', skill: 'React', resource: 'React 性能优化指南', estimatedHours: 15, status: 'completed', progress: 100 },
]

const demoAlerts: FreshnessAlert[] = [
  { skillName: 'jQuery', halfLife: 6, currentFreshness: 28, suggestedAction: '建议迁移到 React/Vue 等现代框架，jQuery 市场需求持续下降', urgency: 'high' },
  { skillName: 'Docker/K8s', halfLife: 18, currentFreshness: 65, suggestedAction: '关注 K8s 最新版本特性，更新 CKAD 认证', urgency: 'medium' },
  { skillName: 'MLOps', halfLife: 12, currentFreshness: 40, suggestedAction: '学习 MLflow + Kubeflow，建立 ML 工程化能力', urgency: 'high' },
  { skillName: 'Go', halfLife: 24, currentFreshness: 45, suggestedAction: '继续深入学习 Go 并发模式和标准库', urgency: 'medium' },
]

const demoSwitchOptions: CareerSwitchOption[] = [
  { targetRole: 'AI 产品经理', transferabilityScore: 78, skillOverlap: ['Python', '数据分析', 'NLP'], skillGaps: ['产品设计', '用户研究', '竞品分析'], estimatedTransitionMonths: 6, marketDemand: 88 },
  { targetRole: '数据架构师', transferabilityScore: 65, skillOverlap: ['SQL', 'Python', '系统设计'], skillGaps: ['数据建模', 'ETL设计', '数据治理'], estimatedTransitionMonths: 9, marketDemand: 75 },
  { targetRole: '大数据工程师', transferabilityScore: 52, skillOverlap: ['SQL', 'Python', 'Go'], skillGaps: ['Spark', 'Hadoop', 'Hive', 'Flink'], estimatedTransitionMonths: 12, marketDemand: 82 },
  { targetRole: 'ML Engineer', transferabilityScore: 60, skillOverlap: ['Python', '深度学习', 'NLP'], skillGaps: ['分布式训练', '模型部署', 'A/B实验'], estimatedTransitionMonths: 8, marketDemand: 90 },
  { targetRole: '全栈开发', transferabilityScore: 85, skillOverlap: ['TypeScript', 'React', 'SQL', 'Python'], skillGaps: ['Node.js', 'Next.js'], estimatedTransitionMonths: 4, marketDemand: 72 },
  { targetRole: 'AI工程师', transferabilityScore: 72, skillOverlap: ['Python', '深度学习', 'NLP', 'SQL'], skillGaps: ['大模型微调', 'DeepSpeed', 'RLHF'], estimatedTransitionMonths: 7, marketDemand: 95 },
]

const demoSignalDetails: SignalDetail[] = [
  { skillName: 'Python', category: '编程语言', totalConfidence: 0.98, verificationStatus: 'confirmed',
    sources: [
      { source: 'jd', frequency: 245, confidence: 0.99, examples: ['JD-20260801-001', 'JD-20260801-015'] },
      { source: 'github', frequency: 180, confidence: 0.95, examples: ['trending/python', 'awesome-python'] },
      { source: 'arxiv', frequency: 120, confidence: 0.92, examples: ['2301.00001', '2306.12345'] },
      { source: 'standard', frequency: 50, confidence: 0.98, examples: ['IEEE-SE-2025', 'ACM-CC-2025'] },
    ] },
  { skillName: '深度学习', category: 'AI/ML', totalConfidence: 0.92, verificationStatus: 'confirmed',
    sources: [
      { source: 'jd', frequency: 210, confidence: 0.94, examples: ['JD-20260801-003', 'JD-20260801-022'] },
      { source: 'github', frequency: 150, confidence: 0.90, examples: ['pytorch/pytorch', 'tensorflow/tensorflow'] },
      { source: 'arxiv', frequency: 280, confidence: 0.95, examples: ['2301.00002', '2306.54321'] },
      { source: 'standard', frequency: 30, confidence: 0.85, examples: ['IEEE-AI-2025'] },
    ] },
  { skillName: 'MLOps', category: 'AI/ML', totalConfidence: 0.72, verificationStatus: 'candidate',
    sources: [
      { source: 'jd', frequency: 95, confidence: 0.75, examples: ['JD-20260801-008'] },
      { source: 'github', frequency: 60, confidence: 0.70, examples: ['mlflow/mlflow'] },
      { source: 'arxiv', frequency: 25, confidence: 0.60, examples: ['2306.99999'] },
      { source: 'standard', frequency: 8, confidence: 0.55, examples: [] },
    ] },
  { skillName: 'Kubernetes', category: 'DevOps', totalConfidence: 0.70, verificationStatus: 'candidate',
    sources: [
      { source: 'jd', frequency: 185, confidence: 0.80, examples: ['JD-20260801-012'] },
      { source: 'github', frequency: 140, confidence: 0.75, examples: ['kubernetes/kubernetes'] },
      { source: 'arxiv', frequency: 15, confidence: 0.50, examples: [] },
      { source: 'standard', frequency: 20, confidence: 0.65, examples: ['CNCF-2025'] },
    ] },
  { skillName: 'Go', category: '编程语言', totalConfidence: 0.75, verificationStatus: 'confirmed',
    sources: [
      { source: 'jd', frequency: 130, confidence: 0.78, examples: ['JD-20260801-019'] },
      { source: 'github', frequency: 160, confidence: 0.82, examples: ['golang/go'] },
      { source: 'arxiv', frequency: 10, confidence: 0.45, examples: [] },
      { source: 'standard', frequency: 12, confidence: 0.60, examples: [] },
    ] },
]

const demoEvolutionSnapshots: EvolutionSnapshot[] = [
  { snapshotId: 'snap-2025-01', positionName: 'AI 算法工程师', timestamp: '2025-01-15', description: '2025年初岗位技能基线', skillCount: 12, dataSources: ['JD×156', 'GitHub×45'],
    changes: [
      { type: 'added', skillName: '大模型微调', evidence: '32条JD提及LoRA/QLoRA', source: 'JD聚合' },
      { type: 'added', skillName: 'RAG', evidence: '28条JD提及检索增强生成', source: 'JD聚合' },
      { type: 'upgraded', skillName: 'PyTorch', oldLevel: '中级', newLevel: '高级', evidence: '85%JD要求熟练使用', source: 'JD分析' },
    ] },
  { snapshotId: 'snap-2025-06', positionName: 'AI 算法工程师', timestamp: '2025-06-20', description: '2025年中技能需求更新', skillCount: 15, dataSources: ['JD×210', 'GitHub×68', 'arXiv×35'],
    changes: [
      { type: 'added', skillName: 'DeepSpeed', evidence: '分布式训练需求激增，45条JD提及', source: 'JD+GitHub' },
      { type: 'added', skillName: 'RLHF', evidence: '对齐技术成为标配，38条JD提及', source: 'JD+arXiv' },
      { type: 'removed', skillName: 'TensorFlow 1.x', evidence: '旧版本需求降至5%以下', source: 'JD衰退分析' },
      { type: 'upgraded', skillName: 'NLP', oldLevel: '中级', newLevel: '高级', evidence: '大模型时代NLP要求提升', source: 'JD趋势' },
    ] },
  { snapshotId: 'snap-2026-01', positionName: 'AI 算法工程师', timestamp: '2026-01-10', description: '2026年初最新技能图谱', skillCount: 18, dataSources: ['JD×285', 'GitHub×92', 'arXiv×58', '标准×12'],
    changes: [
      { type: 'added', skillName: '多模态模型', evidence: '视觉语言模型需求爆发，62条JD提及', source: 'JD+arXiv' },
      { type: 'added', skillName: 'Agent框架', evidence: 'AI Agent成为新方向，48条JD提及', source: 'JD+GitHub' },
      { type: 'upgraded', skillName: 'MLOps', oldLevel: '初级', newLevel: '中级', evidence: '工程化能力要求提升', source: 'JD趋势' },
      { type: 'downgraded', skillName: '传统机器学习', oldLevel: '高级', newLevel: '中级', evidence: '深度学习取代大部分传统ML', source: 'JD衰退分析' },
    ] },
]

// ── Store ──

export const usePersonalStore = defineStore('personal', () => {
  const skills = ref<SkillItem[]>([...demoSkills])
  const matches = ref<JobMatch[]>([...demoMatches])
  const learningPath = ref<LearningStep[]>([...demoLearningPath])
  const alerts = ref<FreshnessAlert[]>([...demoAlerts])
  const switchOptions = ref<CareerSwitchOption[]>([...demoSwitchOptions])
  const signalDetails = ref<SignalDetail[]>([...demoSignalDetails])
  const evolutionSnapshots = ref<EvolutionSnapshot[]>([...demoEvolutionSnapshots])
  const positions = ref<PositionItem[]>([])
  const profile = ref<ProfileData | null>(null)
  const growth = ref<{ currentLevel: number; levels: { level: number; name: string; minSkills: number }[]; timeline: GrowthEvent[] } | null>(null)
  const milestones = ref<CareerMilestone[]>([])
  const loading = ref(false)

  const skillCount = computed(() => skills.value.length)
  const healthySkillCount = computed(() => skills.value.filter(s => s.status === 'healthy' || s.status === 'matched').length)
  const alertSkillCount = computed(() => skills.value.filter(s => s.status === 'alert').length)
  const bestMatch = computed(() => matches.value.reduce((best, m) => m.matchRate > best.matchRate ? m : best, matches.value[0]))
  const topSkillCategory = computed(() => {
    const cats = new Map<string, number>()
    skills.value.filter(s => s.level === 'expert' || s.level === 'advanced').forEach(s => cats.set(s.category, (cats.get(s.category) || 0) + 1))
    return [...cats.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || '—'
  })

  /** 单技能信号查找：详情页按技能名解析 */
  function signalByName(name: string): SignalDetail | null {
    return signalDetails.value.find(s => s.skillName === name) ?? null
  }

  async function fetchSkills() {
    loading.value = true
    try {
      const res = await client.get('/api/personal/skills') as any
      if (res?.skills?.length) skills.value = res.skills
    } catch {}
    finally { loading.value = false }
  }

  async function fetchMatches() {
    try {
      const res = await client.get('/api/personal/matches') as any
      if (res?.matches?.length) matches.value = res.matches
    } catch {}
  }

  async function fetchLearningPath() {
    try {
      const res = await client.get('/api/personal/learning-path') as any
      if (res?.steps?.length) learningPath.value = res.steps
    } catch {}
  }

  async function fetchFreshness() {
    try {
      const res = await client.get('/api/personal/freshness') as any
      if (res?.alerts?.length) alerts.value = res.alerts
    } catch {}
  }

  async function fetchSwitchOptions() {
    try {
      const res = await client.get('/api/personal/switch') as any
      if (res?.options?.length) switchOptions.value = res.options
    } catch {}
  }

  async function fetchProfile() {
    try {
      const res = await client.get('/api/personal/profile') as any
      if (res?.name) profile.value = res
    } catch {}
  }

  async function fetchGrowth() {
    try {
      const res = await client.get('/api/personal/growth') as any
      if (res?.timeline) growth.value = res
    } catch {}
  }

  async function fetchMilestones() {
    try {
      const res = await client.get('/api/personal/milestones') as any
      if (res?.milestones?.length) milestones.value = res.milestones
    } catch {}
  }

  async function fetchPositions() {
    try {
      const res = await client.get('/api/positions') as any
      if (res?.positions?.length) positions.value = res.positions
    } catch {}
  }

  /**
   * 岗位演化 —— 前端适配真实端点 GET /api/positions/{id}/evolution。
   * 后端返回 { position_id, snapshot_count, timeline:[{from,to,added_skills,removed_skills,modified_skills,summary}] }。
   * timeline 映射为 EvolutionSnapshot[]；timeline 为空（快照 <2）时保留 demo 兜底。
   */
  async function fetchEvolution(positionId: string, positionName?: string) {
    try {
      const res = await client.get(`/api/positions/${positionId}/evolution`) as any
      const timeline = res?.timeline
      if (!timeline?.length) return
      evolutionSnapshots.value = timeline.map((t: any, i: number) => {
        const added: EvolutionChange[] = (t.added_skills || []).map((s: string) =>
          ({ type: 'added', skillName: s, evidence: t.summary || '新增技能', source: '快照对比' }))
        const removed: EvolutionChange[] = (t.removed_skills || []).map((s: string) =>
          ({ type: 'removed', skillName: s, evidence: t.summary || '移除技能', source: '快照对比' }))
        const modified: EvolutionChange[] = (t.modified_skills || []).map((m: any) =>
          ({ type: m.old_confidence < m.new_confidence ? 'upgraded' : 'downgraded',
             skillName: m.name, oldLevel: m.old_confidence.toFixed(2), newLevel: m.new_confidence.toFixed(2),
             evidence: `置信度 ${m.old_confidence} → ${m.new_confidence}`, source: '快照对比' }))
        return {
          snapshotId: `evol-${i}`,
          positionName: positionName || positionId,
          timestamp: t.to || t.from || '',
          description: t.summary || `演化阶段 ${i + 1}`,
          skillCount: added.length + removed.length + modified.length,
          changes: [...added, ...removed, ...modified],
          dataSources: [],
        } as EvolutionSnapshot
      })
    } catch {}
  }

  return {
    skills, matches, learningPath, alerts, switchOptions, signalDetails, evolutionSnapshots, positions, profile, growth, milestones, loading,
    skillCount, healthySkillCount, alertSkillCount, bestMatch, topSkillCategory, signalByName,
    fetchSkills, fetchMatches, fetchLearningPath, fetchFreshness, fetchSwitchOptions, fetchPositions, fetchEvolution,
    fetchProfile, fetchGrowth, fetchMilestones,
  }
})
