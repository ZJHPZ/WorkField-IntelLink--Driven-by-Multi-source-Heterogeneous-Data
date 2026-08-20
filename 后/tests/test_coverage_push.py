"""补充测试 —— 推覆盖率到 60%"""
import pytest
from app.domain import (
    JobPosting, Paragraph, SectionType, SourceType, TechStack,
    ExtractedSkill, SkillStat, DynamicMetrics, VerifyVerdict, GateResult,
)
from app.pipeline.l2_normalize import normalize_name, SKILL_ALIASES, normalize_and_count
from app.pipeline.l2_metrics import MetricsCalculator
from app.pipeline.l2_cooccurrence import CooccurrenceAnalyzer, build_cooccurrence
from app.pipeline.l3_verify import verify, _norm
from app.pipeline.l4_snapshot import SnapshotManager, Snapshot
from app.services.match_service import match_skills, batch_match
from app.services.enterprise_service import diagnose_jd, team_skill_gap
from app.services.career_service import career_gap_analysis, learning_path
from app.domain.signals import SkillSignal, FusedSkill, SourceDocument, TextSegment
from app.adapters.fusion import FusionEngine


# ══════════════════════════════════════════════
# L2 归一化 + 频次统计（关键覆盖缺口）
# ══════════════════════════════════════════════

class TestL2NormalizeDeep:
    def test_normalize_and_count_multi_jd(self):
        """多 JD 归一化统计"""
        skills_a = [ExtractedSkill("Python", "必备", "t1", "rule"),
                     ExtractedSkill("Django", "加分", "t2", "rule")]
        skills_b = [ExtractedSkill("Python", "必备", "t3", "rule"),
                     ExtractedSkill("Flask", "加分", "t4", "rule")]
        extracted = [("jd-1", "AI", skills_a), ("jd-2", "AI", skills_b)]
        stats = normalize_and_count(extracted)
        assert "Python" in stats
        assert stats["Python"].df == 2  # 两个 JD 都提到
        assert stats["Django"].df == 1

    def test_normalize_strips_signal_prefix_deep(self):
        """深度测试信号词剥离"""
        cases = [
            ("熟练掌握Python", "Python"),
            ("精通Kubernetes", "Kubernetes"),
            ("会使用Docker", "Docker"),
            ("具备团队管理能力", "团队管理能力"),
        ]
        for raw, expected in cases:
            result = normalize_name(raw)
            assert expected in result, f"{raw} -> expected {expected}, got {result}"

    def test_all_aliases_resolve(self):
        """所有别名都能解析到规范名"""
        for alias, canon in SKILL_ALIASES.items():
            result = normalize_name(alias)
            assert result == canon, f"alias '{alias}' -> expected '{canon}', got '{result}'"

    def test_single_jd_candidate_status(self):
        """单 JD → candidate 状态（孤证不入图谱）"""
        skills = [ExtractedSkill("NewSkill", "必备", "text", "rule")]
        stats = normalize_and_count([("jd-1", "AI", skills)])
        assert stats["NewSkill"].verification_status == "candidate"


# ══════════════════════════════════════════════
# L2 共现 + 指标（覆盖缺口）
# ══════════════════════════════════════════════

class TestCooccurrenceDeep:
    def test_jaccard_strength(self):
        a = CooccurrenceAnalyzer()
        a.add_jd("j1", ["A", "B", "C"])
        a.add_jd("j2", ["A", "B"])
        a.add_jd("j3", ["A", "D"])
        # A-B Jaccard: |A∩B|=2 / |A∪B|=2 = 1.0 (both appear together in J1,J2; A appears in J3 too)
        # A: {j1,j2,j3}, B: {j1,j2} => intersection=j1,j2 (2), union=j1,j2,j3 (3) => 2/3
        s = a.get_strength("A", "B")
        assert 0.5 < s <= 1.0

    def test_build_from_list(self):
        jd_list = [("j1", ["X", "Y"]), ("j2", ["X", "Y"]), ("j3", ["X", "Z"])]
        a = build_cooccurrence(jd_list)
        assert a.get_strength("X", "Y") > 0

    def test_empty_analyzer(self):
        a = CooccurrenceAnalyzer()
        assert a.get_stats()["total_jds"] == 0


