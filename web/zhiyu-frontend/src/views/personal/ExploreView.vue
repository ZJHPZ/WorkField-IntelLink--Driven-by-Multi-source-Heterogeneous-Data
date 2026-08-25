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
                  <div v-for="s in previewTicker" :key="s.name" class="flex items-center gap-2">
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
                    <span class="text-[11px] font-bold" style="color:var(--text-primary)">{{ pos.name }}</span>
                    <span class="tag-plate text-[7px]" :style="{color:pos.type==='新兴'?'var(--cyan-400)':'var(--text-muted)',borderColor:pos.type==='新兴'?'var(--cyan-500)':'var(--border-color)'}">{{ pos.type }}</span>
                  </div>
                  <div class="flex items-center gap-3 text-[8px]" style="color:var(--text-muted)">
                    <span>{{ pos.skillCount }} skills</span><span>{{ pos.salary }}</span><span>{{ pos.techStack }}</span>
                  </div>
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
                    <h2 class="text-lg font-bold mb-3" style="color:var(--text-primary)">{{ selectedPosition.name }}</h2>
                    <div class="grid grid-cols-3 gap-2 mb-4">
                      <div class="panel-asymmetric p-2 text-center"><div class="text-[7px] tracking-widest" style="color:var(--text-muted)">SALARY</div><div class="data-segment text-sm" style="color:var(--mint-500)">{{ selectedPosition.salary }}</div></div>
                      <div class="panel-asymmetric p-2 text-center"><div class="text-[7px] tracking-widest" style="color:var(--text-muted)">CITY</div><div class="data-segment text-sm" style="color:var(--text-primary)">{{ selectedPosition.city }}</div></div>
                      <div class="panel-asymmetric p-2 text-center"><div class="text-[7px] tracking-widest" style="color:var(--text-muted)">EXP</div><div class="data-segment text-sm" style="color:var(--text-primary)">{{ selectedPosition.exp }}</div></div>
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
                <div v-for="(ev, i) in evolutionEvents" :key="ev.date" class="flex gap-4">
                  <div class="flex flex-col items-center w-3"><span class="w-3 h-3 rounded-full flex-shrink-0" :style="{background:ev.color,boxShadow:'0 0 6px '+ev.color}"></span><div v-if="i < evolutionEvents.length-1" class="w-px flex-1 my-1" style="background:var(--border-color)"></div></div>
                  <div class="pb-5 flex-1"><div class="flex items-center gap-2 mb-1"><span class="data-segment text-[10px]" :style="{color:ev.color}">{{ ev.date }}</span><span class="tag-plate text-[7px]" :style="{color:ev.color,borderColor:ev.color}">{{ ev.type }}</span></div><p class="text-[11px] font-bold" style="color:var(--text-primary)">{{ ev.skill }}</p><p class="text-[9px] mt-0.5" style="color:var(--text-muted)">{{ ev.detail }}</p></div>
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
                <div class="text-[9px] font-mono" style="color:var(--text-muted)">{{ role.evidenceCount }} JDs · {{ role.industry }}</div>
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
              <div class="relative z-[1]"><div class="flex items-center gap-2 mb-3"><span class="w-1.5 h-1.5 rounded-full bg-mint-500" style="box-shadow:0 0 4px var(--mint-500)"></span><span class="text-[9px] tracking-widest" style="color:var(--mint-400)">EMERGING TOP 6</span></div>
                <div class="space-y-2"><div v-for="(s, i) in emergingSkills" :key="s.name" class="flex items-center gap-2"><span class="data-segment text-[9px] w-4 text-center" style="color:var(--text-muted)">{{ String(i+1).padStart(2,'0') }}</span><span class="flex-1 text-[10px] font-mono" style="color:var(--text-primary)">{{ s.name }}</span><span class="data-segment text-[10px]" style="color:var(--mint-500)">{{ s.emergence }}</span></div></div>
              </div>
            </div>
            <div class="panel-asymmetric p-5 shadow-deep relative">
              <div class="rivet" style="top:8px;left:8px"></div>
              <div class="relative z-[1]"><div class="flex items-center gap-2 mb-3"><span class="w-1.5 h-1.5 rounded-full bg-rose-500" style="box-shadow:0 0 4px var(--rose-500)"></span><span class="text-[9px] tracking-widest" style="color:var(--rose-400)">DECLINING TOP 6</span></div>
                <div class="space-y-2"><div v-for="(s, i) in decliningSkills" :key="s.name" class="flex items-center gap-2"><span class="data-segment text-[9px] w-4 text-center" style="color:var(--text-muted)">{{ String(i+1).padStart(2,'0') }}</span><span class="flex-1 text-[10px] font-mono" style="color:var(--text-primary)">{{ s.name }}</span><span class="data-segment text-[10px]" style="color:var(--rose-500)">{{ s.decline }}</span></div></div>
              </div>
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
import SignalPrism from '@/components/personal/SignalPrism.vue'

