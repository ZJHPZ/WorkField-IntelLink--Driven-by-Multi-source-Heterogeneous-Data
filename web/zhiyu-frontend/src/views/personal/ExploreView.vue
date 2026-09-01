<template>
  <div class="space-y-4">
    <!-- ═══════════════════════ 舰桥指挥台 ═══════════════════════ -->
    <div class="panel-neon holo-overlay scan-line-fast p-0 overflow-hidden shadow-deep">
      <div class="relative z-[3] p-4 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 panel-industrial flex items-center justify-center">
            <svg class="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2 mb-0.5">
              <span class="tag-plate">EXPLORER</span>
              <span class="w-1.5 h-1.5 rounded-full bg-mint-500" style="box-shadow:0 0 6px var(--mint-500)"></span>
            </div>
            <h1 class="text-sm font-bold tracking-tight" style="color:var(--text-primary)">岗位探索</h1>
          </div>
        </div>
        <button v-if="activeModule" @click="collapseModule"
          class="nav-chip text-[9px] tracking-widest flex items-center gap-1.5">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
          返回模组选择
        </button>
      </div>
    </div>

    <!-- ═══════════════════════ 模组选择区 ═══════════════════════ -->
    <div class="relative" style="min-height: 520px">

      <!-- ── 模组卡片（未展开） ── -->
      <transition name="module-grid">
        <div v-if="!activeModule" class="grid grid-cols-1 lg:grid-cols-12 gap-3" style="height: 520px">

          <!-- 模组1: 岗位库（大卡，占5列） -->
          <div @click="expandModule('positions')"
            class="lg:col-span-5 panel-industrial shadow-deep cursor-pointer group relative overflow-hidden transition-all duration-300 hover:scale-[1.01]"
            style="animation: module-appear 0.4s ease-out both">
            <div class="rivet" style="top:8px;left:8px"></div>
            <div class="rivet" style="top:8px;right:8px"></div>
            <div class="rivet" style="bottom:8px;left:8px"></div>
            <div class="rivet" style="bottom:8px;right:8px"></div>
            <!-- 背景网格 -->
            <div class="absolute inset-0 opacity-10" style="background-image:linear-gradient(var(--brand-500) 1px,transparent 1px),linear-gradient(90deg,var(--brand-500) 1px,transparent 1px);background-size:20px 20px"></div>
            <div class="relative z-[1] p-5 h-full flex flex-col">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <span class="data-segment text-xl text-brand-500">01</span>
                  <span class="tag-plate">DATABASE</span>
                </div>
                <span class="w-2 h-2 rounded-full bg-brand-500 group-hover:scale-150 transition-transform" style="box-shadow:0 0 8px var(--brand-500)"></span>
              </div>
              <h3 class="text-lg font-bold tracking-wide mb-1" style="color:var(--text-primary)">岗位库</h3>
              <p class="text-[10px] tracking-wider mb-4" style="color:var(--text-muted)">浏览 · 筛选 · 选择目标岗位</p>
              <!-- 预览：3 个岗位卡片 -->
              <div class="flex-1 space-y-2">
                <div v-for="pos in previewPositions" :key="pos.name"
                  class="flex items-center gap-3 px-3 py-2 transition-all"
                  style="background:var(--bg-secondary);border-left:2px solid var(--brand-500)">
                  <span class="text-[10px] font-bold flex-1" style="color:var(--text-primary)">{{ pos.name }}</span>
                  <span class="text-[9px] font-mono" style="color:var(--mint-500)">{{ pos.match }}%</span>
                  <span class="text-[8px]" style="color:var(--text-muted)">{{ pos.salary }}</span>
                </div>
              </div>
              <div class="mt-3 pt-2 flex items-center justify-between" style="border-top:1px dashed var(--border-color)">
                <span class="data-segment text-sm text-brand-500">42</span>
                <span class="text-[8px] font-mono tracking-widest" style="color:var(--text-muted)">POSITIONS</span>
              </div>
            </div>
          </div>

          <!-- 右侧 2×2 网格 -->
          <div class="lg:col-span-7 grid grid-cols-2 gap-3">

            <!-- 模组2: 岗位演化 -->
            <div @click="expandModule('evolution')"
              class="panel-bridge shadow-deep cursor-pointer group relative overflow-hidden transition-all duration-300 hover:scale-[1.01]"
              style="animation: module-appear 0.4s ease-out 0.06s both">
              <div class="rivet" style="top:6px;left:6px"></div>
              <div class="relative z-[1] p-4 h-full flex flex-col">
                <div class="flex items-center justify-between mb-2">
                  <span class="data-segment text-lg text-cyan-500">02</span>
                  <span class="w-2 h-2 rounded-full bg-cyan-500 group-hover:scale-150 transition-transform" style="box-shadow:0 0 6px var(--cyan-500)"></span>
                </div>
                <h3 class="text-sm font-bold mb-1" style="color:var(--text-primary)">岗位演化</h3>
                <p class="text-[9px] mb-3" style="color:var(--text-muted)">能力要求变化 · 时间线追踪</p>
                <!-- 迷你时间线预览 -->
                <div class="flex-1 space-y-1">
                  <div v-for="ev in previewEvolution" :key="ev.date" class="flex items-center gap-2">
                    <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :style="{background:ev.color}"></span>
                    <span class="text-[8px] font-mono w-12 flex-shrink-0" style="color:var(--text-muted)">{{ ev.date }}</span>
                    <span class="text-[9px] truncate" :style="{color:ev.color}">{{ ev.label }}</span>
                  </div>
                </div>
                <div class="mt-auto pt-2 flex items-center justify-between" style="border-top:1px dashed var(--border-color)">
                  <span class="data-segment text-sm text-cyan-500">12</span>
                  <span class="text-[8px] tracking-widest" style="color:var(--text-muted)">CHANGES</span>
                </div>
              </div>
            </div>

            <!-- 模组3: 新岗发现 -->
            <div @click="expandModule('discovery')"
              class="panel-neon shadow-deep cursor-pointer group relative overflow-hidden transition-all duration-300 hover:scale-[1.01]"
              style="animation: module-appear 0.4s ease-out 0.12s both">
              <div class="rivet" style="top:6px;left:6px"></div>
              <div class="holo-overlay absolute inset-0 z-0 opacity-10"></div>
              <div class="relative z-[3] p-4 h-full flex flex-col">
                <div class="flex items-center justify-between mb-2">
                  <span class="data-segment text-lg" style="color:#a855f7">03</span>
                  <span class="w-2 h-2 rounded-full group-hover:scale-150 transition-transform" style="background:#a855f7;box-shadow:0 0 6px #a855f7"></span>
                </div>
                <h3 class="text-sm font-bold mb-1" style="color:var(--text-primary)">新岗发现</h3>
                <p class="text-[9px] mb-3" style="color:var(--text-muted)">AI 辩论 · 候选岗位验证</p>
                <!-- 预览：发现结果 -->
                <div class="flex-1 space-y-1.5">
                  <div v-for="r in previewDiscovery" :key="r.name" class="flex items-center gap-2 px-2 py-1.5" style="background:var(--bg-secondary)">
                    <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :style="{background:r.color}"></span>
                    <span class="text-[9px] flex-1" style="color:var(--text-primary)">{{ r.name }}</span>
                    <span class="text-[8px] font-mono px-1 py-0.5" :style="{color:r.color,background:r.color+'15',border:'1px solid '+r.color+'30'}">{{ r.verdict }}</span>
                  </div>
                </div>
                <div class="mt-auto pt-2 flex items-center justify-between" style="border-top:1px dashed var(--border-color)">
                  <span class="data-segment text-sm" style="color:#a855f7">5</span>
                  <span class="text-[8px] tracking-widest" style="color:var(--text-muted)">CANDIDATES</span>
                </div>
              </div>
            </div>

            <!-- 模组4: 全景图谱 -->
            <div @click="expandModule('graph')"
              class="panel-circuit shadow-deep cursor-pointer group relative overflow-hidden transition-all duration-300 hover:scale-[1.01]"
              style="animation: module-appear 0.4s ease-out 0.18s both">
              <div class="rivet" style="top:6px;left:6px"></div>
              <div class="absolute inset-0 opacity-5" style="background-image:radial-gradient(circle,var(--mint-500) 1px,transparent 1px);background-size:12px 12px"></div>
              <div class="relative z-[1] p-4 h-full flex flex-col">
                <div class="flex items-center justify-between mb-2">
                  <span class="data-segment text-lg text-mint-500">04</span>
                  <span class="w-2 h-2 rounded-full bg-mint-500 group-hover:scale-150 transition-transform" style="box-shadow:0 0 6px var(--mint-500)"></span>
                </div>
                <h3 class="text-sm font-bold mb-1" style="color:var(--text-primary)">全景图谱</h3>
                <p class="text-[9px] mb-3" style="color:var(--text-muted)">技能点级颗粒度 · 交互可视化</p>
                <!-- 迷你图谱预览 -->
                <div class="flex-1 flex items-center justify-center">
                  <svg viewBox="0 0 120 80" class="w-full h-full opacity-30">
                    <circle cx="60" cy="40" r="3" fill="var(--mint-500)"/>
                    <circle cx="30" cy="20" r="2" fill="var(--brand-500)"/>
                    <circle cx="90" cy="25" r="2" fill="var(--brand-500)"/>
                    <circle cx="25" cy="55" r="2" fill="var(--cyan-500)"/>
                    <circle cx="85" cy="60" r="2" fill="var(--cyan-500)"/>
                    <circle cx="50" cy="15" r="1.5" fill="var(--mint-500)"/>
                    <circle cx="75" cy="50" r="1.5" fill="var(--mint-500)"/>
                    <line x1="60" y1="40" x2="30" y2="20" stroke="var(--brand-500)" stroke-width="0.5" opacity="0.4"/>
                    <line x1="60" y1="40" x2="90" y2="25" stroke="var(--brand-500)" stroke-width="0.5" opacity="0.4"/>
                    <line x1="60" y1="40" x2="25" y2="55" stroke="var(--cyan-500)" stroke-width="0.5" opacity="0.4"/>
                    <line x1="60" y1="40" x2="85" y2="60" stroke="var(--cyan-500)" stroke-width="0.5" opacity="0.4"/>
                    <line x1="30" y1="20" x2="50" y2="15" stroke="var(--mint-500)" stroke-width="0.3" opacity="0.3"/>
                    <line x1="90" y1="25" x2="75" y2="50" stroke="var(--mint-500)" stroke-width="0.3" opacity="0.3"/>
                  </svg>
                </div>
                <div class="mt-auto pt-2 flex items-center justify-between" style="border-top:1px dashed var(--border-color)">
                  <span class="data-segment text-sm text-mint-500">160</span>
                  <span class="text-[8px] tracking-widest" style="color:var(--text-muted)">NODES</span>
                </div>
              </div>
            </div>

            <!-- 模组5: 人才需求 -->
            <div @click="expandModule('talent')"
              class="panel-hazard shadow-deep cursor-pointer group relative overflow-hidden transition-all duration-300 hover:scale-[1.01]"
              style="animation: module-appear 0.4s ease-out 0.24s both">
              <div class="rivet" style="top:6px;left:6px"></div>
              <div class="relative z-[1] p-4 h-full flex flex-col">
                <div class="flex items-center justify-between mb-2">
                  <span class="data-segment text-lg" style="color:#f59e0b">05</span>
                  <span class="w-2 h-2 rounded-full group-hover:scale-150 transition-transform" style="background:#f59e0b;box-shadow:0 0 6px #f59e0b"></span>
                </div>
                <h3 class="text-sm font-bold mb-1" style="color:var(--text-primary)">人才需求</h3>
                <p class="text-[9px] mb-3" style="color:var(--text-muted)">新兴/衰退排行 · 薪资趋势</p>
                <!-- 预览：ticker 风格 -->
                <div class="flex-1 space-y-1">
                  <div v-for="s in previewTicker" :key="s.direction + s.name" class="flex items-center gap-2">
                    <span class="text-[9px] flex-1 font-mono" style="color:var(--text-primary)">{{ s.name }}</span>
                    <span class="data-segment text-[10px]" :style="{color:s.direction==='up'?'var(--mint-500)':'var(--rose-500)'}">{{ s.direction==='up' ? '▲' : '▼' }}{{ s.value }}</span>
                  </div>
                </div>
                <div class="mt-auto pt-2 flex items-center justify-between" style="border-top:1px dashed var(--border-color)">
                  <span class="data-segment text-sm" style="color:#f59e0b">21</span>
                  <span class="text-[8px] tracking-widest" style="color:var(--text-muted)">SKILLS</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════ 展开的子模块 ═══════════════════════ -->
      <transition name="module-expand">
        <div v-if="activeModule" class="module-content">

          <!-- ── 岗位库 ── -->
          <div v-if="activeModule === 'positions'" class="space-y-3">
            <div class="panel-bridge p-3 shadow-deep flex items-center gap-3 flex-wrap">
              <span class="text-[8px] tracking-widest" style="color:var(--text-muted)">STACK:</span>
              <button v-for="stack in techStacks" :key="stack" @click="toggleFilter(stack)"
                class="text-[9px] px-2.5 py-1 font-mono transition-all"
                :style="activeFilters.includes(stack) ? {background:'var(--brand-500)',color:'white'} : {background:'var(--bg-secondary)',color:'var(--text-muted)',border:'1px solid var(--border-color)'}">
                {{ stack }}
              </button>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
              <div class="lg:col-span-2 space-y-1.5 overflow-y-auto pr-1" style="max-height:460px;scrollbar-width:thin;scrollbar-color:var(--brand-500) transparent">
                <div v-for="(pos, i) in filteredPositions" :key="pos.id" @click="selectPosition(pos)"
                  class="panel-asymmetric p-3 cursor-pointer transition-all"
                  :class="selectedPosition?.id === pos.id ? 'shadow-deep' : ''"
                  :style="selectedPosition?.id === pos.id ? {borderLeft:'3px solid var(--brand-500)'} : {}">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="data-segment text-[8px]" style="color:var(--text-muted)">{{ String(i+1).padStart(2,'0') }}</span>
                    <span class="text-[11px] font-bold min-w-0 truncate" style="color:var(--text-primary)">{{ pos.name }}</span>
                    <span class="tag-plate text-[7px]" :style="{color:pos.type==='新兴'?'var(--cyan-400)':'var(--text-muted)',borderColor:pos.type==='新兴'?'var(--cyan-500)':'var(--border-color)'}">{{ pos.type }}</span>
                    <button @click.stop="toggleFavoritePosition(pos)"
                      class="ml-auto shrink-0 w-6 h-6 flex items-center justify-center transition-all"
                      :title="isFavorite(pos.id) ? '取消收藏' : '收藏该岗位'"
                      :style="isFavorite(pos.id)
                        ? { color:'#facc15', textShadow:'0 0 8px rgba(250,204,21,0.7)', transform:'scale(1.08)' }
                        : { color:'var(--text-muted)', opacity:'0.55' }">
                      <svg class="w-4 h-4" viewBox="0 0 24 24" :fill="isFavorite(pos.id)?'currentColor':'none'" stroke="currentColor" stroke-width="1.6"><path stroke-linecap="round" stroke-linejoin="round" :d="STAR_PATH"/></svg>
                    </button>
                  </div>
                  <div class="flex items-center gap-3 text-[8px]" style="color:var(--text-muted)">
                    <span>{{ pos.skillCount }} skills</span><span>{{ pos.salary }}</span><span>{{ pos.techStack }}</span>
                  </div>
                </div>
                <!-- 空态：筛选后无匹配岗位时给出反馈，而不是静默空白 -->
                <div v-if="!filteredPositions.length" class="flex flex-col items-center justify-center py-12 text-center">
                  <div class="data-segment text-2xl mb-2" style="color:var(--text-muted)">00</div>
                  <p class="text-[10px] tracking-wider mb-3" style="color:var(--text-muted)">当前筛选下暂无匹配岗位</p>
                  <button @click="activeFilters = []" class="px-3 py-1 text-[9px] font-mono font-bold tracking-wider uppercase transition-colors" style="background:var(--bg-secondary);color:var(--brand-400);border:1px solid var(--border-color)">清除筛选</button>
                </div>
              </div>
              <div class="lg:col-span-3">
                <div v-if="selectedPosition" class="panel-industrial panel-circuit p-5 shadow-deep relative">
                  <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
                  <div class="relative z-[1]">
                    <div class="flex items-center justify-between mb-3">
                      <div><span class="tag-plate" :style="{color:selectedPosition.type==='新兴'?'var(--cyan-400)':'var(--brand-400)',borderColor:selectedPosition.type==='新兴'?'var(--cyan-500)':'var(--brand-500)'}">{{ selectedPosition.type }}</span></div>
                      <div class="data-segment text-2xl text-brand-500">{{ selectedPosition.matchRate }}%</div>
                    </div>
                    <div class="flex items-center justify-between gap-2 mb-1">
                      <h2 class="text-lg font-bold min-w-0 truncate" style="color:var(--text-primary)">{{ selectedPosition.name }}</h2>
                      <button @click="toggleFavoritePosition(selectedPosition)"
                        class="shrink-0 flex items-center gap-1.5 px-2.5 py-1 text-[9px] font-mono font-bold tracking-wider uppercase transition-all"
                        :style="isFavorite(selectedPosition.id)
                          ? { background:'color-mix(in srgb, #eab308 14%, transparent)', color:'#facc15', border:'1px solid color-mix(in srgb, #eab308 40%, transparent)', boxShadow:'0 0 8px color-mix(in srgb, #eab308 25%, transparent)' }
                          : { background:'var(--bg-secondary)', color:'var(--text-muted)', border:'1px solid var(--border-color)' }"
                        style="clip-path:polygon(0 0,calc(100% - 6px) 0,100% 100%,6px 100%)">
                        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" :fill="isFavorite(selectedPosition.id)?'currentColor':'none'" stroke="currentColor" stroke-width="1.6"><path stroke-linecap="round" stroke-linejoin="round" :d="STAR_PATH"/></svg>
                        {{ isFavorite(selectedPosition.id) ? '已收藏' : '收藏' }}
                      </button>
                    </div>
                    <div v-if="selectedCoverage.total" class="flex items-center gap-2 text-[9px] font-mono mb-3 flex-wrap" style="color:var(--text-muted)">
                      <span>个人覆盖</span>
                      <span class="font-bold" style="color:var(--mint-500)">{{ selectedCoverage.matched }}</span><span class="opacity-50">/ {{ selectedCoverage.total }}</span>
                      <span v-if="selectedCoverage.partial" class="opacity-70">≈ 近似 {{ selectedCoverage.partial }}</span>
                      <span v-if="selectedCoverage.missing" style="color:#f87171">· 缺 {{ selectedCoverage.missing }}</span>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-4">
                      <div class="panel-asymmetric p-2 text-center"><div class="text-[7px] tracking-widest" style="color:var(--text-muted)">SALARY</div><div class="data-segment text-sm" style="color:var(--mint-500)">{{ selectedPosition.salary }}</div></div>
                      <div class="panel-asymmetric p-2 text-center"><div class="text-[7px] tracking-widest" style="color:var(--text-muted)">CITY</div><div class="data-segment text-sm" style="color:var(--text-primary)">{{ selectedPosition.city }}</div></div>
                      <div class="panel-asymmetric p-2 text-center"><div class="text-[7px] tracking-widest" style="color:var(--text-muted)">EXP</div><div class="data-segment text-sm" style="color:var(--text-primary)">{{ selectedPosition.exp }}</div></div>
                    </div>
                    <div v-if="selectedPosition.topCompanies?.length" class="mb-3">
                      <div class="text-[8px] tracking-widest mb-1.5" style="color:var(--text-muted)">TOP COMPANIES · {{ selectedPosition.jdCount }} JD</div>
                      <div class="flex flex-wrap gap-1">
                        <span v-for="c in selectedPosition.topCompanies.slice(0, 4)" :key="c.company_name" class="text-[9px] px-1.5 py-0.5 font-mono" :style="{background:'var(--bg-secondary)',color:'var(--text-secondary)',border:'1px solid var(--border-color)'}">{{ c.company_name }} ×{{ c.count }}</span>
                      </div>
                    </div>
                    <div class="mb-3"><div class="text-[8px] tracking-widest mb-1.5" style="color:var(--brand-400)">必备技能</div><div class="flex flex-wrap gap-1"><span v-for="s in selectedPosition.requiredSkills" :key="s" class="text-[9px] px-1.5 py-0.5 font-mono" :style="{background:isUserSkill(s)?'color-mix(in srgb, var(--mint-500) 10%, transparent)':'color-mix(in srgb, var(--brand-500) 06%, transparent)',color:isUserSkill(s)?'var(--mint-500)':'var(--brand-400)',border:'1px solid '+(isUserSkill(s)?'color-mix(in srgb, var(--mint-500) 25%, transparent)':'color-mix(in srgb, var(--brand-500) 15%, transparent)')}">{{ s }}</span></div></div>
                    <div class="mb-4"><div class="text-[8px] tracking-widest mb-1.5" style="color:var(--text-muted)">加分技能</div><div class="flex flex-wrap gap-1"><span v-for="s in selectedPosition.bonusSkills" :key="s" class="text-[9px] px-1.5 py-0.5 font-mono" style="background:var(--bg-secondary);color:var(--text-muted);border:1px solid var(--border-color)">{{ s }}</span></div></div>
                    <div class="flex gap-2 pt-3" style="border-top:1px dashed var(--border-color)">
                      <router-link to="/personal/match" class="px-3 py-1.5 text-[9px] font-bold tracking-wider uppercase text-white bg-brand-500 hover:bg-brand-600 transition-colors" style="clip-path:polygon(0 0,calc(100% - 4px) 0,100% 100%,0 100%)">匹配分析</router-link>
                      <router-link to="/personal/match/compare" class="px-3 py-1.5 text-[9px] font-bold tracking-wider uppercase bg-brand-500/20 border border-brand-500/30 text-brand-400">岗位对比</router-link>
                      <router-link to="/personal/learning-path" class="px-3 py-1.5 text-[9px] font-bold tracking-wider uppercase bg-brand-500/20 border border-brand-500/30 text-brand-400">学习路径</router-link>
                    </div>
                  </div>
                </div>
                <div v-else class="panel-asymmetric p-10 text-center shadow-deep"><p class="text-[10px] tracking-wider" style="color:var(--text-muted)">← 选择一个岗位查看详情</p></div>
              </div>
            </div>
          </div>

          <!-- ── 岗位演化 ── -->
          <div v-if="activeModule === 'evolution'" class="panel-industrial panel-circuit p-5 shadow-deep relative">
            <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
            <div class="relative z-[1]">
              <div class="flex items-center gap-2 mb-4"><span class="tag-plate" style="color:var(--cyan-400);border-color:var(--cyan-500)">TIMELINE</span><h3 class="text-xs font-bold tracking-wide uppercase" style="color:var(--text-primary)">岗位能力演化时间线</h3></div>
              <div class="space-y-0">
                <div v-for="(ev, i) in evolutionEvents" :key="ev.date + '-' + i" class="flex gap-4 cursor-pointer group" @click="openEvolutionDetail(ev)">
                  <div class="flex flex-col items-center w-3"><span class="w-3 h-3 rounded-full flex-shrink-0" :style="{background:ev.color,boxShadow:'0 0 6px '+ev.color}"></span><div v-if="i < evolutionEvents.length-1" class="w-px flex-1 my-1" style="background:var(--border-color)"></div></div>
                  <div class="pb-5 flex-1 transition-all group-hover:translate-x-0.5" style="border-radius:2px"><div class="flex items-center gap-2 mb-1"><span class="data-segment text-[10px]" :style="{color:ev.color}">{{ ev.date }}</span><span class="tag-plate text-[7px]" :style="{color:ev.color,borderColor:ev.color}">{{ ev.type }}</span></div><p class="text-[11px] font-bold" style="color:var(--text-primary)">{{ ev.skill }}</p><p class="text-[9px] mt-0.5" style="color:var(--text-muted)">{{ ev.detail }}</p><div class="mt-1 text-[8px] font-mono tracking-widest opacity-0 group-hover:opacity-100 transition-opacity" :style="{color:ev.color}">▸ 查看详情</div></div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── 新岗发现 ── -->
          <div v-if="activeModule === 'discovery'" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div v-for="role in discoveredRoles" :key="role.name" class="panel-industrial panel-circuit p-5 shadow-deep relative">
              <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
              <div class="relative z-[1]">
                <div class="flex items-center justify-between mb-3"><span class="tag-plate" :style="{color:role.verdictColor,borderColor:role.verdictColor}">{{ role.verdict }}</span><span class="data-segment text-sm" :style="{color:role.verdictColor}">{{ role.confidence }}</span></div>
                <h3 class="text-sm font-bold mb-2" style="color:var(--text-primary)">{{ role.name }}</h3>
                <p class="text-[10px] mb-3" style="color:var(--text-secondary)">{{ role.description }}</p>
                <div class="flex flex-wrap gap-1 mb-3"><span v-for="s in role.skills" :key="s" class="text-[8px] px-1.5 py-0.5 font-mono" style="background:color-mix(in srgb, var(--cyan-500) 06%, transparent);color:var(--cyan-400);border:1px solid color-mix(in srgb, var(--cyan-500) 15%, transparent)">{{ s }}</span></div>
                <div class="text-[9px] font-mono" style="color:var(--text-muted)">{{ role.evidenceCount ? role.evidenceCount + ' JDs · ' : '' }}{{ role.industry }}{{ role.discoveredAt ? ' · 发现于 ' + role.discoveredAt : '' }}</div>
              </div>
            </div>
          </div>

          <!-- ── 全景图谱 ── -->
          <div v-if="activeModule === 'graph'" class="panel-industrial panel-circuit p-5 shadow-deep relative">
            <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div>
            <div class="relative z-[1]">
              <div class="flex items-center gap-2 mb-4"><span class="tag-plate" style="color:var(--mint-400);border-color:var(--mint-500)">GRAPH</span><h3 class="text-xs font-bold tracking-wide uppercase" style="color:var(--text-primary)">技能信号棱镜</h3></div>
              <SignalPrism :beams="graphBeams" :height="280" />
              <div class="mt-3 flex items-center justify-between">
                <span class="text-[9px] font-mono tracking-widest" style="color:var(--text-muted)">{{ graphBeams.length }} SOURCES · {{ store.skills.length }} SKILLS</span>
                <router-link to="/enterprise/graph" class="px-4 py-2 text-[9px] font-bold tracking-wider uppercase text-white bg-brand-500 hover:bg-brand-600 transition-colors" style="clip-path:polygon(0 0,calc(100% - 4px) 0,100% 100%,0 100%)">进入全屏图谱</router-link>
              </div>
            </div>
          </div>

          <!-- ── 人才需求 ── -->
          <div v-if="activeModule === 'talent'" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div class="panel-neon panel-circuit p-5 shadow-deep relative">
              <div class="rivet" style="top:8px;left:8px"></div>
              <div class="relative z-[1]"><div class="flex items-center gap-2 mb-3"><span class="w-1.5 h-1.5 rounded-full bg-mint-500" style="box-shadow:0 0 4px var(--mint-500)"></span><span class="text-[9px] tracking-widest" style="color:var(--mint-400)">EMERGING · {{ emergingSkills.length }} SKILLS</span></div>
                <div class="space-y-2"><div v-for="(s, i) in emergingSkills" :key="s.name" class="flex items-center gap-2"><span class="data-segment text-[9px] w-4 text-center" style="color:var(--text-muted)">{{ String(i+1).padStart(2,'0') }}</span><span class="flex-1 min-w-0"><div class="text-[10px] font-mono truncate" style="color:var(--text-primary)">{{ s.name }}</div><div class="text-[8px] font-mono truncate" style="color:var(--text-muted)">{{ s.category }} · 波动 {{ s.volatility }}</div></span><span class="data-segment text-[10px]" style="color:var(--mint-500)">{{ s.emergence }}</span></div></div>
              </div>
            </div>
            <div class="panel-asymmetric p-5 shadow-deep relative">
              <div class="rivet" style="top:8px;left:8px"></div>
              <div class="relative z-[1]"><div class="flex items-center gap-2 mb-3"><span class="w-1.5 h-1.5 rounded-full bg-rose-500" style="box-shadow:0 0 4px var(--rose-500)"></span><span class="text-[9px] tracking-widest" style="color:var(--rose-400)">DECLINING · {{ decliningSkills.length }} SKILLS</span></div>
                <div class="space-y-2"><div v-for="(s, i) in decliningSkills" :key="s.name" class="flex items-center gap-2"><span class="data-segment text-[9px] w-4 text-center" style="color:var(--text-muted)">{{ String(i+1).padStart(2,'0') }}</span><span class="flex-1 min-w-0"><div class="text-[10px] font-mono truncate" style="color:var(--text-primary)">{{ s.name }}</div><div class="text-[8px] font-mono truncate" style="color:var(--text-muted)">{{ s.category }} · 波动 {{ s.volatility }}</div></span><span class="data-segment text-[10px]" style="color:var(--rose-500)">{{ s.decline }}</span></div></div>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- ── 演化节点详情弹窗 ── -->
      <transition name="detail-fade">
        <div v-if="selectedEvolution" class="fixed inset-0 z-[70] flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/70" @click="closeEvolutionDetail"></div>
          <div class="relative z-10 w-full max-w-lg panel-industrial panel-circuit p-6 shadow-deep" style="animation:detail-pop 0.25s ease-out">
            <div class="rivet" style="top:8px;left:8px"></div><div class="rivet" style="top:8px;right:8px"></div><div class="rivet" style="bottom:8px;left:8px"></div><div class="rivet" style="bottom:8px;right:8px"></div>
            <button class="absolute top-3 right-3 w-6 h-6 flex items-center justify-center text-[11px] leading-none" style="color:var(--text-muted);border:1px solid var(--border-color)" @click="closeEvolutionDetail">✕</button>
            <div class="relative z-[1]">
              <div class="flex items-center gap-2 mb-3"><span class="data-segment text-sm" :style="{color:selectedEvolution.color}">{{ selectedEvolution.date }}</span><span class="tag-plate text-[8px]" :style="{color:selectedEvolution.color,borderColor:selectedEvolution.color}">{{ selectedEvolution.type }}</span></div>
              <h3 class="text-base font-bold mb-2" style="color:var(--text-primary)">{{ selectedEvolution.skill }}</h3>
              <p class="text-[11px] leading-relaxed mb-4" style="color:var(--text-secondary)">{{ selectedEvolution.detail }}</p>
              <div v-if="selectedEvolution.metric" class="mb-3"><div class="text-[8px] tracking-widest mb-1.5" style="color:var(--text-muted)">关键指标</div><span class="data-segment text-xs" :style="{color:selectedEvolution.color}">{{ selectedEvolution.metric }}</span></div>
              <div v-if="selectedEvolution.sources?.length" class="mb-3"><div class="text-[8px] tracking-widest mb-1.5" style="color:var(--text-muted)">数据来源</div><div class="flex flex-wrap gap-1"><span v-for="s in selectedEvolution.sources" :key="s" class="text-[9px] px-1.5 py-0.5 font-mono" style="background:var(--bg-secondary);color:var(--text-secondary);border:1px solid var(--border-color)">{{ s }}</span></div></div>
              <div v-if="selectedEvolution.related?.length" class="mb-2"><div class="text-[8px] tracking-widest mb-1.5" style="color:var(--text-muted)">相关技能</div><div class="flex flex-wrap gap-1"><span v-for="s in selectedEvolution.related" :key="s" class="text-[9px] px-1.5 py-0.5 font-mono" style="background:color-mix(in srgb, var(--brand-500) 06%, transparent);color:var(--brand-400);border:1px solid color-mix(in srgb, var(--brand-500) 15%, transparent)">{{ s }}</span></div></div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePersonalStore } from '@/stores/personal'
