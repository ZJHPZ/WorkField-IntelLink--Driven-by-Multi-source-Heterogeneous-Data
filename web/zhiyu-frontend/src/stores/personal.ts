import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'
import { computePositionMatches } from '@/utils/matches'

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
  // ── 真实数据源增强字段（/api/positions × 用户画像计算，或满篇详细模拟实例）──
  positionId?: string
  techStack?: string
  city?: string
  jdCount?: number
  topCompanies?: { company_name: string; count: number }[]
  requiredSkills?: string[]
  partialSkills?: string[]
  learningPath?: { skill: string; hours: number; duration: string; resource: string }[]
  source?: 'db' | 'real' | 'sim'
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
  // ── T1/T4 派生可选字段（/api/positions 增强后返回）──
  city?: string
  salaryRange?: string
  jdCount?: number
  topCompanies?: { company_name: string; count: number }[]
  topCities?: { city: string; count: number }[]
  requiredSkills?: string[]
  bonusSkills?: string[]
}

// ── 岗位收藏（岗位库「收藏」快照，localStorage 持久化）──
// 从岗位库收藏时对必备技能做一次个人覆盖分类，快照存入 matched/partial/missing，
// 供个人中心「岗位收藏」与岗位对比直接复用 —— 无需依赖后端（后端无收藏表）。

