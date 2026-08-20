<template>
  <div class="metaball-wrap relative" :style="{ height: height + 'px' }">
    <canvas ref="canvasRef" class="w-full h-full" />
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { SimplexNoise } from '@/utils/noise'

interface Ball {
  x: number; y: number
  vx: number; vy: number
  r: number       // 半径
  color: string   // #rrggbb
  noiseOff: number
}

const props = withDefaults(defineProps<{
  balls?: Ball[]
  height?: number
  threshold?: number      // metaball 融合阈值
  colors?: string[]       // 默认颜色池
  interactive?: boolean   // 鼠标交互
}>(), {
  balls: () => [],
  height: 300,
  threshold: 0.55,
  colors: () => ['#818cf8', '#06b6d4', '#a855f7', '#10b981'],
  interactive: true,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animId = 0
let time = 0
const noise = new SimplexNoise(99)

// 内部球体（如果没有传入balls，自动生成）
let internalBalls: Ball[] = []
const activeBalls = ref<Ball[]>([])

function initBalls(w: number, h: number) {
  if (props.balls.length) {
    activeBalls.value = props.balls
  } else {
    const count = 8 + Math.floor(Math.random() * 5)
    internalBalls = Array.from({ length: count }, (_, i) => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      r: 20 + Math.random() * 40,
      color: props.colors[i % props.colors.length],
      noiseOff: Math.random() * 1000,
    }))
    activeBalls.value = internalBalls
  }
}

// 鼠标位置
const mouse = { x: -1000, y: -1000 }

function onMouseMove(e: MouseEvent) {
  if (!props.interactive) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
}

function updateBalls(w: number, h: number) {
  const t = time * 0.01
  activeBalls.value.forEach(b => {
    // 噪声驱动有机运动
    const nx = noise.noise3D(b.x * 0.003, b.y * 0.003, t + b.noiseOff)
    const ny = noise.noise3D(b.x * 0.003, b.y * 0.003, t + b.noiseOff + 100)
    b.vx += nx * 0.02
    b.vy += ny * 0.02

    // 鼠标吸引
    if (props.interactive && mouse.x > 0) {
      const dx = mouse.x - b.x
      const dy = mouse.y - b.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 200 && dist > 0) {
        b.vx += (dx / dist) * 0.05
        b.vy += (dy / dist) * 0.05
      }
    }

    // 阻力 + 边界弹回
    b.vx *= 0.98
    b.vy *= 0.98
    b.x += b.vx
    b.y += b.vy

    if (b.x < b.r) { b.x = b.r; b.vx *= -0.6 }
    if (b.x > w - b.r) { b.x = w - b.r; b.vx *= -0.6 }
    if (b.y < b.r) { b.y = b.r; b.vy *= -0.6 }
    if (b.y > h - b.r) { b.y = h - b.r; b.vy *= -0.6 }
  })
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  const w = rect.width, h = rect.height

  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr; canvas.height = h * dpr; ctx.scale(dpr, dpr)
  }

  time++
  updateBalls(w, h)

  // Metaball 渲染：逐像素采样标量场
  // 优化：只在球体附近区域采样
  const step = 3 // 采样步长（越大越快，越小越精细）
  const threshold = props.threshold

  ctx.clearRect(0, 0, w, h)

  // 使用 ImageData 逐像素渲染
  const imgData = ctx.createImageData(Math.ceil(w / step), Math.ceil(h / step))
  const data = imgData.data

  for (let py = 0; py < h; py += step) {
    for (let px = 0; px < w; px += step) {
      let totalField = 0
      let r = 0, g = 0, b_ = 0, totalWeight = 0

      for (const ball of activeBalls.value) {
        const dx = px - ball.x
        const dy = py - ball.y
        const distSq = dx * dx + dy * dy
        const field = (ball.r * ball.r) / (distSq + 1)
        totalField += field

        if (field > 0.01) {
          const c = hexToRgb(ball.color)
          const w = field
          r += c.r * w; g += c.g * w; b_ += c.b * w; totalWeight += w
        }
      }

      if (totalField > threshold) {
        const idx = ((py / step) * Math.ceil(w / step) + (px / step)) * 4
        const blend = Math.min(totalField / threshold, 3) / 3
        const alpha = Math.min(blend * 0.8, 0.9)

        if (totalWeight > 0) {
          data[idx] = Math.round(r / totalWeight)
          data[idx + 1] = Math.round(g / totalWeight)
          data[idx + 2] = Math.round(b_ / totalWeight)
        } else {
          data[idx] = 99; data[idx + 1] = 102; data[idx + 2] = 241
        }
        data[idx + 3] = Math.round(alpha * 255)
      }
    }
  }

  // 缩放回原尺寸
  const tempCanvas = document.createElement('canvas')
  tempCanvas.width = Math.ceil(w / step)
  tempCanvas.height = Math.ceil(h / step)
  tempCanvas.getContext('2d')!.putImageData(imgData, 0, 0)

  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(tempCanvas, 0, 0, w, h)

  // 叠加球体核心光点
  ctx.globalCompositeOperation = 'lighter'
  activeBalls.value.forEach(b => {
    const grad = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r * 0.6)
    const c = hexToRgb(b.color)
    grad.addColorStop(0, `rgba(${c.r},${c.g},${c.b},0.3)`)
    grad.addColorStop(1, 'transparent')
    ctx.fillStyle = grad
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.r * 0.6, 0, Math.PI * 2)
    ctx.fill()
  })
  ctx.globalCompositeOperation = 'source-over'

  animId = requestAnimationFrame(draw)
}

function hexToRgb(hex: string) {
  const m = hex.match(/^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i)
  return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : { r: 99, g: 102, b: 241 }
}

onMounted(() => {
  const canvas = canvasRef.value
  if (canvas) {
    const rect = canvas.getBoundingClientRect()
    initBalls(rect.width, rect.height)
  }
  animId = requestAnimationFrame(draw)
})

onUnmounted(() => cancelAnimationFrame(animId))
</script>

<style scoped>
.metaball-wrap { overflow: hidden; position: relative; }
canvas { display: block; }
</style>
