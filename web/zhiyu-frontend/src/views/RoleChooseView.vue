<template>
  <div class="choose-page">
    <!-- 品牌条 -->
    <header class="choose-brand">
      <div class="brand-hex">
        <svg viewBox="0 0 56 56" class="w-full h-full">
          <polygon points="28,2 52,16 52,40 28,54 4,40 4,16" fill="url(#hexGrad)" stroke="#7c8cf8" stroke-width="1.5"/>
          <defs><linearGradient id="hexGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#4f46e5"/><stop offset="100%" stop-color="#818cf8"/></linearGradient></defs>
        </svg>
        <span class="absolute inset-0 flex items-center justify-center text-white font-bold text-sm">职</span>
      </div>
      <div>
        <h1 class="text-xl font-bold tracking-wide uppercase choose-title">职域智联</h1>
        <p class="font-mono text-[10px] tracking-[0.3em] choose-muted">SELECT WORKSPACE · 选择工作台</p>
      </div>
    </header>

    <!-- 双卡对开 -->
    <main class="choose-grid">
      <!-- ── 个人侧 · 深空舰桥工业风格 ── -->
      <div
        class="choose-card personal-card"
        role="button"
        tabindex="0"
        :aria-label="'进入个人工作台'"
        @click="pick('personal')"
        @keydown.enter="pick('personal')"
      >
        <div class="rivet" style="top:10px;left:10px"></div>
        <div class="rivet" style="top:10px;right:10px"></div>
        <div class="rivet" style="bottom:10px;left:10px"></div>
        <div class="rivet" style="bottom:10px;right:10px"></div>

        <div class="personal-inner">
          <div class="flex items-center justify-between mb-4">
            <span class="tag-plate" style="color:#818cf8;border-color:#6366f1">PERSONAL · 个人侧</span>
            <span class="data-segment" style="color:#34d399">PER</span>
          </div>

          <h2 class="personal-title">职业发展台</h2>
          <p class="personal-sub">面向个人专业者 · 职业规划与能力成长</p>

          <ul class="personal-feats">
            <li><span class="feat-dot" style="background:#818cf8"></span>技能画像 · 人岗匹配</li>
            <li><span class="feat-dot" style="background:#34d399"></span>学习路径 · 技能保鲜</li>
            <li><span class="feat-dot" style="background:#22d3ee"></span>转行分析 · 成长轨迹</li>
            <li><span class="feat-dot" style="background:#a78bfa"></span>信号光谱 · 演化剧场 · AI 顾问</li>
          </ul>

          <div class="personal-cta">
            <span class="data-segment" style="color:#818cf8">进入个人工作台</span>
            <span class="cta-arrow">→</span>
          </div>
        </div>
      </div>

      <!-- ── 企业侧 · 蓝皮书·权威纸面 ── -->
      <div
        class="choose-card enterprise-card ent-shell"
        data-side="enterprise"
        role="button"
        tabindex="0"
        :aria-label="'进入企业工作台'"
        @click="pick('enterprise')"
        @keydown.enter="pick('enterprise')"
      >
        <div class="doc-masthead px-5 py-4">
          <div class="relative z-[1] flex items-center justify-between gap-3">
            <div>
              <span class="seal-chip" style="color:#fff;border-color:#fff">● 企业侧</span>
              <h2 class="ent-title-serif text-lg font-bold" style="color:#fff;margin-top:4px">岗位标准智能管理台</h2>
              <p class="text-[10px] font-mono tracking-widest" style="color:rgba(255,255,255,0.55);margin-top:2px">ENTERPRISE · HR / 管理者</p>
            </div>
            <span class="seal-chip seal-chip--dim" style="color:rgba(255,255,255,0.6);border-color:rgba(255,255,255,0.35)">ENT</span>
          </div>
        </div>

        <div class="enterprise-body">
          <p class="enterprise-sub">面向人事与管理者 · 岗位标准制定与人才决策</p>

          <div class="leader-row"><span class="label">岗位标准库</span><span class="dots"></span><span class="val" style="color:var(--ent-navy)">51 岗位</span></div>
          <div class="leader-row"><span class="label">JD 质量诊断</span><span class="dots"></span><span class="val" style="color:var(--ent-navy)">9041 条</span></div>
          <div class="leader-row"><span class="label">团队盘点</span><span class="dots"></span><span class="val" style="color:var(--ent-navy)">技能缺口</span></div>
          <div class="leader-row"><span class="label">需求预测</span><span class="dots"></span><span class="val" style="color:var(--ent-navy)">市场趋势</span></div>

          <div class="mt-5 flex items-center justify-between" style="border-top:1px solid var(--ent-rule);padding-top:14px">
            <span class="footnote" style="margin:0">数据截止 2026-08 · 蓝皮书 v1.0</span>
            <span class="ent-btn ent-btn--coral" style="cursor:pointer">进入企业工作台 →</span>
          </div>
        </div>
      </div>
    </main>

    <footer class="choose-foot">选择即进入体验 · 无需登录 · 进入后可通过顶部「切换工作台」随时更换</footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const appStore = useAppStore()
