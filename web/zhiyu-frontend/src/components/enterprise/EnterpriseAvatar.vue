<template>
  <div class="ent-avatar-float">
    <!-- ═══ 折叠芯片：唤起数字人 ═══ -->
    <button
      v-if="!store.enabled"
      class="ent-avatar-chip"
      @click="open"
      title="唤起数字人"
    >
      <span class="ent-avatar-dot"></span>
      <span class="ent-avatar-chip-text">数字人</span>
    </button>

    <!-- ═══ 迷你窗：数字人舞台 + 汇报脚本 ═══ -->
    <div v-else class="ent-avatar-card">
      <header class="ent-avatar-head">
        <span class="ent-avatar-name">数字人 · 汇报员</span>
        <span class="ent-avatar-badge" :class="store.mode">{{ modeLabel }}</span>
      </header>

      <!-- 舞台：真实 SDK 挂载在 stage-sdk，遮罩为兄弟元素（不干扰 SDK DOM） -->
      <div class="ent-avatar-stage">
        <div ref="stageRef" class="ent-avatar-stage-sdk"></div>

        <div v-if="store.mode === 'connecting'" class="ent-avatar-overlay">
          <div class="ent-avatar-spin"></div>
          <span class="ent-avatar-overlay-text">数字人连接中…</span>
        </div>

        <div v-if="store.mode === 'demo'" class="ent-avatar-overlay ent-avatar-demo">
          <svg class="ent-avatar-figure" :class="{ speaking: store.isSpeaking }" viewBox="0 0 120 180" aria-hidden="true">
            <!-- 说话光晕 -->
            <circle class="ent-avatar-halo" cx="60" cy="54" r="34" />
            <circle class="ent-avatar-head" cx="60" cy="54" r="24" />
            <!-- 西装肩线 -->
            <path d="M18 178 C20 128 40 116 60 116 C80 116 100 128 102 178 Z" class="ent-avatar-suit" />
            <!-- 珊瑚领带 -->
            <path d="M53 118 L60 144 L67 118 Z" class="ent-avatar-tie" />
          </svg>
          <div class="ent-avatar-waves" :class="{ active: store.isSpeaking }">
            <i v-for="n in 5" :key="n"></i>
          </div>
          <span class="ent-avatar-demotag">演示数字人</span>
          <!-- 真实 persona：形象/音色 ID（讯飞云端资源，未配密钥时以演示角色呈现） -->
          <div v-if="store.persona" class="ent-avatar-persona">
            形象 {{ store.persona.avatarId }} · 音色 {{ store.persona.voiceId }}
          </div>
          <!-- 连接失败原因（真实通路失败时展示，帮助排查） -->
          <div v-if="store.error" class="ent-avatar-error">{{ store.error }}</div>
        </div>

        <div v-if="store.playNotAllowed" class="ent-avatar-overlay ent-avatar-unmute" @click="store.resumeAudio()">
          <span>🔊 点击开启声音</span>
        </div>
      </div>

      <!-- 字幕 -->
      <div class="ent-avatar-caption" :class="{ empty: !store.currentText }">
        {{ store.currentText || '选择下方脚本，开始朗读汇报' }}
      </div>

      <!-- 操作行 -->
      <div class="ent-avatar-actions">
        <select
          class="ent-avatar-script"
          :value="selectedId"
          :disabled="store.isSpeaking"
          @change="playSelected($event)"
          title="选择汇报脚本"
        >
          <option value="" disabled>📋 汇报脚本…</option>
          <option v-for="s in scripts" :key="s.id" :value="s.id">{{ s.title }}</option>
        </select>
        <button
          class="ent-avatar-btn"
          :class="{ disabled: !store.isSpeaking }"
          :disabled="!store.isSpeaking"
          @click="store.stop()"
          title="停止朗读"
        >⏹</button>
        <button
          class="ent-avatar-btn"
          :disabled="!lastScript"
          :class="{ disabled: !lastScript }"
          @click="replay"
          title="重播上一次"
        >🔊</button>
        <button class="ent-avatar-btn ent-avatar-close" @click="store.close()" title="关闭">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, nextTick } from 'vue'
