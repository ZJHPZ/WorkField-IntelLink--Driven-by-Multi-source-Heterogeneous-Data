<template>
  <div
    class="planet-node"
    :class="statusClass"
    :style="nodeStyle"
    @click="handleClick"
  >
    <div class="planet-node__body">
      <span class="planet-node__name">{{ name }}</span>
    </div>
    <div v-if="status === 'mastered'" class="planet-node__glow" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  id: string
  name: string
  status: 'mastered' | 'learning' | 'locked'
  x: number
  y: number
  size?: number
}>(), {
  size: 64,
})

const emit = defineEmits<{ (e: 'click', id: string): void }>()

const nodeStyle = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`,
  width: `${props.size}px`,
  height: `${props.size}px`,
}))

const statusClass = computed(() => `planet-node--${props.status}`)

function handleClick() {
  if (props.status !== 'locked') emit('click', props.id)
}
</script>

<style scoped>
.planet-node {
  position: absolute;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.3s ease;
  z-index: 10;
}
.planet-node:hover { transform: scale(1.15); z-index: 20; }
.planet-node__body {
  width: 100%; height: 100%; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #d1d5db, #9ca3af);
  color: white; font-size: 0.7rem; font-weight: 700;
  text-align: center; padding: 0.4rem; line-height: 1.2;
  transition: all 0.3s ease;
}
.planet-node--mastered .planet-node__body {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  box-shadow: 0 0 24px rgba(34,197,94,0.4);
}
.planet-node--learning .planet-node__body {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  animation: planetPulse 2s infinite;
  box-shadow: 0 0 16px rgba(59,130,246,0.3);
}
.planet-node--locked .planet-node__body {
  background: linear-gradient(135deg, #d1d5db, #9ca3af);
  opacity: 0.5; cursor: not-allowed;
}
.planet-node__glow {
  position: absolute; inset: -6px; border-radius: 50%;
  background: conic-gradient(from 0deg, #22c55e, #4ade80, transparent, #22c55e);
  animation: planetGlow 3s linear infinite; pointer-events: none;
}
@keyframes planetPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}
@keyframes planetGlow {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
