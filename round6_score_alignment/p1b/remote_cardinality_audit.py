#!/usr/bin/env python3
"""P1b step 8: read-only audit of the 818-row segment-count constraint.

Checks the historical weak-label rows against one configurable constraint
(the same kind of constraint the P1a prompt/parser share) and reports the
distribution, including the known 7-segment row.  Changes nothing.

Prints JSON to stdout.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

WORK = Path("/home/inspur/aic_video_work")
SPLITS = {"train": WORK / "temporal_round5/data/train.jsonl",
          "dev": WORK / "temporal_round5/data/dev.jsonl",
          "holdout": WORK / "temporal_round5/data/holdout.jsonl"}
MANIFEST = WORK / "temporal_round5/data/split_manifest.json"
CONSTRAINT_MAX = 5
CONSTRAINT_MIN = 0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    out = {"constraint": {"min_segments": CONSTRAINT_MIN, "max_segments": CONSTRAINT_MAX},
           "files": {}, "per_split": {}, "violations": [], "totals": {}}
    histogram = Counter()
    total_rows = 0
    for name, path in SPLITS.items():
        out["files"][name] = {"path": str(path), "sha256": sha256(path)}
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
        local = Counter()
        for row in rows:
            segments = row.get("segments_clip_local")
            n = len(segments) if isinstance(segments, list) else None
            local[str(n)] += 1
            histogram[str(n)] += 1
            total_rows += 1
            problems = []
            if n is None:
                problems.append("segments_clip_local missing or not a list")
            else:
                if not CONSTRAINT_MIN <= n <= CONSTRAINT_MAX:
                    problems.append(f"n_segments {n} outside {CONSTRAINT_MIN}..{CONSTRAINT_MAX}")
                clip_duration = row.get("clip_duration_sec")
                for i, seg in enumerate(segments or []):
                    if not (isinstance(seg, list) and len(seg) == 2):
                        problems.append(f"segment {i} is not a 2-element list")
                        continue
                    a, b = seg
                    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (a, b)):
                        problems.append(f"segment {i} non-numeric")
                        continue
                    if not (math.isfinite(a) and math.isfinite(b)):
                        problems.append(f"segment {i} non-finite")
                        continue
                    if not 0 <= a < b:
                        problems.append(f"segment {i} violates 0 <= start < end")
                    if isinstance(clip_duration, (int, float)) and b > clip_duration + 5e-3:
                        problems.append(f"segment {i} exceeds clip duration")
            if problems:
                out["violations"].append({
                    "split": name, "sample_id": row.get("sample_id"),
                    "video_id": row.get("video_id"), "youtube_id": row.get("youtube_id"),
                    "n_segments": n, "problems": problems,
                    "segments_clip_local": segments,
                    "action": "REPORTED_ONLY_NO_CHANGE",
                })
        out["per_split"][name] = {"rows": len(rows), "histogram": dict(sorted(local.items(),
                                                                             key=lambda kv: int(kv[0])))}
    out["totals"] = {
        "rows": total_rows,
        "histogram": dict(sorted(histogram.items(), key=lambda kv: int(kv[0]))),
        "rows_above_max": sum(v for k, v in histogram.items() if int(k) > CONSTRAINT_MAX),
        "rows_below_min": sum(v for k, v in histogram.items() if int(k) < CONSTRAINT_MIN),
        "distinct_n_segments": sorted(int(k) for k in histogram),
    }
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out["manifest_cross_check"] = {
        "manifest_sha256": sha256(MANIFEST),
        "dataset_sha256": manifest.get("dataset_sha256"),
        "balance_global_n_segments": (manifest.get("balance") or {}).get("global_quantiles", {}).get("n_segments"),
        "counts": manifest.get("counts"),
    }
    out["note"] = ("read-only audit; the violating row(s) are reported and left byte-identical. "
                   "No training label or production config was modified.")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