import type { FavoritePosition } from '@/stores/personal'
import { classifySkills } from '@/utils/matches'
import SignalPrism from '@/components/personal/SignalPrism.vue'
import client from '@/api/client'

const store = usePersonalStore()
const activeModule = ref<string|null>(null)
const selectedPosition = ref<any>(null)
const activeFilters = ref<string[]>([])
// 演化节点详情弹窗：当前选中的节点（点击时间线节点弹出）
const selectedEvolution = ref<any>(null)

function expandModule(key: string) { activeModule.value = key }
function collapseModule() { activeModule.value = null; selectedPosition.value = null }

// ── 模组网格预览（previewPositions/Evolution/Discovery/Ticker 为 computed，
//    由下方真实数据 ref 派生，接口落库后模块卡预览同步刷新 —— 见「数据接线区」）──

// ── 岗位库数据 ──
// 技术栈筛选：从当前数据派生（真实岗位库 tech_stack 分布，按出现频次降序），无数据时回退四类硬编码。
// 避免「筛选按钮点进空列表」——按钮只在存在对应岗位时渲染。
const techStacks = computed(() => {
  const counts = new Map<string, number>()
  allPositions.value.forEach((p: any) => {
    if (p.techStack) counts.set(p.techStack, (counts.get(p.techStack) || 0) + 1)
  })
  if (!counts.size) return ['人工智能', '大数据', '智能系统', '物联网']
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).map(e => e[0])
})
const allPositions = computed(() => {
  // 真实岗位库优先：store.positions 来自 /api/positions（T1 画像 + T4 技能），
  // 含真实城市/薪资/公司/技能；空时回退 matches（用户匹配）与硬编码 demo。
  if (store.positions.length) {
    const maxJd = Math.max(...store.positions.map(p => p.jdCount || 0))
    return store.positions.map(p => ({
      id: p.position_id,
      name: p.name,
      type: p.position_type,
      techStack: p.tech_stack,
      skillCount: p.skill_count,
      salary: p.salaryRange || '—',
      city: p.city || '—',
      exp: '—',
      jdCount: p.jdCount || 0,
      topCompanies: p.topCompanies || [],
      topCities: p.topCities || [],
      // 市场需求热度：按 jd_count 归一化，替代个人匹配率（无个人匹配语境）
      matchRate: maxJd ? Math.max(5, Math.min(99, Math.round(((p.jdCount || 0) / maxJd) * 99))) : 60,
      requiredSkills: (p.requiredSkills || []).slice(0, 8),
      bonusSkills: (p.bonusSkills || []).slice(0, 8),
    }))
  }
  if (store.matches.length) {
    return store.matches.map(m => ({
      id:m.id, name:m.positionName, type:'既有', techStack:'人工智能',
      skillCount:m.matchedSkills.length+m.missingSkills.length, salary:m.salaryRange,
      city:'合肥', exp:'3-5年', matchRate:m.matchRate,
      requiredSkills:m.matchedSkills.concat(m.missingSkills.slice(0,3)),
      bonusSkills:m.missingSkills.slice(3),
    }))
  }
  return [
    { id:'1', name:'AI 算法工程师', type:'新兴', techStack:'人工智能', skillCount:7, salary:'40-70K', city:'合肥', exp:'3-5年', matchRate:72, requiredSkills:['Python','PyTorch','Transformer','RAG','DeepSpeed'], bonusSkills:['MLOps','NLP','LangChain'] },
    { id:'2', name:'大数据开发工程师', type:'既有', techStack:'大数据', skillCount:8, salary:'25-45K', city:'北京', exp:'3-5年', matchRate:52, requiredSkills:['Spark','Flink','Kafka','Hadoop','SQL'], bonusSkills:['ClickHouse','Doris','Iceberg'] },
    { id:'3', name:'全栈开发工程师', type:'既有', techStack:'智能系统', skillCount:6, salary:'30-50K', city:'上海', exp:'3-5年', matchRate:85, requiredSkills:['TypeScript','React','Node.js','SQL','Docker'], bonusSkills:['AWS','Kubernetes'] },
    { id:'4', name:'嵌入式 AI 工程师', type:'新兴', techStack:'智能系统', skillCount:8, salary:'18-35K', city:'成都', exp:'2-4年', matchRate:45, requiredSkills:['C++','Linux','TensorFlow Lite','ARM','CUDA'], bonusSkills:['ROS','NPU','Jetson'] },
    { id:'5', name:'ML Engineer', type:'既有', techStack:'人工智能', skillCount:7, salary:'45-80K', city:'上海', exp:'3-5年', matchRate:68, requiredSkills:['Python','PyTorch','Docker','SQL','Git'], bonusSkills:['MLOps','Kubernetes','Airflow'] },
  ]
})
const filteredPositions = computed(() => {
  // 只保留仍存在于当前数据中的筛选（数据刷新后旧筛选自动失效，避免锁死空列表）
  const valid = techStacks.value.filter(t => activeFilters.value.includes(t))
  const list = valid.length ? allPositions.value.filter(p => valid.includes(p.techStack)) : allPositions.value
  return [...list].sort((a,b) => b.matchRate - a.matchRate)
})
function toggleFilter(s:string){const i=activeFilters.value.indexOf(s);if(i>=0)activeFilters.value.splice(i,1);else activeFilters.value.push(s)}
function selectPosition(p:any){selectedPosition.value=p}
function isUserSkill(n:string){return store.skills.some(s=>s.name.toLowerCase()===n.toLowerCase())}

