# 职域智联 · 深空舰桥工业风格设计系统

> 版本: v2.0  
> 更新: 2026-08-03  
> 设计定位: 打破 AI 辅助设计的"玻璃态+对称圆角+同质装饰"三大套路，打造像真实战舰操控台一样的沉浸式 B 端体验。

---

## 一、设计哲学

### 核心原则

> 每个像素都让用户相信这是一艘真实战舰的操控面板，而不是 Bootstrap 变了个颜色。

| 原则 | 说明 |
|------|------|
| **拒绝圆角通胀** | 用 `clip-path` 切角、不对称圆角替代统一 `rounded-2xl` |
| **材质层次分化** | 三种面板三种身份：装甲板 / 控制台 / 辅助面板 |
| **光效代替装饰** | 用霓虹发光、全息扫描、数码管替代装饰性 emoji 和渐变条 |
| **工业细节真实** | 铆钉、电路纹、告警斜纹、结构梁——让人相信是真实建造的 |
| **排版纪律** | 等宽字体 + 全大写 + 宽字距 + LED 指示点 |

### 从"AI味"到"工程感"

| AI 套路 | 新风格替代 |
|---------|-----------|
| `glass-card rounded-2xl` 玻璃态泛滥 | `panel-industrial` / `panel-bridge` / `panel-neon` 三种面板 |
| `grid-cols-2/3` 对称强迫 | 5列/7列不对称网格，错位布局 |
| 四角L形/渐变光条 同质装饰 | 铆钉螺丝 + 电路走线 + 结构梁 + 告警斜纹 |
| 扁平 backdrop-blur | 四层纵深阴影 `shadow-deep` |
| emoji 图标 | SVG 工业图标 + CSS 状态点 + 等宽铭牌 |

---

## 二、面板系统 (六大核心面板)

### 2.1 panel-industrial — 重型装甲板

```css
特点: 右下切角 + 16px坐标网格 + 铆钉区 + 厚阴影
用途: 页面头部、主要数据区
应用: 所有页面的标题头部、匹配排行、技能详情
```

### 2.2 panel-bridge — 舰桥控制台

```css
特点: 左上切角 + 浅阴影 + 金属侧边
用途: 次级数据面板、表单区
应用: 雷达图、曲线图、简历上传
```

### 2.3 panel-asymmetric — 辅助面板

```css
特点: 2px/24px 不对称圆角 + 轻薄边框
用途: 侧边栏、标签区、告警卡片
应用: 保鲜预警、技能标签、侧边信息
```

### 2.4 panel-neon — 霓虹核心显示器

```css
特点: 发光边框 + neon-flicker 微闪 + 内发光
用途: 最重要的数据展示区
应用: 灯塔面板、等级进阶、可行性仪表盘、AI面板
```

### 2.5 panel-circuit — 电路纹面板

```css
特点: 纯CSS PCB走线(水平/垂直线+焊盘圆点)
用途: 数据密集区、雷达图容器
应用: 技能星图、匹配雷达详情
```

### 2.6 panel-hazard — 告警斜纹面板

```css
特点: repeating-linear-gradient(-45deg) 黄黑/白黑条纹(顶部8px)
用途: 预警/告警区域
应用: 保鲜预警面板
```

---

## 三、TOP 5 亮眼设计

### 1. 全息指挥台头部
```
panel-neon + holo-overlay + scan-line-fast + data-segment 四层叠加
→ 发光边框、全息扫描纹、垂直扫描线、7段数码管读数同时运行
应用: PersonalCenterView 头部
```

### 2. 电路纹面板
```
纯CSS实现PCB走线纹——水平/垂直线 + 6个焊盘圆点
不需要任何图片资源
暗色下若隐若现，浅色下加深为工程蓝图质感
应用: 技能星图、匹配雷达
```

### 3. 浅色/深色双轨自适应
```
不是简单的"调透明度"
深色"发光" → 浅色"印刷"
网格从白色发光线 → 黑色工程线
data-segment 从 text-shadow 发光 → text-shadow:none
铭牌从黑底 → 浅灰底
面板阴影从48px黑 → 24px浅
```

### 4. 告警斜纹
```
repeating-linear-gradient(-45deg) 实现的黄黑/白黑 hazard stripe
只在预警面板顶部8px出现，工业感极强且不干扰阅读
应用: FreshnessView 预警区、PersonalCenterView 保鲜区
```

### 5. 结构梁分隔
```
渐变金属横梁 + ◆菱形铭牌
替代传统 <hr> 或边框线，让分隔本身成为设计元素
应用: 头部与内容之间、导航与底部之间
```

---

## 四、装饰系统

### 4.1 铆钉螺丝 (.rivet)
```
5px 金属渐变圆点，四角定位
深色: 亮螺丝 (白色高光)
浅色: 暗螺丝 (灰色高光)
```

