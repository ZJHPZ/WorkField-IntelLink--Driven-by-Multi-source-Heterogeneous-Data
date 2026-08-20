"""匹配准确率评测。

赛题要求：匹配准确率 >= 90%。
以专家标注的 match_level (高/中/低) 为金标准，验证系统匹配率是否一致。

用法:
  python -m app.eval.match_accuracy --gold data/gold/match_labeled.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging

from app.services.match_service import match_skills

logger = logging.getLogger(__name__)


def evaluate(gold_path: str) -> dict:
    """评测匹配准确率。

    Args:
        gold_path: JSONL, 每行 {user_skills: [...], position_skills: [...],
                  gold_match_level: "high"|"medium"|"low"}

    Returns:
        准确率统计
    """
    labeled = _load_gold(gold_path)
    if not labeled:
        logger.error("金标准集为空")
        return {"accuracy": 0, "correct": 0, "total": 0}

    def system_level(rate: float) -> str:
        if rate >= 0.7: return "high"
        if rate >= 0.4: return "medium"
        return "low"

    correct = 0
    details = []

    for item in labeled:
        result = match_skills(
            item["user_skills"],
            item["position_skills"],
            position_name=item.get("position_name", ""),
        )
        pred_level = system_level(result.match_rate)
        gold_level = item.get("gold_match_level", "high")

        is_correct = pred_level == gold_level
        if is_correct:
            correct += 1

        details.append({
            "match_rate": result.match_rate,
            "system_level": pred_level,
            "gold_level": gold_level,
            "correct": is_correct,
        })

    total = len(labeled)
    return {
        "accuracy": round(correct / total, 4) if total > 0 else 0,
        "correct": correct,
        "total": total,
        "details": details[:10],
    }


def _load_gold(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description="匹配准确率评测")
    ap.add_argument("--gold", required=True, help="金标准 JSONL")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)

    result = evaluate(args.gold)
    print(f"\n匹配准确率:")
    print(f"  Accuracy: {result['accuracy']:.2%}")
    print(f"  Correct:  {result['correct']}/{result['total']}")
    print(f"  达标(>=90%): {'PASS' if result['accuracy'] >= 0.9 else 'FAIL'}")


if __name__ == "__main__":
    main()