// ── 岗位收藏：收藏时对必备技能做个人覆盖分类，快照存入 store（localStorage 持久化）──
const STAR_PATH = 'M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.563.563 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.563.563 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z'
function buildFavorite(pos: any): FavoritePosition {
  const cls = classifySkills(store.skills, pos.requiredSkills || [])
  return {
    id: pos.id,
    name: pos.name,
    salary: pos.salary,
    city: pos.city,
    techStack: pos.techStack,
    jdCount: pos.jdCount || 0,
    matchRate: pos.matchRate || 60,
    matchedSkills: cls.matched,
    partialSkills: cls.partial,
    missingSkills: cls.missing,
    requiredSkills: pos.requiredSkills || [],
    bonusSkills: pos.bonusSkills || [],
    topCompanies: pos.topCompanies || [],
    favoritedAt: Date.now(),
  }
}
function toggleFavoritePosition(pos: any) { store.toggleFavorite(buildFavorite(pos)) }
function isFavorite(id: string) { return store.isFavorite(id) }
/** 当前选中岗位的个人覆盖读数（必备技能中已掌握 / 近似 / 缺失） */
const selectedCoverage = computed(() => {
  const p = selectedPosition.value
  if (!p) return { matched: 0, partial: 0, missing: 0, total: 0 }
  const cls = classifySkills(store.skills, p.requiredSkills || [])
  return { matched: cls.matched.length, partial: cls.partial.length, missing: cls.missing.length, total: (p.requiredSkills || []).length }
})