const themeStore = useThemeStore()

function pick(r: 'personal' | 'enterprise') {
  appStore.switchRole(r)
  themeStore.setPalette(r === 'personal' ? 'warm' : 'indigo')
  router.push(r === 'personal' ? '/personal' : '/enterprise')
}
</script>

<style scoped>
/* 中性深色底：选边页不随当前主题 mode / data-side 走，保证双卡各自成立 */
.choose-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  padding: 32px 20px;
  background:
    radial-gradient(900px 480px at 12% -8%, rgba(99, 102, 241, 0.16), transparent 60%),
    radial-gradient(820px 420px at 92% 108%, rgba(200, 92, 86, 0.14), transparent 55%),
    linear-gradient(180deg, #0a0f22 0%, #0e1329 55%, #0a0e1f 100%);
}

.choose-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-hex {
  position: relative;
  width: 44px;
  height: 44px;
  filter: drop-shadow(0 0 10px rgba(129, 140, 248, 0.35));
}
.choose-title { color: #eef1ff; }
.choose-muted { color: #7d89b8; }

.choose-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
  width: min(1080px, 100%);
}
@media (min-width: 1024px) {
  .choose-grid { grid-template-columns: 1fr 1fr; }
}

.choose-card {
  position: relative;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  outline: none;
}
.choose-card:hover,
.choose-card:focus-visible { transform: translateY(-6px) scale(1.01); }

/* ── 个人卡 · 深空舰桥 ── */
.personal-card {
  border: 1px solid #39456e;
  box-shadow:
    0 0 0 1px rgba(99, 102, 241, 0.12),
    0 0 24px rgba(99, 102, 241, 0.08),
    inset 0 0 40px rgba(99, 102, 241, 0.04);
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 14px 100%, 0 calc(100% - 14px));
  overflow: hidden;
}
.personal-card::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 22px 22px;
}
.personal-card::after {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 1px;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(129, 140, 248, 0.9), transparent);
  animation: choose-scan 4.5s linear infinite;
}
.personal-inner {
  position: relative;
  z-index: 1;
  padding: 26px 24px;
  min-height: 340px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(165deg, #121a3a 0%, #1b2247 48%, #131a38 100%);
}
.personal-title { color: #eef1ff; font-size: 22px; font-weight: 800; letter-spacing: 0.06em; }
.personal-sub { color: #8a94c2; font-size: 12px; margin-top: 4px; }
.personal-feats {
  margin-top: 20px;
  display: grid;
  gap: 10px;
  list-style: none;
}
.personal-feats li {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #c3cbe8;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}
.feat-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px currentColor;
}
.personal-cta {
  margin-top: auto;
  padding-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px dashed #39456e;
}
.cta-arrow { color: #818cf8; font-size: 16px; }

/* ── 企业卡 · 蓝皮书 ── */
.enterprise-card {
  position: relative;
  border-radius: 2px;
  box-shadow:
    0 1px 2px rgba(0, 9, 76, 0.05),
    0 10px 30px rgba(0, 9, 76, 0.10);
}
.enterprise-card:hover,
.enterprise-card:focus-visible {
  box-shadow:
    0 1px 2px rgba(0, 9, 76, 0.05),
    0 16px 40px rgba(0, 9, 76, 0.18);
}
.enterprise-body {
  padding: 18px 20px 20px;
  background: var(--ent-card);
}
.enterprise-sub {
  color: var(--ent-ink-muted);
  font-size: 12px;
  margin-bottom: 16px;
}

@keyframes choose-scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.choose-foot {
  color: #6b76a3;
  font-size: 11px;
  font-family: 'Courier New', monospace;
  letter-spacing: 0.08em;
  text-align: center;
}
</style>
