import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'
import { normalizeGraph, buildDemoGraph } from '@/utils/graph'

// ── 类型定义 ──

export interface PositionStandard {
  id: string
  name: string
  department: string
  level: string
  skills: SkillRequirement[]
  status: 'confirmed' | 'emerging' | 'stable' | 'declining'
  lastUpdated: string
  marketDemand: number   // 0-100 市场需求指数
  matchRate: number      // 0-100 团队匹配率
}

export interface SkillRequirement {
  name: string
  level: 'basic' | 'intermediate' | 'advanced' | 'expert'
  weight: number         // 0-1 该技能权重
  trend: 'rising' | 'stable' | 'declining'
  freshness: number      // 0-100 保鲜度
}

export interface RoleCandidate {
  id: string
  title: string
  source: string
  discoveredAt: string
  confidence: number
  status: 'candidate' | 'confirmed' | 'rejected'
  debatePoints: { pro: string[]; con: string[] }
  skillOverlap: number
}

export interface JDDiagnosis {
  id: string
  positionName: string
  jdTitle: string
  submittedAt: string
  inflationIndex: number   // 0-1 JD 通胀指数
  missingKeywords: string[]
  redundantKeywords: string[]
  overallScore: number     // 0-100
  status: 'healthy' | 'warning' | 'critical'
}

export interface MarketSkill {
  name: string
  weight: number       // 市场需求权重 0-1
  level: 'basic' | 'intermediate' | 'advanced' | 'expert'
  freshness: number
}

export interface TeamGap {
  skillName: string
  requiredLevel: string
  currentAvg: number       // 0-100
  gap: number              // 差值
  affectedPositions: number
  priority: 'high' | 'medium' | 'low'
}

// ── 人才需求预测类型 ──

export interface SkillTrend {
  name: string
  score: number            // 新兴度/衰退度 0-1
  phase: 'hot' | 'rising' | 'new' | 'cooling' | 'fading'
}

export interface TalentForecast {
  emerging: SkillTrend[]   // 升温技能（由 hot_skills 映射）
  cooling: SkillTrend[]    // 降温技能（由 cooling_skills 映射）
  recommendation: string
}

// ── 人才库类型（对齐 /api/enterprise/talent-pool 契约）──

export type HrStatus = '' | 'shortlisted' | 'interviewing' | 'offered' | 'archived'

export interface TalentCandidate {
  id: string
  name: string
  title: string
  targetRole: string
  city: string
  experienceYears: string
  education: string
  salaryMin: number
  salaryMax: number
  skillCount: number
  topSkills: string[]
  bestMatchRate: number
  favorite: boolean
  hrStatus: HrStatus
  note: string
  updatedAt: string | null
}

export interface TalentSkill {
  name: string
  category: string
  level: 'basic' | 'intermediate' | 'advanced' | 'expert'
  freshness: number
  yearsOfExperience: number
  marketDemand: number
  status: string
}

export interface TalentMatch {
  positionId: string
  positionName: string
  company: string
  matchRate: number
  matchedSkills: string[]
  missingSkills: string[]
  salaryRange: string
}

export interface TalentAnnotation {
  favorite: boolean
  hrStatus: HrStatus
  note: string
  updatedAt: string | null
}

export interface TalentDetail {
  id: string
  profile: {
    name: string
    title: string
    targetRole: string
    targetCity: string
    city: string
    industry: string
    experienceYears: string
    education: string
    major: string
    englishLevel: string
    salaryMin: number
    salaryMax: number
    workMode: string
    relocateOk: boolean
    travelOk: boolean
    avatarEmoji: string
  }
  skills: TalentSkill[]
  matches: TalentMatch[]
  annotation: TalentAnnotation
}

export interface EnterpriseProfile {
  enterpriseId: string
  name: string
  shortName: string
  logoEmoji: string
  uscc: string
  nature: string
  industry: string
  foundedYear: number | null
  headcount: string
  financing: string
  city: string
  address: string
  website: string
  description: string
  tags: string[]
  techStack: string[]
  hiringChannels: string[]
  hrName: string
  hrTitle: string
  hrPhone: string
  hrEmail: string
  createdAt: string | null
  updatedAt: string | null
}

// ── 演化时间轴类型 ──

export interface SkillSnapshot {
  name: string
  level: 'basic' | 'intermediate' | 'advanced' | 'expert'
  weight: number
  freshness: number
  change: 'added' | 'removed' | 'upgraded' | 'downgraded' | 'unchanged'
  changeReason?: string    // 为什么变化（如 "ChatGPT发布推动LLM需求"）
}

export interface TimelineEvent {
  date: string              // e.g. "2023Q1"
  label: string             // e.g. "2023年第一季度"
  marketDemand: number      // 0-100 市场需求指数
  matchRate: number         // 0-100 团队匹配率
  salaryRange: string       // e.g. "25-45K"
  adoptionRate: number      // 0-100 企业采用率
  tools: string[]           // 常用工具/框架
  marketContext: string     // 市场背景描述
  industryEvents: string[]  // 触发变化的行业事件
  typicalProjects: string[] // 该时期典型项目
  skills: SkillSnapshot[]
  dataSources: string[]
  summary: string
}

export interface PositionEvolution {
  positionId: string
  positionName: string
  timeline: TimelineEvent[]
}

// ── 全景图谱类型 ──

export interface GraphNode {
  id: string
  name: string
  category: 'position' | 'skill'
  techStack?: string       // AI/前端/后端/数据/DevOps
  level?: string           // P5/P6/P7/P8
  marketDemand?: number    // 0-100
  skillCount?: number
  symbolSize?: number
}

export interface GraphLink {
  source: string
  target: string
  value?: number           // 关联强度
}

// ── Demo 数据 ──

const demoPositions: PositionStandard[] = [
  {
    id: 'pos-1', name: 'AI 算法工程师', department: '技术部', level: 'P7',
    skills: [
      { name: '深度学习', level: 'expert', weight: 0.30, trend: 'rising', freshness: 92 },
      { name: 'Python', level: 'expert', weight: 0.20, trend: 'stable', freshness: 88 },
      { name: 'NLP', level: 'advanced', weight: 0.15, trend: 'rising', freshness: 85 },
      { name: 'MLOps', level: 'intermediate', weight: 0.15, trend: 'rising', freshness: 78 },
      { name: '分布式训练', level: 'advanced', weight: 0.20, trend: 'stable', freshness: 80 },
    ],
    status: 'confirmed', lastUpdated: '2026-07-28', marketDemand: 94, matchRate: 72,
  },
  {
    id: 'pos-2', name: '全栈开发工程师', department: '技术部', level: 'P6',
    skills: [
      { name: 'React', level: 'expert', weight: 0.25, trend: 'stable', freshness: 90 },
      { name: 'Node.js', level: 'advanced', weight: 0.20, trend: 'stable', freshness: 82 },
      { name: 'TypeScript', level: 'advanced', weight: 0.20, trend: 'rising', freshness: 88 },
      { name: 'AWS', level: 'intermediate', weight: 0.15, trend: 'stable', freshness: 75 },
      { name: 'Docker/K8s', level: 'intermediate', weight: 0.20, trend: 'rising', freshness: 76 },
    ],
    status: 'stable', lastUpdated: '2026-07-15', marketDemand: 78, matchRate: 85,
  },
  {
    id: 'pos-3', name: '数据分析师', department: '数据部', level: 'P5',
    skills: [
      { name: 'SQL', level: 'expert', weight: 0.30, trend: 'stable', freshness: 90 },
      { name: 'Python', level: 'advanced', weight: 0.25, trend: 'stable', freshness: 85 },
      { name: 'Tableau', level: 'intermediate', weight: 0.20, trend: 'declining', freshness: 60 },
      { name: '统计学', level: 'advanced', weight: 0.25, trend: 'stable', freshness: 88 },
    ],
    status: 'emerging', lastUpdated: '2026-07-20', marketDemand: 85, matchRate: 68,
  },
  {
    id: 'pos-4', name: '技术项目经理', department: '技术部', level: 'P7',
    skills: [
      { name: '敏捷管理', level: 'advanced', weight: 0.25, trend: 'stable', freshness: 80 },
      { name: '技术架构', level: 'advanced', weight: 0.25, trend: 'rising', freshness: 82 },
      { name: '团队领导', level: 'advanced', weight: 0.25, trend: 'stable', freshness: 85 },
      { name: '风险管理', level: 'intermediate', weight: 0.25, trend: 'stable', freshness: 78 },
    ],
    status: 'stable', lastUpdated: '2026-06-30', marketDemand: 70, matchRate: 90,
  },
  {
    id: 'pos-5', name: 'DevOps 工程师', department: '技术部', level: 'P6',
    skills: [
      { name: 'CI/CD', level: 'expert', weight: 0.30, trend: 'rising', freshness: 92 },
      { name: 'Kubernetes', level: 'advanced', weight: 0.25, trend: 'rising', freshness: 86 },
      { name: 'Terraform', level: 'advanced', weight: 0.20, trend: 'rising', freshness: 84 },
      { name: '监控告警', level: 'intermediate', weight: 0.25, trend: 'stable', freshness: 75 },
    ],
    status: 'confirmed', lastUpdated: '2026-07-25', marketDemand: 88, matchRate: 65,
  },
  {
    id: 'pos-6', name: '前端开发工程师', department: '技术部', level: 'P5',
    skills: [
      { name: 'React/Vue', level: 'expert', weight: 0.30, trend: 'stable', freshness: 88 },
      { name: 'TypeScript', level: 'advanced', weight: 0.25, trend: 'rising', freshness: 85 },
      { name: 'CSS/Tailwind', level: 'advanced', weight: 0.20, trend: 'stable', freshness: 82 },
      { name: '性能优化', level: 'intermediate', weight: 0.25, trend: 'rising', freshness: 72 },
    ],
    status: 'stable', lastUpdated: '2026-07-10', marketDemand: 75, matchRate: 88,
  },
  {
    id: 'pos-7', name: '资深后端工程师', department: '技术部', level: 'P7',
    skills: [
      { name: 'Go/Rust', level: 'advanced', weight: 0.25, trend: 'rising', freshness: 82 },
      { name: '系统设计', level: 'expert', weight: 0.30, trend: 'stable', freshness: 90 },
      { name: '数据库优化', level: 'advanced', weight: 0.25, trend: 'stable', freshness: 85 },
      { name: '消息队列', level: 'advanced', weight: 0.20, trend: 'stable', freshness: 80 },
    ],
    status: 'confirmed', lastUpdated: '2026-08-01', marketDemand: 90, matchRate: 55,
  },
  {
    id: 'pos-8', name: 'QA 测试工程师', department: '质量部', level: 'P5',
    skills: [
      { name: '自动化测试', level: 'advanced', weight: 0.30, trend: 'rising', freshness: 80 },
      { name: '性能测试', level: 'intermediate', weight: 0.25, trend: 'stable', freshness: 72 },
      { name: '测试框架', level: 'advanced', weight: 0.25, trend: 'stable', freshness: 78 },
      { name: '安全测试', level: 'basic', weight: 0.20, trend: 'rising', freshness: 55 },
    ],
    status: 'declining', lastUpdated: '2026-05-20', marketDemand: 42, matchRate: 95,
  },
]