// ── 演化数据（Silent Fallback demo · 50 条详细技能演化事件）──
const evolutionEvents = ref([
  { date:'2026-Q4', type:'新增', skill:'Agent 智能体编排', detail:'主流大模型岗位 JD 从「了解」转为「熟练掌握」，42 条 JD 明确要求 Agent 框架与任务编排', color:'var(--mint-500)' },
  { date:'2026-Q4', type:'新增', skill:'MCP 模型上下文协议', detail:'MCP 成为 Agent 连接外部工具的事实标准，35 条 JD 新增协议要求，emergence 3.18', color:'var(--mint-500)' },
  { date:'2026-Q4', type:'升级', skill:'RAG 检索增强生成', detail:'从「加分项」升级为「必备项」，置信度 0.72 → 0.88，跨 28 条 JD 验证通过', color:'var(--mint-500)' },
  { date:'2026-Q4', type:'需求', skill:'多模态大模型', detail:'视觉语言岗位需求环比 +38%，emergence 3.05，薪资中位上浮 15%', color:'var(--cyan-500)' },
  { date:'2026-Q3', type:'新增', skill:'LoRA/QLoRA 微调', detail:'端侧部署场景激增，28 条 JD 要求低成本微调能力，替代全参微调成为主流', color:'var(--mint-500)' },
  { date:'2026-Q3', type:'升级', skill:'PyTorch', detail:'从 中级 → 高级，85% AI 岗位 JD 要求熟练使用，含分布式训练实践', color:'var(--mint-500)' },
  { date:'2026-Q3', type:'修改', skill:'Transformer 置信度提升', detail:'置信度 0.68 → 0.82，跨 JD 验证通过，成为所有大模型岗位的基石要求', color:'var(--brand-500)' },
  { date:'2026-Q3', type:'新增', skill:'RLHF 对齐', detail:'对齐技术成为大模型标配，38 条 JD 提及，与偏好数据标注岗位联动', color:'var(--mint-500)' },
  { date:'2026-Q3', type:'需求', skill:'Agent 应用开发', detail:'智能体应用岗需求同比 +52%，岗位数量从 14 条跃升至 96 条', color:'var(--cyan-500)' },
  { date:'2026-Q2', type:'新增', skill:'DeepSpeed 分布式训练', detail:'大模型训练岗新增必备技能，emergence 2.41，要求熟悉 ZeRO/流水并行', color:'var(--mint-500)' },
  { date:'2026-Q2', type:'升级', skill:'NLP', detail:'从 中级 → 高级，大模型时代 NLP 要求提升，加入评测与对齐内容', color:'var(--mint-500)' },
  { date:'2026-Q2', type:'新增', skill:'vLLM 推理优化', detail:'推理引擎选型进入 JD，19 条提及 PagedAttention 与量化部署', color:'var(--mint-500)' },
  { date:'2026-Q2', type:'修改', skill:'Kubernetes 实战化', detail:'从「了解」升级为「实战」，要求会写 Helm Chart 并调优调度器', color:'var(--brand-500)' },
  { date:'2026-Q2', type:'新增', skill:'eBPF 可观测', detail:'可观测性与安全工程岗位新增 eBPF 要求，17 条 JD，Cilium 生态驱动', color:'var(--mint-500)' },
  { date:'2026-Q1', type:'新增', skill:'Agent 应用框架', detail:'LangGraph / AutoGen 进入 JD 技能清单，12 条 JD 明确要求框架落地', color:'var(--mint-500)' },
  { date:'2026-Q1', type:'升级', skill:'Docker 容器化', detail:'容器化从加分项变为必备项，覆盖 90% 后端与 AI 应用岗位', color:'var(--mint-500)' },
  { date:'2026-Q1', type:'修改', skill:'Rust 需求上升', detail:'系统级岗位需求上升，置信度 0.51 → 0.63，与性能敏感场景绑定', color:'var(--brand-500)' },
  { date:'2026-Q1', type:'新增', skill:'WebAssembly 边缘计算', detail:'前端边缘计算岗位新增 Wasm 要求，CDN 与边缘函数场景推动', color:'var(--mint-500)' },
  { date:'2026-Q1', type:'需求', skill:'推理引擎优化', detail:'GPU 推理优化岗位需求 +45%，月薪中位 45-70K，紧俏度第一梯队', color:'var(--cyan-500)' },
  { date:'2025-Q4', type:'降级', skill:'传统机器学习', detail:'深度学习取代大部分传统 ML，从 高级 → 中级，仅保留表格类场景', color:'var(--rose-500)' },
  { date:'2025-Q4', type:'删除', skill:'Theano', detail:'市场需求归零，decline 0.95，框架生态彻底关闭', color:'var(--rose-500)' },
  { date:'2025-Q4', type:'修改', skill:'特征工程定位调整', detail:'从「核心」降为「辅助」，AutoML 与端到端学习接管多数手工特征', color:'var(--brand-500)' },
  { date:'2025-Q4', type:'新增', skill:'数据质量工程', detail:'大模型数据治理岗位新增，14 条 JD 要求血缘与质量规则落地', color:'var(--mint-500)' },
  { date:'2025-Q4', type:'需求', skill:'MLOps 工程化', detail:'模型运维岗位需求同比 +40%，MLflow/Kubeflow 双栈成为标配', color:'var(--cyan-500)' },
  { date:'2025-Q3', type:'新增', skill:'Agent 安全对齐', detail:'安全评测岗位新增要求，覆盖提示注入、越权与工具滥用', color:'var(--mint-500)' },
  { date:'2025-Q3', type:'升级', skill:'Spark', detail:'从 中级 → 高级，湖仓一体化场景要求 SQL 与流批一体能力', color:'var(--mint-500)' },
  { date:'2025-Q3', type:'修改', skill:'Flink 地位上升', detail:'实时计算地位上升，置信度提升，要求状态管理与背压调优', color:'var(--brand-500)' },
  { date:'2025-Q3', type:'新增', skill:'Iceberg 湖格式', detail:'湖格式进入数据岗 JD，21 条提及，取代 Hive 成为默认表格式', color:'var(--mint-500)' },
  { date:'2025-Q3', type:'新增', skill:'Doris 实时分析', detail:'实时分析引擎岗位新增，15 条 JD 要求物化视图与高并发查询', color:'var(--mint-500)' },
  { date:'2025-Q2', type:'降级', skill:'Hadoop MR', detail:'被 Spark/Flink 取代，从 高级 → 初级，仅遗留迁移项目使用', color:'var(--rose-500)' },
  { date:'2025-Q2', type:'删除', skill:'Flash', detail:'彻底退出需求列表，decline 0.98，播放器生态消亡', color:'var(--rose-500)' },
  { date:'2025-Q2', type:'修改', skill:'Vue3 组合式 API', detail:'前端主流框架，组合式 API 成为面试必考，选项式写法被淘汰', color:'var(--brand-500)' },
  { date:'2025-Q2', type:'新增', skill:'Next.js SSR', detail:'全栈岗位新增要求，SSR/ISR 成为服务端渲染标配', color:'var(--mint-500)' },
  { date:'2025-Q2', type:'需求', skill:'湖仓一体架构', detail:'数据架构岗需求 +33%，ICEBERG+Spark+Flink 组合成招聘高频词', color:'var(--cyan-500)' },
  { date:'2025-Q1', type:'新增', skill:'ClickHouse OLAP', detail:'OLAP 实时分析新增要求，11 条 JD 要求向量化执行与分布式查询', color:'var(--mint-500)' },
  { date:'2025-Q1', type:'修改', skill:'Go 云原生化', detail:'云原生岗位要求上升，置信度 0.45 → 0.58，与 K8s 生态绑定', color:'var(--brand-500)' },
  { date:'2025-Q1', type:'新增', skill:'ArgoCD GitOps', detail:'GitOps 进入 DevOps 岗 JD，声明式交付成为团队规范', color:'var(--mint-500)' },
  { date:'2025-Q1', type:'新增', skill:'Terraform IaC', detail:'基础设施即代码成为运维必备，多云管理岗位要求逐步统一', color:'var(--mint-500)' },
  { date:'2025-Q1', type:'降级', skill:'AngularJS', detail:'被框架时代淘汰，从 高级 → 废弃维护，岗位需求趋近于零', color:'var(--rose-500)' },
  { date:'2024-Q4', type:'新增', skill:'Prometheus 可观测', detail:'可观测性岗位新增要求，指标采集与告警体系成为标配', color:'var(--mint-500)' },
  { date:'2024-Q4', type:'修改', skill:'TypeScript 必备化', detail:'从 加分 到 必备，前端与全栈岗位均要求类型安全', color:'var(--brand-500)' },
  { date:'2024-Q4', type:'删除', skill:'CoffeeScript', detail:'需求归零，被 ES6+ 原生语法彻底取代', color:'var(--rose-500)' },
  { date:'2024-Q4', type:'新增', skill:'向量数据库', detail:'Milvus/FAISS 进入 AI 岗 JD，RAG 场景驱动检索基础设施招聘', color:'var(--mint-500)' },
  { date:'2024-Q4', type:'需求', skill:'AI 应用工程化', detail:'AI 应用工程岗需求 +28%，提示工程与评估成为独立职责', color:'var(--cyan-500)' },
  { date:'2024-Q3', type:'新增', skill:'LangChain 应用开发', detail:'应用开发框架新增要求，快速原型与链路编排成为日常', color:'var(--mint-500)' },
  { date:'2024-Q3', type:'降级', skill:'jQuery', detail:'前端原生与框架化替代，从 常用 → 维护性技能，decline 0.82', color:'var(--rose-500)' },
  { date:'2024-Q3', type:'修改', skill:'React Concurrent', detail:'Concurrent 特性成为要求，Suspense 与 useTransition 进入笔试', color:'var(--brand-500)' },
  { date:'2024-Q3', type:'新增', skill:'GraphQL 数据层', detail:'数据查询层新增要求，BFF 模式与订阅能力进入 JD', color:'var(--mint-500)' },
  { date:'2024-Q2', type:'删除', skill:'Bower 包管理', detail:'包管理时代终结，被 npm/yarn/pnpm 统一取代', color:'var(--rose-500)' },
  { date:'2024-Q2', type:'新增', skill:'GitOps 交付', detail:'部署自动化岗位新增要求，环境漂移治理成为团队规范', color:'var(--mint-500)' },
])

