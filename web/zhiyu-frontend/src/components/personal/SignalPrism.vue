<template>
  <div class="prism-wrap relative" :style="{ height: height + 'px' }" @mousemove="onMouseMove" @mouseleave="onMouseLeave">
    <canvas ref="canvasRef" class="w-full h-full" />
    <!-- 标签叠加层 -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute text-xs font-mono font-bold tracking-wider" :style="{ left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)' }">
        ALL SKILLS
      </div>
      <div v-for="beam in beams" :key="beam.source"
        class="absolute text-xs font-mono font-bold tracking-wider flex items-center gap-2"
        :style="{ right: '16px', top: (beam.targetY / 280 * height - 6) + 'px', color: beam.color }">
        <span class="w-2 h-2 rounded-full" :style="{ background: beam.color, boxShadow: '0 0 8px ' + beam.color }"></span>
        {{ beam.label }}
        <span style="color:var(--text-muted);font-weight:400">{{ beam.count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { SimplexNoise, fbm } from '@/utils/noise'
import { getBrandColor, PALETTE } from '@/utils/color'

interface BeamData {
  source: string; label: string; count: number; color: string; targetY: number
}

const props = withDefaults(defineProps<{
  beams: BeamData[]
  height?: number
}>(), { height: 280 })

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animId = 0
let time = 0
const noise = new SimplexNoise(42)
const noise2 = new SimplexNoise(137)

// 鼠标交互
const mouse = { x: -1000, y: -1000, active: false }
function onMouseMove(e: MouseEvent) {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
  mouse.active = true
}
function onMouseLeave() { mouse.active = false; mouse.x = -1000; mouse.y = -1000 }

// ── 粒子系统 ──

interface Particle {
  x: number; y: number; vx: number; vy: number
  life: number; maxLife: number; size: number; alpha: number
  color: string; phase: 'input' | 'refract'; beamIdx: number
  noiseOff: number // 噪声偏移（每个粒子独特）
}

let inputParticles: Particle[] = []
let beamParticles: Particle[][] = [[], [], [], []]

// 力场参数
const FORCES = {
  noiseStrength: 0.4,    // 噪声扰动力度
  mouseRadius: 120,       // 鼠标影响半径
  mouseStrength: 0.8,     // 鼠标排斥力度
  gravity: 0.01,          // 微重力
  drag: 0.995,            // 阻力
  beamGravity: 0.008,     // 光束引力
}

const prism = { cx: 300, cy: 140, topX: 250, topY: 40, botX: 250, botY: 240, tipX: 330, tipY: 140 }

// 主题感知色（warm 主题下 brand 为玫红，不写死 indigo）
const brandRgb = hexToRgb(getBrandColor())
const purpleRgb = hexToRgb(PALETTE.purple)
const cyanRgb = hexToRgb(PALETTE.cyan)
const brandA = (a: number) => `rgba(${brandRgb.r},${brandRgb.g},${brandRgb.b},${a})`
const purpleA = (a: number) => `rgba(${purpleRgb.r},${purpleRgb.g},${purpleRgb.b},${a})`
const cyanA = (a: number) => `rgba(${cyanRgb.r},${cyanRgb.g},${cyanRgb.b},${a})`

function spawnInputParticle(): Particle {
  const y = 140 + (Math.random() - 0.5) * 40
  return {
    x: -5, y, vx: 2.2 + Math.random() * 0.6, vy: (Math.random() - 0.5) * 0.2,
    life: 0, maxLife: 220 + Math.random() * 80,
    size: 1.2 + Math.random() * 1.8, alpha: 0.5 + Math.random() * 0.5,
    color: '#ffffff', phase: 'input', beamIdx: -1,
    noiseOff: Math.random() * 1000,
  }
}

function spawnRefractParticle(beamIdx: number): Particle {
  const beam = props.beams[beamIdx]
  const angle = ((beamIdx - 1.5) / 3) * 0.4
  const speed = 1.8 + Math.random() * 0.6
  return {
    x: prism.tipX + 8, y: prism.cy + (Math.random() - 0.5) * 10,
    vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed + (beam.targetY - prism.cy) * 0.006,
    life: 0, maxLife: 200 + Math.random() * 100,
    size: 0.8 + Math.random() * 1.5, alpha: 0.4 + Math.random() * 0.6,
    color: beam.color, phase: 'refract', beamIdx,
    noiseOff: Math.random() * 1000,
  }
}

function updateParticle(p: Particle, s: number, w: number, h: number, t: number): boolean {
  p.life++
  if (p.life > p.maxLife) return false

  // 噪声扰动（有机运动）
  const nx = noise.noise3D(p.x * 0.008, p.y * 0.008, t * 0.003 + p.noiseOff) * FORCES.noiseStrength
  const ny = noise2.noise3D(p.x * 0.008, p.y * 0.008, t * 0.003 + p.noiseOff + 100) * FORCES.noiseStrength
  p.vx += nx * 0.1
  p.vy += ny * 0.1

  // 鼠标排斥
  if (mouse.active) {
    const dx = p.x - mouse.x
    const dy = p.y - mouse.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < FORCES.mouseRadius && dist > 0) {
      const force = (1 - dist / FORCES.mouseRadius) * FORCES.mouseStrength
      p.vx += (dx / dist) * force
      p.vy += (dy / dist) * force
    }
  }

  // 光束引力（折射粒子向目标Y偏移）
  if (p.phase === 'refract' && p.beamIdx >= 0) {
    const targetY = props.beams[p.beamIdx].targetY
    p.vy += (targetY - p.y) * FORCES.beamGravity * 0.1
  }

  // 微重力 + 阻力
  p.vy += FORCES.gravity
  p.vx *= FORCES.drag
  p.vy *= FORCES.drag

  p.x += p.vx
  p.y += p.vy

  // 边界检查
  if (p.phase === 'input' && p.x > prism.topX * s + 20 * s) return false
  if (p.x > w + 20 || p.y < -20 || p.y > h + 20) return false

  return true
}

function drawParticle(ctx: CanvasRenderingContext2D, p: Particle, s: number) {
  const fade = 1 - (p.life / p.maxLife)
  const fadeEase = fade * fade // 二次缓出
  const r = p.size * s
  const a = p.alpha * fadeEase

  // 核心光点
  const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 3)
  if (p.phase === 'input') {
    grad.addColorStop(0, `rgba(255,255,255,${a})`)
    grad.addColorStop(0.4, `rgba(200,210,255,${a * 0.5})`)
    grad.addColorStop(1, 'transparent')
  } else {
    // 从color解析rgb
    const c = hexToRgb(p.color)
    grad.addColorStop(0, `rgba(${c.r},${c.g},${c.b},${a})`)
    grad.addColorStop(0.4, `rgba(${c.r},${c.g},${c.b},${a * 0.4})`)
    grad.addColorStop(1, 'transparent')
  }
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.arc(p.x, p.y, r * 3, 0, Math.PI * 2)
  ctx.fill()

  // 高光核心
  ctx.fillStyle = `rgba(255,255,255,${a * 0.8})`
  ctx.beginPath()
  ctx.arc(p.x, p.y, r * 0.4, 0, Math.PI * 2)
  ctx.fill()
}

