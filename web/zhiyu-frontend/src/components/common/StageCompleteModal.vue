<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[9999] flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      <!-- Confetti particles -->
      <div class="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          v-for="piece in confettiPieces"
          :key="piece.id"
          class="confetti-piece absolute"
          :style="{
            width: piece.size + 'px',
            height: piece.size * 0.6 + 'px',
            backgroundColor: piece.color,
            top: '-10px',
            left: piece.left + '%',
            borderRadius: '2px',
            animationDelay: piece.delay + 's',
            animationDuration: piece.duration + 's',
            transform: `rotate(${piece.rotation}deg)`,
          }"
        />
      </div>

      <!-- Modal card -->
      <div class="relative animate-scale-in bg-white dark:bg-space-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl text-center">
        <!-- Glow icon -->
        <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-brand-gradient flex items-center justify-center animate-glow-pulse-strong">
          <span class="text-4xl">{{ icon }}</span>
        </div>

        <h2 class="text-xl font-bold mb-2" :style="{ color: 'var(--text-primary)' }">{{ title }}</h2>
        <p class="text-sm mb-6" :style="{ color: 'var(--text-secondary)' }">{{ subtitle }}</p>

        <div v-if="details && details.length > 0" class="flex flex-wrap justify-center gap-2 mb-6">
          <span
            v-for="d in details"
            :key="d"
            class="text-xs px-3 py-1.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200"
          >{{ d }}</span>
        </div>

        <button
          class="w-full py-3 bg-brand-gradient text-white rounded-xl font-medium hover:opacity-90 transition-opacity"
          @click="$emit('close')"
        >
          {{ actionLabel }}
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  visible: boolean
  title?: string
  subtitle?: string
  icon?: string
  actionLabel?: string
  details?: string[]
}>(), {
  title: '🎉 完成！',
  subtitle: '',
  icon: '✨',
  actionLabel: '知道了',
  details: () => [],
})

defineEmits<{ (e: 'close'): void }>()

// Deterministic confetti — 40 pieces, 7 colors
const confettiColors = ['#6366f1', '#818cf8', '#a855f7', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e']
const confettiPieces = computed(() =>
  Array.from({ length: 40 }, (_, i) => ({
    id: i,
    size: 6 + (i % 7) * 2,
    color: confettiColors[i % confettiColors.length],
    left: (i * 31 + 7) % 100,
    delay: (i * 0.04) % 1.5,
    duration: 1.2 + (i % 5) * 0.2,
    rotation: (i * 37) % 360,
  }))
)
</script>
