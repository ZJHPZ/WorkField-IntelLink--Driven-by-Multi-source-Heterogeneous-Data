<template>
  <div class="avatar-player" :class="{ 'is-mini': mini }">
    <!-- SDK 播放器挂载容器 -->
    <div ref="containerRef" class="avatar-container"></div>

    <!-- 加载 / 占位 -->
    <div v-if="isLoading || !isReady" class="avatar-overlay">
      <div v-if="isLoading" class="avatar-loading-spinner"></div>
      <span v-else class="avatar-placeholder-icon">🧑‍💻</span>
      <p class="avatar-overlay-text">{{ isLoading ? '数字人加载中...' : '点击下方按钮开启数字人' }}</p>
    </div>

    <!-- 浏览器禁止自动播放 -->
    <div v-if="isReady && avatarStore.playNotAllowed" class="avatar-overlay avatar-unmute" @click="avatarStore.resumeAudio()">
      <span class="avatar-unmute-icon">🔊</span>
      <span class="avatar-unmute-text">点击开启声音</span>
    </div>

    <!-- 控制按钮 -->
    <div v-if="isReady" class="avatar-controls">
      <button
        v-if="!mini"
        class="avatar-ctrl-btn"
        title="关闭数字人"
        @click="close"
      >✕</button>
      <button
        v-else
        class="avatar-ctrl-btn"
        title="关闭数字人"
        @click="close"
      >✕</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useAvatarStore } from '@/stores/avatar'

const props = defineProps<{
  mini?: boolean
}>()

const emit = defineEmits<{
  close: []
  toggleSize: []
}>()

const avatarStore = useAvatarStore()
const containerRef = ref<HTMLDivElement | null>(null)
const isReady = computed(() => avatarStore.isActive && !avatarStore.isConnecting)
const isLoading = computed(() => avatarStore.enabled && avatarStore.isConnecting)

async function close() {
  emit('close')
}

onMounted(async () => {
  if (!containerRef.value) return
  if (avatarStore.enabled) {
    if (avatarStore.isActive) {
      // 已连接，只是切换容器（欢迎态 ↔ 消息态迷你窗）
      avatarStore.movePlayer(containerRef.value)
    } else if (!avatarStore.isConnecting) {
      // 首次连接
      await avatarStore.connectPlayer(containerRef.value)
    }
  }
})

// 当 enabled 变为 true 时触发连接
watch(() => avatarStore.enabled, async (val) => {
  if (val && containerRef.value && !avatarStore.isActive && !avatarStore.isConnecting) {
    await avatarStore.connectPlayer(containerRef.value)
  }
})

onBeforeUnmount(() => {
  // 不销毁 SDK，另一个 AvatarPlayer 实例会接管容器
})
</script>

<style scoped>
.avatar-player {
  position: relative;
  width: 100%;
  background: #f8f9fd;
  border-radius: 16px;
  overflow: hidden;
  aspect-ratio: 9 / 16;
  max-height: 480px;
  border: 1px solid rgba(99, 102, 241, 0.18);
}

.avatar-player.is-mini {
  width: 180px;
  aspect-ratio: 9 / 16;
  max-height: 320px;
  position: fixed;
  bottom: 100px;
  right: 24px;
  z-index: 100;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.avatar-container {
  width: 100%;
  height: 100%;
  border-radius: inherit;
}

/* SDK 内部的 video/canvas 填满容器 */
.avatar-container :deep(video),
.avatar-container :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
  border-radius: inherit;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f9fd;
  z-index: 2;
}

.avatar-overlay-text {
  font-size: 13px;
  color: #5b6abf;
  margin-top: 8px;
}

.avatar-placeholder-icon {
  font-size: 40px;
  opacity: 0.8;
}

.avatar-loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid rgba(99, 102, 241, 0.15);
  border-top-color: rgba(99, 102, 241, 0.6);
  border-radius: 50%;
  animation: avatar-spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes avatar-spin {
  to { transform: rotate(360deg); }
}

.avatar-unmute {
  background: rgba(99, 102, 241, 0.12);
  cursor: pointer;
  transition: background 0.3s ease;
}

.avatar-unmute:hover {
  background: rgba(99, 102, 241, 0.22);
}

.avatar-unmute-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.avatar-unmute-text {
  font-size: 13px;
  color: #4f5aa8;
  font-weight: 500;
}

.avatar-controls {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  z-index: 3;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.avatar-player:hover .avatar-controls {
  opacity: 1;
}

.avatar-ctrl-btn {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  border: none;
  background: rgba(99, 102, 241, 0.15);
  color: #5b6abf;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
  transition: background 0.2s ease;
}

.avatar-ctrl-btn:hover {
  background: rgba(99, 102, 241, 0.30);
}
</style>