// ── 演化节点详情增强表 ──
// 按技能名补齐 demo 事件的 关键指标 / 数据来源 / 相关技能，供点击节点后的详情弹窗展示；
// 真实演化节点自带 timeline 字段（marketDemand/salaryRange/dataSources/tools），不走此表。
const evolutionDetailEnrich: Record<string, { metric: string; sources: string[]; related: string[] }> = {
  'Agent 智能体编排': { metric:'需求环比 +38% · emergence 3.42', sources:['JD×42','GitHub×26','arXiv×8'], related:['LangGraph','MCP','工具调用'] },
  'MCP 模型上下文协议': { metric:'emergence 3.18 · 置信度 0.81', sources:['JD×35','GitHub×22'], related:['Agent','工具协议','鉴权'] },
  'RAG 检索增强生成': { metric:'置信度 0.72 → 0.88', sources:['JD×28','arXiv×15'], related:['向量数据库','Embedding','重排序'] },
  '多模态大模型': { metric:'需求环比 +38% · emergence 3.05', sources:['JD×24','arXiv×31'], related:['视觉Transformer','图文对齐','扩散模型'] },
  'LoRA/QLoRA 微调': { metric:'emergence 2.74 · 覆盖岗位 28 条', sources:['JD×28','GitHub×19'], related:['PEFT','量化','端侧部署'] },
  'PyTorch': { metric:'必备化 · 需求占比 85%', sources:['JD×210','GitHub×180'], related:['CUDA','分布式训练','ONNX'] },
  'Transformer 置信度提升': { metric:'置信度 0.68 → 0.82', sources:['JD×96','arXiv×58'], related:['自注意力','预训练','注意力机制'] },
  'RLHF 对齐': { metric:'覆盖岗位 38 条 · emergence 2.88', sources:['JD×38','arXiv×22'], related:['偏好数据','DPO','安全对齐'] },
  'Agent 应用开发': { metric:'需求同比 +52%（14 → 96 条）', sources:['JD×96','GitHub×41'], related:['任务编排','工具调度','记忆'] },
  'DeepSpeed 分布式训练': { metric:'emergence 2.41 · 月薪中位 45-70K', sources:['JD×19','GitHub×15'], related:['ZeRO','流水并行','混合精度'] },
  'NLP': { metric:'级别 中级 → 高级', sources:['JD×85','arXiv×47'], related:['大模型','分词','评测'] },
  'vLLM 推理优化': { metric:'emergence 2.81 · 岗位 19 条', sources:['JD×19','GitHub×28'], related:['PagedAttention','量化','批处理'] },
  'Kubernetes 实战化': { metric:'置信度 0.62 → 0.74', sources:['JD×130','GitHub×90'], related:['Helm','调度器','容器网络'] },
  'eBPF 可观测': { metric:'emergence 2.62 · 岗位 17 条', sources:['JD×17','GitHub×14'], related:['Cilium','内核','Tracee'] },
  'Agent 应用框架': { metric:'岗位 12 条 · emergence 2.36', sources:['JD×12','GitHub×21'], related:['LangGraph','AutoGen','CrewAI'] },
  'Docker 容器化': { metric:'需求覆盖 90% 后端岗位', sources:['JD×240','GitHub×120'], related:['镜像','编排','安全'] },
  'Rust 需求上升': { metric:'置信度 0.51 → 0.63', sources:['JD×33','GitHub×56'], related:['内存安全','性能','Tauri'] },
  'WebAssembly 边缘计算': { metric:'emergence 2.20 · 岗位 8 条', sources:['JD×8','arXiv×6'], related:['WASI','边缘函数','Rust'] },
  '推理引擎优化': { metric:'需求 +45% · 月薪中位 45-70K', sources:['JD×31','GitHub×25'], related:['GPU','算子融合','显存'] },
  '传统机器学习': { metric:'级别 高级 → 中级', sources:['JD×58','arXiv×12'], related:['特征工程','AutoML','表格数据'] },
  'Theano': { metric:'decline 0.95 · 需求归零', sources:['JD×0','GitHub×2'], related:['TensorFlow','PyTorch','Keras'] },
  '特征工程定位调整': { metric:'从 核心 降为 辅助', sources:['JD×45','arXiv×9'], related:['AutoML','Embedding','端到端学习'] },
  '数据质量工程': { metric:'岗位 14 条 · emergence 2.24', sources:['JD×14','GitHub×7'], related:['血缘','质量规则','数据治理'] },
  'MLOps 工程化': { metric:'需求同比 +40%', sources:['JD×78','GitHub×52'], related:['MLflow','Kubeflow','CI/CD'] },
  'Agent 安全对齐': { metric:'岗位 9 条 · emergence 2.22', sources:['JD×9','arXiv×11'], related:['提示注入','红队','越权'] },
  'Spark': { metric:'级别 中级 → 高级', sources:['JD×95','GitHub×60'], related:['湖仓','流批一体','SQL'] },
  'Flink 地位上升': { metric:'置信度 0.58 → 0.70', sources:['JD×62','GitHub×48'], related:['Kafka','状态管理','背压'] },
  'Iceberg 湖格式': { metric:'岗位 21 条 · emergence 2.44', sources:['JD×21','GitHub×30'], related:['Hudi','Delta Lake','湖仓'] },
  'Doris 实时分析': { metric:'岗位 15 条 · emergence 2.37', sources:['JD×15','GitHub×12'], related:['物化视图','OLAP','ClickHouse'] },
  'Hadoop MR': { metric:'级别 高级 → 初级', sources:['JD×6','GitHub×4'], related:['Spark','Flink','HDFS'] },
  'Flash': { metric:'decline 0.98 · 彻底退出', sources:['JD×0','GitHub×1'], related:['HTML5','WebGL','视频'] },
  'Vue3 组合式 API': { metric:'置信度 0.81 · 必备化', sources:['JD×110','GitHub×75'], related:['组合式函数','Pinia','Vite'] },
  'Next.js SSR': { metric:'岗位 24 条 · emergence 2.13', sources:['JD×24','GitHub×40'], related:['SSR','ISR','App Router'] },
  '湖仓一体架构': { metric:'需求 +33% · 岗位 19 条', sources:['JD×19','GitHub×11'], related:['Iceberg','Spark','Flink'] },
  'ClickHouse OLAP': { metric:'岗位 11 条 · emergence 2.31', sources:['JD×11','GitHub×14'], related:['向量化','分布式','物化视图'] },
  'Go 云原生化': { metric:'置信度 0.45 → 0.58', sources:['JD×72','GitHub×88'], related:['K8s','并发','gRPC'] },
  'ArgoCD GitOps': { metric:'岗位 13 条 · emergence 2.55', sources:['JD×13','GitHub×17'], related:['Flux','声明式','多环境'] },
  'Terraform IaC': { metric:'岗位 22 条 · emergence 2.48', sources:['JD×22','GitHub×26'], related:['HCL','多云','状态管理'] },
  'AngularJS': { metric:'从 高级 到 废弃维护', sources:['JD×2','GitHub×3'], related:['Angular','React','Vue'] },
  'Prometheus 可观测': { metric:'岗位 16 条 · emergence 2.34', sources:['JD×16','GitHub×20'], related:['Grafana','告警','指标'] },
  'TypeScript 必备化': { metric:'从 加分 到 必备', sources:['JD×150','GitHub×100'], related:['类型系统','Vue3','React'] },
  'CoffeeScript': { metric:'decline 0.93 · 需求归零', sources:['JD×0','GitHub×1'], related:['ES6','Babel','JSX'] },
  '向量数据库': { metric:'岗位 27 条 · emergence 2.31', sources:['JD×27','GitHub×23'], related:['Milvus','FAISS','HNSW'] },
  'AI 应用工程化': { metric:'需求 +28% · 岗位 34 条', sources:['JD×34','GitHub×18'], related:['提示工程','评测','应用网关'] },
  'LangChain 应用开发': { metric:'岗位 18 条 · emergence 1.72', sources:['JD×18','GitHub×25'], related:['RAG','Agent','LCEL'] },
  'jQuery': { metric:'decline 0.82 · 维护性技能', sources:['JD×8','GitHub×5'], related:['原生 DOM','框架化'] },
  'React Concurrent': { metric:'置信度 0.66 → 0.75', sources:['JD×66','GitHub×54'], related:['Suspense','useTransition','并发'] },
  'GraphQL 数据层': { metric:'岗位 10 条 · 稳定增长', sources:['JD×10','GitHub×19'], related:['BFF','Schema','订阅'] },
  'Bower 包管理': { metric:'decline 0.97 · 已淘汰', sources:['JD×0','GitHub×0'], related:['npm','yarn','pnpm'] },
  'GitOps 交付': { metric:'岗位 12 条 · emergence 2.41', sources:['JD×12','GitHub×16'], related:['ArgoCD','环境漂移','发布'] },
}

