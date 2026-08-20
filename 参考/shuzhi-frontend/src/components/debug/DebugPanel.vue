<template>
  <!-- 折叠齿轮按钮 -->
  <button
    v-if="!isOpen"
    class="fixed bottom-6 right-6 z-50 w-11 h-11 rounded-full flex items-center justify-center text-xl shadow-lg border transition-all duration-300 hover:rotate-90"
    :style="{ background: 'rgba(15,23,42,0.9)', borderColor: 'rgba(99,102,241,0.35)', color: 'var(--brand-400)' }"
    @click="isOpen = true"
    title="调试面板"
  ><img :src="iconSetUp" class="debug-gear-icon" alt="" /></button>

  <!-- 展开面板 -->
  <Transition name="debug-slide">
    <aside
      v-if="isOpen"
      class="fixed top-0 right-0 h-full w-[360px] z-50 flex flex-col shadow-2xl"
      :style="{ background: 'rgba(15,23,42,0.94)', borderLeft: '1px solid rgba(99,102,241,0.25)', color: 'var(--text-primary)' }"
    >
      <!-- 标题栏 -->
      <div class="flex items-center justify-between px-4 py-3 shrink-0" :style="{ borderBottom: '1px solid rgba(99,102,241,0.15)' }">
        <h2 class="text-sm font-bold flex items-center gap-2">
          <img :src="iconSetUp" class="debug-title-icon" alt="" /> 调试控制台
          <span class="text-[10px] px-1.5 py-0.5 bg-brand-500/20 text-brand-400 rounded-full font-normal">admin</span>
        </h2>
        <button class="text-gray-400 hover:text-white transition-colors text-lg leading-none" @click="isOpen = false">✕</button>
      </div>

      <!-- 标签导航 -->
      <div class="flex gap-1 px-3 py-2 shrink-0 overflow-x-auto" :style="{ borderBottom: '1px solid rgba(99,102,241,0.1)' }">
        <button
          v-for="tab in tabs" :key="tab.key"
          class="px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1"
          :style="activeTab === tab.key ? { background: 'rgba(99,102,241,0.2)', color: 'var(--brand-400)' } : { color: 'var(--text-muted)' }"
          @click="activeTab = tab.key"
        >
          <img v-if="tab.svg" :src="tab.svg" class="debug-tab-icon" alt="" />
          <span v-if="tab.emoji">{{ tab.emoji }}</span>
          {{ tab.label }}
        </button>
      </div>

      <!-- 内容区 -->
      <div class="flex-1 overflow-y-auto px-3 py-3 space-y-4 text-xs">
        <!-- ========== 宠物 Tab ========== -->
        <section v-if="activeTab === 'pet'">
          <h3 class="text-brand-400 font-semibold mb-2">状态切换</h3>
          <div class="flex flex-wrap gap-1.5 mb-3">
            <button v-for="s in petStates" :key="s" class="px-2.5 py-1 rounded-md text-xs transition-all border"
              :style="petStore.currentState === s ? { background: 'rgba(99,102,241,0.2)', borderColor: 'var(--brand-500)', color: 'var(--brand-400)' } : { borderColor: 'rgba(99,102,241,0.12)', color: 'var(--text-secondary)' }"
              @click="petStore.setState(s)">{{ emojiFor(s) }} {{ s }}</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">选择宠物</h3>
          <div class="flex flex-wrap gap-1.5 mb-3">
            <button v-for="(cfg, id) in petConfigs" :key="id" class="px-2.5 py-1 rounded-md text-xs transition-all border"
              :style="petStore.currentPet === id ? { background: 'rgba(99,102,241,0.2)', borderColor: 'var(--brand-500)', color: 'var(--brand-400)' } : { borderColor: 'rgba(99,102,241,0.12)', color: 'var(--text-secondary)' }"
              @click="petStore.setCurrentPet(id)">{{ cfg.name }}</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">动作</h3>
          <div class="flex flex-wrap gap-1.5 mb-3">
            <button class="px-2.5 py-1 rounded-md text-xs border transition-all" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="petStore.interact()">💬 互动</button>
            <button class="px-2.5 py-1 rounded-md text-xs border transition-all" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="petStore.celebrate('🎉 调试庆祝！')">🎉 庆祝</button>
            <button class="px-2.5 py-1 rounded-md text-xs border transition-all" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="petStore.triggerAlert()">⚠️ 休息提醒</button>
            <button class="px-2.5 py-1 rounded-md text-xs border transition-all" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="customBubble()">💭 气泡</button>
            <button class="px-2.5 py-1 rounded-md text-xs border transition-all" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="petStore.dismissBubble()">✕ 关闭气泡</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">位置/大小</h3>
          <div class="grid grid-cols-2 gap-2 mb-2">
            <div>
              <span :style="{ color: 'var(--text-muted)' }">X: {{ petStore.position.x }}</span>
              <input type="range" :min="-200" max="200" :value="petStore.position.x" class="w-full"
                @input="petStore.setPosition(Number(($event.target as HTMLInputElement).value), petStore.position.y)">
            </div>
            <div>
              <span :style="{ color: 'var(--text-muted)' }">Y: {{ petStore.position.y }}</span>
              <input type="range" :min="-200" max="200" :value="petStore.position.y" class="w-full"
                @input="petStore.setPosition(petStore.position.x, Number(($event.target as HTMLInputElement).value))">
            </div>
          </div>
          <div class="mb-3">
            <span :style="{ color: 'var(--text-muted)' }">大小: {{ petStore.size }}px</span>
            <input type="range" :min="60" max="300" :value="petStore.size" class="w-full"
              @input="petStore.setSize(Number(($event.target as HTMLInputElement).value))">
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">学习时长模拟</h3>
          <div class="flex gap-1.5 mb-2">
            <input type="number" v-model.number="petMinutesInput" class="w-20 px-2 py-1 rounded text-xs border" placeholder="分钟"
              :style="{ background: 'rgba(15,23,42,0.6)', borderColor: 'rgba(99,102,241,0.2)', color: 'var(--text-primary)' }">
            <button class="px-2 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="petStore.tickLearning(petMinutesInput)">+ 分钟</button>
            <button class="px-2 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="petStore.resetRestTimer()">重置</button>
          </div>
          <p :style="{ color: 'var(--text-muted)' }">累计: {{ petStore.learningMinutes }}分钟 (≥150触发休息提醒)</p>
        </section>

        <!-- ========== 学习 Tab ========== -->
        <section v-if="activeTab === 'learning'">
          <h3 class="text-brand-400 font-semibold mb-2">学习指标</h3>
          <div class="grid grid-cols-2 gap-2 mb-3">
            <div>
              <span :style="{ color: 'var(--text-muted)' }">Streak: {{ learningStore.streakDays }}天</span>
              <input type="range" :min="0" :max="365" :value="learningStore.streakDays" class="w-full"
                @input="learningStore.streakDays = Number(($event.target as HTMLInputElement).value)">
            </div>
            <div>
              <span :style="{ color: 'var(--text-muted)' }">今日时长: {{ learningStore.todayMinutes }}min</span>
              <input type="range" :min="0" :max="240" :value="learningStore.todayMinutes" class="w-full"
                @input="learningStore.todayMinutes = Number(($event.target as HTMLInputElement).value)">
            </div>
            <div>
              <span :style="{ color: 'var(--text-muted)' }">Curiosity: {{ learningStore.curiosityIndex }}</span>
              <input type="range" :min="0" :max="100" :value="learningStore.curiosityIndex" class="w-full"
                @input="learningStore.curiosityIndex = Number(($event.target as HTMLInputElement).value)">
            </div>
            <div>
              <span :style="{ color: 'var(--text-muted)' }">Flow: {{ learningStore.flowState }}</span>
              <select :value="learningStore.flowState" class="w-full px-1.5 py-1 rounded text-xs border"
                :style="{ background: 'rgba(15,23,42,0.6)', borderColor: 'rgba(99,102,241,0.2)', color: 'var(--text-primary)' }"
                @change="learningStore.flowState = ($event.target as HTMLSelectElement).value as any">
                <option value="flow">flow</option><option value="engaged">engaged</option><option value="bored">bored</option><option value="frustrated">frustrated</option>
              </select>
            </div>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">阶段进度 (滑动到100触发完成弹窗)</h3>
          <div v-if="learningStore.currentPath" class="space-y-2 mb-3 max-h-64 overflow-y-auto">
            <div v-for="(stage, i) in learningStore.currentPath.stages" :key="i" class="flex items-center gap-2">
              <span class="w-20 truncate" :style="{ color: 'var(--text-secondary)' }">{{ stage.title.slice(0, 10) }}</span>
              <input type="range" :min="0" :max="100" :value="stage.progress" class="flex-1"
                @input="stage.progress = Number(($event.target as HTMLInputElement).value); if (stage.progress >= 100) stage.status = 'completed'">
              <span class="w-10 text-right text-[10px]" :class="stage.status === 'completed' ? 'text-mint-500' : 'text-gray-400'">{{ stage.progress }}%</span>
            </div>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">Topic 掌握度一键满级</h3>
          <button class="px-3 py-1.5 rounded-md text-xs border transition-all mb-2"
            style="border-color: rgba(16,185,129,0.3); color: var(--mint-500);"
            @click="masterAllTopics()">🚀 全部 Topic → 满级 (mastery=1.0)</button>
          <div class="max-h-40 overflow-y-auto space-y-1">
            <div v-for="t in learningStore.topicMasteryList.slice(0, 10)" :key="t.topicId" class="flex items-center gap-2">
              <span class="w-24 truncate" :style="{ color: 'var(--text-secondary)' }">{{ t.name }}</span>
              <span class="text-[10px]" :style="{ color: 'var(--text-muted)' }">{{ t.masteryLevel.toFixed(2) }}</span>
              <span class="text-[10px] px-1 rounded" :class="t.status === 'mastered' ? 'text-mint-500 bg-mint-500/10' : t.status === 'learning' ? 'text-brand-400 bg-brand-500/10' : 'text-gray-400'">{{ t.status }}</span>
            </div>
          </div>
        </section>

        <!-- ========== 成就 Tab ========== -->
        <section v-if="activeTab === 'achievements'">
          <h3 class="text-brand-400 font-semibold mb-2">用户属性</h3>
          <div class="grid grid-cols-3 gap-2 mb-3">
            <div>
              <span :style="{ color: 'var(--text-muted)' }">金币: {{ userStore.profile.totalCoins }}</span>
              <input type="number" :value="userStore.profile.totalCoins" class="w-full px-1.5 py-0.5 rounded text-xs border"
                :style="{ background: 'rgba(15,23,42,0.6)', borderColor: 'rgba(99,102,241,0.2)', color: 'var(--text-primary)' }"
                @input="userStore.profile.totalCoins = Number(($event.target as HTMLInputElement).value)">
            </div>
            <div>
              <span :style="{ color: 'var(--text-muted)' }">LV: {{ userStore.profile.currentLevel }}</span>
              <input type="number" :value="userStore.profile.currentLevel" class="w-full px-1.5 py-0.5 rounded text-xs border"
                :style="{ background: 'rgba(15,23,42,0.6)', borderColor: 'rgba(99,102,241,0.2)', color: 'var(--text-primary)' }"
                @input="userStore.profile.currentLevel = Number(($event.target as HTMLInputElement).value)">
            </div>
            <div>
              <span :style="{ color: 'var(--text-muted)' }">EXP: {{ userStore.profile.totalExp }}</span>
              <input type="number" :value="userStore.profile.totalExp" class="w-full px-1.5 py-0.5 rounded text-xs border"
                :style="{ background: 'rgba(15,23,42,0.6)', borderColor: 'rgba(99,102,241,0.2)', color: 'var(--text-primary)' }"
                @input="userStore.profile.totalExp = Number(($event.target as HTMLInputElement).value)">
            </div>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">成就解锁切换 (toggle 触发粒子动画)</h3>
          <div class="space-y-1.5 max-h-80 overflow-y-auto">
            <div v-for="a in userStore.achievements" :key="a.id" class="flex items-center gap-2 py-1">
              <button class="px-2 py-0.5 rounded text-[10px] font-medium border transition-all min-w-[50px]"
                :class="a.isUnlocked ? 'text-mint-500 border-mint-500/30 bg-mint-500/10' : 'text-gray-400 border-gray-400/20'"
                @click="a.isUnlocked = !a.isUnlocked">
                {{ a.isUnlocked ? '已解锁' : '已锁定' }}
              </button>
              <span class="flex-1 truncate" :style="{ color: a.isUnlocked ? 'var(--text-primary)' : 'var(--text-muted)' }">{{ a.name }}</span>
              <span class="text-[10px] px-1 rounded" :style="{ color: 'var(--text-muted)' }">{{ a.rarity }}</span>
            </div>
          </div>

          <h3 class="text-brand-400 font-semibold mt-3 mb-2">一键操作</h3>
          <div class="flex gap-1.5">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(16,185,129,0.3); color: var(--mint-500);"
              @click="userStore.achievements.forEach(a => a.isUnlocked = true)">全部解锁</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="userStore.achievements.forEach(a => a.isUnlocked = false)">全部锁定</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="userStore.fetchAchievements()">🔄 重置为默认</button>
          </div>
        </section>

        <!-- ========== 主题 Tab ========== -->
        <section v-if="activeTab === 'theme'">
          <h3 class="text-brand-400 font-semibold mb-2">主题模式</h3>
          <div class="flex gap-2 mb-3">
            <button class="px-3 py-1.5 rounded-md text-xs border transition-all"
              :style="themeStore.mode === 'dark' ? { background: 'rgba(99,102,241,0.2)', borderColor: 'var(--brand-500)', color: 'var(--brand-400)' } : { borderColor: 'rgba(99,102,241,0.12)', color: 'var(--text-secondary)' }"
              @click="themeStore.setTheme('dark')"><img :src="iconMoon" class="debug-theme-icon" alt="" /> 深色</button>
            <button class="px-3 py-1.5 rounded-md text-xs border transition-all"
              :style="themeStore.mode === 'light' ? { background: 'rgba(99,102,241,0.2)', borderColor: 'var(--brand-500)', color: 'var(--brand-400)' } : { borderColor: 'rgba(99,102,241,0.12)', color: 'var(--text-secondary)' }"
              @click="themeStore.setTheme('light')">☀️ 浅色</button>
            <button class="px-3 py-1.5 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="themeStore.toggle()">🔀 切换</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">星空背景</h3>
          <div class="text-xs" :style="{ color: 'var(--text-muted)' }">
            CosmicBackground 在深色主题下自动显示。切换到浅色主题即隐藏。
          </div>
        </section>

        <!-- ========== 弹窗 Tab ========== -->
        <section v-if="activeTab === 'modals'">
          <h3 class="text-brand-400 font-semibold mb-2">阶段完成弹窗</h3>
          <div class="text-xs mb-2" :style="{ color: 'var(--text-muted)' }">先在学习 Tab 中把某个阶段进度拉到 100，然后点下方按钮触发弹窗（自动绕过 dedup guard）。</div>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="clearSessionStorage()">清除 sessionStorage</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="triggerStageComplete()">🎊 触发阶段完成</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="dismissStageComplete()">关闭弹窗</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">成就解锁动画</h3>
          <div class="text-xs mb-2" :style="{ color: 'var(--text-muted)' }">在成就 Tab 中先将某个成就锁定，再解锁即可触发粒子动画（BadgeCard 自动检测）。</div>
        </section>

        <!-- ========== 对话 Tab ========== -->
        <section v-if="activeTab === 'chat'">
          <h3 class="text-brand-400 font-semibold mb-2">模拟消息</h3>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="injectMockSession()">📨 注入 Mock 会话</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="injectStreamingMessage()">⚡ 模拟 Streaming</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="chatStore.sessions = []; chatStore.currentSessionId = null">🗑️ 清空对话</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">当前会话</h3>
          <div :style="{ color: 'var(--text-muted)' }">会话数: {{ chatStore.sessions.length }} | Stream状态: {{ chatStore.isStreaming ? '进行中' : '空闲' }}</div>
          <div class="mt-2 max-h-48 overflow-y-auto space-y-1">
            <div v-for="s in chatStore.sessions" :key="s.id" class="flex items-center gap-2 text-[10px]">
              <span :style="{ color: s.id === chatStore.currentSessionId ? 'var(--brand-400)' : 'var(--text-secondary)' }">{{ s.title }}</span>
              <span :style="{ color: 'var(--text-muted)' }">({{ s.messages.length }}条)</span>
              <button class="text-rose-500 ml-auto" @click="chatStore.sessions = chatStore.sessions.filter(x => x.id !== s.id)">删除</button>
            </div>
          </div>
        </section>

        <!-- ========== 苏格拉底 Tab ========== -->
        <section v-if="activeTab === 'socratic'">
          <h3 class="text-brand-400 font-semibold mb-2">服务状态</h3>
          <div class="flex items-center gap-2 mb-3">
            <span class="text-xs" :style="{ color: 'var(--text-muted)' }">API: {{ SOCRATIC_API }}</span>
            <button class="px-2.5 py-1 rounded-md text-xs border transition-all"
              :style="{ borderColor: 'rgba(99,102,241,0.12)', color: 'var(--text-secondary)' }"
              @click="checkHealth()">🔍 健康检查</button>
            <span class="text-xs font-medium px-1.5 py-0.5 rounded"
              :style="socraticHealthStatus === 'ok' ? { background: 'rgba(16,185,129,0.15)', color: '#10b981' } : socraticHealthStatus === 'error' ? { background: 'rgba(244,63,94,0.15)', color: '#f43f5e' } : socraticHealthStatus === 'degraded' ? { background: 'rgba(245,158,11,0.15)', color: '#f59e0b' } : { color: 'var(--text-muted)' }">
              {{ socraticHealthStatus === 'idle' ? '未检测' : socraticHealthStatus.toUpperCase() }}
            </span>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">面板状态</h3>
          <div class="grid grid-cols-3 gap-1.5 mb-3 text-[10px]">
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">可见: </span>
              <span :class="socraticStore.panelVisible ? 'text-mint-500' : 'text-gray-400'">{{ socraticStore.panelVisible ? '是' : '否' }}</span>
            </div>
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">展开: </span>
              <span :class="!socraticStore.panelCollapsed ? 'text-mint-500' : 'text-gray-400'">{{ !socraticStore.panelCollapsed ? '是' : '否' }}</span>
            </div>
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">生成: </span>
              <span :class="socraticStore.isGenerating ? 'text-brand-400' : 'text-gray-400'">{{ socraticStore.isGenerating ? '中' : '空闲' }}</span>
            </div>
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">计数: </span>
              <span :class="socraticStore.knowledgeQuestionCount >= 3 ? 'text-rose-500' : 'text-gray-400'">{{ socraticStore.knowledgeQuestionCount }} / 3</span>
            </div>
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">自动触发: </span>
              <span :class="socraticStore.shouldAutoTrigger ? 'text-rose-500' : 'text-gray-400'">{{ socraticStore.shouldAutoTrigger ? '待触发' : '否' }}</span>
            </div>
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">有内容: </span>
              <span :class="socraticStore.hasContent ? 'text-mint-500' : 'text-gray-400'">{{ socraticStore.hasContent ? '是' : '否' }}</span>
            </div>
            <div class="px-2 py-1 rounded" :style="{ background: 'rgba(15,23,42,0.6)' }">
              <span :style="{ color: 'var(--text-muted)' }">蒙版: </span>
              <span :class="socraticStore.showOverlay ? 'text-brand-400' : 'text-gray-400'">{{ socraticStore.showOverlay ? '显示中' : '隐藏' }}</span>
            </div>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">面板控制</h3>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="socraticStore.togglePanel()">🔘 切换面板</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="socraticStore.openPanel()">📂 展开面板</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="socraticStore.closePanel()">📁 收起面板</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="socraticStore.dismissPanel()">✕ 关闭面板</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">蒙版控制</h3>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(245,158,11,0.3); color: #f59e0b;"
              @click="showOverlayNow()">🖼️ 显示蒙版</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="socraticStore.dismissOverlay()">✕ 隐藏蒙版</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">快速测试问题</h3>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="quickSocraticTest('MapReduce的Shuffle过程是怎样的？')">🔹 Shuffle</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="quickSocraticTest('HDFS的读写流程是什么？')">🔹 HDFS</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="quickSocraticTest('Spark和MapReduce有什么区别？')">🔹 Spark vs MR</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="quickSocraticTest('CAP理论是什么？')">🔹 CAP</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">自定义问题</h3>
          <div class="flex gap-2 mb-3">
            <input
              v-model="socraticTestInput"
              type="text"
              placeholder="输入知识问题..."
              class="flex-1 px-2.5 py-1.5 rounded text-xs border-0 outline-none"
              :style="{ background: 'rgba(15,23,42,0.6)', color: 'var(--text-primary)' }"
              @keyup.enter="quickSocraticTest(socraticTestInput)"
            />
            <button class="px-3 py-1.5 rounded-md text-xs font-medium text-white transition-all hover:opacity-90 disabled:opacity-50 shrink-0"
              style="background: linear-gradient(135deg, #f59e0b, #d97706);"
              :disabled="!socraticTestInput.trim() || socraticStore.isGenerating"
              @click="quickSocraticTest(socraticTestInput)">
              {{ socraticStore.isGenerating ? '生成中...' : '生成反思' }}
            </button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">模拟连续提问 (测试 auto-trigger)</h3>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
              @click="simulateKnowledgeQuestion()">📊 模拟知识问题 +1</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="socraticStore.resetCounter()">🔄 重置计数</button>
          </div>

          <!-- 当前问题 -->
          <div v-if="socraticStore.currentQuestion" class="mb-3">
            <h3 class="text-brand-400 font-semibold mb-1">当前问题</h3>
            <p class="text-xs px-2.5 py-2 rounded" style="background: rgba(15,23,42,0.6); color: var(--text-secondary);">{{ socraticStore.currentQuestion }}</p>
          </div>

          <!-- 生成结果 — 三段式 -->
          <div v-if="socraticStore.hasContent">
            <h3 class="text-brand-400 font-semibold mb-2">生成结果</h3>
            <div class="space-y-2 max-h-64 overflow-y-auto">
              <div v-if="socraticStore.questionsSection" class="p-2.5 rounded-lg" style="background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.15);">
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-sm">💬</span>
                  <span class="text-[10px] font-semibold" style="color: #6366f1;">引导性问题</span>
                </div>
                <p class="text-xs leading-relaxed whitespace-pre-line" style="color: var(--text-primary);">{{ socraticStore.questionsSection }}</p>
              </div>
              <div v-if="socraticStore.assumptionsSection" class="p-2.5 rounded-lg" style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.15);">
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-sm">⚡</span>
                  <span class="text-[10px] font-semibold" style="color: #f59e0b;">关键假设检验</span>
                </div>
                <p class="text-xs leading-relaxed whitespace-pre-line" style="color: var(--text-primary);">{{ socraticStore.assumptionsSection }}</p>
              </div>
              <div v-if="socraticStore.reflectionSection" class="p-2.5 rounded-lg" style="background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.15);">
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-sm">✨</span>
                  <span class="text-[10px] font-semibold" style="color: #10b981;">一句话反思</span>
                </div>
                <p class="text-xs leading-relaxed italic font-medium" style="color: var(--text-primary);">{{ socraticStore.reflectionSection }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- ========== 系统 Tab ========== -->
        <section v-if="activeTab === 'system'">
          <h3 class="text-brand-400 font-semibold mb-2">存储清理</h3>
          <div class="flex gap-1.5 mb-3 flex-wrap">
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="clearLocalStorage()">🗑️ 清空 localStorage</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="clearSessionStorage()">🗑️ 清空 sessionStorage</button>
            <button class="px-2.5 py-1 rounded-md text-xs border" style="border-color: rgba(244,63,94,0.3); color: var(--rose-500);"
              @click="nukeAndRefresh()">💣 全部清除+刷新</button>
          </div>

          <h3 class="text-brand-400 font-semibold mb-2">Store 状态快照</h3>
          <button class="px-2.5 py-1 rounded-md text-xs border mb-2" style="border-color: rgba(99,102,241,0.12); color: var(--text-secondary);"
            @click="dumpState()">📋 打印 Store 状态到控制台</button>
        </section>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { usePetStore, petConfigs, type PetState } from '@/stores/pet'
import { useLearningStore } from '@/stores/learning'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { useSocraticStore } from '@/stores/socratic'
import { checkSocraticHealth } from '@/api/socratic'
import { useThemeStore } from '@/stores/theme'
import iconSetUp from '@/assets/icons/jian/set-up-svgrepo-com.svg'
import iconMoon from '@/assets/icons/star/moon-svgrepo-com.svg'
import iconTrophy from '@/assets/icons/blue/trophy-svgrepo-com.svg'
import iconPicture from '@/assets/icons/jian/picture-svgrepo-com.svg'
import iconShortMessage from '@/assets/icons/fang/short-message-svgrepo-com.svg'

const petStore = usePetStore()
const learningStore = useLearningStore()
const userStore = useUserStore()
const chatStore = useChatStore()
const socraticStore = useSocraticStore()
const themeStore = useThemeStore()

const isOpen = ref(false)
const activeTab = ref('pet')
const petMinutesInput = ref(30)
const socraticTestInput = ref('')
const socraticHealthStatus = ref<'idle' | 'ok' | 'degraded' | 'error'>('idle')

const tabs = [
  { key: 'pet', emoji: '🐱', label: '宠物' },
  { key: 'learning', emoji: '📚', label: '学习' },
  { key: 'achievements', svg: iconTrophy, label: '成就' },
  { key: 'theme', svg: iconPicture, label: '主题' },
  { key: 'modals', emoji: '🎊', label: '弹窗' },
  { key: 'chat', svg: iconShortMessage, label: '对话' },
  { key: 'socratic', emoji: '🏛️', label: '苏格拉底' },
  { key: 'system', svg: iconSetUp, label: '系统' },
]

const petStates: PetState[] = ['idle', 'active', 'alert', 'celebrate', 'sleeping']

function emojiFor(s: PetState): string {
  const map: Record<PetState, string> = { idle: '😺', active: '🎯', alert: '⚠️', celebrate: '🎉', sleeping: '😴' }
  return map[s] || '🐱'
}

function masterAllTopics() {
  for (const t of learningStore.topicMasteryList) {
    t.masteryLevel = 1.0
    t.status = 'mastered'
  }
}

function triggerStageComplete() {
  if (!learningStore.currentPath) return
  for (const stage of learningStore.currentPath.stages) {
    window.sessionStorage.removeItem(`stage_celebrated_${stage.stageId}`)
  }
  const completed = learningStore.currentPath.stages.find(s => s.status === 'completed')
  if (!completed) {
    showAlert('没有 completed 状态阶段！请先在"学习"Tab 把某个阶段进度拉到 100。')
    return
  }
  showAlert(`阶段 "${completed.title}" 已设为完成。请导航到 Dashboard 页面查看弹窗。\n如果弹窗不显示，请手动调用 checkStageMilestone()。`)
}

function dismissStageComplete() {
  showAlert('弹窗由 Dashboard.vue 的 showStageComplete ref 控制。关闭弹窗需要在该页面操作。')
}

function injectMockSession() {
  if (!chatStore.getCurrentSession()) chatStore.createSession()
  const session = chatStore.getCurrentSession()
  if (!session) return
  session.messages.push(
    { id: `mock_u_${Date.now()}`, role: 'user', content: '什么是 HDFS？', timestamp: Date.now() - 60000 },
    { id: `mock_a_${Date.now()}`, role: 'assistant', content: '**HDFS**（Hadoop Distributed File System）是 Hadoop 的分布式文件系统，核心特点：\n\n1. **高容错性** — 数据自动多副本（默认3份）\n2. **高吞吐量** — 适合批量处理大文件\n3. **主从架构** — NameNode 管理元数据，DataNode 存储数据块\n\n默认块大小 **128MB**，适合"一次写入、多次读取"的场景。', agentId: 'document', timestamp: Date.now() - 30000, topics: ['HDFS分布式文件系统', 'Hadoop概述'] },
  )
  session.title = 'Mock: HDFS 问答'
}

function injectStreamingMessage() {
  if (!chatStore.getCurrentSession()) chatStore.createSession()
  chatStore.isStreaming = true
  const session = chatStore.getCurrentSession()
  if (!session) return
  const msgId = `mock_stream_${Date.now()}`
  session.messages.push({ id: msgId, role: 'assistant', content: '⏳ 正在生成...', agentId: 'qa', timestamp: Date.now(), isStreaming: true })
  // Simulate chunks
  const chunks = ['Spark ', '是', '一个', '**快速**', '的', '大数据', '处理引擎', '。', '\n\n', '它支持', 'Java', '、', 'Scala', '、', 'Python', '和', '**R**', '语言。']
  let i = 0
  const timer = setInterval(() => {
    const msg = session.messages.find(m => m.id === msgId)
    if (!msg || i >= chunks.length) {
      clearInterval(timer)
      chatStore.isStreaming = false
      if (msg) { msg.isStreaming = false; msg.content = msg.content.replace('⏳ 正在生成...', '') }
      return
    }
    if (msg.content === '⏳ 正在生成...') msg.content = ''
    msg.content += chunks[i]
    i++
  }, 200)
}

function dumpState() {
  console.group('🛠️ Debug Panel — Store 状态快照')
  console.log('Pet:', { state: petStore.currentState, pet: petStore.currentPet, pos: petStore.position, size: petStore.size, learningMin: petStore.learningMinutes })
  console.log('Learning:', { streak: learningStore.streakDays, todayMin: learningStore.todayMinutes, curiosity: learningStore.curiosityIndex, flow: learningStore.flowState, path: learningStore.currentPath, topics: learningStore.topicMasteryList.length })
  console.log('User:', { profile: userStore.profile, achievements: userStore.achievements.map(a => ({ name: a.name, unlocked: a.isUnlocked })) })
  console.log('Theme:', themeStore.mode)
  console.log('Chat:', { sessions: chatStore.sessions.length, streaming: chatStore.isStreaming })
  console.groupEnd()
}

function customBubble() {
  const text = window.prompt('气泡文字:', '测试气泡~ 🐱') || '测试气泡~ 🐱'
  petStore.showBubble({ text, duration: 0 })
}

function showAlert(msg: string) { window.alert(msg) }

// ── 苏格拉底测试函数 ──
const SOCRATIC_API = import.meta.env.VITE_SOCRATIC_API_URL || 'http://localhost:8001'

async function checkHealth() {
  socraticHealthStatus.value = 'idle'
  try {
    const ok = await checkSocraticHealth()
    socraticHealthStatus.value = ok ? 'ok' : 'degraded'
  } catch {
    socraticHealthStatus.value = 'error'
  }
}

async function quickSocraticTest(question: string) {
  const q = question.trim()
  if (!q || socraticStore.isGenerating) return
  socraticTestInput.value = ''
  // 使用 onKnowledgeQuestionAsked → 自动 generate → 完成后弹出蒙版
  socraticStore.onKnowledgeQuestionAsked(q)
}

function showOverlayNow() {
  // 确保 hasContent 为 true，直接显示蒙版
  if (!socraticStore.hasContent) {
    socraticStore.rawText = '（调试模式 — 蒙版测试）'
    socraticStore.currentQuestion = '调试测试问题'
  }
  socraticStore.showOverlay = true
}

function simulateKnowledgeQuestion() {
  const demoQs = [
    '什么是HDFS的联邦模式？',
    'Kafka如何保证消息不丢失？',
    'Spark的内存管理机制是怎样的？',
    'Flink的Checkpoint原理是什么？',
    '数据库索引为什么用B+树？',
  ]
  const q = demoQs[socraticStore.knowledgeQuestionCount % demoQs.length]
  socraticStore.onKnowledgeQuestionAsked(q)
}

function clearLocalStorage() { window.localStorage.clear(); showAlert('localStorage 已清空') }
function clearSessionStorage() { window.sessionStorage.clear(); showAlert('sessionStorage 已清空') }
function nukeAndRefresh() { window.localStorage.clear(); window.sessionStorage.clear(); window.location.reload() }
</script>

<style scoped>
.debug-gear-icon {
  width: 1.25em;
  height: 1.25em;
  display: inline-block;
  filter: brightness(0) saturate(100%) invert(36%) sepia(89%) saturate(1545%) hue-rotate(225deg) brightness(99%) contrast(96%);
}

.debug-title-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
}

.debug-tab-icon {
  width: 0.875em;
  height: 0.875em;
  display: inline-block;
  flex-shrink: 0;
}

.debug-theme-icon {
  width: 0.875em;
  height: 0.875em;
  display: inline-block;
  flex-shrink: 0;
}

.debug-slide-enter-active { transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.debug-slide-leave-active { transition: transform 0.2s ease-in; }
.debug-slide-enter-from,
.debug-slide-leave-to { transform: translateX(100%); }

input[type="range"] {
  -webkit-appearance: none;
  height: 4px;
  border-radius: 2px;
  background: rgba(99, 102, 241, 0.2);
  outline: none;
  cursor: pointer;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--brand-500);
  cursor: pointer;
}
</style>
