/**
 * avatar store — 企业侧全局悬浮数字人的唯一状态源。
 *
 * 真实通路：服务端 /api/enterprise/avatar/signed-url 签发后走讯飞 SDK（mode='real'）。
 * 演示通路：未配置/连接失败自动降级（mode='demo'）—— SVG 讲者 + 浏览器 TTS 朗读 + 字幕。
 * 任何情况都不抛错：验收开箱即用（Silent Fallback）。
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useAvatarSDK, type AvatarPersona } from '@/composables/useAvatarSDK'

export type AvatarMode = 'off' | 'connecting' | 'real' | 'demo'

export const useAvatarStore = defineStore('avatar', () => {
  const sdk = useAvatarSDK()

  const enabled = ref(false)
  const mode = ref<AvatarMode>('off')
  const currentText = ref('')
  const isSpeaking = ref(false)
  const error = ref<string | null>(null)
  /** 真实 persona（形象/音色 ID）—— 演示模式用其标识真实数字人、挑选最接近的音色 */
  const persona = ref<AvatarPersona | null>(null)

  // 讯飞常见 vcn 音色性别标记，用于把真实音色 id 近似映射到浏览器中文音色
  const _FEMALE_VOICES = ['yezi', 'xiaoyan', 'xiaoxiao', 'huihui', 'yaoyao', 'wanwan', 'xiaorou']
  const _MALE_VOICES = ['kangkang', 'yunxi', 'yunjian', 'xiaofeng', 'xiaoyu', 'qiqi', 'manman']

  function _pickDemoVoice(synth: SpeechSynthesis): SpeechSynthesisVoice | null {
    const zh = synth.getVoices().filter((v) => v.lang.toLowerCase().startsWith('zh'))
    if (!zh.length) return null
    const id = (persona.value?.voiceId || '').toLowerCase()
    const name = (v: SpeechSynthesisVoice) => v.name.toLowerCase()
    const isF = (v: SpeechSynthesisVoice) => _FEMALE_VOICES.some((k) => name(v).includes(k))
    const isM = (v: SpeechSynthesisVoice) => _MALE_VOICES.some((k) => name(v).includes(k))
    const wantFemale = _FEMALE_VOICES.some((k) => id.includes(k))
    const wantMale = _MALE_VOICES.some((k) => id.includes(k))
    if (wantFemale && !wantMale) return zh.find(isF) || zh.find((v) => !isM(v)) || zh[0]
    if (wantMale && !wantFemale) return zh.find(isM) || zh.find((v) => !isF(v)) || zh[0]
    return zh[0]
  }

  // SDK 状态镜像（播放受限 / 错误）
  const playNotAllowed = computed(() => sdk.playNotAllowed.value)
  watch(() => sdk.error.value, (v) => { if (v) error.value = v })

  const isReal = computed(() => mode.value === 'real')

  // ── 演示通路：浏览器 TTS ──
  function _demoSpeak(text: string) {
    currentText.value = text
    isSpeaking.value = true
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
    const synth = window.speechSynthesis
    synth.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'
    u.rate = 1.0
    u.pitch = 1.0
    // 浏览器无法直接使用讯飞音色（需云端鉴权），按真实 voiceId 性别近似挑选最接近的中文音色
    const v = _pickDemoVoice(synth)
    if (v) u.voice = v
    u.onend = () => { isSpeaking.value = false }
    u.onerror = () => { isSpeaking.value = false }
    try { synth.speak(u) } catch { /* 无 TTS/受限时仅渲染字幕，不抛错 */ }
  }

  // ── 生命周期 ──

  /** 展开迷你窗并置为「连接中」（此时 stage 尚在挂载，随后须调用 connect）。 */
  function show() {
    if (enabled.value) return
    enabled.value = true
    mode.value = 'connecting'
    error.value = null
    // 预取真实 persona（形象/音色 ID），演示模式据此标识与选音
    void sdk.getPersona().then((p) => { persona.value = p })
  }

  /** 连接数字人：真实 SDK 成功 → real；未配置/失败 → demo（不抛错）。
   *  需在 show() 之后、stage 元素挂载之后调用（由组件 nextTick 后传入）。 */
  async function connect(container: HTMLDivElement) {
    try {
      await sdk.connect(container, {
        mode: 'driver',
        protocol: 'webrtc',
        fps: 25,
        bitrate: 4000000,
        width: 720,
        height: 1280,
      })
      mode.value = 'real'
    } catch (e: any) {
      // 未配置凭证 / SDK 加载失败 → 演示数字人接管（SDK 容器保持为空，遮罩覆盖）
      error.value = e?.message || String(e)
      mode.value = 'demo'
    }
  }

  /** 朗读一段汇报脚本（真实通路文本驱动；演示通路 TTS + 字幕）。 */
  async function speak(text: string) {
    if (!enabled.value || !text.trim()) return
    currentText.value = text
    if (isReal.value) {
      isSpeaking.value = true
      await sdk.interrupt()
      await sdk.driveText(text)
    } else {
      _demoSpeak(text)
    }
  }

  /** 停止朗读 / 驱动。 */
  function stop() {
    if (isReal.value) {
      sdk.interrupt()
    } else if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    isSpeaking.value = false
    currentText.value = ''
  }

  /** 解除浏览器自动播放限制（真实通路）。 */
  function resumeAudio() {
    sdk.resumeAudio()
  }

  /** 关闭数字人并释放真实连接。 */
  function close() {
    stop()
    if (isReal.value) sdk.disconnect()
    mode.value = 'off'
    enabled.value = false
    isSpeaking.value = false
    error.value = null
  }

  return {
    enabled,
    mode,
    currentText,
    isSpeaking,
    error,
    persona,
    playNotAllowed,
    isReal,
    show,
    connect,
    speak,
    stop,
    resumeAudio,
    close,
  }
})
