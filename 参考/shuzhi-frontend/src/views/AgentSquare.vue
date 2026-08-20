<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- ===== 顶部英雄区 ===== -->
    <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-purple-500 to-fuchsia-500 p-6 md:p-8 text-white shadow-xl shadow-purple-500/20">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-6 right-20 w-40 h-40 rounded-full bg-white blur-3xl"></div>
        <div class="absolute bottom-0 left-1/3 w-56 h-28 rounded-full bg-fuchsia-300 blur-3xl"></div>
        <div class="absolute top-1/2 left-10 w-20 h-20 rounded-full bg-cyan-300 blur-2xl"></div>
      </div>
      <div class="relative">
        <div class="flex items-center gap-3 mb-3">
          <span class="text-4xl animate-float">🤖</span>
          <div>
            <h1 class="text-2xl md:text-3xl font-bold">多智能体架构</h1>
            <p class="text-sm text-white/70 mt-1">帕克的核心 — 16 个专业智能体协同作战</p>
          </div>
        </div>
        <p class="text-sm text-white/80 leading-relaxed max-w-2xl">
          帕克不是单一的 AI，而是一个由 <span class="font-bold text-white">16 个专业智能体</span> 组成的协作团队。
          当你提出问题时，<span class="font-bold text-white">调度智能体</span> 会理解你的意图，
          将任务拆解并分配给最合适的专业智能体，它们各司其职、协同作战，为你提供最精准的回答。
        </p>
      </div>
    </div>

    <!-- ===== 协作流程图 ===== -->
    <div class="glass-card rounded-2xl p-6 overflow-hidden">
      <h2 class="text-base font-semibold mb-2 flex items-center gap-2" style="color: var(--text-primary);">
        <span class="text-lg">🔄</span> 协作流程
      </h2>
      <p class="text-xs mb-6" style="color: var(--text-muted);">一次提问，多个智能体协同响应</p>

      <!-- 三阶段水平流程 -->
      <div class="flow-stage-row">
        <!-- 阶段 1: 输入 -->
        <div class="flow-stage">
          <div class="flow-stage-num">1</div>
          <div class="flow-stage-card flow-stage-input">
            <div class="flow-stage-emoji">👤</div>
            <div class="flow-stage-title">用户输入</div>
            <div class="flow-stage-items">
              <span class="flow-chip">💬 文字</span>
              <span class="flow-chip">🖼️ 图片</span>
              <span class="flow-chip">📎 文件</span>
              <span class="flow-chip">🎙️ 语音</span>
            </div>
          </div>
        </div>

        <!-- 箭头 -->
        <div class="flow-stage-arrow">
          <svg width="48" height="24" viewBox="0 0 48 24">
            <defs>
              <linearGradient id="arrow-grad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="rgba(99,102,241,0.15)"/>
                <stop offset="100%" stop-color="rgba(99,102,241,0.4)"/>
              </linearGradient>
            </defs>
            <line x1="0" y1="12" x2="36" y2="12" stroke="url(#arrow-grad)" stroke-width="2" stroke-dasharray="4 3"/>
            <polygon points="36,6 48,12 36,18" fill="rgba(99,102,241,0.35)"/>
          </svg>
        </div>

        <!-- 阶段 2: 调度 -->
        <div class="flow-stage">
          <div class="flow-stage-num">2</div>
          <div class="flow-stage-card flow-stage-orchestrator">
            <div class="orchestrator-ring">
              <div class="orchestrator-ring-inner">
                <div class="flow-stage-emoji">🧠</div>
              </div>
            </div>
            <div class="flow-stage-title">调度智能体</div>
            <div class="flow-stage-subtitle">意图识别 · 任务拆解 · 智能路由</div>
            <div class="flow-stage-badge">核心枢纽</div>
          </div>
        </div>

        <!-- 箭头 -->
        <div class="flow-stage-arrow">
          <svg width="48" height="24" viewBox="0 0 48 24">
            <line x1="0" y1="12" x2="36" y2="12" stroke="url(#arrow-grad)" stroke-width="2" stroke-dasharray="4 3"/>
            <polygon points="36,6 48,12 36,18" fill="rgba(99,102,241,0.35)"/>
          </svg>
        </div>

        <!-- 阶段 3: 专业智能体 -->
        <div class="flow-stage flow-stage-wide">
          <div class="flow-stage-num">3</div>
          <div class="flow-stage-card flow-stage-agents">
            <div class="flow-stage-title" style="margin-bottom: 10px;">专业智能体协作</div>
            <div class="flow-agents-ring">
              <!-- 中心 -->
              <div class="agents-ring-hub">
                <span>⚡</span>
              </div>
              <!-- 环绕节点 -->
              <div v-for="(agent, i) in ringAgents" :key="agent.id"
                class="agents-ring-node"
                :style="ringPosition(i, ringAgents.length)"
                :class="{ 'ring-node-active': activeAgentId === agent.id }"
              >
                <span class="ring-node-icon">{{ agent.icon }}</span>
                <span class="ring-node-label">{{ agent.name }}</span>
              </div>
              <!-- 连线 SVG -->
              <svg class="agents-ring-lines" viewBox="0 0 280 280">
                <line v-for="(agent, i) in ringAgents" :key="'line-'+agent.id"
                  :x1="140" :y1="140"
                  :x2="ringXY(i, ringAgents.length).x" :y2="ringXY(i, ringAgents.length).y"
                  :stroke="activeAgentId === agent.id ? 'rgba(99,102,241,0.5)' : 'rgba(99,102,241,0.12)'"
                  :stroke-width="activeAgentId === agent.id ? 2 : 1"
                  stroke-dasharray="4 3"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- 箭头 -->
        <div class="flow-stage-arrow">
          <svg width="48" height="24" viewBox="0 0 48 24">
            <line x1="0" y1="12" x2="36" y2="12" stroke="url(#arrow-grad)" stroke-width="2" stroke-dasharray="4 3"/>
            <polygon points="36,6 48,12 36,18" fill="rgba(99,102,241,0.35)"/>
          </svg>
        </div>

        <!-- 阶段 4: 输出 -->
        <div class="flow-stage">
          <div class="flow-stage-num">4</div>
          <div class="flow-stage-card flow-stage-output">
            <div class="flow-stage-emoji">✨</div>
            <div class="flow-stage-title">智能回复</div>
            <div class="flow-stage-items">
              <span class="flow-chip flow-chip-green">📝 文字解答</span>
              <span class="flow-chip flow-chip-green">📊 图表生成</span>
              <span class="flow-chip flow-chip-green">🔊 语音播报</span>
              <span class="flow-chip flow-chip-green">📄 文档输出</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 智能体分类展示 ===== -->
    <div v-for="category in categories" :key="category.title" class="glass-card rounded-2xl p-6">
      <h2 class="text-base font-semibold mb-4 flex items-center gap-2" style="color: var(--text-primary);">
        <span class="text-lg">{{ category.icon }}</span> {{ category.title }}
        <span class="text-xs font-normal px-2 py-0.5 rounded-full" style="background: rgba(99,102,241,0.08); color: var(--text-muted);">
          {{ category.agents.length }} 个智能体
        </span>
      </h2>
      <p class="text-sm mb-5" style="color: var(--text-secondary);">{{ category.desc }}</p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div
          v-for="agent in category.agents"
          :key="agent.id"
          class="agent-card"
          :class="{ 'agent-card-active': activeAgentId === agent.id }"
        >
          <div class="flex items-start gap-3.5">
            <div class="agent-icon-wrapper" :style="{ background: agent.bgColor }">
              <span class="text-xl">{{ agent.icon }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-bold" style="color: var(--text-primary);">{{ agent.name }}</span>
                <span v-if="activeAgentId === agent.id" class="agent-badge-running">运行中</span>
              </div>
              <p class="text-xs leading-relaxed mb-2" style="color: var(--text-secondary);">{{ agent.desc }}</p>
              <div class="flex flex-wrap gap-1">
                <span v-for="tag in agent.tags" :key="tag" class="agent-tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 底部说明 ===== -->
    <div class="glass-card rounded-2xl p-5 flex items-start gap-3">
      <span class="text-xl shrink-0">💡</span>
      <div>
        <p class="text-sm font-medium" style="color: var(--text-primary);">如何触发不同智能体？</p>
        <p class="text-xs mt-1 leading-relaxed" style="color: var(--text-secondary);">
          直接用自然语言提问即可。例如问「什么是 Hadoop？」会触发答疑智能体，
          说「帮我规划学习路径」会触发学习路径智能体，上传图片会自动唤醒多模态理解智能体。
          调度智能体会根据你的意图自动选择最合适的专业智能体，你无需手动切换。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const activeAgentId = computed(() => chatStore.activeAgent?.id || '')

interface AgentInfo {
  id: string
  name: string
  icon: string
  desc: string
  tags: string[]
  bgColor: string
}

interface AgentCategory {
  title: string
  icon: string
  desc: string
  agents: AgentInfo[]
}

const ringAgents = [
  { id: 'conversation', name: '对话', icon: '💬' },
  { id: 'learning_path', name: '路径', icon: '🗺️' },
  { id: 'question', name: '出题', icon: '📝' },
  { id: 'qa', name: '答疑', icon: '🔍' },
  { id: 'evaluation', name: '评估', icon: '📊' },
  { id: 'document', name: '文档', icon: '📄' },
  { id: 'multimodal', name: '多模态', icon: '👁️' },
  { id: 'resource', name: '资源', icon: '🌐' },
]

function ringPosition(i: number, total: number) {
  const angle = (i / total) * 2 * Math.PI - Math.PI / 2
  const r = 110
  const cx = 140 + r * Math.cos(angle) - 30
  const cy = 140 + r * Math.sin(angle) - 30
  return { left: cx + 'px', top: cy + 'px' }
}

function ringXY(i: number, total: number) {
  const angle = (i / total) * 2 * Math.PI - Math.PI / 2
  const r = 110
  return {
    x: 140 + r * Math.cos(angle),
    y: 140 + r * Math.sin(angle),
  }
}

const allAgents: AgentInfo[] = [
  {
    id: 'orchestrator',
    name: '调度智能体',
    icon: '🧠',
    desc: '帕克的大脑。理解用户意图，拆解复杂需求，规划多智能体协作流程，将任务精准分派给最合适的专业智能体。',
    tags: ['意图识别', '任务拆解', '智能路由', '协作调度'],
    bgColor: 'rgba(99,102,241,0.12)',
  },
  {
    id: 'conversation',
    name: '对话智能体',
    icon: '💬',
    desc: '负责理解你的学习需求和背景，维护多轮对话上下文，构建你的学习者画像，让每次对话都更懂你。',
    tags: ['需求分析', '上下文管理', '画像构建'],
    bgColor: 'rgba(16,185,129,0.12)',
  },
  {
    id: 'learning_path',
    name: '学习路径智能体',
    icon: '🗺️',
    desc: '翻阅知识图谱，根据你的当前水平和学习目标，规划个性化的学习路线，动态调整学习计划和节奏。',
    tags: ['路径规划', '知识图谱', '个性化推荐'],
    bgColor: 'rgba(245,158,11,0.12)',
  },
  {
    id: 'question',
    name: '题库智能体',
    icon: '📝',
    desc: '精心设计练习题，挑选合适的考察角度，校准题目难度，确保干扰项有区分度，让每道题都有训练价值。',
    tags: ['题目生成', '难度校准', '选项设计'],
    bgColor: 'rgba(239,68,68,0.12)',
  },
  {
    id: 'document',
    name: '文档智能体',
    icon: '📄',
    desc: '整理知识要点，构建文档框架，撰写结构化学习笔记，绘制思维导图，将零散知识编织成体系。',
    tags: ['笔记生成', '思维导图', '知识梳理'],
    bgColor: 'rgba(168,85,247,0.12)',
  },
  {
    id: 'evaluation',
    name: '评估智能体',
    icon: '📊',
    desc: '评估你的回答质量，分析知识薄弱环节，对比标准答案逐项打分，生成详细的学习评估报告。',
    tags: ['回答评估', '薄弱点分析', '学习报告'],
    bgColor: 'rgba(20,184,166,0.12)',
  },
  {
    id: 'qa',
    name: '答疑智能体',
    icon: '🔍',
    desc: '在知识库中搜索最佳答案，追根溯源寻找真相，关联相关知识点构建知识网络，给你通俗易懂的解释。',
    tags: ['知识搜索', '深度解答', '知识关联'],
    bgColor: 'rgba(59,130,246,0.12)',
  },
  {
    id: 'multimedia',
    name: '多媒体智能体',
    icon: '🎨',
    desc: '生成教学示意图、概念关系图和可视化讲解素材，将抽象概念转化为直观的视觉表达。',
    tags: ['图表生成', '可视化', '概念图'],
    bgColor: 'rgba(236,72,153,0.12)',
  },
  {
    id: 'multimodal',
    name: '多模态理解智能体',
    icon: '👁️',
    desc: '识别图片中的内容，提取文字信息，理解图像中的知识点，结合图片内容分析你提出的问题。',
    tags: ['图像识别', 'OCR', '图文理解'],
    bgColor: 'rgba(139,92,246,0.12)',
  },
  {
    id: 'audio',
    name: '语音处理智能体',
    icon: '🎙️',
    desc: '将文字转为自然流畅的语音朗读，识别语音输入内容，支持多种音色选择，让学习更沉浸。',
    tags: ['TTS 语音合成', 'ASR 语音识别', '多音色'],
    bgColor: 'rgba(249,115,22,0.12)',
  },
  {
    id: 'rag_question',
    name: '题库检索智能体',
    icon: '📚',
    desc: '在海量题库中搜索相关题目，根据知识点精准筛选，从题库中调取最佳匹配的练习题和真题。',
    tags: ['题库检索', '知识点匹配', '真题调取'],
    bgColor: 'rgba(34,197,94,0.12)',
  },
  {
    id: 'resource',
    name: '资源搜索智能体',
    icon: '🌐',
    desc: '搜索互联网学习资源，检索官方文档和社区讨论，查找 B 站教学视频，为你找到最好的学习材料。',
    tags: ['资源搜索', '文档检索', '视频查找'],
    bgColor: 'rgba(6,182,212,0.12)',
  },
  {
    id: 'diagnosis',
    name: '诊断智能体',
    icon: '🩺',
    desc: '诊断你的知识薄弱点，分析错题模式，评估知识盲区，定位根源问题，给出针对性提升建议。',
    tags: ['薄弱点诊断', '错题分析', '盲区定位'],
    bgColor: 'rgba(244,63,94,0.12)',
  },
  {
    id: 'recommendation',
    name: '推荐智能体',
    icon: '💡',
    desc: '筛选学习资源，分析你的学习偏好，匹配推荐内容，生成个性化的学习建议和资源清单。',
    tags: ['资源筛选', '偏好分析', '个性推荐'],
    bgColor: 'rgba(251,191,36,0.12)',
  },
  {
    id: 'bigdata_learning',
    name: '大数据学习智能体',
    icon: '📊',
    desc: '专注于大数据领域，检索大数据知识图谱，梳理 Hadoop/Spark/Flink 等技术栈关联，分析学习路径。',
    tags: ['大数据', '技术栈梳理', '学习路径'],
    bgColor: 'rgba(99,102,241,0.12)',
  },
  {
    id: 'learning_engine',
    name: '学习引擎智能体',
    icon: '⚙️',
    desc: '分析你的学习进度数据，基于遗忘曲线计算最佳复习时间，动态调整学习策略，让学习更高效。',
    tags: ['进度分析', '复习调度', '策略优化'],
    bgColor: 'rgba(107,114,128,0.12)',
  },
]

const agents = allAgents

const categories: AgentCategory[] = [
  {
    title: '核心调度',
    icon: '🧠',
    desc: '理解意图、拆解任务、协调全局',
    agents: allAgents.filter(a => ['orchestrator'].includes(a.id)),
  },
  {
    title: '学习辅助',
    icon: '📖',
    desc: '围绕学习场景的专业智能体，覆盖从规划到评估的完整学习链路',
    agents: allAgents.filter(a => ['conversation', 'learning_path', 'qa', 'evaluation', 'learning_engine', 'bigdata_learning'].includes(a.id)),
  },
  {
    title: '内容生成',
    icon: '✏️',
    desc: '生成题目、文档、图表等学习内容',
    agents: allAgents.filter(a => ['question', 'document', 'multimedia', 'rag_question'].includes(a.id)),
  },
  {
    title: '感知理解',
    icon: '👁️',
    desc: '理解图片、语音等多模态输入',
    agents: allAgents.filter(a => ['multimodal', 'audio'].includes(a.id)),
  },
  {
    title: '分析推荐',
    icon: '💡',
    desc: '诊断薄弱点、搜索资源、个性化推荐',
    agents: allAgents.filter(a => ['diagnosis', 'resource', 'recommendation'].includes(a.id)),
  },
]
</script>

<style scoped>
/* ── 阶段式水平流程 ── */
.flow-stage-row {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  padding: 8px 0 12px;
  overflow-x: auto;
}

.flow-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  position: relative;
}

