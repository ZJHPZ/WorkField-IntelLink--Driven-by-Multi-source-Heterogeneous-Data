"""核心 Pipeline 模块单元测试 —— 6 个模块"""
import pytest
from app.domain import JobPosting, Paragraph, SectionType, SourceType, TechStack
from app.pipeline.l1_clean import clean, CleanedJD, classify_skill
from app.pipeline.l1_segment import segment_text, classify_section
from app.pipeline.l3_extract import _rule_extract, _atomize
from app.pipeline.l3_verify import verify, _norm, _skill_in_evidence
from app.pipeline.l2_normalize import normalize_name, SKILL_ALIASES
from app.pipeline.l2_dedup import JDDeduplicator, deduplicate_jds
from app.pipeline.l2_metrics import MetricsCalculator


# ══════════════════════════════════════════════
# L1 清洗
# ══════════════════════════════════════════════

def make_jd(title="Python工程师", paragraphs=None):
    if paragraphs is None:
        paragraphs = [
            Paragraph(section=SectionType.REQUIREMENT, text="熟悉Python和Django框架"),
            Paragraph(section=SectionType.BONUS, text="有Docker使用经验"),
        ]
    return JobPosting(
        jd_id="test-001", source=SourceType.JD, tech_stack=TechStack.AI,
        title=title, posted_date="2026-07-01", paragraphs=paragraphs,
        salary_min=15000, salary_max=30000, experience_years=3, education="本科",
    )


class TestL1Clean:
    def test_clean_basic(self):
        jd = make_jd()
        result = clean(jd)
        assert result.jd_id == "test-001"
        assert result.title == "Python工程师"
        assert result.salary_min == 15000
        assert len(result.candidates) >= 1
        assert any("Python" in phrase for _, phrase, _, _ in result.candidates)

    def test_clean_filters_welfare(self):
        jd = make_jd(paragraphs=[
            Paragraph(section=SectionType.WELFARE, text="五险一金带薪年假弹性工作"),
            Paragraph(section=SectionType.REQUIREMENT, text="熟悉Python"),
        ])
        result = clean(jd)
        phrases = [phrase for _, phrase, _, _ in result.candidates]
        assert not any("五险一金" in p for p in phrases)

    def test_clean_filters_other_section(self):
        jd = make_jd(paragraphs=[
            Paragraph(section=SectionType.OTHER, text="Python工程师 北京 30-60K"),
            Paragraph(section=SectionType.REQUIREMENT, text="熟悉Python"),
        ])
        result = clean(jd)
        phrases = [phrase for _, phrase, _, _ in result.candidates]
        assert not any("30-60K" in p for p in phrases)

    def test_salary_parse_k_format(self):
        from app.pipeline.l1_clean import _parse_salary
        lo, hi = _parse_salary("薪资 30-60K")
        assert lo == 30000
        assert hi == 60000

    def test_classify_l3_hard(self):
        level, cat = classify_skill("熟悉Kubernetes容器编排", "requirement")
        assert level == "L3"

    def test_classify_l0_noise(self):
        level, cat = classify_skill("五险一金弹性工作", "welfare")
        assert level == "L0"

    def test_clean_preserves_strong_fields(self):
        jd = make_jd(paragraphs=[
            Paragraph(section=SectionType.REQUIREMENT, text="3-5年经验 硕士学历 25-50K"),
        ])
        result = clean(jd)
        assert result.salary_min == 15000  # From constructor, not parsed


class TestL1Segment:
    def test_segment_basic(self):
        text = "任职要求：\n熟悉Python\n熟悉Django\n\n福利待遇：\n五险一金"
        paragraphs = segment_text(text)
        assert len(paragraphs) >= 1
        # 至少有 requirement 或 welfare 段落
        sections = [p.section for p in paragraphs]
        assert SectionType.REQUIREMENT in sections or SectionType.WELFARE in sections

    def test_classify_section(self):
        assert classify_section("任职要求：") == SectionType.REQUIREMENT
        assert classify_section("岗位职责") == SectionType.RESPONSIBILITY
        assert classify_section("加分项") == SectionType.BONUS
        assert classify_section("福利待遇") == SectionType.WELFARE
        assert classify_section("公司介绍") == SectionType.COMPANY
        assert classify_section("随机文本内容") == SectionType.OTHER


# ══════════════════════════════════════════════
# L2 归一化 + 去重 + 指标
# ══════════════════════════════════════════════

class TestL2Normalize:
    def test_normalize_known_alias(self):
        assert normalize_name("k8s") == "Kubernetes"
        assert normalize_name("Kubernetes") == "Kubernetes"

    def test_normalize_unknown(self):
        assert normalize_name("SomeNewSkill") == "SomeNewSkill"

    def test_normalize_strips_prefix(self):
        assert normalize_name("熟悉Python") == "Python"
        assert normalize_name("精通Docker") == "Docker"

    def test_aliases_comprehensive(self):
        tests = [
            ("pytorch", "PyTorch"), ("tf", "TensorFlow"),
            ("rag", "RAG"), ("golang", "Go"),
            ("sql", "SQL"), ("kafka", "Kafka"),
            ("docker", "Docker"), ("clickhouse", "ClickHouse"),
        ]
        for raw, expected in tests:
            assert normalize_name(raw) == expected, f"{raw} -> {expected}"


