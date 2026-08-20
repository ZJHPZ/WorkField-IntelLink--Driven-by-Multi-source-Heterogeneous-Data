import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useAvatarSDK } from '@/composables/useAvatarSDK'

export const useAvatarStore = defineStore('avatar', () => {
  const sdk = useAvatarSDK()

  const enabled = ref(false)
  const mode = ref<'driver' | 'interact'>('driver')

  const isActive = computed(() => enabled.value && sdk.isConnected.value)

  // 同步 SDK 状态
  watch(() => sdk.error.value, (v) => { if (v) enabled.value = false })

  async function connectPlayer(wrapper: HTMLDivElement) {
    if (sdk.isConnected.value || sdk.isConnecting.value) return
    await sdk.connect(wrapper, {
      mode: mode.value,
      protocol: 'webrtc',
      fps: 25,
      bitrate: 4000000,
      width: 720,
      height: 1280,
    })
  }

  function movePlayer(wrapper: HTMLDivElement) {
    sdk.moveToContainer(wrapper)
  }

  function disconnectPlayer() {
    sdk.disconnect()
  }

  async function driveText(text: string) {
    if (!sdk.isConnected.value) return
    await sdk.driveText(text)
  }

  async function interactText(text: string) {
    if (!sdk.isConnected.value) return null
    return sdk.interactText(text)
  }

  async function interrupt() {
    await sdk.interrupt()
  }

  function toggle() {
    enabled.value = !enabled.value
  }

  async function stopSession() {
    sdk.disconnect()
    enabled.value = false
  }

  return {
    // 来自 SDK 的状态
    isConnecting: sdk.isConnecting,
    isPlaying: sdk.isPlaying,
    error: sdk.error,
    streamUrl: sdk.streamUrl,
    playNotAllowed: sdk.playNotAllowed,
    nlpText: sdk.nlpText,
    // Store 自身状态
    enabled,
    mode,
    isActive,
    // 方法
    connectPlayer,
    disconnectPlayer,
    movePlayer,
    driveText,
    interactText,
    interrupt,
    resumeAudio: sdk.resumeAudio,
    resize: sdk.resize,
    toggle,
    stopSession,
  }
})