import { useAvatarStore } from '@/stores/avatar'
import { useEnterpriseStore } from '@/stores/enterprise'
import { buildAvatarScripts, type AvatarScript } from '@/utils/avatarScripts'

const store = useAvatarStore()
const ent = useEnterpriseStore()

const stageRef = ref<HTMLDivElement | null>(null)
const selectedId = ref('')
const lastScript = ref<AvatarScript | null>(null)

const scripts = computed(() => buildAvatarScripts(ent))

const modeLabel = computed(() => {
  switch (store.mode) {
    case 'real': return '已连接'
    case 'demo': return '演示模式'
    case 'connecting': return '连接中'
    default: return '—'
  }
})

async function open() {
  // 先展开迷你窗（stage 挂载），再连接 SDK —— 否则 stage 尚不存在，真实/演示都无处挂载
  store.show()
  await nextTick()
  const el = stageRef.value
  if (!el) { store.mode = 'demo'; return }
  await store.connect(el)
}

function playSelected(e: Event) {
  const id = (e.target as HTMLSelectElement).value
  selectedId.value = ''
  const s = scripts.value.find((x) => x.id === id)
  if (!s) return
  lastScript.value = s
  store.speak(s.text)
}

function replay() {
  if (lastScript.value) store.speak(lastScript.value.text)
}

onBeforeUnmount(() => { store.close() })
</script>

<style scoped>
/* ═══════ 企业侧悬浮数字人 —— 蓝皮书色板（navy/coral/paper） ═══════ */

.ent-avatar-float {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 90;
  font-family: var(--ent-font, inherit);
}

/* ── 折叠芯片 ── */
.ent-avatar-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 16px;
  background: var(--ent-paper);
  border: 1px solid var(--ent-navy);
  border-radius: 6px;
  box-shadow: 0 4px 18px rgba(0, 9, 76, 0.18);
  cursor: pointer;
  transition: all 0.2s ease;
}
.ent-avatar-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 9, 76, 0.26);
}
.ent-avatar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ent-coral);
  box-shadow: 0 0 0 3px rgba(200, 92, 86, 0.18);
  animation: avatar-dot 2s ease-in-out infinite;
}
@keyframes avatar-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
.ent-avatar-chip-text {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--ent-navy);
}

/* ── 迷你窗 ── */
.ent-avatar-card {
  width: 216px;
  background: var(--ent-paper);
  border: 1px solid var(--ent-navy);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 10px 34px rgba(0, 9, 76, 0.30);
  display: flex;
  flex-direction: column;
}

.ent-avatar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 7px 10px;
  background: var(--ent-navy);
  color: #fff;
}
.ent-avatar-name {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ent-avatar-badge {
  flex: none;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 2px 6px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 3px;
  color: #fff;
}
.ent-avatar-badge.demo { border-color: var(--ent-coral); color: var(--ent-coral); }
.ent-avatar-badge.connecting { opacity: 0.7; animation: avatar-dot 1.2s ease-in-out infinite; }

/* ── 舞台 ── */
.ent-avatar-stage {
  position: relative;
  aspect-ratio: 9 / 16;
  background:
    radial-gradient(120% 60% at 50% 0%, rgba(200, 92, 86, 0.16), transparent 60%),
    linear-gradient(180deg, #0a1250 0%, var(--ent-navy) 100%);
  overflow: hidden;
}
.ent-avatar-stage-sdk {
  width: 100%;
  height: 100%;
}
.ent-avatar-stage-sdk :deep(video),
.ent-avatar-stage-sdk :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
}

.ent-avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.ent-avatar-overlay-text {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.65);
  letter-spacing: 0.08em;
}
.ent-avatar-spin {
  width: 26px;
  height: 26px;
  border: 2px solid rgba(200, 92, 86, 0.22);
  border-top-color: var(--ent-coral);
  border-radius: 50%;
  animation: avatar-spin 0.8s linear infinite;
}
@keyframes avatar-spin { to { transform: rotate(360deg); } }

