"""JD 解析准确率评测 —— Precision / Recall / F1。

赛题要求 §4：JD 解析准确率 ≥ 90%。
以规范技能名为匹配单位，先过 L2 normalize_name 消除别名假阴性。

用法：
  python -m app.eval.jd_accuracy --gold data/gold/real_labeled.jsonl --no-spark
  python -m app.eval.jd_accuracy --gold data/gold/synthetic_derived.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """评测结果。"""
    metric: str = "jd_accuracy"
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    total_gold: int = 0
    total_pred: int = 0
    details: list[dict] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []


def evaluate(gold_path: str, use_spark: bool = False, limit: int = 0) -> EvalResult:
    """评测 JD 解析准确率。

    Args:
        gold_path: 金标准 JSONL 路径
        use_spark: 是否使用星火
        limit: 限制评测条数（0=全部）
    """
    # 加载金标准
    labeled = _load_gold(gold_path, limit)
    if not labeled:
        logger.error("金标准集为空")
        return EvalResult()

    # 准备数据
    tp = fp = fn = 0
    details = []

    from app.pipeline.l1_clean import clean as l1_clean
    from app.pipeline.l3_extract import extract as l3_extract
    from app.pipeline.l2_normalize import normalize_name
    from app.domain import JobPosting

    client = None
    if use_spark:
        try:
            from app.utils.spark import SparkClient
            client = SparkClient()
        except Exception as e:
            logger.warning(f"星火不可用，规则兜底: {e}")

    for i, item in enumerate(labeled):
        jd = item["jd"]
        gold_labels = item["labels"]  # list[SkillLabel dict]

        # 跑 pipeline
        cleaned = l1_clean(jd)
        extracted = l3_extract(cleaned, client)

        # 归一化
        pred_set = {normalize_name(s.name) for s in extracted}
        gold_set = {normalize_name(lb["name"]) for lb in gold_labels}

        # 计算 TP/FP/FN
        jd_tp = pred_set & gold_set
        jd_fp = pred_set - gold_set
        jd_fn = gold_set - pred_set

        tp += len(jd_tp)
        fp += len(jd_fp)
        fn += len(jd_fn)

        details.append({
            "jd_id": jd.jd_id,
            "title": jd.title,
            "tp": list(jd_tp),
            "fp": list(jd_fp),
            "fn": list(jd_fn),
        })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    result = EvalResult(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        tp=tp, fp=fp, fn=fn,
        total_gold=sum(len(item["labels"]) for item in labeled),
        total_pred=sum(1 for item in labeled for _ in range(len(item.get("labels", [])))),
        details=details,
    )

    # 修正 total_pred
    result.total_pred = tp + fp

    return result


def _load_gold(path: str, limit: int = 0) -> list[dict]:
    """加载金标准集。"""
    from app.domain import JobPosting, Paragraph, SectionType, SourceType, TechStack

    labeled = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)

            jd_data = d.get("jd", d)
            paragraphs = [
                Paragraph(
                    section=SectionType(p.get("section", "requirement")),
                    text=p.get("text", ""),
                )
                for p in jd_data.get("paragraphs", [])
            ]

            jd = JobPosting(
                jd_id=jd_data.get("jd_id", ""),
                source=SourceType.JD,
                tech_stack=TechStack.AI,
                title=jd_data.get("title", ""),
                posted_date=jd_data.get("posted_date", ""),
                paragraphs=paragraphs,
            )
            labels = d.get("labels", [])
            labeled.append({"jd": jd, "labels": labels})

    return labeled


def main():
    ap = argparse.ArgumentParser(description="JD 解析准确率评测")
    ap.add_argument("--gold", required=True, help="金标准 JSONL 路径")
    ap.add_argument("--no-spark", action="store_true", help="不调星火")
    ap.add_argument("--limit", type=int, default=0, help="限制条数")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    result = evaluate(args.gold, use_spark=not args.no_spark, limit=args.limit)

    print("\n" + "=" * 50)
    print("JD 解析准确率评测")
    print("=" * 50)
    print(f"金标准技能数:  {result.total_gold}")
    print(f"预测技能数:    {result.total_pred}")
    print(f"TP: {result.tp}  FP: {result.fp}  FN: {result.fn}")
    print(f"Precision: {result.precision:.2%}")
    print(f"Recall:    {result.recall:.2%}")
    print(f"F1:        {result.f1:.2%}")
    print(f"达标(≥90%): {'✅' if result.f1 >= 0.9 else '❌'}")

    # 前 5 条明细
    print("\n前 5 条明细:")
    for d in result.details[:5]:
        print(f"  {d['jd_id']} | {d['title']}")
        if d["fp"]:
            print(f"    FP (幻觉): {d['fp']}")
        if d["fn"]:
            print(f"    FN (漏抽): {d['fn']}")


if __name__ == "__main__":
    main()
