"""服务层单测 —— 企业侧人才库（talent_pool_service）。

不连 MySQL：用 _FakeSession 按表名分发查询结果（同 test_api.py 的 _FakeSession 模式）。
"""
import asyncio
from unittest.mock import patch

from app.persistence.zhiyv_models import (
    UserProfile,
    UserSkill,
    UserMatch,
    TalentPoolEntry,
)
from app.services import talent_pool_service


# ── fake session ──

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
    """execute 按表名分发，并按 WHERE 子句过滤（仅支持 user_id 的 == / != / in_）。

    get_final_froms()[0].name 取表名；whereclause 为 BinaryExpression 时对行做简单过滤，
    使 demo_user 排除、单用户详情等语义与真实 MySQL 一致。
    """

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
    """评估 whereclause 对单行的匹配（= / != / in_ 作用于 user_id 列）。"""
    if wc is None:
        return True
    try:
        col = wc.left
        op = wc.operator
        right = getattr(wc.right, "value", wc.right)
        from sqlalchemy.sql import operators
        rowval = getattr(row, col.key, None)
        if op is operators.eq:
            return rowval == right
        if op is operators.ne:
            return rowval != right
        if op is operators.in_op:
            return rowval in right
    except Exception:
        return True  # 解析不了就当全部命中
    return True


def _make_get_session(session):
    async def _gen():
        yield session
    return _gen


def _run(coro):
    return asyncio.run(coro)


# ── 测试数据 ──

def _demo_profile():
    return UserProfile(user_id="demo_user", name="张明", title="高级前端开发工程师",
                       target_role="前端架构工程师", city="北京", experience_years="5-8年",
                       education="本科", salary_min=25, salary_max=45)


def _li_wei():
    return UserProfile(user_id="cand_li_wei", name="李伟", title="高级后端开发工程师",
                       target_role="资深后端工程师", city="上海", experience_years="8-10年",
                       education="本科", salary_min=35, salary_max=55)


def _wang_fang():
    return UserProfile(user_id="cand_wang_fang", name="王芳", title="AI 算法工程师",
                       target_role="大模型算法工程师", city="北京", experience_years="5-8年",
                       education="硕士", salary_min=40, salary_max=65)


def _li_wei_skills():
    return [
        UserSkill(user_id="cand_li_wei", skill_name="Go", canonical_name="go",
                  category="编程语言", level="expert", freshness=92, years_of_experience=8.0,
                  market_demand=90, status="healthy"),
        UserSkill(user_id="cand_li_wei", skill_name="Kubernetes", canonical_name="kubernetes",
                  category="DevOps", level="advanced", freshness=78, years_of_experience=4.0,
                  market_demand=85, status="healthy"),
    ]


def _li_wei_matches():
    return [
        UserMatch(user_id="cand_li_wei", position_id="pos-go-senior",
                  position_name="资深后端工程师", company="某云原生平台", match_rate=88.0,
                  matched_skills={"Go": 3, "系统设计": 3}, missing_skills={"Rust": 0},
                  salary_range="45-82K"),
        # 存 0.82（0-1 制）也应兼容 → 82.0
        UserMatch(user_id="cand_li_wei", position_id="pos-platform",
                  position_name="平台工程师", company="某互联网大厂", match_rate=0.82,
                  matched_skills={"Go": 3, "Kubernetes": 3}, missing_skills={},
                  salary_range="40-70K"),
    ]


def _base_rows(**overrides):
    rows = {
        "user_profiles": [_demo_profile(), _li_wei(), _wang_fang()],
        "talent_pool_entries": [],
        "user_skills": _li_wei_skills(),
        "user_matches": _li_wei_matches(),
    }
    rows.update(overrides)
    return rows


def _patch(session):
    return patch.object(talent_pool_service, "get_session", _make_get_session(session))


# ── list_candidates ──