// 市场需求技能集（招聘JD语料聚合）——用于「市场 vs 标准」对比报告
const demoMarket: Record<string, MarketSkill[]> = {
  'pos-1': [
    { name: '深度学习', weight: 0.22, level: 'expert', freshness: 92 },
    { name: 'Python', weight: 0.16, level: 'expert', freshness: 88 },
    { name: 'NLP', weight: 0.12, level: 'advanced', freshness: 85 },
    { name: 'MLOps', weight: 0.20, level: 'advanced', freshness: 84 },
    { name: '分布式训练', weight: 0.14, level: 'advanced', freshness: 80 },
    { name: '大模型微调', weight: 0.10, level: 'advanced', freshness: 90 },
    { name: 'RAG 应用', weight: 0.06, level: 'intermediate', freshness: 86 },
  ],
  'pos-2': [
    { name: 'React', weight: 0.22, level: 'expert', freshness: 90 },
    { name: 'Node.js', weight: 0.16, level: 'advanced', freshness: 82 },
    { name: 'TypeScript', weight: 0.22, level: 'advanced', freshness: 90 },
    { name: 'AWS', weight: 0.14, level: 'intermediate', freshness: 75 },
    { name: 'Docker/K8s', weight: 0.18, level: 'advanced', freshness: 82 },
    { name: 'Serverless', weight: 0.08, level: 'intermediate', freshness: 78 },
  ],
  'pos-3': [
    { name: 'SQL', weight: 0.28, level: 'expert', freshness: 90 },
    { name: 'Python', weight: 0.28, level: 'advanced', freshness: 86 },
    { name: 'Tableau', weight: 0.10, level: 'intermediate', freshness: 52 },
    { name: '统计学', weight: 0.22, level: 'advanced', freshness: 88 },
    { name: 'AB 实验', weight: 0.08, level: 'intermediate', freshness: 80 },
    { name: '数据工程', weight: 0.04, level: 'basic', freshness: 70 },
  ],
  'pos-4': [
    { name: '敏捷管理', weight: 0.20, level: 'advanced', freshness: 78 },
    { name: '技术架构', weight: 0.28, level: 'advanced', freshness: 85 },
    { name: '团队领导', weight: 0.22, level: 'advanced', freshness: 85 },
    { name: '风险管理', weight: 0.18, level: 'intermediate', freshness: 76 },
    { name: 'AI 项目管理', weight: 0.12, level: 'intermediate', freshness: 82 },
  ],
  'pos-5': [
    { name: 'CI/CD', weight: 0.26, level: 'expert', freshness: 92 },
    { name: 'Kubernetes', weight: 0.28, level: 'advanced', freshness: 88 },
    { name: 'Terraform', weight: 0.18, level: 'advanced', freshness: 84 },
    { name: '监控告警', weight: 0.18, level: 'intermediate', freshness: 72 },
    { name: '可观测性', weight: 0.10, level: 'advanced', freshness: 80 },
  ],
  'pos-6': [
    { name: 'React/Vue', weight: 0.24, level: 'expert', freshness: 88 },
    { name: 'TypeScript', weight: 0.24, level: 'advanced', freshness: 87 },
    { name: 'CSS/Tailwind', weight: 0.14, level: 'advanced', freshness: 80 },
    { name: '性能优化', weight: 0.22, level: 'advanced', freshness: 76 },
    { name: '微前端', weight: 0.08, level: 'intermediate', freshness: 74 },
    { name: 'WebAssembly', weight: 0.08, level: 'basic', freshness: 68 },
  ],
  'pos-7': [
    { name: 'Go/Rust', weight: 0.30, level: 'advanced', freshness: 88 },
    { name: '系统设计', weight: 0.26, level: 'expert', freshness: 90 },
    { name: '数据库优化', weight: 0.20, level: 'advanced', freshness: 85 },
    { name: '消息队列', weight: 0.14, level: 'advanced', freshness: 78 },
    { name: '云原生', weight: 0.10, level: 'advanced', freshness: 82 },
  ],
  'pos-8': [
    { name: '自动化测试', weight: 0.32, level: 'advanced', freshness: 84 },
    { name: '性能测试', weight: 0.20, level: 'intermediate', freshness: 72 },
    { name: '测试框架', weight: 0.18, level: 'advanced', freshness: 78 },
    { name: '安全测试', weight: 0.22, level: 'advanced', freshness: 66 },
    { name: 'AI 测试', weight: 0.08, level: 'basic', freshness: 70 },
  ],
}

const demoCandidates: RoleCandidate[] = [
  {
    id: 'cand-1', title: 'LLM 应用工程师', source: '招聘市场分析', discoveredAt: '2026-08-02',
    confidence: 87, status: 'candidate', debatePoints: {
      pro: ['市场需求增长 320% YoY', '与现有 AI 工程师技能高度重叠', '多部门提出需求'],
      con: ['岗位定义尚不清晰', '人才供给不足', '可能被现有岗位覆盖'],
    }, skillOverlap: 75,
  },
  {
    id: 'cand-2', title: '数据安全合规师', source: '行业趋势报告', discoveredAt: '2026-07-30',
    confidence: 72, status: 'candidate', debatePoints: {
      pro: ['新法规合规需求', '数据泄露事件频发'],
      con: ['市场规模待验证', '与合规部门职责重叠'],
    }, skillOverlap: 45,
  },
  {
    id: 'cand-3', title: 'AI 产品经理', source: '竞品分析', discoveredAt: '2026-07-28',
    confidence: 91, status: 'confirmed', debatePoints: {
      pro: ['AI 产品线扩张', '已有 3 个 BU 提出招聘需求', '行业标准逐步建立'],
      con: ['需要跨领域能力', '薪资预算偏高'],
    }, skillOverlap: 68,
  },
  {
    id: 'cand-4', title: '数据标注质量师', source: '行业趋势报告', discoveredAt: '2026-08-01',
    confidence: 64, status: 'candidate', debatePoints: {
      pro: ['AI 训练数据需求激增', '可替代外包标注、降低质量风险'],
      con: ['岗位技术含量偏低', '与现有 QA 职责部分重叠'],
    }, skillOverlap: 32,
  },
  {
    id: 'cand-5', title: 'AI 训练平台工程师', source: '招聘市场分析', discoveredAt: '2026-07-31',
    confidence: 82, status: 'candidate', debatePoints: {
      pro: ['GPU 训练基础设施需求爆发', '与 MLOps 技能链高度兼容', '多个业务团队依赖'],
      con: ['人才稀缺', '与 DevOps 职责边界模糊'],
    }, skillOverlap: 58,
  },
  {
    id: 'cand-6', title: 'VR 内容开发工程师', source: '竞品分析', discoveredAt: '2026-07-20',
    confidence: 41, status: 'rejected', debatePoints: {
      pro: ['竞品已有 VR 内容布局'],
      con: ['市场需求不足', '与公司战略不符', '人才供给极低'],
    }, skillOverlap: 18,
  },
]

const demoDiagnoses: JDDiagnosis[] = [
  { id: 'diag-1', positionName: 'AI 算法工程师', jdTitle: '高级 AI 算法工程师', submittedAt: '2026-08-01', inflationIndex: 0.35, missingKeywords: ['联邦学习', '模型压缩'], redundantKeywords: ['Office 办公'], overallScore: 72, status: 'warning' },
  { id: 'diag-2', positionName: '数据分析师', jdTitle: '资深数据分析师', submittedAt: '2026-07-29', inflationIndex: 0.15, missingKeywords: ['A/B 测试'], redundantKeywords: [], overallScore: 88, status: 'healthy' },
  { id: 'diag-3', positionName: 'DevOps 工程师', jdTitle: 'DevOps 技术专家', submittedAt: '2026-07-25', inflationIndex: 0.52, missingKeywords: ['服务网格', 'GitOps'], redundantKeywords: ['PHP', 'Apache'], overallScore: 58, status: 'critical' },
  { id: 'diag-4', positionName: '产品经理', jdTitle: '高级产品经理', submittedAt: '2026-07-22', inflationIndex: 0.28, missingKeywords: ['增长实验', 'AI 产品设计'], redundantKeywords: ['精通 Office 全家桶'], overallScore: 76, status: 'warning' },
  { id: 'diag-5', positionName: '前端工程师', jdTitle: '资深前端工程师', submittedAt: '2026-07-20', inflationIndex: 0.42, missingKeywords: ['WebAssembly', '微前端'], redundantKeywords: ['jQuery', 'IE 兼容'], overallScore: 61, status: 'warning' },
  { id: 'diag-6', positionName: '安全工程师', jdTitle: '安全攻防专家', submittedAt: '2026-07-18', inflationIndex: 0.12, missingKeywords: [], redundantKeywords: [], overallScore: 91, status: 'healthy' },
]

const demoTeamGaps: TeamGap[] = [
  { skillName: 'Kubernetes', requiredLevel: 'advanced', currentAvg: 52, gap: 48, affectedPositions: 3, priority: 'high' },
  { skillName: '联邦学习', requiredLevel: 'intermediate', currentAvg: 15, gap: 85, affectedPositions: 2, priority: 'high' },
  { skillName: 'Terraform', requiredLevel: 'advanced', currentAvg: 38, gap: 62, affectedPositions: 1, priority: 'medium' },
  { skillName: '性能优化', requiredLevel: 'intermediate', currentAvg: 55, gap: 45, affectedPositions: 2, priority: 'medium' },
  { skillName: '安全测试', requiredLevel: 'basic', currentAvg: 30, gap: 70, affectedPositions: 1, priority: 'low' },
]

// 人才需求预测 Demo 数据（趋势外推 · 90 天语料窗口）
const demoForecast: TalentForecast = {
  emerging: [
    { name: '大模型微调', score: 0.92, phase: 'hot' },
    { name: 'RAG 应用', score: 0.88, phase: 'hot' },
    { name: 'Agent 编排', score: 0.84, phase: 'hot' },
    { name: '端侧 AI', score: 0.78, phase: 'rising' },
    { name: '模型量化压缩', score: 0.74, phase: 'rising' },
    { name: '联邦学习', score: 0.71, phase: 'rising' },
    { name: 'MLOps', score: 0.66, phase: 'rising' },
    { name: '智能体工程', score: 0.62, phase: 'new' },
    { name: 'AI 测试', score: 0.58, phase: 'new' },
    { name: '数据安全合规', score: 0.54, phase: 'new' },
  ],
  cooling: [
    { name: '传统 CV 特征工程', score: 0.86, phase: 'cooling' },
    { name: '数据标注', score: 0.78, phase: 'cooling' },
    { name: '规则引擎', score: 0.72, phase: 'cooling' },
    { name: '传统 BI 报表', score: 0.65, phase: 'cooling' },
    { name: '手工测试执行', score: 0.55, phase: 'cooling' },
    { name: '静态页面开发', score: 0.48, phase: 'fading' },
    { name: '传统数仓建模', score: 0.42, phase: 'fading' },
    { name: '原生混合开发', score: 0.36, phase: 'fading' },
    { name: '传统关系型调优', score: 0.30, phase: 'fading' },
  ],
  recommendation: '建议优先招聘/培训：大模型微调、RAG 应用、Agent 编排、端侧 AI、模型量化压缩；数据标注 / 手工测试执行 建议转岗转型培训。',
}

// ── 人才库 Demo 数据（8 名候选人 · 与后端 CANDIDATES 对齐）──

