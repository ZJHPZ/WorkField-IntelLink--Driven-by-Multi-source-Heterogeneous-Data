"""智联招聘 JD 采样数据摄取脚本 —— 将 .xls 导入 MySQL zhiyv.jd_records 表。

用法：
    python -m app.services.load_jd_xls [--xls <path>] [--force]

行为：
- 默认 --xls 指向仓库根目录下 a13*JD采样数据.xls（如已改位置请显式传入）
- 按岗位编码 (jd_id) 去重，保留首次出现，跳过后续重复行
- --force 先清空 jd_records 再重载（表非空且未带 --force 时拒绝执行）
- 输出入库行数、去重跳过数、各字段空值计数
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 薪资区间：数字-数字 / 数字~数字；单值兜底
_SALARY_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[-~—]\s*(\d+(?:\.\d+)?)")
_SALARY_SINGLE_RE = re.compile(r"(\d+(?:\.\d+)?)")

# xls 表头名 → JDRecord 字段名（原始列）
_HEADER_MAP = {
    "岗位名称": "title",
    "地址": "location",
    "薪资范围": "salary_raw",
    "公司名称": "company_name",
    "所属行业": "industry",
    "公司规模": "company_size",
    "公司类型": "company_type",
    "岗位编码": "jd_id",
    "岗位详情": "jd_text",
    "更新日期": "posted_date_raw",
    "公司详情": "company_desc",
    "岗位来源地址": "source_url",
}


def _clean_html(text: str) -> str:
    """把 HTML <br> 转成换行，压缩空白。"""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = text.replace("\r", "")
    return text.strip()


def _split_location(location: str) -> tuple[str | None, str | None]:
    """地址 '城市-区县' → (city, district)，清理 'None'。"""
    if not location:
        return None, None
    parts = [p.strip() for p in location.split("-")]
    city = parts[0] or None
    district = None
    if len(parts) > 1 and parts[1] and parts[1] != "None":
        district = parts[1]
    return city, district


def _parse_salary(raw: str) -> tuple[int | None, int | None, str]:
    """解析薪资原文 → (salary_min, salary_max, salary_unit)。

    单位统一换算成元：万 ×10000；元/天、元/时 保留原值并标注单位；面议返回 None。
    """
    if not raw:
        return None, None, ""
    raw = raw.strip()
    if not raw or "面议" in raw or "薪酬" in raw:
        return None, None, "面议"
    unit = "月"
    if "元/天" in raw:
        unit = "天"
    elif "元/时" in raw:
        unit = "时"
    mult = 10000 if "万" in raw else 1
    m = _SALARY_RANGE_RE.search(raw)
    if m:
        lo, hi = float(m.group(1)) * mult, float(m.group(2)) * mult
        return int(round(lo)), int(round(hi)), unit
    m = _SALARY_SINGLE_RE.search(raw)
    if m:
        v = int(round(float(m.group(1)) * mult))
        return v, v, unit
    return None, None, unit


def _parse_date(raw: str) -> date | None:
    """仅解析完整时间戳（如 2025-07-27 00:24:24）；无年份的 'M月D日' 返回 None。"""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _read_xls(path: str) -> tuple[list[dict], int]:
    """用 xlrd 读 .xls，返回 (原始行列表, 总行数)。原始行以 JDRecord 字段名作 key。"""
    import xlrd

    book = xlrd.open_workbook(path)
    sh = book.sheet_by_index(0)

    # 表头 → 列号（按表头名映射，列序变化也能容错）
    col_idx: dict[str, int] = {}
    for c in range(sh.ncols):
        name = str(sh.cell_value(0, c)).strip()
        if name in _HEADER_MAP:
            col_idx[_HEADER_MAP[name]] = c

    missing = set(_HEADER_MAP.values()) - set(col_idx)
    if missing:
        raise SystemExit(f"xls 表头不完整，缺少字段: {sorted(missing)}")

    rows: list[dict] = []
    for r in range(1, sh.nrows):
        rec: dict = {}
        for field, c in col_idx.items():
            v = sh.cell_value(r, c)
            rec[field] = v if isinstance(v, str) else str(v)
        rows.append(rec)
    return rows, sh.nrows - 1


def _normalize(rec: dict) -> dict:
    """单行归一化 → 可直接构造 JDRecord 的 kwargs。"""
    # 个别行岗位编码后附查询参数（如 ?jobSourceType=2&...），取 '?' 前主体
    jd_id = re.split(r"[?&]", rec["jd_id"])[0].strip()
    title = rec["title"].strip()
    location = rec["location"].strip()
    salary_raw = rec["salary_raw"].strip()
    company_name = rec["company_name"].strip()
    industry = rec["industry"].strip()
    company_size = rec["company_size"].strip()
    company_type = rec["company_type"].strip()
    jd_text = _clean_html(rec["jd_text"])
    posted_raw = rec["posted_date_raw"].strip()
    company_desc = _clean_html(rec["company_desc"])
    source_url = rec["source_url"].strip()

    city, district = _split_location(location)
    salary_min, salary_max, salary_unit = _parse_salary(salary_raw)

    return {
        "jd_id": jd_id,
        "title": title,
        "location": location,
        "city": city,
        "district": district,
        "salary_raw": salary_raw,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_unit": salary_unit,
        "company_name": company_name,
        "industry": industry,
        "company_size": company_size,
        "company_type": company_type,
        "jd_text": jd_text or None,
        "posted_date_raw": posted_raw,
        "posted_date": _parse_date(posted_raw),
        "company_desc": company_desc or None,
        "source_url": source_url,
        "source": "zhaopin",
    }


async def _load(records: list[dict], force: bool) -> tuple[int, int]:
    """去重并批量写入 jd_records，返回 (入库行数, 跳过重复数)。"""
    from sqlalchemy import func, select, text

    from app.config import get_settings
    from app.persistence.database import close_db, get_session, init_db
    from app.persistence.zhiyv_models import JDRecord

    settings = get_settings()
    await init_db(settings)
    try:
        async for session in get_session():
            if not force:
                existing = (
                    await session.execute(select(func.count()).select_from(JDRecord))
                ).scalar()
                if existing:
                    raise SystemExit(
                        f"jd_records 已存在 {existing} 行；如需重载请加 --force"
                    )
            else:
                await session.execute(text("TRUNCATE TABLE jd_records"))
                await session.commit()

            seen: set[str] = set()
            skipped = 0
            loaded = 0
            batch: list[JDRecord] = []
            for rec in records:
                jd_id = rec["jd_id"]
                if not jd_id or jd_id in seen:
                    skipped += 1
                    continue
                seen.add(jd_id)
                batch.append(JDRecord(**rec))
                if len(batch) >= 500:
                    session.add_all(batch)
                    await session.commit()
                    loaded += len(batch)
                    batch = []
            if batch:
                session.add_all(batch)
                await session.commit()
                loaded += len(batch)
            return loaded, skipped
    finally:
        await close_db()


def _summary(records: list[dict], loaded: int, skipped: int) -> None:
    """打印入库摘要与字段空值计数（基于源数据）。"""
    from collections import Counter

    null_fields = ("jd_text", "company_desc", "company_type", "company_size", "industry", "city", "salary_unit")
    empties = Counter()
    for rec in records:
        for f in null_fields:
            v = rec.get(f)
            if v is None or (isinstance(v, str) and not v.strip()):
                empties[f] += 1

    print("=" * 50)
    print("JD 数据摄取摘要")
    print("=" * 50)
    print(f"源数据行数:     {len(records)}")
    print(f"入库行数:       {loaded}  (按岗位编码去重)")
    print(f"跳过重复/空:    {skipped}")
    for f in null_fields:
        print(f"  空值 {f:<14} {empties[f]}")
    print("[OK] jd_records 已就绪")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="导入智联招聘 JD 采样数据到 zhiyv.jd_records")
    parser.add_argument(
        "--xls",
        type=str,
        default="",
        help="xls 文件路径（默认自动查找仓库根目录 a13*JD采样数据.xls）",
    )
    parser.add_argument("--force", action="store_true", help="清空 jd_records 后重载")
    args = parser.parse_args()

    xls_path = args.xls
    if not xls_path:
        candidates = sorted(Path(__file__).resolve().parents[3].glob("a13*JD采样数据.xls"))
        if not candidates:
            raise SystemExit("未找到默认 xls 文件，请用 --xls 指定路径")
        xls_path = str(candidates[0])

    raw_records, total = _read_xls(xls_path)
    records = [_normalize(r) for r in raw_records]
    print(f"读取 {total} 行自 {xls_path}")

    loaded, skipped = asyncio.run(_load(records, force=args.force))
    _summary(records, loaded, skipped)


if __name__ == "__main__":
    main()