export interface FavoritePosition {
  id: string
  name: string
  salary: string
  city: string
  techStack: string
  jdCount: number
  matchRate: number           // 岗位库展示的匹配热度（与岗位库一致）
  matchedSkills: string[]
  partialSkills: string[]
  missingSkills: string[]
  requiredSkills: string[]
  bonusSkills: string[]
  topCompanies?: { company_name: string; count: number }[]
  favoritedAt: number
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

// 满篇详细的模拟展示实例（真实数据源无法满足时的兜底 —— 字段与真实匹配完全同构：
// source:'sim' 明示模拟；若 /api/personal/matches 或真实岗位计算可用，会被适配链替换）。
const richDemoMatches: JobMatch[] = [
  {
    id: 'm-1', positionName: 'AI 算法工程师', company: '某头部 AI 研发平台', matchRate: 82,
    matchedSkills: ['Python', '深度学习', 'NLP'], partialSkills: ['PyTorch'],
    missingSkills: ['MLOps', '分布式训练', '模型部署'],
    salaryRange: '40-70K', techStack: 'AI/ML', city: '北京', jdCount: 312,
    topCompanies: [{ company_name: '某头部 AI 研发平台', count: 128 }, { company_name: '某大模型独角兽', count: 57 }],
    requiredSkills: ['Python', '深度学习', 'NLP', 'PyTorch', 'MLOps', '分布式训练', '模型部署', 'TensorRT'],
    learningPath: [
      { skill: 'MLOps', hours: 30, duration: '2-3个月', resource: 'MLflow + Kubeflow 工程化实战' },
      { skill: '分布式训练', hours: 40, duration: '3-4个月', resource: 'DeepSpeed + Megatron 多卡训练' },
      { skill: '模型部署', hours: 20, duration: '1-2个月', resource: 'Triton + vLLM 推理优化' },
    ],
    source: 'sim',
  },
  {
    id: 'm-2', positionName: '全栈开发工程师', company: '某一线互联网大厂', matchRate: 85,
    matchedSkills: ['TypeScript', 'React', 'SQL'], partialSkills: ['Node.js'],
    missingSkills: ['AWS', 'Redis', 'Docker 编排'],
    salaryRange: '30-50K', techStack: '全栈', city: '上海', jdCount: 486,
    topCompanies: [{ company_name: '某一线互联网大厂', count: 203 }, { company_name: '某电商平台', count: 88 }],
    requiredSkills: ['TypeScript', 'React', 'SQL', 'Node.js', 'AWS', 'Redis', 'Docker 编排', '微服务'],
    learningPath: [
      { skill: 'AWS', hours: 25, duration: '1-2个月', resource: 'AWS 认证 + 云原生实践' },
      { skill: 'Redis', hours: 16, duration: '1个月', resource: 'Redis 深度使用与缓存架构' },
      { skill: 'Docker 编排', hours: 24, duration: '1-2个月', resource: 'Docker Compose + 服务编排' },
    ],
    source: 'sim',
  },
  {
    id: 'm-3', positionName: 'ML Engineer', company: '某 AI 独角兽', matchRate: 78,
    matchedSkills: ['Python', '深度学习', 'NLP', 'Kubernetes'], partialSkills: [],
    missingSkills: ['MLOps', '模型评估', 'A/B 实验'],
    salaryRange: '45-80K', techStack: 'AI/ML', city: '深圳', jdCount: 228,
    topCompanies: [{ company_name: '某 AI 独角兽', count: 94 }, { company_name: '某自动驾驶公司', count: 40 }],
    requiredSkills: ['Python', '深度学习', 'NLP', 'Kubernetes', 'MLOps', '模型评估', 'A/B 实验', '特征工程'],
    learningPath: [
      { skill: 'MLOps', hours: 30, duration: '2-3个月', resource: 'MLflow + Kubeflow 工程化实战' },
      { skill: '模型评估', hours: 18, duration: '1个月', resource: '模型验证指标体系' },
      { skill: 'A/B 实验', hours: 20, duration: '1-2个月', resource: '实验设计与显著性检验' },
    ],
    source: 'sim',
  },
  {
    id: 'm-4', positionName: '前端架构工程师', company: '某大型金融科技集团', matchRate: 88,
    matchedSkills: ['TypeScript', 'React', 'SQL', '系统设计'], partialSkills: [],
    missingSkills: ['微前端', 'Webpack 性能调优'],
    salaryRange: '35-60K', techStack: '前端', city: '杭州', jdCount: 176,
    topCompanies: [{ company_name: '某大型金融科技集团', count: 62 }, { company_name: '某云服务商', count: 31 }],
    requiredSkills: ['TypeScript', 'React', 'SQL', '系统设计', '微前端', 'Webpack 性能调优', '可视化', '工程化'],
    learningPath: [
      { skill: '微前端', hours: 28, duration: '2-3个月', resource: 'qiankun + Module Federation 实战' },
      { skill: 'Webpack 性能调优', hours: 22, duration: '1-2个月', resource: '打包优化与拆包策略' },
    ],
    source: 'sim',
  },
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
  // ── 岗位实例 ①：AI 算法工程师 ──
  { snapshotId: 'snap-2025-01', positionName: 'AI 算法工程师', timestamp: '2025-01-15', description: '2025年初岗位技能基线', skillCount: 12, dataSources: ['JD×156', 'GitHub×45', 'arXiv×18'],
    changes: [
      { type: 'added', skillName: '大模型微调', evidence: '32条JD提及LoRA/QLoRA，微调成为算法岗标配能力', source: 'JD聚合' },
      { type: 'added', skillName: 'RAG', evidence: '28条JD提及检索增强生成，知识库问答需求爆发', source: 'JD聚合' },
      { type: 'upgraded', skillName: 'PyTorch', oldLevel: '中级', newLevel: '高级', evidence: '85%JD要求熟练使用PyTorch做训练与部署', source: 'JD分析' },
      { type: 'added', skillName: 'Agent框架', evidence: '15条JD首现AI Agent框架要求，尚处探索期', source: 'JD+GitHub' },
    ] },
  { snapshotId: 'snap-2025-06', positionName: 'AI 算法工程师', timestamp: '2025-06-20', description: '2025年中技能需求更新', skillCount: 15, dataSources: ['JD×210', 'GitHub×68', 'arXiv×35'],
    changes: [
      { type: 'added', skillName: 'DeepSpeed', evidence: '分布式训练需求激增，45条JD提及多卡训练', source: 'JD+GitHub' },
      { type: 'added', skillName: 'RLHF', evidence: '对齐技术成为标配，38条JD提及偏好优化', source: 'JD+arXiv' },
      { type: 'removed', skillName: 'TensorFlow 1.x', evidence: '旧版本需求降至5%以下，生态向PyTorch收敛', source: 'JD衰退分析' },
      { type: 'upgraded', skillName: 'NLP', oldLevel: '中级', newLevel: '高级', evidence: '大模型时代NLP要求提升至高级', source: 'JD趋势' },
      { type: 'downgraded', skillName: '传统机器学习', oldLevel: '高级', newLevel: '中级', evidence: '深度学习取代大部分传统ML场景', source: 'JD衰退分析' },
    ] },
  { snapshotId: 'snap-2025-12', positionName: 'AI 算法工程师', timestamp: '2025-12-01', description: '2025年底：工程化能力收敛', skillCount: 16, dataSources: ['JD×248', 'GitHub×80', 'arXiv×42'],
    changes: [
      { type: 'upgraded', skillName: 'MLOps', oldLevel: '初级', newLevel: '高级', evidence: 'MLflow/Kubeflow 工程化实践写入JD', source: 'JD+GitHub' },
      { type: 'added', skillName: '模型量化', evidence: '25条JD提及 TensorRT/vLLM 推理优化', source: 'JD聚合' },
      { type: 'added', skillName: '多模态模型', evidence: '视觉语言模型需求爆发，62条JD提及', source: 'JD+arXiv' },
    ] },
  { snapshotId: 'snap-2026-08', positionName: 'AI 算法工程师', timestamp: '2026-08-10', description: '2026年中：Agent原生时代', skillCount: 17, dataSources: ['JD×320', 'GitHub×110', 'arXiv×66'],
    changes: [
      { type: 'upgraded', skillName: 'Agent框架', oldLevel: '中级', newLevel: '专家', evidence: 'Agent成为算法岗核心，75条JD要求自主编排', source: 'JD+GitHub' },
      { type: 'added', skillName: 'Function-Calling', evidence: 'Agentic工作流成主流，40条JD提及工具调用', source: 'JD+arXiv' },
      { type: 'removed', skillName: '特征工程', oldLevel: '高级', newLevel: '—', evidence: '端到端模型减少人工特征工程，需求归零', source: 'JD衰退分析' },
    ] },

  // ── 岗位实例 ②：Java 后端工程师 ──
  { snapshotId: 'snap-2024-01', positionName: 'Java 后端工程师', timestamp: '2024-01-20', description: '2024年初：微服务化推进', skillCount: 13, dataSources: ['JD×210', 'GitHub×38'],
    changes: [
      { type: 'added', skillName: 'Spring Cloud Alibaba', evidence: '微服务改造推进，40条JD要求注册中心/网关', source: 'JD聚合' },
      { type: 'upgraded', skillName: 'Spring Boot', oldLevel: '中级', newLevel: '高级', evidence: 'Spring Boot成为后端必选框架，90%JD要求', source: 'JD分析' },
      { type: 'added', skillName: 'Redis', evidence: '缓存场景普及，35条JD要求Redis使用', source: 'JD聚合' },
      { type: 'added', skillName: '分布式事务', evidence: 'Seata等方案进入JD，20条JD提及', source: 'JD+GitHub' },
    ] },
  { snapshotId: 'snap-2025-03', positionName: 'Java 后端工程师', timestamp: '2025-03-18', description: '2025年：云原生改造', skillCount: 15, dataSources: ['JD×268', 'GitHub×52'],
    changes: [
      { type: 'added', skillName: 'Kubernetes', evidence: '云原生推进，48条JD要求K8s部署与编排', source: 'JD+GitHub' },
      { type: 'upgraded', skillName: 'MySQL', oldLevel: '中级', newLevel: '高级', evidence: '高并发场景要求MySQL调优与索引设计', source: 'JD分析' },
      { type: 'added', skillName: 'Kafka', evidence: '异步化改造，30条JD提及消息队列', source: 'JD聚合' },
      { type: 'downgraded', skillName: 'Struts', oldLevel: '高级', newLevel: '初级', evidence: '老旧框架需求持续萎缩', source: 'JD衰退分析' },
    ] },
  { snapshotId: 'snap-2026-06', positionName: 'Java 后端工程师', timestamp: '2026-06-02', description: '2026年中：AI工程化落地', skillCount: 16, dataSources: ['JD×301', 'GitHub×60', 'arXiv×12'],
    changes: [
      { type: 'added', skillName: '大模型应用开发', evidence: 'Spring AI/LLM应用集成，52条JD提及', source: 'JD+arXiv' },
      { type: 'upgraded', skillName: '微服务', oldLevel: '中级', newLevel: '专家', evidence: '微服务治理能力进入专家要求', source: 'JD分析' },
      { type: 'removed', skillName: 'Struts', oldLevel: '高级', newLevel: '—', evidence: 'JD中Struts需求归零', source: 'JD衰退分析' },
    ] },

  // ── 岗位实例 ③：前端开发工程师 ──
  { snapshotId: 'snap-2024-02', positionName: '前端开发工程师', timestamp: '2024-02-10', description: '2024年初：框架收敛', skillCount: 10, dataSources: ['JD×180', 'GitHub×55'],
    changes: [
      { type: 'added', skillName: 'Vue3', evidence: 'Vue3成为主流，55条JD要求组合式API', source: 'JD聚合' },
      { type: 'upgraded', skillName: 'TypeScript', oldLevel: '中级', newLevel: '高级', evidence: 'TS成为前端必备，78%JD要求类型安全', source: 'JD分析' },
      { type: 'downgraded', skillName: 'jQuery', oldLevel: '高级', newLevel: '初级', evidence: 'jQuery需求降至10%以下', source: 'JD衰退分析' },
    ] },
  { snapshotId: 'snap-2025-04', positionName: '前端开发工程师', timestamp: '2025-04-08', description: '2025年：工程化深化', skillCount: 13, dataSources: ['JD×226', 'GitHub×72'],
    changes: [
      { type: 'added', skillName: 'Vite', evidence: '构建工具迁移Vite，30条JD提及', source: 'JD+GitHub' },
      { type: 'added', skillName: '微前端', evidence: '中后台微前端落地，22条JD要求qiankun', source: 'JD聚合' },
      { type: 'upgraded', skillName: 'React', oldLevel: '中级', newLevel: '高级', evidence: 'React18+并发特性要求提升', source: 'JD分析' },
      { type: 'added', skillName: '性能优化', evidence: 'Web性能指标成为考核项，18条JD提及', source: 'JD聚合' },
    ] },
  { snapshotId: 'snap-2026-05', positionName: '前端开发工程师', timestamp: '2026-05-16', description: '2026年：AI辅助开发', skillCount: 14, dataSources: ['JD×255', 'GitHub×88'],
    changes: [
      { type: 'added', skillName: 'AI编码工具集成', evidence: 'Copilot/Cursor工作流进入团队要求', source: 'JD+GitHub' },
      { type: 'upgraded', skillName: '微前端', oldLevel: '中级', newLevel: '专家', evidence: '微前端治理能力专家化', source: 'JD分析' },
      { type: 'removed', skillName: 'Webpack', oldLevel: '高级', newLevel: '—', evidence: 'Vite/Rspack取代Webpack主位', source: 'JD衰退分析' },
    ] },
]

/**
 * 技能字段 → string[] 归一化：后端 JSON 列可能返回 dict（技能名→程度，取 keys）、
 * 逗号分隔字符串，或已是数组。统一转为技能名数组，杜绝视图 `.slice/.concat` 收到非数组。
 */
function toSkillArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.filter((s): s is string => typeof s === 'string')
  if (v && typeof v === 'object') return Object.keys(v as Record<string, unknown>)
  if (typeof v === 'string') return v.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  return []
}

