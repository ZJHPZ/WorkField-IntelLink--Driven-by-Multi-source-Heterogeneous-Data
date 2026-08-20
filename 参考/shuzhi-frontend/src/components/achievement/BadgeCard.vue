<template>
  <div
    class="relative rounded-2xl border-2 p-4 text-center transition-all duration-300 group"
    :class="[achievement.isUnlocked ? unlockedClasses : lockedClasses, justUnlocked ? 'animate-achievement-unlock' : '']"
    :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }"
  >
    <!-- 光爆粒子 (解锁时) -->
    <div v-if="justUnlocked" class="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl">
      <div v-for="p in particles" :key="p.id"
        class="achievement-particle absolute w-2 h-2 rounded-full"
        :style="{
          top: '50%', left: '50%',
          '--px': p.x + 'px', '--py': p.y + 'px',
          backgroundColor: p.color,
        }" />
    </div>

    <!-- Icon with glow -->
    <div class="w-16 h-16 mx-auto mb-3 rounded-full flex items-center justify-center text-3xl relative"
      :class="achievement.isUnlocked ? 'bg-gradient-to-br ' + rarityGradient : 'bg-gray-100'">
      <img :src="iconEmoji" class="badge-icon" :class="achievement.isUnlocked ? '' : 'grayscale opacity-30'" alt="" />
      <!-- 发光环 (已解锁) -->
      <div v-if="achievement.isUnlocked" class="absolute inset-0 rounded-full pointer-events-none"
        :style="{ boxShadow: '0 0 20px ' + glowColor + ', 0 0 40px ' + glowColor }" />
    </div>
    <!-- Name -->
    <h4 class="text-sm font-semibold mb-1" :class="achievement.isUnlocked ? 'text-gray-800' : 'text-gray-400'">
      {{ achievement.name }}
    </h4>
    <!-- Description -->
    <p class="text-xs text-gray-400 mb-2">{{ achievement.description }}</p>
    <!-- Progress -->
    <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-1">
      <div class="h-full rounded-full transition-all" :class="rarityBarClass"
        :style="{ width: Math.min(achievement.progress / achievement.target * 100, 100) + '%' }" />
    </div>
    <span class="text-xs" :class="achievement.isUnlocked ? 'text-mint-600' : 'text-gray-400'">
      {{ achievement.isUnlocked ? '已解锁 ' + (achievement.unlockedAt || '') : achievement.progress + '/' + achievement.target }}
    </span>
    <!-- Rarity badge -->
    <span class="absolute top-2 right-2 text-xs px-2 py-0.5 rounded-full font-medium" :class="rarityBadgeClass">
      {{ rarityLabel }}
    </span>
  </div>
</template>

<script setup lang="ts">
import type { Achievement } from '@/stores/user'
import { computed, ref, watch } from 'vue'
import iconTrophy from '@/assets/icons/blue/trophy-svgrepo-com.svg'
import iconFan from '@/assets/icons/blue/fan-svgrepo-com.svg'
import iconIllumination from '@/assets/icons/fang/illumination-svgrepo-com.svg'
import iconStarTrack from '@/assets/icons/star/star-track-svgrepo-com.svg'
import iconCardHolder from '@/assets/icons/fang/card-holder-svgrepo-com.svg'

const props = defineProps<{ achievement: Achievement }>()

const wasLocked = ref(!props.achievement.isUnlocked)
const justUnlocked = ref(false)

// 检测新解锁
watch(() => props.achievement.isUnlocked, (now) => {
  if (now && wasLocked.value) {
    justUnlocked.value = true
    setTimeout(() => { justUnlocked.value = false }, 1500)
  }
  wasLocked.value = !now
}, { immediate: true })

const particles = Array.from({ length: 12 }, (_, i) => {
  const angle = (i / 12) * Math.PI * 2
  const dist = 30 + Math.random() * 50
  return {
    id: i,
    x: Math.cos(angle) * dist,
    y: Math.sin(angle) * dist,
    color: ['#6366f1', '#a855f7', '#06b6d4', '#f59e0b', '#10b981'][i % 5],
  }
})

const rarityConfig: Record<string, { gradient: string; bar: string; badge: string; label: string; glow: string }> = {
  common: { gradient: 'from-gray-300 to-gray-400', bar: 'bg-gray-400', badge: 'bg-gray-100 text-gray-600', label: '普通', glow: 'rgba(156,163,175,0.4)' },
  rare: { gradient: 'from-blue-400 to-blue-600', bar: 'bg-blue-500', badge: 'bg-blue-50 text-blue-700', label: '稀有', glow: 'rgba(96,165,250,0.5)' },
  epic: { gradient: 'from-purple-400 to-purple-600', bar: 'bg-purple-500', badge: 'bg-purple-50 text-purple-700', label: '史诗', glow: 'rgba(168,85,247,0.5)' },
  legendary: { gradient: 'from-amber-400 to-amber-600', bar: 'bg-amber-500', badge: 'bg-amber-50 text-amber-700', label: '传说', glow: 'rgba(251,191,36,0.6)' },
}
const rc = computed(() => rarityConfig[props.achievement.rarity] || rarityConfig.common)
const glowColor = computed(() => rc.value.glow)
const iconEmojiMap: Record<string, string> = { milestone: iconTrophy, streak: iconFan, skill: iconIllumination, special: iconStarTrack }
const iconEmoji = computed(() => iconEmojiMap[props.achievement.category] || iconCardHolder)
const rarityGradient = computed(() => rc.value.gradient)
const rarityBarClass = computed(() => rc.value.bar)
const rarityBadgeClass = computed(() => rc.value.badge)
const rarityLabel = computed(() => rc.value.label)
const unlockedClasses = 'shadow-sm hover:shadow-md'
const lockedClasses = 'opacity-75'
</script>

<style scoped>
.badge-icon {
  width: 1.5em;
  height: 1.5em;
  display: inline-block;
}
</style>
