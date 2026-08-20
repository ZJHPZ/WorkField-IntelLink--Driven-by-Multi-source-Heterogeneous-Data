import { ref, type Ref, onUnmounted } from 'vue'
import * as THREE from 'three'
import gsap from 'gsap'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import type { TopicMastery } from '@/stores/learning'

// ─── Types ───────────────────────────────────────────
export interface UniverseVertex {
  id: string
  index: number
  basePosition: THREE.Vector3
  solid: 'icosa' | 'dodeca'
  knowledgeNode?: TopicMastery
  mesh: THREE.Mesh
  glowMesh: THREE.Mesh
  ringMeshes: THREE.Mesh[]
  driftPhase: { x: number; y: number; z: number }
  driftSpeed: number
  driftAmp: number
}

interface StardustParticle {
  fromIdx: number
  toIdx: number
  progress: number
  speed: number
  mesh: THREE.Mesh
}

interface TrailEdge {
  key: string
  opacity: number
  line: THREE.Line
}

// ─── Constants ───────────────────────────────────────
const ICOSA_RADIUS = 1.5
const DODECA_RADIUS = 2.2
const LISSAJOUS_PERIODS = { x: 7, y: 11, z: 13 }
const BASE_ROTATION_SPEED = 0.25
const IDLE_TIMEOUT = 180_000 // 3 minutes
const EDGE_TARGET_RATIO = 0.25 // fraction of all possible pairs
const STARDUST_MAX = 40
const BLOOM_STRENGTH = 1.2
const BLOOM_RADIUS = 0.4
const BLOOM_THRESHOLD = 0.2

// ─── Mobile detection ──────────────────────────────
const isMobile = (() => {
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  const lowDpr = window.devicePixelRatio < 2
  const narrowViewport = window.innerWidth < 768
  return hasTouch && (lowDpr || narrowViewport)
})()

// Runtime config (adjusted for mobile)
const CFG = {
  bloomStrength: isMobile ? BLOOM_STRENGTH * 0.5 : BLOOM_STRENGTH,
  stardustMax: isMobile ? 15 : STARDUST_MAX,
  starCount: isMobile ? 100 : 300,
  petalCount: isMobile ? 4 : 6,
  idleBloomStrength: isMobile ? 0.15 : 0.3,
}

// ─── Vertex definitions ─────────────────────────────
const PHI = (1 + Math.sqrt(5)) / 2

