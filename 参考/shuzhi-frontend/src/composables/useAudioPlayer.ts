/**
 * useAudioPlayer — TTS 语音播放 Composable
 *
 * 优先使用浏览器 Web Speech API (speechSynthesis)，零延迟即时播放。
 * 降级使用后端 Coze TTS API。
 */
import { ref, readonly } from 'vue'

export type PlayState = 'idle' | 'loading' | 'playing' | 'paused' | 'done' | 'error'

// 全局追踪当前播放，确保同时只有一个在播
let currentUtterance: SpeechSynthesisUtterance | null = null
let currentAudio: HTMLAudioElement | null = null

export function useAudioPlayer() {
  const playState = ref<PlayState>('idle')
  const errorMsg = ref<string | null>(null)
  const useBrowserTTS = typeof window !== 'undefined' && !!window.speechSynthesis

  function stopAll() {
    if (useBrowserTTS) {
      window.speechSynthesis.cancel()
    }
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio = null
    }
    currentUtterance = null
  }

  /** 浏览器 TTS：即时播放，无需网络 */
  function playWithBrowser(text: string): Promise<void> {
    return new Promise((resolve) => {
      stopAll()

      const utterance = new SpeechSynthesisUtterance(text)
      currentUtterance = utterance

      utterance.lang = 'zh-CN'
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0

      // 选择中文女声
      const voices = window.speechSynthesis.getVoices()
      const zhVoice =
        voices.find(v => v.lang === 'zh-CN' && v.name.includes('Xiaoxiao')) ||
        voices.find(v => v.lang === 'zh-CN' && v.name.includes('Female')) ||
        voices.find(v => v.lang === 'zh-CN') ||
        voices.find(v => v.lang.startsWith('zh'))

      if (zhVoice) utterance.voice = zhVoice

      utterance.onstart = () => { playState.value = 'playing' }
      utterance.onpause = () => { playState.value = 'paused' }
      utterance.onresume = () => { playState.value = 'playing' }
      utterance.onend = () => {
        playState.value = 'done'
        currentUtterance = null
        resolve()
      }
      utterance.onerror = (e) => {
        errorMsg.value = `语音播放失败: ${e.error}`
        playState.value = 'error'
        currentUtterance = null
        resolve()
      }

      // voices 可能异步加载，如果为空则延迟后重试
      if (voices.length === 0) {
        window.speechSynthesis.onvoiceschanged = () => {
          const v2 = window.speechSynthesis.getVoices()
          const zh = v2.find(v => v.lang.startsWith('zh'))
          if (zh) utterance.voice = zh
          window.speechSynthesis.speak(utterance)
        }
      } else {
        window.speechSynthesis.speak(utterance)
      }
    })
  }

  /** 后端 TTS：请求 API → 下载音频 → 播放 */
  async function playWithBackend(text: string): Promise<void> {
    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || ''
    const userId = localStorage.getItem('user_id') || 'default_user'

    playState.value = 'loading'
    errorMsg.value = null

    let audioUrl: string
    try {
      const resp = await fetch(`${apiBase}/api/v1/audio/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
        body: JSON.stringify({ text, speaker: 'zh_female_xiaohe_uranus_bigtts', audio_format: 'mp3', sample_rate: 24000, speech_rate: 0, uid: userId }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error((err as any).detail || `TTS 请求失败 (${resp.status})`)
      }
      const json = await resp.json()
      const data = json.data || json
      if (!data.audio_url) throw new Error('未获取到音频地址')
      audioUrl = data.audio_url
    } catch (e: any) {
      errorMsg.value = e.message || '语音合成失败'
      playState.value = 'error'
      return
    }

    stopAll()
    const audio = new Audio(audioUrl)
    currentAudio = audio

    return new Promise((resolve) => {
      audio.onloadeddata = () => { playState.value = 'playing' }
      audio.onended = () => { playState.value = 'done'; currentAudio = null; resolve() }
      audio.onpause = () => {
        if (audio.currentTime > 0 && !audio.ended) playState.value = 'paused'
      }
      audio.onerror = () => {
        errorMsg.value = '音频播放失败'
        playState.value = 'error'
        currentAudio = null
        resolve()
      }
      audio.play().catch((e: any) => {
        errorMsg.value = `播放失败: ${e.message}`
        playState.value = 'error'
        currentAudio = null
        resolve()
      })
    })
  }

  /** 统一播放入口 */
  async function play(text: string, _speaker?: string): Promise<void> {
    if (useBrowserTTS) {
      await playWithBrowser(text)
    } else {
      await playWithBackend(text)
    }
  }

  function pause(): void {
    if (useBrowserTTS) {
      window.speechSynthesis.pause()
    } else if (currentAudio) {
      currentAudio.pause()
    }
  }

  function resume(): void {
    if (useBrowserTTS) {
      window.speechSynthesis.resume()
    } else if (currentAudio) {
      currentAudio.play().catch(() => {})
      playState.value = 'playing'
    }
  }

  function stop(): void {
    stopAll()
    playState.value = 'idle'
  }

  return {
    playState: readonly(playState),
    error: readonly(errorMsg),
    play,
    pause,
    resume,
    stop,
    useBrowserTTS,
  }
}
