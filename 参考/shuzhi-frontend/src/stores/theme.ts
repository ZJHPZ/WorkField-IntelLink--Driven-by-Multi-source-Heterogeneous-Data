import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'shuzhi_theme'

function getStoredTheme(): ThemeMode | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'light' || v === 'dark') return v
  } catch { /* ignore */ }
  return null
}

export const useThemeStore = defineStore('theme', () => {
  const stored = getStoredTheme()
  // 「宇宙战舰」视觉基底：默认深色星空
  const mode = ref<ThemeMode>(stored || 'dark')

  function applyTheme(routePath?: string) {
    const root = document.documentElement
    root.setAttribute('data-theme', mode.value)

    // 更新 meta theme-color
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', mode.value === 'dark' ? '#050510' : '#f8fafc')
    }
    // 防止未使用的参数警告
    void routePath
  }

  function toggle() {
    mode.value = mode.value === 'light' ? 'dark' : 'light'
  }

  function setTheme(m: ThemeMode) {
    mode.value = m
  }

  // 持久化
  watch(mode, (m) => {
    try { localStorage.setItem(STORAGE_KEY, m) } catch { /* ignore */ }
    applyTheme()
  })

  // 初始应用
  applyTheme()

  return { mode, applyTheme, toggle, setTheme }
})
