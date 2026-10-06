"""Summarize frozen P2-T manifests without opening media."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def summarize(rows: list[dict]) -> dict:
    durations = [r["clip_end_sec"] - r["clip_start_sec"] for r in rows]
    target = [sum(b - a for a, b in r["segments_clip_local"]) for r in rows]
    ratios = [a / b for a, b in zip(target, durations)]
    return {
        "rows": len(rows), "source_groups": len({r["youtube_id"] for r in rows}),
        "clip_duration_mean": statistics.mean(durations),
        "clip_duration_median": statistics.median(durations),
        "truth_duration_mean": statistics.mean(target),
        "truth_duration_median": statistics.median(target),
        "truth_ratio_mean": statistics.mean(ratios),
        "truth_ratio_median": statistics.median(ratios),
        "segment_count_histogram": {str(n): sum(len(r["segments_clip_local"]) == n for r in rows)
                                    for n in sorted({len(r["segments_clip_local"]) for r in rows})},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=Path, required=True)
    ap.add_argument("--dev", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    train, dev = read(args.train), read(args.dev)
    if {r["youtube_id"] for r in train} & {r["youtube_id"] for r in dev}:
        raise RuntimeError("train/dev source leakage")
    args.out.write_text(json.dumps({"train": summarize(train), "dev": summarize(dev)},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
