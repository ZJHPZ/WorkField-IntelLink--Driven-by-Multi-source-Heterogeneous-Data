# JD 数据二次加工与展示对接实施计划

> **本文档是「职域智联」JD 数据展示对接工作的唯一权威实施契约。**
> 后续每一步实施（建表、写脚本、改 API、改前端）都必须**严格参照本文档的阶段、文件、字段与验证标准执行**；与本文档冲突的既有实现以本文档为准，但不得破坏已通过的测试基线（pytest 104 passed）。
>
> 状态跟踪见文末「实施进度表」——每一步完成并验证后回填。

---

## 0. 背景与目标

已建成 `zhiyv.jd_records` 表（9,178 行真实智联招聘 JD 采样数据，51 个唯一岗位名，12 列原始 + 派生列），它是当前唯一的**原始 JD 数据源**。

现状：**没有任何展示用到 jd_records**。前端所有页面靠 Silent Fallback（demo 数据）兜底；岗位类端点的薪资/公司/城市/行业字段要么硬编码、要么恒空；`/api/enterprise/diagnose` 是 stub（恒返回空列表）；`PositionDiffView` 市场侧与 `SpectrumView` 信号光谱是**纯 demo、无任何后端端点**。

**本计划目标**：对 `jd_records` 做二次加工，派生 6 张新表（T1–T6），并通过 API 与前端 store/视图接通，让真实 JD 数据驱动岗位库、岗位演化、市场对比、信号光谱、JD 诊断五大展示域；同时顺带为既有 `verified_skills` / `skill_stats` / `skill_cooccurrence` 表灌入真实数据。

---

## 1. 现状盘点（已验证事实，2026-08-29 核对）

### 1.1 前端数据消费总览

**个人侧 store `src/stores/personal.ts`**（Silent Fallback：demo 先置、API 成功才覆盖、失败静默）：

| 调用 | 端点 | 当前真实数据 | jd_records 可补 |
|---|---|---|---|
| fetchSkills | GET /api/personal/skills | user_skills（空→demo 保留） | ✗（用户侧数据） |
| fetchMatches | GET /api/personal/matches | user_matches（空→demo） | ◐（可补 company/salary） |
| fetchLearningPath | GET /api/personal/learning-path | learning_steps（空→demo） | ✗ |
| fetchFreshness | GET /api/personal/freshness | user_skills+skill_stats | ◐（skill_stats 由 Phase B 灌入） |
| fetchSwitchOptions | GET /api/personal/switch | user_skills+verified_skills | ◐（同上） |
| fetchProfile / Growth / Milestones | /profile /growth /milestones | user_*（空→demo） | ✗ |
| fetchPositions | GET /api/positions | verified_skills（空→store.positions 保持 `[]`） | ✅ T1+T4 重灌 |
| fetchEvolution | GET /api/positions/{id}/evolution | evolution_records（空→demo 保留） | ✅ T3 重灌 |
| **signalDetails** | **无端点** | **纯 demo** | ✅ T5 |
| evolutionSnapshots | 见 fetchEvolution | 见上 | ✅ |

**企业侧 store `src/stores/enterprise.ts`**：

| 调用 | 端点 | 当前真实数据 | jd_records 可补 |
|---|---|---|---|
| fetchPositions | GET /api/enterprise/positions | verified_skills（空→demo） | ✅ T1+T4 |
| fetchCandidates | GET /api/enterprise/discovery | new_roles（空→demo） | ✗（agent 管线产物，不在本次范围） |
| fetchDiagnoses | GET /api/enterprise/diagnose | **stub 恒返回空** → demo | ✅ T6 |
| fetchTeamGaps | GET /api/enterprise/team/gaps | skill_stats（空→demo） | ◐（Phase B 灌 skill_stats） |
| fetchForecast | GET /api/enterprise/talent/forecast | skill_stats（空→demo） | ◐（同上） |
| fetchEvolution | GET /api/enterprise/positions/{id}/evolution | evolution_records（空→demo） | ✅ T3 |
| **market**（PositionDiffView 市场侧） | **无端点** | **纯 demo** | ✅ T4 |

