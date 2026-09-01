import { defineStore } from 'pinia'
import { ref, reactive, computed, nextTick } from 'vue'
import client from '@/api/client'

// ── 类型定义 ──

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  isStreaming?: boolean
  hasError?: boolean
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
}

// ── Agent 状态池 ──

const AGENT_STATUS: Record<string, string[]> = {
  thinking: ['正在思考...', '分析中...', '推理中...'],
  searching: ['检索技能数据...', '查询岗位图谱...', '匹配知识库...'],
  analyzing: ['分析技能差距...', '评估匹配度...', '计算置信度...'],
  generating: ['生成建议...', '构建学习路径...', '撰写分析报告...'],
  parker: ['正在呼叫帕克...', '雷达扫描中...', '航线规划中...', '匹配技能图谱...'],
}

let lastStatusIndex = -1

function pickStatus(agent: string): string {
  const pool = AGENT_STATUS[agent] || AGENT_STATUS.thinking
  if (pool.length <= 1) return pool[0] || ''
  let i = Math.floor(Math.random() * pool.length)
  if (i === lastStatusIndex) i = (i + 1) % pool.length // 避免连续重复同一条
  lastStatusIndex = i
  return pool[i]
}

// ── Store ──

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string>('')
  const isStreaming = ref(false)
  const currentAgent = ref('')
  const agentStatus = ref('')
  const inputText = ref('')

  // 停止生成：AbortController 中止 fetch/reader
  let abortController: AbortController | null = null
  // 状态词轮换：长等待期每 ~3s 换一条短语，避免界面死板
  let statusTimer: ReturnType<typeof setInterval> | null = null

  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value)
  )
  const messages = computed(() => currentSession.value?.messages || [])

  // ── 会话管理 ──

  function createSession(): ChatSession {
    const session: ChatSession = {
      id: `chat-${Date.now()}`,
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    return session
  }

  function switchSession(id: string) {
    currentSessionId.value = id
  }

  function deleteSession(id: string) {
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx > -1) {
      sessions.value.splice(idx, 1)
      if (currentSessionId.value === id) {
        currentSessionId.value = sessions.value[0]?.id || ''
      }
    }
  }

  // ── 发送消息（SSE 流式） ──

  async function sendMessage(content: string) {
    if (!content.trim() || isStreaming.value) return

    if (!currentSession.value) createSession()
    const session = currentSession.value!

    // 添加用户消息
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: Date.now(),
    }
    session.messages.push(userMsg)

    // 更新标题（首条消息）
    if (session.messages.filter(m => m.role === 'user').length === 1) {
      session.title = content.trim().slice(0, 20)
    }

    // 添加 assistant 占位（reactive：流式写入需经过 proxy 触发渲染）
    const assistantMsg = reactive<ChatMessage>({
      id: `msg-${Date.now()}-ai`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    })
    session.messages.push(assistantMsg)

    isStreaming.value = true
    inputText.value = ''

    try {
      await streamChat(session.id, content.trim(), assistantMsg)
    } catch (err: any) {
      if (err?.name === 'AbortError') {
        // 用户主动停止：保留已生成的部分内容，不标记错误
        if (!assistantMsg.content) {
          assistantMsg.content = '（已停止生成）'
        }
      } else {
        // 真实错误：保留部分内容 + 追加错误提示，供重试
        assistantMsg.content += `\n\n⚠️ 抱歉，出现了错误：${err.message || '请稍后重试'}`
        assistantMsg.hasError = true
      }
    } finally {
      assistantMsg.isStreaming = false
      isStreaming.value = false
      currentAgent.value = ''
      agentStatus.value = ''
      stopStatusRotation()
      abortController = null
    }
  }

  // ── SSE 流式对话 ──

  async function streamChat(sessionId: string, userMessage: string, assistantMsg: ChatMessage) {
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''

    // 新请求先中止上一次残留的（防御性），并挂上本次 AbortController
    abortController?.abort()
    abortController = new AbortController()

    const response = await fetch(`${apiBase}/api/personal/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMessage,
        session_id: sessionId,
      }),
      signal: abortController.signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') return

          try {
            const parsed = JSON.parse(data)
            handleSSEEvent(parsed, assistantMsg)
          } catch {
            // 非 JSON 数据，直接追加
            assistantMsg.content += data
          }
        }
      }
    }
  }

  function handleSSEEvent(event: any, assistantMsg: ChatMessage) {
    switch (event.type) {
      case 'content':
        assistantMsg.content += event.content || ''
        break
      case 'agent_start':
        currentAgent.value = event.agent || 'thinking'
        startStatusRotation(currentAgent.value)
        break
      case 'agent_end':
        stopStatusRotation()
        currentAgent.value = ''
        agentStatus.value = ''
        break
      case 'progress':
        agentStatus.value = event.message || ''
        break
      case 'error':
        assistantMsg.content += `\n\n⚠️ ${event.message || '处理出错'}`
        break
    }
  }

  // ── 状态词轮换（长等待期避免界面死板） ──

  function startStatusRotation(agent: string) {
    stopStatusRotation()
    agentStatus.value = pickStatus(agent)
    statusTimer = setInterval(() => {
      agentStatus.value = pickStatus(currentAgent.value || agent)
    }, 2800)
  }

  function stopStatusRotation() {
    if (statusTimer !== null) {
      clearInterval(statusTimer)
      statusTimer = null
    }
  }

  // ── 停止生成 ──

  function stopStreaming() {
    abortController?.abort()
    // 状态清理交给 sendMessage 的 finally（isStreaming/agentStatus 统一复位）
  }

  // ── 重试最后一条 ──

  async function retryLast() {
    if (isStreaming.value) return
    const session = currentSession.value
    if (!session) return
    const msgs = session.messages
    let userIdx = -1
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'user') { userIdx = i; break }
    }
    if (userIdx < 0) return
    const lastUserText = msgs[userIdx].content
    // 移除最后一条用户消息及其后的失败回复，再干净地重发
    session.messages.splice(userIdx)
    await sendMessage(lastUserText)
  }

  // ── 滚动到底部 ──

  async function scrollToBottom(el: HTMLElement | null) {
    await nextTick()
    if (el) el.scrollTop = el.scrollHeight
  }

  return {
    sessions, currentSessionId, currentSession, messages,
    isStreaming, currentAgent, agentStatus, inputText,
    createSession, switchSession, deleteSession, sendMessage,
    stopStreaming, retryLast, scrollToBottom,
  }
})
