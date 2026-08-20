/**
 * 波纹点击效果 — 点击时从点击点向外扩散环形波
 * 用法：const { rippleX, rippleY, rippleActive, onClick } = useRippleClick()
 */
import { ref } from 'vue'

export function useRippleClick() {
  const rippleX = ref(50)
  const rippleY = ref(50)
  const rippleActive = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  const onClick = (e: MouseEvent) => {
    const el = e.currentTarget as HTMLElement
    const rect = el.getBoundingClientRect()
    rippleX.value = ((e.clientX - rect.left) / rect.width) * 100
    rippleY.value = ((e.clientY - rect.top) / rect.height) * 100

    if (timer) clearTimeout(timer)
    rippleActive.value = false
    void el.offsetWidth // force reflow
    rippleActive.value = true
    timer = setTimeout(() => { rippleActive.value = false }, 600)
  }

  return { rippleX, rippleY, rippleActive, onClick }
}
