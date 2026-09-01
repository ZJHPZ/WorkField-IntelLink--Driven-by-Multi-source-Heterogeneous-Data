"""服务层单测 —— 企业侧企业资料（enterprise_profile_service）。

不连 MySQL：用 _FakeSession 按表名分发查询结果（同 test_talent_pool_service 模式）。
"""
import asyncio
from unittest.mock import patch

from app.persistence.zhiyv_models import EnterpriseProfile
from app.services import enterprise_profile_service


# ── fake session（按 enterprise_id 过滤）──

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
    def __init__(self, rows_by_table):
        self._tables = rows_by_table
        self.added = []
        self.committed = False

    async def execute(self, stmt):
        try:
            name = stmt.get_final_froms()[0].name
        except AttributeError:  # 兼容旧版本 SQLAlchemy
            name = stmt.froms[0].name
        rows = [
            row for row in self._tables.get(name, [])
            if _where_matches(stmt.whereclause, row)
        ]
        return _FakeResult(rows)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


def _where_matches(wc, row) -> bool:
    """评估 whereclause 对单行的匹配（= 作用于 enterprise_id 列）。"""
    if wc is None:
        return True
    try:
        from sqlalchemy.sql import operators
        col = wc.left
        op = wc.operator
        right = getattr(wc.right, "value", wc.right)
        rowval = getattr(row, col.key, None)
        if op is operators.eq:
            return rowval == right
    except Exception:
        return True
    return True


def _make_get_session(session):
    async def _gen():
        yield session
    return _gen


def _run(coro):
    return asyncio.run(coro)


# ── 测试数据 ──

def _yunqi():
    return EnterpriseProfile(
        enterprise_id="demo_ent",
        name="云启智能科技有限公司",
        short_name="云启智能",
        logo_emoji="🚀",
        uscc="91110108MA01KJ7X2P",
        nature="民营",
        industry="人工智能 · 企业服务",
        founded_year=2015,
        headcount="500-999人",
        financing="C 轮",
        city="北京",
        address="北京市海淀区中关村软件园 9 号楼",
        website="https://www.yunqi.tech",
        description="云启智能企业简介",
        tags=["弹性工作", "六险一金"],
        tech_stack=["Go", "Python"],
        hiring_channels=["BOSS 直聘"],
        hr_name="沈静",
        hr_title="招聘总监",
        hr_phone="010-89012345",
        hr_email="hr@yunqi.tech",
    )


def _base_rows(**overrides):
    rows = {"enterprise_profiles": []}
    rows.update(overrides)
    return rows


def _patch(session):
    return patch.object(enterprise_profile_service, "get_session", _make_get_session(session))


# ── get_profile ──

class TestGetProfile:
    def test_empty_returns_none(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            profile = _run(enterprise_profile_service.get_profile())
        assert profile is None

    def test_existing_returns_camelcase(self):
        session = _FakeSession(_base_rows(enterprise_profiles=[_yunqi()]))
        with _patch(session):
            profile = _run(enterprise_profile_service.get_profile())
        assert profile is not None
        assert profile["enterpriseId"] == "demo_ent"
        assert profile["name"] == "云启智能科技有限公司"
        assert profile["shortName"] == "云启智能"
        assert profile["foundedYear"] == 2015
        assert profile["techStack"] == ["Go", "Python"]
        assert profile["tags"] == ["弹性工作", "六险一金"]
        assert profile["hiringChannels"] == ["BOSS 直聘"]
        assert profile["hrName"] == "沈静"


# ── upsert_profile ──

class TestUpsertProfile:
    def test_create_new(self):
        session = _FakeSession(_base_rows())
        body = {
            "name": "云启智能科技有限公司", "shortName": "云启智能", "foundedYear": 2015,
            "techStack": ["Go", "Python"], "tags": ["弹性工作"],
            "hiringChannels": ["BOSS 直聘"], "hrName": "沈静", "hrEmail": "hr@yunqi.tech",
        }
        with _patch(session):
            profile = _run(enterprise_profile_service.upsert_profile(body))
        assert profile["name"] == "云启智能科技有限公司"
        assert profile["shortName"] == "云启智能"
        assert profile["foundedYear"] == 2015
        assert profile["techStack"] == ["Go", "Python"]
        assert profile["hiringChannels"] == ["BOSS 直聘"]
        assert profile["hrEmail"] == "hr@yunqi.tech"
        assert session.committed is True
        # 新建了一条 EnterpriseProfile
        assert len(session.added) == 1
        assert isinstance(session.added[0], EnterpriseProfile)

    def test_partial_update_keeps_others(self):
        p = _yunqi()
        session = _FakeSession(_base_rows(enterprise_profiles=[p]))
        with _patch(session):
            profile = _run(enterprise_profile_service.upsert_profile({"shortName": "云启"}))
        assert profile["name"] == "云启智能科技有限公司"  # 未动
        assert profile["shortName"] == "云启"
        assert profile["techStack"] == ["Go", "Python"]  # 未动
        assert profile["foundedYear"] == 2015
        assert session.added == []  # 已存在 → 不新建

    def test_idempotent_single_row(self):
        p = _yunqi()
        session = _FakeSession(_base_rows(enterprise_profiles=[p]))
        with _patch(session):
            _run(enterprise_profile_service.upsert_profile({"city": "北京"}))
            _run(enterprise_profile_service.upsert_profile({"city": "上海"}))
        assert session.added == []
        assert p.city == "上海"

    def test_unknown_keys_ignored(self):
        p = _yunqi()
        session = _FakeSession(_base_rows(enterprise_profiles=[p]))
        with _patch(session):
            profile = _run(enterprise_profile_service.upsert_profile({"garbage": 1, "nonsense": "x"}))
        assert profile["name"] == "云启智能科技有限公司"
        assert not hasattr(p, "garbage")

    def test_none_value_skipped(self):
        p = _yunqi()
        session = _FakeSession(_base_rows(enterprise_profiles=[p]))
        with _patch(session):
            profile = _run(enterprise_profile_service.upsert_profile({"name": None}))
        assert profile["name"] == "云启智能科技有限公司"  # None 不覆盖