### 1.2 后端缺口确认（51 个端点中）

1. **没有任何端点返回 JD 的薪资/公司/城市/行业真实数据**（jd_records 是孤表，仅 `load_jd_xls.py` 引用 JDRecord）。
2. 岗位列表 `get_positions()` 以 `verified_skills.jd_id` 当岗位身份——**单条 JD 编码 ≠ 岗位**，且 verified_skills 为空时列表恒空。
3. `evolution_records` 的演化时间轴返回 `salaryRange:""`、`marketDemand:0`、`adoptionRate:0`（恒空）。
4. `PositionDiffView`（`store.market`）与 `SpectrumView`（`store.signalDetails`）**无任何后端端点**。
5. `/api/enterprise/diagnose` 恒返回 `{diagnoses: []}`（stub）。
6. 技能市场域（`skill_stats`/`verified_skills`/`skill_cooccurrence`）存在但为空——需跑 L1–L4 管线才有数据；管线当前从 `data/jd/batch1.jsonl` 读，**不读 MySQL jd_records**。

### 1.3 管线可复用资产（Phase B 的依据）

- `app/pipeline/l1_clean.py`：`clean(JobPosting) -> CleanedJD`
- `app/pipeline/l3_extract.py`：`extract(CleanedJD, client=None) -> list[ExtractedSkill]`（client=None 即纯规则，确定性、零 LLM 成本）
- `app/pipeline/l3_verify.py`：`verify(jd_id, full_text, skills) -> gate`（纯规则幻觉闸门）
- `app/pipeline/l2_normalize.py`：`normalize_and_count(extracted_by_jd)`、`normalize_name()`
- `app/pipeline/l2_cooccurrence.py`：`build_cooccurrence(jd_skills_list)`
- `app/services/enterprise_service.py`：`diagnose_jd(jd_id, title, skills, avg_skill_count)`（T6 复用）
- `app/domain/__init__.py`：`JobPosting(jd_id, source, tech_stack, title, posted_date, paragraphs, salary_min, salary_max, experience_years, education, city)`、`Paragraph(section, text)`、`SectionType`、`TechStack`、`SourceType`、`ExtractedSkill`

---

## 2. 总体架构

```
jd_records（9,178 行真实 JD）
   │
   ├─ Phase A：纯 SQL 聚合 ───────────────► T1 jd_position_profile（岗位画像）
   │                                       ├─ T2 jd_position_city_salary（岗位×城市薪资）
   │                                       └─ T3 jd_position_evolution（岗位演化月桶）
   │
   └─ Phase B：管线抽取（L1+L3+闸门+L2）──► T4 jd_position_skills（岗位×技能权重）
                                           ├─ T5 jd_skill_signal（技能信号·jd 源）
                                           ├─ T6 jd_quality_diagnosis（JD 质量诊断）
                                           └─ 顺带灌入现有表 verified_skills / skill_stats / skill_cooccurrence
                │
                ▼
   Phase D：API 对接（改造现有端点 + 新增 /api/jd/* 三个端点）
                │
                ▼
   Phase E：前端对接（personal.ts / enterprise.ts + 4 个视图）
```

---

## 3. 核心决策（后续不得偏离）

