/**
 * Simplex Noise 2D/3D — 紧凑实现，用于粒子有机运动
 * 基于 Stefan Gustavson 的 SimplexNoise 算法
 */

const F2 = 0.5 * (Math.sqrt(3) - 1)
const G2 = (3 - Math.sqrt(3)) / 6
const F3 = 1 / 3
const G3 = 1 / 6

const grad3 = [
  [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
  [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
  [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
]

export class SimplexNoise {
  private perm: Uint8Array
  private permMod12: Uint8Array

  constructor(seed = 0) {
    const p = new Uint8Array(256)
    for (let i = 0; i < 256; i++) p[i] = i
    // Fisher-Yates shuffle with seed
    let s = seed
    for (let i = 255; i > 0; i--) {
      s = (s * 16807 + 0) % 2147483647
      const j = s % (i + 1)
      const tmp = p[i]; p[i] = p[j]; p[j] = tmp
    }
    this.perm = new Uint8Array(512)
    this.permMod12 = new Uint8Array(512)
    for (let i = 0; i < 512; i++) {
      this.perm[i] = p[i & 255]
      this.permMod12[i] = this.perm[i] % 12
    }
  }

  noise2D(xin: number, yin: number): number {
    const { perm, permMod12 } = this
    const s = (xin + yin) * F2
    const i = Math.floor(xin + s)
    const j = Math.floor(yin + s)
    const t = (i + j) * G2
    const x0 = xin - (i - t)
    const y0 = yin - (j - t)

    const i1 = x0 > y0 ? 1 : 0
    const j1 = x0 > y0 ? 0 : 1

    const x1 = x0 - i1 + G2
    const y1 = y0 - j1 + G2
    const x2 = x0 - 1 + 2 * G2
    const y2 = y0 - 1 + 2 * G2

    const ii = i & 255
    const jj = j & 255

    let n0 = 0, n1 = 0, n2 = 0

    let t0 = 0.5 - x0 * x0 - y0 * y0
    if (t0 >= 0) {
      t0 *= t0
      const gi0 = permMod12[ii + perm[jj]]
      n0 = t0 * t0 * (grad3[gi0][0] * x0 + grad3[gi0][1] * y0)
    }

    let t1 = 0.5 - x1 * x1 - y1 * y1
    if (t1 >= 0) {
      t1 *= t1
      const gi1 = permMod12[ii + i1 + perm[jj + j1]]
      n1 = t1 * t1 * (grad3[gi1][0] * x1 + grad3[gi1][1] * y1)
    }

    let t2 = 0.5 - x2 * x2 - y2 * y2
    if (t2 >= 0) {
      t2 *= t2
      const gi2 = permMod12[ii + 1 + perm[jj + 1]]
      n2 = t2 * t2 * (grad3[gi2][0] * x2 + grad3[gi2][1] * y2)
    }

    return 70 * (n0 + n1 + n2)
  }

  noise3D(xin: number, yin: number, zin: number): number {
    const { perm, permMod12 } = this
    const s = (xin + yin + zin) * F3
    const i = Math.floor(xin + s)
    const j = Math.floor(yin + s)
    const k = Math.floor(zin + s)
    const t = (i + j + k) * G3
    const x0 = xin - (i - t)
    const y0 = yin - (j - t)
    const z0 = zin - (k - t)

    const i1 = x0 >= y0 ? (y0 >= z0 ? 1 : x0 >= z0 ? 1 : 0) : (y0 < z0 ? 0 : x0 < z0 ? 0 : 1)
    const j1 = x0 >= y0 ? (y0 >= z0 ? 0 : x0 >= z0 ? 0 : 1) : (y0 < z0 ? 1 : x0 >= z0 ? 1 : 0)
    const k1 = x0 >= y0 ? (y0 >= z0 ? 0 : x0 >= z0 ? 0 : 1) : (y0 < z0 ? 0 : x0 >= z0 ? 0 : 1)

    const x1 = x0 - i1 + G3, y1 = y0 - j1 + G3, z1 = z0 - k1 + G3
    const x2 = x0 - 2 * G3, y2 = y0 - 2 * G3, z2 = z0 - 2 * G3
    const x3 = x0 - 1 + 3 * G3, y3 = y0 - 1 + 3 * G3, z3 = z0 - 1 + 3 * G3

    const ii = i & 255, jj = j & 255, kk = k & 255
    let n0 = 0, n1 = 0, n2 = 0, n3 = 0

    let t0 = 0.6 - x0 * x0 - y0 * y0 - z0 * z0
    if (t0 >= 0) { t0 *= t0; const gi = permMod12[ii + perm[jj + perm[kk]]]; n0 = t0 * t0 * (grad3[gi][0] * x0 + grad3[gi][1] * y0 + grad3[gi][2] * z0) }
    let t1 = 0.6 - x1 * x1 - y1 * y1 - z1 * z1
    if (t1 >= 0) { t1 *= t1; const gi = permMod12[ii + i1 + perm[jj + j1 + perm[kk + k1]]]; n1 = t1 * t1 * (grad3[gi][0] * x1 + grad3[gi][1] * y1 + grad3[gi][2] * z1) }
    let t2 = 0.6 - x2 * x2 - y2 * y2 - z2 * z2
    if (t2 >= 0) { t2 *= t2; const gi = permMod12[ii + 1 + perm[jj + 1 + perm[kk + 1]]]; n2 = t2 * t2 * (grad3[gi][0] * x2 + grad3[gi][1] * y2 + grad3[gi][2] * z2) }
    let t3 = 0.6 - x3 * x3 - y3 * y3 - z3 * z3
    if (t3 >= 0) { t3 *= t3; const gi = permMod12[ii + 1 + perm[jj + 1 + perm[kk + 1]]]; n3 = t3 * t3 * (grad3[gi][0] * x3 + grad3[gi][1] * y3 + grad3[gi][2] * z3) }

    return 32 * (n0 + n1 + n2 + n3)
  }
}

/**
 * Fractal Brownian Motion — 叠加多层噪声产生更丰富的细节
 */
export function fbm(noise: SimplexNoise, x: number, y: number, octaves = 4, lacunarity = 2, gain = 0.5): number {
  let sum = 0, amp = 1, freq = 1, max = 0
  for (let i = 0; i < octaves; i++) {
    sum += noise.noise2D(x * freq, y * freq) * amp
    max += amp
    amp *= gain
    freq *= lacunarity
  }
  return sum / max
}