function icosaVertices(r: number): THREE.Vector3[] {
  const raw = [
    [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
    [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
    [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1],
  ]
  return raw.map(v => new THREE.Vector3(v[0], v[1], v[2]).normalize().multiplyScalar(r))
}

function dodecaVertices(r: number): THREE.Vector3[] {
  const invPhi = 1 / PHI
  const raw = [
    [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1],
    [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1],
    [0, invPhi, PHI], [0, invPhi, -PHI], [0, -invPhi, PHI], [0, -invPhi, -PHI],
    [invPhi, PHI, 0], [invPhi, -PHI, 0], [-invPhi, PHI, 0], [-invPhi, -PHI, 0],
    [PHI, 0, invPhi], [PHI, 0, -invPhi], [-PHI, 0, invPhi], [-PHI, 0, -invPhi],
  ]
  return raw.map(v => new THREE.Vector3(v[0], v[1], v[2]).normalize().multiplyScalar(r))
}

export function useUniverse(
  canvasRef: Ref<HTMLCanvasElement | null>,
  options: {
    knowledgeNodes: Ref<TopicMastery[]>
    onNodeClick?: (node: TopicMastery) => void
    onNodeHover?: (node: TopicMastery | null) => void
  },
) {
  // ─── Reactive state ──────────────────────────────
  const isReady = ref(false)
  const selectedNode = ref<TopicMastery | null>(null)
  const hoveredNode = ref<TopicMastery | null>(null)
  const isIdle = ref(false)
  const isWakingUp = ref(false)
  // ─── Three.js internals ──────────────────────────
  let scene: THREE.Scene
  let camera: THREE.PerspectiveCamera
  let renderer: THREE.WebGLRenderer
  let composer: EffectComposer
  let bloomPass: UnrealBloomPass

  let icosaGroup: THREE.Group
  let dodecaGroup: THREE.Group
  let mainGroup: THREE.Group
  let edgeGroup: THREE.Group
  let stardustGroup: THREE.Group
  let bloomGroup: THREE.Group
  let quotesGroup: THREE.Group
  let quoteSprites: { sprite: THREE.Sprite; orbitParams: { axis: THREE.Vector3; speed: number; radiusX: number; radiusY: number; phase: number } }[] = []

  let vertices: UniverseVertex[] = []
  let activeEdges: [number, number][] = []
  let trailEdges: TrailEdge[] = []
  let stardustParticles: StardustParticle[] = []
  let backgroundStars: THREE.Points

  let raycaster: THREE.Raycaster
  let mouse = new THREE.Vector2()

  let animationId = 0
  let clock: THREE.Clock
  let lastInteraction = Date.now()
  let idleTimer: ReturnType<typeof setTimeout> | null = null
  let isDisposed = false

  // Track for edge trail effect
  let prevEdgeKeys = new Set<string>()

  // Camera system
  let cameraTarget = new THREE.Vector3(0, 0, 0)
  let cameraIdealPos = new THREE.Vector3(0, 0.8, 6.5)
  let cameraCruiseEnabled = true
  let cameraCruiseTime = 0
  const CAMERA_CRUISE_R = 6.5
  const CAMERA_CRUISE_THETA_PERIOD = 17
  const CAMERA_CRUISE_PHI_PERIOD = 23

  // ─── Init ────────────────────────────────────────
  function init() {
    if (!canvasRef.value) return

    clock = new THREE.Clock()

    // Renderer
    renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.2

    // Scene
    scene = new THREE.Scene()

    // Camera
    camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 50)
    camera.position.set(0, 0.8, 6.5)
    camera.lookAt(0, 0, 0)

    // Post-processing
    const renderPass = new RenderPass(scene, camera)
    bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      CFG.bloomStrength,
      BLOOM_RADIUS,
      BLOOM_THRESHOLD,
    )
    composer = new EffectComposer(renderer)
    composer.addPass(renderPass)
    composer.addPass(bloomPass)

    // Lights
    scene.add(new THREE.AmbientLight(0x1a1a3e, 0.6))
    const pointLight = new THREE.PointLight(0x6366f1, 80, 15)
    pointLight.position.set(0, 3, 4)
    scene.add(pointLight)
    const pointLight2 = new THREE.PointLight(0x06b6d4, 40, 12)
    pointLight2.position.set(-3, -1, 2)
    scene.add(pointLight2)

    // Groups
    mainGroup = new THREE.Group()
    icosaGroup = new THREE.Group()
    dodecaGroup = new THREE.Group()
    edgeGroup = new THREE.Group()
    stardustGroup = new THREE.Group()
    bloomGroup = new THREE.Group()
    quotesGroup = new THREE.Group()
    mainGroup.add(icosaGroup, dodecaGroup)
    scene.add(mainGroup, edgeGroup, stardustGroup, bloomGroup, quotesGroup)

    // Background stars
    createBackgroundStars()

    // Floating quotes
    createFloatingQuotes()

    // Geometry
    createGeometry()

    // Wireframes
    createWireframes()

    // Raycaster
    raycaster = new THREE.Raycaster()
    raycaster.params.Points.threshold = 0.3
    raycaster.params.Line = { threshold: 0.15 }

    // Events
    canvasRef.value.addEventListener('click', onCanvasClick)
    canvasRef.value.addEventListener('mousemove', onCanvasMove)
    canvasRef.value.addEventListener('pointerdown', () => { lastInteraction = Date.now() })
    window.addEventListener('resize', onResize)
    document.addEventListener('keydown', onKeyDown)

    // Idle timer
    resetIdleTimer()

    isReady.value = true
    animate()
  }

  // ─── Background stars ────────────────────────────
  function createBackgroundStars() {
    const count = CFG.starCount
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const r = 8 + Math.random() * 12
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = r * Math.cos(phi)
      const c = new THREE.Color().setHSL(0.55 + Math.random() * 0.2, 0.3, 0.5 + Math.random() * 0.5)
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    const mat = new THREE.PointsMaterial({ size: 0.03, vertexColors: true, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending, depthWrite: false })
    backgroundStars = new THREE.Points(geo, mat)
    scene.add(backgroundStars)
  }

  // ─── Floating quotes ────────────────────────────
  function createFloatingQuotes() {
    const quotes = [
      { text: '数据是新的石油', author: '— Clive Humby' },
      { text: 'The best way to learn\nis to teach', author: '— Frank Oppenheimer' },
      { text: '知识就是力量', author: '— 培根' },
    ]

    quotes.forEach((q, i) => {
      const canvas = document.createElement('canvas')
      canvas.width = 512; canvas.height = 128
      const ctx = canvas.getContext('2d')!

      // Translucent text
      ctx.fillStyle = '#ffffff'
      ctx.font = '28px "PingFang SC","Microsoft YaHei",sans-serif'
      ctx.textAlign = 'center'
      ctx.shadowColor = '#818cf8'
      ctx.shadowBlur = 8
      const lines = q.text.split('\n')
      lines.forEach((line, li) => {
        ctx.fillText(line, 256, 42 + li * 36)
      })
      ctx.shadowBlur = 0

      // Author smaller below
      ctx.fillStyle = '#ffffff88'
      ctx.font = '16px "PingFang SC","Microsoft YaHei",sans-serif'
      ctx.fillText(q.author, 256, 42 + lines.length * 36 + 22)

      const texture = new THREE.CanvasTexture(canvas)
      texture.minFilter = THREE.LinearFilter; texture.magFilter = THREE.LinearFilter
      const spriteMat = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity: 0.25,
        blending: THREE.NormalBlending,
        depthWrite: false,
      })
      const sprite = new THREE.Sprite(spriteMat)
      sprite.scale.set(3.5, 0.875, 1)

      // Elliptical orbit params
      const axis = new THREE.Vector3(
        Math.sin(i * 2.1) * 0.6,
        Math.cos(i * 2.1) * 0.8,
        Math.cos(i * 1.7) * 0.5,
      ).normalize()
      const orbitParams = {
        axis,
        speed: 0.15 + i * 0.06, // rad/s
        radiusX: 4.2 + i * 0.35,
        radiusY: 3.8 + i * 0.25,
        phase: i * (Math.PI * 2 / 3),
      }

      quoteSprites.push({ sprite, orbitParams })
      quotesGroup.add(sprite)
    })
  }

  // ─── Geometry creation ───────────────────────────
  function createGeometry() {
    const icoVerts = icosaVertices(ICOSA_RADIUS)
    const dodVerts = dodecaVertices(DODECA_RADIUS)

    const knowledgeNodes = options.knowledgeNodes.value

    function createVertexMesh(pos: THREE.Vector3, color: string, size: number, emissiveIntensity: number) {
      const geo = new THREE.SphereGeometry(size, 32, 32)
      const mat = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity,
        roughness: 0.3,
        metalness: 0.1,
      })
      return new THREE.Mesh(geo, mat)
    }

    function createGlowMesh(pos: THREE.Vector3, color: string, size: number) {
      const geo = new THREE.SphereGeometry(size * 1.8, 16, 16)
      const mat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.3,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
      return new THREE.Mesh(geo, mat)
    }

    const allBasePositions: THREE.Vector3[] = []
    const solids: Array<'icosa' | 'dodeca'> = []

    icoVerts.forEach(v => { allBasePositions.push(v.clone()); solids.push('icosa') })
    dodVerts.forEach(v => { allBasePositions.push(v.clone()); solids.push('dodeca') })

    vertices = allBasePositions.map((pos, i) => {
      const knowledgeNode = i < knowledgeNodes.length ? knowledgeNodes[i] : undefined
      const isDecorative = !knowledgeNode
      const solid = solids[i]

      const color = knowledgeNode
        ? nodeColor(knowledgeNode.status)
        : solid === 'icosa' ? '#4f46e5' : '#0891b2'

      const size = knowledgeNode
        ? (knowledgeNode.status === 'mastered' ? 0.07 : knowledgeNode.status === 'learning' ? 0.06 : 0.04)
        : 0.035

      const emissiveIntensity = knowledgeNode
        ? (knowledgeNode.status === 'mastered' ? 0.9 : knowledgeNode.status === 'learning' ? 0.6 : 0.1)
        : 0.15

      const mesh = createVertexMesh(pos, color, size, emissiveIntensity)
      const glowMesh = createGlowMesh(pos, color, size)

      mesh.userData = { vertexIndex: i, knowledgeNode }
      glowMesh.userData = { vertexIndex: i, isGlow: true }

      if (solid === 'icosa') icosaGroup.add(mesh, glowMesh)
      else dodecaGroup.add(mesh, glowMesh)

      return {
        id: knowledgeNode?.topicId || `decorative-${i}`,
        index: i,
        basePosition: pos.clone(),
        solid,
        knowledgeNode,
        mesh,
        glowMesh,
        ringMeshes: [],
        driftPhase: {
          x: Math.random() * Math.PI * 2,
          y: Math.random() * Math.PI * 2,
          z: Math.random() * Math.PI * 2,
        },
        driftSpeed: 0.5 + Math.random() * 0.8,
        driftAmp: 0.03 + Math.random() * 0.06,
      }
    })
  }

  // ─── Wireframes ───────────────────────────────────
  function createWireframes() {
    const icoGeo = new THREE.IcosahedronGeometry(ICOSA_RADIUS, 1)
    const icoWire = new THREE.LineSegments(
      new THREE.EdgesGeometry(icoGeo),
      new THREE.LineBasicMaterial({ color: 0x6366f1, transparent: true, opacity: 0.12, depthWrite: false }),
    )
    icosaGroup.add(icoWire)

    const dodGeo = new THREE.DodecahedronGeometry(DODECA_RADIUS, 0)
    const dodWire = new THREE.LineSegments(
      new THREE.EdgesGeometry(dodGeo),
      new THREE.LineBasicMaterial({ color: 0x06b6d4, transparent: true, opacity: 0.10, depthWrite: false }),
    )
    dodecaGroup.add(dodWire)
  }

  // ─── Edge computation ────────────────────────────
  function edgeKey(i: number, j: number): string {
    return Math.min(i, j) + '-' + Math.max(i, j)
  }

  function computeEdges(positions: THREE.Vector3[], time: number): [number, number][] {
    const totalPairs = (positions.length * (positions.length - 1)) / 2
    const targetCount = Math.floor(totalPairs * EDGE_TARGET_RATIO)

    const pairs: { i: number; j: number; dist: number }[] = []
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        pairs.push({ i, j, dist: positions[i].distanceTo(positions[j]) })
      }
    }
    pairs.sort((a, b) => a.dist - b.dist)

    // Dynamic threshold with slight oscillation
    const baseIdx = Math.floor(targetCount * (0.9 + Math.sin(time * 0.4) * 0.1))
    const threshold = pairs[Math.min(baseIdx, pairs.length - 1)].dist + Math.sin(time * 0.7) * 0.15

    return pairs.filter(p => p.dist <= threshold).map(p => [p.i, p.j] as [number, number])
  }

  // ─── Stardust ─────────────────────────────────────
  function spawnStardust(fromIdx: number, toIdx: number, fromPos: THREE.Vector3, toPos: THREE.Vector3) {
    const geo = new THREE.SphereGeometry(0.015, 8, 8)
    const mat = new THREE.MeshBasicMaterial({ color: 0xffffff, blending: THREE.AdditiveBlending, depthWrite: false })
    const mesh = new THREE.Mesh(geo, mat)
    stardustGroup.add(mesh)
    stardustParticles.push({
      fromIdx,
      toIdx,
      progress: 0,
      speed: 0.15 + Math.random() * 0.35,
      mesh,
    })
    mesh.position.copy(fromPos)
  }

  function updateStardust(vertexPositions: THREE.Vector3[], dt: number) {
    // Spawn new particles on random edges
    if (activeEdges.length > 0 && stardustParticles.length < CFG.stardustMax && Math.random() < 0.3) {
      const edge = activeEdges[Math.floor(Math.random() * activeEdges.length)]
      spawnStardust(edge[0], edge[1], vertexPositions[edge[0]], vertexPositions[edge[1]])
    }

    // Update existing particles
    for (let p = stardustParticles.length - 1; p >= 0; p--) {
      const particle = stardustParticles[p]
      particle.progress += particle.speed * dt

      if (particle.progress >= 1) {
        stardustGroup.remove(particle.mesh)
        particle.mesh.geometry.dispose()
        ;(particle.mesh.material as THREE.Material).dispose()
        stardustParticles.splice(p, 1)
        continue
      }

      // Check if edge still exists
      const ek = edgeKey(particle.fromIdx, particle.toIdx)
      const edgeExists = activeEdges.some(e => edgeKey(e[0], e[1]) === ek)
      if (!edgeExists) {
        stardustGroup.remove(particle.mesh)
        particle.mesh.geometry.dispose()
        ;(particle.mesh.material as THREE.Material).dispose()
        stardustParticles.splice(p, 1)
        continue
      }

      const from = vertexPositions[particle.fromIdx]
      const to = vertexPositions[particle.toIdx]
      particle.mesh.position.lerpVectors(from, to, particle.progress)
    }
  }

  // ─── Edge rendering ──────────────────────────────
  function updateEdgeLines(vertexPositions: THREE.Vector3[], newEdges: [number, number][]) {
    const newKeys = new Set(newEdges.map(e => edgeKey(e[0], e[1])))

    // Fade out removed edges → trail effect
    for (const trail of trailEdges) {
      if (!newKeys.has(trail.key)) {
        trail.opacity -= 0.05
        if (trail.opacity <= 0) {
          edgeGroup.remove(trail.line)
          trail.line.geometry.dispose()
          ;(trail.line.material as THREE.Material).dispose()
        } else {
          ;(trail.line.material as THREE.LineBasicMaterial).opacity = trail.opacity * 0.4
        }
      }
    }
    trailEdges = trailEdges.filter(t => t.opacity > 0)

    // Update or create edges
    for (const [i, j] of newEdges) {
      const key = edgeKey(i, j)
      const existing = trailEdges.find(t => t.key === key)
      if (existing) {
        existing.opacity = Math.min(existing.opacity + 0.1, 1)
        ;(existing.line.material as THREE.LineBasicMaterial).opacity = existing.opacity * 0.4
        const positions = existing.line.geometry.attributes.position as THREE.BufferAttribute
        const posI = vertexPositions[i]
        const posJ = vertexPositions[j]
        positions.setXYZ(0, posI.x, posI.y, posI.z)
        positions.setXYZ(1, posJ.x, posJ.y, posJ.z)
        positions.needsUpdate = true
      } else {
        const geo = new THREE.BufferGeometry()
        const posI = vertexPositions[i]
        const posJ = vertexPositions[j]
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
          posI.x, posI.y, posI.z, posJ.x, posJ.y, posJ.z,
        ]), 3))
        const mat = new THREE.LineBasicMaterial({
          color: 0x818cf8,
          transparent: true,
          opacity: 0.4,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        })
        const line = new THREE.Line(geo, mat)
        edgeGroup.add(line)
        trailEdges.push({ key, opacity: 1, line })
      }
    }

    // New disappearing edges
    for (const key of prevEdgeKeys) {
      if (!newKeys.has(key) && !trailEdges.some(t => t.key === key)) {
        const [i, j] = key.split('-').map(Number)
        const geo = new THREE.BufferGeometry()
        const posI = vertexPositions[i]
        const posJ = vertexPositions[j]
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
          posI.x, posI.y, posI.z, posJ.x, posJ.y, posJ.z,
        ]), 3))
        const mat = new THREE.LineBasicMaterial({
          color: 0xa78bfa,
          transparent: true,
          opacity: 0.5,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        })
        const line = new THREE.Line(geo, mat)
        edgeGroup.add(line)
        trailEdges.push({ key, opacity: 0.7, line })
      }
    }

    prevEdgeKeys = newKeys
    activeEdges = newEdges
  }

  // ─── Node color helpers ──────────────────────────
  function nodeColor(status: string): string {
    switch (status) {
      case 'mastered': return '#fbbf24'
      case 'learning': return '#6366f1'
      default: return '#475569'
    }
  }

  // ─── Animation loop ──────────────────────────────
  function animate() {
    if (isDisposed) return
    animationId = requestAnimationFrame(animate)

    const dt = Math.min(clock.getDelta(), 0.1)
    const time = clock.elapsedTime

    // Lissajous rotation
    const rotX = Math.sin(time * BASE_ROTATION_SPEED * (2 * Math.PI / LISSAJOUS_PERIODS.x))
    const rotY = Math.sin(time * BASE_ROTATION_SPEED * (2 * Math.PI / LISSAJOUS_PERIODS.y))
    const rotZ = Math.sin(time * BASE_ROTATION_SPEED * (2 * Math.PI / LISSAJOUS_PERIODS.z))

    // During idle, slow way down; during wake, lerp toward normal
    const speedMult = isIdle.value ? (isWakingUp.value ? wakeSpeedMult : 0.08) : 1.0

    icosaGroup.rotation.set(rotX * speedMult, rotY * speedMult, rotZ * speedMult)
    dodecaGroup.rotation.set(-rotY * speedMult * 0.7, rotZ * speedMult * 0.8, -rotX * speedMult * 0.6)

    // Compute current world positions of all vertices
    const vertexWorldPositions = vertices.map(v => {
      const local = v.basePosition.clone()
      // Apply drift
      local.x += Math.sin(time * v.driftSpeed + v.driftPhase.x) * v.driftAmp
      local.y += Math.cos(time * v.driftSpeed * 1.3 + v.driftPhase.y) * v.driftAmp
      local.z += Math.sin(time * v.driftSpeed * 0.7 + v.driftPhase.z) * v.driftAmp
      // Transform to world
      const group = v.solid === 'icosa' ? icosaGroup : dodecaGroup
      const world = local.clone()
      group.localToWorld(world)
      // Transform back to mainGroup local space (edges and stardust are in world)
      mainGroup.worldToLocal(world)
      return world
    })

    // Update vertex mesh positions
    vertices.forEach((v, i) => {
      const pos = vertexWorldPositions[i]
      v.mesh.position.copy(pos)
      v.glowMesh.position.copy(pos)

      // Dynamic glow based on state
      if (v.knowledgeNode) {
        updateNodeGlow(v, time)
      }
    })

    // Compute and update edges
    const newEdges = computeEdges(vertexWorldPositions, time)
    updateEdgeLines(vertexWorldPositions, newEdges)

    // Update stardust
    updateStardust(vertexWorldPositions, dt)

    // Camera cruise
    cameraCruiseTime += dt
    if (cameraCruiseEnabled) {
      const theta = Math.sin(cameraCruiseTime * (2 * Math.PI / CAMERA_CRUISE_THETA_PERIOD)) * 0.45
      const phi = Math.sin(cameraCruiseTime * (2 * Math.PI / CAMERA_CRUISE_PHI_PERIOD)) * 0.3 + 0.45
      cameraIdealPos.set(
        CAMERA_CRUISE_R * Math.sin(phi) * Math.cos(theta),
        CAMERA_CRUISE_R * Math.cos(phi) * 0.5 + 0.6,
        CAMERA_CRUISE_R * Math.cos(phi) * Math.sin(theta) + 1.5,
      )
    }
    camera.position.lerp(cameraIdealPos, 0.03)
    camera.lookAt(cameraTarget)

    // Update floating quotes
    const quotesTargetOpacity = isIdle.value ? 0.0 : 0.25
    quoteSprites.forEach(q => {
      const angle = time * q.orbitParams.speed + q.orbitParams.phase
      // Elliptical orbit via Rodrigues rotation around axis
      const basePos = new THREE.Vector3(
        Math.cos(angle) * q.orbitParams.radiusX,
        Math.sin(angle) * q.orbitParams.radiusY,
        0,
      )
      // Rotate around orbit axis
      const axis = q.orbitParams.axis
      const cosA = Math.cos(angle * 0.3)
      const sinA = Math.sin(angle * 0.3)
      const rotated = basePos.clone()
        .applyAxisAngle(axis, angle * 0.4)
      q.sprite.position.copy(rotated)

      // Opacity oscillation + idle fade
      const osc = 0.15 + Math.sin(time * 0.7 + q.orbitParams.phase) * 0.1
      const target = isIdle.value ? 0.0 : osc
      const mat = q.sprite.material as THREE.SpriteMaterial
      mat.opacity += (target - mat.opacity) * 0.03
    })

    // Background stars subtle rotation
    backgroundStars.rotation.y += dt * 0.015
    backgroundStars.rotation.x += dt * 0.008

    // Render
    composer.render()
  }

  function updateNodeGlow(v: UniverseVertex, time: number) {
    if (!v.knowledgeNode) return
    const status = v.knowledgeNode.status
    const glowMat = v.glowMesh.material as THREE.MeshBasicMaterial
    const meshMat = v.mesh.material as THREE.MeshStandardMaterial

    switch (status) {
      case 'mastered': {
        // Breathing glow, 4s period
        const breathe = 0.7 + Math.sin(time * Math.PI / 2) * 0.3
        glowMat.opacity = 0.25 * breathe + 0.15
        meshMat.emissiveIntensity = 0.7 * breathe + 0.3
        break
      }
      case 'learning': {
        // Heartbeat: two quick pulses then pause
        const t = time % 2.5
        const pulse = t < 0.15 ? Math.sin(t / 0.15 * Math.PI) :
          t < 0.45 && t > 0.3 ? Math.sin((t - 0.3) / 0.15 * Math.PI) : 0
        glowMat.opacity = 0.15 + pulse * 0.3
        meshMat.emissiveIntensity = 0.4 + pulse * 0.5
        break
      }
      default: {
        // Locked: barely visible, subtle specular only
        glowMat.opacity = 0.05 + Math.sin(time * 0.3) * 0.02
        meshMat.emissiveIntensity = 0.05
      }
    }
  }

  // ─── Interaction ──────────────────────────────────
  function getIntersections(event: MouseEvent): THREE.Intersection[] {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1
    raycaster.setFromCamera(mouse, camera)
    const meshes = vertices.map(v => v.mesh)
    return raycaster.intersectObjects(meshes)
  }

  function onCanvasClick(event: MouseEvent) {
    lastInteraction = Date.now()
    if (isIdle.value) { triggerWakeUp(); return }

    const intersects = getIntersections(event)
    if (intersects.length > 0) {
      const obj = intersects[0].object as THREE.Mesh
      const idx = obj.userData.vertexIndex as number
      const vertex = vertices[idx]
      if (vertex?.knowledgeNode) {
        selectedNode.value = vertex.knowledgeNode
        options.onNodeClick?.(vertex.knowledgeNode)
        focusCameraOnNode(idx)
      }
    } else {
      selectedNode.value = null
      returnCameraToCruise()
      options.onNodeClick?.(null as any)
    }
  }

  function onCanvasMove(event: MouseEvent) {
    if (isIdle.value) return
    lastInteraction = Date.now()
    resetIdleTimer()

    const intersects = getIntersections(event)
    if (intersects.length > 0) {
      const obj = intersects[0].object as THREE.Mesh
      const idx = obj.userData.vertexIndex as number
      const vertex = vertices[idx]
      if (vertex?.knowledgeNode) {
        hoveredNode.value = vertex.knowledgeNode
        options.onNodeHover?.(vertex.knowledgeNode)
        document.body.style.cursor = 'pointer'
        return
      }
    }
    hoveredNode.value = null
    options.onNodeHover?.(null)
    document.body.style.cursor = ''
  }

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      selectedNode.value = null
      returnCameraToCruise()
    }
  }

  // ─── Idle / Wake ─────────────────────────────────
  function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer)
    if (isIdle.value && !isWakingUp.value) return // already idle
    idleTimer = setTimeout(() => {
      if (Date.now() - lastInteraction >= IDLE_TIMEOUT) {
        enterIdle()
      }
    }, IDLE_TIMEOUT)
  }

  function enterIdle() {
    isIdle.value = true
    // Reduce bloom + stars for the "sketch mode" feel
    bloomPass.strength = CFG.idleBloomStrength
    ;(backgroundStars.material as THREE.PointsMaterial).opacity = 0.15
  }

  let wakeSpeedMult = 1.0 // lerped toward target, 1.0 = normal speed

  function triggerWakeUp() {
    if (!isIdle.value || isWakingUp.value) return
    isWakingUp.value = true

    // Build adjacency list from active edges
    const adjList = new Map<number, number[]>()
    for (const [i, j] of activeEdges) {
      if (!adjList.has(i)) adjList.set(i, [])
      if (!adjList.has(j)) adjList.set(j, [])
      adjList.get(i)!.push(j)
      adjList.get(j)!.push(i)
    }

    // Find most central node (highest degree)
    let centerIdx = 0, maxDeg = 0
    for (const [idx, neighbors] of adjList) {
      if (neighbors.length > maxDeg) { maxDeg = neighbors.length; centerIdx = idx }
    }

    // BFS to get vertex levels
    const vertexLevels = new Map<number, number>()
    const visited = new Set<number>([centerIdx])
    const queue: number[] = [centerIdx]
    vertexLevels.set(centerIdx, 0)
    while (queue.length > 0) {
      const cur = queue.shift()!
      const level = vertexLevels.get(cur)!
      for (const neighbor of (adjList.get(cur) || [])) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor)
          vertexLevels.set(neighbor, level + 1)
          queue.push(neighbor)
        }
      }
    }
    const maxLevel = Math.max(...vertexLevels.values(), 1)

    // Assign edge levels (min level of its two vertices)
    const edgeLevels = new Map<string, number>()
    for (const [i, j] of activeEdges) {
      const li = vertexLevels.get(i) ?? maxLevel
      const lj = vertexLevels.get(j) ?? maxLevel
      edgeLevels.set(edgeKey(i, j), Math.min(li, lj))
    }

    // Build GSAP timeline
    const tl = gsap.timeline({
      onComplete: () => {
        bloomPass.strength = CFG.bloomStrength
        isIdle.value = false
        isWakingUp.value = false
        wakeSpeedMult = 1.0
        resetIdleTimer()
      },
    })

    // Phase 1 (0–0.3s): All vertex meshes glow up
    vertices.forEach(v => {
      const mat = v.mesh.material as THREE.MeshStandardMaterial
      const targetEmissive = v.knowledgeNode
        ? (v.knowledgeNode.status === 'mastered' ? 0.9 : v.knowledgeNode.status === 'learning' ? 0.6 : 0.1)
        : 0.15
      tl.to(mat, { emissiveIntensity: targetEmissive, duration: 0.3, ease: 'power2.out' }, 0)
    })

    // Phase 2 (0.3–0.8s): Edge ignition by BFS level
    const edgeEntries: { key: string; level: number; line: THREE.Line }[] = []
    for (const trail of trailEdges) {
      const level = edgeLevels.get(trail.key) ?? maxLevel
      if (trail.opacity > 0.3) {
        edgeEntries.push({ key: trail.key, level, line: trail.line })
      }
    }
    edgeEntries.sort((a, b) => a.level - b.level)

    edgeEntries.forEach(e => {
      const mat = e.line.material as THREE.LineBasicMaterial
      const startDelay = 0.3 + (e.level / Math.max(maxLevel, 1)) * 0.5
      // Flash: opacity boost then settle
      tl.to(mat, { opacity: 0.9, duration: 0.08, ease: 'power1.out' }, startDelay)
      tl.to(mat, { opacity: 0.4, duration: 0.4, ease: 'power2.out' }, startDelay + 0.08)
    })

    // Phase 3 (0.8–1.5s): Rotation speed ramp
    wakeSpeedMult = 0.08
    tl.to({ val: 0.08 }, {
      val: 1.0, duration: 0.7, ease: 'expo.out',
      onUpdate(this: any) { wakeSpeedMult = this.targets()[0].val },
    }, 0.8)

    // Phase 4 (1.5–2.0s): Bloom + background stars restore
    tl.to(backgroundStars.material, { opacity: 0.7, duration: 0.5, ease: 'power2.out' }, 1.5)
    tl.to(bloomPass, { strength: CFG.bloomStrength, duration: 0.5, ease: 'power2.out' }, 1.5)
  }

  // ─── Resize ───────────────────────────────────────
  function onResize() {
    if (!renderer) return
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
    composer.setSize(window.innerWidth, window.innerHeight)
  }

  // ─── Bloom System ──────────────────────────────────
  function getVertexWorldPos(idx: number): THREE.Vector3 {
    const v = vertices[idx]
    const local = v.basePosition.clone()
    const group = v.solid === 'icosa' ? icosaGroup : dodecaGroup
    const world = local.clone()
    group.localToWorld(world)
    return world
  }

  function focusCameraOnNode(idx: number) {
    cameraCruiseEnabled = false
    const worldPos = getVertexWorldPos(idx)
    const dir = worldPos.clone().normalize()
    const targetPos = worldPos.clone().add(dir.multiplyScalar(2.0))
    gsap.to(cameraIdealPos, {
      x: targetPos.x, y: targetPos.y, z: targetPos.z,
      duration: 0.8, ease: 'power2.inOut', overwrite: 'auto',
    })
    gsap.to(cameraTarget, {
      x: worldPos.x, y: worldPos.y, z: worldPos.z,
      duration: 0.8, ease: 'power2.inOut', overwrite: 'auto',
    })
  }

  function returnCameraToCruise() {
    cameraCruiseEnabled = true
    cameraCruiseTime = 0 // reset phase so it starts from a nice angle
    gsap.to(cameraTarget, {
      x: 0, y: 0, z: 0, duration: 1.0, ease: 'power2.inOut', overwrite: 'auto',
    })
  }

  // ─── Public: focus on node ───────────────────────
  function focusNode(topicId: string) {
    const vertex = vertices.find(v => v.knowledgeNode?.topicId === topicId)
    if (!vertex) return
    selectedNode.value = vertex.knowledgeNode!
    focusCameraOnNode(vertex.index)
  }

  // ─── Public: learning progress micro-feedback ─────
  function notifyProgress(topicId: string, oldMastery: number, newMastery: number) {
    const vertex = vertices.find(v => v.knowledgeNode?.topicId === topicId)
    if (!vertex?.knowledgeNode) return

    const node = vertex.knowledgeNode
    const newStatus = newMastery >= 0.85 ? 'mastered' : newMastery > 0 ? 'learning' : 'locked'
    const oldStatus = oldMastery >= 0.85 ? 'mastered' : oldMastery > 0 ? 'learning' : 'locked'

    // Update node data
    node.masteryLevel = newMastery
    node.status = newStatus

    // Update visual appearance (color + emissive)
    const color = nodeColor(newStatus)
    const meshMat = vertex.mesh.material as THREE.MeshStandardMaterial
    const glowMat = vertex.glowMesh.material as THREE.MeshBasicMaterial
    meshMat.color.set(color)
    meshMat.emissive.set(color)
    glowMat.color.set(color)

    // Always: scale bounce
    gsap.killTweensOf(vertex.mesh.scale)
    gsap.killTweensOf(vertex.glowMesh.scale)
    gsap.to(vertex.mesh.scale, { x: 1.25, y: 1.25, z: 1.25, duration: 0.35, ease: 'back.out(2)' })
    gsap.to(vertex.mesh.scale, { x: 1.0, y: 1.0, z: 1.0, duration: 0.55, delay: 0.35, ease: 'elastic.out(1, 0.4)' })
    gsap.to(vertex.glowMesh.scale, { x: 1.5, y: 1.5, z: 1.5, duration: 0.35, ease: 'back.out(2)' })
    gsap.to(vertex.glowMesh.scale, { x: 1.0, y: 1.0, z: 1.0, duration: 0.55, delay: 0.35, ease: 'elastic.out(1, 0.4)' })

    // Cross-threshold: mini bloom
    if (oldStatus !== newStatus) {
      if (newStatus === 'mastered') {
        // Golden particle burst + glow expand
        triggerMiniBloom(vertex.index, '#fbbf24', 14)
        gsap.to(glowMat, { opacity: 0.6, duration: 0.4, yoyo: true, repeat: 1, ease: 'power2.inOut' })
        gsap.to(meshMat, { emissiveIntensity: 1.2, duration: 0.4, yoyo: true, repeat: 1, ease: 'power2.inOut' })
      } else if (newStatus === 'learning' && oldStatus === 'locked') {
        // Blue unlock pulse
        triggerMiniBloom(vertex.index, '#6366f1', 8)
        const ringGeo = new THREE.RingGeometry(0.06, 0.1, 32)
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0x6366f1, transparent: true, opacity: 0.8,
          side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false,
        })
        const ring = new THREE.Mesh(ringGeo, ringMat)
        const worldPos = getVertexWorldPos(vertex.index)
        ring.position.copy(worldPos)
        ring.lookAt(new THREE.Vector3(0, 0, 0))
        bloomGroup.add(ring)
        gsap.to(ring.scale, { x: 5, y: 5, z: 5, duration: 0.8, ease: 'power2.out' })
        gsap.to(ringMat, { opacity: 0, duration: 0.7, ease: 'power2.in' })
        gsap.to(ring.scale, {
          x: 0, y: 0, z: 0, duration: 0, delay: 0.9,
          onComplete: () => { bloomGroup.remove(ring); ringGeo.dispose(); ringMat.dispose() },
        })
      }
    }
  }

  function triggerMiniBloom(vertexIndex: number, colorHex: string, particleCount: number) {
    const worldPos = getVertexWorldPos(vertexIndex)
    for (let i = 0; i < particleCount; i++) {
      const geo = new THREE.SphereGeometry(0.015, 6, 6)
      const mat = new THREE.MeshBasicMaterial({
        color: colorHex, blending: THREE.AdditiveBlending,
        transparent: true, opacity: 0.9, depthWrite: false,
      })
      const particle = new THREE.Mesh(geo, mat)
      particle.position.copy(worldPos)
      const dir = new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 2,
      ).normalize()
      const speed = 0.4 + Math.random() * 0.8
      bloomGroup.add(particle)

      gsap.to(particle.position, {
        x: worldPos.x + dir.x * speed,
        y: worldPos.y + dir.y * speed,
        z: worldPos.z + dir.z * speed,
        duration: 0.8 + Math.random() * 0.4, ease: 'power2.out',
      })
      gsap.to(mat, { opacity: 0, duration: 0.7, delay: 0.2 + Math.random() * 0.3, ease: 'power2.in' })
      gsap.to(particle.scale, { x: 0.01, y: 0.01, z: 0.01, duration: 1.0, delay: 0.3,
        onComplete: () => { bloomGroup.remove(particle); geo.dispose(); mat.dispose() },
      })
    }
  }

  // ─── Cleanup ─────────────────────────────────────
  function dispose() {
    isDisposed = true
    if (animationId) cancelAnimationFrame(animationId)
    if (idleTimer) clearTimeout(idleTimer)
    if (canvasRef.value) {
      canvasRef.value.removeEventListener('click', onCanvasClick)
      canvasRef.value.removeEventListener('mousemove', onCanvasMove)
    }
    window.removeEventListener('resize', onResize)
    document.removeEventListener('keydown', onKeyDown)

    // Clean up scene objects
    scene?.traverse((obj) => {
      if (obj instanceof THREE.Mesh || obj instanceof THREE.Line || obj instanceof THREE.Points) {
        obj.geometry?.dispose()
        const materials = Array.isArray(obj.material) ? obj.material : [obj.material]
        materials.forEach(m => m?.dispose())
      }
    })

    // Clean bloom pass render targets
    if (bloomPass) {
      bloomPass.renderTargetBright?.dispose?.()
      bloomPass.renderTargetsHorizontal?.forEach?.((rt: THREE.WebGLRenderTarget) => rt?.dispose?.())
      bloomPass.renderTargetsVertical?.forEach?.((rt: THREE.WebGLRenderTarget) => rt?.dispose?.())
    }

    renderer?.dispose()
  }

  onUnmounted(dispose)

  return {
    isReady,
    selectedNode,
    hoveredNode,
    isIdle,
    isWakingUp,
    init,
    focusNode,
    notifyProgress,
    dispose,
  }
}
