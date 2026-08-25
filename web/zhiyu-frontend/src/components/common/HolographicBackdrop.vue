<template>
  <div class="holo-backdrop absolute inset-0 pointer-events-none overflow-hidden" ref="containerRef" />
</template>

<script setup lang="ts">
/**
 * HolographicBackdrop — WebGL全息背景
 * GLSL fragment shader 实现：扫描线 + 噪声扰动 + Fresnel边缘发光 + 色差
 * 用法：<HolographicBackdrop /> 放在 panel-neon 内部
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { hexToVec3, getBrandColor } from '@/utils/color'

const props = withDefaults(defineProps<{
  color?: string       // 主色调 #rrggbb
  speed?: number       // 动画速度
  intensity?: number   // 效果强度 0-1
  scanLines?: boolean  // 扫描线
  noise?: boolean      // 噪声扰动
}>(), {
  color: () => getBrandColor('#6366f1'),
  speed: 1,
  intensity: 0.3,
  scanLines: true,
  noise: true,
})

const containerRef = ref<HTMLElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.OrthographicCamera | null = null
let material: THREE.ShaderMaterial | null = null
let geometry: THREE.PlaneGeometry | null = null
let animId = 0
let startTime = Date.now()

// GLSL Vertex Shader
const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

// GLSL Fragment Shader — 全息效果
const fragmentShader = `
precision highp float;

uniform float uTime;
uniform vec2 uResolution;
uniform vec3 uColor;
uniform float uSpeed;
uniform float uIntensity;
uniform float uScanLines;
uniform float uNoise;

varying vec2 vUv;

// Simplex noise 2D
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                     -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m; m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 uv = vUv;
  vec2 center = vec2(0.5);
  float t = uTime * uSpeed;

  // Fresnel 边缘发光
  float dist = length(uv - center);
  float fresnel = pow(1.0 - dist * 1.2, 2.0) * 0.3;
  float edgeGlow = pow(smoothstep(0.3, 0.7, dist), 3.0) * 0.4;

  // 扫描线
  float scan = 1.0;
  if (uScanLines > 0.5) {
    float scanLine = sin(uv.y * uResolution.y * 0.8 + t * 2.0) * 0.5 + 0.5;
    scan = mix(0.85, 1.0, scanLine);
    // 水平扫描带
    float scanBand = smoothstep(0.0, 0.02, abs(fract(uv.y - t * 0.05) - 0.5) - 0.48);
    scan *= mix(1.0, 1.3, 1.0 - scanBand);
  }

  // 噪声扰动
  float n = 0.0;
  if (uNoise > 0.5) {
    n = snoise(uv * 3.0 + t * 0.3) * 0.15;
    n += snoise(uv * 8.0 - t * 0.5) * 0.05;
  }

  // 色差（RGB偏移）
  float chromatic = 0.003 + edgeGlow * 0.005;
  vec3 colorShift = vec3(
    uColor.r + chromatic,
    uColor.g,
    uColor.b - chromatic
  );

  // 组合
  vec3 finalColor = colorShift * (fresnel + edgeGlow + n + 0.05) * scan;
  float alpha = (fresnel + edgeGlow * 0.5 + n * 0.3) * uIntensity;

  // 顶部和底部渐隐
  alpha *= smoothstep(0.0, 0.15, uv.y) * smoothstep(1.0, 0.85, uv.y);

  gl_FragColor = vec4(finalColor, alpha);
}
`

function toVec3(hex: string): THREE.Vector3 {
  return new THREE.Vector3(...hexToVec3(hex))
}

function init() {
  const el = containerRef.value
  if (!el) return

  const w = el.clientWidth || 300
  const h = el.clientHeight || 200

  // Renderer
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false })
  renderer.setSize(w, h)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  el.appendChild(renderer.domElement)
  renderer.domElement.style.position = 'absolute'
  renderer.domElement.style.inset = '0'

  // Scene + Camera
  scene = new THREE.Scene()
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)

  // Shader Material
  material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: new THREE.Vector2(w, h) },
      uColor: { value: toVec3(props.color) },
      uSpeed: { value: props.speed },
      uIntensity: { value: props.intensity },
      uScanLines: { value: props.scanLines ? 1.0 : 0.0 },
      uNoise: { value: props.noise ? 1.0 : 0.0 },
    },
    transparent: true,
    depthTest: false,
    blending: THREE.AdditiveBlending,
  })

  // Fullscreen quad
  geometry = new THREE.PlaneGeometry(2, 2)
  const mesh = new THREE.Mesh(geometry, material)
  scene.add(mesh)

  animate()
}

function animate() {
  if (!renderer || !scene || !camera || !material) return
  const elapsed = (Date.now() - startTime) / 1000
  material.uniforms.uTime.value = elapsed
  renderer.render(scene, camera)
  animId = requestAnimationFrame(animate)
}

function resize() {
  const el = containerRef.value
  if (!el || !renderer || !material) return
  const w = el.clientWidth
  const h = el.clientHeight
  renderer.setSize(w, h)
  material.uniforms.uResolution.value.set(w, h)
}

watch(() => props.color, (c) => { if (material) material.uniforms.uColor.value = toVec3(c) })
watch(() => props.intensity, (v) => { if (material) material.uniforms.uIntensity.value = v })
watch(() => props.speed, (v) => { if (material) material.uniforms.uSpeed.value = v })

onMounted(() => {
  init()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', resize)
  geometry?.dispose()
  material?.dispose()
  renderer?.dispose()
})
</script>

<style scoped>
.holo-backdrop {
  z-index: 0;
}
canvas {
  display: block;
}
</style>
