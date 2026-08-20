import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'
import { useLearningStore } from '@/stores/learning'
import { useVoiceEngine } from '@/composables/voice-engine'

export interface ChatImage {
  url: string
  alt: string
  concept?: string
  diagramType?: string
  subject?: string
}

export interface ChatFile {
  url: string
  filename: string
  size: number
  content_type?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  images?: ChatImage[]
  files?: ChatFile[]
  agentId?: string
  timestamp: number
  isStreaming?: boolean
  topics?: string[]  // 本次回复涉及的知识点
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
}

export interface AgentState {
  id: string
  name: string
  statusMessage: string
  startedAt: number
}

// 智能体灵动状态消息池 — 每个智能体有多组动作描述，随机轮换避免机械感
const agentStatusPool: Record<string, string[]> = {
  conversation: [
    '正在仔细聆听你的问题',
    '正在分析你的学习需求',
    '正在理解你的学习背景',
    '正在揣摩你的真实意图',
    '正在抽取对话中的学习特征',
    '正在分析你的学习偏好和风格',
    '正在更新你的学习者画像',
    '正在回顾你的历史学习轨迹',
  ],
  learning_path: [
    '正在翻阅知识图谱，规划最佳路线',
    '正在分析你的学习进度，寻找最优路径',
    '正在为你绘制个性化学习地图',
    '正在梳理知识脉络，量身定制计划',
    '正在追踪学科前沿，更新路径推荐',
    '正在根据你的薄弱点动态调整路线',
    '正在匹配最适合你的学习资源',
    '正在计算各阶段学习时间分配',
  ],
  question: [
    '正在精心设计一道好题',
    '正在挑选合适的考察角度',
    '正在雕琢题目的每个细节',
    '正在编排思维训练的关卡',
    '正在创作一道有挑战的题目',
    '正在构思一道编程实践题',
    '正在设计选项，确保干扰项有区分度',
    '正在根据你的水平校准题目难度',
  ],
  document: [
    '正在整理知识要点，构建文档框架',
    '正在撰写结构化学习笔记',
    '正在绘制思维导图，梳理逻辑关系',
    '正在归纳核心知识点，生成摘要',
    '正在搭建文档大纲结构',
    '正在将零散知识编织成体系',
    '正在排版美化，让内容更易读',
  ],
  evaluation: [
    '正在仔细评估你的回答',
    '正在分析知识薄弱环节',
    '正在生成学习评估报告',
    '正在检查知识掌握程度',
    '正在对比标准答案，逐项打分',
    '正在计算你的学习进度百分比',
    '正在分析错题模式，定位根源问题',
    '正在为你定制针对性提升建议',
  ],
  qa: [
    '正在知识库中搜索答案',
    '正在查阅相关资料文献',
    '正在整理最佳解答思路',
    '正在追根溯源，寻找真相',
    '正在关联相关知识点，构建知识网络',
    '正在分析问题类型，选择讲解策略',
    '正在准备通俗易懂的类比解释',
  ],
  multimedia: [
    '正在生成教学示意图',
    '正在绘制概念关系图',
    '正在制作可视化讲解素材',
    '正在渲染知识结构图',
    '正在创作教学动画脚本',
    '正在设计视频讲解分镜',
    '正在将抽象概念转化为视觉表达',
  ],
  email: [
    '正在整理学习报告邮件',
    '正在排版学习周报',
    '正在准备推送内容',
    '正在生成练习题邮件附件',
    '正在打包学习计划邮件',
    '正在设计邮件模板样式',
  ],
  wechat: [
    '正在撰写公众号文章',
    '正在排版微信推送',
    '正在准备学习通知',
    '正在从素材库挑选配图',
    '正在优化标题，提升阅读吸引力',
    '正在编排学习干货系列内容',
  ],
  orchestrator: [
    '正在认真理解你的问题',
    '正在分析任务的关键要素',
    '正在拆解复杂需求',
    '正在组织最佳执行方案',
    '正在调度协作者，分派任务',
    '正在评估各智能体的匹配度',
    '正在规划多智能体协作流程',
  ],
  multimodal: [
    '正在识别图片中的内容',
    '正在分析上传的图像',
    '正在提取图片中的文字信息',
    '正在理解图像中的知识点',
    '正在结合图片内容分析问题',
  ],
  audio: [
    '正在将文字转为语音朗读',
    '正在合成自然流畅的语音',
    '正在识别语音内容',
    '正在处理音频输入',
  ],
  rag_question: [
    '正在题库中搜索相关题目',
    '正在检索最佳匹配的练习题',
    '正在根据知识点筛选题目',
    '正在从题库中调取真题',
  ],
  recommendation: [
    '正在为你筛选学习资源',
    '正在分析你的学习偏好',
    '正在匹配推荐内容',
    '正在生成个性化学习建议',
  ],
  bigdata_learning: [
    '正在检索大数据知识图谱',
    '正在梳理技术栈关联',
    '正在分析大数据学习路径',
  ],
  learning_engine: [
    '正在分析学习进度数据',
    '正在计算最佳复习时间',
    '正在调整学习策略',
  ],
  resource: [
    '正在搜索互联网学习资源',
    '正在检索官方文档',
    '正在查找社区讨论',
    '正在搜索B站教学视频',
  ],
  diagnosis: [
    '正在诊断知识薄弱点',
    '正在分析错题模式',
    '正在评估知识盲区',
  ],
  // 多智能体并行时的聚合状态文案
  _multi: [
    '正在同时调度 {agents}，协同作战',
    '正在协调 {agents} 一起为你服务',
    '正在让 {agents} 分头行动',
    '正在召集 {agents} 各展所长',
  ],
}

