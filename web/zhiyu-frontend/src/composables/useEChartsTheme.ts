/**
 * ECharts 主题色 composable —— 以 CSS var 为单一来源（variables.css 定义各主题值）。
 * 依赖 themeStore 触发响应式重算：主题切换时 ECharts option 自动重建。
 * 注意：所有返回值均为 ComputedRef，消费端用 `.value` 取值。
 */

import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { getCssColor } from '@/utils/color'

export function useEChartsTheme() {
  const themeStore = useThemeStore()

  const isDark = computed(() => themeStore.mode === 'dark')
  const isWarm = computed(() => themeStore.palette === 'warm')

  /** 读取 CSS var（跟随 data-theme），以 themeStore 为响应触发器 */
  const cssVar = (varName: string, fallback: string) =>
    computed(() => {
      void isDark.value
      void isWarm.value
      return getCssColor(varName, fallback)
    })

  /** 品牌主色 */
  const brand = cssVar('--brand-500', '#818cf8')
  /** 品牌深色 */
  const brandDark = cssVar('--brand-600', '#6366f1')
  /** 品牌浅色 */
  const brandLight = cssVar('--brand-400', '#a5b4fc')
  /** 辅助色（cyan 主题无关） */
  const cyan = cssVar('--cyan-500', '#06b6d4')
  /** 语义色 */
  const mint = cssVar('--mint-500', '#10b981')
  const rose = cssVar('--rose-500', '#f43f5e')

  /** tooltip 背景色 */
  const tooltipBg = computed(() => isDark.value ? 'rgba(15,23,42,0.95)' : 'rgba(255,255,255,0.98)')
  /** tooltip 边框色（brand 8 位 hex + alpha，跟随主题） */
  const tooltipBorder = computed(() => brand.value + (isDark.value ? '4d' : '33'))
  /** tooltip 文字色 */
  const tooltipText = computed(() => isDark.value ? '#e2e8f0' : '#1e293b')
  /** 轴标签色 */
  const axisLabel = computed(() => isDark.value ? '#94a3b8' : '#64748b')
  /** 轴线色 */
  const axisLine = computed(() => brand.value + (isDark.value ? '1f' : '14'))
  /** 分割线色 */
  const splitLine = computed(() => brand.value + (isDark.value ? '14' : '0f'))

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