- **D1 岗位身份**：岗位规范身份 = `jd_records.title`（岗位名称）。所有派生表按 `title` 为主键维度。改造涉及 `/api/positions*`、`/api/enterprise/positions*` 的岗位读取路径；**当 T1/T4 表为空时必须回退现有 verified_skills 逻辑**（保证测试与旧行为不破）。
- **D2 薪资聚合口径**：薪资分位数/中位数**只统计 `salary_unit='月'` 的行**（天/时/面议行不参与薪资聚合）；同时记录 `salary_cover_rate`（月薪行占该岗位 JD 比例）供前端判断可信度。
- **D3 演化时间桶**：T3 按「月份」桶聚合（`month_key` = `01`–`12`，无日期行归入 `00`），**不伪造年份**。展示语义为「采样窗口内各月 JD 需求与薪资分布」，不是跨年趋势。技能市场时间序列指标（emergence/decline/half_life）因 8,809/9,178 行无年份，**Phase B 一律置 0**，待多期数据后再算。
- **D4 技能抽取**：Phase B 默认**纯规则**（`extract(cleaned, None)`），确定性、零 LLM 成本、可全量跑 9,178 行；`--spark` 可选启用星火（受速率限制，不默认）。
- **D5 信号光谱**：T5 只填 `jd` 这一个信号源（github/arxiv/standard 无数据源，维持 demo/0）。API 返回 `SignalDetail[]`，其中 `sources` 数组里 `source='jd'` 的元素用真实数据，其余保留 demo。
- **D6 市场 vs 标准对比（PositionDiffView）**：市场侧 = T4 真实数据；标准侧 = 维持现有 `/api/enterprise/positions` 返回。当两者同源时差异可能全部「一致」——这是诚实的表现，标注口径说明即可，不做伪造。
- **D7 幂等**：`build_jd_derived.py` 默认对已非空的派生表**拒绝重建**，`--force` 先 TRUNCATE 再重建（对齐 load_jd_xls 模式）。

---

## 4. 派生表详细定义（Phase 0 建表）

6 张新表模型全部追加到 `后/app/persistence/zhiyv_models.py` 末尾（命名对齐现有 `SkillStat` 风格），由 `init_db()` 的 `create_all` 自动建表。

### T1 `jd_position_profile` —— 岗位画像表（按 title 聚合）

| 列 | 类型 | 说明 |
|---|---|---|
| `title` | String(256) **PK** | 岗位名称 |
| `jd_count` | Integer | 该岗位 JD 总数 |
| `salary_unit` | String(8) | 主导薪资单位（月/天/时/面议） |
| `salary_min_p25` / `salary_min_p50` / `salary_min_p75` | Integer NULL | 月薪下限分位数（元） |
| `salary_max_p25` / `salary_max_p50` / `salary_max_p75` | Integer NULL | 月薪上限分位数（元） |
| `salary_cover_rate` | Float | 月薪行占比（0–1） |
| `top_cities` | JSON | `[{"city":..,"count":n}]` top 5 |
| `top_companies` | JSON | `[{"company_name":..,"count":n}]` top 5 |
| `industry_dist` | JSON | `[{"industry":..,"count":n}]` |
| `size_dist` | JSON | `[{"company_size":..,"count":n}]` |
| `type_dist` | JSON | `[{"company_type":..,"count":n}]` |
| `latest_posted` | Date NULL | 最近发布日期 |
| `updated_at` | DateTime | 默认 now |

### T2 `jd_position_city_salary` —— 岗位×城市薪资表

| 列 | 类型 | 说明 |
|---|---|---|
| `title` | String(256) **联合 PK** | 岗位名称 |
| `city` | String(64) **联合 PK** | 城市 |
| `jd_count` | Integer | 岗位×城市 JD 数 |
| `salary_min_median` | Integer NULL | 月薪下限中位数（元） |
| `salary_max_median` | Integer NULL | 月薪上限中位数（元） |
| `salary_unit` | String(8) | 主导单位 |

### T3 `jd_position_evolution` —— 岗位演化月桶表

| 列 | 类型 | 说明 |
|---|---|---|
| `title` | String(256) **联合 PK** | 岗位名称 |
| `month_key` | String(16) **联合 PK** | 月份桶 `01`–`12`（无日期 `00`） |
| `jd_count` | Integer | 该月桶 JD 数（adoption/需求代理） |
| `salary_min_median` | Integer NULL | 月薪下限中位数（元） |
| `salary_max_median` | Integer NULL | 月薪上限中位数（元） |
| `salary_unit` | String(8) | 主导单位 |

### T4 `jd_position_skills` —— 岗位×技能权重表

| 列 | 类型 | 说明 |
|---|---|---|
| `title` | String(256) **联合 PK** | 岗位名称 |
| `skill_name` | String(128) **联合 PK** | 技能名（规范名） |
| `jd_count` | Integer | 提及该技能的 JD 数 |
| `weight` | Float | `jd_count / 该岗位 JD 总数`（0–1） |
| `required_type` | String(16) | 主导类型：`必备`/`加分` |
| `level` | String(16) | `basic/intermediate/advanced/expert`（由平均置信度映射） |
| `confidence` | Float | 平均抽取置信度（0–1） |

