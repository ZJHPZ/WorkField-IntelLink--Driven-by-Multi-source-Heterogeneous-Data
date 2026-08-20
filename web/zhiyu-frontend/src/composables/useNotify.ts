/** 全局通知 composable —— 配合 NotificationBar 组件使用。 */

import { reactive } from 'vue'

interface NotifyState {
  visible: boolean
  message: string
  detail: string
  type: 'info' | 'warning' | 'success'
}

const state = reactive<NotifyState>({
  visible: false,
  message: '',
  detail: '',
  type: 'info',
})

let timer: ReturnType<typeof setTimeout> | null = null

function show(message: string, detail = '', type: NotifyState['type'] = 'info', duration = 3000) {
  if (timer) clearTimeout(timer)
  state.message = message
  state.detail = detail
  state.type = type
  state.visible = true
  timer = setTimeout(() => {
    state.visible = false
    timer = null
  }, duration)
}

function close() {
  if (timer) clearTimeout(timer)
  state.visible = false
}

export function useNotify() {
  return { state, show, close }
}
