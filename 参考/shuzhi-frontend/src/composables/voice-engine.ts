/**
 * VoiceEngine — 流式 TTS 音频播放引擎
 *
 * 后端通过 SSE 流式生成 TTS 音频 URL (audio_url 事件)，
 * 前端按序播放，支持暂停/继续、语速/音量调节。
 */
import { ref } from 'vue'

export type VoiceState = 'idle' | 'speaking' | 'paused'

export interface VoiceSettings {
  rate: number   // 0.5 - 2.0
  volume: number // 0 - 1
}

// 可选音色列表
export const SPEAKERS: Record<string, string> = {
  'zh_female_xiaohe_uranus_bigtts': '小和（温柔女声）',
  'zh_female_vv_uranus_bigtts': 'Vivian（中英双语女声）',
  'zh_male_m191_uranus_bigtts': '云舟（清晰男声）',
  'zh_male_taocheng_uranus_bigtts': '萧天（稳重男声）',
  'zh_male_dayi_saturn_bigtts': '大义（播音男声）',
}

export class VoiceEngine {
  private _isEnabled = false
  private audio: HTMLAudioElement | null = null
  private _queue: { url: string; text: string }[] = []
  private _state: VoiceState = 'idle'

  readonly isSupported: boolean
  readonly state = ref<VoiceState>('idle')
  readonly settings = ref<VoiceSettings>({
    rate: 1.0,
    volume: 1.0,
  })
  readonly speaker = ref<string>('zh_female_xiaohe_uranus_bigtts')

  constructor() {
    this.isSupported = typeof window !== 'undefined' && typeof Audio !== 'undefined'
  }

  get isEnabled(): boolean {
    return this._isEnabled
  }

  setEnabled(enabled: boolean): void {
    this._isEnabled = enabled
    if (!enabled) {
      this.stop()
    }
  }

  toggle(): boolean {
    this.setEnabled(!this._isEnabled)
    return this._isEnabled
  }

  updateSettings(partial: Partial<VoiceSettings>): void {
    Object.assign(this.settings.value, partial)
    if (this.audio) {
      this.audio.playbackRate = this.settings.value.rate
      this.audio.volume = this.settings.value.volume
    }
  }

  setSpeaker(speakerId: string): void {
    this.speaker.value = speakerId
  }

  /** 收到后端 audio_url 事件时调用，加入播放队列 */
  enqueue(url: string, text: string): void {
    if (!this._isEnabled) return
    this._queue.push({ url, text })
    if (this._state === 'idle') {
      this._playNext()
    }
  }

  /** 流结束时调用，确保队列全部播放完 */
  drain(): void {
    // 队列由 _playNext 自动消费，nothing to do here
  }

  private _playNext(): void {
    if (this._queue.length === 0) {
      this._state = 'idle'
      this.state.value = 'idle'
      return
    }

    const item = this._queue.shift()!
    this.audio = new Audio(item.url)
    this.audio.playbackRate = this.settings.value.rate
    this.audio.volume = this.settings.value.volume

    this.audio.onplay = () => {
      this._state = 'speaking'
      this.state.value = 'speaking'
    }
    this.audio.onended = () => {
      this._playNext()
    }
    this.audio.onerror = () => {
      console.warn('VoiceEngine audio playback error')
      this._playNext()
    }

    this.audio.play().catch(() => {
      this._playNext()
    })
  }

  stop(): void {
    if (this.audio) {
      this.audio.pause()
      this.audio = null
    }
    this._queue = []
    this._state = 'idle'
    this.state.value = 'idle'
  }

  pause(): void {
    if (this.audio && !this.audio.paused) {
      this.audio.pause()
      this._state = 'paused'
      this.state.value = 'paused'
    }
  }

  resume(): void {
    if (this.audio && this.audio.paused) {
      this.audio.play()
      this._state = 'speaking'
      this.state.value = 'speaking'
    }
  }
}

/** 全局单例 */
let _instance: VoiceEngine | null = null
export function useVoiceEngine(): VoiceEngine {
  if (!_instance) _instance = new VoiceEngine()
  return _instance
}