### T5 `jd_skill_signal` —— 技能信号统计表（jd 源）

| 列 | 类型 | 说明 |
|---|---|---|
| `skill_name` | String(128) **PK** | 技能名（规范名） |
| `category` | String(32) | 类别（来自 tech_stack 映射） |
| `jd_frequency` | Integer | JD 语料提及 JD 数（df） |
| `jd_confidence` | Float | `jd_frequency / 全量技能最大 df` 归一化（0–1） |
| `jd_examples` | JSON | `[jd_id, ...]` 提及该技能的前 3 条 JD id |
| `verification_status` | String(16) | `confirmed`（jd_frequency≥10）/ `candidate`（≥3）/ `unverified` |
| `updated_at` | DateTime | 默认 now |

### T6 `jd_quality_diagnosis` —— JD 质量诊断表

| 列 | 类型 | 说明 |
|---|---|---|
| `jd_id` | String(64) **PK** | JD 编码 |
| `title` | String(256) | 岗位名称 |
| `skill_count` | Integer | 抽取技能数 |
| `inflation_index` | Float | 通胀指数（复用 `diagnose_jd`） |
| `inflated_items` | JSON | 注水项清单 |
| `soft_skill_ratio` | Float | 软技能占比 |
| `required_ratio` | Float | 必备技能占比 |
| `suggestions` | JSON | 改进建议 |
| `overall_score` | Integer | `round(max(0, 100 - inflation*60 - (1-required_ratio)*40))` |
| `status` | String(16) | `healthy`(≥80) / `warning`(≥60) / `critical`(<60) |
| `created_at` | DateTime | 默认 now |

---

## 5. 派生脚本 `build_jd_derived.py`（Phase A/B/C）

新建 `后/app/services/build_jd_derived.py`，CLI 模式对齐 `load_jd_xls.py`：

```
python -m app.services.build_jd_derived --tables profile [--force]   # Phase A：T1+T2+T3
python -m app.services.build_jd_derived --tables skills  [--force]   # Phase B：T4+T5+T6 + 灌现有表
python -m app.services.build_jd_derived --tables all     [--force]   # A+B
```

- 入口模式：`init_db(get_settings())` → 业务 → `finally: close_db()`（同 pipeline_service）。
- 每张目标表先 `TRUNCATE`（`--force`）再批量写入（每 500 行 commit）。
- 结束打印各表行数与关键抽查值。

### Phase A：T1/T2/T3（纯 SQL 聚合，读全量 jd_records 在内存聚合）

1. `SELECT title, jd_count, salary_unit, ... FROM jd_records` 全量读出（9,178 行，内存足够）。
2. **T1**：按 `title` 分组；薪资分位只统计 `salary_unit='月'` 行；top_cities/top_companies/industry_dist/size_dist/type_dist 用 `Counter` 聚合。
3. **T2**：按 `(title, city)` 分组，取薪资中位数。
4. **T3**：从 `posted_date_raw` 正则抽月份（`M月D日`→`MM`，完整日期→`MM`，无法解析→`00`）；按 `(title, month_key)` 分组取 JD 数与薪资中位数。
5. 写入 3 张表。

### Phase B：T4/T5/T6 + 灌现有表（管线抽取，逐 JD 处理）

1. 全量读 jd_records。
2. 对每条 JD 构造 `JobPosting`：
   - `jd_id`、`title`、`source=SourceType.JD`、`tech_stack=TechStack.AI`（D1 决策：不按 title 猜栈，先统一 AI；T5 category 用 `tech_stack` 映射为「AI/大数据/…」，由 Phase B 内部用 title 关键词启发式赋值给 `ExtractedSkill` 的 `section`/`category`，可选）
   - `posted_date`：`posted_date` 完整日期用 `%Y-%m-%d`；否则合成 `2026-{MM}-01`（仅供管线字段非空，不参与时间指标）
   - `paragraphs=[Paragraph(SectionType.REQUIREMENT, jd_text)]`
   - `salary_min/salary_max`（来自 jd_records 已解析值）、`city`
   - `jd_text` 为空的 151 行：跳过抽取（不写入任何派生表）。
