"""全链路 pipeline 服务 —— 编排 L1→L2→L3→L4 全流程。

设计方案 W1 铁律："最小闭环 + 可部署"。
用法：
  python -m app.services.pipeline_service --n 10           # 星火抽取
  python -m app.services.pipeline_service --n 10 --no-spark # 纯规则
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time

from app.config import get_settings
from app.domain import JobPosting, Paragraph, SectionType, SourceType, TechStack
from app.pipeline.l1_clean import clean
from app.pipeline.l3_extract import extract
from app.pipeline.l3_verify import verify
from app.pipeline.l4_graph import build_graph

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# JD 加载（从原有 data/ 目录读取 JSONL）
# ══════════════════════════════════════════════

def _map_source(raw: str) -> SourceType:
    """将旧数据格式的 source 名映射到新 enum。"""
    mapping = {
        "synthetic": SourceType.JD, "real_public": SourceType.JD,
        "real_official": SourceType.JD, "jd": SourceType.JD,
        "jd_api": SourceType.JD,
    }
    return mapping.get(raw, SourceType.JD)


def _map_tech_stack(raw: str) -> TechStack:
    """将旧数据格式的 tech_stack 名映射到新 enum。"""
    try:
        return TechStack(raw) if isinstance(raw, str) else TechStack(raw)
    except ValueError:
        return TechStack.AI  # 默认 AI


def load_jds(n: int) -> list[JobPosting]:
    """从原有数据目录加载模拟 JD。Phase 1 用合成数据跑通链路。"""
    settings = get_settings()
    data_path = settings.DATA_DIR / "batch1.jsonl"

    if not data_path.exists():
        logger.warning(f"数据文件不存在: {data_path}，使用内置硬编码示例 JD")
        return _make_demo_jds(n)

    jds = []
    with open(data_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            line = line.strip()
            if line:
                d = json.loads(line)
                paragraphs = [
                    Paragraph(
                        section=SectionType(p["section"]),
                        text=p["text"],
                    )
                    for p in d.get("paragraphs", [])
                ]
                jds.append(JobPosting(
                    jd_id=d["jd_id"],
                    source=_map_source(d.get("source", "synthetic")),
                    tech_stack=_map_tech_stack(d.get("tech_stack", "人工智能")),
                    title=d["title"],
                    posted_date=d.get("posted_date", "2026-07-01"),
                    paragraphs=paragraphs,
                    salary_min=d.get("salary_min"),
                    salary_max=d.get("salary_max"),
                    experience_years=d.get("experience_years"),
                    education=d.get("education"),
                    city=d.get("city"),
                    meta=d.get("meta", {}),
                ))
    return jds


def _make_demo_jds(n: int) -> list[JobPosting]:
    """当数据文件不存在时，用内置示例 JD 兜底。"""
    demos = [
        JobPosting(
            jd_id="demo-001",
            source=SourceType.JD,
            tech_stack=TechStack.AI,
            title="大模型算法工程师",
            posted_date="2026-07-01",
            paragraphs=[
                Paragraph(SectionType.REQUIREMENT,
                          "熟悉 PyTorch 或 TensorFlow 框架；有大模型微调（LoRA/QLoRA）实战经验；"
                          "精通 Transformer 架构原理；掌握 RAG 与向量数据库（Milvus/Pinecone）；"
                          "熟练使用 DeepSpeed 或 FSDP 进行分布式训练；Python 编程基础扎实"),
                Paragraph(SectionType.BONUS,
                          "有 LangChain/LlamaIndex 使用经验；熟悉 RLHF 流程；"
                          "在 ACL/EMNLP/NeurIPS 发表过论文"),
                Paragraph(SectionType.RESPONSIBILITY,
                          "负责大语言模型的微调与部署；设计 RAG 检索增强生成系统；"
                          "优化模型推理效率与显存占用"),
                Paragraph(SectionType.WELFARE, "五险一金，弹性工作，免费下午茶，年终奖金"),
            ],
            salary_min=30000, salary_max=60000, experience_years=3,
            education="硕士", city="合肥",
        ),
        JobPosting(
            jd_id="demo-002",
            source=SourceType.JD,
            tech_stack=TechStack.BIG_DATA,
            title="大数据开发工程师",
            posted_date="2026-06-15",
            paragraphs=[
                Paragraph(SectionType.REQUIREMENT,
                          "精通 Hadoop/Spark 生态体系；熟悉 Flink 实时计算引擎；"
                          "掌握 Kafka 消息队列；熟练使用 ClickHouse 或 Doris 做 OLAP 分析；"
                          "有数据仓库建模经验（星型/雪花模型）；SQL 功底扎实"),
                Paragraph(SectionType.BONUS,
                          "了解数据湖技术（Iceberg/Hudi）；有 HBase 使用经验"),
                Paragraph(SectionType.RESPONSIBILITY,
                          "负责数据仓库建设与 ETL 流程优化；"
                          "搭建实时数据处理 pipeline；数据质量监控与治理"),
                Paragraph(SectionType.WELFARE, "六险一金，餐补，年度体检，股票期权"),
            ],
            salary_min=25000, salary_max=45000, experience_years=3,
            education="本科", city="北京",
        ),
    ]
    return demos[:n]


# ══════════════════════════════════════════════
# 全链路执行
# ══════════════════════════════════════════════

async def run_pipeline(n: int = 10, use_spark: bool = True,
                     use_agent: bool = False) -> dict:
    """执行全链路 pipeline。

    Args:
        n: 处理 JD 条数
        use_spark: 是否使用星火 LLM
        use_agent: 是否使用多 Agent 模式（Phase 2）
    """
    settings = get_settings()
    jds = load_jds(n)
    logger.info(f"载入 {len(jds)} 条 JD")

    # ── 创建 LLM 客户端 ──
    client = None
    if use_spark:
        try:
            from app.utils.spark import SparkClient
            client = SparkClient()
            logger.info("星火客户端就绪")
        except Exception as e:
            logger.warning(f"星火不可用，全程规则兜底: {e}")

    # ── L1 清洗 + L3 抽取 + L3 校验 ──
    positions = []
    extracted_by_jd = []
    evidences = []
    ev_counter = 0
    gate_total = gate_rejected = 0
    reject_log = []
    spark_hits = rule_hits = 0

    t0 = time.monotonic()
    for i, jd in enumerate(jds, 1):
        # L1
        cleaned = clean(jd)

        # L3 抽取
        skills = extract(cleaned, client)

        # L3 幻觉闸门
        gate = verify(jd.jd_id, jd.full_text(), skills)
        gate_total += gate.total
        gate_rejected += len(gate.rejected)
        for v in gate.rejected:
            reject_log.append({
                "jd_id": jd.jd_id,
                "skill": v.skill.name,
                "evidence": v.skill.evidence,
                "reason": v.reason,
            })
        skills = gate.passed

        # 统计来源
        for s in skills:
            if s.source == "spark":
                spark_hits += 1
            else:
                rule_hits += 1

            # 证据节点
            if s.evidence:
                evidences.append({
                    "eid": ev_counter,
                    "jd_id": jd.jd_id,
                    "text": s.evidence,
                    "skill": s.name,
                    "source": "jd",
                })
                ev_counter += 1

        positions.append({
            "jd_id": jd.jd_id,
            "title": jd.title,
            "tech_stack": jd.tech_stack.value if hasattr(jd.tech_stack, 'value') else jd.tech_stack,
            "skills": skills,
        })
        extracted_by_jd.append((jd.jd_id,
                                jd.tech_stack.value if hasattr(jd.tech_stack, 'value') else jd.tech_stack,
                                skills))

        print(f"  [{i}/{len(jds)}] {jd.title}：抽出 {len(skills)} 个技能")

    elapsed = time.monotonic() - t0
    logger.info(f"L1+L3 完成，用时 {elapsed:.1f}s")
    logger.info(f"抽取来源：星火 {spark_hits} / 规则 {rule_hits}")

    # 幻觉拦截率
    rate = gate_rejected / gate_total if gate_total else 0.0
    logger.info(f"[闸门] 幻觉防控：生成 {gate_total} 项 / 拦截 {gate_rejected} 项 / 拦截率 {rate:.1%}")

    # ── L2 归一化 + 频次 + 置信度 ──
    from app.pipeline.l2_normalize import normalize_and_count
    skill_stats = normalize_and_count(extracted_by_jd)
    logger.info(f"L2 归一化：{len(skill_stats)} 个规范技能")

    # ── L2 共现分析 ──
    from app.pipeline.l2_normalize import normalize_name
    from app.pipeline.l2_cooccurrence import build_cooccurrence as build_cooc
    jd_skills_list = [(jd_id, [normalize_name(s.name) for s in skills])
                      for jd_id, _, skills in extracted_by_jd]
    cooc = build_cooc(jd_skills_list)
    co_stats = cooc.get_stats()
    logger.info(f"L2 共现：{co_stats['total_skills']} 技能, {co_stats['total_cooccurrences']} 对")

    # ── L2 动态指标（基于 posted_date 按月聚合） ──
    from app.pipeline.l2_metrics import MetricsCalculator
    calc = MetricsCalculator()

    # 构建 jd_id → 月份 映射
    jd_month_map = {}
    for jd in jds:
        month = jd.posted_date[:7] if jd.posted_date and len(jd.posted_date) >= 7 else "unknown"
        jd_month_map[jd.jd_id] = month

    # 按月统计每个技能在多少条 JD 中出现（DF per month）
    skill_monthly: dict[str, dict[str, int]] = {}
    for jd_id, _, skills in extracted_by_jd:
        month = jd_month_map.get(jd_id, "unknown")
        seen_in_jd: set[str] = set()
        for sk in skills:
            canon = normalize_name(sk.name if hasattr(sk, 'name') else sk.get("name", ""))
            if canon in seen_in_jd:
                continue
            seen_in_jd.add(canon)
            if canon not in skill_monthly:
                skill_monthly[canon] = {}
            skill_monthly[canon][month] = skill_monthly[canon].get(month, 0) + 1

    metrics_report = {}
    skill_metrics = {}
    for name, stat in skill_stats.items():
        monthly_counts = skill_monthly.get(name, {})
        metrics = calc.compute_all(
            monthly_counts=monthly_counts, skill_count=stat.df,
            avg_skill_count=co_stats["avg_skills_per_jd"],
            required_ratio=stat.required_count / max(1, stat.required_count + stat.bonus_count),
        )
        skill_metrics[name] = metrics
        metrics_report[name] = {
            "emergence": metrics.emergence, "decline": metrics.decline,
            "volatility": metrics.volatility, "half_life": metrics.half_life,
            "half_life_method": metrics.half_life_method,
            "inflation_index": metrics.inflation_index,
        }
    logger.info(f"L2 动态指标：{len(metrics_report)} 个技能已计算（基于 {len(jd_month_map)} 条 JD 按月聚合）")

    # 存入 context 供后续辩论使用
    context["skill_metrics"] = skill_metrics
    context["extracted_by_jd"] = extracted_by_jd

    # ── L4 建图 ──
    import os as _os
    out_dir = _os.path.join(_os.path.dirname(__file__), "..", "output")
    _os.makedirs(out_dir, exist_ok=True)

    from app.pipeline.l4_graph import build_graph_json
    graph_json = build_graph_json(positions, skill_stats, evidences,
                                  cooccurrence=cooc.cooccurrences,
                                  skill_metrics=skill_metrics)

    try:
        graph_stats = await build_graph(positions, skill_stats, evidences,
                                        cooccurrence=cooc.cooccurrences,
                                        skill_metrics=skill_metrics)
        logger.info(f"L4 MySQL 建图：{graph_stats}")
    except Exception as e:
        logger.warning(f"MySQL 建图失败，仅保留 JSON 文件: {e}")
        graph_stats = {"nodes": len(graph_json["nodes"]), "edges": len(graph_json["edges"])}

    # 落盘 graph.json（供前端使用）
    graph_path = _os.path.join(out_dir, "graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_json, f, ensure_ascii=False, indent=2)
    logger.info(f"图谱 JSON → {graph_path}")

    # ── L4 快照 ──
    from app.pipeline.l4_snapshot import SnapshotManager
    snap_mgr = SnapshotManager(storage_dir=_os.path.join(out_dir, "snapshots"))
    snap = snap_mgr.create_snapshot(
        {"nodes": [], "edges": []},
        description=f"Pipeline: {len(jds)} JDs",
    )
    logger.info(f"L4 快照：{snap.snapshot_id}")

    # ── 落盘指标报告 ──
    import json as _json
    metrics_path = _os.path.join(out_dir, "metrics_report.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        _json.dump({"dedup_stats": {}, "cooccurrence_stats": co_stats,
                    "skill_metrics": metrics_report}, f, ensure_ascii=False, indent=2)
    logger.info(f"指标报告 → {metrics_path}")

    return {
        "n_jds": len(jds),
        "n_skills_extracted": sum(len(p["skills"]) for p in positions),
        "n_unique_skills": len(skill_stats),
        "spark_hits": spark_hits, "rule_hits": rule_hits,
        "gate_total": gate_total, "gate_rejected": gate_rejected,
        "intercept_rate": round(rate, 4),
        "cooccurrence_pairs": co_stats["total_cooccurrences"],
        "graph": graph_stats, "snapshot_id": snap.snapshot_id,
        "elapsed_seconds": round(elapsed, 1),
    }


# ══════════════════════════════════════════════
# Agent 驱动 pipeline（Phase 2）
# ══════════════════════════════════════════════

async def run_agent_pipeline(n: int = 10, use_spark: bool = True) -> dict:
    """多 Agent 驱动的端到端 pipeline（新架构）。

    Agent 协作流程：
    ExtractAgent(Federated) → VerifyAgent(Federated) → NormalizeAgent(Federated)
    → EvolutionAgent(Federated) → SuggestAgent(Collaborative)
    + 新岗发现辩论：DiscoveryAgent vs JudgeAgent
    """
    settings = get_settings()
    jds = load_jds(n)
    logger.info(f"[Agent] 载入 {len(jds)} 条 JD")

    client = None
    if use_spark:
        try:
            from app.utils.spark import SparkClient
            client = SparkClient()
            logger.info("[Agent] 星火客户端就绪")
        except Exception as e:
            logger.warning(f"[Agent] 星火不可用: {e}")

    # ── L1 清洗（Agent 模式仍走 pipeline 函数，效率和确定性优先）──
    from app.pipeline.l1_clean import clean as l1_clean
    cleaned_jds = []
    jd_fulltext_map = {}
    for jd in jds:
        c = l1_clean(jd)
        cleaned_jds.append({
            "jd_id": jd.jd_id, "title": jd.title,
            "tech_stack": jd.tech_stack.value if hasattr(jd.tech_stack, 'value') else jd.tech_stack,
            "cleaned": c,
        })
        jd_fulltext_map[jd.jd_id] = jd.full_text()

    context = {
        "cleaned_jds": cleaned_jds,
        "jds": jds,
        "jd_fulltext_map": jd_fulltext_map,
    }

    # ── 使用新 MultiAgentSystem ──
    from app.agents.system import MultiAgentSystem
    from app.agents.agent_state import MultiAgentState, IntentType

    system = MultiAgentSystem().initialize(llm_client=client)
    logger.info(f"[Agent] MultiAgentSystem 初始化完成，共 {len(system.registry.get_all())} 个 Agent")

    # Pipeline 模式：按 Agent 链顺序批量执行
    agent_chain = ["extractor", "verifier", "normalizer"]

    t0 = time.monotonic()
    state = MultiAgentState(
        current_intent=IntentType.PIPELINE,
        payload={
            "cleaned_jds": cleaned_jds,
            "jd_fulltext_map": jd_fulltext_map,
            "jds": jds,
        },
    )

    # 逐个执行 pipeline Agent，每个 Agent 的产出同步到 state.payload 供下游读取
    for agent_id in agent_chain:
        agent = system.registry.get(agent_id)
        if agent:
            logger.info(f"[Agent] → {agent_id}")
            result = await agent.process(state)
            state.set_agent_result(agent_id, result)

            # 将 Agent 产出写入 state.payload（下游 Agent 通过 get_payload 读取）
            data = result.get("data", {})
            for key, val in data.items():
                state.set_payload(key, val)

            # 同时写入 context（兼容后续 L4 建图处理）
            if "extracted_by_jd" in data:
                context["extracted_by_jd"] = data["extracted_by_jd"]
                context["extract_stats"] = {"spark_hits": data.get("spark_hits", 0),
                                           "rule_hits": data.get("rule_hits", 0)}
            if "verified_by_jd" in data:
                context["verified_by_jd"] = data["verified_by_jd"]
                context["gate_stats"] = {"total": data.get("gate_total", 0),
                                        "rejected": data.get("gate_rejected", 0),
                                        "intercept_rate": data.get("intercept_rate", 0)}
            if "skill_stats" in data:
                context["skill_stats"] = data["skill_stats"]

    logger.info(f"[Agent] Pipeline 完成，用时 {time.monotonic() - t0:.1f}s")

    # ── 辩论模式：新岗位发掘 ──
    # 1) 按 emergence 排序，筛选新兴技能（emergence > 1.0 或 top 5）
    skill_stats = context.get("skill_stats", {})
    skill_metrics = context.get("skill_metrics", {})

    # 构建共现数据（从 extracted_by_jd）
    from app.pipeline.l2_normalize import normalize_name
    from app.pipeline.l2_cooccurrence import build_cooccurrence as build_cooc
    extracted_by_jd = context.get("extracted_by_jd", [])
    jd_skills_list = [(jd_id, [normalize_name(s.name if hasattr(s, 'name') else s.get("name", ""))
                                for s in skills])
                      for jd_id, _, skills in extracted_by_jd]
    cooc = build_cooc(jd_skills_list)

    # 2) 按 emergence 排序，筛选新兴技能
    emerging_skills = []
    for name, stat in skill_stats.items():
        metrics = skill_metrics.get(name)
        em = metrics.emergence if metrics else 0
        if em > 1.0:
            emerging_skills.append((name, em, stat))
    if not emerging_skills:
        # 没有 emergence > 1.0 的，取 top 5 按 confidence
        emerging_skills = [(name, 0, stat) for name, stat in
                          sorted(skill_stats.items(), key=lambda x: x[1].confidence, reverse=True)[:5]]

    emerging_skills.sort(key=lambda x: x[1], reverse=True)
    skill_names = [s[0] for s in emerging_skills]

    # 3) 技能聚类：按共现关系分组
    clusters = _cluster_skills(skill_names, cooc)

    # 4) 对每个技能簇发起辩论
    discovered_roles = []
    for cluster in clusters[:3]:  # 最多辩论 3 个候选岗位
        # 从 JD 中找包含这些技能的证据
        cluster_set = set(cluster)
        evidence_jds = []
        for jd_id, _, skills in extracted_by_jd:
            jd_skills = {normalize_name(s.name if hasattr(s, 'name') else s.get("name", ""))
                        for s in skills}
            if cluster_set & jd_skills:
                jd_obj = next((j for j in jds if j.jd_id == jd_id), None)
                if jd_obj:
                    evidence_jds.append({
                        "jd_id": jd_id,
                        "title": jd_obj.title,
                        "full_text": jd_obj.full_text()[:500],
                        "tech_stack": jd_obj.tech_stack.value if hasattr(jd_obj.tech_stack, 'value') else str(jd_obj.tech_stack),
                    })

        # 生成候选岗位名（取簇中最高 emergence 的技能作为核心）
        core_skill = cluster[0]
        term = f"{core_skill}工程师"

        debate_topic = {
            "term": term,
            "emerging_skills": cluster,
            "evidence_jds": evidence_jds,
            "evidence_count": len(evidence_jds),
        }
        debate_state = MultiAgentState(
            current_intent=IntentType.DISCOVER_ROLE,
            payload={"debate_topic": debate_topic},
        )

        # DiscoveryAgent(正方) → JudgeAgent(裁判)
        for aid in ["discoverer", "judge"]:
            agent = system.registry.get(aid)
            if agent:
                result = await agent.process(debate_state)
                debate_state.set_agent_result(aid, result)

        verdict = debate_state.get_agent_result("judge") or {}
        definition = (debate_state.get_agent_result("discoverer") or {}).get("definition", {})

        discovered_roles.append({
            "term": term,
            "skills": cluster,
            "evidence_count": len(evidence_jds),
            "verdict": verdict.get("verdict", "Pending"),
            "reason": verdict.get("reason", ""),
            "definition": definition,
        })

        # 写入 MySQL new_roles 表
        await _save_new_role(term, cluster, evidence_jds, verdict, definition)

    context["discovered_roles"] = discovered_roles
    if discovered_roles:
        logger.info(f"新岗位发掘：{len(discovered_roles)} 个候选，"
                    f"Confirmed={sum(1 for r in discovered_roles if r['verdict']=='Confirmed')}")



    # ── 收集统计 + L4 建图 ──
    # ── 收集统计 ──
    gate_stats = context.get("gate_stats", {})
    extract_stats = context.get("extract_stats", {})

    # ── L4 建图 ──
    verified_by_jd = context.get("verified_by_jd", [])
    positions = []
    evidences = []
    ev_counter = 0
    from app.pipeline.l2_normalize import normalize_name as _norm
    for jd_id, tech_stack, skills in verified_by_jd:
        positions.append({"jd_id": jd_id, "title": "", "tech_stack": tech_stack, "skills": skills})
        for s in skills:
            if hasattr(s, 'evidence') and s.evidence:
                evidences.append({"eid": ev_counter, "jd_id": jd_id,
                                  "text": s.evidence, "skill": _norm(s.name)})
                ev_counter += 1

    try:
        graph_stats = await build_graph(positions, skill_stats, evidences)
    except Exception as e:
        logger.warning(f"[Agent] MySQL 建图失败: {e}")
        graph_stats = {"nodes": 0, "edges": 0}

    return {
        "n_jds": len(jds),
        "n_skills_extracted": sum(len(skills) for _, _, skills in verified_by_jd),
        "n_unique_skills": len(skill_stats),
        "spark_hits": extract_stats.get("spark_hits", 0),
        "rule_hits": extract_stats.get("rule_hits", 0),
        "gate_total": gate_stats.get("total", 0),
        "gate_rejected": gate_stats.get("rejected", 0),
        "intercept_rate": gate_stats.get("intercept_rate", 0),
        "debate_verdict": context.get("debate_verdict", {}).get("verdict", "N/A"),
        "graph": graph_stats,
        "elapsed_seconds": round(time.monotonic() - t0, 1),
    }
def _cluster_skills(skills: list[str], cooc_analyzer) -> list[list[str]]:
    """按共现关系聚类技能。

    策略：从最高 emergence 的技能开始，把与其 Jaccard 共现强度 > 0.3 的技能归入同一簇。
    已归类的技能不再参与后续聚类。
    """
    clusters = []
    used = set()

    for seed in skills:
        if seed in used:
            continue
        cluster = [seed]
        used.add(seed)

        # 查找与 seed 共现的技能
        for other in skills:
            if other in used:
                continue
            strength = cooc_analyzer.get_strength(seed, other)
            if strength > 0.3:
                cluster.append(other)
                used.add(other)

        clusters.append(cluster)

    return clusters


async def _save_new_role(term: str, skills: list[str], evidence_jds: list[dict],
                         verdict: dict, definition: dict) -> None:
    """将辩论结果写入 MySQL new_roles 表。"""
    try:
        from app.persistence.database import get_session
        from app.persistence.zhiyv_models import NewRole

        verdict_str = verdict.get("verdict", "Pending")
        conf = 0.8 if verdict_str == "Confirmed" else 0.5 if verdict_str == "Pending" else 0.2

        async for session in get_session():
            role = NewRole(
                role_name=term,
                responsibilities=definition.get("核心职责", {}).get("value", "") if isinstance(definition.get("核心职责"), dict) else "",
                responsibilities_confidence=conf,
                required_skills=skills,
                required_skills_confidence=conf,
                bonus_skills=definition.get("加分技能", {}).get("value", []) if isinstance(definition.get("加分技能"), dict) else [],
                industries=definition.get("典型行业应用场景", {}).get("value", []) if isinstance(definition.get("典型行业应用场景"), dict) else [],
                market_jd_count=len(evidence_jds),
                status=verdict_str.lower(),
                source="agent",
            )
            session.add(role)
            await session.commit()
    except Exception as e:
        logger.warning(f"新岗位写入 MySQL 失败: {e}")



# ══════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="职域智联图谱 · 全链路 pipeline")
    ap.add_argument("--n", type=int, default=10, help="处理 JD 条数")
    ap.add_argument("--no-spark", action="store_true", help="不调星火，纯规则")
    ap.add_argument("--agent", action="store_true", help="使用多 Agent 模式（Phase 2）")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    use_spark = not args.no_spark

    async def _run():
        """初始化数据库后执行 pipeline。"""
        from app.config import get_settings
        from app.persistence.database import init_db, close_db
        settings = get_settings()
        await init_db(settings)
        try:
            if args.agent:
                return await run_agent_pipeline(n=args.n, use_spark=use_spark)
            else:
                return await run_pipeline(n=args.n, use_spark=use_spark)
        finally:
            await close_db()

    result = asyncio.run(_run())

    print("\n" + "=" * 50)
    print("Pipeline 执行摘要")
    print("=" * 50)
    print(f"JD 数:        {result['n_jds']}")
    print(f"抽取技能数:   {result['n_skills_extracted']}")
    print(f"唯一技能数:   {result['n_unique_skills']}")
    print(f"星火/规则:    {result.get('spark_hits', 0)}/{result.get('rule_hits', 0)}")
    print(f"幻觉拦截率:   {result.get('intercept_rate', 0):.1%} "
          f"({result.get('gate_rejected', 0)}/{result.get('gate_total', 0)})")
    if "debate_verdict" in result:
        print(f"辩论裁决:     {result['debate_verdict']}")
    print(f"图谱:         {result.get('graph', {})}")
    print(f"耗时:         {result['elapsed_seconds']}s")
    print("\n[OK] 全链路闭环跑通")


if __name__ == "__main__":
    main()
