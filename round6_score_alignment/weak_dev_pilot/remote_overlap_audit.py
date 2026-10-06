"""Audit whether historical S2 training saw current weak-dev source groups."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


OLD_TRAIN = Path("/home/inspur/aic_video_work/temporal_round5/data/train.jsonl")


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(dev_path: str, out_path: str):
    dev_file = Path(dev_path)
    old, dev = read_jsonl(OLD_TRAIN), read_jsonl(dev_file)
    old_ids = {r["youtube_id"] for r in old}
    old_rows = {r["row_index"] for r in old}
    overlapping = [r for r in dev if r["youtube_id"] in old_ids]
    report = {"old_train_sha256": hashlib.sha256(OLD_TRAIN.read_bytes()).hexdigest(),
              "new_dev_sha256": hashlib.sha256(dev_file.read_bytes()).hexdigest(),
              "old_train_rows": len(old), "new_dev_rows": len(dev),
              "old_train_source_groups": len(old_ids),
              "dev_source_groups_seen_in_old_train": len({r["youtube_id"] for r in overlapping}),
              "dev_rows_with_historical_source_exposure": len(overlapping),
              "dev_rows_with_exact_historical_row_exposure": sum(r["row_index"] in old_rows for r in dev),
              "overlap_video_ids": sorted(r["video_id"] for r in overlapping),
              "interpretation": "Historical S2 metrics on exposed rows are descriptive only, not prospective generalization evidence"}
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "overlap_video_ids"},
                     ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
