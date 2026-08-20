"""简历提取准确率评测 —— Precision / Recall / F1。

赛题要求：简历要素提取准确率 >= 90%。
以 normalized skill name 为匹配单位。

用法:
  python -m app.eval.resume_accuracy --gold data/gold/resume_labeled.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging

from app.pipeline.l2_normalize import normalize_name

logger = logging.getLogger(__name__)


def evaluate(gold_path: str) -> dict:
    """评测简历提取准确率。

    Args:
        gold_path: 金标准 JSONL，每行 {resume_text: str, labels: [str, ...]}

    Returns:
        {precision, recall, f1, tp, fp, fn}
    """
    labeled = _load_gold(gold_path)
    if not labeled:
        logger.error("金标准集为空")
        return {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0}

    from app.services.resume_service import parse_resume_text

    tp = fp = fn = 0
    details = []

    for item in labeled:
        text = item["resume_text"]
        gold_labels = item["labels"]

        # 抽取
        parsed = parse_resume_text(text)
        pred_names = [s["name"] for s in parsed.skills]

        # 归一化
        pred_set = {normalize_name(n) for n in pred_names}
        gold_set = {normalize_name(lb) for lb in gold_labels}

        tp += len(pred_set & gold_set)
        fp += len(pred_set - gold_set)
        fn += len(gold_set - pred_set)

        details.append({
            "resume_id": parsed.resume_id,
            "tp": list(pred_set & gold_set),
            "fp": list(pred_set - gold_set),
            "fn": list(gold_set - pred_set),
        })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn,
        "total_gold": sum(len(item["labels"]) for item in labeled),
        "details": details[:10],
    }


def _load_gold(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description="简历提取准确率评测")
    ap.add_argument("--gold", required=True, help="金标准 JSONL")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)

    result = evaluate(args.gold)
    print(f"\n简历提取准确率:")
    print(f"  Precision: {result['precision']:.2%}")
    print(f"  Recall:    {result['recall']:.2%}")
    print(f"  F1:        {result['f1']:.2%}")
    print(f"  达标(>=90%): {'PASS' if result['f1'] >= 0.9 else 'FAIL'}")


if __name__ == "__main__":
    main()