// ── 演化节点详情弹窗逻辑 ──
function openEvolutionDetail(ev: any) {
  const extra = evolutionDetailEnrich[ev.skill] || {}
  selectedEvolution.value = { ...ev, ...extra }
}
function closeEvolutionDetail() {
  selectedEvolution.value = null
}

// ── 新岗发现数据（Silent Fallback demo · 50 个详细候选岗位）──
const discoveredRoles = ref([
  { name:'RAG 工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.85', description:'负责检索增强生成系统的设计与落地，连接大模型与企业知识库，优化检索质量与召回率', skills:['RAG','向量数据库','LangChain','Embedding','检索排序'], evidenceCount:12, industry:'AI/知识管理', source:'AI 辩论', discoveredAt:'2026-08-15' },
  { name:'MLOps 工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.88', description:'负责模型全生命周期管理，从训练到部署到监控的工程化，建设 CI/CD 流水线', skills:['Docker','Kubernetes','MLflow','Airflow','CI/CD'], evidenceCount:18, industry:'AI/工程化', source:'AI 辩论', discoveredAt:'2026-08-12' },
  { name:'Agent 应用工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.72', description:'搭建多智能体协作系统，负责任务分解、工具调用与记忆管理', skills:['Agent框架','MCP','工具调用','任务编排','记忆系统'], evidenceCount:9, industry:'AI/智能体', source:'流水线发现', discoveredAt:'2026-08-20' },
  { name:'大模型微调工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.86', description:'基于开源基座做领域微调，掌握高效微调与对齐技术', skills:['LoRA','DeepSpeed','RLHF','PyTorch','数据配比'], evidenceCount:21, industry:'AI/大模型', source:'AI 辩论', discoveredAt:'2026-08-18' },
  { name:'推理优化工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.68', description:'优化大模型推理性能，负责算子融合与量化部署', skills:['vLLM','CUDA','模型量化','算子优化','PagedAttention'], evidenceCount:6, industry:'AI/推理', source:'流水线发现', discoveredAt:'2026-08-22' },
  { name:'多模态算法工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.84', description:'研发图文/视频多模态模型，负责跨模态对齐与生成', skills:['视觉Transformer','图文对齐','视频理解','扩散模型'], evidenceCount:15, industry:'AI/多模态', source:'AI 辩论', discoveredAt:'2026-08-10' },
  { name:'数据治理工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.61', description:'建设企业数据治理体系，覆盖质量、血缘、元数据与合规', skills:['数据质量','数据血缘','元数据','主数据','数据合规'], evidenceCount:4, industry:'数据/治理', source:'流水线发现', discoveredAt:'2026-08-25' },
  { name:'湖仓一体架构师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.66', description:'设计湖仓一体数据架构，统一批流存储与计算引擎', skills:['Iceberg','Hudi','Delta Lake','Flink','Spark'], evidenceCount:5, industry:'数据/架构', source:'流水线发现', discoveredAt:'2026-08-24' },
  { name:'实时计算工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.82', description:'构建毫秒级实时计算链路，处理高并发事件流', skills:['Flink','Kafka','Doris','状态管理','背压调优'], evidenceCount:14, industry:'数据/实时', source:'AI 辩论', discoveredAt:'2026-08-08' },
  { name:'平台工程 SRE', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.70', description:'建设内部开发者平台，通过 IaC 与 GitOps 提升交付效率', skills:['Terraform','ArgoCD','Kubernetes','可观测性','平台即产品'], evidenceCount:7, industry:'云原生/平台', source:'流水线发现', discoveredAt:'2026-08-21' },
  { name:'eBPF 安全工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.58', description:'基于 eBPF 构建云原生安全观测与实时审计能力', skills:['eBPF','Cilium','内核编程','实时审计','零信任'], evidenceCount:3, industry:'安全/内核', source:'流水线发现', discoveredAt:'2026-08-27' },
  { name:'AI 应用前端工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.80', description:'构建 AI 应用交互前端，处理流式输出与实时渲染', skills:['TypeScript','React','SSE','流式渲染','WebSocket'], evidenceCount:11, industry:'前端/AI', source:'AI 辩论', discoveredAt:'2026-08-06' },
  { name:'向量数据库工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.63', description:'研发高性能向量检索服务，优化索引结构与召回性能', skills:['Milvus','FAISS','HNSW','索引优化','近似最近邻'], evidenceCount:4, industry:'数据/向量', source:'流水线发现', discoveredAt:'2026-08-23' },
  { name:'Agent 安全评测员', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.55', description:'对智能体做安全红队测试，覆盖提示注入与越权工具调用', skills:['提示注入','越权检测','安全红队','对齐评测','攻击面分析'], evidenceCount:2, industry:'安全/AI', source:'流水线发现', discoveredAt:'2026-08-28' },
  { name:'大模型评估工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.79', description:'建设大模型自动化评测体系，负责评测集与回归基线', skills:['评测集构建','自动化评估','RAG评估','回归基线','胜率评测'], evidenceCount:10, industry:'AI/质量', source:'AI 辩论', discoveredAt:'2026-08-05' },
  { name:'端侧大模型工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.60', description:'将大模型压缩并部署到端侧设备，保证低延迟推理', skills:['模型量化','知识蒸馏','端侧部署','算子优化','NPU'], evidenceCount:3, industry:'AI/端侧', source:'流水线发现', discoveredAt:'2026-08-26' },
  { name:'数据质量平台开发', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.59', description:'开发数据质量监控平台，沉淀质量规则与自动修复能力', skills:['数据血缘','质量规则','任务调度','规则引擎','异常检测'], evidenceCount:3, industry:'数据/平台', source:'流水线发现', discoveredAt:'2026-08-29' },
  { name:'知识图谱工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.77', description:'构建知识图谱与 GraphRAG，支撑企业级复杂问答', skills:['图谱构建','关系抽取','图数据库','GraphRAG','实体链接'], evidenceCount:8, industry:'AI/知识', source:'AI 辩论', discoveredAt:'2026-08-04' },
  { name:'GitOps 平台工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.65', description:'落地 GitOps 交付体系，实现多环境声明式发布', skills:['ArgoCD','Flux','Git 工作流','多云管理','环境漂移治理'], evidenceCount:5, industry:'云原生/DevOps', source:'流水线发现', discoveredAt:'2026-08-19' },
  { name:'可观测性工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.81', description:'构建指标-日志-链路三位一体可观测平台', skills:['Prometheus','OpenTelemetry','Grafana','链路追踪','告警治理'], evidenceCount:13, industry:'DevOps/可观测', source:'AI 辩论', discoveredAt:'2026-08-07' },
  { name:'特征平台工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.57', description:'建设在线特征平台，支撑实时推理与离线训练统一特征', skills:['特征存储','实时特征','在线推理','特征一致性'], evidenceCount:3, industry:'数据/特征', source:'流水线发现', discoveredAt:'2026-08-30' },
  { name:'大模型安全对齐工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.78', description:'负责模型安全对齐与红队评测，降低有害输出风险', skills:['RLHF','DPO','安全红队','越狱防御','价值观对齐'], evidenceCount:9, industry:'AI/安全', source:'AI 辩论', discoveredAt:'2026-08-03' },
  { name:'WebAssembly 边缘工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.54', description:'基于 Wasm 构建边缘计算服务，实现毫秒级函数分发', skills:['WebAssembly','边缘计算','微服务','Rust','WASI'], evidenceCount:2, industry:'边缘/前端', source:'流水线发现', discoveredAt:'2026-08-31' },
  { name:'数据产品经理(AI)', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.83', description:'规划 AI 数据产品，将大模型能力产品化并制定指标体系', skills:['数据产品','大模型应用','指标体系','商业化','用户洞察'], evidenceCount:16, industry:'数据/产品', source:'AI 辩论', discoveredAt:'2026-08-02' },
  { name:'MCP 协议工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.71', description:'研发模型上下文协议服务层，标准化工具接入与鉴权', skills:['MCP','工具协议','服务编排','鉴权','资源发现'], evidenceCount:8, industry:'AI/协议', source:'流水线发现', discoveredAt:'2026-08-16' },
  { name:'智能体编排工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.80', description:'构建智能体任务编排引擎，负责调度、记忆与多智能体协作', skills:['任务编排','工具调度','记忆架构','状态机','并行执行'], evidenceCount:10, industry:'AI/智能体', source:'AI 辩论', discoveredAt:'2026-08-09' },
  { name:'实时特征计算工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.60', description:'构建毫秒级实时特征链路，保障在线推理特征时效', skills:['Flink','Redis','特征服务','窗口计算','一致性'], evidenceCount:4, industry:'数据/实时', source:'流水线发现', discoveredAt:'2026-08-17' },
  { name:'湖仓数据工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.76', description:'基于湖仓架构做数据建模与管道开发，沉淀高质量数据资产', skills:['Spark','Iceberg','数据建模','管道开发','数据血缘'], evidenceCount:8, industry:'数据/湖仓', source:'AI 辩论', discoveredAt:'2026-08-11' },
  { name:'大模型训练工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.69', description:'负责千卡级分布式训练，调优集群利用率与故障恢复', skills:['Megatron','DeepSpeed','集群调度','InfiniBand','Checkpoint 恢复'], evidenceCount:6, industry:'AI/训练', source:'流水线发现', discoveredAt:'2026-08-13' },
  { name:'数据库内核工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.56', description:'研发数据库存储与查询内核，优化并发控制与执行计划', skills:['C++','存储引擎','查询优化','MVCC','执行器'], evidenceCount:3, industry:'数据库/内核', source:'流水线发现', discoveredAt:'2026-08-14' },
  { name:'云原生网关工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.79', description:'构建云原生流量网关，负责路由、限流与服务治理', skills:['Envoy','Istio','网关','限流熔断','可观测'], evidenceCount:9, industry:'云原生/网络', source:'AI 辩论', discoveredAt:'2026-08-01' },
  { name:'Prompt 工程专家', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.62', description:'沉淀提示工程方法论，提升应用指令遵循与工具调用成功率', skills:['提示工程','指令遵循','工具调用','少样本设计','评测'], evidenceCount:4, industry:'AI/应用', source:'流水线发现', discoveredAt:'2026-08-05' },
  { name:'大模型数据标注主管', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.53', description:'管理大模型训练数据飞轮，把控标注质量与配比', skills:['数据标注','评测数据','数据飞轮','质量巡检','样本配比'], evidenceCount:2, industry:'AI/数据', source:'流水线发现', discoveredAt:'2026-09-01' },
  { name:'智能体记忆系统工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.57', description:'设计智能体长期记忆架构，实现会话状态与知识沉淀', skills:['记忆架构','向量检索','会话状态','遗忘策略','压缩'], evidenceCount:3, industry:'AI/智能体', source:'流水线发现', discoveredAt:'2026-09-02' },
  { name:'推理服务平台工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.81', description:'建设统一推理服务平台，支持多模型灰度与弹性扩缩', skills:['vLLM','Kubernetes','灰度发布','弹性伸缩','成本优化'], evidenceCount:11, industry:'AI/推理', source:'AI 辩论', discoveredAt:'2026-07-31' },
  { name:'模型压缩工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.60', description:'压缩大模型体积，通过蒸馏与剪枝适配边缘硬件', skills:['知识蒸馏','剪枝','量化','NPU','混合精度'], evidenceCount:4, industry:'AI/压缩', source:'流水线发现', discoveredAt:'2026-09-03' },
  { name:'数据血缘工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.55', description:'解析任务调度血缘，构建数据资产关系图谱', skills:['血缘解析','调度解析','知识图谱','元数据','影响分析'], evidenceCount:3, industry:'数据/治理', source:'流水线发现', discoveredAt:'2026-09-04' },
  { name:'多云迁移工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.58', description:'主导应用多云迁移与账号治理，保障迁移零停机', skills:['Terraform','云账号治理','迁移工具','成本治理','割接演练'], evidenceCount:3, industry:'云原生/多云', source:'流水线发现', discoveredAt:'2026-09-05' },
  { name:'AI 测试工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.75', description:'建立大模型应用回归测试体系，覆盖功能与安全用例', skills:['自动化测试','大模型评测','回归测试','用例生成','灰度验证'], evidenceCount:7, industry:'质量/AI', source:'AI 辩论', discoveredAt:'2026-07-30' },
  { name:'服务网格工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.63', description:'落地服务网格与零信任访问，统一流量与安全策略', skills:['Istio','Envoy','Sidecar','零信任','策略下发'], evidenceCount:4, industry:'云原生/网络', source:'流水线发现', discoveredAt:'2026-09-06' },
  { name:'大模型数据管线工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.59', description:'构建训练数据流水线，完成清洗、去重与配比调度', skills:['数据清洗','去重','质量评分','样本配比','调度'], evidenceCount:3, industry:'AI/数据', source:'流水线发现', discoveredAt:'2026-09-07' },
  { name:'端侧推理工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.74', description:'优化端侧推理链路，交付低功耗低延迟的离线能力', skills:['ONNX','量化','端侧部署','算子库','内存优化'], evidenceCount:6, industry:'AI/端侧', source:'AI 辩论', discoveredAt:'2026-07-29' },
  { name:'GraphRAG 工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.61', description:'将知识图谱与大模型检索结合，解决复杂多跳问答', skills:['知识图谱','GraphRAG','检索增强','关系推理','评估'], evidenceCount:4, industry:'AI/知识', source:'流水线发现', discoveredAt:'2026-09-08' },
  { name:'金融大模型应用工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.82', description:'在风控合规约束下落地金融大模型应用，建设智能体助手', skills:['风控','合规审计','RAG','智能体','可解释性'], evidenceCount:13, industry:'行业/金融', source:'AI 辩论', discoveredAt:'2026-07-28' },
  { name:'数据分析+AI 复合岗', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.64', description:'用大模型增强数据分析链路，自动生成洞察与可视化', skills:['SQL','Python','大模型','数据可视化','自动洞察'], evidenceCount:5, industry:'数据/复合', source:'流水线发现', discoveredAt:'2026-09-09' },
  { name:'游戏 AI 工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.52', description:'将大模型引入游戏 NPC 与剧情生成，提升交互沉浸感', skills:['强化学习','行为树','大模型NPC','剧情生成','对话系统'], evidenceCount:2, industry:'行业/游戏', source:'流水线发现', discoveredAt:'2026-09-10' },
  { name:'具身智能算法工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.78', description:'研发机器人多模态感知与决策，打通仿真到真机迁移', skills:['多模态','强化学习','机器人','仿真迁移','视觉导航'], evidenceCount:9, industry:'AI/具身', source:'AI 辩论', discoveredAt:'2026-07-27' },
  { name:'联邦学习工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.50', description:'在隐私约束下做多方协同建模，保护数据不出域', skills:['联邦学习','隐私计算','分布式训练','安全聚合'], evidenceCount:2, industry:'AI/隐私', source:'流水线发现', discoveredAt:'2026-09-11' },
  { name:'大模型硬件协同工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.51', description:'面向 NPU 做算子协同优化，提升训练推理能效比', skills:['NPU','编译优化','算子库','性能分析','能效优化'], evidenceCount:2, industry:'AI/芯片', source:'流水线发现', discoveredAt:'2026-09-12' },
  { name:'智能体平台产品经理', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.77', description:'规划智能体开放平台，定义开发者生态与商业化路径', skills:['智能体','开放平台','商业化','开发者生态','数据分析'], evidenceCount:8, industry:'行业/AI产品', source:'AI 辩论', discoveredAt:'2026-07-26' },
])

// ── 人才需求数据（Silent Fallback demo · 各 50 条新兴/衰退技能，含波动率与类别）──
const emergingSkills = ref([
  { name:'Agent 智能体', emergence:'3.42', volatility:'0.88', category:'AI/ML' },
  { name:'MCP 协议', emergence:'3.18', volatility:'0.92', category:'AI/ML' },
  { name:'多模态大模型', emergence:'3.05', volatility:'0.71', category:'AI/ML' },
  { name:'RAG 检索增强', emergence:'2.96', volatility:'0.66', category:'AI/ML' },
  { name:'RLHF 对齐', emergence:'2.88', volatility:'0.74', category:'AI/ML' },
  { name:'vLLM 推理', emergence:'2.81', volatility:'0.83', category:'AI/ML' },
  { name:'LoRA 微调', emergence:'2.74', volatility:'0.58', category:'AI/ML' },
  { name:'eBPF 可观测', emergence:'2.62', volatility:'0.69', category:'DevOps' },
  { name:'湖仓一体', emergence:'2.52', volatility:'0.55', category:'数据' },
  { name:'ArgoCD GitOps', emergence:'2.55', volatility:'0.62', category:'DevOps' },
  { name:'Iceberg 湖格式', emergence:'2.44', volatility:'0.51', category:'数据' },
  { name:'Rust', emergence:'2.47', volatility:'0.64', category:'编程语言' },
  { name:'Terraform IaC', emergence:'2.48', volatility:'0.59', category:'DevOps' },
  { name:'DeepSpeed 训练', emergence:'2.41', volatility:'0.57', category:'AI/ML' },
  { name:'GitOps 交付', emergence:'2.41', volatility:'0.53', category:'DevOps' },
  { name:'Agent 应用框架', emergence:'2.36', volatility:'0.81', category:'AI/ML' },
  { name:'Doris 实时分析', emergence:'2.37', volatility:'0.48', category:'数据' },
  { name:'Kubernetes', emergence:'2.34', volatility:'0.46', category:'DevOps' },
  { name:'ClickHouse OLAP', emergence:'2.31', volatility:'0.47', category:'数据' },
  { name:'Zig', emergence:'2.30', volatility:'0.72', category:'编程语言' },
  { name:'推理优化', emergence:'2.29', volatility:'0.79', category:'AI/ML' },
  { name:'数据质量工程', emergence:'2.24', volatility:'0.50', category:'数据' },
  { name:'模型安全对齐', emergence:'2.22', volatility:'0.76', category:'AI/ML' },
  { name:'WebAssembly', emergence:'2.20', volatility:'0.63', category:'前端' },
  { name:'平台工程', emergence:'2.20', volatility:'0.49', category:'DevOps' },
  { name:'多 Agent 协作', emergence:'2.15', volatility:'0.85', category:'AI/ML' },
  { name:'实时数仓', emergence:'2.17', volatility:'0.44', category:'数据' },
  { name:'OpenTelemetry', emergence:'2.13', volatility:'0.52', category:'DevOps' },
  { name:'Next.js SSR', emergence:'2.13', volatility:'0.41', category:'前端' },
  { name:'Go', emergence:'2.13', volatility:'0.38', category:'编程语言' },
  { name:'知识图谱+LLM', emergence:'2.08', volatility:'0.61', category:'AI/ML' },
  { name:'React Server Components', emergence:'2.06', volatility:'0.45', category:'前端' },
  { name:'数据产品', emergence:'2.10', volatility:'0.43', category:'数据' },
  { name:'云原生安全', emergence:'2.06', volatility:'0.57', category:'DevOps' },
  { name:'OLAP 引擎', emergence:'2.03', volatility:'0.42', category:'数据' },
  { name:'检索增强训练', emergence:'2.01', volatility:'0.68', category:'AI/ML' },
  { name:'TypeScript', emergence:'1.99', volatility:'0.35', category:'前端' },
  { name:'端侧大模型', emergence:'1.95', volatility:'0.70', category:'AI/ML' },
  { name:'边缘渲染', emergence:'1.92', volatility:'0.54', category:'前端' },
  { name:'长上下文工程', emergence:'1.89', volatility:'0.73', category:'AI/ML' },
  { name:'Transformer', emergence:'1.89', volatility:'0.33', category:'AI/ML' },
  { name:'前端 AI 应用', emergence:'1.85', volatility:'0.56', category:'前端' },
  { name:'大模型评测', emergence:'1.82', volatility:'0.60', category:'AI/ML' },
  { name:'RAG 评估', emergence:'1.75', volatility:'0.65', category:'AI/ML' },
  { name:'LangChain', emergence:'1.72', volatility:'0.67', category:'AI/ML' },
  { name:'AutoML', emergence:'1.65', volatility:'0.49', category:'AI/ML' },
  { name:'特征平台', emergence:'1.58', volatility:'0.46', category:'数据' },
  { name:'FSDP 并行', emergence:'1.55', volatility:'0.63', category:'AI/ML' },
  { name:'模型蒸馏', emergence:'1.48', volatility:'0.55', category:'AI/ML' },
  { name:'量化部署', emergence:'1.42', volatility:'0.58', category:'AI/ML' },
])
const decliningSkills = ref([
  { name:'jQuery', decline:'0.82', volatility:'0.41', category:'前端框架' },
  { name:'Theano', decline:'0.95', volatility:'0.62', category:'AI/ML' },
  { name:'Flash', decline:'0.98', volatility:'0.55', category:'前端框架' },
  { name:'SVN', decline:'0.71', volatility:'0.38', category:'版本管理' },
  { name:'Hadoop MR', decline:'0.68', volatility:'0.47', category:'大数据' },
  { name:'Perl', decline:'0.65', volatility:'0.52', category:'编程语言' },
  { name:'AngularJS', decline:'0.86', volatility:'0.39', category:'前端框架' },
  { name:'CoffeeScript', decline:'0.93', volatility:'0.48', category:'编程语言' },
  { name:'Bower', decline:'0.97', volatility:'0.51', category:'包管理' },
  { name:'Grunt', decline:'0.89', volatility:'0.44', category:'构建工具' },
  { name:'Gulp', decline:'0.76', volatility:'0.40', category:'构建工具' },
  { name:'RequireJS', decline:'0.94', volatility:'0.49', category:'模块化' },
  { name:'Backbone.js', decline:'0.91', volatility:'0.43', category:'前端框架' },
  { name:'Ember.js', decline:'0.96', volatility:'0.50', category:'前端框架' },
  { name:'Bootstrap 3', decline:'0.88', volatility:'0.36', category:'CSS 框架' },
  { name:'PHP5', decline:'0.92', volatility:'0.45', category:'编程语言' },
  { name:'Ruby on Rails', decline:'0.84', volatility:'0.42', category:'后端框架' },
  { name:'Django 1.x', decline:'0.79', volatility:'0.37', category:'后端框架' },
  { name:'传统 SQL 优化', decline:'0.62', volatility:'0.33', category:'数据库' },
  { name:'Apache Ant', decline:'0.85', volatility:'0.46', category:'构建工具' },
  { name:'手写 Makefile', decline:'0.58', volatility:'0.31', category:'构建工具' },
  { name:'ECMAScript 5', decline:'0.83', volatility:'0.35', category:'编程语言' },
  { name:'Less', decline:'0.69', volatility:'0.32', category:'CSS 预处理' },
  { name:'Stylus', decline:'0.88', volatility:'0.41', category:'CSS 预处理' },
  { name:'Handlebars', decline:'0.90', volatility:'0.43', category:'模板引擎' },
  { name:'Mocha + Chai', decline:'0.61', volatility:'0.34', category:'测试' },
  { name:'PhantomJS', decline:'0.95', volatility:'0.52', category:'测试' },
  { name:'Windows Forms', decline:'0.93', volatility:'0.47', category:'桌面开发' },
  { name:'Silverlight', decline:'0.98', volatility:'0.53', category:'桌面开发' },
  { name:'ActionScript', decline:'0.97', volatility:'0.54', category:'编程语言' },
  { name:'JSP', decline:'0.87', volatility:'0.40', category:'后端技术' },
  { name:'Struts2', decline:'0.94', volatility:'0.48', category:'后端框架' },
  { name:'Hibernate XML', decline:'0.78', volatility:'0.36', category:'ORM' },
  { name:'SVN 分支策略', decline:'0.70', volatility:'0.33', category:'版本管理' },
  { name:'TFS', decline:'0.75', volatility:'0.38', category:'版本管理' },
  { name:'IBM MQ', decline:'0.66', volatility:'0.39', category:'中间件' },
  { name:'WebSphere', decline:'0.93', volatility:'0.49', category:'中间件' },
  { name:'传统 ETL', decline:'0.67', volatility:'0.35', category:'大数据' },
  { name:'DataStage', decline:'0.85', volatility:'0.44', category:'大数据' },
  { name:'Informatica', decline:'0.81', volatility:'0.42', category:'大数据' },
  { name:'SAS Base', decline:'0.77', volatility:'0.40', category:'数据分析' },
  { name:'传统 MATLAB', decline:'0.64', volatility:'0.34', category:'数据分析' },
  { name:'VBScript', decline:'0.96', volatility:'0.50', category:'脚本语言' },
  { name:'Pascal', decline:'0.92', volatility:'0.45', category:'编程语言' },
  { name:'Visual Basic 6', decline:'0.94', volatility:'0.48', category:'编程语言' },
  { name:'COBOL', decline:'0.97', volatility:'0.51', category:'编程语言' },
  { name:'手写汇编', decline:'0.89', volatility:'0.46', category:'编程语言' },
  { name:'传统 BI 报表', decline:'0.73', volatility:'0.37', category:'数据分析' },
  { name:'Crystal Reports', decline:'0.91', volatility:'0.47', category:'报表' },
  { name:'单体架构', decline:'0.68', volatility:'0.35', category:'架构' },
])

// ── 模组网格预览（由真实数据 ref 派生，接口落库后模块卡预览自动刷新）──
const previewPositions = computed(() => allPositions.value.slice(0, 3).map(p => ({ name: p.name, match: p.matchRate, salary: p.salary })))
const previewEvolution = computed(() => evolutionEvents.value.slice(0, 3).map(e => ({ date: e.date, label: `${e.skill} ${e.type}`, color: e.color })))
const previewDiscovery = computed(() => discoveredRoles.value.slice(0, 2).map(r => ({ name: r.name, verdict: r.verdict, color: r.verdictColor })))
const previewTicker = computed(() => [
  ...emergingSkills.value.slice(0, 2).map(s => ({ name: s.name, direction: 'up' as const, value: s.emergence })),
  ...decliningSkills.value.slice(0, 2).map(s => ({ name: s.name, direction: 'down' as const, value: s.decline })),
])

// ══ 真实数据接线（真实在前 + demo 补齐至 50 条）══
// 每个模块始终呈现 50 条详细数据：接口返回的真实条目置顶，demo 兜底补足余量；
// 接口失败 / 返回空时整列保留 demo。沿用 stores/personal.ts fetchSignalDetails 的 merge 惯例。

/** 真实条目在前，demo 补齐至 cap 条（默认 50）。双泛型：真实条目可带扩展字段，demo 兜底结构可更简 */
function fillTo<A, B>(real: A[], demo: B[], cap = 50): Array<A | B> {
  return [...real, ...demo].slice(0, cap)
}

// 人才需求：新兴/衰退技能排行 → /api/metrics/emerging + /api/metrics/declining
async function fetchRankings() {
  try {
    const em = await client.get('/api/metrics/emerging') as any
    const dec = await client.get('/api/metrics/declining') as any
    if (em?.emerging_skills?.length) {
      const real = em.emerging_skills.slice(0, 50).map((s: any) => ({
        name: s.name, emergence: Number(s.emergence || 0).toFixed(2),
        volatility: Number(s.volatility || 0).toFixed(2), category: '市场信号',
      }))
      emergingSkills.value = fillTo(real, emergingSkills.value)
    }
    if (dec?.declining_skills?.length) {
      const real = dec.declining_skills.slice(0, 50).map((s: any) => ({
        name: s.name, decline: Number(s.decline || 0).toFixed(2),
        volatility: Number(s.volatility || 0).toFixed(2), category: '市场信号',
      }))
      decliningSkills.value = fillTo(real, decliningSkills.value)
    }
  } catch { /* silent — demo 保留 */ }
}

// 新岗发现：流水线/AI 发现候选 → /api/enterprise/discovery（与 T4 新岗发现同源，按岗位名去重）
async function fetchDiscoveries() {
  try {
    const res = await client.get('/api/enterprise/discovery') as any
    const cands: any[] = res?.candidates || []
    if (!cands.length) return
    const seen = new Set<string>()
    const real = cands.filter((c: any) => {
      if (seen.has(c.title)) return false
      seen.add(c.title)
      return true
    }).map((c: any) => {
      const pending = !String(c.status || '').toLowerCase().includes('confirm')
      const pro: string[] = c.debatePoints?.pro || []
      const con: string[] = c.debatePoints?.con || []
      const source = c.source === 'agent' ? 'AI 辩论' : c.source === 'manual' ? '人工申报' : '流水线发现'
      return {
        name: c.title,
        verdict: pending ? 'Pending' : 'Confirmed',
        verdictColor: pending ? '#f59e0b' : 'var(--mint-500)',
        confidence: Number(c.confidence ?? 0.5).toFixed(2),
        description: pro[0] || con[0] || (pending ? '待评审候选岗位 · 等待 AI 辩论验证' : '候选岗位已通过验证'),
        skills: [...pro, ...con].slice(0, 8),
        evidenceCount: c.skillOverlap || 0,
        industry: source,
        source,
        discoveredAt: c.discoveredAt ? String(c.discoveredAt).slice(0, 10) : '',
      }
    })
    discoveredRoles.value = fillTo(real, discoveredRoles.value)
  } catch { /* silent — demo 保留 */ }
}

// 岗位演化：最热岗位（jd_count 最大）的真实月桶时间线。
// 用 /api/enterprise/positions/{id}/evolution —— 同源 MySQL 数据，节点含 label/marketDemand/summary，
// 比个人侧月桶接口（仅 from/to/summary）更适合渲染需求热度趋势。
function topPosition() {
  if (!store.positions.length) return null
  return [...store.positions].sort((a, b) => (b.jdCount || 0) - (a.jdCount || 0))[0]
}
async function fetchPositionEvolution() {
  const top = topPosition()
  if (!top) return
  try {
    const res = await client.get(`/api/enterprise/positions/${top.position_id}/evolution`) as any
    const tl: any[] = res?.timeline || []
    if (!tl.length) return
    const real = tl.map((t: any, i: number) => {
      const prev = i > 0 ? tl[i - 1].marketDemand : null
      let type = '需求'
      if (prev !== null) {
        if (t.marketDemand > prev) type = '上升'
        else if (t.marketDemand < prev) type = '回落'
        else type = '持平'
      }
      const color = type === '上升' ? 'var(--mint-500)' : type === '回落' ? 'var(--rose-500)' : 'var(--cyan-500)'
      return {
        date: t.label || String(t.date ?? '').replace(/^\d{4}-/, ''),
        type,
        skill: top.name,
        detail: t.summary || t.marketContext || '',
        color,
        // 详情弹窗扩展字段：真实节点自带 timeline 信息
        metric: `需求热度 ${t.marketDemand ?? 0}% · 月薪中位 ${t.salaryRange || '—'}`,
        sources: t.dataSources || [],
        related: (t.tools || []).slice(0, 8),
      }
    })
    evolutionEvents.value = fillTo(real, evolutionEvents.value)
  } catch { /* silent — demo 保留 */ }
}

// ── 图谱信号棱镜（按技能类别聚合，Silent Fallback）──
const graphBeams = computed(() => {
  const catCount = new Map<string, number>()
  store.skills.forEach(s => { catCount.set(s.category, (catCount.get(s.category) || 0) + 1) })
  const cats = [...catCount.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5)
  if (!cats.length) return [
    { source: 'AI/ML', label: 'AI/ML', count: 24, color: '#22d3ee', targetY: 70 },
    { source: '前端', label: '前端', count: 18, color: '#34d399', targetY: 140 },
    { source: '数据', label: '数据', count: 12, color: '#a855f7', targetY: 210 },
  ]
  const colors = ['#22d3ee', '#34d399', '#a855f7', '#fbbf24', '#fb7185']
  return cats.map(([label, count], i) => ({
    source: label, label, count,
    color: colors[i % colors.length],
    targetY: 50 + (i / Math.max(cats.length - 1, 1)) * 180,
  }))
})

onMounted(async () => {
  store.fetchSkills()
  store.fetchMatches()
  await store.fetchPositions()   // 岗位演化需岗位库先就绪（据此选最热岗位）
  fetchRankings()
  fetchDiscoveries()
  fetchPositionEvolution()
})
</script>

<style scoped>
@keyframes module-appear { from { opacity:0; transform:scale(0.92) translateY(12px); } to { opacity:1; transform:scale(1) translateY(0); } }
.module-grid-enter-active { transition:all 0.3s ease; }
.module-grid-leave-active { transition:all 0.2s ease; }
.module-grid-leave-to { opacity:0; transform:scale(0.95); }
.module-expand-enter-active { transition:all 0.35s ease; }
.module-expand-leave-active { transition:all 0.2s ease; }
.module-expand-enter-from { opacity:0; transform:scale(0.95) translateY(10px); }
.module-expand-leave-to { opacity:0; transform:scale(0.95); }
/* 演化节点详情弹窗 */
@keyframes detail-pop { from { opacity:0; transform:scale(0.94) translateY(8px); } to { opacity:1; transform:scale(1) translateY(0); } }
.detail-fade-enter-active { transition:all 0.25s ease; }
.detail-fade-leave-active { transition:all 0.18s ease; }
.detail-fade-enter-from, .detail-fade-leave-to { opacity:0; }
</style>
