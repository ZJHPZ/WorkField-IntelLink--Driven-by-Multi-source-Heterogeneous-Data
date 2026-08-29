"""JD 数据二次加工派生脚本 —— 从 zhiyv.jd_records 派生 T1–T6 表并顺带灌入既有技能表。

依据《JD数据二次加工与展示对接实施计划.md》§5。CLI 模式对齐 load_jd_xls.py。

用法：
    python -m app.services.build_jd_derived --tables profile [--force]   # Phase A：T1+T2+T3
    python -m app.services.build_jd_derived --tables skills  [--force]   # Phase B：T4+T5+T6 + 灌现有表
    python -m app.services.build_jd_derived --tables all     [--force]   # A+B

行为：
- 幂等（D7）：目标表非空且未带 --force 时拒绝执行
- Phase B 默认纯规则抽取（D4），--spark 可选启用星火
- 每 500 行批量 commit；结束打印各表行数
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
import unicodedata
from collections import Counter

logger = logging.getLogger(__name__)

# 月份桶解析（T3，D3：无日期行归入 '00'，不伪造年份）
_FULL_DATE = re.compile(r"(?:19|20)\d{2}[-/](\d{1,2})[-/]\d{1,2}")  # 2025-07-27 / 2025/07/27
_MONTH_CN = re.compile(r"(\d{1,2})月")                              # 5月19日 / 2025年07月28日
_MONTH_NUM = re.compile(r"^(\d{1,2})[-/](\d{1,2})")                # 07-27（无年份）

# T5 category 启发式：title 关键词 → 领域类别（D1 统一 AI 之上的细分）
_CATEGORY_RULES = [
    ("算法", "AI"), ("人工智能", "AI"), ("大模型", "AI"), ("机器学习", "AI"), ("深度学习", "AI"),
    ("数据", "大数据"), ("大数据", "大数据"), ("数仓", "大数据"), ("ETL", "大数据"), ("etl", "大数据"),
    ("嵌入式", "智能系统"), ("智能", "智能系统"), ("驱动", "智能系统"),
    ("物联网", "物联网"), ("iot", "物联网"), ("IOT", "物联网"),
]

_BATCH = 500


def _month_key(raw: str) -> str:
    """从 posted_date_raw 抽月份桶（01–12），无法解析 → '00'。

    顺序：完整日期(YYYY-MM-DD)取月份 → M月D日 → M-D 无年份 → '00'。
    年份锚定避免把 '2025-07-27' 的年份后两位误当月份。
    """
    if not raw:
        return "00"
    m = _FULL_DATE.search(raw)
    if m:
        return m.group(1).zfill(2)
    m = _MONTH_CN.search(raw)
    if m:
        return m.group(1).zfill(2)
    m = _MONTH_NUM.match(raw)
    if m:
        return m.group(1).zfill(2)
    return "00"


def _title_category(title: str) -> str:
    for kw, cat in _CATEGORY_RULES:
        if kw in title:
            return cat
    return "AI"


def _pct(vals: list[int], p: float) -> int | None:
    """线性插值分位数。"""
    if not vals:
        return None
    vals = sorted(vals)
    k = (len(vals) - 1) * p
    lo = int(k)
    hi = min(len(vals) - 1, lo + 1)
    if lo == hi:
        return vals[lo]
    return round(vals[lo] + (vals[hi] - vals[lo]) * (k - lo))


def _median(vals: list[int]) -> int | None:
    if not vals:
        return None
    vals = sorted(vals)
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    return round((vals[mid - 1] + vals[mid]) / 2)


def _level_from_confidence(conf: float) -> str:
    """口径与 app/api/enterprise.py::_level_from_confidence 保持一致。"""
    if conf >= 0.8:
        return "expert"
    elif conf >= 0.6:
        return "advanced"
    elif conf >= 0.4:
        return "intermediate"
    return "basic"


_PRESERVE_CASE: set[str] | None = None


def _strip_invisible(s: str) -> str:
    """剥离 Unicode Cf（格式控制：零宽连接符/软连字符等）与 Cc（控制）字符。

    原因：utf8mb4_0900_ai_ci 把零宽字符视为等权，'\\u200ccad' 与 'cad' 在 MySQL
    主键上撞车，但在 Python 里是两个字符串。
    """
    return "".join(ch for ch in s if unicodedata.category(ch) not in ("Cf", "Cc"))


def _fold(name: str) -> str:
    """折叠技能名，使 Python 键与 MySQL 主键 collation 判定一致。

    - NFKC：全角（3）→半角(3)、全角数字/空格→半角（0900_ai_ci 视全半角相等）
    - 剥离 Cf/Cc 不可见字符（零宽字符在 0900_ai_ci 中视为等权）
    - SKILL_ALIASES 输出（C++/Kubernetes/Go…）保留原样（别名映射已去重大小写）
    - 其余 ASCII 大写字母小写化（0900_ai_ci 大小写不敏感，ORACLE/oracle 会撞主键）
    """
    global _PRESERVE_CASE
    if _PRESERVE_CASE is None:
        from app.pipeline.l2_normalize import SKILL_ALIASES
        _PRESERVE_CASE = set(SKILL_ALIASES.values())
    n = _strip_invisible(unicodedata.normalize("NFKC", name))
    if n in _PRESERVE_CASE:
        return n
    return re.sub(r"[A-Z]", lambda m: m.group(0).lower(), n)


def _clip(s: str, n: int) -> str:
    """截断超长字符串，避免列宽溢出（skill_name String(128) / title String(256)）。"""
    return s if len(s) <= n else s[:n]


# 纯规则抽取噪声过滤（D4 已知副产物：JD 福利/营销文案句子碎片被当技能名）
_JUNK_MARKERS = (
    "有无经验均可", "高人一等", "奋斗者", "值得为之奋斗", "有充实",
    "优先", "及以上", "以上的", "等条件", "的能力", "较强", "良好",
    # 福利/晋升/氛围类营销碎片
    "充实", "晋升机会", "生日会", "五险一金", "团建", "下午茶",
    "并进行", "并有", "并使用", "扎实的", "初步的", "一定的", "较好的",
)


def _is_junk(name: str) -> bool:
    """是否为明显非技能（句子碎片/营销文案）。真实原子技能名一般 ≤16 字且为名词。"""
    if not name:
        return True
    if len(name) > 16:
        return True
    # marker 优先（短词如「有充实」先命中「充实」），再查「有X」句式碎片
    if any(j in name for j in _JUNK_MARKERS):
        return True
    if name.startswith("有") and len(name) >= 5:
        return True
    return False


async def _table_nonempty(session, models: list) -> list[str]:
    """返回非空的目标表名列表。"""
    from sqlalchemy import func, select

    non_empty = []
    for m in models:
        cnt = (await session.execute(select(func.count()).select_from(m))).scalar()
        if cnt:
            non_empty.append(m.__tablename__)
    return non_empty


async def _truncate_and_insert(session, model, rows: list) -> None:
    """TRUNCATE 后按批写入。rows 为空则跳过。"""
    from sqlalchemy import text

    if not rows:
        return
    await session.execute(text(f"TRUNCATE TABLE {model.__tablename__}"))
    await session.commit()
    for i in range(0, len(rows), _BATCH):
        session.add_all(rows[i:i + _BATCH])
        await session.commit()


# ══════════════════════════════════════════════
# Phase A：T1/T2/T3 纯 SQL 聚合（读全量在内存聚合）
# ══════════════════════════════════════════════

async def _build_profile(session, force: bool) -> None:
    from sqlalchemy import select

    from app.persistence.zhiyv_models import (
        JDPositionCitySalary,
        JDPositionEvolution,
        JDPositionProfile,
        JDRecord,
    )

    if not force:
        non_empty = await _table_nonempty(
            session, [JDPositionProfile, JDPositionCitySalary, JDPositionEvolution]
        )
        if non_empty:
            raise SystemExit(f"Phase A 目标表非空 {non_empty}；如需重建请加 --force")

    rows = (await session.execute(select(JDRecord))).scalars().all()
    print(f"[Phase A] 读取 jd_records {len(rows)} 行")

    by_title: dict[str, list] = {}
    for r in rows:
        by_title.setdefault(r.title, []).append(r)

    profiles: list[JDPositionProfile] = []
    city_rows: list[JDPositionCitySalary] = []
    evo_rows: list[JDPositionEvolution] = []

    for title, recs in by_title.items():
        # D2：薪资分位只统计 salary_unit='月' 且 min/max 均非空的行
        month_rows = [r for r in recs
                      if r.salary_unit == "月" and r.salary_min is not None and r.salary_max is not None]
        smin = [r.salary_min for r in month_rows]
        smax = [r.salary_max for r in month_rows]
        unit_counter = Counter(r.salary_unit for r in recs)
        dominant = unit_counter.most_common(1)[0][0] if unit_counter else ""
        dates = [r.posted_date for r in recs if r.posted_date]

        # T1 岗位画像
        profiles.append(JDPositionProfile(
            title=title,
            jd_count=len(recs),
            salary_unit=dominant,
            salary_min_p25=_pct(smin, 0.25), salary_min_p50=_pct(smin, 0.50), salary_min_p75=_pct(smin, 0.75),
            salary_max_p25=_pct(smax, 0.25), salary_max_p50=_pct(smax, 0.50), salary_max_p75=_pct(smax, 0.75),
            salary_cover_rate=round(len(month_rows) / len(recs), 4) if recs else 0.0,
            top_cities=[{"city": c, "count": n} for c, n
                        in Counter(r.city for r in recs if r.city).most_common(5)],
            top_companies=[{"company_name": c, "count": n} for c, n
                           in Counter(r.company_name for r in recs if r.company_name).most_common(5)],
            industry_dist=[{"industry": i, "count": n} for i, n
                           in Counter(r.industry for r in recs if r.industry).most_common()],
            size_dist=[{"company_size": s, "count": n} for s, n
                       in Counter(r.company_size for r in recs if r.company_size).most_common()],
            type_dist=[{"company_type": t, "count": n} for t, n
                       in Counter(r.company_type for r in recs if r.company_type).most_common()],
            latest_posted=max(dates) if dates else None,
        ))

        # T2 岗位×城市
        by_city: dict[str, list] = {}
        for r in recs:
            if r.city:
                by_city.setdefault(r.city, []).append(r)
        for city, crecs in by_city.items():
            cmonth = [r for r in crecs
                      if r.salary_unit == "月" and r.salary_min is not None and r.salary_max is not None]
            cunit = Counter(r.salary_unit for r in crecs).most_common(1)[0][0] if crecs else ""
            city_rows.append(JDPositionCitySalary(
                title=title, city=city, jd_count=len(crecs),
                salary_min_median=_median([r.salary_min for r in cmonth]),
                salary_max_median=_median([r.salary_max for r in cmonth]),
                salary_unit=cunit,
            ))

        # T3 岗位演化月桶（D3：月份桶 01–12，无日期 → 00）
        by_month: dict[str, list] = {}
        for r in recs:
            by_month.setdefault(_month_key(r.posted_date_raw), []).append(r)
        for mk, mrecs in by_month.items():
            mmonth = [r for r in mrecs
                      if r.salary_unit == "月" and r.salary_min is not None and r.salary_max is not None]
            munit = Counter(r.salary_unit for r in mrecs).most_common(1)[0][0] if mrecs else ""
            evo_rows.append(JDPositionEvolution(
                title=title, month_key=mk, jd_count=len(mrecs),
                salary_min_median=_median([r.salary_min for r in mmonth]),
                salary_max_median=_median([r.salary_max for r in mmonth]),
                salary_unit=munit,
            ))

    await _truncate_and_insert(session, JDPositionProfile, profiles)
    await _truncate_and_insert(session, JDPositionCitySalary, city_rows)
    await _truncate_and_insert(session, JDPositionEvolution, evo_rows)
    print(f"[Phase A] T1 岗位画像 {len(profiles)} 行 / "
          f"T2 城市薪资 {len(city_rows)} 行 / T3 演化月桶 {len(evo_rows)} 行")


# ══════════════════════════════════════════════
# Phase B：T4/T5/T6 + 灌现有表（管线抽取，逐 JD 处理）
# ══════════════════════════════════════════════

async def _build_skills(session, force: bool, use_spark: bool) -> None:
    from sqlalchemy import select

    from app.domain import JobPosting, Paragraph, SectionType, SourceType, TechStack
    from app.persistence.zhiyv_models import (
        JDQualityDiagnosis,
        JDRecord,
        JDPositionSkill,
        JDSkillSignal,
        SkillCooccurrence,
        SkillStat,
        VerifiedSkill,
    )
    from app.pipeline.l1_clean import clean
    from app.pipeline.l2_cooccurrence import build_cooccurrence
    from app.pipeline.l2_normalize import normalize_and_count, normalize_name
    from app.pipeline.l3_extract import extract
    from app.pipeline.l3_verify import verify
    from app.services.enterprise_service import diagnose_jd

    targets = [
        JDPositionSkill, JDSkillSignal, JDQualityDiagnosis,
        VerifiedSkill, SkillStat, SkillCooccurrence,
    ]
    if not force:
        non_empty = await _table_nonempty(session, targets)
        if non_empty:
            raise SystemExit(f"Phase B 目标表非空 {non_empty}；如需重建请加 --force")

    client = None
    if use_spark:
        try:
            from app.utils.spark import SparkClient
            client = SparkClient()
            print("[Phase B] 星火客户端就绪")
        except Exception as e:
            print(f"[Phase B] 星火不可用，纯规则兜底: {e}")

    rows = (await session.execute(select(JDRecord))).scalars().all()
    total = len(rows)
    print(f"[Phase B] 读取 jd_records {total} 行")

    extracted_by_jd: list[tuple[str, str, list]] = []
    verified_rows: list[VerifiedSkill] = []
    jd_skills_list: list[tuple[str, list[str]]] = []
    diagnosis_rows: list[JDQualityDiagnosis] = []
    skill_jd_ids: dict[str, set[str]] = {}
    skill_req_counter: dict[str, Counter] = {}
    skill_conf_vals: dict[str, list[float]] = {}
    category_counter: dict[str, Counter] = {}
    title_jd_count: Counter = Counter()
    title_skill_count: dict[tuple[str, str], int] = {}

    skipped_empty = 0
    for idx, r in enumerate(rows, 1):
        if not r.jd_text:
            skipped_empty += 1
            continue
        # D3：无完整日期时合成 '2026-{MM}-01'，仅供管线字段非空，不参与时间指标
        posted = r.posted_date.strftime("%Y-%m-%d") if r.posted_date \
            else f"2026-{_month_key(r.posted_date_raw)}-01"
        jd = JobPosting(
            jd_id=r.jd_id,
            source=SourceType.JD,
            tech_stack=TechStack.AI,
            title=r.title,
            posted_date=posted,
            paragraphs=[Paragraph(SectionType.REQUIREMENT, r.jd_text)],
            salary_min=r.salary_min,
            salary_max=r.salary_max,
            city=r.city or "",
        )
        try:
            cleaned = clean(jd)
            skills = extract(cleaned, client)
            gate = verify(r.jd_id, jd.full_text(), skills)
            skills = gate.passed
        except Exception as e:
            logger.warning(f"JD {r.jd_id} 抽取失败: {e}")
            continue

        # 噪声过滤（句子碎片/营销文案不是技能），T4/T5/T6/既有表全链路保持一致
        kept: list = []
        for s in skills:
            canon = _clip(_fold(normalize_name(s.name)), 128)
            if len(canon) >= 2 and not _is_junk(canon):
                kept.append(s)
        skills = kept

        extracted_by_jd.append((r.jd_id, TechStack.AI.value, skills))
        title_jd_count[r.title] += 1

        cat = _title_category(r.title)
        canon_names: list[str] = []
        seen: set[str] = set()
        for s in skills:
            canon = _clip(_fold(normalize_name(s.name)), 128)
            if canon in seen:
                continue
            seen.add(canon)
            canon_names.append(canon)
            verified_rows.append(VerifiedSkill(
                jd_id=r.jd_id, jd_title=_clip(r.title, 256), skill_name=canon,
                tech_stack=TechStack.AI.value,
                required_type=s.required_type,
                evidence=(s.evidence or "")[:500],
                source=s.source,
            ))
            skill_jd_ids.setdefault(canon, set()).add(r.jd_id)
            skill_req_counter.setdefault(canon, Counter())[s.required_type] += 1
            skill_conf_vals.setdefault(canon, []).append(s.confidence)
            category_counter.setdefault(canon, Counter())[cat] += 1
            title_skill_count[(r.title, canon)] = title_skill_count.get((r.title, canon), 0) + 1

        jd_skills_list.append((r.jd_id, canon_names))

        # T6 质量诊断（复用 diagnose_jd，公式见计划 §4 T6）
        diag = diagnose_jd(r.jd_id, r.title,
                           [{"name": s.name, "required_type": s.required_type, "source": s.source}
                            for s in skills])
        score = round(max(0, 100 - diag.inflation_index * 60 - (1 - diag.required_ratio) * 40))
        status = "healthy" if score >= 80 else "warning" if score >= 60 else "critical"
        diagnosis_rows.append(JDQualityDiagnosis(
            jd_id=r.jd_id, title=r.title,
            skill_count=diag.skill_count,
            inflation_index=diag.inflation_index,
            inflated_items=diag.inflated_items,
            soft_skill_ratio=diag.soft_skill_ratio,
            required_ratio=diag.required_ratio,
            suggestions=diag.suggestions,
            overall_score=score, status=status,
        ))

        if idx % 500 == 0:
            print(f"  [{idx}/{total}] 已处理，空 jd_text 跳过 {skipped_empty}")

    print(f"[Phase B] 完成抽取：{len(extracted_by_jd)} 条 JD / "
          f"{len(verified_rows)} 条技能记录 / 空 jd_text 跳过 {skipped_empty}")

    # ── 灌既有表 verified_skills ──
    await _truncate_and_insert(session, VerifiedSkill, verified_rows)

    # ── 灌既有表 skill_stats（D3：时间序列指标一律 0）──
    # normalize_and_count 的键未折叠大小写（ORACLE/oracle 是两键），MySQL 主键
    # 大小写不敏感 → 先按 _fold 合并再落库。
    from dataclasses import replace as _dc_replace
    raw_stats = normalize_and_count(extracted_by_jd)
    merged_stats: dict[str, SkillStat] = {}
    for name, st in raw_stats.items():
        k = _clip(_fold(name), 128)
        if k not in merged_stats:
            merged_stats[k] = _dc_replace(st, name=k)
        else:
            base = merged_stats[k]
            base.df += st.df
            base.required_count += st.required_count
            base.bonus_count += st.bonus_count
            base.tech_stacks += st.tech_stacks
            base.confidence = max(base.confidence, st.confidence)
            base.verification_status = (
                "confirmed" if base.verification_status == "confirmed"
                or st.verification_status == "confirmed"
                else "candidate" if base.verification_status == "candidate"
                or st.verification_status == "candidate"
                else "unverified"
            )
    stats = merged_stats

    stat_rows: list[SkillStat] = []
    for name, st in stats.items():
        jd_ids = sorted(skill_jd_ids.get(name, set()))
        stat_rows.append(SkillStat(
            skill_name=name, df=st.df,
            jd_ids=jd_ids,
            required_count=st.required_count, bonus_count=st.bonus_count,
            tech_stacks=st.tech_stacks,
            source_weights={"jd": st.df},
            source_evidences=jd_ids[:5],
            first_seen_months_ago=0,
            avg_inflation=0.0,
            confidence=st.confidence,
            source_score=st.source_score,
            status="confirmed" if st.verification_status == "confirmed" else "candidate",
            verification_status=st.verification_status,
            emergence=0.0, decline=0.0, volatility=0.0,
            half_life=None, half_life_method="",
            evolution_speed=0.0, inflation_index=0.0,
        ))
    await _truncate_and_insert(session, SkillStat, stat_rows)

    # ── 灌既有表 skill_cooccurrence ──
    cooc = build_cooccurrence(jd_skills_list)
    cooc_rows: list[SkillCooccurrence] = []
    for (a, b), cnt in cooc.cooccurrences.items():
        cooc_rows.append(SkillCooccurrence(
            skill_a=a, skill_b=b, count=cnt,
            strength=round(cooc.get_strength(a, b), 4),
        ))
    await _truncate_and_insert(session, SkillCooccurrence, cooc_rows)

    # ── T4 岗位×技能权重 ──
    t4_rows: list[JDPositionSkill] = []
    for (title, skill), cnt in title_skill_count.items():
        tjd = title_jd_count.get(title, 1)
        req_c = skill_req_counter.get(skill, Counter())
        rtype = "必备" if req_c.get("必备", 0) >= req_c.get("加分", 0) else "加分"
        confs = skill_conf_vals.get(skill, [1.0])
        avg_conf = sum(confs) / len(confs)
        t4_rows.append(JDPositionSkill(
            title=title, skill_name=skill,
            jd_count=cnt,
            weight=round(cnt / tjd, 4),
            required_type=rtype,
            level=_level_from_confidence(avg_conf),
            confidence=round(avg_conf, 4),
        ))
    await _truncate_and_insert(session, JDPositionSkill, t4_rows)

    # ── T5 技能信号（jd 源，D5）──
    max_df = max(st.df for st in stats.values()) if stats else 1
    t5_rows: list[JDSkillSignal] = []
    for name, st in stats.items():
        jd_ids = sorted(skill_jd_ids.get(name, set()))
        cat_counter = category_counter.get(name, Counter())
        cat = cat_counter.most_common(1)[0][0] if cat_counter else "AI"
        vstatus = "confirmed" if st.df >= 10 else "candidate" if st.df >= 3 else "unverified"
        t5_rows.append(JDSkillSignal(
            skill_name=name, category=cat,
            jd_frequency=st.df,
            jd_confidence=round(st.df / max_df, 4),
            jd_examples=jd_ids[:3],
            verification_status=vstatus,
        ))
    await _truncate_and_insert(session, JDSkillSignal, t5_rows)

    # ── T6 JD 质量诊断 ──
    await _truncate_and_insert(session, JDQualityDiagnosis, diagnosis_rows)

    print(f"[Phase B] verified_skills {len(verified_rows)} / skill_stats {len(stat_rows)} / "
          f"cooccurrence {len(cooc_rows)} / T4 {len(t4_rows)} / T5 {len(t5_rows)} / T6 {len(diagnosis_rows)}")


# ══════════════════════════════════════════════
# CLI 入口（对齐 pipeline_service / load_jd_xls）
# ══════════════════════════════════════════════

async def _run(tables: list[str], force: bool, use_spark: bool) -> None:
    from app.config import get_settings
    from app.persistence.database import close_db, get_session, init_db

    settings = get_settings()
    await init_db(settings)
    try:
        async for session in get_session():
            if "profile" in tables:
                await _build_profile(session, force)
            if "skills" in tables:
                await _build_skills(session, force, use_spark)
    finally:
        await close_db()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="从 zhiyv.jd_records 派生 T1–T6 表并灌入既有技能表（计划 §5）"
    )
    parser.add_argument(
        "--tables", choices=["profile", "skills", "all"], default="all",
        help="profile=Phase A(T1+T2+T3) / skills=Phase B(T4+T5+T6+灌表) / all=A+B",
    )
    parser.add_argument("--force", action="store_true", help="清空目标表后重建（D7）")
    parser.add_argument("--spark", action="store_true", help="Phase B 启用星火 LLM 抽取（默认纯规则，D4）")
    args = parser.parse_args()

    tables = ["profile", "skills"] if args.tables == "all" else [args.tables]
    asyncio.run(_run(tables, force=args.force, use_spark=args.spark))


if __name__ == "__main__":
    main()