/* ── 演示数字人 ── */
.ent-avatar-demo {
  pointer-events: none;
}
.ent-avatar-figure {
  width: 96px;
  height: auto;
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.35));
}
.ent-avatar-halo {
  fill: none;
  stroke: var(--ent-coral);
  stroke-width: 1.5;
  opacity: 0.55;
}
.ent-avatar-figure.speaking .ent-avatar-halo {
  animation: avatar-halo 1s ease-in-out infinite;
}
@keyframes avatar-halo {
  0%, 100% { transform: scale(1); opacity: 0.55; }
  50% { transform: scale(1.12); opacity: 0.95; }
}
.ent-avatar-head { fill: var(--ent-paper); }
.ent-avatar-suit { fill: #0b1647; }
.ent-avatar-tie { fill: var(--ent-coral); }
.ent-avatar-figure.speaking .ent-avatar-head {
  animation: avatar-bob 0.7s ease-in-out infinite;
}
@keyframes avatar-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.ent-avatar-waves {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 16px;
}
.ent-avatar-waves i {
  width: 3px;
  height: 4px;
  background: var(--ent-coral);
  border-radius: 1px;
  opacity: 0.45;
}
.ent-avatar-waves.active i { animation: avatar-wave 0.8s ease-in-out infinite; }
.ent-avatar-waves i:nth-child(1) { animation-delay: 0s; }
.ent-avatar-waves i:nth-child(2) { animation-delay: 0.12s; }
.ent-avatar-waves i:nth-child(3) { animation-delay: 0.24s; }
.ent-avatar-waves i:nth-child(4) { animation-delay: 0.36s; }
.ent-avatar-waves i:nth-child(5) { animation-delay: 0.48s; }
@keyframes avatar-wave {
  0%, 100% { height: 4px; opacity: 0.45; }
  50% { height: 16px; opacity: 1; }
}
.ent-avatar-demotag {
  font-size: 9px;
  letter-spacing: 0.14em;
  color: var(--ent-coral);
  border: 1px solid var(--ent-coral);
  border-radius: 3px;
  padding: 2px 7px;
}
.ent-avatar-persona {
  position: absolute;
  bottom: 5px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 8px;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.6);
  font-family: var(--ent-font-mono, inherit);
}
.ent-avatar-error {
  position: absolute;
  bottom: 16px;
  left: 6px;
  right: 6px;
  text-align: center;
  font-size: 8px;
  line-height: 1.4;
  color: rgba(255, 140, 130, 0.85);
  font-family: var(--ent-font-mono, inherit);
}

.ent-avatar-unmute {
  background: rgba(200, 92, 86, 0.18);
  color: #fff;
  font-size: 11px;
  cursor: pointer;
}

/* ── 字幕 ── */
.ent-avatar-caption {
  padding: 7px 10px;
  min-height: 46px;
  font-size: 10px;
  line-height: 1.5;
  color: var(--ent-ink);
  border-top: 1px solid var(--ent-rule);
  border-bottom: 1px solid var(--ent-rule);
  font-family: var(--ent-font-mono, inherit);
}
.ent-avatar-caption.empty { color: var(--ent-ink-muted); }

/* ── 操作行 ── */
.ent-avatar-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 8px;
}
.ent-avatar-script {
  flex: 1;
  min-width: 0;
  font-size: 10px;
  color: var(--ent-ink);
  background: #fff;
  border: 1px solid var(--ent-rule);
  border-radius: 4px;
  padding: 5px 4px;
  cursor: pointer;
  outline: none;
}
.ent-avatar-script:focus { border-color: var(--ent-coral); }
.ent-avatar-btn {
  flex: none;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  background: #fff;
  color: var(--ent-navy);
  border: 1px solid var(--ent-rule);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.ent-avatar-btn:hover:not(.disabled) { border-color: var(--ent-coral); color: var(--ent-coral); }
.ent-avatar-btn.disabled { opacity: 0.35; cursor: not-allowed; }
.ent-avatar-close { color: var(--ent-coral); }
</style>
