"""图谱 Schema + 持久层测试 —— 真实 MySQL + Mock Neo4j"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ══════════════════════════════════════════════
# Graph Schema（无需外部依赖）
# ══════════════════════════════════════════════

class TestGraphSchema:
    def test_all_id_prefixes(self):
        from app.graph.schema import make_id, NodeLabel
        assert make_id(NodeLabel.POSITION, "abc") == "pos::abc"
        assert make_id(NodeLabel.SKILL, "python") == "skill::python"
        assert make_id(NodeLabel.TECH_STACK, "ai") == "stack::ai"
        assert make_id(NodeLabel.EVIDENCE, "1") == "ev::1"

    def test_node_labels_complete(self):
        from app.graph.schema import NodeLabel
        assert len(NodeLabel) >= 7

    def test_rel_types_complete(self):
        from app.graph.schema import RelType
        assert len(RelType) >= 8


# ══════════════════════════════════════════════
# Graph Repository（mock Neo4j 驱动）
# ══════════════════════════════════════════════

class TestGraphRepoMock:
    async def test_upsert_position(self):
        with patch("app.graph.client.run_cypher", new_callable=AsyncMock) as mock_run:
            from app.graph.repository import upsert_position
            from app.domain import Position, PositionType
            pos = Position(position_id="pos::test", name="AI工程师", tech_stack="AI",
                           position_type=PositionType.EMERGING)
            await upsert_position(pos)
            assert mock_run.called

    async def test_upsert_skill(self):
        with patch("app.graph.client.run_cypher", new_callable=AsyncMock) as mock_run:
            from app.graph.repository import upsert_skill
            from app.domain import SkillNode
            await upsert_skill(SkillNode(skill_id="skill::Python", name="Python", confidence=0.9))
            assert mock_run.called

    async def test_link_requires(self):
        with patch("app.graph.client.run_cypher", new_callable=AsyncMock) as mock_run:
            from app.graph.repository import link_requires
            await link_requires("pos::test", "skill::Python", "必备", 0.9)
            assert mock_run.called

    async def test_link_supported_by(self):
        with patch("app.graph.client.run_cypher", new_callable=AsyncMock) as mock_run:
            from app.graph.repository import link_supported_by
            await link_supported_by("skill::Python", "ev::1")
            assert mock_run.called


# ══════════════════════════════════════════════
# Persistence Models（无需外部依赖）
# ══════════════════════════════════════════════

class TestPersistenceModels:
    def test_jd_document_model(self):
        from app.persistence.models import JDDocument
        doc = JDDocument(jd_id="jd-1", title="工程师", source="jd",
                         tech_stack="AI", posted_date="2026-01-01", full_text="Python Django")
        assert doc.jd_id == "jd-1"

    def test_evidence_log_model(self):
        from app.persistence.models import EvidenceLog
        log = EvidenceLog(jd_id="jd-1", skill_name="Python", skill_canonical="Python",
                          evidence_text="熟悉Python", source_type="jd",
                          required_type="必备", extraction_method="rule", gate_verdict="passed")
        assert log.gate_verdict == "passed"

    def test_evolution_changelog_model(self):
        from app.persistence.models import EvolutionChangelog
        log = EvolutionChangelog(position_id="pos::1", position_name="AI工程师",
                                 snapshot_old="s1", snapshot_new="s2",
                                 change_type="added", skill_name="RAG", data_source="market_data")
        assert log.change_type == "added"

    def test_eval_result_model(self):
        from app.persistence.models import EvalResult
        r = EvalResult(metric_name="jd_accuracy", precision=0.92, recall=0.88, f1=0.90)
        assert r.f1 == 0.90


# ══════════════════════════════════════════════
# Persistence 层同步测试
# ══════════════════════════════════════════════

def test_database_url_mysql():
    from app.config import Settings
    s = Settings()
    assert "mysql" in s.database_url
    assert "zhiyu_kg" in s.database_url

def test_database_url_sync_mysql():
    from app.config import Settings
    s = Settings()
    assert "pymysql" in s.database_url_sync

def test_base_metadata():
    from app.persistence.database import Base
    assert Base.metadata is not None

def test_all_model_tablenames():
    from app.persistence.models import JDDocument, EvidenceLog, EvolutionChangelog, EvalResult
    assert JDDocument.__tablename__ == "jd_documents"
    assert EvidenceLog.__tablename__ == "evidence_log"
    assert EvolutionChangelog.__tablename__ == "evolution_changelog"
    assert EvalResult.__tablename__ == "eval_results"

def test_jd_structured_fields():
    from app.persistence.models import JDDocument
    doc = JDDocument(jd_id="x", title="t", source="s", tech_stack="AI",
                     posted_date="2026-01-01", full_text="text",
                     structured_fields={"salary": 30000})
    assert doc.structured_fields == {"salary": 30000}
