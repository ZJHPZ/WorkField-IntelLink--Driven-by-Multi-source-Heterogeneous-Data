// ═══════════════════════════════════════════════
// 图谱蓝图 · 数据纯函数层
// normalizeGraph: 后端 G6 v5 格式 → ECharts 图序列
// buildDemoGraph: 由岗位标准生成丰富 demo（岗位/技能/技术栈/证据 + 五类边）
// ═══════════════════════════════════════════════

// ── G6 v5 形状（与后 /api/graph 对齐）──
export interface GraphNodeV5 {
  id: string
  data: Record<string, any>
}
export interface GraphEdgeV5 {
  id?: string
  source: string
  target: string
  data: Record<string, any>
}
export interface GraphDataV5 {
  nodes: GraphNodeV5[]
  edges: GraphEdgeV5[]
}

// ── normalize 后的 ECharts 图序列 ──
export type ChartNodeKind = 'position' | 'skill' | 'stack' | 'evidence'
export interface ChartNode {
  id: string
  name: string
  kind: ChartNodeKind
  symbolSize: number
  itemStyle: Record<string, any>
  label: Record<string, any>
  _metrics?: Record<string, any>
  _stack?: string
  _level?: string
  _posType?: string
  _verification?: string
  _evidence?: { text: string; source: string; timestamp: string }[]
}
export interface ChartLink {
  source: string
  target: string
  rel: string
  lineStyle: Record<string, any>
  _strength?: number
  _requiredType?: string
}
export interface ChartGraph {
  nodes: ChartNode[]
  links: ChartLink[]
}

// 蓝皮书三色 + 结构灰阶
const NAVY = '#00094C'
const NAVY_900 = '#121A57'
const NAVY_700 = '#1E2A5A'
const CORAL = '#C85C56'
const CORAL_SOFT = '#EAD2D0'
const INK = '#16213E'
const INK_MUTED = '#5B6478'
const DIM = '#9AA1B1'
const RULE = '#D9DDE7'
const WHITE = '#FFFFFF'

