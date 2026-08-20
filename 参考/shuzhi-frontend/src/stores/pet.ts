import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export type PetState = 'idle' | 'active' | 'alert' | 'celebrate' | 'sleeping'
export type PetId = 'cat-movement' | 'loader-cat' | 'orange-cat-peeping' | 'rainbow-cat-remix' | '8bit-cat'

export interface BubbleMessage {
  text: string
  buttons?: { label: string; value: string }[]
  duration?: number // ms, 0 = stay until dismissed
}

interface PetConfig {
  id: PetId
  name: string
  assetPath: string
  idleSegments: [number, number]
  activeSegments: [number, number]
  alertSegments: [number, number]
  celebrateAsset?: string
}

export const petConfigs: Record<PetId, PetConfig> = {
  'cat-movement': {
    id: 'cat-movement',
    name: '帕克',
    assetPath: '/assets/pet/cat-movement.json',
    idleSegments: [0, 88],
    activeSegments: [21, 131],
    alertSegments: [88, 131],
  },
  'loader-cat': {
    id: 'loader-cat',
    name: '小灰',
    assetPath: '/assets/pet/loader-cat.json',
    idleSegments: [0, 32],
    activeSegments: [0, 32],
    alertSegments: [0, 32],
  },
  'orange-cat-peeping': {
    id: 'orange-cat-peeping',
    name: '橘子',
    assetPath: '/assets/pet/orange-cat-peeping.json',
    idleSegments: [0, 77],
    activeSegments: [0, 77],
    alertSegments: [11, 35],
  },
  'rainbow-cat-remix': {
    id: 'rainbow-cat-remix',
    name: '彩虹',
    assetPath: '/assets/pet/rainbow-cat-remix.json',
    idleSegments: [0, 40],
    activeSegments: [0, 40],
    alertSegments: [0, 40],
    celebrateAsset: '/assets/pet/rainbow-cat-remix.json',
  },
  '8bit-cat': {
    id: '8bit-cat',
    name: '像素',
    assetPath: '/assets/pet/8bit-cat.json',
    idleSegments: [0, 104],
    activeSegments: [0, 104],
    alertSegments: [0, 104],
  },
}

// 预设对话库
const dialogLibrary: Record<string, BubbleMessage[]> = {
  idle: [
    { text: '今天天气不错，适合学习~', duration: 4000 },
    { text: '喵~ 有什么我可以帮你的吗？', duration: 4000 },
    { text: '累了就摸摸我休息一下吧。', duration: 3500 },
    { text: '你知道吗？大数据工程师的平均年薪很可观哦！', duration: 5000 },
    { text: 'HDFS 的默认块大小是 128MB，记住了吗？', duration: 5000 },
  ],
  active: [
    { text: '加油！今天的努力是明天的底气！', duration: 3500 },
    { text: '喵呜~ 你学得真认真！', duration: 3000 },
    { text: '这个知识点掌握得不错！', duration: 3000 },
  ],
  alert: [
    {
      text: '已经连续学习 2.5 小时了！帕克提醒你起来走走，喝杯水休息一下~ 🐱',
      buttons: [
        { label: '知道了', value: 'dismiss' },
        { label: '5分钟后再提醒', value: 'snooze' },
      ],
    },
    { text: '长时间坐着对颈椎不好哦，伸个懒腰吧！', duration: 4000 },
  ],
  celebrate: [
    { text: '太厉害了！你又完成了一个学习目标！🎉', duration: 5000 },
    { text: '连续打卡记录刷新中！帕克为你骄傲！', duration: 4000 },
  ],
  sleeping: [
    { text: 'zzZ... 帕克先眯一会儿...', duration: 3000 },
    { text: '呼噜呼噜... 等你回来学习~', duration: 3000 },
  ],
}

function getUserId(): string {
  return localStorage.getItem('user_id') || 'default_user'
}

function randomPick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

