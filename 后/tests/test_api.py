"""API 层单元测试 —— FastAPI TestClient，Mock Neo4j 依赖。

无需启动真实服务器或 Neo4j。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ★ 关键：在 import app.main 之前就 mock 掉 Neo4j
mock_init = AsyncMock()
mock_close = AsyncMock()


@pytest.fixture
def client():
    """创建 TestClient，所有 Neo4j/DB 调用均已 mock。"""
    with patch("app.graph.client.init_neo4j", mock_init), \
         patch("app.graph.client.close_neo4j", mock_close), \
         patch("app.graph.client._driver", None), \
         patch("app.graph.repository.run_cypher", AsyncMock(return_value=[])), \
         patch("app.persistence.database.init_db", AsyncMock()), \
         patch("app.persistence.database.close_db", AsyncMock()):
        from app.main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as c:
            yield c


class TestGraphAPI:
    def test_get_graph_mocked(self, client):
        mock_data = {"nodes": [{"id": "1", "data": {"nodeType": "Skill", "label": "Python"}}], "edges": []}
        with patch("app.api.graph.get_full_graph", new_callable=AsyncMock, return_value=mock_data):
            resp = client.get("/api/graph")
            assert resp.status_code == 200


class TestPositionsAPI:
    def test_get_positions_mocked(self, client):
        mock_nodes = [{"p": {"position_id": "pos::1", "name": "AI", "tech_stack": "AI"}}]
        with patch("app.api.positions.get_positions", new_callable=AsyncMock, return_value=mock_nodes):
            resp = client.get("/api/positions")
            assert resp.status_code == 200

    def test_get_position_404(self, client):
        with patch("app.api.positions.get_position_detail", new_callable=AsyncMock, return_value=None):
            resp = client.get("/api/positions/pos::nonexist")
            assert resp.status_code == 404


class TestMatchAPI:
    def test_match_success(self, client):
        resp = client.post("/api/match", json={
            "position_name": "AI", "user_skills": ["Python"],
            "position_skills": [{"name": "Python", "required_type": "必备", "confidence": 0.9}],
        })
        assert resp.status_code == 200
        assert "match_rate" in resp.json()

    def test_batch_match(self, client):
        resp = client.post("/api/match/batch", json={
            "position_name": "AI",
            "position_skills": [{"name": "Python", "required_type": "必备"}],
            "user_skills_list": [["Python"], ["Java"]],
        })
        assert resp.status_code == 200


class TestEnterpriseAPI:
    def test_diagnose_jd(self, client):
        resp = client.post("/api/enterprise/jd/diagnose", json={
            "jd_id": "jd-1", "title": "工程师",
            "skills": [{"name": "Python"}, {"name": "Django"}],
        })
        assert resp.status_code == 200

    def test_validate_position(self, client):
        resp = client.post("/api/enterprise/positions/validate", json={
            "term": "AI提示词工程师",
            "emerging_skills": ["Prompt Engineering"],
            "evidence_jds": [{"title": "JD1", "full_text": "需要Prompt经验"}],
        })
        assert resp.status_code == 200


class TestPersonalAPI:
    def test_career_gap(self, client):
        resp = client.post("/api/personal/career/gap", json={
            "user_skills": ["Python"],
            "position_skills": [{"name": "Python", "required_type": "必备"}],
            "position_name": "AI",
        })
        assert resp.status_code == 200

    def test_learning_path(self, client):
        resp = client.post("/api/personal/career/learning-path", json={
            "user_skills": ["Python"],
            "position_skills": [{"name": "Python", "required_type": "必备"}, {"name": "PyTorch", "required_type": "必备"}],
            "position_name": "AI",
        })
        assert resp.status_code == 200

    def test_skill_freshness(self, client):
        resp = client.post("/api/personal/career/skill-freshness",
                           json={"user_skills": ["Python"], "skill_metrics": {}})
        assert resp.status_code == 200

    def test_switch_feasibility(self, client):
        resp = client.post("/api/personal/career/switch-feasibility", json={
            "from_skills": ["Python"], "to_skills": ["PyTorch"],
            "from_name": "后端", "to_name": "AI",
        })
        assert resp.status_code == 200

    def test_career_growth(self, client):
        resp = client.post("/api/personal/career/growth", json={
            "position_skills": [{"name": "Python", "level": "初级"}],
        })
        assert resp.status_code == 200


class TestMetricsAPI:
    def test_emerging_skills(self, client):
        resp = client.get("/api/metrics/emerging")
        assert resp.status_code == 200


class TestSnapshotsAPI:
    def test_list_snapshots(self, client):
        with patch("app.api.graph._snap_manager.list_snapshots", return_value=[]):
            resp = client.get("/api/graph/snapshots")
            assert resp.status_code == 200