// ── normalizeGraph：G6 v5 → ECharts ──
export function normalizeGraph(nodes: GraphNodeV5[], edges: GraphEdgeV5[]): ChartGraph {
  const chartNodes: ChartNode[] = []
  const chartLinks: ChartLink[] = []
  const byId = new Map<string, ChartNode>()

  for (const n of nodes) {
    const d = n.data || {}
    const nodeType: string = d.nodeType || 'Skill'
    const label: string = d.label || n.id

    let node: ChartNode
    if (nodeType === 'Position') {
      node = {
        id: n.id,
        name: label,
        kind: 'position',
        symbolSize: 30 + Math.min(14, (d.confidence || 0.8) * 10),
        itemStyle: { color: NAVY, borderColor: NAVY, borderWidth: 0, borderRadius: 2 },
        label: { color: WHITE, fontWeight: 700 },
        _posType: d.position_type || '既有',
        _level: d.level,
        _metrics: { confidence: d.confidence, marketDemand: d.marketDemand, matchRate: d.matchRate },
      }
    } else if (nodeType === 'TechStack') {
      node = {
        id: n.id,
        name: label,
        kind: 'stack',
        symbolSize: 24,
        itemStyle: { color: 'rgba(0,9,76,0.03)', borderColor: NAVY_700, borderWidth: 1, borderDash: [3, 2] },
        label: { color: INK_MUTED, fontSize: 9, fontWeight: 700, letterSpacing: 2 },
      }
    } else if (nodeType === 'Evidence') {
      node = {
        id: n.id,
        name: label,
        kind: 'evidence',
        symbolSize: 4,
        itemStyle: { color: DIM, borderWidth: 0 },
        label: { show: false },
        _metrics: { source: d.source, timestamp: d.timestamp, text: d.text },
      }
    } else {
      // Skill
      const df = d.df ?? 0.5
      node = {
        id: n.id,
        name: label,
        kind: 'skill',
        symbolSize: 12 + Math.min(14, df * 18),
        itemStyle: { color: WHITE, borderColor: NAVY, borderWidth: 1.5 },
        label: { color: INK, fontSize: 10, fontWeight: 700 },
        _metrics: {
          df, confidence: d.confidence, emergence: d.emergence, decline: d.decline,
          halfLife: d.half_life, volatility: d.volatility, requiredCount: d.required_count,
          bonusCount: d.bonus_count, verificationStatus: d.verification_status, status: d.status,
        },
        _verification: d.verification_status || 'pending',
        _stack: d.stack,
        _evidence: d.evidence || [],
      }
    }
    chartNodes.push(node)
    byId.set(n.id, node)
  }

  for (const e of edges) {
    const d = e.data || {}
    const rel: string = d.rel || 'REQUIRES'
    const strength = d.strength ?? 0.5
    let lineStyle: Record<string, any>

    if (rel === 'REQUIRES') {
      lineStyle = d.required_type === '必备'
        ? { color: NAVY, width: 2, type: 'solid' }
        : { color: NAVY, width: 1.5, type: 'dashed' }
    } else if (rel === 'CO_OCCURS') {
      lineStyle = { color: CORAL, width: 1 + Math.min(2, strength * 2), opacity: 0.42, type: 'dashed' }
    } else if (rel === 'BELONGS_TO') {
      lineStyle = { color: RULE, width: 1, type: 'solid' }
    } else if (rel === 'SUPPORTED_BY') {
      lineStyle = { color: DIM, width: 1, type: 'dotted' }
    } else {
      // IN_STACK
      lineStyle = { color: RULE, width: 1, type: 'dashed' }
    }

    chartLinks.push({
      source: e.source,
      target: e.target,
      rel,
      lineStyle,
      _strength: strength,
      _requiredType: d.required_type,
    })
  }

  return { nodes: chartNodes, links: chartLinks }
}

// ── buildDemoGraph：由岗位标准生成 G6 v5 demo 图 ──
export interface DemoPositionInput {
  id: string
  name: string
  department: string
  level: string
  status: string
  marketDemand: number
  matchRate: number
  skills: { name: string; level: string; weight: number; trend: string; freshness: number }[]
}

const STACK_OF: Record<string, string> = {
  'AI 算法工程师': 'AI',
  '全栈开发工程师': '前端',
  '数据分析师': '数据',
  '技术项目经理': '后端',
  'DevOps 工程师': 'DevOps',
  '前端开发工程师': '前端',
  '资深后端工程师': '后端',
  'QA 测试工程师': '质量',
}

// 跨岗位高共现对（strength）
const COOCCUR_PAIRS: [string, string, number][] = [
  ['大模型微调', 'RAG 应用', 0.86],
  ['RAG 应用', 'Agent 编排', 0.8],
  ['大模型微调', 'Agent 编排', 0.72],
  ['Python', '深度学习', 0.68],
  ['深度学习', 'NLP', 0.72],
  ['NLP', 'RAG 应用', 0.78],
  ['React', 'TypeScript', 0.75],
  ['TypeScript', 'CSS/Tailwind', 0.6],
  ['Node.js', 'Docker/K8s', 0.55],
  ['Go/Rust', '系统设计', 0.7],
  ['Go/Rust', 'Kubernetes', 0.62],
  ['SQL', '统计学', 0.6],
  ['SQL', 'Python', 0.66],
  ['Docker/K8s', 'CI/CD', 0.65],
  ['CI/CD', '监控告警', 0.58],
  ['自动化测试', '性能测试', 0.6],
  ['自动化测试', '测试框架', 0.72],
  ['MLOps', '分布式训练', 0.64],
  ['MLOps', '大模型微调', 0.7],
  ['联邦学习', '数据安全合规', 0.5],
]

