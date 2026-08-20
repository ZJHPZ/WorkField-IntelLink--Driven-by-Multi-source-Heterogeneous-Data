# 职域智联 · 企业侧设计系统：「蓝皮书 · 权威纸面」

> 版本: v1.0
> 日期: 2026-08-18
> 配色来源: `web/微信图片_20260730114710_875_57-粉.png`（深海蓝 + 珊瑚粉）
> 设计定位: 打破 AI 辅助设计的"玻璃态+圆角胶囊+浅灰白底"套路，把 B 端岗位标准管理做成**一份正在生效的制度蓝皮书**。

---

## 一、设计哲学

### 一句话定位

> HR 打开页面，看到的是"一份正在生效的岗位标准蓝皮书"——每一屏像一页正式发布的制度文档：深蓝印刷骨架、珊瑚印章标注需要 HR 决策的关键信息、数据以报表引线的形式排布。**产品的行为（发布岗位标准）与视觉（签署文件）合一。**

### 核心原则

| 原则 | 说明 |
|------|------|
| **纸面优先** | 内容浮在浅纸面上，深蓝做结构骨架，珊瑚做唯一彩色情绪 |
| **印章代替胶囊** | 状态 = 方形墨印（微旋转 + 墨晕），不是圆角胶囊 |
| **报表代替卡片堆** | 列表用引线点（·······）+ 右对齐数值，咨询/财务报告排法 |
| **稀缺辉光** | 全系统**唯一发光色 = 珊瑚粉**，只给需决策的信息。光越少越珍贵 |
| **双线纪律** | 分隔用"深蓝粗线 + 珊瑚细线"双轨，替代个人侧的金属梁 |
| **固定浅纸面** | 企业侧恒为浅色纸面，不随全局暗色主题走，与个人侧明暗彻底分离 |

### 从"AI味"到"权威文件"

| AI 套路 | 新风格替代 |
|---------|-----------|
| `glass-card rounded-xl` 玻璃卡 | `panel-doc` 白纸卡 + 细深蓝边 + 左上角章 |
| `bg-brand-gradient` 渐变横幅 | `doc-masthead` 深蓝文件抬头 + 珊瑚印章 |
| 圆角胶囊状态徽章 | `seal-chip` 方形墨印印章 |
| 卡片网格堆叠 | `leader-row` 引线点报表行 |
| 多色霓虹辉光 | 珊瑚单色稀缺辉光 `coral-glow` |
| emoji 图标 | 墨色 SVG / 章形图标 |

---

## 二、色彩系统

### 2.1 主色板（源自参考图）

| Token | 色值 | 用途 |
|-------|------|------|
| `--ent-navy` | `#00094C` | 品牌主色：抬头、标题、主按钮、深蓝印章 |
| `--ent-navy-900` | `#121A57` | 深蓝 hover / 渐变过渡 |
| `--ent-navy-700` | `#1E2A5A` | 侧栏、次级深蓝 |
| `--ent-coral` | `#C85C56` | 强调/亮点：珊瑚印章、KPI、待验证、选中态 |
| `--ent-coral-mid` | `#D68984` | 次级珊瑚 / 渐变 |
| `--ent-coral-soft` | `#EAD2D0` | 珊瑚浅底 / 描边 |
| `--ent-paper` | `#F5F6F8` | 页面底色（纸面） |
| `--ent-card` | `#FFFFFF` | 卡片纸面 |
| `--ent-ink` | `#16213E` | 正文墨色 |
| `--ent-ink-muted` | `#5B6478` | 次要文字 |
| `--ent-rule` | `#D9DDE7` | 分隔线 |
| `--ent-dim` | `#9AA1B1` | 中性 / 稳定 / 禁用 |

### 2.2 语义映射（企业侧独有）

| 状态 | 视觉 | Token |
|------|------|-------|
| 已确认 / 已验证 / 健康 | **深海蓝印章**（权威盖章） | `--ent-navy` |
| 待验证 / 预警 / 新兴 | **珊瑚印章 + 辉光**（需 HR 决策 → 唯一亮色） | `--ent-coral` |
| 稳定 / 中性 | 灰墨 | `--ent-dim` |
| 衰退 / 驳回 / 严重 | **褪色墨 + 删除线**（修订稿里划掉的内容） | `faded-ink` |

### 2.3 与个人侧色板关系

企业侧**不复用**个人侧的 brand 靛蓝、霓虹辉光、全大写工业铭牌。两者共享的只有 mono 数据字体习惯。企业侧是独立的第三套色板（深蓝+珊瑚+纸面），不写入全局 `variables.css` 的四个主题，而是由 `enterprise.css` 以 `.ent-shell` 作用域自带。

---

## 三、四大签名亮点

### 亮点 1：深蓝文件抬头 + 珊瑚印章（`doc-masthead` / `seal-chip`）

- 每个页头 = 一份正式文件抬头：深海蓝渐变通栏，右侧一枚珊瑚印章
- 状态徽章 = **方形墨印印章**：1.5px 珊瑚描边 + `rotate(-1deg)` + 内层墨晕 + 微光
- 隐喻：HR 在"盖章发布"岗位标准

```css
.doc-masthead {
  background: linear-gradient(135deg, #00094C, #121A57 60%, #1E2A5A);
  color: #fff;
  border-bottom: 2px solid var(--ent-coral); /* 珊瑚收边 = 文件下划线 */
}
.seal-chip {
  transform: rotate(-1deg);
  border: 1.5px solid var(--ent-coral);
  background: rgba(200,92,86,0.06);
  box-shadow: inset 0 0 0 1px rgba(200,92,86,0.15), 0 0 10px rgba(200,92,86,0.08);
}
```