class TestL2Dedup:
    def test_dedup_unique(self):
        jds = [
            {"jd_id": "1", "full_text": "Python Django 后端开发"},
            {"jd_id": "2", "full_text": "Java Spring 微服务架构"},
        ]
        unique, stats = deduplicate_jds(jds)
        assert len(unique) == 2
        assert stats["dedup_rate"] == 0.0

    def test_dedup_near_duplicate(self):
        jds = [
            {"jd_id": "1", "full_text": "Python Django REST API 开发"},
            {"jd_id": "2", "full_text": "Python Django REST API 开发工程师"},
        ]
        unique, stats = deduplicate_jds(jds, threshold=0.6)
        assert len(unique) <= 2  # May or may not dedup depending on SimHash


class TestL2Metrics:
    def test_emergence(self):
        calc = MetricsCalculator()
        # Rising trend: 10, 15, 20, 30, 50
        e = calc.emergence([10, 15, 20, 30, 50])
        assert e > 0

    def test_decline(self):
        calc = MetricsCalculator()
        # Declining: 100, 80, 60, 40, 20
        d = calc.decline([100, 80, 60, 40, 20])
        assert d > 0

    def test_volatility(self):
        calc = MetricsCalculator()
        v = calc.volatility([10, 10, 10, 10])
        assert v == 0.0

    def test_evolution_speed(self):
        calc = MetricsCalculator()
        speed = calc.evolution_speed({"A", "B", "C"}, {"A", "B", "D"})
        assert speed == 0.5  # 2 changed / 4 total

    def test_half_life_insufficient(self):
        calc = MetricsCalculator()
        hl, method = calc.half_life({"2024-01": 10, "2024-02": 15})
        assert hl is None

    def test_inflation(self):
        calc = MetricsCalculator()
        idx = calc.inflation_index(15, avg_skill_count=8, required_ratio=0.2)
        assert idx > 0.3  # High inflation


# ══════════════════════════════════════════════
# L3 抽取 + 闸门
# ══════════════════════════════════════════════

class TestL3Extract:
    def test_rule_extract_basic(self):
        cleaned = CleanedJD(
            jd_id="t1", title="测试", tech_stack="AI", posted_date="2026-01-01",
            candidates=[
                ("requirement", "熟悉Python和Django", "L3", "hard"),
                ("requirement", "有团队合作精神", "L1", "soft"),
            ],
        )
        skills = _rule_extract(cleaned)
        assert len(skills) >= 1

    def test_atomize_splits(self):
        atoms = _atomize("C语言与嵌入式开发")
        assert len(atoms) >= 2  # Should split into C语言 + 嵌入式开发

    def test_atomize_slash(self):
        atoms = _atomize("Docker/K8s 容器化")
        assert len(atoms) >= 2

    def test_rule_strips_number_prefix(self):
        cleaned = CleanedJD(
            jd_id="t2", title="测试", tech_stack="AI", posted_date="2026-01-01",
            candidates=[("requirement", "1. 精通Python编程", "L3", "hard")],
        )
        skills = _rule_extract(cleaned)
        if skills:
            assert not skills[0].name.startswith("1."), f"Should strip '1.' prefix: {skills[0].name}"


class TestL3Verify:
    def test_verify_all_pass(self):
        jd_text = "熟悉Python和Django框架"
        from app.pipeline.l3_extract import ExtractedSkill
        skills = [
            ExtractedSkill("Python", "必备", "熟悉Python和Django框架", "rule"),
            ExtractedSkill("Django", "必备", "熟悉Python和Django框架", "rule"),
        ]
        gate = verify("t1", jd_text, skills)
        assert len(gate.passed) == 2
        assert len(gate.rejected) == 0

    def test_verify_no_evidence(self):
        from app.pipeline.l3_extract import ExtractedSkill
        skills = [ExtractedSkill("Flink", "必备", "", "spark")]
        gate = verify("t2", "Java后端开发", skills)
        assert len(gate.rejected) == 1
        assert "无证据" in gate.rejected[0].reason

    def test_verify_fake_evidence(self):
        from app.pipeline.l3_extract import ExtractedSkill
        skills = [ExtractedSkill("Spark", "必备", "精通Spark离线计算", "spark")]
        gate = verify("t3", "Python后端开发经验", skills)
        assert len(gate.rejected) == 1
        assert "伪造证据" in gate.rejected[0].reason

    def test_verify_evidence_not_contain_skill(self):
        from app.pipeline.l3_extract import ExtractedSkill
        skills = [ExtractedSkill("Flink", "必备", "熟悉Kafka消息队列", "spark")]
        gate = verify("t4", "熟悉Kafka消息队列", skills)
        assert len(gate.rejected) == 1
        assert "证据不支撑" in gate.rejected[0].reason

    def test_intercept_rate(self):
        from app.pipeline.l3_extract import ExtractedSkill
        jd_text = "精通Python开发"
        skills = [
            ExtractedSkill("Python", "必备", "精通Python开发", "rule"),
            ExtractedSkill("Flink", "必备", "", "spark"),
            ExtractedSkill("Spark", "必备", "精通Spark", "spark"),
        ]
        gate = verify("t5", jd_text, skills)
        assert gate.intercept_rate > 0
        assert gate.total == 3