.flow-stage-wide {
  flex-shrink: 1;
  min-width: 280px;
}

.flow-stage-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(99,102,241,0.12);
  color: #6366f1;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.flow-stage-card {
  border-radius: 16px;
  padding: 16px 18px;
  text-align: center;
  transition: all 0.3s ease;
  min-width: 140px;
}

.flow-stage-input {
  background: rgba(99,102,241,0.04);
  border: 1px solid rgba(99,102,241,0.1);
}

.flow-stage-orchestrator {
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08));
  border: 1px solid rgba(99,102,241,0.18);
  box-shadow: 0 4px 30px rgba(99,102,241,0.08);
  position: relative;
}

.flow-stage-output {
  background: rgba(16,185,129,0.04);
  border: 1px solid rgba(16,185,129,0.12);
}

.flow-stage-agents {
  background: rgba(99,102,241,0.02);
  border: 1px solid rgba(99,102,241,0.08);
  padding: 16px 12px;
  min-width: 280px;
}

.flow-stage-emoji {
  font-size: 32px;
  line-height: 1;
  margin-bottom: 8px;
}

.flow-stage-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.flow-stage-subtitle {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 3px;
}

.flow-stage-badge {
  font-size: 10px;
  padding: 2px 10px;
  border-radius: 9999px;
  background: rgba(99,102,241,0.12);
  color: #6366f1;
  font-weight: 600;
  margin-top: 8px;
  display: inline-block;
}

