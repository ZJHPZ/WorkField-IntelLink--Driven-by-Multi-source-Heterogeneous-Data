/**
 * useAvatarSDK — 讯飞虚拟人 SDK-Web 封装
 *
 * 凭证由服务端 `/api/enterprise/avatar/signed-url` 签发（apiKey/apiSecret 不落前端），
 * 前端只拿到限时 signedUrl + 非机密资源 ID。动态加载
 * `/avatar-sdk-web_3.2.3.1002/esm/index.js`，管理 AvatarPlatform 实例、事件、生命周期。
 *
 * 服务端未配置凭证 → 抛 AvatarNotConfiguredError，调用方切换「演示数字人」。
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

/** 服务端 /api/enterprise/avatar/signed-url 契约（camelCase）。
 *  personaReady：资源 ID（appId/sceneId/avatarId/voiceId）齐备即可引用真实 persona；
 *  configured：资源 ID + 密钥齐备才签发 signedUrl 走真实 SDK。 */
export interface AvatarConfig {
  configured: boolean
  personaReady?: boolean
  signedUrl?: string
  appId?: string
  sceneId?: string
  avatarId?: string
  voiceId?: string
}

export interface AvatarPersona {
  avatarId: string
  voiceId: string
}

export class AvatarNotConfiguredError extends Error {
  constructor() {
    super('AVATAR_NOT_CONFIGURED')
    this.name = 'AvatarNotConfiguredError'
  }
}

const SDK_LOADER = '/avatar-loader.js'

type AvatarSDKModule = {
  AvatarPlatform: new (props?: unknown) => AvatarSDKInstance
  SDKEvents: Record<string, string>
  PlayerEvents: Record<string, string>
}
let _moduleCache: AvatarSDKModule | null = null
let _loadPromise: Promise<AvatarSDKModule> | null = null

async function loadSDK() {
  if (_moduleCache) return _moduleCache
  if (_loadPromise) return _loadPromise

  _loadPromise = new Promise((resolve, reject) => {
    const gk = '__avatarSDK__'
    const script = document.createElement('script')
    script.type = 'module'
    // avatar-loader.js 负责 import SDK 并挂到 window.__avatarSDK__（SDK ESM 自身不注册全局）
    script.src = SDK_LOADER
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

async function fetchAvatarConfig(): Promise<AvatarConfig> {
  const resp = await fetch('/api/enterprise/avatar/signed-url')
  if (!resp.ok) throw new Error(`获取数字人配置失败 (${resp.status})`)
  const data = await resp.json()
  return (data || {}) as AvatarConfig
}

/** 仅读取 persona（形象/音色 ID），不要求签名配置 —— 演示模式用它标识真实 persona。 */
async function getPersona(): Promise<AvatarPersona | null> {
  try {
    const cfg = await fetchAvatarConfig()
    if (cfg.personaReady && cfg.avatarId && cfg.voiceId) {
      return { avatarId: cfg.avatarId, voiceId: cfg.voiceId }
    }
    return null
  } catch {
    return null
  }
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
    if (data?.stream_url) streamUrl.value = data.stream_url
  }

  function _onDisconnected(err?: any) {
    isConnected.value = false
    isConnecting.value = false
    isPlaying.value = false
    if (err?.message) error.value = err.message
  }

  function _onNlp(data: any) {
    nlpText.value = data?.displayContent || data?.content || ''
  }

  function _onFrameStart() { isPlaying.value = true }
  function _onFrameStop() { isPlaying.value = false }

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
      // 凭证由服务端签发，前端不接触 apiKey/apiSecret；未配置 → 抛错交给演示模式
      const config = await fetchAvatarConfig()
      if (!config.configured) throw new AvatarNotConfiguredError()

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
        signedUrl: config.signedUrl,
        appId: config.appId || '',
        sceneId: config.sceneId,
      })

      platform.setGlobalParams({
        stream: {
          protocol: options?.protocol || 'webrtc',
          fps: options?.fps ?? 25,
          bitrate: options?.bitrate ?? 4000000,
          alpha: options?.alpha ?? 0,
        },
        avatar: {
          avatar_id: config.avatarId || '',
          width: options?.width ?? 720,
          height: options?.height ?? 1280,
          audio_format: 1,
        },
        tts: {
          vcn: config.voiceId || '',
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
      // 未配置 / SDK 失败统一抛给调用方处理（演示模式接管）
      throw e
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

  async function interrupt() {
    const p = instance.value
    if (!p || !isConnected.value) return
    try { await p.interrupt() } catch {}
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
    interrupt,
    resumeAudio,
    disconnect,
    getPersona,
  }
}
