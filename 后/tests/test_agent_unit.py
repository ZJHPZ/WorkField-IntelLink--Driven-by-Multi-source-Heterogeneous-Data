"""多智能体系统单元测试 —— 7 个测试用例"""
import asyncio
import pytest
from app.agents.agent_state import IntentType, MultiAgentState


def test_01_system_init(system, registry):
    """测试 1: Agent 系统初始化"""
    agents = registry.get_all()
    assert len(agents) == 9, f"Expected 9 agents, got {len(agents)}"
    assert "extractor" in agents
    assert "verifier" in agents
    assert "normalizer" in agents
    assert "matcher" in agents
    assert "discoverer" in agents
    assert "judge" in agents
    assert "evolver" in agents
    assert "suggester" in agents
    assert "orchestrator" in agents


def test_02_intent_routing(router):
    """测试 2: 意图路由"""
    assert router.route(IntentType.EXTRACT_SKILLS) == "extractor"
    assert router.route(IntentType.MATCH_POSITION) == "matcher"
    assert router.route(IntentType.DISCOVER_ROLE) == "discoverer"
    assert router.route(IntentType.CAREER_GAP) == "suggester"
    assert router.get_chain("matcher") == ["extractor", "normalizer"]
    assert router.get_chain("suggester") == ["matcher"]


def test_03_extract_agent(registry):
    """测试 3: ExtractAgent 联邦式执行"""
    from app.pipeline.l1_clean import CleanedJD

    cleaned = CleanedJD(
        jd_id="test-001", title="AI工程师", tech_stack="人工智能",
        posted_date="2026-07-01",
        candidates=[
            ("requirement", "熟悉PyTorch和TensorFlow", "L3", "hard"),
            ("requirement", "精通Transformer架构", "L3", "hard"),
            ("bonus", "有DeepSpeed经验", "L3", "hard"),
        ],
    )

    state = MultiAgentState(
        current_intent=IntentType.EXTRACT_SKILLS,
        payload={"cleaned_jd": cleaned},
    )

    agent = registry.get("extractor")
    result = asyncio.run(agent.process(state))
    assert result["success"] is True
    skills = result["data"]["skills"]
    assert len(skills) >= 2
    assert any("PyTorch" in s.name for s in skills)


def test_04_verify_agent(registry):
    """测试 4: VerifyAgent 幻觉闸门"""
    from app.pipeline.l3_extract import ExtractedSkill
    from app.pipeline.l1_clean import CleanedJD

    # Step 1: Extract
    cleaned = CleanedJD(
        jd_id="test-v", title="测试", tech_stack="AI", posted_date="2026-01-01",
        candidates=[("requirement", "熟悉Python和Docker容器化", "L3", "hard")],
    )
    extract_state = MultiAgentState(
        current_intent=IntentType.EXTRACT_SKILLS,
        payload={"cleaned_jd": cleaned},
    )
    extract_result = asyncio.run(registry.get("extractor").process(extract_state))
    skills = extract_result["data"]["skills"]

    # Step 2: Verify
    jd_text = "熟悉Python和Docker容器化"
    verify_state = MultiAgentState(
        current_intent=IntentType.VERIFY_SKILLS,
        payload={
            "extracted_by_jd": [("test-v", "AI", skills)],
            "jd_fulltext_map": {"test-v": jd_text},
        },
    )
    result = asyncio.run(registry.get("verifier").process(verify_state))
    data = result["data"]
    assert data["gate_total"] > 0
    assert data["gate_rejected"] == 0  # All rule-extracted, all should pass
    assert "verified_by_jd" in data


def test_05_normalize_agent(registry):
    """测试 5: NormalizeAgent 归一化"""
    from app.pipeline.l3_extract import ExtractedSkill
    from app.pipeline.l1_clean import CleanedJD

    cleaned = CleanedJD(
        jd_id="test-n", title="测试", tech_stack="AI", posted_date="2026-01-01",
        candidates=[("requirement", "熟悉k8s和PyTorch框架", "L3", "hard")],
    )
    es = MultiAgentState(current_intent=IntentType.EXTRACT_SKILLS, payload={"cleaned_jd": cleaned})
    skills = asyncio.run(registry.get("extractor").process(es))["data"]["skills"]

    ns = MultiAgentState(
        current_intent=IntentType.NORMALIZE_SKILLS,
        payload={"verified_by_jd": [("test-n", "AI", skills)]},
    )
    result = asyncio.run(registry.get("normalizer").process(ns))
    data = result["data"]
    assert len(data["skill_stats"]) > 0
    # k8s should be normalized to Kubernetes
    names = list(data["skill_stats"].keys())
    assert any("Kubernetes" in n for n in names) or any("k8s" in n.lower() for n in names)


def test_06_evolution_agent(registry):
    """测试 6: EvolutionAgent 演化分析"""
    state = MultiAgentState(
        current_intent=IntentType.EVOLUTION_ANALYSIS,
        payload={
            "snapshots": [
                {"snapshot_id": "s1", "skills": {"Python": {"confidence": 0.8}, "Java": {"confidence": 0.7}}},
                {"snapshot_id": "s2", "skills": {"Python": {"confidence": 0.9}, "Go": {"confidence": 0.8}}},
            ],
        },
    )
    result = asyncio.run(registry.get("evolver").process(state))
    data = result["data"]
    assert data["added_skills"] == ["Go"]
    assert data["removed_skills"] == ["Java"]
    assert "新增1/删除1" in data["summary"]


def test_07_match_agent(registry, system):
    """测试 7: MatchAgent 人岗匹配"""
    result = asyncio.run(system.process(IntentType.MATCH_POSITION, {
        "user_skills": ["Python", "SQL", "Git"],
        "position_skills": [
            {"name": "Python", "required_type": "必备", "confidence": 0.9},
            {"name": "PyTorch", "required_type": "必备", "confidence": 0.8},
            {"name": "Docker", "required_type": "加分", "confidence": 0.7},
        ],
        "position_name": "AI工程师",
    }))
    data = result["result"]["data"]
    assert result["agent_id"] == "matcher"
    assert 0 <= data["match_rate"] <= 1
    assert "Python" in data["matched_skills"]
    assert any(m["name"] == "PyTorch" for m in data["missing_skills"])
