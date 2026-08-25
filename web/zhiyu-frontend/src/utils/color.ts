/**
 * 颜色工具 — 统一霓虹色板 + hex 转换
 * 供 canvas / SVG 组件使用（CSS 侧走 var(--*) token）
 */

/** 语义色板（默认深空 indigo 主题；warm 主题 brand 用 getBrandColor() 读取） */
export const PALETTE = {
  brand: '#818cf8',
  brandStrong: '#6366f1',
  cyan: '#06b6d4',
  cyanLight: '#22d3ee',
  purple: '#a855f7',
  mint: '#10b981',
  mintLight: '#34d399',
  amber: '#f59e0b',
  amberLight: '#fbbf24',
  rose: '#f43f5e',
  roseLight: '#fb7185',
} as const

export type PaletteKey = keyof typeof PALETTE

/** #rrggbb / #rgb → [r, g, b] */
export function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '').trim()
  const full = h.length === 3
    ? h.split('').map((c) => c + c).join('')
    : h
  const n = parseInt(full, 16)
  if (Number.isNaN(n)) return [0, 0, 0]
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

/** #rrggbb → 归一化 [0..1] 分量（Three.js 用） */
export function hexToVec3(hex: string): [number, number, number] {
  const [r, g, b] = hexToRgb(hex)
  return [r / 255, g / 255, b / 255]
}

/**
 * 读取当前主题的 brand-500（warm 主题下为玫红 #e8536c，而非静态 indigo）。
 * canvas/SVG 组件用此函数获得真实主题色。
 */
export function getBrandColor(fallback: string = PALETTE.brand): string {
  if (typeof document === 'undefined') return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue('--brand-500').trim()
  return v || fallback
}

/** 读取语义色 token 的当前值（同 getBrandColor 思路） */
export function getCssColor(varName: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
  return v || fallback
}