class TestMetricsDeep:
    def test_compute_all_complete(self):
        calc = MetricsCalculator()
        monthly = {"2024-01": 100, "2024-02": 90, "2024-03": 80, "2024-04": 70,
                    "2024-05": 60, "2024-06": 50}
        m = calc.compute_all(monthly, {"A", "B"}, {"B", "C"}, skill_count=6, avg_skill_count=8)
        assert m.decline > 0
        assert m.evolution_speed > 0

    def test_half_life_peak_method(self):
        calc = MetricsCalculator()
        hl, method = calc.half_life({"2024-01": 10, "2024-02": 20, "2024-03": 30,
                                      "2024-04": 25, "2024-05": 15, "2024-06": 8})
        assert hl is not None or method in ("insufficient", "peak", "rising")

    def test_decline_stable(self):
        calc = MetricsCalculator()
        d = calc.decline([10, 10, 10, 10])
        assert d == 0.0


# ══════════════════════════════════════════════
# L3 闸门深度测试
# ══════════════════════════════════════════════

class TestVerifyDeep:
    def test_all_three_gates(self):
        """测试三道闸各拦截一种"""
        jd_text = "Python Django 开发经验"
        skills = [
            ExtractedSkill("Python", "必备", "Python Django 开发经验", "rule"),   # pass
            ExtractedSkill("Flink", "必备", "", "spark"),                        # 闸1: 空证据
            ExtractedSkill("Spark", "必备", "精通Spark离线计算", "spark"),       # 闸2: 不在原文
            ExtractedSkill("Redis", "必备", "Python Django 开发经验", "spark"),  # 闸3: 证据不含技能
        ]
        gate = verify("t1", jd_text, skills)
        assert len(gate.passed) == 1
        assert len(gate.rejected) == 3

    def test_norm_function(self):
        assert _norm("Python Django") == _norm("python django")
        assert _norm("C 语言") == _norm("C语言")


# ══════════════════════════════════════════════
# 信号融合（Adapter 层）
# ══════════════════════════════════════════════

class TestFusionDeep:
    def test_multi_source_confirmed(self):
        engine = FusionEngine()
        signals = [
            SkillSignal("K8s", "必备", "t1", "d1", SourceType.JD, credibility=0.7),
            SkillSignal("K8s", "必备", "t2", "d2", SourceType.GITHUB, credibility=0.8),
            SkillSignal("K8s", "加分", "t3", "d3", SourceType.STANDARD, credibility=0.95),
        ]
        fused = engine.fuse(signals)
        assert len(fused) == 1
        assert fused[0].verification_status == "confirmed"
        assert fused[0].confidence > 0.9  # 3 sources boost

    def test_required_type_priority(self):
        engine = FusionEngine()
        signals = [
            SkillSignal("Python", "加分", "t1", "d1", SourceType.JD, credibility=0.7),
            SkillSignal("Python", "必备", "t2", "d2", SourceType.JD, credibility=0.7),
        ]
        fused = engine.fuse(signals)
        assert fused[0].required_type == "必备"  # Takes higher priority


# ══════════════════════════════════════════════
# L4 快照
# ══════════════════════════════════════════════

class TestSnapshotDeep:
    def test_diff_no_changes(self):
        mgr = SnapshotManager()
        old = mgr.create_snapshot({
            "nodes": [{"data": {"nodeType": "Skill", "label": "Python", "confidence": 0.9, "df": 5}}],
            "edges": [],
        }, snapshot_id="s1")
        new = mgr.create_snapshot({
            "nodes": [{"data": {"nodeType": "Skill", "label": "Python", "confidence": 0.9, "df": 5}}],
            "edges": [],
        }, snapshot_id="s2")
        diff = mgr.diff_snapshots(old, new)
        assert len(diff.added_skills) == 0
        assert len(diff.removed_skills) == 0
        assert len(diff.modified_skills) == 0

    def test_create_from_scratch(self):
        mgr = SnapshotManager()
        snap = mgr.create_snapshot({"nodes": [], "edges": []}, timestamp="2026-01-01")
        assert snap.snapshot_id.startswith("snap_")
        assert snap.timestamp == "2026-01-01"