.flow-stage-items {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 5px;
  margin-top: 10px;
}

.flow-chip {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 8px;
  background: rgba(99,102,241,0.06);
  color: var(--text-secondary);
  white-space: nowrap;
}

.flow-chip-green {
  background: rgba(16,185,129,0.08);
  color: #059669;
}

.flow-stage-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding-top: 30px;
  flex-shrink: 0;
}

/* ── 调度智能体光环 ── */
.orchestrator-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  margin: 0 auto 10px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: conic-gradient(
    from 0deg,
    rgba(99,102,241,0.2),
    rgba(139,92,246,0.2),
    rgba(236,72,153,0.15),
    rgba(99,102,241,0.2)
  );
  animation: ring-spin 8s linear infinite;
}

.orchestrator-ring::before {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1));
}

.orchestrator-ring-inner {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(8,8,24,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

@keyframes ring-spin {
  to { transform: rotate(360deg); }
}

/* ── 智能体辐射环 ── */
.flow-agents-ring {
  position: relative;
  width: 280px;
  height: 280px;
  margin: 0 auto;
}

.agents-ring-hub {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15));
  border: 1px solid rgba(99,102,241,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  z-index: 2;
  box-shadow: 0 0 20px rgba(99,102,241,0.1);
}

.agents-ring-node {
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 14px;
  background: rgba(99,102,241,0.05);
  border: 1px solid rgba(99,102,241,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: all 0.3s ease;
  z-index: 2;
  cursor: default;
}

.agents-ring-node:hover {
  background: rgba(99,102,241,0.1);
  border-color: rgba(99,102,241,0.25);
  transform: scale(1.08);
  box-shadow: 0 4px 16px rgba(99,102,241,0.1);
}

.ring-node-active {
  background: rgba(99,102,241,0.12) !important;
  border-color: rgba(99,102,241,0.35) !important;
  box-shadow: 0 0 20px rgba(99,102,241,0.15);
  animation: node-glow 2s ease-in-out infinite;
}

@keyframes node-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(99,102,241,0.15); }
  50% { box-shadow: 0 0 28px rgba(99,102,241,0.25); }
}

.ring-node-icon {
  font-size: 18px;
  line-height: 1;
}

.ring-node-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.agents-ring-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

/* ── 智能体卡片 ── */
.agent-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(99,102,241,0.02);
  border: 1px solid rgba(99,102,241,0.06);
  transition: all 0.25s ease;
}

.agent-card:hover {
  background: rgba(99,102,241,0.05);
  border-color: rgba(99,102,241,0.12);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(99,102,241,0.06);
}

.agent-card-active {
  background: rgba(99,102,241,0.06) !important;
  border-color: rgba(99,102,241,0.2) !important;
  box-shadow: 0 0 20px rgba(99,102,241,0.08);
}

.agent-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.agent-badge-running {
  font-size: 10px;
  padding: 1px 8px;
  border-radius: 9999px;
  background: rgba(16,185,129,0.15);
  color: #10b981;
  font-weight: 600;
  animation: badge-pulse 2s ease-in-out infinite;
}

@keyframes badge-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.agent-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(99,102,241,0.06);
  color: var(--text-muted);
}
</style>