// 证据样本池（按技能名）
const EVIDENCE_POOL: Record<string, { text: string; source: string; timestamp: string }[]> = {
  '大模型微调': [
    { text: '岗位职责明确要求大模型 SFT/RLHF 微调经验，2026 年需求占比同比 +180%', source: '招聘JD · 大厂AI岗', timestamp: '2026-07' },
    { text: '行业报告将微调能力列为 2026 下半年 AI 工程师核心技能', source: '行业报告 · AI人才趋势', timestamp: '2026-06' },
  ],
  'RAG 应用': [
    { text: '检索增强生成成为企业知识库标配，JD 提及率升至 42%', source: '招聘JD · 知识库方向', timestamp: '2026-07' },
  ],
  'Agent 编排': [
    { text: '多智能体编排框架在金融/客服场景落地，人才缺口显著', source: '招聘JD · 智能体方向', timestamp: '2026-07' },
  ],
  '联邦学习': [
    { text: '隐私计算合规推动联邦学习进入金融试点', source: '行业报告 · 隐私计算', timestamp: '2026-05' },
  ],
  'Kubernetes': [
    { text: '云原生岗位普遍要求 K8s 生产级运维能力', source: '招聘JD · 云平台岗', timestamp: '2026-06' },
  ],
  '深度学习': [
    { text: '深度学习仍是 CV/NLP 岗位的硬性门槛技能', source: '招聘JD · 算法岗', timestamp: '2026-07' },
  ],
}

