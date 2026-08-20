import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export interface ProfileDimension {
  key: string
  label: string
  value: number       // 0-100
  previousValue: number
  icon: string
  color: string
}

export interface ProfileUpdatePayload {
  user_id: string
  profile: Record<string, any>
  star_chart: { center: string; rays: any[] }
  dimensions: ProfileDimension[]
  ai_summary: string
  last_updated: string
}

function getUserId(): string {
  return localStorage.getItem('user_id') || 'default_user'
}

// Demo fallback — 智能体未返回数据时的初始占位
function buildDemoDimensions(): ProfileDimension[] {
  return [
    { key: 'knowledge_breadth', label: '知识广度', value: 45, previousValue: 38, icon: '🌐', color: '#6366f1' },
    { key: 'knowledge_depth', label: '知识深度', value: 32, previousValue: 28, icon: '🔬', color: '#06b6d4' },
    { key: 'curiosity', label: '好奇心', value: 72, previousValue: 65, icon: '🔍', color: '#f59e0b' },
    { key: 'learning_grit', label: '学习韧性', value: 55, previousValue: 50, icon: '💪', color: '#10b981' },
    { key: 'practice_tendency', label: '实践倾向', value: 38, previousValue: 35, icon: '🛠️', color: '#a855f7' },
    { key: 'thinking_mode', label: '思维模式', value: 48, previousValue: 45, icon: '🧩', color: '#f43f5e' },
  ]
}

function buildDemoSummary(): string {
  return '你的好奇心指数表现突出，说明你对大数据领域充满探索欲。知识广度和深度正在稳步增长，继续保持当前的学习节奏，重点关注实践能力的培养。'
}

export const useProfileModelingStore = defineStore('profileModeling', () => {
  const dimensions = ref<ProfileDimension[]>([])
  const aiSummary = ref('')
  const lastUpdated = ref('')
  const isLoading = ref(false)
  const isAgentExtracted = ref(false)

  const trendMap = computed(() => {
    const map: Record<string, { direction: string; delta: number }> = {}
    for (const d of dimensions.value) {
      const delta = d.value - d.previousValue
      map[d.key] = {
        direction: delta > 2 ? 'up' : delta < -2 ? 'down' : 'stable',
        delta: Math.abs(delta),
      }
    }
    return map
  })

  // ── API 拉取 ──
  async function fetchProfileModel() {
    isLoading.value = true
    try {
      const uid = getUserId()
      const data = await client.get(`/api/v1/profile/modeling?user_id=${encodeURIComponent(uid)}`) as any
      if (data?.dimensions && Array.isArray(data.dimensions)) {
        applyDimensions(data)
        return
      }
    } catch {
      // fallback to demo
    } finally {
      isLoading.value = false
    }

    if (dimensions.value.length === 0) {
      dimensions.value = buildDemoDimensions()
      aiSummary.value = buildDemoSummary()
      lastUpdated.value = new Date().toISOString()
    }
  }

  // ── SSE / WS 实时更新入口 ──
  function applyProfileUpdate(payload: ProfileUpdatePayload) {
    if (payload.dimensions && Array.isArray(payload.dimensions)) {
      applyDimensions(payload)
    } else if (payload.star_chart?.rays) {
      // 从 star_chart.rays 转换
      dimensions.value = payload.star_chart.rays
        .filter((r: any) => r.type !== 'array' && r.type !== 'text')
        .map((r: any) => ({
          key: r.label,
          label: r.label,
          value: typeof r.value === 'number' ? r.value : (r.level || 1) * 20,
          previousValue: typeof r.value === 'number' ? Math.max(0, r.value - 5) : (r.level || 1) * 20 - 5,
          icon: _iconForLabel(r.label),
          color: r.color || '#6366f1',
        }))
      aiSummary.value = payload.ai_summary || ''
      lastUpdated.value = payload.last_updated || new Date().toISOString()
    }
  }

  function applyDimensions(data: any) {
    dimensions.value = data.dimensions.map((d: any) => ({
      key: d.key || '',
      label: d.label || d.name || '',
      value: Math.min(100, Math.max(0, d.value || 0)),
      previousValue: Math.min(100, Math.max(0, d.previous_value || d.previousValue || 0)),
      icon: d.icon || _iconForLabel(d.label),
      color: d.color || _colorForLabel(d.label),
    }))
    aiSummary.value = data.ai_summary || data.summary || ''
    lastUpdated.value = data.last_updated || data.updated_at || new Date().toISOString()
  }

  // ── 智能体画像反馈 ──
  const isFeedbackLoading = ref(false)

  async function fetchAgentFeedback() {
    isFeedbackLoading.value = true
    try {
      const uid = getUserId()
      const data = await client.post(`/api/v1/profile/agent-feedback`, { user_id: uid }) as any
      if (data?.success && data.feedback) {
        aiSummary.value = data.feedback
        lastUpdated.value = new Date().toISOString()
        return data.feedback
      } else {
        // 智能体不可用时保留现有摘要
        console.warn('Agent feedback unavailable:', data?.message)
        return null
      }
    } catch (e) {
      console.warn('Agent feedback request failed:', e)
      return null
    } finally {
      isFeedbackLoading.value = false
    }
  }

  // ── WebSocket 消息处理 ──
  function onWsMessage(msg: any) {
    if (msg.type === 'profile_update' && msg.data) {
      const d = msg.data
      if (d.dimensions && Array.isArray(d.dimensions)) {
        applyDimensions(d)
      }
    }
  }

  return {
    dimensions, aiSummary, lastUpdated, isLoading, isAgentExtracted, trendMap,
    isFeedbackLoading,
    fetchProfileModel,
    applyProfileUpdate,
    applyDimensions,
    fetchAgentFeedback,
    onWsMessage,
  }
})

// ── 维度标签 → 图标 / 颜色映射 ──
function _iconForLabel(label: string): string {
  const m: Record<string, string> = {
    '知识广度': '🌐', '知识深度': '🔬', '好奇心': '🔍', '学习韧性': '💪',
    '实践倾向': '🛠️', '思维模式': '🧩', '学习进度': '📈', '兴趣领域': '🎯',
    '学习风格': '🎨', '学习速度': '⚡',
  }
  return m[label] || '📊'
}

function _colorForLabel(label: string): string {
  const m: Record<string, string> = {
    '知识广度': '#6366f1', '知识深度': '#06b6d4', '好奇心': '#f59e0b',
    '学习韧性': '#10b981', '实践倾向': '#a855f7', '思维模式': '#f43f5e',
    '学习进度': '#10b981', '兴趣领域': '#a855f7',
    '学习风格': '#6366f1', '学习速度': '#f59e0b',
  }
  return m[label] || '#6366f1'
}
