/**
 * useAvatarSDK — 讯飞虚拟人 SDK-Web 封装
 *
 * 通过后端获取鉴权 URL，动态加载 /public/avatar-sdk-web_3.2.3.1002/esm/index.js，
 * 管理 AvatarPlatform 实例、事件、生命周期。
 */
import { ref, shallowRef } from 'vue'

// ── 类型（对应 SDK index.d.ts）──
export interface AvatarSDKInstance {
  setApiInfo(info: {
    serverUrl?: string
    appId: string
    apiKey?: string
    apiSecret?: string
    sceneId?: string
    sceneVersion?: string
    signedUrl?: string
  }): AvatarSDKInstance

  setGlobalParams(config: {
    stream: { protocol: 'xrtc' | 'webrtc' | 'rtmp'; fps?: number; bitrate?: number; alpha?: 0 | 1 }
    avatar: { avatar_id: string; width: number; height: number; scale?: number; audio_format?: 1 | 2 }
    tts: { vcn: string; speed?: number; pitch?: number; volume?: number }
    avatar_dispatch?: { interactive_mode?: 0 | 1; content_analysis?: 0 | 1 }
    air?: { air: 0 | 1; add_nonsemantic?: 0 | 1 }
    subtitle?: { subtitle: 0 | 1; font_color?: string }
    background?: { type: string; data: string }
    originHost?: string
    targetHost?: string
  }): AvatarSDKInstance

  start(props?: { wrapper?: HTMLDivElement; preRes?: unknown }): Promise<void>
  writeText(text: string, extend: { nlp?: boolean; request_id?: string }): Promise<string>
  interrupt(): Promise<void>
  stop(): void
  destroy(): void
  player?: { resume(): Promise<void>; resize(): void; muted: boolean; volume: number }
  recorder?: unknown
  on(event: string, listener: (...args: any[]) => void): AvatarSDKInstance
  off(event: string, listener: (...args: any[]) => void): AvatarSDKInstance
}

const SDK_PATH = '/avatar-sdk-web_3.2.3.1002/esm/index.js'
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// 后端管理的凭证 — 通过 /api/v1/avatar/signed-url 获取
const AVATAR_CONFIG = {
  appId: import.meta.env.VITE_AVATAR_APP_ID || '',
  sceneId: import.meta.env.VITE_AVATAR_SCENE_ID || '',
  avatarId: import.meta.env.VITE_AVATAR_AVATAR_ID || '',
  voiceId: import.meta.env.VITE_AVATAR_VOICE_ID || '',
}

let _moduleCache: {
  AvatarPlatform: new (props?: unknown) => AvatarSDKInstance
  SDKEvents: Record<string, string>
  PlayerEvents: Record<string, string>
} | null = null
let _loadPromise: Promise<typeof _moduleCache> | null = null

async function loadSDK() {
  if (_moduleCache) return _moduleCache
  if (_loadPromise) return _loadPromise

  _loadPromise = new Promise((resolve, reject) => {
    const gk = '__avatarSDK__'
    const script = document.createElement('script')
    script.type = 'module'
    script.src = '/avatar-loader.js'
    script.onerror = () => {
      document.head.removeChild(script)
      _loadPromise = null
      reject(new Error('数字人 SDK 加载失败'))
    }
    script.onload = () => {
      let attempts = 0
      const check = setInterval(() => {
        const mod = (window as any)[gk]
        if (mod) {
          clearInterval(check)
          delete (window as any)[gk]
          _moduleCache = mod
          resolve(_moduleCache!)
        } else if (++attempts > 25) {
          clearInterval(check)
          document.head.removeChild(script)
          _loadPromise = null
          reject(new Error('数字人 SDK 加载超时'))
        }
      }, 200)
    }
    document.head.appendChild(script)
  })

  return _loadPromise
}

async function fetchSignedUrl(): Promise<string> {
  const resp = await fetch(`${API_BASE}/api/v1/avatar/signed-url?protocol=webrtc`)
  if (!resp.ok) {
    throw new Error(`获取数字人签名 URL 失败 (${resp.status})`)
  }
  const data = await resp.json()
  return data.url
}