const demoTalentDetails: Record<string, TalentDetail> = {
  cand_li_wei: {
    id: 'cand_li_wei',
    profile: { name: '李伟', title: '高级后端开发工程师', targetRole: '资深后端工程师', targetCity: '上海', city: '上海', industry: '互联网/IT', experienceYears: '8-10年', education: '本科', major: '计算机科学与技术', englishLevel: 'CET-6', salaryMin: 35, salaryMax: 55, workMode: 'hybrid', relocateOk: true, travelOk: false, avatarEmoji: '🧑‍💻' },
    skills: [
      { name: 'Go', category: '编程语言', level: 'expert', freshness: 92, yearsOfExperience: 8, marketDemand: 90, status: 'healthy' },
      { name: '系统设计', category: '架构', level: 'expert', freshness: 82, yearsOfExperience: 8, marketDemand: 82, status: 'healthy' },
      { name: 'MySQL', category: '数据', level: 'expert', freshness: 85, yearsOfExperience: 8, marketDemand: 80, status: 'healthy' },
      { name: 'Kubernetes', category: 'DevOps', level: 'advanced', freshness: 78, yearsOfExperience: 4, marketDemand: 85, status: 'healthy' },
      { name: 'Kafka', category: '中间件', level: 'intermediate', freshness: 60, yearsOfExperience: 3, marketDemand: 70, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-go-senior', positionName: '资深后端工程师', company: '某云原生平台', matchRate: 88, matchedSkills: ['Go', '系统设计', 'Kubernetes'], missingSkills: ['Rust', 'eBPF'], salaryRange: '45-82K' },
      { positionId: 'pos-platform', positionName: '平台工程师', company: '某互联网大厂', matchRate: 82, matchedSkills: ['Go', 'Kubernetes', 'Redis'], missingSkills: ['云原生安全'], salaryRange: '40-70K' },
    ],
    annotation: { favorite: true, hrStatus: 'shortlisted', note: '重点跟进：系统设计+Go 双栈资深', updatedAt: '2026-08-28T10:00:00' },
  },
  cand_wang_fang: {
    id: 'cand_wang_fang',
    profile: { name: '王芳', title: 'AI 算法工程师', targetRole: '大模型算法工程师', targetCity: '北京', city: '北京', industry: '互联网/IT', experienceYears: '5-8年', education: '硕士', major: '模式识别与智能系统', englishLevel: 'IELTS 7.0', salaryMin: 40, salaryMax: 65, workMode: 'remote', relocateOk: false, travelOk: false, avatarEmoji: '👩‍💻' },
    skills: [
      { name: 'Python', category: '编程语言', level: 'expert', freshness: 90, yearsOfExperience: 7, marketDemand: 92, status: 'healthy' },
      { name: 'NLP', category: 'AI/ML', level: 'expert', freshness: 88, yearsOfExperience: 6, marketDemand: 88, status: 'healthy' },
      { name: 'LLM 微调', category: 'AI/ML', level: 'advanced', freshness: 95, yearsOfExperience: 3, marketDemand: 95, status: 'healthy' },
      { name: 'PyTorch', category: 'AI/ML', level: 'advanced', freshness: 85, yearsOfExperience: 5, marketDemand: 90, status: 'healthy' },
      { name: 'RAG', category: 'AI/ML', level: 'intermediate', freshness: 80, yearsOfExperience: 2, marketDemand: 88, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-llm', positionName: '大模型算法工程师', company: '某头部大模型公司', matchRate: 90, matchedSkills: ['Python', 'NLP', 'RAG'], missingSkills: ['分布式训练'], salaryRange: '60-90K' },
      { positionId: 'pos-ml-eng', positionName: 'ML Engineer', company: '某 AI 独角兽', matchRate: 85, matchedSkills: ['Python', 'PyTorch', 'NLP'], missingSkills: ['MLOps'], salaryRange: '45-80K' },
    ],
    annotation: { favorite: false, hrStatus: 'interviewing', note: '', updatedAt: '2026-08-27T14:30:00' },
  },
  cand_chen_jie: {
    id: 'cand_chen_jie',
    profile: { name: '陈杰', title: '资深前端开发工程师', targetRole: '前端架构工程师', targetCity: '杭州', city: '杭州', industry: '互联网/IT', experienceYears: '5-8年', education: '本科', major: '软件工程', englishLevel: 'CET-6', salaryMin: 28, salaryMax: 45, workMode: 'hybrid', relocateOk: true, travelOk: true, avatarEmoji: '🧑‍💻' },
    skills: [
      { name: 'TypeScript', category: '前端', level: 'expert', freshness: 88, yearsOfExperience: 6, marketDemand: 80, status: 'healthy' },
      { name: 'React', category: '前端', level: 'expert', freshness: 85, yearsOfExperience: 6, marketDemand: 78, status: 'healthy' },
      { name: '微前端', category: '架构', level: 'advanced', freshness: 82, yearsOfExperience: 3, marketDemand: 70, status: 'healthy' },
      { name: 'Vue', category: '前端', level: 'advanced', freshness: 78, yearsOfExperience: 4, marketDemand: 72, status: 'healthy' },
      { name: 'Node.js', category: '后端', level: 'intermediate', freshness: 70, yearsOfExperience: 3, marketDemand: 75, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-fe-arch', positionName: '前端架构工程师', company: '某大型金融科技集团', matchRate: 89, matchedSkills: ['TypeScript', 'React', '微前端'], missingSkills: ['Webpack 性能调优'], salaryRange: '35-60K' },
      { positionId: 'pos-fullstack', positionName: '全栈开发工程师', company: '某一线互联网大厂', matchRate: 83, matchedSkills: ['TypeScript', 'React', 'Node.js'], missingSkills: ['AWS'], salaryRange: '30-50K' },
    ],
    annotation: { favorite: false, hrStatus: '', note: '', updatedAt: null },
  },
  cand_liu_yang: {
    id: 'cand_liu_yang',
    profile: { name: '刘洋', title: '数据分析师', targetRole: '数据产品经理 / AI BI', targetCity: '深圳', city: '深圳', industry: '互联网/IT', experienceYears: '3-5年', education: '本科', major: '统计学', englishLevel: 'CET-6', salaryMin: 18, salaryMax: 30, workMode: 'hybrid', relocateOk: true, travelOk: false, avatarEmoji: '🧑‍💻' },
    skills: [
      { name: 'SQL', category: '数据', level: 'advanced', freshness: 80, yearsOfExperience: 4, marketDemand: 75, status: 'healthy' },
      { name: 'Pandas', category: '数据', level: 'advanced', freshness: 75, yearsOfExperience: 3, marketDemand: 70, status: 'healthy' },
      { name: 'Python', category: '编程语言', level: 'intermediate', freshness: 72, yearsOfExperience: 3, marketDemand: 92, status: 'healthy' },
      { name: 'A/B 实验', category: '数据', level: 'intermediate', freshness: 70, yearsOfExperience: 2, marketDemand: 72, status: 'healthy' },
      { name: 'Tableau', category: '数据', level: 'intermediate', freshness: 65, yearsOfExperience: 2, marketDemand: 65, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-data-analyst', positionName: '数据分析师', company: '某电商平台', matchRate: 86, matchedSkills: ['SQL', 'Python', 'Pandas'], missingSkills: ['A/B 实验'], salaryRange: '20-35K' },
    ],
    annotation: { favorite: false, hrStatus: '', note: '', updatedAt: null },
  },
  cand_zhao_min: {
    id: 'cand_zhao_min',
    profile: { name: '赵敏', title: 'DevOps 工程师', targetRole: '平台工程架构师', targetCity: '北京', city: '北京', industry: '互联网/IT', experienceYears: '6-8年', education: '本科', major: '自动化', englishLevel: 'CET-6', salaryMin: 32, salaryMax: 55, workMode: 'onsite', relocateOk: false, travelOk: true, avatarEmoji: '🧑‍💻' },
    skills: [
      { name: 'Linux', category: '操作系统', level: 'expert', freshness: 92, yearsOfExperience: 7, marketDemand: 80, status: 'healthy' },
      { name: 'CI/CD', category: 'DevOps', level: 'expert', freshness: 90, yearsOfExperience: 6, marketDemand: 78, status: 'healthy' },
      { name: 'Kubernetes', category: 'DevOps', level: 'expert', freshness: 88, yearsOfExperience: 5, marketDemand: 85, status: 'healthy' },
      { name: 'Docker', category: 'DevOps', level: 'expert', freshness: 85, yearsOfExperience: 6, marketDemand: 82, status: 'healthy' },
      { name: 'Terraform', category: 'DevOps', level: 'advanced', freshness: 80, yearsOfExperience: 3, marketDemand: 80, status: 'healthy' },
      { name: '可观测性', category: 'DevOps', level: 'advanced', freshness: 78, yearsOfExperience: 4, marketDemand: 75, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-devops', positionName: 'DevOps 工程师', company: '某大型云服务商', matchRate: 90, matchedSkills: ['Kubernetes', 'Terraform', 'CI/CD'], missingSkills: ['服务网格'], salaryRange: '45-75K' },
      { positionId: 'pos-sre', positionName: 'SRE 工程师', company: '某金融科技集团', matchRate: 84, matchedSkills: ['Kubernetes', 'Linux', '可观测性'], missingSkills: ['SRE 方法论'], salaryRange: '40-68K' },
    ],
    annotation: { favorite: true, hrStatus: 'offered', note: 'Offer 已发，等待反馈', updatedAt: '2026-08-26T09:15:00' },
  },
  cand_sun_yue: {
    id: 'cand_sun_yue',
    profile: { name: '孙悦', title: '测试开发工程师', targetRole: '质量架构工程师 / AI 测试', targetCity: '成都', city: '成都', industry: '互联网/IT', experienceYears: '3-5年', education: '本科', major: '软件工程', englishLevel: 'CET-4', salaryMin: 15, salaryMax: 25, workMode: 'hybrid', relocateOk: true, travelOk: false, avatarEmoji: '👩‍💻' },
    skills: [
      { name: '自动化测试', category: '测试', level: 'expert', freshness: 86, yearsOfExperience: 4, marketDemand: 72, status: 'healthy' },
      { name: 'API 测试', category: '测试', level: 'advanced', freshness: 80, yearsOfExperience: 4, marketDemand: 68, status: 'healthy' },
      { name: 'Playwright', category: '测试', level: 'advanced', freshness: 78, yearsOfExperience: 3, marketDemand: 70, status: 'healthy' },
      { name: 'SQL', category: '数据', level: 'intermediate', freshness: 70, yearsOfExperience: 3, marketDemand: 75, status: 'healthy' },
      { name: '性能测试', category: '测试', level: 'intermediate', freshness: 65, yearsOfExperience: 2, marketDemand: 65, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-qa', positionName: 'QA 工程师', company: '某大型电商', matchRate: 88, matchedSkills: ['自动化测试', 'Playwright', 'API 测试'], missingSkills: ['性能分析'], salaryRange: '18-30K' },
    ],
    annotation: { favorite: false, hrStatus: '', note: '', updatedAt: null },
  },
  cand_zhou_qi: {
    id: 'cand_zhou_qi',
    profile: { name: '周琪', title: '初级全栈开发工程师', targetRole: '全栈工程师', targetCity: '广州', city: '广州', industry: '互联网/IT', experienceYears: '1-3年', education: '本科', major: '计算机科学', englishLevel: 'CET-6', salaryMin: 12, salaryMax: 20, workMode: 'hybrid', relocateOk: true, travelOk: false, avatarEmoji: '🧑‍💻' },
    skills: [
      { name: 'JavaScript', category: '前端', level: 'advanced', freshness: 80, yearsOfExperience: 2, marketDemand: 85, status: 'healthy' },
      { name: 'Vue', category: '前端', level: 'intermediate', freshness: 75, yearsOfExperience: 2, marketDemand: 72, status: 'healthy' },
      { name: 'Node.js', category: '后端', level: 'intermediate', freshness: 70, yearsOfExperience: 1.5, marketDemand: 75, status: 'healthy' },
      { name: 'MongoDB', category: '数据', level: 'intermediate', freshness: 65, yearsOfExperience: 1, marketDemand: 65, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-fullstack-jr', positionName: '全栈开发工程师', company: '某创业公司', matchRate: 79, matchedSkills: ['JavaScript', 'Vue', 'Node.js'], missingSkills: ['React', '微服务'], salaryRange: '15-25K' },
    ],
    annotation: { favorite: false, hrStatus: '', note: '', updatedAt: null },
  },
  cand_wu_jun: {
    id: 'cand_wu_jun',
    profile: { name: '吴军', title: '数据工程师', targetRole: '大数据平台架构师', targetCity: '南京', city: '南京', industry: '互联网/IT', experienceYears: '5-8年', education: '本科', major: '计算机科学', englishLevel: 'CET-6', salaryMin: 25, salaryMax: 40, workMode: 'hybrid', relocateOk: true, travelOk: true, avatarEmoji: '🧑‍💻' },
    skills: [
      { name: 'SQL', category: '数据', level: 'expert', freshness: 85, yearsOfExperience: 7, marketDemand: 75, status: 'healthy' },
      { name: 'Spark', category: '数据', level: 'expert', freshness: 88, yearsOfExperience: 5, marketDemand: 85, status: 'healthy' },
      { name: 'Hive', category: '数据', level: 'expert', freshness: 84, yearsOfExperience: 6, marketDemand: 65, status: 'healthy' },
      { name: 'Python', category: '编程语言', level: 'advanced', freshness: 80, yearsOfExperience: 5, marketDemand: 92, status: 'healthy' },
      { name: 'Flink', category: '数据', level: 'advanced', freshness: 82, yearsOfExperience: 3, marketDemand: 82, status: 'healthy' },
      { name: 'Kafka', category: '中间件', level: 'advanced', freshness: 78, yearsOfExperience: 4, marketDemand: 70, status: 'healthy' },
    ],
    matches: [
      { positionId: 'pos-data-eng', positionName: '数据工程师', company: '某大型电商', matchRate: 87, matchedSkills: ['SQL', 'Python', 'Spark'], missingSkills: ['实时数仓'], salaryRange: '28-45K' },
    ],
    annotation: { favorite: false, hrStatus: 'archived', note: '薪资预期偏高，暂存档', updatedAt: '2026-08-25T16:40:00' },
  },
}

function toTalentCandidate(d: TalentDetail): TalentCandidate {
  return {
    id: d.id,
    name: d.profile.name,
    title: d.profile.title,
    targetRole: d.profile.targetRole,
    city: d.profile.city,
    experienceYears: d.profile.experienceYears,
    education: d.profile.education,
    salaryMin: d.profile.salaryMin,
    salaryMax: d.profile.salaryMax,
    skillCount: d.skills.length,
    topSkills: d.skills.slice(0, 3).map(s => s.name),
    bestMatchRate: Math.max(...d.matches.map(m => m.matchRate), 0),
    favorite: d.annotation.favorite,
    hrStatus: d.annotation.hrStatus,
    note: d.annotation.note,
    updatedAt: d.annotation.updatedAt,
  }
}

const demoTalentCandidates: TalentCandidate[] = Object.values(demoTalentDetails).map(toTalentCandidate)

// ── 企业侧「当前登录企业」档案 Demo（云启科技 —— 与后端种子一致，仅作为离线兜底）──

const demoEnterpriseProfile: EnterpriseProfile = {
  enterpriseId: 'demo_ent',
  name: '云启智能科技有限公司',
  shortName: '云启智能',
  logoEmoji: '🚀',
  uscc: '91110108MA01KJ7X2P',
  nature: '民营',
  industry: '人工智能 · 企业服务',
  foundedYear: 2015,
  headcount: '500-999人',
  financing: 'C 轮',
  city: '北京',
  address: '北京市海淀区中关村软件园 9 号楼',
  website: 'https://www.yunqi.tech',
  description: '云启智能是一家专注企业级 AI 平台与智能招聘系统的科技公司。以 LLM/RAG 技术为底座，为大型企业提供岗位能力图谱、人岗匹配与人才洞察服务。在招岗位覆盖后端 / AI 算法 / 前端架构 / 数据分析 / 平台工程 / 质量架构 / 全栈 / 大数据等方向。',
  tags: ['弹性工作', '六险一金', '扁平管理', '股票期权', '免费三餐', '年度体检'],
  techStack: ['Go', 'Python', 'Kubernetes', 'RAG / LLM', '大数据'],
  hiringChannels: ['BOSS 直聘', '猎聘', '校招官网', '内推渠道'],
  hrName: '沈静',
  hrTitle: '招聘总监',
  hrPhone: '010-89012345',
  hrEmail: 'hr@yunqi.tech',
  createdAt: null,
  updatedAt: '2026-08-30T09:00:00',
}

// ── 全岗位演化时间轴 Demo 数据 ──

const demoEvolutions: Record<string, PositionEvolution> = {
  'pos-1': {
    positionId: 'pos-1', positionName: 'AI 算法工程师',
    timeline: [
      {
        date: '2021Q1', label: '2021年第一季度', marketDemand: 55, matchRate: 80,
        salaryRange: '25-45K', adoptionRate: 30,
        tools: ['Scikit-learn', 'TensorFlow 1.x', 'Jupyter', 'Pandas'],
        marketContext: 'AI行业处于深度学习红利期，CV/NLP 两条赛道并进。BERT 发布3年，Transformer 架构已成主流。传统 ML 工程师需求稳定。',
        industryEvents: ['GPT-3 发布 (2020.06)', 'AlphaFold 突破蛋白质折叠 (2020.11)', '中国新基建政策推动 AI 基础设施'],
        typicalProjects: ['推荐系统优化', '图像分类模型部署', 'NLP 文本分类'],
        summary: '传统机器学习为主，深度学习刚开始渗透企业级应用',
        dataSources: ['招聘JD(85份)', '行业报告(2份)', '学术论文(8篇)'],
        skills: [
          { name: 'Python', level: 'advanced', weight: 0.30, freshness: 90, change: 'unchanged' },
          { name: '机器学习', level: 'advanced', weight: 0.35, freshness: 88, change: 'unchanged' },
          { name: 'SQL', level: 'intermediate', weight: 0.15, freshness: 85, change: 'unchanged' },
          { name: '统计学', level: 'advanced', weight: 0.20, freshness: 82, change: 'unchanged' },
        ],
      },
      {
        date: '2022Q1', label: '2022年第一季度', marketDemand: 62, matchRate: 75,
        salaryRange: '30-50K', adoptionRate: 45,
        tools: ['PyTorch', 'TensorFlow 2.x', 'HuggingFace Transformers', 'MLflow'],
        marketContext: '深度学习框架之争 PyTorch 胜出。HuggingFace 生态爆发，Transformer 模型平民化。Stable Diffusion 引发 AIGC 第一波浪潮。',
        industryEvents: ['Stable Diffusion 开源 (2022.08)', 'ChatGPT 研发中 (OpenAI 内部)', '中国 AI 大模型专项启动'],
        typicalProjects: ['目标检测系统', '文本生成应用', '模型压缩与量化'],
        summary: '深度学习需求显著上升，PyTorch/TensorFlow 成为标配，传统 SQL 权重下降',
        dataSources: ['招聘JD(128份)', '行业报告(3份)'],
        skills: [
          { name: 'Python', level: 'expert', weight: 0.25, freshness: 92, change: 'upgraded', changeReason: '深度学习项目对Python能力要求升级' },
          { name: '机器学习', level: 'advanced', weight: 0.25, freshness: 85, change: 'unchanged' },
          { name: '深度学习', level: 'intermediate', weight: 0.20, freshness: 78, change: 'added', changeReason: 'Transformer/CNN 在工业界大规模落地' },
          { name: 'SQL', level: 'intermediate', weight: 0.10, freshness: 80, change: 'downgraded', changeReason: '数据工程团队分流，算法岗SQL需求降低' },
          { name: '统计学', level: 'advanced', weight: 0.20, freshness: 80, change: 'unchanged' },
        ],
      },
      {
        date: '2023Q1', label: '2023年第一季度', marketDemand: 75, matchRate: 70,
        salaryRange: '35-60K', adoptionRate: 60,
        tools: ['PyTorch 2.0', 'LangChain', 'HuggingFace', 'Ray', 'Weights & Biases'],
        marketContext: 'ChatGPT 发布引爆全球 AI 竞赛。中国百模大战开启。LangChain 让 LLM 应用开发门槛骤降。Vector DB 成为新基础设施。',
        industryEvents: ['ChatGPT 发布 (2022.11)', 'GPT-4 发布 (2023.03)', '中国百模大战（百度/阿里/讯飞等）', 'Llama 开源引发本地部署潮'],
        typicalProjects: ['LLM 应用开发', 'RAG 检索增强系统', '模型微调与对齐'],
        summary: '大模型浪潮前夕，NLP 需求激增，深度学习成为核心技能',
        dataSources: ['招聘JD(215份)', '行业报告(5份)', '学术论文(12篇)'],
        skills: [
          { name: 'Python', level: 'expert', weight: 0.20, freshness: 90, change: 'unchanged' },
          { name: '机器学习', level: 'advanced', weight: 0.20, freshness: 82, change: 'unchanged' },
          { name: '深度学习', level: 'advanced', weight: 0.25, freshness: 85, change: 'upgraded', changeReason: '大模型训练需要更深的DL功底' },
          { name: 'NLP', level: 'intermediate', weight: 0.15, freshness: 72, change: 'added', changeReason: 'LLM 热潮推动 NLP 需求暴涨' },
          { name: 'SQL', level: 'basic', weight: 0.05, freshness: 70, change: 'downgraded' },
          { name: '统计学', level: 'intermediate', weight: 0.10, freshness: 75, change: 'downgraded' },
          { name: '分布式训练', level: 'basic', weight: 0.05, freshness: 60, change: 'added', changeReason: '大模型需要多卡/多机并行训练' },
        ],
      },
      {
        date: '2024Q1', label: '2024年第一季度', marketDemand: 88, matchRate: 72,
        salaryRange: '40-75K', adoptionRate: 75,
        tools: ['PyTorch 2.x', 'vLLM', 'LangChain/LlamaIndex', 'Kubeflow', 'Triton Inference Server', 'DSPy'],
        marketContext: '大模型全面渗透企业。RAG 架构成为标配。Agent/Function Calling 让 LLM 从对话走向行动。MLOps 从可选变为必备。GPU 算力紧缺。',
        industryEvents: ['Claude 3 发布', 'Gemini 发布', '中国大模型备案制度落地', 'Sora 发布引爆视频生成', '开源模型性能逼近 GPT-3.5'],
        typicalProjects: ['企业 RAG 知识库', 'Agent 自动化工作流', 'LLM 推理优化', '多模态内容理解'],
        summary: '大模型全面爆发，LLM 微调/RLHF 成为必备，MLOps 从可选变为必须',
        dataSources: ['招聘JD(342份)', '行业报告(8份)', '学术论文(25篇)', '课程大纲(15份)'],
        skills: [
          { name: 'Python', level: 'expert', weight: 0.18, freshness: 92, change: 'unchanged' },
          { name: '机器学习', level: 'advanced', weight: 0.15, freshness: 80, change: 'unchanged' },
          { name: '深度学习', level: 'expert', weight: 0.22, freshness: 90, change: 'upgraded', changeReason: 'LLM 架构理解要求达到专家级' },
          { name: 'NLP', level: 'advanced', weight: 0.15, freshness: 82, change: 'upgraded', changeReason: 'Prompt Engineering + RAG 成为日常技能' },
          { name: 'LLM 微调', level: 'intermediate', weight: 0.12, freshness: 75, change: 'added', changeReason: 'LoRA/QLoRA 微调成为岗位标配' },
          { name: 'MLOps', level: 'basic', weight: 0.08, freshness: 65, change: 'added', changeReason: '模型生命周期管理需求激增' },
          { name: '分布式训练', level: 'intermediate', weight: 0.10, freshness: 70, change: 'upgraded', changeReason: '多节点训练常态化' },
          { name: 'SQL', level: 'basic', weight: 0.00, freshness: 40, change: 'removed', changeReason: '数据预处理完全交由数据工程团队' },
        ],
      },
      {
        date: '2025Q1', label: '2025年第一季度', marketDemand: 92, matchRate: 68,
        salaryRange: '45-85K', adoptionRate: 85,
        tools: ['PyTorch 2.x', 'DSPy', 'LangGraph', 'CrewAI', 'MLflow 2.x', 'BentoML', 'Ollama'],
        marketContext: 'Agent 编排框架大爆发。多模态模型成为新范式。合成数据 + RLHF 迭代闭环成熟。企业从"要不要上 AI"变为"怎么大规模上 AI"。',
        industryEvents: ['DeepSeek-R1 发布震撼全球', 'Claude 4 发布', '中国 AI Agent 创业潮', '多模态大模型成为标配', 'AI 安全治理框架出台'],
        typicalProjects: ['多 Agent 协作系统', '多模态内容审核', '端侧模型部署', 'AI Safety 对齐'],
        summary: '多模态/Agent 成为新热点，MLOps 升级为中级必备，传统 ML 被 LLM 范式取代',
        dataSources: ['招聘JD(401份)', '行业报告(12份)', '学术论文(30篇)', '课程大纲(22份)'],
        skills: [
          { name: 'Python', level: 'expert', weight: 0.15, freshness: 94, change: 'unchanged' },
          { name: '深度学习', level: 'expert', weight: 0.20, freshness: 92, change: 'unchanged' },
          { name: 'NLP', level: 'advanced', weight: 0.12, freshness: 85, change: 'unchanged' },
          { name: 'LLM 微调', level: 'advanced', weight: 0.15, freshness: 84, change: 'upgraded', changeReason: 'RLHF/DPO 对齐技术成为高级工程师标配' },
          { name: '多模态 AI', level: 'intermediate', weight: 0.10, freshness: 70, change: 'added', changeReason: '视觉-语言模型应用爆发' },
          { name: 'AI Agent', level: 'basic', weight: 0.08, freshness: 62, change: 'added', changeReason: '自主 Agent 成为企业降本增效新方向' },
          { name: 'MLOps', level: 'intermediate', weight: 0.12, freshness: 78, change: 'upgraded', changeReason: '模型监控/回滚/AB测试成为必备流程' },
          { name: '分布式训练', level: 'advanced', weight: 0.08, freshness: 76, change: 'upgraded' },
          { name: '机器学习', level: 'intermediate', weight: 0.00, freshness: 55, change: 'removed', changeReason: '传统ML方法论被LLM新范式替代' },
        ],
      },
      {
        date: '2026Q3', label: '2026年第三季度 (当前)', marketDemand: 94, matchRate: 72,
        salaryRange: '50-95K', adoptionRate: 92,
        tools: ['PyTorch 2.5', 'vLLM/SGLang', 'LangGraph', 'Agent SDK', '联邦学习框架', '模型压缩工具链'],
        marketContext: 'AI 行业进入平台期后的精细化阶段。端侧 AI + 隐私计算成为新增长点。模型压缩/量化让 AI 部署成本下降 10x。联邦学习在金融/医疗合规场景落地。',
        industryEvents: ['讯飞星火 X2 发布 (2026.02)', '端侧 AI 芯片爆发', 'AI 人才缺口达 500万', '模型蒸馏技术成熟', '中国 AI 应用市场超万亿'],
        typicalProjects: ['端侧 AI 部署', '隐私保护机器学习', '模型蒸馏与压缩', '联邦学习系统', 'AI Agent 企业级落地'],
        summary: '端侧 AI/联邦学习/模型压缩成为新需求，AI Agent 升级为中级，行业进入精细化阶段',
        dataSources: ['招聘JD(352份)', '行业报告(15份)', '学术论文(28篇)', '课程大纲(30份)', '竞品分析(5份)'],
        skills: [
          { name: 'Python', level: 'expert', weight: 0.12, freshness: 95, change: 'unchanged' },
          { name: '深度学习', level: 'expert', weight: 0.18, freshness: 93, change: 'unchanged' },
          { name: 'NLP', level: 'advanced', weight: 0.10, freshness: 88, change: 'unchanged' },
          { name: 'LLM 微调', level: 'expert', weight: 0.15, freshness: 90, change: 'upgraded', changeReason: '模型蒸馏+量化成为降本核心手段' },
          { name: '多模态 AI', level: 'advanced', weight: 0.12, freshness: 78, change: 'upgraded', changeReason: '视觉-语言-语音统一建模需求增长' },
          { name: 'AI Agent', level: 'intermediate', weight: 0.10, freshness: 72, change: 'upgraded', changeReason: 'Multi-Agent 协作架构在金融/客服/研发落地' },
          { name: 'MLOps', level: 'advanced', weight: 0.10, freshness: 82, change: 'upgraded', changeReason: '全流程自动化+监控成为企业级要求' },
          { name: '联邦学习', level: 'intermediate', weight: 0.08, freshness: 68, change: 'added', changeReason: '数据隐私法规趋严，联邦学习成为合规必备' },
          { name: '模型压缩', level: 'basic', weight: 0.05, freshness: 55, change: 'added', changeReason: '端侧部署需求推动模型量化/剪枝/蒸馏技术' },
        ],
      },
    ],
  },

  // ── pos-2: 全栈开发工程师 ──
  'pos-2': { positionId: 'pos-2', positionName: '全栈开发工程师', timeline: [
    { date:'2019Q1',label:'2019年第一季度',marketDemand:70,matchRate:88,salaryRange:'18-30K',adoptionRate:75,tools:['jQuery','Bootstrap','PHP/Laravel','MySQL','Apache'],marketContext:'Web 2.0成熟期，LAMP架构仍是主流。前后端分离刚开始流行。',industryEvents:['React Hooks发布','Vue 3.0预告','Docker成为开发标配'],typicalProjects:['企业官网/后台管理系统','电商平台'],summary:'LAMP+jQuery时代，前后端分离刚兴起',dataSources:['招聘JD(95份)','行业报告(2份)'],skills:[{name:'JavaScript',level:'advanced',weight:0.25,freshness:80,change:'unchanged'},{name:'PHP',level:'advanced',weight:0.25,freshness:85,change:'unchanged'},{name:'MySQL',level:'advanced',weight:0.20,freshness:88,change:'unchanged'},{name:'HTML/CSS',level:'advanced',weight:0.20,freshness:82,change:'unchanged'},{name:'Linux',level:'intermediate',weight:0.10,freshness:80,change:'unchanged'}]},
    { date:'2021Q1',label:'2021年第一季度',marketDemand:78,matchRate:85,salaryRange:'22-40K',adoptionRate:80,tools:['React 17','Vue 3','Node.js','PostgreSQL','Docker','AWS'],marketContext:'前后端分离成为标准。React/Vue全面取代jQuery。Node.js中间层BFF模式盛行。',industryEvents:['Vue 3.0正式发布','Next.js 10发布','Serverless潮流'],typicalProjects:['SPA单页应用','微服务架构迁移'],summary:'React/Vue取代jQuery，Node.js BFF+容器化成为标配',dataSources:['招聘JD(156份)','行业报告(3份)'],skills:[{name:'React/Vue',level:'advanced',weight:0.28,freshness:88,change:'added',changeReason:'SPA框架全面取代jQuery'},{name:'Node.js',level:'intermediate',weight:0.18,freshness:80,change:'added',changeReason:'BFF+SSR成为标配'},{name:'JavaScript',level:'expert',weight:0.22,freshness:90,change:'upgraded'},{name:'MySQL',level:'advanced',weight:0.15,freshness:85,change:'unchanged'},{name:'PHP',level:'intermediate',weight:0.10,freshness:70,change:'downgraded',changeReason:'Node.js/Go抢占份额'},{name:'HTML/CSS',level:'intermediate',weight:0.07,freshness:75,change:'downgraded'}]},
    { date:'2023Q1',label:'2023年第一季度',marketDemand:82,matchRate:82,salaryRange:'28-50K',adoptionRate:85,tools:['Next.js 13','TypeScript','Prisma','Kubernetes','Vercel'],marketContext:'全栈边界模糊化。TypeScript成为行业标准。Edge Computing兴起。',industryEvents:['Next.js App Router','TypeScript份额超40%','Vercel估值$2.5B'],typicalProjects:['全栈SaaS产品','Edge部署','实时协作工具'],summary:'TypeScript+Next.js全栈框架崛起，Edge Computing改变部署范式',dataSources:['招聘JD(210份)','行业报告(5份)'],skills:[{name:'React/Vue',level:'expert',weight:0.25,freshness:92,change:'upgraded',changeReason:'RSC等新特性要求更高深度'},{name:'TypeScript',level:'advanced',weight:0.22,freshness:88,change:'added',changeReason:'类型安全成为团队协作必备'},{name:'Node.js',level:'advanced',weight:0.18,freshness:85,change:'upgraded'},{name:'MySQL/PostgreSQL',level:'intermediate',weight:0.12,freshness:80,change:'unchanged'},{name:'Docker/K8s',level:'intermediate',weight:0.13,freshness:76,change:'added'},{name:'JavaScript',level:'advanced',weight:0.10,freshness:85,change:'unchanged'}]},
    { date:'2025Q1',label:'2025年第一季度',marketDemand:75,matchRate:87,salaryRange:'30-55K',adoptionRate:78,tools:['Next.js 15','Astro','tRPC','Cloudflare Workers','Bun'],marketContext:'AI编码助手让开发效率翻倍。边缘计算+Serverless成为默认架构。前端工具链洗牌。',industryEvents:['Cursor AI IDE爆火','RSC稳定','AI编码渗透率超60%'],typicalProjects:['AI驱动全栈应用','Edge-Native SaaS'],summary:'AI辅助编程改变岗位要求——从"都会"变为"精通架构+AI工具"',dataSources:['招聘JD(185份)','行业报告(6份)'],skills:[{name:'React/Vue',level:'expert',weight:0.22,freshness:90,change:'unchanged'},{name:'TypeScript',level:'expert',weight:0.22,freshness:92,change:'upgraded'},{name:'Node.js/Bun',level:'advanced',weight:0.16,freshness:82,change:'unchanged'},{name:'Docker/K8s',level:'advanced',weight:0.14,freshness:80,change:'upgraded'},{name:'AI工具链',level:'intermediate',weight:0.12,freshness:70,change:'added',changeReason:'Copilot/Cursor成为效率门槛'},{name:'MySQL',level:'intermediate',weight:0.08,freshness:78,change:'unchanged'},{name:'HTML/CSS',level:'basic',weight:0.06,freshness:72,change:'downgraded'}]},
    { date:'2026Q3',label:'2026年第三季度(当前)',marketDemand:78,matchRate:85,salaryRange:'32-60K',adoptionRate:82,tools:['Next.js/Remix','TypeScript 5.x','Prisma','Kubernetes','Bun 2.x','AI SDKs'],marketContext:'AI-Native开发成为新范式。全栈从"写代码"转为"审代码+搭架构"。边缘计算+Vector DB成为全栈新分支。',industryEvents:['Vercel AI SDK成为标配','Bun 2.0生产可用','全栈+AI薪资溢价40%'],typicalProjects:['AI-Native全栈应用','RAG智能后台','多租户SaaS'],summary:'全栈进化为"AI审代码+架构设计"，边缘计算+AI SDK成为新标配',dataSources:['招聘JD(142份)','行业报告(8份)'],skills:[{name:'React/Vue',level:'expert',weight:0.20,freshness:92,change:'unchanged'},{name:'TypeScript',level:'expert',weight:0.20,freshness:94,change:'unchanged'},{name:'Node.js/Bun',level:'advanced',weight:0.15,freshness:85,change:'unchanged'},{name:'Docker/K8s',level:'advanced',weight:0.13,freshness:82,change:'unchanged'},{name:'AI工具链',level:'advanced',weight:0.14,freshness:76,change:'upgraded',changeReason:'AI SDK+Prompt工程成为核心技能'},{name:'Edge/Serverless',level:'intermediate',weight:0.10,freshness:70,change:'added',changeReason:'边缘计算降低延迟成为产品竞争力'},{name:'MySQL',level:'intermediate',weight:0.08,freshness:80,change:'unchanged'}]},
  ]},

  // ── pos-3: 数据分析师 ──
  'pos-3': { positionId: 'pos-3', positionName: '数据分析师', timeline: [
    { date:'2020Q1',label:'2020年第一季度',marketDemand:65,matchRate:90,salaryRange:'12-22K',adoptionRate:60,tools:['Excel','SQL','Tableau 2019','SPSS','Power BI'],marketContext:'数据驱动决策成为共识。BI工具普及期。Python在数据分析快速渗透。',industryEvents:['Tableau被Salesforce收购','Power BI快速增长','国产BI兴起'],typicalProjects:['销售看板','用户漏斗分析','周报自动化'],summary:'Excel+SQL为主，BI工具快速普及，从报表走向可视化',dataSources:['招聘JD(78份)','行业报告(2份)'],skills:[{name:'SQL',level:'advanced',weight:0.30,freshness:90,change:'unchanged'},{name:'Excel',level:'expert',weight:0.25,freshness:85,change:'unchanged'},{name:'Tableau',level:'intermediate',weight:0.20,freshness:80,change:'unchanged'},{name:'统计学',level:'intermediate',weight:0.15,freshness:82,change:'unchanged'},{name:'Python',level:'basic',weight:0.10,freshness:70,change:'unchanged'}]},
    { date:'2022Q1',label:'2022年第一季度',marketDemand:75,matchRate:82,salaryRange:'18-30K',adoptionRate:72,tools:['SQL','Python(Pandas)','Tableau','Metabase','dbt'],marketContext:'现代数据栈(MDS)概念流行。dbt让分析师参与建模。云数仓加速(Snowflake/BigQuery)。',industryEvents:['dbt成为数据转换标准','Snowflake IPO','ELT普及'],typicalProjects:['用户留存分析','AB实验分析','数据建模(dbt)'],summary:'Python成为必备，dbt让分析师参与建模，云数仓普及',dataSources:['招聘JD(132份)','行业报告(3份)'],skills:[{name:'SQL',level:'expert',weight:0.30,freshness:92,change:'upgraded'},{name:'Python',level:'intermediate',weight:0.22,freshness:82,change:'upgraded'},{name:'Tableau',level:'advanced',weight:0.18,freshness:85,change:'unchanged'},{name:'统计学',level:'intermediate',weight:0.15,freshness:80,change:'unchanged'},{name:'Excel',level:'intermediate',weight:0.10,freshness:78,change:'downgraded'},{name:'数据建模',level:'basic',weight:0.05,freshness:65,change:'added'}]},
    { date:'2024Q1',label:'2024年第一季度',marketDemand:85,matchRate:72,salaryRange:'22-40K',adoptionRate:82,tools:['SQL','Python','dbt','Looker','Jupyter','Streamlit'],marketContext:'AI增强分析成为趋势——自然语言查询+自动洞察。Streamlit让分析师构建数据App。Headless BI新方向。',industryEvents:['自然语言BI兴起','Streamlit被Snowflake收购','Text-to-SQL成熟'],typicalProjects:['LLM自助分析','数据App(Streamlit)','指标体系建设'],summary:'Text-to-SQL+AI增强分析改变工作方式，分析师构建数据App',dataSources:['招聘JD(188份)','行业报告(5份)'],skills:[{name:'SQL',level:'expert',weight:0.28,freshness:94,change:'unchanged'},{name:'Python',level:'advanced',weight:0.24,freshness:88,change:'upgraded'},{name:'Tableau/Looker',level:'advanced',weight:0.15,freshness:82,change:'unchanged'},{name:'统计学',level:'advanced',weight:0.14,freshness:84,change:'unchanged'},{name:'数据建模',level:'intermediate',weight:0.10,freshness:72,change:'upgraded'},{name:'A/B测试',level:'intermediate',weight:0.09,freshness:78,change:'added'}]},
    { date:'2026Q3',label:'2026年第三季度(当前)',marketDemand:85,matchRate:68,salaryRange:'25-48K',adoptionRate:88,tools:['SQL','Python','dbt','AI BI工具','Streamlit','Vector DB'],marketContext:'AI原生分析栈兴起。分析师裂变为"数据产品经理"+"分析工程师"。非结构化数据分析成为新技能。',industryEvents:['AI BI产品涌现','Text-to-Insight成熟','分析师+AI薪资涨35%'],typicalProjects:['AI对话式分析','非结构化数据挖掘','自动化洞察'],summary:'AI原生分析——自然语言查询+自动洞察，非结构化数据成为新竞争力',dataSources:['招聘JD(156份)','行业报告(7份)'],skills:[{name:'SQL',level:'expert',weight:0.25,freshness:95,change:'unchanged'},{name:'Python',level:'advanced',weight:0.24,freshness:90,change:'unchanged'},{name:'AI增强分析',level:'intermediate',weight:0.14,freshness:68,change:'added',changeReason:'LLM自动洞察成为新生产力工具'},{name:'统计学',level:'advanced',weight:0.12,freshness:85,change:'unchanged'},{name:'数据建模',level:'advanced',weight:0.12,freshness:80,change:'upgraded'},{name:'A/B测试',level:'advanced',weight:0.08,freshness:82,change:'unchanged'},{name:'Tableau',level:'intermediate',weight:0.05,freshness:68,change:'downgraded',changeReason:'AI BI替代传统拖拽式BI'}]},
  ]},

  // ── pos-5: DevOps 工程师 ──
  'pos-5': { positionId: 'pos-5', positionName: 'DevOps 工程师', timeline: [
    { date:'2019Q1',label:'2019年第一季度',marketDemand:55,matchRate:88,salaryRange:'18-30K',adoptionRate:40,tools:['Jenkins','Docker','Ansible','Nagios','GitLab CI'],marketContext:'DevOps从概念走向落地。Docker成为容器化标准。CI/CD流水线建设是核心。',industryEvents:['Docker Enterprise被收购','GitHub Actions发布','K8s成为编排标准'],typicalProjects:['CI/CD流水线搭建','容器化迁移','监控告警搭建'],summary:'DevOps落地期——CI/CD+容器化是主旋律',dataSources:['招聘JD(65份)','行业报告(2份)'],skills:[{name:'Linux',level:'expert',weight:0.28,freshness:92,change:'unchanged'},{name:'Docker',level:'advanced',weight:0.24,freshness:88,change:'unchanged'},{name:'Jenkins',level:'advanced',weight:0.20,freshness:85,change:'unchanged'},{name:'Shell/Python',level:'advanced',weight:0.18,freshness:84,change:'unchanged'},{name:'监控',level:'intermediate',weight:0.10,freshness:78,change:'unchanged'}]},
    { date:'2021Q1',label:'2021年第一季度',marketDemand:70,matchRate:78,salaryRange:'25-42K',adoptionRate:60,tools:['Kubernetes','Docker','Terraform','Prometheus/Grafana','ArgoCD'],marketContext:'K8s全面胜利。GitOps理念兴起。IaC成为标准。可观测性取代传统监控。',industryEvents:['CNCF生态爆发','HashiCorp IPO','GitOps成为最佳实践'],typicalProjects:['K8s集群管理','IaC基础设施迁移','可观测性平台'],summary:'K8s+Terraform IaC+GitOps成为新范式',dataSources:['招聘JD(145份)','行业报告(3份)'],skills:[{name:'Kubernetes',level:'intermediate',weight:0.25,freshness:78,change:'added',changeReason:'K8s成为事实标准'},{name:'Docker',level:'advanced',weight:0.20,freshness:88,change:'unchanged'},{name:'Terraform',level:'intermediate',weight:0.18,freshness:75,change:'added',changeReason:'IaC多云管理必备'},{name:'Linux',level:'advanced',weight:0.15,freshness:90,change:'unchanged'},{name:'CI/CD',level:'advanced',weight:0.12,freshness:85,change:'unchanged'},{name:'Jenkins',level:'intermediate',weight:0.10,freshness:75,change:'downgraded',changeReason:'新一代工具替代'}]},
    { date:'2023Q1',label:'2023年第一季度',marketDemand:82,matchRate:70,salaryRange:'32-55K',adoptionRate:78,tools:['Kubernetes','Terraform','ArgoCD','OpenTelemetry','eBPF','Cilium'],marketContext:'平台工程(Platform Engineering)成为新方向。GitOps+IDP理念普及。eBPF改变可观测性。FinOps成为刚需。',industryEvents:['Platform Engineering成为趋势','OpenTelemetry标准','eBPF创业潮'],typicalProjects:['内部开发者平台','服务网格落地','FinOps优化'],summary:'平台工程+GitOps+可观测性三位一体，从运维自动化到开发者赋能',dataSources:['招聘JD(198份)','行业报告(5份)'],skills:[{name:'Kubernetes',level:'advanced',weight:0.25,freshness:86,change:'upgraded',changeReason:'K8s从用→理解原理+调优'},{name:'Terraform',level:'advanced',weight:0.20,freshness:84,change:'upgraded'},{name:'CI/CD',level:'advanced',weight:0.16,freshness:88,change:'unchanged'},{name:'可观测性',level:'intermediate',weight:0.15,freshness:76,change:'added',changeReason:'OTel+eBPF成为新标准'},{name:'Linux',level:'advanced',weight:0.12,freshness:92,change:'unchanged'},{name:'Docker',level:'advanced',weight:0.12,freshness:85,change:'unchanged'}]},
    { date:'2025Q1',label:'2025年第一季度',marketDemand:88,matchRate:65,salaryRange:'38-65K',adoptionRate:85,tools:['Kubernetes','Terraform/CDKTF','OpenTelemetry','Cilium/eBPF','KubeCost','Crossplane'],marketContext:'AI/ML基础设施成为DevOps新疆域——GPU调度、模型部署流水线。安全左移(DevSecOps)成为合规要求。',industryEvents:['GPU调度成为新难题','KubeCon偏向AI Infra','Platform Engineering成熟度发布'],typicalProjects:['MLOps平台搭建','GPU集群管理','零信任安全','多云成本优化'],summary:'AI Infra+平台工程双轮驱动，DevOps进化为AI Platform Engineer',dataSources:['招聘JD(245份)','行业报告(7份)'],skills:[{name:'Kubernetes',level:'expert',weight:0.24,freshness:92,change:'upgraded',changeReason:'GPU调度成为新需求'},{name:'Terraform/CDKTF',level:'advanced',weight:0.18,freshness:86,change:'unchanged'},{name:'可观测性',level:'advanced',weight:0.15,freshness:82,change:'upgraded'},{name:'MLOps/GPU Infra',level:'intermediate',weight:0.12,freshness:68,change:'added',changeReason:'AI训练/推理基础设施成为新战场'},{name:'CI/CD',level:'advanced',weight:0.12,freshness:88,change:'unchanged'},{name:'安全/DevSecOps',level:'intermediate',weight:0.10,freshness:72,change:'added',changeReason:'供应链安全+零信任'},{name:'Linux',level:'advanced',weight:0.09,freshness:90,change:'unchanged'}]},
    { date:'2026Q3',label:'2026年第三季度(当前)',marketDemand:88,matchRate:65,salaryRange:'40-72K',adoptionRate:90,tools:['Kubernetes','Terraform','OpenTelemetry','eBPF','AI Infra','Crossplane'],marketContext:'AI Platform Engineering成为独立岗位。GPU利用率优化成为降本核心。FinOps+GreenOps并重。IDP企业标配。',industryEvents:['AI Infra成为KubeCon主题','GPU虚拟化成熟','GreenOps碳感知调度兴起'],typicalProjects:['AI训练平台','GPU成本优化','内部开发者门户','碳感知调度'],summary:'AI Infra+GPU优化+绿色计算重塑DevOps，平台工程全面产品化',dataSources:['招聘JD(210份)','行业报告(9份)'],skills:[{name:'Kubernetes',level:'expert',weight:0.22,freshness:94,change:'unchanged'},{name:'Terraform/CDKTF',level:'advanced',weight:0.16,freshness:88,change:'unchanged'},{name:'可观测性',level:'advanced',weight:0.14,freshness:85,change:'unchanged'},{name:'MLOps/GPU Infra',level:'advanced',weight:0.16,freshness:74,change:'upgraded',changeReason:'AI推理+模型部署流水线成为日常'},{name:'CI/CD',level:'advanced',weight:0.10,freshness:90,change:'unchanged'},{name:'安全/DevSecOps',level:'advanced',weight:0.12,freshness:78,change:'upgraded',changeReason:'AI供应链安全+数据合规'},{name:'FinOps/GreenOps',level:'intermediate',weight:0.10,freshness:68,change:'added',changeReason:'GPU成本+碳感知成为企业KPI'}]},
  ]},

  // ── pos-4: 技术项目经理 ──
  'pos-4': { positionId: 'pos-4', positionName: '技术项目经理', timeline: [
    { date:'2020Q1',label:'2020年第一季度',marketDemand:60,matchRate:92,salaryRange:'22-38K',adoptionRate:55,tools:['Jira','Confluence','MS Project','Git','Slack'],marketContext:'传统PMP方法论主导。敏捷/Scrum在互联网推广。技术经理多从高级工程师转岗。',industryEvents:['Scrum成为主流','Jira成为标配'],typicalProjects:['瀑布式项目交付','Scrum团队转型'],summary:'PMP+Scrum为主，技术经理多从高级工程师转岗',dataSources:['招聘JD(52份)','行业报告(2份)'],skills:[{name:'项目管理',level:'advanced',weight:0.30,freshness:85,change:'unchanged'},{name:'技术架构',level:'intermediate',weight:0.25,freshness:80,change:'unchanged'},{name:'团队管理',level:'intermediate',weight:0.25,freshness:82,change:'unchanged'},{name:'沟通协调',level:'advanced',weight:0.20,freshness:88,change:'unchanged'}]},
    { date:'2022Q1',label:'2022年第一季度',marketDemand:68,matchRate:88,salaryRange:'28-48K',adoptionRate:65,tools:['Jira','Linear','Notion','Figma','GitHub Projects'],marketContext:'远程办公推动异步沟通+文档驱动。Data-Informed决策文化兴起。TMS作为独立学科被认可。',industryEvents:['远程办公工具爆发','Linear重新定义PM体验','技术管理成为独立学科'],typicalProjects:['异地团队协调','OKR落地','技术债务治理'],summary:'远程办公+数据驱动改变管理方式，技术管理独立化',dataSources:['招聘JD(88份)','行业报告(3份)'],skills:[{name:'项目管理',level:'advanced',weight:0.25,freshness:86,change:'unchanged'},{name:'技术架构',level:'advanced',weight:0.25,freshness:82,change:'upgraded'},{name:'团队管理',level:'advanced',weight:0.28,freshness:84,change:'upgraded',changeReason:'远程管理成为必备'},{name:'数据驱动',level:'basic',weight:0.12,freshness:72,change:'added',changeReason:'Engineering Metrics推动数据化'},{name:'沟通协调',level:'advanced',weight:0.10,freshness:88,change:'unchanged'}]},
    { date:'2024Q1',label:'2024年第一季度',marketDemand:72,matchRate:85,salaryRange:'32-55K',adoptionRate:72,tools:['Linear','Notion','DORA Metrics','AI管理工具','Figma'],marketContext:'AI辅助项目管理工具涌现。DORA/SPACE等工程效率度量成为TPM必备。DevEx成为新关注点。',industryEvents:['AI项目管理系统','DORA指标成为标准','Platform Engineering改变协作模式'],typicalProjects:['工程效率提升','AI辅助决策','跨部门平台工程'],summary:'AI辅助管理+工程效率度量成为TPM核心竞争力，DevEx新焦点',dataSources:['招聘JD(105份)','行业报告(4份)'],skills:[{name:'技术架构',level:'advanced',weight:0.26,freshness:84,change:'unchanged'},{name:'工程效率',level:'intermediate',weight:0.20,freshness:76,change:'added',changeReason:'DORA/SPACE成为管理依据'},{name:'团队管理',level:'advanced',weight:0.22,freshness:86,change:'unchanged'},{name:'项目管理',level:'advanced',weight:0.18,freshness:85,change:'unchanged'},{name:'AI工具应用',level:'basic',weight:0.08,freshness:62,change:'added'},{name:'风险管理',level:'intermediate',weight:0.06,freshness:80,change:'unchanged'}]},
    { date:'2026Q3',label:'2026年第三季度(当前)',marketDemand:70,matchRate:90,salaryRange:'35-62K',adoptionRate:75,tools:['Linear','AI管理助手','DORA/Space平台','Notion AI'],marketContext:'AI Agent开始参与项目管理——自动化任务分配。TPM从"管人管事"转向"管系统+数据+AI"。',industryEvents:['AI Agent参与项目管理','DevEx成为组织竞争力','TPM与AI战略融合'],typicalProjects:['AI Agent项目协作','DevEx度量改进','工程效能平台'],summary:'AI Agent参与管理——TPM从管人转向管系统+数据+AI',dataSources:['招聘JD(78份)','行业报告(5份)'],skills:[{name:'技术架构',level:'advanced',weight:0.24,freshness:86,change:'unchanged'},{name:'工程效率/DevEx',level:'advanced',weight:0.22,freshness:80,change:'upgraded',changeReason:'DevEx成为产出关键变量'},{name:'团队管理',level:'advanced',weight:0.20,freshness:88,change:'unchanged'},{name:'AI工具应用',level:'intermediate',weight:0.14,freshness:68,change:'upgraded',changeReason:'AI Agent管理工具链日常操作'},{name:'风险管理',level:'intermediate',weight:0.12,freshness:82,change:'unchanged'},{name:'项目管理',level:'intermediate',weight:0.08,freshness:84,change:'unchanged'}]},
  ]},

  // ── pos-7: 资深后端工程师 ──
  'pos-7': { positionId: 'pos-7', positionName: '资深后端工程师', timeline: [
    { date:'2019Q1',label:'2019年第一季度',marketDemand:75,matchRate:82,salaryRange:'25-42K',adoptionRate:65,tools:['Java/Spring','MySQL','Redis','RabbitMQ','Nginx'],marketContext:'Java生态统治企业后端。微服务从概念走向落地。Spring Boot/Cloud一统天下。',industryEvents:['Spring Boot 2.x大规模采用','Service Mesh提出','CNCF生态爆发'],typicalProjects:['微服务拆分','高并发优化','分布式事务'],summary:'Java/Spring主导，微服务大规模落地',dataSources:['招聘JD(120份)','行业报告(2份)'],skills:[{name:'Java/Spring',level:'expert',weight:0.28,freshness:92,change:'unchanged'},{name:'MySQL',level:'expert',weight:0.22,freshness:90,change:'unchanged'},{name:'Redis/MQ',level:'advanced',weight:0.18,freshness:85,change:'unchanged'},{name:'系统设计',level:'advanced',weight:0.20,freshness:86,change:'unchanged'},{name:'Linux',level:'advanced',weight:0.12,freshness:88,change:'unchanged'}]},
    { date:'2021Q1',label:'2021年第一季度',marketDemand:82,matchRate:70,salaryRange:'32-55K',adoptionRate:75,tools:['Java/Spring','Go','Kubernetes','gRPC','Kafka','TiDB'],marketContext:'Go语言在中间件/基础设施快速崛起。云原生成为架构默认。Service Mesh+可观测性成为新层。',industryEvents:['Go成为CNCF首选','K8s成为标准','Kafka标配化'],typicalProjects:['云原生迁移','事件驱动架构','实时数据管道'],summary:'Go崛起+云原生全面铺开',dataSources:['招聘JD(188份)','行业报告(3份)'],skills:[{name:'Java/Spring',level:'expert',weight:0.22,freshness:90,change:'unchanged'},{name:'Go/Rust',level:'intermediate',weight:0.16,freshness:78,change:'added',changeReason:'Go在基础设施普及'},{name:'MySQL/NewSQL',level:'advanced',weight:0.18,freshness:88,change:'unchanged'},{name:'Kubernetes',level:'intermediate',weight:0.12,freshness:74,change:'added'},{name:'系统设计',level:'advanced',weight:0.18,freshness:86,change:'unchanged'},{name:'Redis/MQ',level:'advanced',weight:0.14,freshness:84,change:'unchanged'}]},
    { date:'2023Q1',label:'2023年第一季度',marketDemand:88,matchRate:62,salaryRange:'38-65K',adoptionRate:82,tools:['Go/Rust','Java/Spring','Kubernetes','Kafka','gRPC','OpenTelemetry'],marketContext:'Go份额持续扩大。Rust在高性能场景崭露头角。云原生全栈成为标配。事件驱动+流处理成为主流。',industryEvents:['Rust进入Linux内核','事件驱动主流','OTel成为标准'],typicalProjects:['高性能中间件','流处理平台','多云架构'],summary:'Go/Rust全面渗透，云原生全栈成为标配',dataSources:['招聘JD(245份)','行业报告(5份)'],skills:[{name:'Go/Rust',level:'advanced',weight:0.24,freshness:86,change:'upgraded',changeReason:'Go云原生主力，Rust性能场景崛起'},{name:'系统设计',level:'expert',weight:0.24,freshness:90,change:'upgraded'},{name:'Java/Spring',level:'advanced',weight:0.16,freshness:85,change:'downgraded',changeReason:'Go抢占份额'},{name:'Kubernetes',level:'advanced',weight:0.14,freshness:82,change:'upgraded'},{name:'MySQL/NewSQL',level:'advanced',weight:0.12,freshness:86,change:'unchanged'},{name:'消息队列',level:'advanced',weight:0.10,freshness:84,change:'unchanged'}]},
    { date:'2025Q1',label:'2025年第一季度',marketDemand:90,matchRate:55,salaryRange:'42-75K',adoptionRate:88,tools:['Go/Rust','Kubernetes','eBPF','WASM','Kafka','AI Infra'],marketContext:'AI推理成为后端新负载。WASM在边缘/Plugin落地。后端+AI复合岗位薪资溢价50%。',industryEvents:['AI推理成核心负载','WASM落地','后端+AI岗位爆发'],typicalProjects:['AI推理平台','高性能API网关','流式处理'],summary:'AI推理成为新核心负载，后端+AI复合化',dataSources:['招聘JD(282份)','行业报告(7份)'],skills:[{name:'Go/Rust',level:'expert',weight:0.24,freshness:92,change:'upgraded',changeReason:'Rust全面取代C/C++'},{name:'系统设计',level:'expert',weight:0.22,freshness:92,change:'unchanged'},{name:'Kubernetes/eBPF',level:'advanced',weight:0.16,freshness:84,change:'unchanged'},{name:'AI Infra',level:'intermediate',weight:0.12,freshness:70,change:'added',changeReason:'AI推理服务化成为新职责'},{name:'消息队列',level:'advanced',weight:0.10,freshness:86,change:'unchanged'},{name:'Java/Spring',level:'intermediate',weight:0.08,freshness:82,change:'unchanged'},{name:'MySQL',level:'advanced',weight:0.08,freshness:88,change:'unchanged'}]},
    { date:'2026Q3',label:'2026年第三季度(当前)',marketDemand:90,matchRate:55,salaryRange:'45-82K',adoptionRate:92,tools:['Go/Rust','Kubernetes','WASM','AI Infra','eBPF','Temporal'],marketContext:'后端从"写逻辑"到"搭AI基础设施"。GPU推理+模型服务化成为核心。WASM让边缘+Plugin成为主流。',industryEvents:['AI推理成独立产品','WASM生产落地','后端薪资两极分化'],typicalProjects:['AI推理平台','WASM边缘计算','多租户分布式系统'],summary:'从"写逻辑"到"搭AI基础设施"，GPU推理+WASM成为新边界',dataSources:['招聘JD(196份)','行业报告(8份)'],skills:[{name:'Go/Rust',level:'expert',weight:0.22,freshness:94,change:'unchanged'},{name:'系统设计',level:'expert',weight:0.22,freshness:94,change:'unchanged'},{name:'AI Infra/推理',level:'advanced',weight:0.15,freshness:76,change:'upgraded',changeReason:'GPU推理优化成为核心'},{name:'Kubernetes',level:'advanced',weight:0.12,freshness:86,change:'unchanged'},{name:'WASM',level:'intermediate',weight:0.10,freshness:70,change:'added',changeReason:'边缘+Plugin全面采用WASM'},{name:'消息队列',level:'advanced',weight:0.08,freshness:88,change:'unchanged'},{name:'MySQL',level:'advanced',weight:0.06,freshness:88,change:'unchanged'},{name:'Java/Spring',level:'intermediate',weight:0.05,freshness:80,change:'unchanged'}]},
  ]},

  // ── pos-8: QA测试工程师 ──
  'pos-8': { positionId: 'pos-8', positionName: 'QA 测试工程师', timeline: [
    { date:'2019Q1',label:'2019年第一季度',marketDemand:55,matchRate:95,salaryRange:'10-20K',adoptionRate:50,tools:['Selenium','JMeter','Postman','Jira','TestRail'],marketContext:'手工测试仍占主导。自动化在互联网初步推广。Selenium是Web自动化标配。',industryEvents:['Selenium成Web自动化标准','持续测试(CT)兴起','测试左移传播'],typicalProjects:['手工回归测试','Selenium自动化','API测试'],summary:'手工测试为主，Selenium自动化初步推广',dataSources:['招聘JD(45份)','行业报告(1份)'],skills:[{name:'手工测试',level:'expert',weight:0.35,freshness:85,change:'unchanged'},{name:'测试用例设计',level:'advanced',weight:0.28,freshness:88,change:'unchanged'},{name:'Selenium',level:'basic',weight:0.15,freshness:72,change:'unchanged'},{name:'SQL',level:'intermediate',weight:0.12,freshness:82,change:'unchanged'},{name:'JMeter',level:'basic',weight:0.10,freshness:70,change:'unchanged'}]},
    { date:'2021Q1',label:'2021年第一季度',marketDemand:58,matchRate:90,salaryRange:'15-28K',adoptionRate:58,tools:['Cypress','Playwright','Postman','k6'],marketContext:'新一代测试工具挑战Selenium。API测试成为重点。k6等现代性能工具兴起。',industryEvents:['Playwright发布','Cypress大量采用','k6成性能测试标准'],typicalProjects:['E2E自动化','API自动化','性能基准测试'],summary:'Playwright/Cypress替代Selenium，API+性能自动化加速',dataSources:['招聘JD(78份)','行业报告(2份)'],skills:[{name:'自动化测试',level:'intermediate',weight:0.30,freshness:80,change:'upgraded'},{name:'测试用例设计',level:'advanced',weight:0.22,freshness:86,change:'unchanged'},{name:'API测试',level:'intermediate',weight:0.18,freshness:78,change:'added'},{name:'SQL',level:'intermediate',weight:0.12,freshness:82,change:'unchanged'},{name:'手工测试',level:'advanced',weight:0.10,freshness:80,change:'downgraded',changeReason:'自动化替代手工回归'},{name:'Selenium',level:'intermediate',weight:0.08,freshness:72,change:'unchanged'}]},
    { date:'2023Q1',label:'2023年第一季度',marketDemand:52,matchRate:88,salaryRange:'18-32K',adoptionRate:62,tools:['Playwright','Cypress','k6','Testcontainers'],marketContext:'质量工程(QE)取代传统QA。左移+右移双向扩展。契约测试+混沌工程新方法论。',industryEvents:['低代码测试工具爆发','契约测试普及','混沌工程走向企业'],typicalProjects:['质量工程建设','契约测试','CICD质量门禁'],summary:'从QA到QE——质量工程化，契约+混沌测试新方法论',dataSources:['招聘JD(95份)','行业报告(3份)'],skills:[{name:'自动化测试',level:'advanced',weight:0.28,freshness:84,change:'upgraded'},{name:'测试框架',level:'intermediate',weight:0.20,freshness:78,change:'added'},{name:'测试用例设计',level:'advanced',weight:0.18,freshness:84,change:'unchanged'},{name:'API测试',level:'advanced',weight:0.14,freshness:82,change:'unchanged'},{name:'性能测试',level:'intermediate',weight:0.12,freshness:76,change:'unchanged'},{name:'手工测试',level:'intermediate',weight:0.08,freshness:72,change:'unchanged'}]},
    { date:'2025Q1',label:'2025年第一季度',marketDemand:45,matchRate:92,salaryRange:'20-35K',adoptionRate:55,tools:['Playwright','AI测试工具','k6','Pact','OpenTelemetry'],marketContext:'AI大幅改变测试——自动生成用例+探索性测试。初级岗位萎缩。生产环境测试成为标配。',industryEvents:['AI测试工具涌现','初级测试岗位减少30%','Shift-Right成为标配'],typicalProjects:['AI辅助测试生成','生产质量监控','测试策略设计'],summary:'AI改变测试——自动生成+探索，初级萎缩，策略设计升值',dataSources:['招聘JD(65份)','行业报告(4份)'],skills:[{name:'自动化测试',level:'advanced',weight:0.26,freshness:86,change:'unchanged'},{name:'测试框架',level:'advanced',weight:0.20,freshness:82,change:'unchanged'},{name:'AI测试工具',level:'basic',weight:0.16,freshness:62,change:'added',changeReason:'AI自动生成测试用例'},{name:'性能测试',level:'advanced',weight:0.14,freshness:80,change:'unchanged'},{name:'安全测试',level:'basic',weight:0.12,freshness:60,change:'added',changeReason:'安全左移推动需求'},{name:'测试用例设计',level:'intermediate',weight:0.12,freshness:82,change:'unchanged'}]},
    { date:'2026Q3',label:'2026年第三季度(当前)',marketDemand:42,matchRate:95,salaryRange:'22-38K',adoptionRate:52,tools:['Playwright','AI Test Agents','k6','安全测试工具','Chaos Mesh'],marketContext:'测试从"执行者"到"质量架构师"。AI Agent承担执行，人专注策略+探索。安全+混沌工程成为标配。',industryEvents:['AI Test Agent自主探索测试','质量工程成独立职业路径','安全+测试融合'],typicalProjects:['AI Agent测试编排','全链路质量平台','混沌+安全自动化'],summary:'AI Agent执行，人专注策略——从测试到质量架构师',dataSources:['招聘JD(52份)','行业报告(5份)'],skills:[{name:'自动化测试',level:'advanced',weight:0.24,freshness:88,change:'unchanged'},{name:'测试框架',level:'advanced',weight:0.20,freshness:84,change:'unchanged'},{name:'AI测试工具',level:'intermediate',weight:0.18,freshness:70,change:'upgraded',changeReason:'AI Agent测试编排关键'},{name:'安全测试',level:'intermediate',weight:0.14,freshness:66,change:'upgraded',changeReason:'安全左移合规要求'},{name:'性能测试',level:'advanced',weight:0.12,freshness:82,change:'unchanged'},{name:'混沌工程',level:'intermediate',weight:0.12,freshness:72,change:'added',changeReason:'生产韧性测试新维度'}]},
  ]},
}

// ── Store ──

export const useEnterpriseStore = defineStore('enterprise', () => {
  const positions = ref<PositionStandard[]>([...demoPositions])
  const candidates = ref<RoleCandidate[]>([...demoCandidates])
  const evolutions = ref<Record<string, PositionEvolution>>({ ...demoEvolutions })
  const currentPositionId = ref<string>('pos-1')
  const diagnoses = ref<JDDiagnosis[]>([...demoDiagnoses])
  const market = ref<Record<string, MarketSkill[]>>({ ...demoMarket })
  const teamGaps = ref<TeamGap[]>([...demoTeamGaps])
  const forecast = ref<TalentForecast>({ ...demoForecast })
  const talentCandidates = ref<TalentCandidate[]>([...demoTalentCandidates])
  const talentDetails = ref<Record<string, TalentDetail>>({ ...demoTalentDetails })
  const enterpriseProfile = ref<EnterpriseProfile>({ ...demoEnterpriseProfile })
  const loading = ref(false)

  const currentEvolution = computed(() =>
    evolutions.value[currentPositionId.value] || evolutions.value['pos-1']
  )

  function setCurrentPosition(positionId: string) {
    currentPositionId.value = positionId
  }

  const positionCount = computed(() => positions.value.length)
  const confirmedCount = computed(() => positions.value.filter(p => p.status === 'confirmed').length)
  const candidateCount = computed(() => candidates.value.filter(c => c.status === 'candidate').length)
  const avgMatchRate = computed(() => Math.round(positions.value.reduce((s, p) => s + p.matchRate, 0) / positions.value.length))
  const warningCount = computed(() => diagnoses.value.filter(d => d.status !== 'healthy').length)
  const highPriorityGaps = computed(() => teamGaps.value.filter(g => g.priority === 'high').length)
  const favoriteCount = computed(() => talentCandidates.value.filter(c => c.favorite).length)
  const highMatchCount = computed(() => talentCandidates.value.filter(c => c.bestMatchRate >= 85).length)
  const activeHrCount = computed(() =>
    talentCandidates.value.filter(c => ['shortlisted', 'interviewing', 'offered'].includes(c.hrStatus)).length
  )

  // ── 全景图谱数据（由 positions 动态生成）──
  const graphData = computed(() => {
    const nodes: GraphNode[] = []
    const links: GraphLink[] = []

    // 技术栈颜色映射
    const techStackMap: Record<string, string> = {
      '技术部': 'AI',
      '数据部': '数据',
      '质量部': 'DevOps',
    }

    for (const pos of positions.value) {
      const techStack = techStackMap[pos.department] || '后端'
      nodes.push({
        id: pos.id,
        name: pos.name,
        category: 'position',
        techStack,
        level: pos.level,
        marketDemand: pos.marketDemand,
        skillCount: pos.skills.length,
        symbolSize: 35 + (pos.marketDemand / 100) * 30,
      })

      for (const skill of pos.skills) {
        const skillId = `skill-${skill.name}`
        if (!nodes.find(n => n.id === skillId)) {
          nodes.push({
            id: skillId,
            name: skill.name,
            category: 'skill',
            techStack,
            marketDemand: skill.freshness,
            symbolSize: 12 + (skill.freshness / 100) * 18,
          })
        }
        links.push({
          source: pos.id,
          target: skillId,
          value: skill.weight,
        })
      }
    }

    return { nodes, links }
  })

  // ── 图谱蓝图：G6 v5 形状图数据 + normalize 序列 + 快照 ──
  const graph = ref<{ nodes: any[]; edges: any[] }>(buildDemoGraph(positions.value))
  const graphSource = ref<'demo' | 'mysql'>('demo')
  const graphSeries = computed(() => normalizeGraph(graph.value.nodes, graph.value.edges))
  const graphNodes = computed(() => graphSeries.value.nodes)
  const graphLinks = computed(() => graphSeries.value.links)

  const snapshot = ref({
    version: 'V14', timestamp: '2026-08-03', description: '2026 下半年 · 全量重建',
    node_count: 0, edge_count: 0,
  })
  const snapshotDiff = ref({
    added_skills: ['大模型微调', 'RAG 应用', 'Agent 编排', '端侧 AI', '联邦学习'],
    removed_skills: ['传统 CV 特征工程', '数据标注', '规则引擎'],
    modified_skills: [
      { name: 'MLOps', old_confidence: 0.72, new_confidence: 0.86 },
      { name: 'Kubernetes', old_confidence: 0.81, new_confidence: 0.9 },
      { name: 'AI 测试', old_confidence: 0.55, new_confidence: 0.74 },
    ],
    added_relations: [{ source: 'AI 算法工程师', target: 'RAG 应用', rel_type: '必备' }],
    removed_relations: [{ source: '数据分析师', target: 'Tableau', rel_type: '必备' }],
    summary: '较上一快照：新增 5 项技能、删除 3 项、修改 3 项置信度；技能共现网络密度上升 18%。',
  })

  async function fetchGraph() {
    try {
      const res = await client.get('/api/graph') as any
      if (res?.nodes?.length) {
        graph.value = { nodes: res.nodes, edges: res.edges || [] }
        graphSource.value = res.source === 'mysql' ? 'mysql' : 'demo'
      }
    } catch {}
  }

  async function fetchSnapshotDiff() {
    try {
      const res = await client.get('/api/graph/snapshots/diff?old=&new=') as any
      if (res?.summary) snapshotDiff.value = res
    } catch {}
  }

  async function fetchPositions() {
    loading.value = true
    try {
      const res = await client.get('/api/enterprise/positions') as any
      if (res?.positions?.length) positions.value = res.positions
    } catch { /* 静默保留 demo 数据 */ }
    finally { loading.value = false }
  }

  async function fetchCandidates() {
    try {
      const res = await client.get('/api/enterprise/discovery') as any
      if (res?.candidates?.length) candidates.value = res.candidates
    } catch {}
  }

  async function fetchDiagnoses() {
    try {
      const res = await client.get('/api/enterprise/diagnose') as any
      if (res?.diagnoses?.length) diagnoses.value = res.diagnoses
    } catch {}
  }

  async function fetchTeamGaps() {
    try {
      const res = await client.get('/api/enterprise/team/gaps') as any
      if (res?.gaps?.length) teamGaps.value = res.gaps
    } catch {}
  }

  async function fetchForecast() {
    try {
      const res = await client.get('/api/enterprise/talent/forecast') as any
      if (res?.hot_skills?.length || res?.cooling_skills?.length) {
        const phaseFor = (i: number, total: number): SkillTrend['phase'] =>
          i < 3 ? 'hot' : i < Math.min(6, total) ? 'rising' : 'new'
        forecast.value = {
          emerging: (res.hot_skills || []).map((s: any, i: number) => ({
            name: s.name, score: s.emergence ?? 0, phase: phaseFor(i, res.hot_skills.length),
          })),
          cooling: (res.cooling_skills || []).map((s: any, i: number) => ({
            name: s.name, score: s.decline ?? 0, phase: 'cooling' as const,
          })),
          recommendation: res.recommendation || forecast.value.recommendation,
        }
      }
    } catch {}
  }

  /** 新岗位裁决：批准立项 / 驳回（印章级联到仪表盘） */
  function setCandidateStatus(id: string, status: RoleCandidate['status']) {
    const c = candidates.value.find((x) => x.id === id)
    if (c) c.status = status
  }

  async function fetchEvolution(positionId?: string) {
    if (positionId) setCurrentPosition(positionId)
    try {
      const pid = positionId || currentPositionId.value
      const res = await client.get(`/api/enterprise/positions/${pid}/evolution`) as any
      if (res?.timeline?.length) {
        evolutions.value[pid] = res
      }
    } catch {}
  }

  /** 市场技能（T4）—— PositionDiffView 市场侧；title 为岗位名（编码由 axios params 处理） */
  async function fetchMarket(title: string) {
    try {
      const res = await client.get('/api/jd/market', { params: { title } }) as any
      if (res?.skills?.length) market.value[title] = res.skills
    } catch {}
  }

  // ── 人才库 ──

  async function fetchTalentPool(params?: Record<string, string | number | boolean>) {
    try {
      const res = await client.get('/api/enterprise/talent-pool', { params }) as any
      if (res?.candidates?.length) talentCandidates.value = res.candidates
    } catch { /* 静默保留 demo 数据 */ }
  }

  async function fetchTalentDetail(id: string) {
    try {
      const res = await client.get(`/api/enterprise/talent-pool/${id}`) as any
      if (res?.profile) {
        talentDetails.value[id] = res
        // 列表同步最新标注
        const row = talentCandidates.value.find((c) => c.id === id)
        if (row) {
          row.favorite = res.annotation.favorite
          row.hrStatus = res.annotation.hrStatus
          row.note = res.annotation.note
          row.updatedAt = res.annotation.updatedAt
        }
      }
    } catch { /* 静默保留 demo 数据 */ }
  }

  /** HR 标注 upsert：乐观更新本地（Silent Fallback——后端不可用交互仍成立），PUT 成功后以响应为准。 */
  async function updateTalentAnnotation(id: string, patch: { favorite?: boolean; hrStatus?: HrStatus; note?: string }): Promise<boolean> {
    const row = talentCandidates.value.find((c) => c.id === id)
    if (row) {
      if (patch.favorite !== undefined) row.favorite = patch.favorite
      if (patch.hrStatus !== undefined) row.hrStatus = patch.hrStatus
      if (patch.note !== undefined) row.note = patch.note
    }
    const detail = talentDetails.value[id]
    if (detail) {
      detail.annotation = { ...detail.annotation, ...patch, updatedAt: new Date().toISOString() }
    }
    try {
      const res = await client.put(`/api/enterprise/talent-pool/${id}/annotation`, patch) as any
      if (res?.annotation) {
        if (detail) detail.annotation = res.annotation
        const r2 = talentCandidates.value.find((c) => c.id === id)
        if (r2) {
          r2.favorite = res.annotation.favorite
          r2.hrStatus = res.annotation.hrStatus
          r2.note = res.annotation.note
          r2.updatedAt = res.annotation.updatedAt
        }
      }
    } catch { /* 静默——本地乐观更新已生效 */ }
    return true
  }

  /** 当前登录企业档案：API 成功则覆盖 demo（Silent Fallback）。 */
  async function fetchEnterpriseProfile() {
    try {
      const res = await client.get('/api/enterprise/profile') as any
      if (res?.profile) enterpriseProfile.value = res.profile
    } catch { /* 静默保留 demo 数据 */ }
  }

  /** 企业档案编辑：乐观合并本地 → PUT → 成功后以响应为准（Silent Fallback——后端不可用编辑仍成立）。 */
  async function updateEnterpriseProfile(patch: Partial<EnterpriseProfile>): Promise<boolean> {
    enterpriseProfile.value = { ...enterpriseProfile.value, ...patch, updatedAt: new Date().toISOString() }
    try {
      const res = await client.put('/api/enterprise/profile', patch) as any
      if (res?.profile) enterpriseProfile.value = res.profile
    } catch { /* 静默——本地乐观更新已生效 */ }
    return true
  }

  return {
    positions, candidates, diagnoses, market, teamGaps, forecast, evolutions, currentEvolution, currentPositionId, graphData, loading,
    graph, graphSource, graphNodes, graphLinks, snapshot, snapshotDiff,
    talentCandidates, talentDetails, favoriteCount, highMatchCount, activeHrCount,
    enterpriseProfile,
    positionCount, confirmedCount, candidateCount, avgMatchRate, warningCount, highPriorityGaps,
    fetchPositions, fetchCandidates, fetchDiagnoses, fetchTeamGaps, fetchForecast, fetchEvolution, fetchMarket, fetchGraph, fetchSnapshotDiff,
    fetchTalentPool, fetchTalentDetail, updateTalentAnnotation,
    fetchEnterpriseProfile, updateEnterpriseProfile,
    setCurrentPosition, setCandidateStatus,
  }
})
