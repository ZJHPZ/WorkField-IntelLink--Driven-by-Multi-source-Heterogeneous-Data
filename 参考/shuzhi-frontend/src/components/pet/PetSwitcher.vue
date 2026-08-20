<template>
  <div class="fixed bottom-4 left-4 z-[10000]">
    <!-- 切换按钮 -->
    <button
      class="w-10 h-10 bg-white/90 backdrop-blur-md rounded-full shadow-lg border border-gray-200 flex items-center justify-center text-lg hover:bg-white transition-all active:scale-95"
      title="宠物管理"
      @click="isOpen = !isOpen"
    >
      {{ isOpen ? '✕' : '🐱' }}
    </button>

    <!-- 管理面板 -->
    <Transition name="slide-up">
      <div v-if="isOpen" class="absolute bottom-12 left-0 w-72 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 p-4 space-y-4 max-h-[70vh] overflow-y-auto">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-700">🐱 桌面宠物管理</h3>
          <span class="text-xs text-gray-400">管理员专用</span>
        </div>

        <!-- 宠物选择 -->
        <div>
          <label class="text-xs font-medium text-gray-500 mb-1.5 block">选择宠物</label>
          <div class="grid grid-cols-2 gap-1.5">
            <button
              v-for="(cfg, id) in petConfigs"
              :key="id"
              class="text-left px-3 py-2 rounded-xl text-xs transition-all border"
              :class="petStore.currentPet === id
                ? 'bg-brand-50 border-brand-300 text-brand-700 font-medium'
                : 'bg-gray-50 border-gray-100 text-gray-600 hover:bg-gray-100'"
              @click="petStore.setCurrentPet(id as PetId)"
            >
              {{ cfg.name }}
            </button>
          </div>
        </div>

        <!-- 行为测试 -->
        <div>
          <label class="text-xs font-medium text-gray-500 mb-1.5 block">测试行为</label>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="beh in behaviors"
              :key="beh.state"
              class="px-3 py-1.5 rounded-xl text-xs font-medium transition-all border active:scale-95"
              :class="petStore.currentState === beh.state
                ? beh.activeClass
                : 'bg-gray-50 border-gray-100 text-gray-600 hover:bg-gray-100'"
              @click="petStore.setState(beh.state as PetState); petStore.randomChat(beh.state as PetState)"
            >
              {{ beh.label }}
            </button>
          </div>
        </div>

        <!-- 对话框测试 -->
        <div>
          <label class="text-xs font-medium text-gray-500 mb-1.5 block">测试对话框</label>
          <div class="flex flex-wrap gap-1.5">
            <button
              class="px-3 py-1.5 rounded-xl text-xs font-medium bg-amber-50 border border-amber-200 text-amber-700 hover:bg-amber-100 transition-all active:scale-95"
              @click="petStore.randomChat()"
            >
              💬 随机对话
            </button>
            <button
              class="px-3 py-1.5 rounded-xl text-xs font-medium bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 transition-all active:scale-95"
              @click="petStore.triggerAlert()"
            >
              ⏰ 休息提醒
            </button>
            <button
              class="px-3 py-1.5 rounded-xl text-xs font-medium bg-green-50 border border-green-200 text-green-600 hover:bg-green-100 transition-all active:scale-95"
              @click="petStore.celebrate('测试成就：你已经解锁了隐藏彩蛋！🎉')"
            >
              🎉 成就彩蛋
            </button>
          </div>
        </div>

        <!-- 尺寸调节 -->
        <div>
          <label class="text-xs font-medium text-gray-500 mb-1.5 block">
            宠物尺寸：{{ petStore.size }}px
          </label>
          <input
            type="range"
            min="60"
            max="260"
            :value="petStore.size"
            class="w-full h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer accent-brand-500"
            @input="petStore.setSize(Number(($event.target as HTMLInputElement).value))"
          />
          <div class="flex justify-between text-[10px] text-gray-400 mt-0.5">
            <span>60px</span>
            <span>260px</span>
          </div>
        </div>

        <!-- 其他操作 -->
        <div class="flex gap-2">
          <button
            class="flex-1 py-2 rounded-xl text-xs font-medium bg-gray-100 text-gray-500 hover:bg-gray-200 transition-all active:scale-95"
            @click="resetPosition"
          >
            📍 重置位置
          </button>
          <button
            class="flex-1 py-2 rounded-xl text-xs font-medium bg-gray-100 text-gray-500 hover:bg-gray-200 transition-all active:scale-95"
            @click="petStore.resetRestTimer()"
          >
            🔄 重置计时
          </button>
        </div>

        <button
          class="w-full py-2 rounded-xl text-xs font-medium border border-dashed border-gray-300 text-gray-400 hover:bg-gray-50 transition-all"
          @click="petStore.toggleVisibility()"
        >
          {{ petStore.isVisible ? '🙈 暂时隐藏' : '👀 显示宠物' }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { usePetStore, petConfigs, type PetState, type PetId } from '@/stores/pet'

const petStore = usePetStore()
const isOpen = ref(false)

const behaviors = [
  { state: 'idle', label: '😴 待机', activeClass: 'bg-blue-50 border-blue-300 text-blue-700' },
  { state: 'active', label: '🎯 活跃', activeClass: 'bg-brand-50 border-brand-300 text-brand-700' },
  { state: 'alert', label: '⚠️ 提醒', activeClass: 'bg-red-50 border-red-300 text-red-700' },
  { state: 'celebrate', label: '🎉 庆祝', activeClass: 'bg-green-50 border-green-300 text-green-700' },
  { state: 'sleeping', label: '💤 睡觉', activeClass: 'bg-purple-50 border-purple-300 text-purple-700' },
]

function resetPosition() {
  petStore.setPosition(20, 20)
}
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.95);
}
</style>
