"""Strict paired weak-dev decision for the 16-source spatial LoRA smoke run."""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

from weak_metrics import load_jsonl, score_records, summarize


SEED = 20260917
DRAW = 10000


def compare(frames, baseline, candidate):
    def indexed(rows):
        by_key = {r["sample_key"]: r for r in rows}
        if len(by_key) != len(rows):
            raise ValueError("duplicate prediction key")
        return by_key

    old = summarize(score_records(frames, indexed(baseline)))
    new = summarize(score_records(frames, indexed(candidate)))
    old_groups = {g["youtube_id"]: g for g in old["per_source_group"]}
    new_groups = {g["youtube_id"]: g for g in new["per_source_group"]}
    if set(old_groups) != set(new_groups):
        raise ValueError("paired source groups differ")
    diffs = [new_groups[k]["P1_mean"] - old_groups[k]["P1_mean"]
             for k in sorted(old_groups)]
    rng = random.Random(SEED)
    boot = sorted(statistics.mean(diffs[rng.randrange(len(diffs))]
                                  for _ in diffs) for _ in range(DRAW))
    observed = statistics.mean(diffs)
    low, high = boot[int(.025 * DRAW)], boot[int(.975 * DRAW)]
    decision = (observed >= .03 and low > 0 and
                new["P1_valid_rate"] >= old["P1_valid_rate"])
    return {"status": "WEAK_PROXY_SPATIAL_SMOKE_COMPARISON_NOT_OFFICIAL_SCORE",
            "frames": len(frames), "source_groups": len(diffs),
            "base_group_macro_iou": old["P1_source_macro_mean"],
            "smoke_group_macro_iou": new["P1_source_macro_mean"],
            "smoke_minus_base": observed, "paired_ci95": [low, high],
            "base_valid_rate": old["P1_valid_rate"],
            "smoke_valid_rate": new["P1_valid_rate"],
            "bootstrap_seed": SEED, "bootstrap_draws": DRAW,
            "full_training_gate": "PASS" if decision else "STOP_KEEP_BASE",
            "per_source_group": [
                {"youtube_id": key, "base": old_groups[key]["P1_mean"],
                 "smoke": new_groups[key]["P1_mean"],
                 "delta": new_groups[key]["P1_mean"] - old_groups[key]["P1_mean"]}
                for key in sorted(old_groups)]}


def main():
    root = Path(__file__).resolve().parents[2] / "reports" / "round6_score_alignment" / "weak_dev_pilot"
    result = compare(load_jsonl(root / "dev_frames.jsonl"),
                     load_jsonl(root / "p1_predictions.jsonl"),
                     load_jsonl(root / "smoke_adapter_dev_predictions.jsonl"))
    (root / "smoke_adapter_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "per_source_group"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
