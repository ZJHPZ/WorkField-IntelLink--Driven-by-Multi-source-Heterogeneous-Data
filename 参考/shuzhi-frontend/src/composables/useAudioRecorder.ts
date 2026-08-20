/**
 * useAudioRecorder — 浏览器语音输入 Composable
 *
 * 优先使用 Web Speech API (SpeechRecognition)，实时识别无需上传。
 * 降级使用 MediaRecorder 录音 + 后端 ASR。
 */
import { ref, readonly } from 'vue'

// 扩展 Window 类型
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

export function useAudioRecorder() {
  // 浏览器语音识别支持检测
  const SpeechRecognitionAPI =
    typeof window !== 'undefined'
      ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      : null

  const isSupported = ref(!!(SpeechRecognitionAPI || (
    typeof window !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof MediaRecorder !== 'undefined'
  )))

  const isRecording = ref(false)
  const duration = ref(0)
  const audioBlob = ref<Blob | null>(null)
  const error = ref<string | null>(null)

  // Web Speech 模式
  let recognition: any = null
  let interimText = ''

  // MediaRecorder 降级模式
  let mediaRecorder: MediaRecorder | null = null
  let stream: MediaStream | null = null
  let timer: ReturnType<typeof setInterval> | null = null
  const chunks: Blob[] = []
  let mimeType: string = ''
  let _stopResolver: ((blob: Blob | null) => void) | null = null

  // 录音结果回调
  let _onResult: ((text: string) => void) | null = null
  let _onInterim: ((text: string) => void) | null = null

  function startTimer() {
    duration.value = 0
    timer = setInterval(() => { duration.value++ }, 1000)
  }

  function stopTimer() {
    if (timer) { clearInterval(timer); timer = null }
  }

  /** 设置识别结果回调 */
  function onResult(cb: (text: string) => void) { _onResult = cb }
  function onInterim(cb: (text: string) => void) { _onInterim = cb }

  /** 使用 Web Speech API 开始语音识别 */
  function startWithWebSpeech(): void {
    if (!SpeechRecognitionAPI) return

    error.value = null
    interimText = ''
    _finalText = ''
    isRecording.value = true
    startTimer()

    _startRecognition()
  }

  let _finalText = ''         // 已确认的最终文本
  let _restartCount = 0       // 自动重启计数
  const MAX_RESTARTS = 30     // 最多自动重启 30 次（约 5-10 分钟）

  function _startRecognition(): void {
    if (!isRecording.value) return
    if (_restartCount >= MAX_RESTARTS) {
      // 自动停止，避免无限循环
      isRecording.value = false
      stopTimer()
      if (_finalText.trim()) {
        _onResult?.(_finalText.trim())
      }
      return
    }

    recognition = new SpeechRecognitionAPI()
    recognition.lang = 'zh-CN'
    recognition.interimResults = true
    recognition.continuous = false     // 每段话说完自动结束，onend 中重启
    recognition.maxAlternatives = 1

    recognition.onresult = (event: any) => {
      let currentInterim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          _finalText += transcript
        } else {
          currentInterim += transcript
        }
      }
      // 显示：已确认 + 当前识别中的文字
      const display = (_finalText + currentInterim).trim()
      if (display) {
        _onInterim?.(display)
      }
      // 有新的 final 结果时通知
      if (_finalText.trim()) {
        _onResult?.(_finalText.trim())
      }
    }

    recognition.onerror = (event: any) => {
      if (event.error === 'no-speech' || event.error === 'aborted') return
      error.value = `语音识别错误: ${event.error}`
    }

    recognition.onend = () => {
      // 仍在录音状态 → 自动重启以支持连续说话
      if (isRecording.value) {
        _restartCount++
        _startRecognition()
      } else {
        stopTimer()
        if (_finalText.trim()) {
          _onResult?.(_finalText.trim())
        }
      }
    }

    try {
      recognition.start()
    } catch {
      // 可能已经在运行
    }
  }

  /** 使用 MediaRecorder 降级模式 (Firefox / Safari) */
  async function startWithMediaRecorder(): Promise<void> {
    error.value = null
    chunks.length = 0
    audioBlob.value = null

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
      })

      mimeType = getSupportedMimeType()
      mediaRecorder = new MediaRecorder(stream, { mimeType, audioBitsPerSecond: 64000 })

      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }
      mediaRecorder.onstop = () => {
        const blob = chunks.length > 0 ? new Blob(chunks, { type: mimeType || 'audio/webm' }) : null
        audioBlob.value = blob
        releaseStream()
        stopTimer()
        isRecording.value = false
        if (_stopResolver) { _stopResolver(blob); _stopResolver = null }
      }
      mediaRecorder.onerror = () => {
        error.value = '录音过程出错'
        releaseStream()
        stopTimer()
        isRecording.value = false
        if (_stopResolver) { _stopResolver(null); _stopResolver = null }
      }

      mediaRecorder.start(250)
      isRecording.value = true
      startTimer()
    } catch (e: any) {
      error.value = e.message || '无法访问麦克风'
      isRecording.value = false
    }
  }

  async function start(): Promise<void> {
    if (!isSupported.value) { error.value = '浏览器不支持语音输入'; return }
    // 优先 Web Speech API (Chrome/Edge)
    if (SpeechRecognitionAPI) {
      startWithWebSpeech()
    } else {
      await startWithMediaRecorder()
    }
  }

  /** 停止语音识别/录音 */
  function stop(): Promise<Blob | null> {
    if (recognition) {
      isRecording.value = false
      _restartCount = MAX_RESTARTS  // 阻止 onend 自动重启
      try { recognition.stop() } catch { /* 忽略 */ }
      recognition = null
      stopTimer()
      return Promise.resolve(null)
    }
    return new Promise((resolve) => {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        _stopResolver = resolve
        mediaRecorder.stop()
      } else {
        releaseStream()
        stopTimer()
        isRecording.value = false
        resolve(audioBlob.value)
      }
    })
  }

  function cancel(): void {
    if (recognition) {
      isRecording.value = false
      _restartCount = MAX_RESTARTS
      interimText = ''
      _finalText = ''
      try { recognition.abort() } catch { /* 忽略 */ }
      recognition = null
      stopTimer()
      return
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.onstop = () => {
        releaseStream()
        stopTimer()
        isRecording.value = false
        if (_stopResolver) { _stopResolver(null); _stopResolver = null }
      }
      mediaRecorder.stop()
    }
    chunks.length = 0
    audioBlob.value = null
    releaseStream()
    stopTimer()
    isRecording.value = false
  }

  function releaseStream() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null }
    mediaRecorder = null
  }

  function getSupportedMimeType(): string {
    for (const t of ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/wav']) {
      if (MediaRecorder.isTypeSupported(t)) return t
    }
    return ''
  }

  return {
    isSupported: readonly(isSupported),
    isRecording: readonly(isRecording),
    duration: readonly(duration),
    audioBlob: readonly(audioBlob),
    error: readonly(error),
    start,
    stop,
    cancel,
    onResult,
    onInterim,
    /** 是否使用 Web Speech API（实时识别，不需要上传） */
    useWebSpeech: !!SpeechRecognitionAPI,
  }
}
