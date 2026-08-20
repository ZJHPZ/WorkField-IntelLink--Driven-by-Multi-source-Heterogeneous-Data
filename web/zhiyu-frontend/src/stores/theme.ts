import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ThemeMode = 'dark' | 'light'
export type ThemePalette = 'indigo' | 'warm'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(
    (localStorage.getItem('theme_mode') as ThemeMode) || 'dark'
  )
  const palette = ref<ThemePalette>(
    (localStorage.getItem('theme_palette') as ThemePalette) || 'indigo'
  )

  function getThemeAttr(): string {
    if (palette.value === 'warm') {
      return mode.value === 'dark' ? 'warm' : 'warm-light'
    }
    return mode.value // 'dark' | 'light'
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', getThemeAttr())
    localStorage.setItem('theme_mode', mode.value)
    localStorage.setItem('theme_palette', palette.value)
  }

  function toggle() {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
    applyTheme()
  }

  function setMode(m: ThemeMode) {
    mode.value = m
    applyTheme()
  }

  function setPalette(p: ThemePalette) {
    palette.value = p
    applyTheme()
  }

  return { mode, palette, toggle, setMode, setPalette, applyTheme }
})