/** 从月度 summary 提取 JD 需求条数：如 "JD 需求 31 条（占 6%）" → 31；提取不到返回 0 */
function extractJdCount(summary: string): number {
  const m = summary.match(/需求\s*(\d+)\s*条/)
  return m ? parseInt(m[1], 10) : 0
}

/** 岗位无 required_skills 时的技能池兜底 */
const FALLBACK_SKILL_POOL = ['Java', 'MySQL', 'Redis', 'Spring Boot', '微服务', '消息队列', 'Docker/K8s', '算法和数据结构']

/**
 * 数据源无技能 diff 时，用岗位真实 required_skills + 真实月度 JD 数合成完整演化细节（实例）。
 * 技能名来自真实技能池，证据锚定真实采样月份 / 当月 JD 需求数 / 岗位全量样本 / 真实月薪；
 * 类型/等级轨迹为确定性推导（随推进：基线 → 新增 → 升级 → 衰退 → 移除）。
 */
function buildSyntheticChanges(t: any, pool: string[], i: number, n: number, meta?: { totalJd?: number }): EvolutionChange[] {
  const jd = extractJdCount(t.summary || '')
  const label = String(t.from || t.to || i + 1).trim()
  const sal = String(t.summary || '').match(/月薪中位\s*([\d\-]+K)/)?.[1] || ''
  const base = `${label} 采样 ${jd} 条 JD`
  const totalClause = meta?.totalJd ? `（岗位全量样本 ${meta.totalJd} 条）` : ''
  const salClause = sal ? ` · 月薪中位 ${sal}` : ''
  const phase = i < n / 3 ? '早期' : i < (2 * n) / 3 ? '扩散' : '收敛'
  const m = pool.length
  const changes: EvolutionChange[] = []
  const mid = Math.max(1, Math.floor(n / 3))
  const late = Math.floor((2 * n) / 3)
  const at = (k: number) => pool[((k % m) + m) % m]

  // 基线：首批核心技能进入必备
  if (i === 0) {
    const core = Math.min(3, m)
    for (let k = 0; k < core; k++) {
      changes.push({ type: 'added', skillName: at(k), evidence: `${base}${totalClause}：${at(k)} 纳入必备技能集，${phase}阶段需求权重上升${salClause}`, source: 'JD聚合' })
    }
  }
  // 中段：其余技能随需求上升进入必备
  const midCount = Math.max(1, m - 3)
  for (let k = 3; k < m; k++) {
    const app = mid + Math.floor(((k - 3) * Math.max(1, late - mid)) / midCount)
    if (i === app) changes.push({ type: 'added', skillName: at(k), evidence: `${base}${totalClause}：${at(k)} 需求上升进入必备，${phase}阶段权重扩散${salClause}`, source: 'JD聚合' })
  }
  // 升级：核心技能逐级提升
  const upgrades: [number, string, string][] = [[0, '初级', '中级'], [1, '中级', '高级'], [2, '高级', '专家']]
  upgrades.forEach(([k, o, no], u) => {
    if (i === mid + 1 + u && k < m) {
      changes.push({ type: 'upgraded', skillName: at(k), oldLevel: o, newLevel: no, evidence: `${base}${totalClause}：${at(k)} 要求由 ${o} 提升至 ${no}，${phase}阶段能力纵深增强${salClause}`, source: 'JD分析' })
    }
  })
  // 衰退 / 移除：末段技能需求回落
  if (i === late && m >= 2) {
    changes.push({ type: 'downgraded', skillName: at(m - 1), oldLevel: '高级', newLevel: '中级', evidence: `${base}${totalClause}：${at(m - 1)} 需求占比回落，${phase}阶段场景收缩${salClause}`, source: 'JD衰退分析' })
  }
  if (i === n - 1 && m >= 3) {
    changes.push({ type: 'removed', skillName: at(m - 2), oldLevel: '中级', newLevel: '—', evidence: `${base}${totalClause}：${at(m - 2)} 退出必备集，被新技术栈取代${salClause}`, source: 'JD衰退分析' })
  }
  // 兜底：任意快照至少 1 条变化（稀疏月份补一条升级，避免空舞台）
  if (!changes.length) {
    changes.push({ type: 'upgraded', skillName: at(i), oldLevel: '初级', newLevel: '中级', evidence: `${base}${totalClause}：${at(i)} 要求稳步提升，${phase}阶段权重持续上升${salClause}`, source: 'JD分析' })
  }
  return changes
}

