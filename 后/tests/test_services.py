"""服务层单元测试 —— match_service, resume_service, enterprise_service, career_service"""
import pytest
from app.services.match_service import match_skills, batch_match
from app.services.enterprise_service import diagnose_jd, team_skill_gap, talent_forecast
from app.services.career_service import (
    career_gap_analysis, learning_path, skill_freshness,
    switch_feasibility, career_growth,
)


class TestMatchService:
    def test_basic_match(self):
        result = match_skills(
            ["Python", "SQL", "Git"],
            [
                {"name": "Python", "required_type": "必备", "confidence": 0.9},
                {"name": "PyTorch", "required_type": "必备", "confidence": 0.8},
                {"name": "Docker", "required_type": "加分", "confidence": 0.7},
            ],
            position_name="AI工程师",
        )
        assert 0 <= result.match_rate <= 1
        assert "Python" in result.matched_skills
        assert any(m["name"] == "PyTorch" for m in result.missing_skills)
        assert result.position_name == "AI工程师"

    def test_perfect_match(self):
        result = match_skills(
            ["Python", "Django", "Docker"],
            [
                {"name": "Python", "required_type": "必备"},
                {"name": "Django", "required_type": "必备"},
                {"name": "Docker", "required_type": "加分"},
            ],
        )
        assert result.match_rate > 0.8

    def test_no_match(self):
        result = match_skills(
            ["Java", "Spring"],
            [{"name": "Python", "required_type": "必备"}],
        )
        assert result.match_rate == 0.0

    def test_batch_match(self):
        results = batch_match(
            [["Python", "SQL"], ["Java", "Spring"]],
            [{"name": "Python", "required_type": "必备"}, {"name": "Docker", "required_type": "加分"}],
            position_name="后端",
        )
        assert len(results) == 2
        assert results[0].match_rate > results[1].match_rate

    def test_partial_match(self):
        result = match_skills(
            ["TensorFlow"],
            [{"name": "TensorFlow", "required_type": "必备"}],
        )
        # Fuzzy matching might pick up similar names
        assert len(result.matched_skills) + len(result.partial_skills) >= 1


class TestEnterpriseService:
    def test_diagnose_jd_normal(self):
        skills = [{"name": "Python"}, {"name": "Django"}, {"name": "Docker"},
                   {"name": "SQL"}, {"name": "Git"}]
        result = diagnose_jd("jd-1", "后端工程师", skills)
        assert 0 <= result.inflation_index <= 1
        assert result.skill_count == 5

    def test_diagnose_inflated(self):
        skills = [{"name": s} for s in [
            "Python", "Django", "Docker", "K8s", "SQL", "Git", "Linux",
            "Redis", "Nginx", "MongoDB", "Kafka", "Spark", "Flink", "Hadoop",
        ]]
        result = diagnose_jd("jd-2", "全栈工程师", skills)
        assert result.inflation_index > 0
        assert len(result.inflated_items) >= 1

    def test_team_gap(self):
        results = [
            {"match_rate": 0.8, "matched_skills": ["A"], "missing_skills": [{"name": "B", "canonical": "B"}]},
            {"match_rate": 0.5, "matched_skills": [], "missing_skills": [{"name": "B", "canonical": "B"}, {"name": "C", "canonical": "C"}]},
        ]
        report = team_skill_gap(results, "AI工程师")
        assert report.total_members == 2
        assert len(report.common_gaps) >= 1
        assert report.common_gaps[0]["skill"] == "B"

    def test_talent_forecast(self):
        metrics = {
            "Python": {"emergence": 0.8, "decline": 0.1},
            "jQuery": {"emergence": 0.1, "decline": 0.9},
        }
        result = talent_forecast(metrics)
        assert len(result["hot_skills"]) >= 1
        assert len(result["cooling_skills"]) >= 1


class TestCareerService:
    def test_gap_analysis(self):
        result = career_gap_analysis(
            ["Python", "SQL"],
            [{"name": "Python", "required_type": "必备"}, {"name": "PyTorch", "required_type": "必备"}],
            "AI工程师",
        )
        assert "match_rate" in result
        assert result["match_rate"] > 0

    def test_learning_path(self):
        result = learning_path(
            ["Python"],
            [{"name": "Python", "required_type": "必备"}, {"name": "PyTorch", "required_type": "必备"}],
            "AI工程师",
        )
        assert len(result["learning_path"]) >= 1

    def test_skill_freshness_no_alerts(self):
        result = skill_freshness(["Python"], {"Python": {"half_life": 24, "decline": 0.0}})
        assert len(result["alerts"]) == 0

    def test_skill_freshness_alert(self):
        result = skill_freshness(["jQuery"], {"jQuery": {"half_life": 6, "decline": 0.5}})
        assert len(result["alerts"]) >= 1

    def test_switch_feasibility(self):
        result = switch_feasibility(
            ["Python", "SQL", "Docker"], ["Python", "PyTorch", "K8s"],
            "后端", "AI工程师",
        )
        assert 0 <= result["jaccard_similarity"] <= 1
        assert result["transferable_count"] >= 1

    def test_career_growth(self):
        result = career_growth([
            {"name": "Python", "level": "初级"},
            {"name": "Django", "level": "初级"},
            {"name": "Docker", "level": "中级"},
            {"name": "System Design", "level": "高级"},
        ])
        assert result["junior"]["count"] >= 1
        assert result["senior"]["count"] >= 1