### 亮点 2：章节编号系统（`.section-head`）

- 每个面板标题 = `01` 等宽大编号 + 名称 + 双线分隔（深蓝粗线 2px + 珊瑚细线 1px）
- 替代个人侧的铆钉/金属梁，制度文件的章节结构

### 亮点 3：引线点报表行（`.leader-row`）

- 列表行 = 标签 + `·······` 引线 + 右对齐 mono 数值，经典财务/咨询报告排法
- 岗位、技能、诊断、候选人全部走引线报表，**一眼是"报表"不是"卡片堆"**

### 亮点 4：珊瑚稀缺辉光（`.coral-glow`）

- 全系统唯一发光 = 珊瑚粉 `text-shadow: 0 0 8px rgba(200,92,86,0.35)`
- 只给关键 KPI、待验证印章、重点操作
- 与个人侧霓虹多色辉光反衬：个人=热闹多光，企业=克制单光

---

## 四、排版规范

| 元素 | 字体 | 字重 | 说明 |
|------|------|------|------|
| 文件抬头/品牌名 | Georgia / 宋体 | bold | 衬线题头，文件气质 |
| 章节标题 | system-ui | bold | 深蓝 |
| 数据读数/编号 | Courier New | 700 | 沿用系统 mono 习惯 |
| 印章文字 | Courier New | 700 | 大写 + 宽字距 |
| 正文 | system-ui | normal | 墨色 |

---

## 五、组件签名清单

| 组件 | 旧（占位玻璃） | 新（蓝皮书） |
|------|--------------|-------------|
| 面板 | `glass-card rounded-xl` | `panel-doc`：白纸卡 + 1px 细边 + 左上角小章 |
| 页头 | `bg-brand-gradient` 横幅 | `doc-masthead`：深蓝抬头 + 珊瑚印章 + 珊瑚下划线 |
| 状态 | 圆角胶囊 `rounded-full` | `seal-chip`：方形墨印 + 微旋转 + 晕染（navy/coral/dim/faded 四态） |
| 列表行 | `flex` 卡片 | `leader-row`：标签 · 引线点 · mono 数值 |
| KPI | `HudCell` 玻璃格 | `stat-tile`：白卡 + 深蓝大数字 + 珊瑚辉光（高亮项） |
| 按钮 | `bg-brand-500 rounded-lg` | `ent-btn`：深蓝底 + 白色文字；hover 珊瑚辉光 |
| 分隔 | `border-t` | `section-rule` 双线：深蓝粗 + 珊瑚细 |
| 衰退 | `opacity-60` 灰 | `faded-ink`：灰蓝 + 删除线（修订稿） |
| 背景 | CosmicBackground 星云 | `paper-backdrop`：浅纸面 + 24px 细网格 |
| 侧栏 | 深空芯片模块 | 制度目录 TOC：深蓝底 + 白色目录项 + 珊瑚激活左线 |

---

## 六、侧栏改造（企业侧 = 制度目录）

企业侧侧栏是"文件目录"而非"控制台"：

- 背景：深海蓝 `--ent-navy` 通体
- 导航项：无芯片切角，白字 + 1px 珊瑚左线激活态 + 悬停浅白底
- 顶部 Logo：文件题头（衬线）样式
- 底部：珊瑚色"盖章"版用户区

---

## 七、页面改造清单

| 页面 | 路由 | 主要签名 |
|------|------|---------|
| Dashboard | /enterprise | doc-masthead + stat-tile + leader-row 岗位报表 + section-head 双栏 |
| Positions | /enterprise/positions | 章节表 + seal-chip 状态列 |
| PositionDetail | /enterprise/positions/:id | doc-masthead + 演化 timeline 报表 |
| Discovery | /enterprise/discovery | section-head + seal-chip 待验证珊瑚辉光 |
| Diagnose | /enterprise/diagnose | 章节报告 + EnergyBar 换珊瑚语义条 |
| Team | /enterprise/team | 热力图 + 引线表 |
| Forecast | /enterprise/forecast | 章节编号 + 趋势 |
| Graph | /enterprise/graph | 深蓝节点 + 珊瑚高亮 |

> 样板页：DashboardView 先按此规范改造验收，确认后铺开其余视图。

---

## 八、CSS 结构

```
src/styles/enterprise.css   # 企业侧独立工具类（本规范全部签名）
```

- 不与 utilities.css 混用；企业侧视图只引 enterprise.css 的类
- 外壳层：App.vue 在 `/enterprise` 下给 shell 加 `data-side="enterprise"`，enterprise.css 据此接管侧栏/背景/内容区
- 个人侧文件与类（panel-*、rivet、nav-chip 等）**禁止**进入企业侧视图

---

## 九、验收锚点

1. 打开 `/enterprise` 是**浅纸面**（不随主题切到深色）
2. 页头是深蓝抬头 + 珊瑚印章，不是渐变横幅
3. 列表是引线点报表行，不是卡片堆
4. 待验证/预警是珊瑚印章 + 辉光（全页唯一发光）
5. 衰退/驳回是褪色墨 + 删除线
6. 侧栏是深蓝制度目录，不是 IC 芯片模块
7. 与个人侧 `/personal` 并排看：一暗一浅、一工业一文件，**完全不像同一套模板换皮**