// ── 光束绘制 ──

function drawInputBeam(ctx: CanvasRenderingContext2D, w: number, h: number, t: number, s: number) {
  const startX = 20 * s
  const endX = prism.topX * s + 10 * s
  const cy = prism.cy * s

  // 光束主体（多层叠加）
  for (let layer = 0; layer < 3; layer++) {
    const width = (3 + layer * 4) * s
    const opacity = 0.3 - layer * 0.08
    const beamGrad = ctx.createLinearGradient(startX, cy, endX, cy)
    beamGrad.addColorStop(0, `rgba(255,255,255,${opacity * 0.1})`)
    beamGrad.addColorStop(0.5, `rgba(200,210,255,${opacity * 0.5})`)
    beamGrad.addColorStop(1, `rgba(255,255,255,${opacity})`)

    ctx.beginPath()
    ctx.moveTo(startX, cy)
    ctx.lineTo(endX, cy)
    ctx.strokeStyle = beamGrad
    ctx.lineWidth = width
    ctx.lineCap = 'round'
    ctx.stroke()
  }

  // 扫描光子脉冲
  const scanPhase = (t * 1.5) % (endX - startX)
  const scanX = startX + scanPhase
  const pulseR = 8 * s + Math.sin(t * 0.1) * 3 * s
  const pulseGrad = ctx.createRadialGradient(scanX, cy, 0, scanX, cy, pulseR)
  pulseGrad.addColorStop(0, 'rgba(255,255,255,0.6)')
  pulseGrad.addColorStop(0.3, 'rgba(200,220,255,0.2)')
  pulseGrad.addColorStop(1, 'transparent')
  ctx.fillStyle = pulseGrad
  ctx.beginPath()
  ctx.arc(scanX, cy, pulseR, 0, Math.PI * 2)
  ctx.fill()
}

