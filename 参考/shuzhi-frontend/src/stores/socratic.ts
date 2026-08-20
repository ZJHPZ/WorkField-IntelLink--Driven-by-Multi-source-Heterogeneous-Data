import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SocraticChunk } from '@/api/socratic'
import { streamSocraticReflection } from '@/api/socratic'

const AUTO_TRIGGER_THRESHOLD = 3
const AUTO_TRIGGER_COOLDOWN_HOURS = 24

export const useSocraticStore = defineStore('socratic', () => {
  // ── Panel state ──
  const panelVisible = ref(false)
  const panelCollapsed = ref(true)

  // ── Content state ──
  const currentQuestion = ref('')
  const isGenerating = ref(false)
  const sections = ref<{ type: string; content: string }[]>([])
  const rawText = ref('')

  // ── Parsed sections ──
  const questionsSection = ref('')
  const assumptionsSection = ref('')
  const reflectionSection = ref('')

  // ── Overlay state ──
  const showOverlay = ref(false)

  // ── Auto-trigger state ──
  const knowledgeQuestionCount = ref(0)
  const lastAutoTriggerTime = ref<number>(0)
  const userManuallyDismissed = ref(false)

  // ── Abort controller for canceling in-flight generation ──
  let abortController: AbortController | null = null

  // ── Computed ──
  const hasContent = computed(() => rawText.value.length > 0)
  const shouldAutoTrigger = computed(() => {
    if (userManuallyDismissed.value) return false
    if (panelCollapsed.value === false) return false // already open
    const now = Date.now()
    const cooldown = AUTO_TRIGGER_COOLDOWN_HOURS * 3600 * 1000
    if (now - lastAutoTriggerTime.value < cooldown) return false
    return knowledgeQuestionCount.value >= AUTO_TRIGGER_THRESHOLD
  })

  // ── Actions ──

  function openPanel(question?: string) {
    if (question) {
      currentQuestion.value = question
    }
    panelVisible.value = true
    panelCollapsed.value = false
    showOverlay.value = false
  }

  function togglePanel() {
    if (!panelVisible.value) {
      panelVisible.value = true
      panelCollapsed.value = false
    } else {
      panelCollapsed.value = !panelCollapsed.value
    }
  }

  function closePanel() {
    panelCollapsed.value = true
    showOverlay.value = false
  }

  function dismissPanel() {
    panelVisible.value = false
    panelCollapsed.value = true
    userManuallyDismissed.value = true
    lastAutoTriggerTime.value = Date.now()
    showOverlay.value = false
  }

  function dismissOverlay() {
    showOverlay.value = false
  }

  /** Called by ChatView when a knowledge question is asked & answered — auto-generates reflection */
  function onKnowledgeQuestionAsked(question: string) {
    console.log('[Socratic] onKnowledgeQuestionAsked:', question.slice(0, 50))
    currentQuestion.value = question
    knowledgeQuestionCount.value++

    // 每个知识问题都自动生成苏格拉底反思
    generate(question)

    if (shouldAutoTrigger.value) {
      autoOpenPanel(question)
    }
  }

  function onNonKnowledgeMessage() {
    // 闲聊类消息，不计入计数（但也不重置）
  }

  function autoOpenPanel(question: string) {
    currentQuestion.value = question
    panelVisible.value = true
    panelCollapsed.value = false
    lastAutoTriggerTime.value = Date.now()
    knowledgeQuestionCount.value = 0
    userManuallyDismissed.value = false
  }

  function resetCounter() {
    knowledgeQuestionCount.value = 0
  }

  /** Generate Socratic reflection for the given question */
  async function generate(question?: string) {
    const q = question || currentQuestion.value
    if (!q) return

    console.log('[Socratic] generate() called with:', q.slice(0, 50))

    // Cancel previous in-flight request
    if (abortController) {
      abortController.abort()
    }
    abortController = new AbortController()
    const signal = abortController.signal

    currentQuestion.value = q
    isGenerating.value = true
    sections.value = []
    rawText.value = ''
    questionsSection.value = ''
    assumptionsSection.value = ''
    reflectionSection.value = ''

    try {
      let full = ''
      for await (const chunk of streamSocraticReflection({ question: q }, signal)) {
        if (chunk.type === 'text') {
          full += chunk.content
          rawText.value = full
          sections.value.push({ type: chunk.section || 'text', content: chunk.content })
        } else if (chunk.type === 'error') {
          rawText.value = `❌ ${chunk.content}`
        }
      }

      // Parse sections from full text
      parseSections(full)

      // Show overlay on successful generation (only if panel is collapsed)
      if (full && !signal.aborted && panelCollapsed.value) {
        showOverlay.value = true
        console.log('[Socratic] Overlay shown — hasContent:', hasContent.value, 'panelCollapsed:', panelCollapsed.value)
      } else {
        console.log('[Socratic] Overlay skipped — full:', !!full, 'aborted:', signal.aborted, 'panelCollapsed:', panelCollapsed.value)
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // Silently ignore — replaced by newer request
      } else {
        rawText.value = `❌ 生成失败: ${err.message || '未知错误'}`
      }
    } finally {
      if (abortController?.signal === signal) {
        abortController = null
      }
      isGenerating.value = false
      // Reset auto-trigger counter (user engaged with Socratic mode)
      knowledgeQuestionCount.value = 0
    }
  }

  function parseSections(text: string) {
    // Remove the bracket markers for display
    const clean = (s: string) => s.replace(/[【】]/g, '').trim()

    const qMatch = text.match(/【引导性问题】([\s\S]*?)(?=【关键假设检验】|$)/)
    const aMatch = text.match(/【关键假设检验】([\s\S]*?)(?=【一句话反思】|$)/)
    const rMatch = text.match(/【一句话反思】([\s\S]*?)$/)

    if (qMatch) questionsSection.value = clean(qMatch[1])
    if (aMatch) assumptionsSection.value = clean(aMatch[1])
    if (rMatch) reflectionSection.value = clean(rMatch[1])
  }

  return {
    panelVisible,
    panelCollapsed,
    currentQuestion,
    isGenerating,
    sections,
    rawText,
    questionsSection,
    assumptionsSection,
    reflectionSection,
    knowledgeQuestionCount,
    hasContent,
    shouldAutoTrigger,
    showOverlay,
    openPanel,
    togglePanel,
    closePanel,
    dismissPanel,
    dismissOverlay,
    onKnowledgeQuestionAsked,
    onNonKnowledgeMessage,
    autoOpenPanel,
    resetCounter,
    generate,
  }
})