export function buildDemoGraph(positions: DemoPositionInput[]): GraphDataV5 {
  const nodes: GraphNodeV5[] = []
  const edges: GraphEdgeV5[] = []
  const stackSet = new Set<string>()
  const skillStack = new Map<string, string>()   // skillName → stack
  const requiredCount = new Map<string, number>()
  const bonusCount = new Map<string, number>()
  const extraSkills = [
    { name: '大模型微调', level: 'advanced', freshness: 90, trend: 'rising' },
    { name: 'RAG 应用', level: 'intermediate', freshness: 86, trend: 'rising' },
    { name: 'Agent 编排', level: 'intermediate', freshness: 84, trend: 'rising' },
    { name: '端侧 AI', level: 'basic', freshness: 74, trend: 'rising' },
    { name: '联邦学习', level: 'basic', freshness: 66, trend: 'rising' },
  ]

  // 1) 岗位 + 技术栈节点，技能计数
  for (const pos of positions) {
    const stack = STACK_OF[pos.name] || '后端'
    stackSet.add(stack)
    nodes.push({
      id: `pos::${pos.id}`,
      data: {
        nodeType: 'Position', label: pos.name, tech_stack: stack,
        position_type: pos.status === 'emerging' ? '新兴' : '既有',
        confidence: 0.8, level: pos.level, marketDemand: pos.marketDemand, matchRate: pos.matchRate,
      },
    })
    for (const s of pos.skills) {
      skillStack.set(s.name, stack)
      if (s.weight >= 0.2) requiredCount.set(s.name, (requiredCount.get(s.name) || 0) + 1)
      else bonusCount.set(s.name, (bonusCount.get(s.name) || 0) + 1)
    }
  }
  for (const stack of stackSet) {
    nodes.push({ id: `stack::${stack}`, data: { nodeType: 'TechStack', label: stack } })
  }

  // 2) 技能节点（岗位技能 + 追加市场热词）
  const skillNames = new Set<string>()
  for (const pos of positions) for (const s of pos.skills) skillNames.add(s.name)
  for (const s of extraSkills) { skillNames.add(s.name); if (!skillStack.has(s.name)) skillStack.set(s.name, 'AI') }

  for (const name of skillNames) {
    const freshness = positions
      .flatMap((p) => p.skills)
      .find((s) => s.name === name)?.freshness
      ?? extraSkills.find((s) => s.name === name)?.freshness ?? 60
    const trend = positions
      .flatMap((p) => p.skills)
      .find((s) => s.name === name)?.trend ?? 'stable'

    const status = freshness >= 80 ? 'confirmed' : freshness >= 60 ? 'pending' : 'rejected'
    const verification = status
    nodes.push({
      id: `skill::${name}`,
      data: {
        nodeType: 'Skill', label: name, df: 0.15 + (freshness / 100) * 0.7,
        confidence: 0.6 + (freshness / 100) * 0.35,
        required_count: requiredCount.get(name) || 0,
        bonus_count: bonusCount.get(name) || 0,
        verification_status: verification, status,
        emergence: trend === 'rising' ? 0.5 + (freshness / 100) * 0.45 : trend === 'declining' ? 0.15 : 0.3,
        decline: trend === 'declining' ? 0.5 + (100 - freshness) / 100 * 0.4 : 0.15,
        half_life: Math.round(10 + (freshness / 100) * 26),
        volatility: Math.round((0.15 + (100 - freshness) / 100 * 0.3) * 100) / 100,
        stack: skillStack.get(name),
        evidence: EVIDENCE_POOL[name] || [],
      },
    })
  }

  // 3) 岗位-技能 REQUIRES + 岗位-栈 IN_STACK
  for (const pos of positions) {
    const stack = STACK_OF[pos.name] || '后端'
    edges.push({ id: `e-in-${pos.id}`, source: `pos::${pos.id}`, target: `stack::${stack}`, data: { rel: 'IN_STACK' } })
    for (const s of pos.skills) {
      edges.push({
        id: `e-req-${pos.id}-${s.name}`, source: `pos::${pos.id}`, target: `skill::${s.name}`,
        data: { rel: 'REQUIRES', required_type: s.weight >= 0.2 ? '必备' : '加分' },
      })
    }
  }

  // 4) 技能-栈 BELONGS_TO
  for (const name of skillNames) {
    const stack = skillStack.get(name)
    if (stack) edges.push({ id: `e-bel-${name}`, source: `skill::${name}`, target: `stack::${stack}`, data: { rel: 'BELONGS_TO' } })
  }

  // 5) 技能-技能 CO_OCCURS（同岗位两两 + 高共现对）
  const coPairs = new Set<string>()
  for (const pos of positions) {
    for (let i = 0; i < pos.skills.length; i++) {
      for (let j = i + 1; j < pos.skills.length; j++) {
        const a = pos.skills[i].name, b = pos.skills[j].name
        const key = [a, b].sort().join('|')
        if (!coPairs.has(key)) { coPairs.add(key); edges.push({ id: `e-co-${a}-${b}`, source: `skill::${a}`, target: `skill::${b}`, data: { rel: 'CO_OCCURS', strength: 0.45 + ((i * 7 + j * 5) % 3) * 0.1 } }) }
      }
    }
  }
  for (const [a, b, strength] of COOCCUR_PAIRS) {
    if (!skillNames.has(a) || !skillNames.has(b)) continue
    const key = [a, b].sort().join('|')
    if (!coPairs.has(key)) { coPairs.add(key); edges.push({ id: `e-co-${a}-${b}`, source: `skill::${a}`, target: `skill::${b}`, data: { rel: 'CO_OCCURS', strength } }) }
  }

  // 6) 部分技能的证据节点 SUPPORTED_BY
  const withEvidence = ['大模型微调', 'RAG 应用', 'Agent 编排', '联邦学习', 'Kubernetes', '深度学习']
  for (const name of withEvidence) {
    const evs = EVIDENCE_POOL[name] || []
    if (!evs.length || !skillNames.has(name)) continue
    const ev = evs[0]
    const evId = `ev::${name}`
    nodes.push({ id: evId, data: { nodeType: 'Evidence', label: ev.text.slice(0, 22), text: ev.text, source: ev.source, timestamp: ev.timestamp } })
    edges.push({ id: `e-sup-${name}`, source: `skill::${name}`, target: evId, data: { rel: 'SUPPORTED_BY' } })
  }

  return { nodes, edges }
}