function drawPrism(ctx: CanvasRenderingContext2D, s: number, t: number) {
  const cx = prism.cx * s, cy = prism.cy * s
  const tx = prism.topX * s, ty = prism.topY * s
  const bx = prism.botX * s, by = prism.botY * s
  const px = prism.tipX * s, py = prism.tipY * s

  // 外部光晕（脉冲）
  const pulse = 0.5 + Math.sin(t * 0.02) * 0.5
  const outerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, (80 + pulse * 20) * s)
  outerGlow.addColorStop(0, brandA(0.06))
  outerGlow.addColorStop(0.5, purpleA(0.03))
  outerGlow.addColorStop(1, 'transparent')
  ctx.fillStyle = outerGlow
  ctx.beginPath()
  ctx.arc(cx, cy, (80 + pulse * 20) * s, 0, Math.PI * 2)
  ctx.fill()

  // 棱镜主体
  ctx.beginPath()
  ctx.moveTo(tx, ty)
  ctx.lineTo(px, py)
  ctx.lineTo(bx, by)
  ctx.closePath()

  // 玻璃渐变
  const glassGrad = ctx.createLinearGradient(tx, ty, px, py)
  glassGrad.addColorStop(0, brandA(0.1))
  glassGrad.addColorStop(0.3, purpleA(0.06))
  glassGrad.addColorStop(0.6, cyanA(0.08))
  glassGrad.addColorStop(1, brandA(0.05))
  ctx.fillStyle = glassGrad
  ctx.fill()

  // 边框（双层）
  ctx.strokeStyle = brandA(0.5)
  ctx.lineWidth = 1.5 * s
  ctx.stroke()
  ctx.strokeStyle = brandA(0.15)
  ctx.lineWidth = 4 * s
  ctx.stroke()

  // 内部折射线（动态）
  for (let i = 0; i < 5; i++) {
    const phase = (t * 0.01 + i * 0.2) % 1
    const startX = tx + (px - tx) * phase * 0.8
    const startY = ty + (py - ty) * phase * 0.8
    const endX = bx + (px - bx) * phase * 0.6
    const endY = by + (py - by) * phase * 0.6
    ctx.beginPath()
    ctx.moveTo(startX, startY)
    ctx.lineTo(endX, endY)
    ctx.strokeStyle = brandA(0.05 + Math.sin(t * 0.03 + i) * 0.03)
    ctx.lineWidth = 0.5 * s
    ctx.stroke()
  }

  // 高光反射条
  const reflX = tx + 15 * s
  const reflY1 = ty + 25 * s
  const reflY2 = ty + 70 * s
  const reflGrad = ctx.createLinearGradient(reflX, reflY1, reflX, reflY2)
  reflGrad.addColorStop(0, 'rgba(255,255,255,0)')
  reflGrad.addColorStop(0.3, 'rgba(255,255,255,0.12)')
  reflGrad.addColorStop(0.7, 'rgba(255,255,255,0.08)')
  reflGrad.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.beginPath()
  ctx.moveTo(reflX, reflY1)
  ctx.lineTo(reflX + 3 * s, reflY2)
  ctx.strokeStyle = reflGrad
  ctx.lineWidth = 2.5 * s
  ctx.stroke()

  // 内部散射光斑
  for (let i = 0; i < 3; i++) {
    const fx = cx - 15 * s + Math.sin(t * 0.015 + i * 2) * 15 * s
    const fy = cy + Math.cos(t * 0.012 + i * 2.5) * 20 * s
    const fr = (4 + Math.sin(t * 0.02 + i) * 2) * s
    const fg = ctx.createRadialGradient(fx, fy, 0, fx, fy, fr)
    fg.addColorStop(0, 'rgba(255,255,255,0.08)')
    fg.addColorStop(1, 'transparent')
    ctx.fillStyle = fg
    ctx.beginPath()
    ctx.arc(fx, fy, fr, 0, Math.PI * 2)
    ctx.fill()
  }
}