const store = usePersonalStore()
const activeModule = ref<string|null>(null)
const selectedPosition = ref<any>(null)
const activeFilters = ref<string[]>([])

function expandModule(key: string) { activeModule.value = key }
function collapseModule() { activeModule.value = null; selectedPosition.value = null }

// ── 岗位库预览 ──
const previewPositions = [
  { name:'AI 算法工程师', match:72, salary:'40-70K' },
  { name:'全栈开发工程师', match:85, salary:'30-50K' },
  { name:'大数据工程师', match:52, salary:'35-60K' },
]

// ── 演化预览 ──
const previewEvolution = [
  { date:'Q3', label:'RAG 新增为必备', color:'var(--mint-500)' },
  { date:'Q2', label:'DeepSpeed 升级', color:'var(--mint-500)' },
  { date:'Q1', label:'Theano 删除', color:'var(--rose-500)' },
]

// ── 新岗发现预览 ──
const previewDiscovery = [
  { name:'RAG 工程师', verdict:'Pending', color:'#f59e0b' },
  { name:'MLOps 工程师', verdict:'Confirmed', color:'var(--mint-500)' },
]

// ── 人才需求预览 ticker ──
const previewTicker = [
  { name:'RAG', direction:'up', value:'2.96' },
  { name:'DeepSpeed', direction:'up', value:'2.41' },
  { name:'jQuery', direction:'down', value:'0.82' },
  { name:'Theano', direction:'down', value:'0.95' },
]

// ── 岗位库数据 ──
const techStacks = ['人工智能', '大数据', '智能系统', '物联网']
const allPositions = computed(() => {
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
  let list = allPositions.value
  if (activeFilters.value.length) list = list.filter(p => activeFilters.value.includes(p.techStack))
  return [...list].sort((a,b) => b.matchRate - a.matchRate)
})
function toggleFilter(s:string){const i=activeFilters.value.indexOf(s);if(i>=0)activeFilters.value.splice(i,1);else activeFilters.value.push(s)}
function selectPosition(p:any){selectedPosition.value=p}
function isUserSkill(n:string){return store.skills.some(s=>s.name.toLowerCase()===n.toLowerCase())}

// ── 演化数据 ──
const evolutionEvents = [
  { date:'2026-Q3', type:'新增', skill:'RAG 检索增强生成', detail:'多条 JD 新增为必备技能，emergence 2.96', color:'var(--mint-500)' },
  { date:'2026-Q2', type:'新增', skill:'DeepSpeed 分布式训练', detail:'大模型岗位要求从加分升级为必备', color:'var(--mint-500)' },
  { date:'2026-Q1', type:'修改', skill:'Transformer 置信度提升', detail:'从 0.68 → 0.82，跨 JD 验证通过', color:'var(--brand-500)' },
  { date:'2025-Q4', type:'删除', skill:'Theano', detail:'市场需求归零，decline 0.95', color:'var(--rose-500)' },
  { date:'2025-Q3', type:'新增', skill:'LoRA/QLoRA 微调', detail:'大模型微调岗位新增必备技能', color:'var(--mint-500)' },
]

// ── 新岗发现数据 ──
const discoveredRoles = [
  { name:'RAG 工程师', verdict:'Pending', verdictColor:'#f59e0b', confidence:'0.7', description:'负责检索增强生成系统的设计与落地，连接大模型与企业知识库', skills:['RAG','向量数据库','LangChain','Embedding'], evidenceCount:6, industry:'AI/知识管理' },
  { name:'MLOps 工程师', verdict:'Confirmed', verdictColor:'var(--mint-500)', confidence:'0.85', description:'负责模型全生命周期管理，从训练到部署到监控的工程化', skills:['Docker','Kubernetes','MLflow','Airflow','CI/CD'], evidenceCount:12, industry:'AI/工程化' },
]

// ── 人才需求数据 ──
const emergingSkills = [{ name:'RAG', emergence:'2.96' },{ name:'DeepSpeed', emergence:'2.41' },{ name:'LoRA', emergence:'2.15' },{ name:'Transformer', emergence:'1.89' },{ name:'LangChain', emergence:'1.72' },{ name:'FSDP', emergence:'1.55' }]
const decliningSkills = [{ name:'jQuery', decline:'0.82' },{ name:'Theano', decline:'0.95' },{ name:'Hadoop MR', decline:'0.68' },{ name:'SVN', decline:'0.71' },{ name:'Flash', decline:'0.98' },{ name:'Perl', decline:'0.65' }]

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

onMounted(() => { store.fetchSkills(); store.fetchMatches() })
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
</style>