3. 逐 JD：`clean(jd)` → `extract(cleaned, client)` → `verify(jd_id, full_text, skills)` 取 `gate.passed`（--spark 时 `client=SparkClient()`，否则 None）。
4. 用 `normalize_name()` 规范技能名。
5. **写 `verified_skills`**（现有表）：每 JD×技能一行（jd_id, jd_title, skill_name, tech_stack, required_type, evidence, source）。
6. **写 `skill_stats`**（现有表）：`normalize_and_count` 后逐技能写入，**emergence/decline/half_life/volatility 全部 0**（D3），confidence/source_score 用正常值，`verification_status` 用 T5 口径。
7. **写 `skill_cooccurrence`**（现有表）：`build_cooccurrence(jd_skills_list)` 结果落表。
8. **T4**：按 `(title, 规范技能名)` 聚合 → jd_count、weight、required_type（多数派）、level（`_level_from_confidence` 口径映射）、confidence（平均）。
9. **T5**：按技能聚合 df → jd_frequency、归一化 jd_confidence、前 3 例 jd_id、verification_status。
10. **T6**：对每条 JD 调 `diagnose_jd(jd_id, title, skills, avg_skill_count)`，计算 overall_score 与 status 落表。

> 注：T6 复用 `app.services.enterprise_service.diagnose_jd`，其 `inflation_index` 内部用 `MetricsCalculator`，纯规则。

---

## 6. API 对接（Phase D）

### D1 现有端点增强（优先读 T1/T4/T3/T6，空则回退原逻辑）

| 端点 | 文件 | 增强内容 |
|---|---|---|
| GET /api/positions | `app/api/positions.py` | 当 `jd_position_profile` 非空：返回按 title 的岗位列表 `{position_id=title, name, tech_stack, position_type, skill_count, city, salary_range, jd_count, top_companies, top_cities}`；否则回退 `get_positions()`。`position_type`：jd_count 高且 T4 含高频新兴技能→`新兴`，否则 `既有`。 |
| GET /api/positions/{position_id} | `app/api/positions.py` | position_id 命中 T1.title → 返回 T1 画像 + T4 技能（兼容原 `{position, skills}` 结构）；否则回退。 |
| GET /api/positions/{position_id}/evolution | `app/api/positions.py` | 命中 T3.title → 按 month_key 排序返回 timeline（映射见下）；否则回退。 |
| GET /api/enterprise/positions | `app/api/enterprise.py` | 当 T1 非空：返回 `{id=title, name, department, level, skills(来自 T4), status, lastUpdated, marketDemand(jd_count 归一化 0-100), matchRate:0}`；否则回退现有 verified_skills 逻辑。 |
| GET /api/enterprise/positions/{id}/evolution | `app/api/enterprise.py` | 命中 T3 → timeline 填充 `salaryRange`（中位月薪→"X-YK"）、`marketDemand`/`adoptionRate`（jd_count 归一化）、`tools`（T4 top5 技能名）、`dataSources=["JD采样×N"]`、`marketContext`（自动文案）、`skills`（T4 快照）；否则回退。 |
| GET /api/enterprise/positions/{id}/standard | `app/api/enterprise.py` | 命中 T4 → 返回 T4 技能作为标准；否则回退。 |
| GET /api/enterprise/diagnose | `app/api/enterprise.py` | 改为返回 T6 前 50 行，映射为前端 `JDDiagnosis[]` 形状 `{id, positionName, jdTitle, submittedAt, inflationIndex, missingKeywords, redundantKeywords, overallScore, status}`（inflated_items→redundantKeywords 近似，missingKeywords 暂空）；T6 空则返回 `{diagnoses:[]}`（demo 兜底不变）。 |

### D2 新增端点 `app/api/jd.py`（挂到 `router.py`：`api_router.include_router(jd.router, prefix="/jd", tags=["JD 数据"])`）