export const usePetStore = defineStore('pet', () => {
  const isVisible = ref(true)
  const currentState = ref<PetState>('idle')
  const currentPet = ref<PetId>('cat-movement')
  const position = ref({ x: 0, y: 0 }) // 距右下角的偏移 px
  const size = ref(120) // px
  const bubbleMessage = ref<BubbleMessage | null>(null)
  const isDragging = ref(false)
  const learningMinutes = ref(0)
  const restReminderShown = ref(false)
  const lastInteraction = ref(Date.now())
  const snoozeUntil = ref(0)

  // 当前宠物配置
  const currentConfig = computed(() => petConfigs[currentPet.value])

  // 宠物名字
  const petName = computed(() => currentConfig.value?.name || '帕克')

  // 是否应显示休息提醒
  const shouldRest = computed(() => {
    if (restReminderShown.value) return false
    if (Date.now() < snoozeUntil.value) return false
    return learningMinutes.value >= 150 // 2.5 小时
  })

  // 无操作超时 → 睡觉
  const shouldSleep = computed(() => {
    if (currentState.value === 'alert' || currentState.value === 'celebrate') return false
    return Date.now() - lastInteraction.value > 5 * 60 * 1000 // 5分钟无操作
  })

  function setState(state: PetState) {
    currentState.value = state
    lastInteraction.value = Date.now()
  }

  function showBubble(msg: BubbleMessage) {
    bubbleMessage.value = msg
    if (msg.duration && msg.duration > 0) {
      setTimeout(() => {
        if (bubbleMessage.value === msg) {
          bubbleMessage.value = null
        }
      }, msg.duration)
    }
  }

  function dismissBubble() {
    bubbleMessage.value = null
  }

  function randomChat(category?: PetState) {
    const cat = category || currentState.value
    const msgs = dialogLibrary[cat] || dialogLibrary.idle
    if (msgs.length > 0) {
      showBubble(randomPick(msgs))
    }
  }

  function interact() {
    setState('active')
    randomChat('active')
    // 3 秒后回到 idle
    setTimeout(() => {
      if (currentState.value === 'active') {
        setState('idle')
      }
    }, 3000)
  }

  function triggerAlert(message?: string) {
    setState('alert')
    restReminderShown.value = true
    if (message) {
      showBubble({ text: message, buttons: [{ label: '知道了', value: 'dismiss' }] })
    } else {
      const alertMsgs = dialogLibrary.alert
      showBubble(randomPick(alertMsgs))
    }
  }

  function handleAlertAction(action: string) {
    if (action === 'dismiss') {
      dismissBubble()
      setState('idle')
    } else if (action === 'snooze') {
      dismissBubble()
      snoozeUntil.value = Date.now() + 5 * 60 * 1000
      restReminderShown.value = false
      setState('idle')
    }
  }

  function celebrate(message?: string) {
    setState('celebrate')
    showBubble({
      text: message || randomPick(dialogLibrary.celebrate).text,
      duration: 5000,
    })
    setTimeout(() => {
      if (currentState.value === 'celebrate') {
        setState('idle')
      }
    }, 5000)
  }

  function tickLearning(minutes: number) {
    learningMinutes.value += minutes
  }

  function setPosition(x: number, y: number) {
    position.value = { x, y }
    saveSettings()
  }

  function setSize(s: number) {
    size.value = Math.max(60, Math.min(300, s))
    saveSettings()
  }

  function setCurrentPet(pet: PetId) {
    currentPet.value = pet
    saveSettings()
  }

  function toggleVisibility() {
    isVisible.value = !isVisible.value
  }

  function resetRestTimer() {
    learningMinutes.value = 0
    restReminderShown.value = false
    snoozeUntil.value = 0
  }

  // 持久化设置 (localStorage + 后端同步)
  async function saveSettings() {
    const settings = {
      currentPet: currentPet.value,
      position: position.value,
      size: size.value,
    }
    localStorage.setItem(`pet_settings_${getUserId()}`, JSON.stringify(settings))

    // 异步同步到后端
    try {
      await client.put(`/api/v1/users/${getUserId()}/pet-settings`, null, {
        params: {
          current_pet: currentPet.value,
          position_x: position.value.x,
          position_y: position.value.y,
          size: size.value,
        },
      })
    } catch { /* 后端不可用时仅本地存储 */ }
  }

  async function loadSettings() {
    // 优先从后端加载
    try {
      const data = await client.get(`/api/v1/users/${getUserId()}/pet-settings`) as any
      if (data?.data) {
        const s = data.data
        if (s.current_pet) currentPet.value = s.current_pet
        if (s.position) position.value = s.position
        if (s.size) size.value = s.size
        if (s.is_visible !== undefined) isVisible.value = s.is_visible
        return
      }
    } catch { /* 后端不可用，使用本地存储 */ }

    // 本地存储回退
    try {
      const raw = localStorage.getItem(`pet_settings_${getUserId()}`)
      if (raw) {
        const settings = JSON.parse(raw)
        if (settings.currentPet) currentPet.value = settings.currentPet
        if (settings.position) position.value = settings.position
        if (settings.size) size.value = settings.size
      }
    } catch { /* ignore */ }
  }

  // 初始化
  loadSettings()

  return {
    isVisible, currentState, currentPet, position, size,
    bubbleMessage, isDragging, learningMinutes, restReminderShown,
    lastInteraction, snoozeUntil,
    currentConfig, petName, shouldRest, shouldSleep,
    setState, showBubble, dismissBubble, randomChat, interact,
    triggerAlert, handleAlertAction, celebrate,
    tickLearning, setPosition, setSize, setCurrentPet,
    toggleVisibility, resetRestTimer,
    loadSettings, saveSettings,
  }
})