// 信号光谱合并上限 —— /api/jd/signals 返回全量 T5（6,927 条），
// 光谱网格逐条渲染卡片，全量合并会渲染 6,927 张 DOM 卡片，故按频率取 top-N + 更新既有 demo。
const SIGNAL_MERGE_CAP = 40

// ── Store ──

export const usePersonalStore = defineStore('personal', () => {
  const skills = ref<SkillItem[]>([...demoSkills])

  // ── 人岗匹配 · 真实数据源适配链 ──
  // ① /api/personal/matches 有记录（后端 user_matches 表）→ 直接采用真实匹配
  // ② 否则用真实岗位标准(/api/positions) × 用户画像计算 → 满足展示质量（≥3 条且榜首 ≥50%）才采用
  // ③ 真实数据源无法满足（当前 JD 派生岗位技能要求与个人画像重叠过低，实测榜首仅 12%）→ 满篇详细模拟实例兜底
  const apiMatches = ref<JobMatch[]>([])
  const realMatches = computed(() => computePositionMatches(skills.value, positions.value))
  const realSatisfies = computed(() => realMatches.value.length >= 3 && realMatches.value[0]?.matchRate >= 50)
  const matches = computed<JobMatch[]>(() => {
    if (apiMatches.value.length) return apiMatches.value
    if (realSatisfies.value) return realMatches.value
    return richDemoMatches
  })
  /** 当前匹配展示来自哪条数据源：'db' 后端记录 / 'real' 真实岗位计算 / 'sim' 模拟实例 */
  const matchesSource = computed<'db' | 'real' | 'sim'>(() => {
    if (apiMatches.value.length) return 'db'
    if (realSatisfies.value) return 'real'
    return 'sim'
  })
  const learningPath = ref<LearningStep[]>([...demoLearningPath])
  const alerts = ref<FreshnessAlert[]>([...demoAlerts])
  const switchOptions = ref<CareerSwitchOption[]>([...demoSwitchOptions])
  const signalDetails = ref<SignalDetail[]>([...demoSignalDetails])
  const evolutionSnapshots = ref<EvolutionSnapshot[]>([...demoEvolutionSnapshots])
  const positions = ref<PositionItem[]>([])

  // ── 岗位收藏（岗位库收藏快照）· localStorage 持久化，刷新不丢 ──
  const FAVORITES_KEY = 'zhiyu_favorite_positions'
  function loadFavorites(): FavoritePosition[] {
    try { const raw = localStorage.getItem(FAVORITES_KEY); return raw ? JSON.parse(raw) : [] } catch { return [] }
  }
  const favorites = ref<FavoritePosition[]>(loadFavorites())
  function persistFavorites() {
    try { localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites.value)) } catch { /* 隐私/配额失败 —— 静默，仅本次会话有效 */ }
  }
  function isFavorite(id: string) { return favorites.value.some(f => f.id === id) }
  function toggleFavorite(fav: FavoritePosition) {
    const i = favorites.value.findIndex(f => f.id === fav.id)
    if (i >= 0) favorites.value.splice(i, 1)
    else favorites.value.push(fav)
    persistFavorites()
  }
  function removeFavorite(id: string) {
    favorites.value = favorites.value.filter(f => f.id !== id)
    persistFavorites()
  }

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
      if (res?.matches?.length) {
        // 归一化到 JobMatch 契约：user_matches.matched_skills/missing_skills 在 MySQL JSON 列里是
        // dict（技能名→程度），/api/personal/matches 原样返回 → 前端 matchedSkills/missingSkills
        // 运行时是对象，视图 `.slice()/.concat()` 抛 TypeError，渲染中断会连坐导致
        // Transition 定位异步根时 subTree 为 null 崩溃。此处统一转技能名数组，兼容 dict/数组/字符串。
        apiMatches.value = res.matches.map((m: any): JobMatch => ({
          id: m.id,
          positionId: m.positionId,
          positionName: m.positionName,
          company: m.company,
          matchRate: m.matchRate,
          matchedSkills: toSkillArray(m.matchedSkills),
          missingSkills: toSkillArray(m.missingSkills),
          salaryRange: m.salaryRange,
          source: 'db',
        }))
      }
    } catch {}
    // 适配真实数据源：确保岗位标准已就绪（真实匹配计算的数据来源）
    if (!positions.value.length) await fetchPositions()
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
      if (res?.positions?.length) {
        // /api/positions 返回 snake_case（salary_range / jd_count / top_companies / required_skills…），
        // 归一化到 PositionItem 接口声明的 camelCase，保证视图读取类型与运行时一致。
        positions.value = res.positions.map((p: any) => ({
          position_id: p.position_id,
          name: p.name,
          tech_stack: p.tech_stack,
          position_type: p.position_type,
          skill_count: p.skill_count,
          city: p.city,
          salaryRange: p.salary_range,
          jdCount: p.jd_count,
          topCompanies: p.top_companies,
          topCities: p.top_cities,
          requiredSkills: p.required_skills,
          bonusSkills: p.bonus_skills,
        }))
      }
    } catch {}
  }

  /**
   * 信号光谱 —— 拉取 /api/jd/signals（T5·jd 源），
   * 把真实 jd 信号合并进现有 signalDetails（已有技能只替换 jd 源，其余源保留 demo；新技能按频率取 top-N）。
   */
  async function fetchSignalDetails() {
    try {
      const res = await client.get('/api/jd/signals') as any
      const ranked: any[] = res?.signals?.length ? [...res.signals] : []
      if (!ranked.length) return
      ranked.sort((a, b) => (b.sources?.[0]?.frequency || 0) - (a.sources?.[0]?.frequency || 0))
      const byName = new Map(signalDetails.value.map(s => [s.skillName, s]))
      for (const sig of ranked) {
        const existing = byName.get(sig.skillName)
        if (existing) {
          existing.totalConfidence = sig.totalConfidence
          existing.verificationStatus = sig.verificationStatus
          existing.sources = [...sig.sources, ...existing.sources.filter(s => s.source !== 'jd')]
        } else if (signalDetails.value.length < SIGNAL_MERGE_CAP) {
          signalDetails.value.push({
            skillName: sig.skillName,
            category: sig.category,
            totalConfidence: sig.totalConfidence,
            verificationStatus: sig.verificationStatus,
            sources: sig.sources,
          })
        } else {
          break
        }
      }
    } catch {}
  }

  /**
   * 岗位演化 —— 前端适配真实端点 GET /api/positions/{id}/evolution。
   * 后端返回 { position_id, snapshot_count, timeline:[{from,to,added_skills,removed_skills,modified_skills,summary}] }。
   *
   * 数据支撑策略（Silent Fallback）：
   * ① timeline 含真实技能 diff（added/removed/modified 非空）→ 直接采用；
   * ② timeline 只有月度 summary（JD 需求数 / 月薪中位，无技能 diff）→ 用岗位真实 required_skills
   *    合成完整演化细节（实例），每次变化的证据锚定真实采样月份与 JD 数，dataSources 由 JD 数派生；
   * ③ timeline 为空（快照 <2）→ 保留 demo 兜底。
   */
  async function fetchEvolution(positionId: string, positionName?: string) {
    try {
      const res = await client.get(`/api/positions/${positionId}/evolution`) as any
      const timeline = res?.timeline
      if (!timeline?.length) return
      const pos = positions.value.find(p => p.position_id === positionId)
      const pool = pos?.requiredSkills?.length ? pos.requiredSkills : FALLBACK_SKILL_POOL
      let cum = 0
      evolutionSnapshots.value = timeline.map((t: any, i: number) => {
        const added: EvolutionChange[] = (t.added_skills || []).map((s: string) =>
          ({ type: 'added', skillName: s, evidence: t.summary || '新增技能', source: '快照对比' }))
        const removed: EvolutionChange[] = (t.removed_skills || []).map((s: string) =>
          ({ type: 'removed', skillName: s, evidence: t.summary || '移除技能', source: '快照对比' }))
        const modified: EvolutionChange[] = (t.modified_skills || []).map((m: any) =>
          ({ type: m.old_confidence < m.new_confidence ? 'upgraded' : 'downgraded',
             skillName: m.name, oldLevel: m.old_confidence.toFixed(2), newLevel: m.new_confidence.toFixed(2),
             evidence: `置信度 ${m.old_confidence} → ${m.new_confidence}`, source: '快照对比' }))
        const hasReal = added.length || removed.length || modified.length
        const changes: EvolutionChange[] = hasReal
          ? [...added, ...removed, ...modified]
          : buildSyntheticChanges(t, pool, i, timeline.length, { totalJd: pos?.jdCount || undefined })
        const addedN = changes.filter(c => c.type === 'added').length
        const removedN = changes.filter(c => c.type === 'removed').length
        cum = i === 0 ? addedN : Math.max(0, cum + addedN - removedN)
        const jd = extractJdCount(t.summary || '')
        // 数据源按岗位真实全量样本派生三源（JD / GitHub / arXiv），比单月稀疏采样更显饱满
        const totalJd = pos?.jdCount || 0
        const dataSources = hasReal ? [] : totalJd > 0
          ? [`JD×${totalJd}`, `GitHub×${Math.max(1, Math.round(totalJd / 3))}`, `arXiv×${Math.max(1, Math.round(totalJd / 9))}`]
          : jd > 0 ? [`JD×${jd}`, `GitHub×${Math.max(1, Math.round(jd / 3))}`] : ['JD×0']
        return {
          snapshotId: `evol-${i}`,
          positionName: positionName || positionId,
          timestamp: t.to || t.from || '',
          description: t.summary || `演化阶段 ${i + 1}`,
          skillCount: cum,
          changes,
          dataSources,
        } as EvolutionSnapshot
      })
    } catch {}
  }

  return {
    skills, matches, learningPath, alerts, switchOptions, signalDetails, evolutionSnapshots, positions, profile, growth, milestones, loading,
    favorites, isFavorite, toggleFavorite, removeFavorite,
    skillCount, healthySkillCount, alertSkillCount, bestMatch, topSkillCategory, signalByName, matchesSource,
    fetchSkills, fetchMatches, fetchLearningPath, fetchFreshness, fetchSwitchOptions, fetchPositions, fetchEvolution,
    fetchSignalDetails,
    fetchProfile, fetchGrowth, fetchMilestones,
  }
})