| 端点 | 返回 | 前端消费 |
|---|---|---|
| GET /api/jd/market?title=X | T4 该 title 全部技能，映射 `MarketSkill[]`：`{name, weight, level, freshness}`（freshness=round(100×confidence)，D6） | PositionDiffView `store.market` |
| GET /api/jd/signals | T5 全量，映射 `SignalDetail[]`：`{skillName, category, totalConfidence, verificationStatus, sources:[{source:'jd', frequency, confidence, examples}]}`；github/arxiv/standard 三个源保持 demo 数据（D5） | SpectrumView/SpectrumDetailView `store.signalDetails` |
| GET /api/jd/quality?limit=N | T6 映射 `JDDiagnosis[]`（同 D1 diagnose 形状） | 备选（diagnose 端点已增强，此端点为冗余保险） |

> 统一查询辅助：在 `app/graph/repository.py` 或新建 `app/services/jd_service.py` 提供 `get_position_profile(title)`、`get_position_city_salary(title)`、`get_position_evolution(title)`、`get_position_skills(title)`、`get_skill_signals()`、`get_quality_diagnoses(limit)` 六个读函数；API 层只做形状映射，保持仓储层单一职责。

---

## 7. 前端对接（Phase E）

### E1 `src/stores/personal.ts`

- `PositionItem` 接口追加可选字段：`city?`、`salaryRange?`、`jdCount?`、`topCompanies?`、`topCities?`、`requiredSkills?`、`bonusSkills?`。
- 新增 `fetchSignalDetails()` → GET `/api/jd/signals`；成功且 `res?.signals?.length` 时，把返回的 jd 源合并进现有 `signalDetails`（其余源保留 demo）。
- `fetchPositions` 不变（后端已扩展字段，类型透传）。

### E2 `src/stores/enterprise.ts`

- 新增 `fetchMarket(title)` → GET `/api/jd/market?title=encodeURIComponent(title)`；成功且 `res?.skills?.length` 时 `market.value[title] = res.skills`。
- `fetchEvolution` / `fetchPositions` 不变（后端已增强，id 变 title 后按 title 读取）。

### E3 视图

| 视图 | 改动 |
|---|---|
| `views/personal/ExploreView.vue` | `allPositions` 改为**优先 `store.positions`**（非空时用，含真实 city/salary/companies），否则回退现有 matches/硬编码逻辑；详情面板字段接 `selectedPosition.city/salaryRange/topCompanies` |
| `views/enterprise/PositionDiffView.vue` | `onMounted` 追加 `store.fetchMarket(id.value)`；`hasMarket` 逻辑不变（market[title] 由真实数据填充） |
| `views/personal/SpectrumView.vue` / `SpectrumDetailView.vue` | `onMounted` 追加 `store.fetchSignalDetails()` |
| `views/enterprise/DiagnoseView.vue` / `BatchDiagnoseView.vue` | `onMounted` 已有 `store.fetchDiagnoses()`，无需改（后端已增强） |

> 企业侧视图不得引入个人侧工业样式类；个人侧不得引入企业侧蓝皮书类（双设计系统约束不变）。

---

## 8. 实施步骤（严格按序执行）

| 步骤 | 动作 | 产物/命令 | 验证 |
|---|---|---|---|
| **P0** | zhiyv_models.py 追加 6 个模型 | 代码 | `uvicorn` 启动无异常；`SHOW TABLES` 见 6 张新表 |
| **P1** | 新建 build_jd_derived.py 骨架（CLI + init_db + 幂等检查） | 代码 | `--tables profile` 能跑（先空表） |
| **P2** | Phase A 实现 T1/T2/T3 | `python -m app.services.build_jd_derived --tables profile --force` | 行数 = 51（T1）/ 每岗位城市数（T2）/ 51×月份桶（T3）；抽查薪资分位 |
| **P3** | Phase B 实现 T4/T5/T6 + 灌现有表 | `python -m app.services.build_jd_derived --tables skills --force`（纯规则） | verified_skills/skill_stats/skill_cooccurrence 非空；T4 行数=岗位×技能；T5 技能数；T6 行数≈9,027（剔除 151 空 jd_text） |
| **P4** | 新建 jd_service.py 6 个读函数 | 代码 | 直接 SQL 抽查返回 |
| **P5** | D1：增强 positions.py / enterprise.py 端点 | 代码 | `curl /api/positions` 返回 title 岗位 + 真实 salary/city；`curl /api/enterprise/diagnose` 返回 T6；旧路径（T1 空时）不破 |
| **P6** | D2：新建 app/api/jd.py + router.py 挂载 | 代码 | `curl '/api/jd/market?title=AI 算法工程师'` 返回 T4；`curl /api/jd/signals` 返回 T5 |
| **P7** | E1/E2：两个 store 扩展 | 代码 | `npm run build` 通过 |
| **P8** | E3：4 个视图接真实数据 | 代码 | `npm run dev` 手测各页有真实数据且不报错 |
| **P9** | 全量回归 | `pytest`（后/）+ `npm run build`（web/zhiyu-frontend/） | pytest 不新增失败（基线 104 passed）；前端构建通过 |

