"""领域模型 + Schema + 信号融合测试"""
import pytest
from app.domain import (
    JobPosting, Paragraph, SectionType, SourceType, TechStack, SkillLevel,
    ExtractedSkill, SkillStat, DynamicMetrics, Position, SkillNode,
    EvidenceNode, EvolutionDiff, MatchResult, GateResult, VerifyVerdict,
    PositionType, VerificationStatus,
)
from app.graph.schema import NodeLabel, RelType, make_id
from app.domain.signals import SkillSignal, FusedSkill, SourceDocument, TextSegment
from app.adapters.fusion import FusionEngine


class TestDomainModels:
    def test_job_posting_full_text(self):
        jd = JobPosting(
            jd_id="1", source=SourceType.JD, tech_stack=TechStack.AI,
            title="工程师", posted_date="2026-01-01",
            paragraphs=[
                Paragraph(section=SectionType.REQUIREMENT, text="Python必备"),
                Paragraph(section=SectionType.BONUS, text="Docker加分"),
            ],
        )
        assert "Python必备" in jd.full_text()
        assert "Docker加分" in jd.full_text()

    def test_gate_result_intercept_rate(self):
        sk = ExtractedSkill("test", "必备", "evidence", "rule")
        gate = GateResult(jd_id="1", total=3,
                          passed=[sk, sk],
                          rejected=[VerifyVerdict(sk, False, "伪造")])
        assert gate.intercept_rate == 1/3

    def test_skill_stat_defaults(self):
        st = SkillStat(name="Python")
        assert st.df == 0
        assert st.confidence == 0.0
        assert st.verification_status == "unverified"

    def test_dynamic_metrics(self):
        m = DynamicMetrics(emergence=0.5, decline=0.1, half_life=12.0,
                           half_life_method="peak")
        assert m.emergence == 0.5
        assert m.half_life == 12.0

    def test_evolution_diff_summary(self):
        diff = EvolutionDiff(
            snapshot_old="s1", snapshot_new="s2",
            timestamp_old="2024-01", timestamp_new="2024-06",
            added_skills=["A", "B"], removed_skills=["C"],
            modified_skills=[{"name": "D"}],
        )
        assert "新增 2" in diff.summary()
        assert "删除 1" in diff.summary()

    def test_position_types(self):
        p = Position(position_id="p1", name="AI工程师", tech_stack="AI",
                     position_type=PositionType.EMERGING)
        assert p.position_type == PositionType.EMERGING

    def test_skill_node(self):
        sn = SkillNode(skill_id="s1", name="Python", status="confirmed",
                       confidence=0.9)
        assert sn.name == "Python"


class TestGraphSchema:
    def test_make_id(self):
        assert make_id(NodeLabel.POSITION, "abc") == "pos::abc"
        assert make_id(NodeLabel.SKILL, "xyz") == "skill::xyz"
        assert make_id(NodeLabel.TECH_STACK, "ai") == "stack::ai"
        assert make_id(NodeLabel.EVIDENCE, "e1") == "ev::e1"

    def test_node_labels(self):
        assert NodeLabel.POSITION.value == "Position"
        assert NodeLabel.SKILL.value == "Skill"

    def test_rel_types(self):
        assert RelType.REQUIRES.value == "REQUIRES"
        assert RelType.SUPPORTED_BY.value == "SUPPORTED_BY"
        assert RelType.CO_OCCURS.value == "CO_OCCURS"


class TestFusionEngine:
    def test_fuse_single_source(self):
        engine = FusionEngine()
        signals = [
            SkillSignal("Python", "必备", "text1", "d1", SourceType.JD, credibility=0.7),
            SkillSignal("Python", "必备", "text2", "d2", SourceType.JD, credibility=0.7),
        ]
        fused = engine.fuse(signals)
        assert len(fused) == 1
        assert fused[0].name == "Python"
        assert fused[0].verification_status == "candidate"  # 单一源类型

    def test_fuse_multi_source(self):
        engine = FusionEngine()
        signals = [
            SkillSignal("Python", "必备", "t1", "d1", SourceType.JD, credibility=0.7),
            SkillSignal("Python", "必备", "t2", "d2", SourceType.GITHUB, credibility=0.8),
        ]
        fused = engine.fuse(signals)
        assert len(fused) == 1
        assert fused[0].verification_status == "confirmed"  # 多源

    def test_fuse_empty(self):
        engine = FusionEngine()
        assert engine.fuse([]) == []
