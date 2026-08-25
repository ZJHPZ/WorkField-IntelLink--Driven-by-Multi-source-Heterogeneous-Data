<template>
  <div class="cosmic-bg fixed inset-0 pointer-events-none z-0 overflow-hidden">
    <!-- 深空底色渐变 -->
    <div class="absolute inset-0" style="background: radial-gradient(ellipse at 30% 20%, #1a1040 0%, #0a0a18 40%, #050510 70%, #020208 100%);" />

    <!-- 星云光晕（color-mix 跟随主题品牌色） -->
    <div class="absolute inset-0 opacity-30"
      style="background:
        radial-gradient(ellipse 400px 300px at 20% 30%, color-mix(in srgb, var(--brand-500) 12%, transparent) 0%, transparent 60%),
        radial-gradient(ellipse 350px 280px at 70% 50%, color-mix(in srgb, var(--cyan-500) 10%, transparent) 0%, transparent 60%),
        radial-gradient(ellipse 300px 250px at 45% 75%, color-mix(in srgb, var(--purple-500) 8%, transparent) 0%, transparent 60%),
        radial-gradient(ellipse 250px 200px at 80% 20%, color-mix(in srgb, var(--mint-500) 6%, transparent) 0%, transparent 50%);
      " />

    <!-- 星空粒子层 -->
    <div class="absolute inset-0">
      <div v-for="star in stars" :key="star.id"
        class="absolute rounded-full"
        :class="star.twinkle ? 'animate-twinkle' : ''"
        :style="{
          width: star.size + 'px',
          height: star.size + 'px',
          top: star.top + '%',
          left: star.left + '%',
          backgroundColor: star.color,
          opacity: star.opacity,
          animationDelay: star.delay + 's',
          animationDuration: star.duration + 's',
          boxShadow: star.glow ? `0 0 ${star.glow}px ${star.color}` : 'none',
        }" />
    </div>

    <!-- 流动数据光线 -->
    <div class="absolute inset-0 opacity-[0.06]">
      <div class="absolute h-px w-full" style="top: 25%; background: linear-gradient(90deg, transparent, var(--brand-500), var(--cyan-500), var(--brand-500), transparent); background-size: 200% 100%; animation: dataFlowH 8s linear infinite;" />
      <div class="absolute h-px w-full" style="top: 55%; background: linear-gradient(90deg, transparent, var(--purple-500), var(--brand-500), var(--purple-500), transparent); background-size: 200% 100%; animation: dataFlowH 10s linear infinite reverse;" />
      <div class="absolute h-px w-full" style="top: 75%; background: linear-gradient(90deg, transparent, var(--cyan-500), var(--mint-500), var(--cyan-500), transparent); background-size: 200% 100%; animation: dataFlowH 12s linear infinite; animation-delay: -4s;" />
      <div class="absolute w-px h-full" style="left: 30%; background: linear-gradient(180deg, transparent, color-mix(in srgb, var(--brand-500) 50%, transparent), transparent); background-size: 100% 200%; animation: dataFlowV 9s linear infinite;" />
      <div class="absolute w-px h-full" style="left: 65%; background: linear-gradient(180deg, transparent, color-mix(in srgb, var(--cyan-500) 40%, transparent), transparent); background-size: 100% 200%; animation: dataFlowV 11s linear infinite reverse;" />
    </div>

    <!-- 大型光点: 缓慢漂移 -->
    <div class="absolute w-96 h-96 rounded-full blur-3xl opacity-[0.04]"
      style="top: 15%; left: 60%; background: var(--brand-500); animation: driftPlanet 20s ease-in-out infinite;" />
    <div class="absolute w-64 h-64 rounded-full blur-3xl opacity-[0.03]"
      style="top: 60%; left: 25%; background: var(--cyan-500); animation: driftPlanet 25s ease-in-out infinite reverse;" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 确定性星空（避免每次渲染闪烁）
const stars = computed(() =>
  Array.from({ length: 80 }, (_, i) => {
    const seed = i * 17 + (i % 11) * 3
    return {
      id: i,
      size: (i % 5 === 0) ? 1.8 : (i % 7 === 0) ? 1.2 : 0.6,
      top: (seed % 100),
      left: ((seed * 31 + (i % 13) * 7) % 100),
      color: i % 8 === 0 ? 'color-mix(in srgb, var(--brand-500) 70%, transparent)' :
             i % 9 === 0 ? 'color-mix(in srgb, var(--cyan-500) 60%, transparent)' :
             i % 11 === 0 ? 'color-mix(in srgb, var(--purple-500) 50%, transparent)' :
             'rgba(255,255,255,0.55)',
      opacity: 0.3 + (i % 10) * 0.06,
      twinkle: i % 4 !== 0,
      delay: ((i * 0.13) % 5),
      duration: 2 + (i % 5) * 0.7,
      glow: i % 5 === 0 ? 2 + (i % 3) : 0,
    }
  })
)
</script>

<style scoped>
@keyframes dataFlowH {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
@keyframes dataFlowV {
  0% { background-position: 50% 0%; }
  100% { background-position: 50% 200%; }
}
@keyframes driftPlanet {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(40px, -30px) scale(1.1); }
  50% { transform: translate(-20px, 20px) scale(0.9); }
  75% { transform: translate(-30px, -10px) scale(1.05); }
}
</style>