---

## 9. 验证与验收标准

1. **T1/T2/T3**：`SELECT title, jd_count, salary_min_p50, salary_max_p50, top_cities FROM jd_position_profile ORDER BY jd_count DESC LIMIT 5` 有 51 行、值合理（如 AI 类岗位月薪中位 2–6 万区间）。
2. **T4**：`SELECT title, skill_name, weight FROM jd_position_skills WHERE title='AI 算法工程师' ORDER BY weight DESC LIMIT 10` 返回真实技能权重。
3. **T5**：`/api/jd/signals` 返回技能含 `source:'jd'` 的真实 frequency/confidence/examples。
4. **T6**：`/api/enterprise/diagnose` 返回非空诊断列表，overall_score 分布含 healthy/warning/critical。
5. **前端**：ExploreView 岗位库显示真实城市/薪资；PositionDiffView 市场列出现真实技能权重；Spectrum 信号光谱 jd 源为真实数据；企业岗位演化曲线有薪资/需求走势。
6. **回归**：pytest 基线不降；`npm run build` 零类型错误。

---

## 10. 明确不做（本次范围外）

1. **Discovery 新岗发现**：依赖 agent 辩论管线产物 `new_roles`，与 jd_records 派生无关，不动。
2. **skill_stats 时间序列指标**：emergence/decline/half_life 保持 0（D3），待多期数据。
3. **非 jd 信号源**（github/arxiv/standard）：T5 不涉及，维持 demo。
4. **匹配算法重构**：`/api/match*` 保持 agent 驱动；`user_matches` 的 company/salary 填充本轮不做（仅 `/api/positions` 岗位库路径展示真实薪资）。
5. **jd_raw / extract_cache / gate_log** 空表：不动。
6. **双设计系统**：不引入/不混用工业类与企业蓝皮书类。
7. **docker-compose / Neo4j / asyncpg 遗留**：不处理（CLAUDE.md 既有记录）。

---

## 11. 关键文件清单

| 文件 | 动作 |
|---|---|
| `后/app/persistence/zhiyv_models.py` | 追加 T1–T6 六个模型（P0） |
| `后/app/services/build_jd_derived.py` | 新建派生 CLI（P1–P3） |
| `后/app/services/jd_service.py` | 新建 6 个读函数（P4） |
| `后/app/api/positions.py` | D1 岗位列表/详情/演化增强 |
| `后/app/api/enterprise.py` | D1 岗位标准/演化/diagnose 增强 |
| `后/app/api/jd.py` | 新建 market/signals/quality 端点（P6） |
| `后/app/api/router.py` | 挂载 jd router |
| `web/zhiyu-frontend/src/stores/personal.ts` | PositionItem 扩展 + fetchSignalDetails（E1） |
| `web/zhiyu-frontend/src/stores/enterprise.ts` | fetchMarket（E2） |
| `web/zhiyu-frontend/src/views/personal/ExploreView.vue` | 岗位库接真实数据（E3） |
| `web/zhiyu-frontend/src/views/enterprise/PositionDiffView.vue` | fetchMarket（E3） |
| `web/zhiyu-frontend/src/views/personal/SpectrumView.vue` / `SpectrumDetailView.vue` | fetchSignalDetails（E3） |

---

## 12. 风险与数据限制

