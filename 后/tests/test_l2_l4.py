"""L2 + L4 模块补充测试 —— 归一化统计、共现、快照"""
import pytest
from app.pipeline.l2_normalize import normalize_and_count, normalize_name
from app.pipeline.l2_cooccurrence import CooccurrenceAnalyzer, build_cooccurrence
from app.pipeline.l2_metrics import MetricsCalculator
from app.pipeline.l4_snapshot import SnapshotManager, Snapshot, SnapshotDiff
from app.domain import ExtractedSkill, SkillStat


class TestNormalizeAndCount:
    def test_basic_count(self):
        skills = [
            ExtractedSkill("Python", "必备", "熟悉Python", "rule"),
            ExtractedSkill("Django", "加分", "了解Django", "rule"),
            ExtractedSkill("Python", "必备", "掌握Python", "rule"),
        ]
        extracted = [("jd-1", "AI", skills), ("jd-2", "AI", [skills[0]])]
        stats = normalize_and_count(extracted)
        assert len(stats) > 0
        assert "Python" in stats
        assert stats["Python"].df >= 1

    def test_alias_normalization_in_count(self):
        skills = [
            ExtractedSkill("k8s", "必备", "熟悉k8s", "rule"),
            ExtractedSkill("kubernetes", "必备", "了解kubernetes", "rule"),
        ]
        extracted = [("jd-1", "AI", skills)]
        stats = normalize_and_count(extracted)
        assert "Kubernetes" in stats
        assert stats["Kubernetes"].df >= 1

    def test_confidence_assignment(self):
        skills = [ExtractedSkill("Python", "必备", "test", "rule") for _ in range(3)]
        extracted = [("jd-1", "AI", [skills[0]]), ("jd-2", "AI", [skills[1]]), ("jd-3", "AI", [skills[2]])]
        stats = normalize_and_count(extracted)
        assert stats["Python"].confidence > 0
        assert stats["Python"].df == 3
        assert stats["Python"].verification_status == "confirmed"


class TestCooccurrence:
    def test_basic_cooccurrence(self):
        analyzer = CooccurrenceAnalyzer()
        analyzer.add_jd("jd-1", ["Python", "Django", "Docker"])
        analyzer.add_jd("jd-2", ["Python", "Django", "Flask"])
        analyzer.add_jd("jd-3", ["Java", "Spring"])

        strength = analyzer.get_strength("Python", "Django")
        assert strength > 0
        assert analyzer.get_stats()["total_jds"] == 3

    def test_build_cooccurrence(self):
        jd_list = [
            ("j1", ["A", "B", "C"]),
            ("j2", ["A", "B"]),
        ]
        analyzer = build_cooccurrence(jd_list)
        assert analyzer.get_strength("A", "B") > 0
        assert analyzer.get_strength("A", "C") < analyzer.get_strength("A", "B")

    def test_top_cooccurring(self):
        analyzer = CooccurrenceAnalyzer()
        for i in range(5):
            analyzer.add_jd(f"j{i}", ["Python", "Django", "Docker"])
        for i in range(2):
            analyzer.add_jd(f"j{i+5}", ["Python", "Flask"])

        top = analyzer.get_top_cooccurring("Python", top_k=3)
        assert len(top) >= 1
        # Django (5 co-occurrences) should rank higher than Flask (2)
        django_entry = next((t for t in top if t[0] == "Django"), None)
        flask_entry = next((t for t in top if t[0] == "Flask"), None)
        assert django_entry is not None

    def test_get_stats(self):
        analyzer = CooccurrenceAnalyzer()
        analyzer.add_jd("j1", ["A", "B", "C"])
        analyzer.add_jd("j2", ["A", "D"])
        stats = analyzer.get_stats()
        assert stats["total_jds"] == 2
        assert stats["total_skills"] == 4
        assert stats["avg_skills_per_jd"] == 2.5


class TestL4Snapshot:
    def test_create_snapshot(self):
        mgr = SnapshotManager()
        graph_data = {
            "nodes": [
                {"data": {"nodeType": "Skill", "label": "Python", "confidence": 0.9, "df": 5, "status": "confirmed"}},
                {"data": {"nodeType": "Skill", "label": "Django", "confidence": 0.8, "df": 3, "status": "confirmed"}},
            ],
            "edges": [
                {"source": "skill::Python", "target": "skill::Django", "data": {"rel": "CO_OCCURS"}},
            ],
        }
        snap = mgr.create_snapshot(graph_data, description="Test")
        assert snap.snapshot_id.startswith("snap_")
        assert len(snap.skills) == 2
        assert snap.metadata["skill_count"] == 2

    def test_diff_snapshots(self):
        mgr = SnapshotManager()
        old = mgr.create_snapshot({
            "nodes": [
                {"data": {"nodeType": "Skill", "label": "Python", "confidence": 0.8, "df": 3}},
                {"data": {"nodeType": "Skill", "label": "Java", "confidence": 0.7, "df": 2}},
            ],
            "edges": [],
        }, snapshot_id="old", timestamp="2024-01-01")
        new = mgr.create_snapshot({
            "nodes": [
                {"data": {"nodeType": "Skill", "label": "Python", "confidence": 0.95, "df": 8}},
                {"data": {"nodeType": "Skill", "label": "Go", "confidence": 0.8, "df": 5}},
            ],
            "edges": [],
        }, snapshot_id="new", timestamp="2024-06-01")

        diff = mgr.diff_snapshots(old, new)
        assert "Go" in diff.added_skills
        assert "Java" in diff.removed_skills
        assert len(diff.modified_skills) == 1
        assert diff.modified_skills[0]["name"] == "Python"

    def test_list_snapshots(self):
        mgr = SnapshotManager()
        mgr.create_snapshot({"nodes": [], "edges": []}, timestamp="2024-01-01",
                            snapshot_id="s1", description="First")
        mgr.create_snapshot({"nodes": [], "edges": []}, timestamp="2024-06-01",
                            snapshot_id="s2", description="Second")
        snapshots = mgr.list_snapshots()
        assert len(snapshots) == 2

    def test_to_dict_from_dict(self):
        mgr = SnapshotManager()
        snap = mgr.create_snapshot({
            "nodes": [{"data": {"nodeType": "Skill", "label": "Python", "confidence": 0.9, "df": 5}}],
            "edges": [],
        })
        d = snap.to_dict()
        restored = Snapshot.from_dict(d)
        assert restored.snapshot_id == snap.snapshot_id
        assert "Python" in restored.skills


class TestL2MetricsExtra:
    def test_compute_all(self):
        calc = MetricsCalculator()
        metrics = calc.compute_all(
            monthly_counts={"2024-01": 10, "2024-02": 15, "2024-03": 20, "2024-04": 25},
            old_skills={"A", "B"}, new_skills={"B", "C"},
            skill_count=5, avg_skill_count=8, required_ratio=0.6,
        )
        assert metrics.emergence > 0
        assert metrics.evolution_speed > 0
        assert 0 <= metrics.inflation_index <= 1