function drawRefractBeams(ctx: CanvasRenderingContext2D, w: number, h: number, t: number, s: number) {
  const startX = prism.tipX * s + 8 * s
  const endXBase = w - 80 * s

  props.beams.forEach((beam, i) => {
    const targetY = beam.targetY * s
    const beamWidth = (1.5 + (beam.count / 100) * 2) * s
    const c = hexToRgb(beam.color)

    // 贝塞尔控制点（带噪声扰动）
    const cpX = startX + (endXBase - startX) * 0.5
    const cpY = (prism.cy * s + targetY) / 2 + Math.sin(t * 0.01 + i * 1.5) * 8 * s

    // 多层光束（辉光层+核心层）
    for (let layer = 0; layer < 3; layer++) {
      const lw = beamWidth * (1 + layer * 2.5)
      const la = [0.7, 0.2, 0.06][layer]

      ctx.beginPath()
      ctx.moveTo(startX, prism.cy * s)
      ctx.quadraticCurveTo(cpX, cpY, endXBase, targetY)

      const beamGrad = ctx.createLinearGradient(startX, prism.cy * s, endXBase, targetY)
      beamGrad.addColorStop(0, `rgba(${c.r},${c.g},${c.b},${la * 0.2})`)
      beamGrad.addColorStop(0.3, `rgba(${c.r},${c.g},${c.b},${la * 0.6})`)
      beamGrad.addColorStop(0.7, `rgba(${c.r},${c.g},${c.b},${la * 0.9})`)
      beamGrad.addColorStop(1, `rgba(${c.r},${c.g},${c.b},${la})`)

      ctx.strokeStyle = beamGrad
      ctx.lineWidth = lw
      ctx.lineCap = 'round'
      ctx.stroke()
    }

    // 终端脉冲环
    const pulse = 0.5 + Math.sin(t * 0.03 + i * 1.5) * 0.5
    const ringR = (6 + pulse * 5) * s
    ctx.beginPath()
    ctx.arc(endXBase, targetY, ringR, 0, Math.PI * 2)
    ctx.strokeStyle = beam.color + Math.round(40 + pulse * 30).toString(16).padStart(2, '0')
    ctx.lineWidth = 1 * s
    ctx.stroke()

    // 终端光点
    const dotGrad = ctx.createRadialGradient(endXBase, targetY, 0, endXBase, targetY, 5 * s)
    dotGrad.addColorStop(0, beam.color)
    dotGrad.addColorStop(0.5, beam.color + '80')
    dotGrad.addColorStop(1, 'transparent')
    ctx.fillStyle = dotGrad
    ctx.beginPath()
    ctx.arc(endXBase, targetY, 5 * s, 0, Math.PI * 2)
    ctx.fill()
  })
}

// ── 主渲染循环 ──

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

  ctx.clearRect(0, 0, w, h)
  time++

  const s = h / 280

  // 生成粒子
  if (Math.random() < 0.4) inputParticles.push(spawnInputParticle())
  props.beams.forEach((beam, i) => {
    if (Math.random() < 0.12 + beam.count / 600) beamParticles[i].push(spawnRefractParticle(i))
  })

  // 更新粒子
  inputParticles = inputParticles.filter(p => updateParticle(p, s, w, h, time))
  beamParticles.forEach(bp => {
    for (let i = bp.length - 1; i >= 0; i--) {
      if (!updateParticle(bp[i], s, w, h, time)) bp.splice(i, 1)
    }
  })

  // 绘制顺序：光束 → 棱镜 → 粒子（混合模式叠加）
  drawInputBeam(ctx, w, h, time, s)
  drawRefractBeams(ctx, w, h, time, s)
  drawPrism(ctx, s, time)

  // 粒子用additive blending
  ctx.globalCompositeOperation = 'lighter'
  inputParticles.forEach(p => drawParticle(ctx, p, s))
  beamParticles.forEach(bp => bp.forEach(p => drawParticle(ctx, p, s)))
  ctx.globalCompositeOperation = 'source-over'

  animId = requestAnimationFrame(draw)
}

// ── 工具函数 ──

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const m = hex.match(/^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i)
  return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : { r: 255, g: 255, b: 255 }
}

onMounted(() => { inputParticles = []; beamParticles = [[], [], [], []]; animId = requestAnimationFrame(draw) })
onUnmounted(() => cancelAnimationFrame(animId))
</script>

<style scoped>
.prism-wrap { overflow: hidden }
canvas { display: block }
</style>