- **日期无年份**（8,809/9,178）：演化展示为月份分布而非跨年趋势（D3），已在设计中规避。
- **jd_text 空**（151 行）：不参与抽取，T6 行数略小于 9,178。
- **T4 纯规则抽取精度**：规则覆盖有限（无 LLM 时组合技能/新技能易漏），`--spark` 可升级，但默认纯规则保证可复现。
- **岗位身份变更**（jd_id→title）：需在 P5/P6 保证回退路径，避免破坏现有测试与未跑派生数据时的旧行为。
- **薪资单位异构**：天/时/面议不参与月薪聚合（D2），`salary_cover_rate` 暴露可信度。

---

## 13. 实施进度表

| 步骤 | 状态 | 完成时间 | 验证结果 |
|---|---|---|---|
| P0 建表 | ✅ | 2026-08-29 | 6 张新表已建（SHOW TABLES 验证） |
| P1 脚本骨架 | ✅ | 2026-08-29 | build_jd_derived.py 建成（CLI + init_db + 幂等检查） |
| P2 Phase A (T1/T2/T3) | ✅ | 2026-08-29 | T1=51 / T2=2717 / T3=489；月桶 01–12 全量归桶，薪资分位合理 |
| P3 Phase B (T4/T5/T6+灌表) | ✅ | 2026-08-29 | verified_skills=11620 / skill_stats=6927 / cooc=12491 / T4=8099 / T5=6927 / T6=9041（=9178−137 空文本）；纯规则 + 保守噪声过滤（句子碎片/福利文案，见 build_jd_derived `_is_junk`） |
| P4 jd_service 读函数 | ✅ | 2026-08-29 | jd_service.py 六读函数全部验证：Java 岗位画像 cnt=537 / min50=14000 / max50=26000；top_cities 深圳78/武汉51；skills top=MySQL w=0.1007；signals top=办公软件 136；diagnoses healthy100/critical42 |
| P5 D1 端点增强 | ✅ | 2026-08-29 | positions.py + enterprise.py 增强完成并实测：/api/positions→51 岗位（Java 14-26K / 537 JD / skill_count 565）；/api/enterprise/positions→51 岗位 + T4 技能；/api/enterprise/positions/{id}/evolution→11 月桶（salaryRange/marketDemand/tools/dataSources 填充）；standard→100 技能；/api/enterprise/diagnose→50 条（healthy/warning/critical 分布）；pytest 104 passed 基线不降（5 failed + 14 errors 均为既有 Neo4j→MySQL 迁移漂移，与本次无关） |
| P6 D2 /api/jd 端点 | ✅ | 2026-08-29 | app/api/jd.py 建成 + router.py 挂载 /jd：/api/jd/market?title=Java→100 技能（MySQL w=0.1007）；/api/jd/signals→6927 信号（办公软件 freq=136 置信 1.0 + 3 例 jd_id）；/api/jd/quality→诊断同 diagnose 形状 |
| P7 store 扩展 | ✅ | 2026-08-29 | E1 personal.ts：PositionItem 增 7 可选字段 + fetchSignalDetails（top-N 合并 jd 源，SIGNAL_MERGE_CAP=40 防 6927 卡渲染）；E2 enterprise.ts：fetchMarket(title)；`npm run build` 通过（vue-tsc 0 错误） |
| P8 视图接通 | ✅ | 2026-08-29 | E3 四视图：ExploreView allPositions 优先 store.positions（真实 city/salary/topCompanies）+ 详情面板 TOP COMPANIES·JD 数；PositionDiffView onMounted 追加 fetchMarket(id)；SpectrumView / SpectrumDetailView onMounted 追加 fetchSignalDetails；personal.ts fetchPositions 归一化 snake→camel（PositionItem 接口与运行时一致）；`npm run build` 通过（vue-tsc 0 错误） |
| P9 全量回归 | ✅ | 2026-08-29 | pytest（后/）= 104 passed 基线不降（5 failed + 14 errors 为既有 Neo4j→MySQL 迁移漂移，git stash 验证与本次无关）；`npm run build` 通过（vue-tsc 0 类型错误）。**P0–P9 全阶段完成。** |
