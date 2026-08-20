/**
 * 磁吸悬停效果 — 元素被鼠标"吸引"产生偏移
 * 用法：const { style, onMouseMove, onMouseLeave } = useMagneticHover({ strength: 0.3, radius: 150 })
 */
import { ref, computed, type CSSProperties } from 'vue'

export function useMagneticHover(opts: { strength?: number; radius?: number; scale?: number } = {}) {
  const { strength = 0.3, radius = 150, scale = 1.02 } = opts

  const offsetX = ref(0)
  const offsetY = ref(0)
  const isHovering = ref(false)

  const style = computed<CSSProperties>(() => ({
    transform: `translate(${offsetX.value}px, ${offsetY.value}px) ${isHovering.value ? `scale(${scale})` : ''}`,
    transition: isHovering.value ? 'transform 0.15s ease-out' : 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
  }))

  const onMouseMove = (e: MouseEvent) => {
    const el = e.currentTarget as HTMLElement
    const rect = el.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    const dx = e.clientX - cx
    const dy = e.clientY - cy
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < radius) {
      const factor = (1 - dist / radius) * strength
      offsetX.value = dx * factor
      offsetY.value = dy * factor
      isHovering.value = true
    } else {
      offsetX.value = 0
      offsetY.value = 0
      isHovering.value = false
    }
  }

  const onMouseLeave = () => {
    offsetX.value = 0
    offsetY.value = 0
    isHovering.value = false
  }

  return { style, onMouseMove, onMouseLeave }
}
