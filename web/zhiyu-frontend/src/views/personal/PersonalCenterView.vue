<template>
  <div class="space-y-0">
    <!-- ═══════════════════════ 全息指挥台头部 ═══════════════════════ -->
    <div class="panel-neon holo-overlay scan-line-fast p-0 overflow-hidden shadow-deep">
      <div class="relative z-[3] flex flex-col lg:flex-row">
        <!-- 左侧：全息身份 -->
        <div class="flex-1 p-6 panel-circuit">
          <div class="flex items-center gap-5 relative z-[1]">
            <!-- 六角头像 — 霓虹发光 -->
            <HexAvatar :letter="userDisplayName.charAt(0)" :size="72" :stroke="2" :glow="12" />
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="tag-plate">COMMANDER</span>
                <span class="text-xs font-mono tracking-widest" style="color:var(--brand-400)">ID: ZM-{{ String(userLevel).padStart(3,'0') }}</span>
              </div>
              <h1 class="text-2xl font-bold tracking-tight data-segment" style="color:var(--text-primary)">{{ userDisplayName }}</h1>
              <p class="text-sm mt-1" style="color:var(--brand-400)">{{ userTitle }}</p>
            </div>
          </div>
        </div>
        <!-- 右侧：核心读数 — 7段数码管风格 -->
        <div class="lg:w-96 p-5 grid grid-cols-4 gap-0 panel-dark-zone" style="border-left:1px solid var(--brand-500); border-left-style: dashed">
          <div class="text-center p-2 relative">
            <div class="data-segment text-2xl text-brand-500 mb-0.5">{{ store.skillCount }}</div>
            <div class="text-xs tracking-widest" style="color:var(--text-muted)">SKILLS</div>
            <div class="absolute bottom-1 left-2 right-2 h-px bg-brand-500/20"></div>
          </div>
          <div class="text-center p-2 relative">
            <div class="data-segment text-2xl text-mint-500 mb-0.5">{{ store.bestMatch?.matchRate||'—' }}<span v-if="store.bestMatch" class="text-sm">%</span></div>
            <div class="text-xs tracking-widest" style="color:var(--text-muted)">MATCH</div>
            <div class="absolute bottom-1 left-2 right-2 h-px bg-mint-500/20"></div>
          </div>
          <div class="text-center p-2 relative">
            <div class="data-segment text-2xl text-cyan-500 mb-0.5">{{ careerMilestones.filter(m=>m.unlocked).length }}</div>
            <div class="text-xs tracking-widest" style="color:var(--text-muted)">MS</div>
            <div class="absolute bottom-1 left-2 right-2 h-px bg-cyan-500/20"></div>
          </div>
          <div class="text-center p-2 relative">
            <div class="data-segment text-2xl mb-0.5" :class="store.alertSkillCount>0?'text-rose-500':''" :style="{color:store.alertSkillCount>0?undefined:'var(--text-primary)'}">{{ store.alertSkillCount }}</div>
            <div class="text-xs tracking-widest" :class="store.alertSkillCount>0?'text-rose-400':''" :style="{color:store.alertSkillCount>0?undefined:'var(--text-muted)'}">ALERT</div>
            <div class="absolute bottom-1 left-2 right-2 h-px" :class="store.alertSkillCount>0?'bg-rose-500/30':''" style="background:rgba(255,255,255,0.08)"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ 结构梁分隔 ═══════════════════════ -->
    <div class="beam-divider"></div>

    <!-- ═══════════════════════ 选项卡 — 铭牌标签 ═══════════════════════ -->
    <div class="flex gap-0 overflow-x-auto px-1" style="border-bottom:2px solid var(--border-color)">
      <button v-for="tab in tabs" :key="tab.key"
        class="px-5 py-3 text-xs font-bold tracking-widest uppercase transition-all relative font-mono whitespace-nowrap"
        :style="{
          color: activeTab===tab.key ? tab.color : 'var(--text-muted)',
          borderBottom: activeTab===tab.key ? '2px solid '+tab.color : '2px solid transparent',
          marginBottom: '-2px',
          textShadow: activeTab===tab.key ? '0 0 8px '+tab.color : 'none'
        }"
        @click="activeTab = tab.key">
        <span class="w-1.5 h-1.5 rounded-full inline-block mr-1.5" :style="{background:tab.color, boxShadow:'0 0 6px '+tab.color}"></span>{{ tab.label }}
      </button>
    </div>

    <!-- ═══════════════════════ Tab 1: 职业档案 ═══════════════════════ -->
    <div v-if="activeTab==='profile'" class="pt-4 space-y-4">
      <!-- Row 1: 个人身份 + 求职意向 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- 左侧: 个人身份信息 -->
        <div class="panel-industrial panel-circuit shadow-deep p-5 relative">
          <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
          <div class="relative z-[1]">
            <div class="flex items-center gap-2 mb-4">
              <span class="tag-plate">IDENTITY</span>
              <h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">个人身份</h3>
            </div>
            <div class="grid grid-cols-2 gap-x-3 gap-y-3">
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">姓名</label><input v-model="editName" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" /></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">手机</label><input v-model="editPhone" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" /></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">邮箱</label><input v-model="editEmail" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" /></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">出生年份</label><select v-model="editBirthYear" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option v-for="y in birthYears" :key="y" :value="y">{{ y }}</option></select></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">当前状态</label><select v-model="editStatus" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>在职 — 观望机会</option><option>在职 — 暂不换</option><option>已离职</option><option>应届毕业生</option><option>自由职业</option></select></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">所在行业</label><select v-model="editIndustry" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>互联网/IT</option><option>金融/保险</option><option>制造业</option><option>教育/培训</option><option>医疗/健康</option><option>电商/零售</option><option>房地产/建筑</option><option>能源/环保</option></select></div>
            </div>
            <div style="border-top:1px solid var(--border-color);margin-top:16px;padding-top:12px">
              <div class="flex items-center gap-2 mb-3"><span class="tag-plate" style="color:var(--brand-400);border-color:var(--brand-500)">EDU</span><span class="text-xs font-bold tracking-wide uppercase" :style="{color:'var(--text-muted)'}">教育背景</span></div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">最高学历</label><select v-model="editEducation" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>本科</option><option>硕士</option><option>博士</option><option>大专</option></select></div>
                <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">专业</label><input v-model="editMajor" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" /></div>
                <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">英语水平</label><select v-model="editEnglish" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>CET-4</option><option>CET-6</option><option>IELTS 6.5+</option><option>TOEFL 90+</option><option>专业八级</option><option>无证书/流利</option></select></div>
              </div>
            </div>
          </div>
        </div>
        <!-- 右侧: 求职意向 + 简历 -->
        <div class="flex flex-col gap-4">
          <div class="panel-bridge shadow-deep p-5">
            <PanelHeader label="TARGET" title="求职意向" color="cyan" />
            <div class="grid grid-cols-2 gap-3">
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">期望职位</label><input v-model="editTargetRole" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" /></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">期望城市</label><input v-model="editTargetCity" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" /></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">期望行业</label><select v-model="editTargetIndustry" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>互联网/IT</option><option>金融/保险</option><option>AI/人工智能</option><option>电商/零售</option><option>教育/培训</option><option>不限</option></select></div>
              <div><label class="text-xs font-bold tracking-wide block mb-1" :style="{color:'var(--text-muted)'}">薪资期望 K/月</label><div class="flex items-center gap-2"><input v-model.number="editSalaryMin" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" placeholder="最低" /><span :style="{color:'var(--text-muted)'}">—</span><input v-model.number="editSalaryMax" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" placeholder="最高" /></div></div>
            </div>
            <div class="flex flex-wrap gap-2 mt-4">
              <span v-for="p in editPriorities" :key="p" class="text-xs px-2.5 py-1 font-mono transition-all cursor-pointer rounded-sm border" :style="editPriority===p?{background:'var(--brand-500)',color:'white',borderColor:'var(--brand-500)'}:{background:'var(--bg-secondary)',color:'var(--text-muted)',borderColor:'var(--border-color)'}" @click="editPriority=p">{{ p }}</span>
            </div>
            <div class="grid grid-cols-3 gap-2 mt-4">
              <div class="text-xs font-mono flex items-center gap-2 cursor-pointer" @click="editTravel = !editTravel"><span class="w-3 h-3 border-2 flex items-center justify-center" :style="{borderColor:editTravel?'var(--brand-500)':'var(--border-color)',background:editTravel?'var(--brand-500)':'transparent'}"><span v-if="editTravel" class="w-1.5 h-1.5 bg-white"></span></span>接受出差</div>
              <div class="text-xs font-mono flex items-center gap-2 cursor-pointer" @click="editRelocate = !editRelocate"><span class="w-3 h-3 border-2 flex items-center justify-center" :style="{borderColor:editRelocate?'var(--brand-500)':'var(--border-color)',background:editRelocate?'var(--brand-500)':'transparent'}"><span v-if="editRelocate" class="w-1.5 h-1.5 bg-white"></span></span>接受异地</div>
              <div><select v-model="editWorkMode" class="w-full px-2 py-1.5 text-xs border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>现场办公</option><option>混合办公</option><option>远程办公</option><option>不限</option></select></div>
            </div>
          </div>
          <!-- 简历上传 -->
          <div class="panel-asymmetric frame-mech p-4">
            <PanelHeader label="RESUME" title="简历" margin="sm" />
            <div class="border-2 border-dashed rounded-sm p-4 text-center transition-all cursor-pointer group hover:border-brand-400" :style="{borderColor:'var(--border-color)'}" @click="goResume">
              <svg class="w-8 h-8 mx-auto mb-1.5 opacity-30 group-hover:opacity-60 transition-opacity" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-linecap="round"/><polyline points="14 2 14 8 20 8" stroke-linecap="round"/><line x1="12" y1="18" x2="12" y2="12" stroke-linecap="round"/><line x1="9" y1="15" x2="15" y2="15" stroke-linecap="round"/></svg>
              <p class="text-xs font-bold" :style="{color:'var(--text-secondary)'}">上传 / 更新简历</p>
              <p class="text-xs mt-0.5" :style="{color:'var(--text-muted)'}">前往简历解析 · PDF · Word</p>
            </div>
          </div>
          <!-- 技能标签 -->
          <div class="panel-asymmetric p-4" style="border-color:color-mix(in srgb, var(--brand-500) 15%, transparent)">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold tracking-wide" :style="{color:'var(--text-muted)'}">SKILL TAGS</span>
              <div class="flex items-center gap-1.5">
                <input v-if="tagInputVisible" v-model="newTag" @keyup.enter="addSkillTag" @blur="cancelTag"
                  class="w-28 px-2 py-1 text-xs border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}" placeholder="技能名" />
                <button @click="tagInputVisible ? addSkillTag() : tagInputVisible = true" class="text-xs px-2 py-0.5 border font-mono transition-all hover:border-brand-400" :style="{color:'var(--text-muted)',borderColor:'var(--border-color)'}">{{ tagInputVisible ? 'OK' : '+ ADD' }}</button>
              </div>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(tag,i) in skillTags" :key="tag" class="tag-tilted" :style="{background:i<3?'color-mix(in srgb, var(--brand-500) 08%, transparent)':'var(--bg-secondary)',color:i<3?'var(--brand-500)':'var(--text-secondary)',borderColor:i<3?'color-mix(in srgb, var(--brand-500) 25%, transparent)':'var(--border-color)'}">{{ tag }}</span>
            </div>
          </div>
          <!-- 保鲜预警 -->
          <div class="panel-asymmetric p-3 panel-hazard" v-if="store.alertSkillCount>0">
            <div class="text-xs font-bold tracking-wide mb-2 flex items-center gap-1.5" :style="{color:'var(--text-primary)'}"><span class="w-1.5 h-1.5 rounded-full bg-rose-500" style="box-shadow:0 0 6px color-mix(in srgb, var(--rose-500) 50%, transparent)"></span>保鲜预警</div>
            <div class="flex flex-wrap gap-1.5"><span v-for="a in store.alerts" :key="a.skillName" class="text-xs px-2 py-0.5 font-mono rounded-sm" style="background:color-mix(in srgb, var(--rose-500) 08%, transparent);color:#f87171;border:1px solid color-mix(in srgb, var(--rose-500) 20%, transparent)">{{ a.skillName }} {{ a.currentFreshness }}%</span></div>
            <router-link to="/personal/freshness" class="text-xs font-mono tracking-wider mt-2 inline-block" style="color:var(--brand-400)">[ HANDLE ]</router-link>
          </div>
        </div>
      </div>
      <!-- 保存按钮 -->
      <div class="flex justify-end"><button @click="saveProfile" class="px-8 py-2.5 text-xs font-mono font-bold text-white transition-all hover:scale-105 shadow-deep" style="background:linear-gradient(135deg,var(--brand-600),var(--brand-500));clip-path:polygon(0 0,calc(100% - 10px) 0,100% 100%,0 100%);box-shadow:0 4px 20px color-mix(in srgb, var(--brand-500) 30%, transparent)">SAVE PROFILE</button></div>
    </div>

    <!-- ═══════════════════════ Tab 2: 技能总览 ═══════════════════════ -->
    <div v-if="activeTab==='skills'" class="pt-4 space-y-4">
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div class="lg:col-span-3 panel-neon panel-circuit p-4 shadow-deep">
          <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
          <div class="relative z-[1]">
            <div class="flex items-center gap-2 mb-3">
              <span class="tag-plate">RADAR</span>
              <h3 class="text-sm font-bold tracking-wide uppercase" :style="{color:'var(--text-primary)'}">技能雷达</h3>
            </div>
            <MatchRadar v-if="radarDims.length" :dimensions="radarDims" user-name="我的技能" :target-name="'行业基准'" />
          </div>
        </div>
        <div class="lg:col-span-2 space-y-2">
          <div v-for="cat in skillCategories" :key="cat.name" class="panel-asymmetric p-3 shadow-deep" style="background:var(--bg-card)">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="font-bold flex items-center gap-1.5" :style="{color:'var(--text-primary)'}"><span class="w-2 h-2 rounded-full" :style="{background:cat.color,boxShadow:'0 0 6px '+cat.color}"></span>{{ cat.name }}</span>
              <span class="font-mono data-segment text-sm" :style="{color:cat.color}">{{ cat.healthy }}/{{ cat.total }}</span>
            </div>
            <div class="h-1.5 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full transition-all duration-700" :style="{width:(cat.healthy/Math.max(cat.total,1)*100)+'%',background:cat.color}"></div></div>
            <div class="flex flex-wrap gap-1 mt-2">
              <span v-for="s in cat.skills" :key="s.name" class="text-xs px-1.5 py-0.5 rounded-sm font-mono transition-all hover:scale-105"
                :style="{background:s.status==='healthy'||s.status==='matched'?'color-mix(in srgb, var(--mint-500) 08%, transparent)':s.status==='alert'?'color-mix(in srgb, var(--amber-500) 08%, transparent)':'color-mix(in srgb, var(--rose-500) 06%, transparent)',color:s.status==='healthy'||s.status==='matched'?'var(--mint-500)':s.status==='alert'?'#f59e0b':'#f43f5e',border:'1px solid '+(s.status==='healthy'||s.status==='matched'?'color-mix(in srgb, var(--mint-500) 20%, transparent)':s.status==='alert'?'color-mix(in srgb, var(--amber-500) 20%, transparent)':'color-mix(in srgb, var(--rose-500) 15%, transparent)')}">{{ s.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ Tab 3: 匹配快照 ═══════════════════════ -->
    <div v-if="activeTab==='match'" class="pt-4 space-y-4">
      <div class="panel-neon p-5 shadow-deep">
        <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
        <div class="flex items-center justify-between mb-4">
          <PanelHeader label="MATCH" title="岗位匹配快照" margin="none" />
          <router-link to="/personal/match" class="text-xs font-mono tracking-wider" style="color:var(--brand-400)">[ FULL ANALYSIS ]</router-link>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div v-for="(m, idx) in store.matches" :key="m.id"
            class="p-4 transition-all lift-on-hover shadow-deep relative overflow-hidden holo-overlay"
            :style="{background:'var(--bg-card)',border:'1px solid var(--border-color)',borderTop:'3px solid '+(idx===0?'var(--brand-500)':idx===1?'var(--cyan-500)':'#f59e0b')}">
            <div class="relative z-[3]">
              <div class="flex items-center justify-between mb-2">
                <span class="tag-plate" :style="{color:idx===0?'var(--brand-400)':idx===1?'var(--cyan-400)':'#fbbf24',borderColor:idx===0?'var(--brand-500)':idx===1?'var(--cyan-500)':'#f59e0b'}">RANK {{ idx+1 }}</span>
                <span class="data-segment text-xl" :style="{color:idx===0?'var(--brand-500)':idx===1?'var(--cyan-500)':'#f59e0b'}">{{ m.matchRate }}%</span>
              </div>
              <h4 class="text-sm font-bold mb-1" :style="{color:'var(--text-primary)'}">{{ m.positionName }}</h4>
              <p class="text-xs mb-3" :style="{color:'var(--text-muted)'}">{{ m.company }} · {{ m.salaryRange }}</p>
              <div class="flex flex-wrap gap-1 mb-3">
                <span v-for="s in m.matchedSkills.slice(0,3)" :key="s" class="text-xs px-1.5 py-0.5 font-mono rounded-sm" style="background:color-mix(in srgb, var(--mint-500) 08%, transparent);color:var(--mint-500);border:1px solid color-mix(in srgb, var(--mint-500) 20%, transparent)">{{ s }}</span>
                <span v-for="s in m.missingSkills.slice(0,2)" :key="s" class="text-xs px-1.5 py-0.5 font-mono rounded-sm" style="background:color-mix(in srgb, var(--rose-500) 06%, transparent);color:#f87171;border:1px solid color-mix(in srgb, var(--rose-500) 15%, transparent)">+{{ s }}</span>
              </div>
              <router-link :to="'/personal/match'" class="text-xs font-mono tracking-wider" style="color:var(--brand-400)">[ DETAIL ]</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ Tab 4: 职业里程碑 ═══════════════════════ -->
    <div v-if="activeTab==='milestones'" class="pt-4 space-y-4">
      <div class="panel-industrial panel-circuit p-5 shadow-deep">
        <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
        <div class="relative z-[1]">
          <div class="flex items-center justify-between mb-4">
            <PanelHeader label="MS" title="职业里程碑" color="amber" margin="none" />
            <span class="text-xs font-mono" :style="{color:'var(--text-muted)'}">{{ careerMilestones.filter(m=>m.unlocked).length }}/{{ careerMilestones.length }} UNLOCKED</span>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 spring-list">
            <div v-for="m in careerMilestones" :key="m.id"
              class="p-4 text-center transition-all lift-on-hover relative"
              :class="m.unlocked?'shadow-deep':''"
              :style="{background:m.unlocked?'var(--bg-card)':'var(--bg-secondary)',border:'1px solid '+(m.unlocked?m.color:'var(--border-color)'),opacity:m.unlocked?1:0.55}">
              <div class="absolute top-2 right-2"><span class="text-xs px-1.5 py-0.5 font-mono font-bold rounded-sm" :style="{background:m.rarityBg,color:m.rarityColor,border:'1px solid '+m.rarityColor}">{{ m.rarity }}</span></div>
              <div class="text-3xl mb-2" :style="{filter:m.unlocked?'drop-shadow(0 0 8px '+m.color+')':'grayscale(1) opacity(0.4)'}">{{ m.icon }}</div>
              <h4 class="text-sm font-bold mb-1" :style="{color:m.unlocked?'var(--text-primary)':'var(--text-muted)'}">{{ m.name }}</h4>
              <p class="text-xs mb-2" :style="{color:'var(--text-muted)'}">{{ m.desc }}</p>
              <div class="h-1.5 progress-track-dark" style="background:var(--bg-secondary)"><div class="h-full transition-all" :style="{width:Math.min(m.progress/m.target*100,100)+'%',background:m.unlocked?'var(--mint-500)':m.color}"></div></div>
              <span class="text-xs font-mono mt-1 inline-block" :style="{color:m.unlocked?'var(--mint-500)':'var(--text-muted)'}">{{ m.unlocked ? 'ACHIEVED' : m.progress+'/'+m.target }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════ Tab 5: 偏好设置 ═══════════════════════ -->
    <div v-if="activeTab==='prefs'" class="pt-4 space-y-4">
      <div class="panel-industrial p-5 shadow-deep">
        <div class="rivet" style="top:10px;left:10px"></div><div class="rivet" style="top:10px;right:10px"></div>
        <PanelHeader label="PREFS" title="职业偏好" color="cyan" />
        <div class="max-w-lg space-y-4">
          <div>
            <label class="text-xs font-bold tracking-wide block mb-1.5" :style="{color:'var(--text-muted)'}">关注岗位方向</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="role in targetRoles" :key="role" class="text-xs px-3 py-1.5 font-mono transition-all" :style="selectedRoles.includes(role)?{background:'var(--brand-500)',color:'white',boxShadow:'0 0 12px color-mix(in srgb, var(--brand-500) 30%, transparent)'}:{background:'var(--bg-secondary)',color:'var(--text-muted)',border:'1px solid var(--border-color)'}" @click="toggleRole(role)">{{ role }}</button>
            </div>
          </div>
          <div>
            <label class="text-xs font-bold tracking-wide block mb-1.5" :style="{color:'var(--text-muted)'}">薪资期望 (K/月)</label>
            <div class="flex items-center gap-3"><input v-model.number="salaryMin" type="range" min="10" max="100" step="5" class="flex-1" /><span class="text-xs font-mono font-bold data-segment" style="color:var(--text-primary)">{{ salaryMin }}K — {{ salaryMax }}K</span></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="text-xs font-bold tracking-wide block mb-1.5" :style="{color:'var(--text-muted)'}">意向城市</label><select v-model="prefCity" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>北京</option><option>上海</option><option>深圳</option><option>杭州</option><option>成都</option><option>广州</option></select></div>
            <div><label class="text-xs font-bold tracking-wide block mb-1.5" :style="{color:'var(--text-muted)'}">保鲜通知频率</label><select v-model="notifyFreq" class="w-full px-3 py-2 text-sm border font-mono" :style="{background:'var(--bg-card)',color:'var(--text-primary)',borderColor:'var(--border-color)'}"><option>每周</option><option>每月</option><option>每季度</option><option>关闭</option></select></div>
          </div>
          <button @click="savePreferences" class="px-6 py-2 text-xs font-mono font-bold text-white transition-all hover:scale-105" style="background:linear-gradient(135deg,var(--brand-600),var(--brand-500));clip-path:polygon(0 0,calc(100% - 10px) 0,100% 100%,0 100%);box-shadow:0 4px 16px color-mix(in srgb, var(--brand-500) 30%, transparent)">SAVE PREFERENCES</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePersonalStore } from '@/stores/personal'
import { useNotify } from '@/composables/useNotify'
import { useScrollReveal } from '@/composables/useScrollReveal'
import HexAvatar from '@/components/common/HexAvatar.vue'
import PanelHeader from '@/components/common/PanelHeader.vue'
import MatchRadar from '@/components/personal/MatchRadar.vue'
import type { RadarDimension } from '@/components/personal/MatchRadar.vue'

const store = usePersonalStore()
const { show: notify } = useNotify()
useScrollReveal()

const editName = ref('张明')
const editTitle = ref('高级前端开发工程师')
const editPhone = ref('138****6789')
const editEmail = ref('zhangming@email.com')
const editBirthYear = ref(1995)
const editStatus = ref('在职 — 观望机会')
const editIndustry = ref('互联网/IT')
const editEducation = ref('本科')
const editMajor = ref('计算机科学与技术')
const editEnglish = ref('CET-6')
const editExperience = ref('5-8年')
const editCity = ref('北京')
const editTargetRole = ref('AI 算法工程师')
const editTargetCity = ref('北京/上海')
const editTargetIndustry = ref('AI/人工智能')
const editSalaryMin = ref(35)
const editSalaryMax = ref(60)
const editPriority = ref('技术成长')
const editPriorities = ['薪资优先','技术成长','工作生活平衡','平台稳定','团队氛围']
const editTravel = ref(false)
const editRelocate = ref(true)
const editWorkMode = ref('混合办公')
const router = useRouter()
function goResume(){ router.push('/personal/resume') }

const birthYears = Array.from({length:30},(_,i)=>2026-18-i) // 18岁到48岁

const userDisplayName = computed(() => editName.value)
const userTitle = computed(() => editTitle.value)
const userLevel = ref(24)

const tabs = [
  { key:'profile', label:'职业档案', color:'var(--brand-400)' },
  { key:'skills', label:'技能总览', color:'#10b981' },
  { key:'match', label:'匹配快照', color:'#06b6d4' },
  { key:'milestones', label:'职业里程碑', color:'#f59e0b' },
  { key:'prefs', label:'偏好设置', color:'#a855f7' },
]
const activeTab = ref('profile')

const radarDims = computed<RadarDimension[]>(() => {
  const cats = new Map<string,{total:number;healthy:number}>()
  store.skills.forEach(s=>{const c=cats.get(s.category)||{total:0,healthy:0};c.total++;if(s.freshness>=60)c.healthy++;cats.set(s.category,c)})
  return [...cats.entries()].map(([name,v])=>({name,userScore:Math.round((v.healthy/Math.max(v.total,1))*100),targetScore:85,max:100}))
})

const skillCategories = computed(() => {
  const catMap = new Map<string,{name:string;total:number;healthy:number;skills:{name:string;status:string;freshness:number}[],color:string}>()
  const colors = ['var(--brand-500)','#06b6d4','#10b981','#f59e0b','#a855f7','#f43f5e']; let ci=0
  store.skills.forEach(s=>{const c=catMap.get(s.category)||{name:s.category,total:0,healthy:0,skills:[],color:colors[ci++%colors.length]};c.total++;if(s.freshness>=60)c.healthy++;c.skills.push({name:s.name,status:s.status,freshness:s.freshness});catMap.set(s.category,c)})
  return [...catMap.values()]
})

interface Milestone { id:number;name:string;desc:string;icon:string;rarity:string;rarityBg:string;rarityColor:string;color:string;unlocked:boolean;progress:number;target:number }
const demoMilestones: Milestone[] = [
  { id:1,name:'首次匹配',desc:'完成第一次人岗匹配',icon:'◆',rarity:'COMMON',rarityBg:'rgba(107,114,128,0.1)',rarityColor:'#6b7280',color:'#6b7280',unlocked:true,progress:1,target:1},
  { id:2,name:'技能图谱',desc:'掌握8项以上可识别技能',icon:'◈',rarity:'RARE',rarityBg:'color-mix(in srgb, var(--brand-500) 10%, transparent)',rarityColor:'var(--brand-500)',color:'var(--brand-500)',unlocked:true,progress:12,target:8},
  { id:3,name:'保鲜达人',desc:'连续3个月保鲜度>80%',icon:'▲',rarity:'RARE',rarityBg:'color-mix(in srgb, var(--brand-500) 10%, transparent)',rarityColor:'var(--brand-500)',color:'var(--brand-500)',unlocked:true,progress:3,target:3},
  { id:4,name:'跨界突破',desc:'完成一次转行分析',icon:'⬢',rarity:'EPIC',rarityBg:'color-mix(in srgb, var(--purple-500) 10%, transparent)',rarityColor:'#a855f7',color:'#a855f7',unlocked:false,progress:0,target:1},
  { id:5,name:'顶尖匹配',desc:'匹配度达到85%',icon:'★',rarity:'EPIC',rarityBg:'color-mix(in srgb, var(--purple-500) 10%, transparent)',rarityColor:'#a855f7',color:'#a855f7',unlocked:false,progress:72,target:85},
  { id:6,name:'学习路径',desc:'完成一条学习路径',icon:'⌖',rarity:'RARE',rarityBg:'color-mix(in srgb, var(--brand-500) 10%, transparent)',rarityColor:'var(--brand-500)',color:'var(--brand-500)',unlocked:false,progress:2,target:5},
  { id:7,name:'薪资跃升',desc:'匹配薪资达期望',icon:'◉',rarity:'EPIC',rarityBg:'color-mix(in srgb, var(--purple-500) 10%, transparent)',rarityColor:'#a855f7',color:'#a855f7',unlocked:false,progress:0,target:1},
  { id:8,name:'全栈专家',desc:'掌握5个领域技能',icon:'❖',rarity:'LEGENDARY',rarityBg:'color-mix(in srgb, var(--amber-500) 10%, transparent)',rarityColor:'#d4a574',color:'#f59e0b',unlocked:false,progress:4,target:5},
]
// 真实 /api/personal/milestones 覆盖 demo（Silent Fallback）
const careerMilestones = computed<Milestone[]>(() => {
  if (!store.milestones.length) return demoMilestones
  const rarityMeta: Record<string, { bg: string; color: string }> = {
    common: { bg: 'rgba(107,114,128,0.1)', color: '#6b7280' },
    rare: { bg: 'color-mix(in srgb, var(--brand-500) 10%, transparent)', color: 'var(--brand-500)' },
    epic: { bg: 'color-mix(in srgb, var(--purple-500) 10%, transparent)', color: '#a855f7' },
    legendary: { bg: 'color-mix(in srgb, var(--amber-500) 10%, transparent)', color: '#d4a574' },
  }
  const colors = ['#6b7280', 'var(--brand-500)', '#06b6d4', '#10b981', '#f59e0b', '#a855f7', '#f43f5e', '#d4a574']
  return store.milestones.map((m, i) => {
    const meta = rarityMeta[(m.rarity || 'common').toLowerCase()] || rarityMeta.common
    return {
      id: m.id, name: m.name, desc: m.description, icon: m.icon || '◆',
      rarity: (m.rarity || 'COMMON').toUpperCase(),
      rarityBg: meta.bg, rarityColor: meta.color, color: colors[i % colors.length],
      unlocked: m.unlocked, progress: m.progress, target: m.target,
    }
  })
})

const targetRoles = ['AI工程师','全栈开发','大数据工程师','AI产品经理','ML Engineer','数据架构师']
const selectedRoles = ref(['AI工程师','全栈开发'])
const salaryMin = ref(30); const salaryMax = ref(60)
const prefCity = ref('北京'); const notifyFreq = ref('每月')
function toggleRole(role:string){const i=selectedRoles.value.indexOf(role);if(i>=0)selectedRoles.value.splice(i,1);else selectedRoles.value.push(role)}
function saveProfile(){notify('✓ 档案已保存',`${editName.value} 的职业档案已更新`,'success')}
function savePreferences(){notify('✓ 偏好已保存','求职偏好设置已更新','success')}
const skillTags = ref(['Python','TypeScript','React','深度学习','NLP','SQL','Docker','系统设计'])
const tagInputVisible = ref(false)
const newTag = ref('')
function addSkillTag() {
  const tag = newTag.value.trim()
  if (tag) { skillTags.value.push(tag); notify('TAG 已添加', `技能标签 "${tag}" 已添加`, 'info') }
  newTag.value = ''
  tagInputVisible.value = false
}
function cancelTag() { newTag.value = ''; tagInputVisible.value = false }

function applyProfile() {
  const p = store.profile
  if (!p) return
  if (p.name) editName.value = p.name
  if (p.title) editTitle.value = p.title
  if (p.phone) editPhone.value = p.phone
  if (p.email) editEmail.value = p.email
  if (p.birthYear) editBirthYear.value = p.birthYear
  if (p.status) editStatus.value = p.status
  if (p.industry) editIndustry.value = p.industry
  if (p.education) editEducation.value = p.education
  if (p.major) editMajor.value = p.major
  if (p.englishLevel) editEnglish.value = p.englishLevel
  if (p.experienceYears) editExperience.value = `${p.experienceYears}年`
  if (p.city) editCity.value = p.city
  if (p.targetRole) editTargetRole.value = p.targetRole
  if (p.targetCity) editTargetCity.value = p.targetCity
  if (p.targetIndustry) editTargetIndustry.value = p.targetIndustry
  if (p.salaryMin) editSalaryMin.value = p.salaryMin
  if (p.salaryMax) editSalaryMax.value = p.salaryMax
  if (p.priority) editPriority.value = p.priority
  if (p.travelOk != null) editTravel.value = p.travelOk
  if (p.relocateOk != null) editRelocate.value = p.relocateOk
  if (p.workMode) editWorkMode.value = p.workMode
}

onMounted(async () => {
  await Promise.all([store.fetchSkills(), store.fetchMatches(), store.fetchFreshness(), store.fetchProfile(), store.fetchMilestones()])
  applyProfile()
})
</script>
