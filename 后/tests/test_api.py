"""API 层单元测试 —— FastAPI TestClient，Mock Neo4j 依赖。

无需启动真实服务器或 Neo4j。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.persistence.zhiyv_models import UserProfile, UserSkill, UserMatch, EnterpriseProfile

# ★ 关键：在 import app.main 之前就 mock 掉 Neo4j
mock_init = AsyncMock()
mock_close = AsyncMock()


@pytest.fixture
def client():
    """创建 TestClient，所有 Neo4j/DB 调用均已 mock。"""
    with patch("app.graph.client.init_neo4j", mock_init), \
         patch("app.graph.client.close_neo4j", mock_close), \
         patch("app.graph.client._driver", None), \
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


class TestPersonalAIChat:
    """/api/personal/ai/chat —— Coze 帕克分支 + 本地回退分支的 SSE 契约。"""

    def test_ai_chat_coze_branch_preserves_contract(self, client):
        """配置了 COZE_API_TOKEN → 走帕克，SSE 契约不变（agent_start(parker)/content/agent_end/[DONE]）。"""
        from types import SimpleNamespace

        async def fake_stream(msg, sid, timeout=120.0):
            yield {"type": "start"}
            yield {"type": "content", "content": "你好，"}
            yield {"type": "content", "content": "帕克。\n\n**下一段**"}
            yield {"type": "done"}

        fake_settings = SimpleNamespace(
            COZE_API_TOKEN="test-token", COZE_API_URL="https://example.com/stream_run"
        )
        with patch("app.config.get_settings", return_value=fake_settings), \
             patch("app.services.coze_service.stream_chat", side_effect=fake_stream):
            resp = client.post("/api/personal/ai/chat",
                               json={"message": "帮我做规划", "session_id": "chat-1"})

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.text
        assert '"type": "agent_start"' in body and '"agent": "parker"' in body
        assert '"type": "content"' in body and "你好，" in body and "帕克" in body
        assert '"type": "agent_end"' in body
        assert "[DONE]" in body

    def test_ai_chat_fallback_when_no_token(self, client):
        """未配置 COZE_API_TOKEN → 回退星火/规则分支（agent thinking），不打网络。"""
        from types import SimpleNamespace

        fake_settings = SimpleNamespace(COZE_API_TOKEN="", COZE_API_URL="https://example.com/stream_run")
        with patch("app.config.get_settings", return_value=fake_settings), \
             patch("app.api.deps.get_llm_client", return_value=None):
            resp = client.post("/api/personal/ai/chat",
                               json={"message": "转行可行吗", "session_id": "chat-2"})

        assert resp.status_code == 200
        body = resp.text
        assert '"agent": "thinking"' in body
        assert '"type": "agent_end"' in body
        assert "[DONE]" in body


class TestBuildUserContext:
    """_build_user_context —— 真实 DB 数据进上下文 + DB 失败回退 demo。"""

    def test_happy_path_includes_real_data(self):
        """fake session 返回真实档案/技能/匹配/学习路径 → 上下文包含这些内容。"""
        import asyncio
        from app.api.personal import _build_user_context
        from app.persistence.zhiyv_models import (
            UserProfile, UserSkill, UserMatch, LearningStepModel,
        )

        profile = UserProfile(
            user_id="demo_user", name="李雷", title="前端开发工程师",
            experience_years="5", education="本科", major="计算机科学",
            city="北京", target_role="AI 算法工程师", target_city="上海",
            target_industry="互联网", salary_min=25, salary_max=40,
        )
        skill = UserSkill(
            user_id="demo_user", skill_name="Python", category="编程语言",
            level="advanced", freshness=92, years_of_experience=3.0,
        )
        match = UserMatch(
            user_id="demo_user", position_name="AI 算法工程师",
            company="字节跳动", match_rate=85.0,
            matched_skills={"Python": 3}, missing_skills={"PyTorch": 0},
        )
        step = LearningStepModel(
            user_id="demo_user", title="学习 PyTorch", skill="PyTorch",
            status="in_progress", progress=40, estimated_hours=30, sort_order=1,
        )

        session = _FakeSession({
            "user_profiles": [profile],
            "user_skills": [skill],
            "user_matches": [match],
            "learning_steps": [step],
        })

        with patch("app.api.personal.get_session",
                   new=_make_fake_get_session(session)):
            ctx = asyncio.run(_build_user_context())

        assert "李雷" in ctx
        assert "前端开发工程师" in ctx
        assert "Python" in ctx
        assert "advanced" in ctx
        assert "AI 算法工程师" in ctx
        assert "85" in ctx
        assert "PyTorch" in ctx
        assert "学习 PyTorch" in ctx

    def test_falls_back_to_demo_on_db_error(self):
        """DB 未初始化（get_session 抛错）→ 回退 demo 画像，上下文非空。"""
        import asyncio
        from app.api.personal import _build_user_context

        def _boom():
            raise RuntimeError("数据库未初始化，请先调用 init_db()")

        with patch("app.api.personal.get_session", side_effect=_boom):
            ctx = asyncio.run(_build_user_context())

        assert "姓名" in ctx
        assert len(ctx) > 20


# ── _build_user_context 测试辅助：fake session ──

class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return _FakeScalars(self._rows)


class _FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    """execute 按表名分发行（select(...).froms[0].name）。"""

    def __init__(self, rows_by_table):
        self._tables = rows_by_table
        self.added = []

    async def execute(self, stmt):
        try:
            name = stmt.get_final_froms()[0].name
        except AttributeError:  # 兼容旧版本 SQLAlchemy
            name = stmt.froms[0].name
        return _FakeResult(self._tables.get(name, []))

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


def _make_fake_get_session(session):
    """返回一个可调用的 async generator 函数，yield 给定 session。"""
    async def _gen():
        yield session
    return _gen


class TestTalentPoolAPI:
    """企业侧人才库端点 —— patch talent_pool_service.get_session 返回 fake session。"""

    @staticmethod
    def _rows():
        return {
            "user_profiles": [
                UserProfile(user_id="cand_li_wei", name="李伟", title="高级后端开发工程师",
                            target_role="资深后端工程师", city="上海", experience_years="8-10年",
                            education="本科", salary_min=35, salary_max=55),
            ],
            "talent_pool_entries": [],
            "user_skills": [
                UserSkill(user_id="cand_li_wei", skill_name="Go", canonical_name="go",
                          category="编程语言", level="expert", freshness=92, years_of_experience=8.0,
                          market_demand=90, status="healthy"),
            ],
            "user_matches": [
                UserMatch(user_id="cand_li_wei", position_id="pos-go-senior",
                          position_name="资深后端工程师", company="某云原生平台", match_rate=88.0,
                          matched_skills={"Go": 3, "系统设计": 3}, missing_skills={"Rust": 0},
                          salary_range="45-82K"),
            ],
        }

    def test_list_talent_pool(self, client):
        session = _FakeSession(self._rows())
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/talent-pool")
        assert resp.status_code == 200
        body = resp.json()
        assert "candidates" in body
        assert len(body["candidates"]) == 1
        c = body["candidates"][0]
        assert c["id"] == "cand_li_wei"
        assert c["name"] == "李伟"
        assert c["bestMatchRate"] == 88.0
        assert c["topSkills"] == ["Go"]

    def test_list_talent_pool_with_filters(self, client):
        session = _FakeSession(self._rows())
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/talent-pool",
                              params={"position": "资深后端", "city": "上海", "skill": "go"})
        assert resp.status_code == 200
        assert len(resp.json()["candidates"]) == 1

    def test_list_talent_pool_empty(self, client):
        session = _FakeSession({"user_profiles": []})
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/talent-pool")
        assert resp.status_code == 200
        assert resp.json() == {"candidates": []}

    def test_talent_pool_detail(self, client):
        session = _FakeSession(self._rows())
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/talent-pool/cand_li_wei")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "cand_li_wei"
        assert body["profile"]["name"] == "李伟"
        assert len(body["skills"]) == 1
        assert body["matches"][0]["matchRate"] == 88.0
        assert body["annotation"] == {"favorite": False, "hrStatus": "", "note": "", "updatedAt": None}

    def test_talent_pool_detail_404(self, client):
        session = _FakeSession({"user_profiles": []})
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/talent-pool/nobody")
        assert resp.status_code == 404

    def test_talent_pool_annotation_put(self, client):
        session = _FakeSession(self._rows())
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.put("/api/enterprise/talent-pool/cand_li_wei/annotation",
                              json={"favorite": True, "hrStatus": "shortlisted", "note": "重点跟进"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["annotation"]["favorite"] is True
        assert body["annotation"]["hrStatus"] == "shortlisted"
        assert body["annotation"]["note"] == "重点跟进"

    def test_talent_pool_annotation_404(self, client):
        session = _FakeSession({"user_profiles": []})
        with patch("app.services.talent_pool_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.put("/api/enterprise/talent-pool/nobody/annotation",
                              json={"favorite": True})
        assert resp.status_code == 404


class TestEnterpriseProfileAPI:
    """企业侧企业资料端点 —— patch enterprise_profile_service.get_session 返回 fake session。"""

    @staticmethod
    def _rows():
        return {
            "enterprise_profiles": [
                EnterpriseProfile(
                    enterprise_id="demo_ent", name="云启智能科技有限公司", short_name="云启智能",
                    logo_emoji="🚀", uscc="91110108MA01KJ7X2P", nature="民营",
                    industry="人工智能 · 企业服务", founded_year=2015, headcount="500-999人",
                    financing="C 轮", city="北京", address="北京市海淀区中关村软件园 9 号楼",
                    website="https://www.yunqi.tech", description="云启智能企业简介",
                    tags=["弹性工作", "六险一金"], tech_stack=["Go", "Python"],
                    hiring_channels=["BOSS 直聘"], hr_name="沈静", hr_title="招聘总监",
                    hr_phone="010-89012345", hr_email="hr@yunqi.tech",
                ),
            ],
        }

    def test_profile_get(self, client):
        session = _FakeSession(self._rows())
        with patch("app.services.enterprise_profile_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert "profile" in body
        p = body["profile"]
        assert p["enterpriseId"] == "demo_ent"
        assert p["name"] == "云启智能科技有限公司"
        assert p["shortName"] == "云启智能"
        assert p["foundedYear"] == 2015
        assert p["techStack"] == ["Go", "Python"]
        assert p["hrName"] == "沈静"

    def test_profile_get_empty_returns_null(self, client):
        session = _FakeSession({"enterprise_profiles": []})
        with patch("app.services.enterprise_profile_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.get("/api/enterprise/profile")
        assert resp.status_code == 200
        assert resp.json() == {"profile": None}

    def test_profile_put_camelcase_roundtrip(self, client):
        session = _FakeSession({"enterprise_profiles": []})
        with patch("app.services.enterprise_profile_service.get_session",
                   new=_make_fake_get_session(session)):
            resp = client.put(
                "/api/enterprise/profile",
                json={"name": "云启智能科技有限公司", "shortName": "云启", "foundedYear": 2015,
                      "techStack": ["Go", "Kubernetes"], "hiringChannels": ["BOSS 直聘"],
                      "hrEmail": "hr@yunqi.tech"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        p = body["profile"]
        assert p["name"] == "云启智能科技有限公司"
        assert p["shortName"] == "云启"
        assert p["foundedYear"] == 2015
        assert p["techStack"] == ["Go", "Kubernetes"]
        assert p["hiringChannels"] == ["BOSS 直聘"]
        assert p["hrEmail"] == "hr@yunqi.tech"

    def test_profile_put_then_get_reflects_update(self, client):
        session = _FakeSession(self._rows())
        with patch("app.services.enterprise_profile_service.get_session",
                   new=_make_fake_get_session(session)):
            put = client.put("/api/enterprise/profile", json={"city": "上海"})
            get = client.get("/api/enterprise/profile")
        assert put.status_code == 200
        body = get.json()["profile"]
        assert body["city"] == "上海"
        assert body["name"] == "云启智能科技有限公司"  # 其他字段未动


class TestAvatarAPI:
    """数字人配置端点 —— 服务端签发 signedUrl，密钥不外发。"""

    def test_no_credentials_returns_configured_false(self, client):
        with patch("app.api.enterprise.get_avatar_config", return_value={"configured": False}):
            resp = client.get("/api/enterprise/avatar/signed-url")
        assert resp.status_code == 200
        assert resp.json() == {"configured": False}

    def test_full_credentials_returns_signed_url(self, client):
        with patch("app.api.enterprise.get_avatar_config", return_value={
            "configured": True,
            "signedUrl": "wss://avatar.cn-huadong-1.xf-yun.com/v1/interact?host=...",
            "appId": "a4d63d4b",
            "sceneId": "332415734762311680",
            "avatarId": "111306001",
            "voiceId": "x4_yezi",
        }):
            resp = client.get("/api/enterprise/avatar/signed-url")
        assert resp.status_code == 200
        body = resp.json()
        assert body["configured"] is True
        assert body["signedUrl"].startswith("wss://avatar.cn-huadong-1.xf-yun.com/")
        assert body["appId"] == "a4d63d4b"
        assert "apiKey" not in body and "apiSecret" not in body