class TestListCandidates:
    def test_excludes_demo_user(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates())
        ids = {r["id"] for r in rows}
        assert "demo_user" not in ids
        assert ids == {"cand_li_wei", "cand_wang_fang"}

    def test_empty_db_returns_empty_list(self):
        session = _FakeSession(_base_rows(user_profiles=[]))
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates())
        assert rows == []

    def test_position_filter(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates(position="大模型"))
        assert [r["id"] for r in rows] == ["cand_wang_fang"]

    def test_city_filter(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates(city="上海"))
        assert [r["id"] for r in rows] == ["cand_li_wei"]

    def test_skill_filter_matches_canonical(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates(skill="kubernetes"))
        assert [r["id"] for r in rows] == ["cand_li_wei"]

    def test_favorite_filter(self):
        entry = TalentPoolEntry(user_id="cand_li_wei", favorite=True, hr_status="shortlisted", note="重点跟进")
        session = _FakeSession(_base_rows(talent_pool_entries=[entry]))
        with _patch(session):
            fav = _run(talent_pool_service.list_candidates(favorite=True))
            non = _run(talent_pool_service.list_candidates(favorite=False))
        assert [r["id"] for r in fav] == ["cand_li_wei"]
        assert "cand_li_wei" not in [r["id"] for r in non]

    def test_hr_status_filter(self):
        entry = TalentPoolEntry(user_id="cand_wang_fang", favorite=False, hr_status="interviewing", note="")
        session = _FakeSession(_base_rows(talent_pool_entries=[entry]))
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates(hr_status="interviewing"))
        assert [r["id"] for r in rows] == ["cand_wang_fang"]

    def test_best_match_rate_compat(self):
        """match_rate 存 0.82 或 88.0 都归一百分制，取 max。"""
        session = _FakeSession(_base_rows())
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates())
        li = next(r for r in rows if r["id"] == "cand_li_wei")
        assert li["bestMatchRate"] == 88.0

    def test_top_skills_sorted_by_level(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            rows = _run(talent_pool_service.list_candidates())
        li = next(r for r in rows if r["id"] == "cand_li_wei")
        assert li["topSkills"] == ["Go", "Kubernetes"]  # expert 先于 advanced


# ── get_candidate_detail ──

class TestCandidateDetail:
    def test_detail_shape(self):
        entry = TalentPoolEntry(user_id="cand_li_wei", favorite=True, hr_status="shortlisted", note="重点跟进")
        session = _FakeSession(_base_rows(talent_pool_entries=[entry]))
        with _patch(session):
            detail = _run(talent_pool_service.get_candidate_detail("cand_li_wei"))

        assert detail is not None
        assert detail["id"] == "cand_li_wei"
        assert detail["profile"]["name"] == "李伟"
        assert detail["profile"]["city"] == "上海"
        assert len(detail["skills"]) == 2
        # matched_skills dict → key list
        match = detail["matches"][0]
        assert match["positionName"] == "资深后端工程师"
        assert match["matchRate"] == 88.0
        assert match["matchedSkills"] == ["Go", "系统设计"]
        assert match["missingSkills"] == ["Rust"]
        assert detail["annotation"]["favorite"] is True
        assert detail["annotation"]["hrStatus"] == "shortlisted"
        assert detail["annotation"]["note"] == "重点跟进"

    def test_unknown_user_returns_none(self):
        session = _FakeSession(_base_rows(user_profiles=[]))
        with _patch(session):
            detail = _run(talent_pool_service.get_candidate_detail("nobody"))
        assert detail is None

    def test_no_annotation_returns_defaults(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            detail = _run(talent_pool_service.get_candidate_detail("cand_li_wei"))
        assert detail["annotation"] == {"favorite": False, "hrStatus": "", "note": "", "updatedAt": None}


# ── upsert_annotation ──

class TestUpsertAnnotation:
    def test_create_new(self):
        session = _FakeSession(_base_rows())
        with _patch(session):
            ann = _run(talent_pool_service.upsert_annotation(
                "cand_li_wei", favorite=True, hr_status="shortlisted", note="重点跟进"))
        assert ann["favorite"] is True
        assert ann["hrStatus"] == "shortlisted"
        assert session.committed is True
        # 新建了一条 TalentPoolEntry
        assert len(session.added) == 1
        assert isinstance(session.added[0], TalentPoolEntry)

    def test_partial_update_keeps_others(self):
        entry = TalentPoolEntry(user_id="cand_li_wei", favorite=True, hr_status="", note="")
        session = _FakeSession(_base_rows(talent_pool_entries=[entry]))
        with _patch(session):
            ann = _run(talent_pool_service.upsert_annotation("cand_li_wei", note="只改备注"))
        assert ann["favorite"] is True  # 未动
        assert ann["hrStatus"] == ""
        assert ann["note"] == "只改备注"
        assert session.added == []  # 已存在 → 不新建

    def test_idempotent_no_second_row(self):
        entry = TalentPoolEntry(user_id="cand_li_wei", favorite=False, hr_status="", note="")
        session = _FakeSession(_base_rows(talent_pool_entries=[entry]))
        with _patch(session):
            _run(talent_pool_service.upsert_annotation("cand_li_wei", hr_status="offered"))
            _run(talent_pool_service.upsert_annotation("cand_li_wei", hr_status="offered"))
        assert session.added == []
        assert entry.hr_status == "offered"

    def test_unknown_user_returns_none(self):
        session = _FakeSession(_base_rows(user_profiles=[]))
        with _patch(session):
            ann = _run(talent_pool_service.upsert_annotation("nobody", favorite=True))
        assert ann is None