export function useAvatarSDK() {
  const instance = shallowRef<AvatarSDKInstance | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const isPlaying = ref(false)
  const error = ref<string | null>(null)
  const nlpText = ref('')
  const playNotAllowed = ref(false)
  const streamUrl = ref<string | null>(null)

  let _wrapper: HTMLDivElement | null = null
  let _mode: 'driver' | 'interact' = 'driver'

  function _onConnected(data: any) {
    isConnected.value = true
    isConnecting.value = false
    error.value = null
    if (data?.stream_url) {
      streamUrl.value = data.stream_url
    }
  }

  function _onDisconnected(err?: any) {
    isConnected.value = false
    isConnecting.value = false
    isPlaying.value = false
    if (err?.message) {
      error.value = err.message
    }
  }

  function _onNlp(data: any) {
    nlpText.value = data?.displayContent || data?.content || ''
  }

  function _onFrameStart() {
    isPlaying.value = true
  }

  function _onFrameStop() {
    isPlaying.value = false
  }

  function _onError(err: { message?: string }) {
    error.value = err?.message || '虚拟人未知错误'
  }

  async function connect(
    wrapper: HTMLDivElement,
    options?: {
      mode?: 'driver' | 'interact'
      protocol?: 'xrtc' | 'webrtc'
      fps?: number
      bitrate?: number
      alpha?: 0 | 1
      width?: number
      height?: number
    },
  ) {
    if (isConnecting.value || isConnected.value) return

    isConnecting.value = true
    error.value = null
    nlpText.value = ''
    playNotAllowed.value = false
    _wrapper = wrapper
    _mode = options?.mode || 'driver'

    try {
      // 从后端获取鉴权 URL（凭证不暴露在前端）
      const signedUrl = await fetchSignedUrl()

      const sdk = await loadSDK()
      const platform = new sdk.AvatarPlatform({
        useInlinePlayer: true,
        logLevel: 2,
      })

      platform.on(sdk.SDKEvents.connected, _onConnected)
      platform.on(sdk.SDKEvents.disconnected, _onDisconnected)
      platform.on(sdk.SDKEvents.nlp, _onNlp)
      platform.on(sdk.SDKEvents.frame_start, _onFrameStart)
      platform.on(sdk.SDKEvents.frame_stop, _onFrameStop)
      platform.on(sdk.SDKEvents.error, _onError)

      if (platform.player) {
        ;(platform.player as any).on?.(sdk.PlayerEvents.playNotAllowed, () => {
          playNotAllowed.value = true
        })
      }

      platform.setApiInfo({
        signedUrl,
        appId: AVATAR_CONFIG.appId,
        sceneId: AVATAR_CONFIG.sceneId,
      })

      platform.setGlobalParams({
        stream: {
          protocol: options?.protocol || 'webrtc',
          fps: options?.fps ?? 25,
          bitrate: options?.bitrate ?? 4000000,
          alpha: options?.alpha ?? 0,
        },
        avatar: {
          avatar_id: AVATAR_CONFIG.avatarId,
          width: options?.width ?? 720,
          height: options?.height ?? 1280,
          audio_format: 1,
        },
        tts: {
          vcn: AVATAR_CONFIG.voiceId,
          speed: 50,
          pitch: 50,
          volume: 100,
        },
        avatar_dispatch: {
          interactive_mode: 1,
        },
      })

      await platform.start({ wrapper })

      instance.value = platform
    } catch (e: any) {
      isConnecting.value = false
      error.value = e?.message || '数字人连接失败'
    }
  }

  async function driveText(text: string) {
    const p = instance.value
    if (!p || !isConnected.value) return
    try {
      await p.writeText(text, { nlp: false })
    } catch (e: any) {
      error.value = e?.message || '文本驱动失败'
    }
  }

  async function interactText(text: string) {
    const p = instance.value
    if (!p || !isConnected.value) return null
    nlpText.value = ''
    try {
      await p.writeText(text, { nlp: true })
      return nlpText.value
    } catch (e: any) {
      error.value = e?.message || '文本交互失败'
      return null
    }
  }

  async function interrupt() {
    const p = instance.value
    if (!p || !isConnected.value) return
    try {
      await p.interrupt()
    } catch {}
  }

  function moveToContainer(wrapper: HTMLDivElement) {
    if (instance.value?.player) {
      ;(instance.value.player as any).container = wrapper
    }
    _wrapper = wrapper
  }

  function resumeAudio() {
    const p = instance.value
    if (p?.player) {
      p.player.muted = false
      p.player.resume().catch(() => {})
    }
    playNotAllowed.value = false
    document.dispatchEvent(new Event('click'))
  }

  function resize() {
    instance.value?.player?.resize()
  }

  function disconnect() {
    if (instance.value) {
      instance.value.stop()
      instance.value = null
    }
    isConnected.value = false
    isConnecting.value = false
    isPlaying.value = false
    error.value = null
    nlpText.value = ''
    playNotAllowed.value = false
    streamUrl.value = null
    _wrapper = null
  }

  function destroy() {
    if (instance.value) {
      instance.value.destroy()
      instance.value = null
    }
    isConnected.value = false
    isConnecting.value = false
    isPlaying.value = false
    error.value = null
    nlpText.value = ''
    playNotAllowed.value = false
    streamUrl.value = null
    _wrapper = null
  }

  return {
    instance,
    isConnected,
    isConnecting,
    isPlaying,
    error,
    nlpText,
    playNotAllowed,
    streamUrl,
    connect,
    driveText,
    interactText,
    interrupt,
    resumeAudio,
    resize,
    moveToContainer,
    disconnect,
    destroy,
  }
}