### 4.2 工业铭牌 (.tag-plate)
```
等宽大写 + LED指示点 + 1px边框
深色: 黑底 rgba(0,0,0,0.4) + 品牌色字
浅色: 浅灰底 rgba(0,0,0,0.05) + 深品牌色字
```

### 4.3 斜角便签 (.tag-tilted)
```
transform: rotate(-2deg) + 投影
杂志排版风格，打破严肃感
```

### 4.4 7段数码管 (.data-segment)
```
Courier New 等宽 + text-shadow 发光 + 闪烁光标
深色: 0 0 8px + 0 0 16px currentColor
浅色: 隐藏发光效果
```

### 4.5 巨型数据读数 (.data-giant)
```
等宽 + 负字距 + 0.9行高
用于核心KPI展示
```

### 4.6 全息覆盖 (.holo-overlay)
```
渐变色光 + 水平扫描线 + holo-scan 6秒循环动画
模拟全息投影投射在面板上
```

### 4.7 快速扫描线 (.scan-line-fast)
```
2秒周期垂直扫描线
用于指挥台头部面板
```

### 4.8 结构梁 (.beam-divider)
```
渐变金属横梁 + ◆菱形铭牌
页内主要分区之间使用
```

### 4.9 纵深阴影 (.shadow-deep)
```
四层阴影: 1px/4px/12px/24px (浅色)
四层阴影: 1px/4px/12px/48px (深色)
配合 lift-on-hover 悬浮抬升
```

### 4.10 机械双层边框 (.frame-mech)
```
border-image 渐变 + outline-offset -6px
双层边框模拟机械框架
```

### 4.11 芯片模块 (.nav-chip)
```
clip-path 八角切角 + border-image 金属渐变 + ::after 引脚条纹
每个导航项像一颗独立IC芯片
悬停 → 边框变品牌色通电
激活 → 引脚变红工作态
```

### 4.12 侧边栏深度 (.sidebar-depth)
```
border-image 从上到下渐变(高光→边框色→暗面) + 投影落在主板
控制台模块凸起于基板之上
```

### 4.13 主板纹理 (.main-board)
```
24px网格覆盖 0.02-0.025透明度
主体区域作为"基板/底板"
```

---

## 五、色彩系统

### 5.1 主题模式

| 属性 | dark (企业) | light (企业) | warm (个人深色) | warm-light (个人浅色) |
|------|-----------|-------------|----------------|---------------------|
| 品牌色 | #818cf8 indigo | #6366f1 | #e8536c rose | #e8536c |
| 背景 | 深空黑 | #f1f5f9 slate | 深空黑 | #fdf2f4 pink |
| 卡片 | rgba(15,23,42,0.55) | #ffffff | rgba(15,23,42,0.55) | #ffffff |
| 文字 | #e2e8f0 | #1e293b | #e2e8f0 | #1e293b |

### 5.2 语义色

| Token | 色值 | 个人侧语义 | 企业侧语义 |
|-------|------|----------|-----------|
| mint | #10b981 | 健康技能 / 匹配成功 | 已验证 |
| cyan | #06b6d4 | 匹配目标 / 学习路径 | 新兴技能 |
| amber | #f59e0b | 保鲜预警 / 待关注 | 待验证 |
| rose | #f43f5e | 高危缺失 / 紧急预警 | 已拒绝 |

---

## 六、排版规范

| 元素 | 字体 | 字重 | 字距 | 大小写 |
|------|------|------|------|--------|
| 面板标题 | system-ui | bold | tracking-wide | uppercase |
| 数据读数 | Courier New | 700 | -0.03em | — |
| 铭牌标签 | Courier New | 700 | 0.08em | uppercase |
| 导航项 | system-ui | bold | tracking-wide | — |
| 正文 | system-ui | normal | normal | — |
| 代码/ID | Courier New | normal | tracking-wider | uppercase |

---

## 七、页面改造清单

### 已完成 (15/15)

