<template>
  <Teleport to="body">
    <Transition name="slide-down">
      <!-- 企业侧：方角纸面通知（深蓝描边 + 珊瑚左线 + 章形方印，无 emoji / 无圆角 / 无个人侧动画） -->
      <div
        v-if="isEnt && visible"
        class="nb-ent fixed top-4 left-1/2 -translate-x-1/2 z-[9998] flex items-start gap-3 max-w-lg px-5 py-3 shadow-2xl"
        :class="'nb-ent--' + type"
      >
        <span class="nb-ent-seal"></span>
        <div class="flex-1 min-w-0">
          <p class="nb-ent-title">{{ message }}</p>
          <p v-if="detail" class="nb-ent-detail">{{ detail }}</p>
        </div>
        <button class="nb-ent-close" @click="$emit('close')">✕</button>
      </div>
      <!-- 个人侧：原样保留（圆角胶囊 + emoji + 主题色） -->
      <div
        v-else-if="visible"
        class="fixed top-4 left-1/2 -translate-x-1/2 z-[9998] px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 max-w-lg animate-scale-in"
        :class="type === 'warning' ? 'bg-amber-50 border border-amber-200 text-amber-800' :
                type === 'success' ? 'bg-mint-50 border border-mint-200 text-mint-800' :
                'bg-brand-50 border border-brand-200 text-brand-800'"
      >
        <span class="text-lg">{{ icon }}</span>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium">{{ message }}</p>
          <p v-if="detail" class="text-xs mt-0.5 opacity-70">{{ detail }}</p>
        </div>
        <button class="text-sm opacity-50 hover:opacity-100 transition-opacity ml-2" @click="$emit('close')">✕</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  visible: boolean
  message: string
  detail?: string
  type?: 'info' | 'warning' | 'success'
}>(), {
  type: 'info',
})

defineEmits<{ (e: 'close'): void }>()

// 按外壳身份分支：App.vue 已在 <html> 上设 data-side="enterprise|personal"
const isEnt = ref(typeof document !== 'undefined' && document.documentElement.dataset.side === 'enterprise')

const icon = computed(() =>
  props.type === 'warning' ? '⚠️' : props.type === 'success' ? '✅' : '🔔'
)
</script>

<style scoped>
.slide-down-enter-active { transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.slide-down-leave-active { transition: all 0.2s ease-in; }
.slide-down-enter-from { opacity: 0; transform: translate(-50%, -20px); }
.slide-down-leave-to { opacity: 0; transform: translate(-50%, -10px); }

/* ── 企业侧变体：方角纸面 · mono · 章形方印 ── */
.nb-ent {
  background: var(--ent-card);
  border: 1px solid var(--ent-navy);
  border-left: 3px solid var(--ent-coral);
  border-radius: 0;
  font-family: 'Courier New', monospace;
  box-shadow: 0 8px 24px rgba(0, 9, 76, 0.18), 0 2px 6px rgba(0, 9, 76, 0.08);
}
.nb-ent-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1.5;
  color: var(--ent-ink);
}
.nb-ent-detail {
  font-size: 10px;
  letter-spacing: 0.04em;
  margin-top: 3px;
  color: var(--ent-ink-muted);
}
/* 章形方印：微旋转小方块 + 墨点，随 type 走珊瑚/深蓝 */
.nb-ent-seal {
  flex: none;
  width: 18px;
  height: 18px;
  margin-top: 1px;
  border: 1.5px solid currentColor;
  transform: rotate(-3deg);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.nb-ent-seal::after {
  content: '';
  width: 6px;
  height: 6px;
  background: currentColor;
}
.nb-ent--warning .nb-ent-seal { color: var(--ent-coral); background: rgba(200, 92, 86, 0.06); }
.nb-ent--success .nb-ent-seal,
.nb-ent--info .nb-ent-seal { color: var(--ent-navy); background: rgba(0, 9, 76, 0.04); }
.nb-ent-close {
  font-size: 12px;
  line-height: 1;
  padding: 0;
  color: var(--ent-dim);
  opacity: 0.7;
  transition: opacity 0.2s ease, color 0.2s ease;
}
.nb-ent-close:hover { opacity: 1; color: var(--ent-coral); }
</style>
