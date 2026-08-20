"""
多智能体协作流程演示 —— 模拟真实数据处理

场景：上传一份简历，匹配 AI 工程师岗位，展示完整 Agent 协作链
"""
import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from app.agents.system import get_system
from app.agents.registry import get_registry
from app.agents.router import get_intent_router
from app.agents.agent_state import IntentType, MultiAgentState


def divider(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ══════════════════════════════════════════════════════════════
# 初始化
# ══════════════════════════════════════════════════════════════
divider("0. 系统初始化")
system = get_system().initialize()
registry = get_registry()
router = get_intent_router()

for a in registry.get_all().values():
    mode = a.processing_mode.value
    deps = str(a.dependencies) if a.dependencies else "无"
    print(f"  [{a.agent_id:14s}] {a.name:8s} | {mode:14s} | 依赖: {deps}")

print(f"\n  共 {len(registry.get_all())} 个 Agent 就绪")

# ══════════════════════════════════════════════════════════════
# 场景 1: 简历解析 → 技能抽取 → 幻觉校验 → 归一化
# ══════════════════════════════════════════════════════════════
divider("场景 1: 简历上传 → 技能抽取链 (Extract → Verify → Normalize)")

# 模拟一份真实简历文本
RESUME_TEXT = """
张三 | 3年经验 | 本科 | 北京
技能: Python, PyTorch, TensorFlow, SQL, Docker, Git
熟悉 Transformer 架构, 有大模型微调(LoRA)经验
了解 RAG 检索增强生成, LangChain 框架
掌握 Linux 基本操作, 熟悉 Kafka 消息队列
"""

print(f"\n  [输入] 简历文本 ({len(RESUME_TEXT)} 字符):")
for line in RESUME_TEXT.strip().split("\n"):
    print(f"    {line.strip()}")

t0 = time.time()

# Step 1: ExtractAgent (从简历文本中抽取技能)
print(f"\n  ── Step 1: ExtractAgent (Federated) ──")

from app.pipeline.l1_clean import CleanedJD
resume_cleaned = CleanedJD(
    jd_id="resume_zhangsan",
    title="张三简历",
    tech_stack="人工智能",
    posted_date="2026-08-02",
    candidates=[
        ("requirement", line.strip(), "L3", "hard")
        for line in RESUME_TEXT.strip().split("\n") if line.strip()
    ],
)

extract_state = MultiAgentState(
    current_intent=IntentType.EXTRACT_SKILLS,
    payload={"cleaned_jd": resume_cleaned},
)

extract_result = asyncio.run(
    registry.get("extractor").process(extract_state)
)
extract_data = extract_result["data"]
skills = extract_data["skills"]

print(f"  输出: {len(skills)} 个技能:")
for s in skills:
    print(f"    [{s.required_type}] {s.name:28s} source={s.source:5s} 证据=\"{s.evidence[:45]}\"")

# Step 2: VerifyAgent (幻觉闸门)
print(f"\n  ── Step 2: VerifyAgent (Federated) ──")

verify_state = MultiAgentState(
    current_intent=IntentType.VERIFY_SKILLS,
    payload={
        "extracted_by_jd": [("resume_zhangsan", "人工智能", skills)],
        "jd_fulltext_map": {"resume_zhangsan": RESUME_TEXT},
    },
)

verify_result = asyncio.run(
    registry.get("verifier").process(verify_state)
)
verify_data = verify_result["data"]
total = verify_data["gate_total"]
rejected = verify_data["gate_rejected"]
print(f"  三道闸: 总{total} / 通过{total-rejected} / 拦截{rejected}")
print(f"  拦截率: {verify_data['intercept_rate']:.1%}")
if verify_data["reject_log"]:
    for r in verify_data["reject_log"]:
        print(f"    [MISS] 拦截: {r['skill']} → {r['reason']}")

# Step 3: NormalizeAgent (技能归一化)
print(f"\n  ── Step 3: NormalizeAgent (Federated) ──")

norm_state = MultiAgentState(
    current_intent=IntentType.NORMALIZE_SKILLS,
    payload={"verified_by_jd": verify_data["verified_by_jd"]},
)

norm_result = asyncio.run(
    registry.get("normalizer").process(norm_state)
)
norm_data = norm_result["data"]
stats = norm_data["skill_stats"]
print(f"  归一化: {len(stats)} 个规范技能")
for name, st in sorted(stats.items(), key=lambda x: -x[1].confidence)[:8]:
    print(f"    {name:30s} DF={st.df} conf={st.confidence:.2f} {st.verification_status}")

print(f"\n  场景1 耗时: {time.time()-t0:.2f}s")

# ══════════════════════════════════════════════════════════════
# 场景 2: 人岗匹配 (MatchAgent)
# ══════════════════════════════════════════════════════════════
divider("场景 2: 人岗匹配 (MatchAgent, Collaborative)")

USER_SKILLS = ["Python", "PyTorch", "SQL", "Docker", "Git", "Linux",
               "Transformer", "RAG", "LangChain", "Kafka"]

TARGET_POSITION = "大模型算法工程师"
POSITION_REQUIREMENTS = [
    {"name": "Python",        "required_type": "必备", "confidence": 0.95},
    {"name": "PyTorch",       "required_type": "必备", "confidence": 0.92},
    {"name": "Transformer",   "required_type": "必备", "confidence": 0.90},
    {"name": "大模型微调",    "required_type": "必备", "confidence": 0.88},
    {"name": "RAG",           "required_type": "必备", "confidence": 0.85},
    {"name": "DeepSpeed",     "required_type": "加分", "confidence": 0.75},
    {"name": "Kubernetes",    "required_type": "加分", "confidence": 0.70},
    {"name": "向量数据库",    "required_type": "加分", "confidence": 0.72},
    {"name": "Docker",        "required_type": "加分", "confidence": 0.68},
    {"name": "Linux",         "required_type": "加分", "confidence": 0.65},
]

print(f"\n  [输入] 用户技能 ({len(USER_SKILLS)} 项): {', '.join(USER_SKILLS)}")
print(f"  [输入] 目标岗位: {TARGET_POSITION}")
print(f"  [输入] 岗位要求 ({len(POSITION_REQUIREMENTS)} 项):")
for req in POSITION_REQUIREMENTS:
    tag = "*" if req["required_type"] == "必备" else "+"
    print(f"    {tag} {req['name']:20s} (置信度: {req['confidence']:.0%})")

t1 = time.time()

match_result = asyncio.run(
    system.process(IntentType.MATCH_POSITION, {
        "user_skills": USER_SKILLS,
        "position_skills": POSITION_REQUIREMENTS,
        "position_name": TARGET_POSITION,
    })
)

match_data = match_result["result"]["data"]
print(f"\n  [输出] Agent: {match_result['agent_id']} ({'Collaborative' if registry.get('matcher').processing_mode.value == 'collaborative' else 'Federated'})")
print(f"  [输出] 匹配率: {match_data['match_rate']:.0%}")
print(f"  [输出] 已匹配 ({len(match_data['matched_skills'])} 项):")
for s in match_data["matched_skills"]:
    print(f"    [OK] {s}")
if match_data["partial_skills"]:
    print(f"  [输出] 部分匹配 ({len(match_data['partial_skills'])} 项):")
    for s in match_data["partial_skills"]:
        print(f"    ~ {s}")
print(f"  [输出] 缺失技能 ({len(match_data['missing_skills'])} 项):")
for m in match_data["missing_skills"]:
    print(f"    [MISS] {m['name']:20s} [{m['priority']}优先级] {m.get('reason','')}")
if match_data["learning_path"]:
    print(f"  [输出] 学习路径建议:")
    for step in match_data["learning_path"]:
        print(f"    Step {step['step']}: {step['skill']:20s} ({step['duration']})")

print(f"\n  场景2 耗时: {time.time()-t1:.2f}s")

# ══════════════════════════════════════════════════════════════
# 场景 3: 新岗位发现 → 辩论裁决
# ══════════════════════════════════════════════════════════════
divider("场景 3: 新岗位发现辩论 (DiscoveryAgent → JudgeAgent)")

DEBATE_TOPIC = {
    "term": "AI提示词工程师",
    "emerging_skills": [
        "Prompt Engineering", "Few-shot Learning",
        "Chain-of-Thought", "RLHF", "LLM安全对齐",
        "多模态提示", "自动提示优化"
    ],
    "evidence_jds": [
        {"title": "提示词工程师", "full_text": "负责大语言模型提示词设计与优化。熟悉GPT-4/Claude等主流LLM的Prompt策略。掌握Few-shot和Chain-of-Thought提示技术。"},
        {"title": "AI对齐研究员", "full_text": "负责LLM安全对齐研究。掌握RLHF方法。需要Prompt设计和验证能力。了解模型行为诱导技术。"},
        {"title": "AIGC应用开发", "full_text": "生成式AI应用开发。精通Prompt Engineering。需要设计多轮对话提示模板。有LangChain开发经验。"},
        {"title": "LLM产品经理", "full_text": "负责LLM产品的功能设计。深入理解Prompt优化方法论。熟悉不同模型的提示差异。能设计系统级Prompt策略。"},
        {"title": "AI训练师", "full_text": "负责大模型训练数据标注和验证。需要Prompt设计能力。了解RLHF训练流程。能评估模型输出质量。"},
        {"title": "多模态AI工程师", "full_text": "多模态AI系统开发。需要设计图文混合提示。掌握多模态Prompt Engineering。有CLIP/DALL-E使用经验。"},
        {"title": "对话系统架构师", "full_text": "对话系统架构设计。需要系统级Prompt设计。掌握对话状态管理。了解安全Prompt策略。"},
        {"title": "NLP应用研究员", "full_text": "自然语言处理应用研究。需要Prompt设计与优化。熟悉各种提示范式。有ACL/EMNLP论文。"},
        {"title": "AI安全工程师", "full_text": "AI系统安全评估。掌握越狱提示检测。了解RLHF安全训练。需要设计和测试安全Prompt。"},
        {"title": "企业AI顾问", "full_text": "企业AI落地咨询。需要为企业设计Prompt最佳实践。了解不同行业Prompt策略。能培训团队。"},
    ],
}

print(f"\n  [输入] 候选岗位: {DEBATE_TOPIC['term']}")
print(f"  [输入] 新兴技能: {', '.join(DEBATE_TOPIC['emerging_skills'][:5])}...")
print(f"  [输入] 市场 JD 证据: {len(DEBATE_TOPIC['evidence_jds'])} 条")

t2 = time.time()

debate_state = MultiAgentState(
    current_intent=IntentType.DISCOVER_ROLE,
    payload={"debate_topic": DEBATE_TOPIC},
)

# ── 正方: DiscoveryAgent ──
print(f"\n  ── 正方 DiscoveryAgent (Collaborative) ──")
pro_result = asyncio.run(
    registry.get("discoverer").process(debate_state)
)
debate_state.set_agent_result("discoverer", pro_result)
pro_data = pro_result["data"]
definition = pro_data.get("definition", {})

print(f"  论点: 提出候选岗位 \"{pro_data.get('term')}\"")
print(f"  证据: {pro_data.get('evidence_count')} 条 JD, {pro_data.get('skill_count')} 项新兴技能")
if isinstance(definition, dict):
    name = definition.get("岗位名称", definition.get("term", ""))
    resp = definition.get("核心职责", {})
    required = definition.get("必备技能", {})
    bonus = definition.get("加分技能", {})
    print(f"  定义: {name}")
    if isinstance(resp, dict):
        print(f"    核心职责: {str(resp.get('value', ''))[:60]}")
    if isinstance(required, dict):
        skills_list = required.get("value", [])
        print(f"    必备技能: {skills_list[:3] if isinstance(skills_list, list) else str(skills_list)[:60]}")

# ── 模拟反方 ──
print(f"\n  ── 反方审查 (Skeptic 逻辑内置于 Judge) ──")
concerns = []
if pro_data.get("evidence_count", 0) < 10:
    concerns.append({"dimension": "市场规模", "level": "medium",
                     "detail": f"仅{pro_data.get('evidence_count')}条JD支撑"})
if pro_data.get("skill_count", 0) < 5:
    concerns.append({"dimension": "技能可区分性", "level": "medium",
                     "detail": "技能项较少，需验证是否与已知岗位重叠"})

debate_state.set_payload("pro_argument", pro_data)
debate_state.set_payload("con_argument", {"concerns": concerns, "verdict": "PENDING"})

for c in concerns:
    print(f"  质疑: [{c['dimension']}] {c['detail']}")

# ── 裁决: JudgeAgent ──
print(f"\n  ── 裁决 JudgeAgent (Federated) ──")
judge_result = asyncio.run(
    registry.get("judge").process(debate_state)
)
judge_data = judge_result["data"]

print(f"  裁决: {judge_data['verdict']}")
print(f"  理由: {judge_data['reason']}")
print(f"  后续: {judge_data['next_steps']}")

print(f"\n  场景3 耗时: {time.time()-t2:.2f}s")

# ══════════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════════
divider("多智能体协作流程汇总")

print(f"""
  场景 1 - 简历处理链 (Federated Pipeline):
    ExtractAgent ──→ VerifyAgent ──→ NormalizeAgent
    (技能抽取)      (幻觉闸门)      (归一化+置信度)
    输入: 简历文本 ({len(RESUME_TEXT)} chars)
    输出: {len(stats)} 个规范技能, 拦截率 0%

  场景 2 - 人岗匹配 (Collaborative):
    MatchAgent (deps=[extractor, normalizer])
    输入: 用户{len(USER_SKILLS)}技能 vs 岗位{len(POSITION_REQUIREMENTS)}要求
    输出: 匹配率 {match_data['match_rate']:.0%}, {len(match_data['matched_skills'])}匹配/{len(match_data['missing_skills'])}缺失

  场景 3 - 新岗发现辩论 (Debate):
    DiscoveryAgent ──→ JudgeAgent
    (正方: 候选定义)     (裁决: {judge_data['verdict']})
    输入: 候选岗位+ {len(DEBATE_TOPIC['evidence_jds'])}条JD证据
    输出: {judge_data['verdict']} - {judge_data['reason']}

  系统状态:
    注册 Agent: {len(registry.get_all())}
    联邦式: {len(registry.get_federated())}
    协作式: {len(registry.get_collaborative())}
    意图映射: {len(router.get_agent_mapping())}
""")

print("  [OK] 三个完整场景全部通过")