// 智能体中文名称
const agentNames: Record<string, string> = {
  conversation: '对话智能体',
  learning_path: '学习路径智能体',
  question: '题库智能体',
  document: '文档智能体',
  evaluation: '评估智能体',
  qa: '答疑智能体',
  multimedia: '多媒体智能体',
  email: '邮件智能体',
  wechat: '微信智能体',
  orchestrator: '调度智能体',
  multimodal: '多模态理解智能体',
  audio: '语音处理智能体',
  rag_question: '题库检索智能体',
  bigdata_learning: '大数据学习智能体',
  learning_engine: '学习引擎智能体',
  resource: '资源搜索智能体',
  diagnosis: '诊断智能体',
  recommendation: '推荐智能体',
  multi_agent_coordinator: '多意图协作',
}

function getUserId(): string {
  return localStorage.getItem('user_id') || 'default_user'
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const isStreaming = ref(false)
  const activeAgent = ref<AgentState | null>(null)
  // 上一次使用的状态消息索引，用于轮换避免重复
  const _lastStatusIndex: Record<string, number> = {}

  // 防抖缓冲：收集短时间窗口内的 agent_start 事件，聚合展示
  const _pendingAgentIds = new Set<string>()
  let _burstTimer: ReturnType<typeof setTimeout> | null = null
  let _minDisplayTimer: ReturnType<typeof setTimeout> | null = null
  const BURST_WINDOW = 350   // ms，收集并行调用的时间窗口
  const MIN_DISPLAY = 700    // ms，状态最短展示时间

  // 会话 ID 管理（多轮对话）
  function getOrCreateSessionId(): string {
    let sid = localStorage.getItem('chat_session_id')
    if (!sid) {
      sid = 'sid_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8)
      localStorage.setItem('chat_session_id', sid)
    }
    return sid
  }

  const conversationId = ref<string>('')

  /** 从消息池中随机选取一个状态描述，尽量避免连续重复 */
  function pickStatusMessage(agentId: string): string {
    const pool = agentStatusPool[agentId] || agentStatusPool['orchestrator'] || ['正在处理...']
    if (pool.length <= 1) return pool[0]
    const lastIdx = _lastStatusIndex[agentId] ?? -1
    let idx: number
    do {
      idx = Math.floor(Math.random() * pool.length)
    } while (idx === lastIdx && pool.length > 1)
    _lastStatusIndex[agentId] = idx
    return pool[idx]
  }

  /** 聚合多智能体状态文案 */
  function pickMultiAgentMessage(ids: string[]): string {
    const pool = agentStatusPool['_multi'] || ['正在同时调度 {agents}']
    const idx = Math.floor(Math.random() * pool.length)
    const names = ids.map(id => getAgentName(id)).join('、')
    return pool[idx].replace('{agents}', names)
  }

  /** 智能体中文名称查找 */
  function getAgentName(agentId: string): string {
    return agentNames[agentId] || agentId
  }

  /** agent_start 事件 → 进入缓冲窗口，收集并行调用 */
  function onAgentStart(agentId: string, agentName?: string) {
    _pendingAgentIds.add(agentId)

    if (_burstTimer) clearTimeout(_burstTimer)
    _burstTimer = setTimeout(() => {
      const ids = [..._pendingAgentIds]
      _pendingAgentIds.clear()

      if (ids.length === 1) {
        // 单一智能体 → 灵动个性化文案（优先使用 API 返回的名称）
        const aid = ids[0]
        activeAgent.value = {
          id: aid,
          name: agentName || getAgentName(aid),
          statusMessage: pickStatusMessage(aid),
          startedAt: Date.now(),
        }
      } else {
        // 多智能体并行 → 聚合文案
        activeAgent.value = {
          id: 'multi',
          name: `${ids.length}个智能体`,
          statusMessage: pickMultiAgentMessage(ids),
          startedAt: Date.now(),
        }
      }
      // answer 可能比 burst 窗口先到，此时安排延迟清除
      _scheduleClearIfNeeded()
    }, BURST_WINDOW)
  }

  /** agent_end → 不再立即清除，状态自然保持到下一事件 */
  function onAgentEnd() {
    // 什么都不做，保持当前状态直到 answer 文本到来
  }

  let _answerStarted = false

  /** 如果状态已设置，安排延迟清除 */
  function _scheduleClearIfNeeded() {
    if (!_answerStarted || !activeAgent.value) return
    if (_minDisplayTimer) clearTimeout(_minDisplayTimer)
    const elapsed = Date.now() - activeAgent.value.startedAt
    const delay = Math.max(0, MIN_DISPLAY - elapsed)
    _minDisplayTimer = setTimeout(() => {
      activeAgent.value = null
    }, delay)
  }

  /** 第一个 answer 文本 → 标记 answer 已开始，尝试安排清除 */
  function onFirstAnswer() {
    _answerStarted = true
    _scheduleClearIfNeeded()
  }

  /** 流结束 → 强制清除所有状态 */
  function clearAgentState() {
    if (_burstTimer) { clearTimeout(_burstTimer); _burstTimer = null }
    if (_minDisplayTimer) { clearTimeout(_minDisplayTimer); _minDisplayTimer = null }
    _clearFallbackTimer()
    _pendingAgentIds.clear()
    _answerStarted = false
    activeAgent.value = null
  }

  function createSession(): ChatSession {
    const session: ChatSession = {
      id: `session_${Date.now()}`,
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    updatedTopicsThisSession.clear()
    return session
  }

  function getCurrentSession(): ChatSession | undefined {
    return sessions.value.find(s => s.id === currentSessionId.value)
  }

  function addMessage(role: ChatMessage['role'], content: string, agentId?: string, extra?: { images?: string[]; files?: { url: string; filename: string; size: number; content_type?: string }[] }) {
    let session = getCurrentSession()
    if (!session) session = createSession()
    const msg: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      role,
      content,
      agentId,
      timestamp: Date.now(),
    }
    if (extra?.images?.length) {
      msg.images = extra.images.map(url => ({ url, alt: '用户上传图片' }))
    }
    if (extra?.files?.length) {
      msg.files = extra.files.map(f => ({ url: f.url, filename: f.filename, size: f.size, content_type: f.content_type }))
    }
    session.messages.push(msg)
    if (session.messages.length === 1 && role === 'user') {
      session.title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
    }
    return msg
  }

  function appendToLastMessage(chunk: string) {
    const session = getCurrentSession()
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.role === 'assistant' && last.isStreaming) {
      last.content += chunk
    }
  }

  function appendImageToLastMessage(image: ChatImage) {
    const session = getCurrentSession()
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.role === 'assistant' && last.isStreaming) {
      if (!last.images) last.images = []
      last.images.push(image)
    }
  }

  function appendFileToLastMessage(file: ChatFile) {
    const session = getCurrentSession()
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.role === 'assistant' && last.isStreaming) {
      if (!last.files) last.files = []
      last.files.push(file)
    }
  }

  // 无 agent_start 事件时的兜底：显示灵动思考状态
  let _fallbackTimer: ReturnType<typeof setTimeout> | null = null
  const FALLBACK_DELAY = 800  // ms — 800ms 后仍无 agent_start，则展示兜底状态

  function _startFallbackStatus() {
    _fallbackTimer = setTimeout(() => {
      if (!activeAgent.value && isStreaming.value) {
        const msgs = agentStatusPool['orchestrator'] || ['正在处理...']
        activeAgent.value = {
          id: 'orchestrator',
          name: '调度智能体',
          statusMessage: msgs[Math.floor(Math.random() * msgs.length)],
          startedAt: Date.now(),
        }
      }
    }, FALLBACK_DELAY)
  }

  function _clearFallbackTimer() {
    if (_fallbackTimer) { clearTimeout(_fallbackTimer); _fallbackTimer = null }
  }

  function startStreamingMessage(agentId?: string) {
    const session = getCurrentSession()
    if (!session) return
    const msg: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'assistant',
      content: '',
      agentId,
      timestamp: Date.now(),
      isStreaming: true,
    }
    session.messages.push(msg)
    isStreaming.value = true
    _answerStarted = false
    _startFallbackStatus()
  }

  function finishStreamingMessage() {
    const session = getCurrentSession()
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.isStreaming) {
      clearAgentState()
      last.isStreaming = false
      // 清理响应文本中的 JSON 片段并统一助手名称
      last.content = last.content
        .replace(/\{"type"\s*:\s*"[^"]*"\s*,\s*"content"\s*:\s*"[^"]*"\s*\}/g, '')
        .replace(/\{"type"\s*:\s*"[^"]*"\s*,\s*"content"\s*:\s*\{[^}]*\}\s*\}/g, '')
        .replace(/学习伙伴智能助手/g, '帕克')
        .replace(/AI助手/g, '帕克')
      // 提取涉及的知识点标签
      last.topics = extractTopics(last.content)
      // 根据对话内容更新知识掌握度
      bumpTopicMastery(last.topics)
    }
    isStreaming.value = false
  }

  // 根据对话中涉及的话题，递增知识掌握度
  function bumpTopicMastery(topics: string[]) {
    const learningStore = useLearningStore()
    let masteryReached = false
    for (const topicName of topics) {
      const topicId = TOPIC_KEYWORD_MAP[topicName]
      if (!topicId || updatedTopicsThisSession.has(topicId)) continue
      updatedTopicsThisSession.add(topicId)

      // 查找当前掌握度，在此基础上 +1（0-5 量表），上限 5
      const existing = learningStore.topicMasteryList.find(t => t.topicId === topicId)
      const currentLevel = existing ? Math.round(existing.masteryLevel * 5) : 0
      const newLevel = Math.min(currentLevel + 1, 5)
      learningStore.updateTopicMastery(topicId, newLevel)
      if (newLevel >= 4 && currentLevel < 4) {
        masteryReached = true
      }
    }
    // 触发宠物庆祝
    if (masteryReached) {
      import('@/stores/pet').then(({ usePetStore }) => {
        usePetStore().celebrate('太棒了！你又掌握了一个知识点！🎉')
      })
    }
  }

  // 从 AI 回复中提取大数据相关知识点，并映射到知识图谱的 topicId
  const TOPIC_KEYWORD_MAP: Record<string, string> = {
    'Hadoop': 'hadoop',
    'HDFS': 'hdfs',
    'MapReduce': 'mapreduce',
    'YARN': 'yarn',
    'Spark': 'spark_core',
    'Spark Core': 'spark_core',
    'Spark SQL': 'spark_sql',
    'Spark Streaming': 'spark_streaming',
    'Flink': 'flink',
    'Kafka': 'kafka',
    'HBase': 'hbase',
    'Hive': 'hive',
    'ZooKeeper': 'zookeeper',
    'Linux': 'linux',
    'SQL': 'sql',
    '数据仓库': 'data_warehouse',
    '数据湖': 'data_lake',
    'Scala': 'scala',
    'Python': 'python',
    'RDD': 'spark_core',
    'DataFrame': 'spark_sql',
    '流处理': 'spark_streaming',
    '批处理': 'mapreduce',
    '分布式': 'hdfs',
    '集群': 'hadoop',
    '机器学习': 'machine_learning',
    '深度学习': 'deep_learning',
    '数据挖掘': 'data_mining',
    'ETL': 'etl',
    '数据管道': 'data_pipeline',
  }

  const updatedTopicsThisSession = new Set<string>()

  function extractTopics(text: string): string[] {
    const found = Object.keys(TOPIC_KEYWORD_MAP).filter(kw =>
      text.toLowerCase().includes(kw.toLowerCase())
    )
    return [...new Set(found)].slice(0, 5)
  }

  async function sendMessage(userInput: string, images?: string[], files?: { url: string; filename: string; size: number; content_type?: string }[]): Promise<void> {
    addMessage('user', userInput, undefined, { images, files })
    const userId = getUserId()
    let streamCompleted = false
    const voiceEnabled = useVoiceEngine().isEnabled
    const voiceSpeaker = useVoiceEngine().speaker.value

    // VoiceEngine: 新对话开始时停止旧朗读
    const voiceEngine = useVoiceEngine()
    voiceEngine.stop()

    // Try backend SSE streaming first
    try {
      const body: Record<string, unknown> = {
        message: userInput,
        session_id: getOrCreateSessionId(),
      }
      if (conversationId.value) {
        body.conversation_id = conversationId.value
      }
      if (voiceEnabled) {
        body.voice_enabled = true
        body.speaker = voiceSpeaker
      }
      if (images && images.length > 0) {
        body.images = images
      }
      if (files && files.length > 0) {
        body.files = files.map(f => {
          const ext = f.filename ? f.filename.split('.').pop()?.toLowerCase() : ''
          const typeMap: Record<string, string> = { pdf: 'document', docx: 'document', xlsx: 'spreadsheet', pptx: 'presentation', txt: 'text', csv: 'spreadsheet' }
          return { name: f.filename, url: f.url, file_type: typeMap[ext || ''] || 'document', content_type: f.content_type }
        })
      }
      const backendUrl = `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/chat/stream`
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId,
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        let errMsg = `AI 服务响应异常 (${response.status})`
        try {
          const errData = await response.json()
          if (errData.detail) {
            if (typeof errData.detail === 'string') errMsg = errData.detail
            else if (Array.isArray(errData.detail)) errMsg = errData.detail.map((e: any) => e.msg || '').join('; ')
          }
        } catch { /* use default message */ }
        clearAgentState()
        finishStreamingMessage()
        voiceEngine.stop()
        addMessage('assistant', errMsg)
        return
      }

      startStreamingMessage()
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.status === 'done' || data.type === 'done' || data.type === 'message_end') {
              // 检查 Coze 错误码，自动刷新会话
              if (data.type === 'message_end' && data.code && data.code !== '0') {
                localStorage.removeItem('chat_session_id')
                conversationId.value = ''
                appendToLastMessage(`\n\n> ⚠️ AI 服务返回错误 (code=${data.code})，请重新发送消息`)
              }
              clearAgentState()
              finishStreamingMessage()
              voiceEngine.drain()
              streamCompleted = true
            } else if (data.type === 'router_meta') {
              // 意图路由信息 — 记录 agent/intent/confidence/architecture
              const session = getCurrentSession()
              const last = session?.messages[session.messages.length - 1]
              if (data.intent) {
                if (last && last.isStreaming) {
                  last.agentId = data.agent || data.intent.toLowerCase()
                }
              } else if (data.architecture === 'multi_agent' && last && last.isStreaming) {
                // 多智能体架构：router_meta 不含 agent/intent 时，标记为多智能体协作
                last.agentId = 'orchestrator'
              }
            } else if (data.type === 'profile_update') {
              // Agent 返回的用户画像更新（v1.0.0: user_id + features）
              if (data.user_id || data.features || data.profile || data.star_chart || data.dimensions || data.ai_summary) {
                import('@/stores/profileModeling').then(({ useProfileModelingStore }) => {
                  useProfileModelingStore().applyProfileUpdate(data)
                }).catch(() => {})
              }
            } else if (data.type === 'run_end') {
              // 运行结束 — 记录日志即可
              console.debug(`[Chat] run_end: run_id=${data.run_id}, total_ms=${data.total_duration_ms}`)
            } else if (data.type === 'message_start') {
              // 对话开始，记录 reply_id
              if (data.reply_id) {
                conversationId.value = data.reply_id as string
              }
            } else if (data.type === 'thinking') {
              // 显示思考状态
              if (data.content && !activeAgent.value) {
                activeAgent.value = {
                  id: 'thinking',
                  name: 'AI 思考中',
                  statusMessage: data.content as string,
                  startedAt: Date.now(),
                }
              }
            } else if ((data.type === 'agent_start' || data.event === 'agent_start') && data.agent_id) {
              if (data.agent_id === 'tts') continue
              onAgentStart(data.agent_id as string, data.agent_name as string | undefined)
              const session = getCurrentSession()
              const last = session?.messages[session.messages.length - 1]
              if (last && last.isStreaming) {
                last.agentId = last.agentId || (data.agent_id as string)
              }
            } else if (data.type === 'agent_end' || data.event === 'agent_end') {
              onAgentEnd()
            } else if (data.type === 'agent_switch' || data.event === 'agent_switch') {
              // 多智能体协作：子智能体切换
              const switchId = data.agent_id as string || ''
              const switchName = data.agent_name as string || getAgentName(switchId)
              if (switchId) {
                activeAgent.value = {
                  id: switchId,
                  name: switchName,
                  statusMessage: data.content as string || pickStatusMessage(switchId),
                  startedAt: Date.now(),
                }
                const session = getCurrentSession()
                const last = session?.messages[session.messages.length - 1]
                if (last && last.isStreaming) {
                  last.agentId = switchId
                }
              }
            } else if (data.type === 'image' && data.content) {
              // AI 生成的图片（来自多媒体智能体）
              appendImageToLastMessage({
                url: data.content as string,
                alt: data.alt as string || 'AI生成图片',
                concept: data.concept as string || '',
                diagramType: data.diagram_type as string || '',
                subject: data.subject as string || '',
              })
            } else if (data.alt !== undefined && data.content) {
              // 图片事件（alt 可能为空字符串，用 !== undefined 判断）- 兼容旧格式
              appendImageToLastMessage({
                url: data.content as string,
                alt: data.alt as string || '',
                concept: data.concept as string || '',
                diagramType: data.diagram_type as string || '',
                subject: data.subject as string || '',
              })
            } else if (data.type === 'tool_request' || data.type === 'tool_response') {
              // 工具调用/响应事件 — 不显示为文本，静默跳过
            } else if (data.event === 'audio_url' && data.audio_url) {
              voiceEngine.enqueue(data.audio_url as string, (data.text as string) || '')
            } else if (data.content) {
              if (activeAgent.value && (data.content as string).trim()) {
                onFirstAnswer()
              }
              appendToLastMessage(data.content)
            }
            if (data.type !== 'profile_update' && (data.dimensions || data.ai_summary || data.star_chart || data.features)) {
              import('@/stores/profileModeling').then(({ useProfileModelingStore }) => {
                useProfileModelingStore().applyProfileUpdate(data)
              }).catch(() => {})
            }
          } catch { /* ignore parse errors */ }
        }
      }
      finishStreamingMessage()
      streamCompleted = true

      if (voiceEnabled && streamCompleted) {
        await requestTTS(voiceSpeaker)
      }
    } catch {
      clearAgentState()
      finishStreamingMessage()
      voiceEngine.stop()
      addMessage('assistant', '抱歉，请求失败，请检查网络连接后重试')
    }

    // 对话完成后，同步学习指标到后端
    if (streamCompleted) {
      await syncChatMetrics(userInput)
    }
  }

  /** 请求独立 TTS 将最后一条 AI 回复转为语音 */
  async function requestTTS(speaker: string) {
    const voiceEngine = useVoiceEngine()
    const session = getCurrentSession()
    if (!session) return
    const lastMsg = session.messages.filter(m => m.role === 'assistant' && !m.isStreaming).pop()
    if (!lastMsg || !lastMsg.content) return

    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      const resp = await fetch(`${apiBase}/api/v1/audio/tts/standalone`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': localStorage.getItem('user_id') || 'default_user',
        },
        body: JSON.stringify({ text: lastMsg.content, speaker }),
      })
      if (resp.ok) {
        const json = await resp.json()
        const audioUrl = json.data?.audio_url || json.data?.audioUrl
        if (audioUrl) {
          voiceEngine.enqueue(audioUrl, lastMsg.content.slice(0, 100))
        }
      }
    } catch {
      // TTS 不可用时静默失败
    }
  }

  // 对话结束后向后端汇报，刷新学习指标
  async function syncChatMetrics(userInput: string) {
    const session = getCurrentSession()
    if (!session) return
    const lastMsg = session.messages.filter(m => m.role === 'assistant' && !m.isStreaming).pop()
    if (!lastMsg) return

    const topics = lastMsg.topics || []
    const learningStore = useLearningStore()

    try {
      const result = await client.post('/api/v1/chat/complete', {
        user_message: userInput,
        assistant_message: lastMsg.content,
        topics,
      }) as any

      if (result) {
        // 同步后端返回的最新指标到本地 store
        if (result.streak_days !== undefined) learningStore.streakDays = result.streak_days
        if (result.today_minutes !== undefined) learningStore.todayMinutes = result.today_minutes
        if (result.curiosity_index !== undefined) learningStore.curiosityIndex = result.curiosity_index
        if (result.topics_mastered !== undefined && learningStore.topicMasteryList.length > 0) {
          // 刷新知识点列表以获取最新掌握度
          await learningStore.fetchTopicMastery()
        }
        // 刷新复习队列
        await learningStore.fetchReviews()
        // 刷新学习星图
        try {
          const { useProfileModelingStore } = await import('@/stores/profileModeling')
          useProfileModelingStore().fetchProfileModel()
        } catch { /* 星图刷新不影响主流程 */ }
      }
    } catch {
      // 后端不可用时仍可正常使用
    }
  }

  async function loadHistory() {
    try {
      const data = await client.get('/api/v1/chat/history') as any
      if (Array.isArray(data) && data.length > 0) {
        const session = createSession()
        data.forEach((item: any) => {
          addMessage(item.role || 'assistant', item.content || '')
        })
        if (data[0]?.content) {
          session.title = data[0].content.slice(0, 30) + (data[0].content.length > 30 ? '...' : '')
        }
      }
    } catch {
      // Backend unavailable
    }
  }

  function switchSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  function deleteSession(sessionId: string) {
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = sessions.value[0]?.id || null
    }
  }

  return {
    sessions, currentSessionId, isStreaming, activeAgent, conversationId,
    createSession, getCurrentSession, addMessage,
    appendToLastMessage, appendImageToLastMessage, appendFileToLastMessage, startStreamingMessage, finishStreamingMessage,
    sendMessage, loadHistory, switchSession, deleteSession,
    pickStatusMessage, getAgentName,
  }
})
