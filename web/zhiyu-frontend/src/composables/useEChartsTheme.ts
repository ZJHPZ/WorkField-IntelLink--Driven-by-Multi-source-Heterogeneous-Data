/** ECharts 主题色 composable —— 根据当前主题动态返回配色。 */

import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

export function useEChartsTheme() {
  const themeStore = useThemeStore()

  const isDark = computed(() => themeStore.mode === 'dark')
  const isWarm = computed(() => themeStore.palette === 'warm')

  /** 品牌主色 */
  const brand = computed(() => isWarm.value ? '#e8536c' : '#818cf8')
  /** 品牌深色 */
  const brandDark = computed(() => isWarm.value ? '#d43d56' : '#6366f1')
  /** 品牌浅色 */
  const brandLight = computed(() => isWarm.value ? '#f48f9c' : '#a5b4fc')
  /** 辅助色（cyan 保持不变） */
  const cyan = '#06b6d4'
  /** 语义色 */
  const mint = '#10b981'
  const rose = '#f43f5e'

  /** tooltip 背景色 */
  const tooltipBg = computed(() => isDark.value ? 'rgba(15,23,42,0.95)' : 'rgba(255,255,255,0.98)')
  /** tooltip 边框色 */
  const tooltipBorder = computed(() => isDark.value ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.2)')
  /** tooltip 文字色 */
  const tooltipText = computed(() => isDark.value ? '#e2e8f0' : '#1e293b')
  /** 轴标签色 */
  const axisLabel = computed(() => isDark.value ? '#94a3b8' : '#64748b')
  /** 轴线色 */
  const axisLine = computed(() => isDark.value ? 'rgba(99,102,241,0.2)' : 'rgba(99,102,241,0.15)')
  /** 分割线色 */
  const splitLine = computed(() => isDark.value ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.06)')

  /** tooltip 配置 */
  const tooltipConfig = computed(() => ({
    backgroundColor: tooltipBg.value,
    borderColor: tooltipBorder.value,
    textStyle: { color: tooltipText.value, fontSize: 11 },
  }))

  return {
    isDark, isWarm,
    brand, brandDark, brandLight,
    cyan, mint, rose,
    tooltipBg, tooltipBorder, tooltipText,
    axisLabel, axisLine, splitLine,
    tooltipConfig,
  }
}