| 页面 | 路由 | 主要面板 | 特色装饰 |
|------|------|---------|---------|
| DashboardView | /personal | panel-industrial + bridge + asymmetric | holo-overlay, scan-line-fast, data-segment, panel-circuit, MatchOrbit 轨道 |
| ProfileView | /personal/profile | panel-neon + industrial + bridge | holo-overlay, circuit, 星图SVG发光 (SkillConstellation), 芯片模块卡片 |
| MatchView | /personal/match | panel-bridge + neon + industrial | holo-overlay, circuit, data-segment, MatchRadar |
| MatchCompareView | /personal/match/compare | panel-hazard 头部 + 镜像 A/B 面板 + 中心 panel-neon | MatchRadar, 得分条 |
| ExploreView | /personal/explore | 六种面板模块中心 + data-segment 编号 | 模块预览卡 (图谱区待接 SignalPrism) |
| LearningPathView | /personal/learning-path | panel-industrial + asymmetric | data-segment, 步骤节点发光, spring-list |
| ResumeView | /personal/resume | panel-circuit 扫描头 + industrial | holo-overlay, 扫描进度 |
| FreshnessView | /personal/freshness | panel-neon + industrial + hazard | holo-overlay, 灯塔光束 (LighthouseBeacon), 告警斜纹, 半衰期分布 |
| SwitchView | /personal/switch | panel-neon + industrial + circuit + bridge | holo-overlay, scan-line-fast, SVG韦恩图 |
| GrowthView | /personal/growth | panel-neon + industrial + bridge | holo-overlay, 进化链 (EvolutionChain), 等级发光 |
| ChatView | /personal/chat | panel-neon + industrial | holo-overlay, scan-line-fast, beam-divider, 全息指挥台 |
| PersonalCenterView | /personal/center | panel-neon + industrial + bridge + asymmetric + hazard | **全部10种装饰** |
| SpectrumView | /personal/spectrum | panel-industrial + ProgressRing | stat-box, src-chip, source-bars 条形码, 信号光谱 |
| SpectrumDetailView | /personal/spectrum/:skill | panel-neon + circuit + dark-zone | SpectrumOscilloscope 示波器, 证据链卡片, CRT 扫描线 |
| EvolutionTheaterView | /personal/evolution | panel-hazard 头部 + industrial | 齿轮轨时间轴, data-giant 变更摘要, spring-list |
| App.vue (侧边栏) | — | sidebar-depth + nav-chip + main-board | 电路纹, 扫描线, 芯片模块, 主板纹理 |

---

## 八、CSS 文件结构

```
src/styles/
├── variables.css      # CSS 变量 (4主题)
├── base.css           # 全局重置
├── animations.css     # 20+ 关键帧动画
├── dark-override.css  # 深色模式覆盖
├── markdown.css       # Markdown 内容样式
├── utilities.css      # 舰桥风格工具类 (860+ 行)
└── tailwind.css       # Tailwind 指令
```

### utilities.css 包含

- 6 种面板类 (industrial / bridge / asymmetric / neon / circuit / hazard)
- 铆钉螺丝 (.rivet)
- 工业铭牌 (.tag-plate)
- 斜角便签 (.tag-tilted)
- 7段数码管 (.data-segment)
- 巨型读数 (.data-giant)
- 全息覆盖 (.holo-overlay)
- 快速扫描线 (.scan-line-fast)
- 结构梁 (.beam-divider)
- 纵深阴影 (.shadow-deep)
- 机械边框 (.frame-mech)
- 芯片模块 (.nav-chip / .nav-chip-active)
- 侧边栏深度 (.sidebar-depth)
- 主板纹理 (.main-board)
- 悬浮抬升 (.lift-on-hover)
- 面板暗区 (.panel-dark-zone)
- 进度条轨道 (.progress-track-dark)
- 网格覆盖 (.grid-overlay)
- 噪点纹理 (.noise-texture)
- 全部浅色/深色双轨适配

---

## 九、组件库

```
src/components/
├── common/
│   ├── CosmicBackground.vue    # 星空背景 (80星+数据流线)
│   ├── ProgressRing.vue        # SVG渐变进度环
│   ├── HudCell.vue             # 数值 KPI 格
│   ├── NotificationBar.vue     # 通知条 (个人胶囊 / 企业纸面双变体)
│   ├── HolographicBackdrop.vue # Three.js 全息背景
│   └── ...
├── personal/
│   ├── MatchRadar.vue          # ECharts 双系列雷达图
│   ├── MatchOrbit.vue          # 岗位环绕轨道
│   ├── SkillConstellation.vue  # 技能星座图
│   ├── LighthouseBeacon.vue    # 技能保鲜灯塔
│   ├── EvolutionChain.vue      # 成长进化链
│   ├── SpectrumOscilloscope.vue # 信号示波器 (工业风参考实现)
│   └── SignalPrism.vue         # 粒子棱镜
```

---

## 十、素材资源

```
src/assets/icons/   # SVG 导航图标 (手机/笔记本/书包/副业/保险/飞机/篮球/鼠标)
sucai/              # 原始图标素材库
```

### 导航图标映射

| 导航项 | SVG | 寓意 |
|--------|-----|------|
| 个人主页 | 手机.svg | 个人化智能设备 |
| 技能画像 | 笔记本.svg | 专业分析与画像 |
| 人岗匹配 | 副业兼职.svg | 岗位匹配机会 |
| 学习路径 | 书包.svg | 学习与成长 |
| 技能保鲜 | 保险证件.svg | 技能保护与保鲜 |
| 转行分析 | 飞机.svg | 职业新航向 |
| 成长轨迹 | 打篮球.svg | 实践中的成长 |
