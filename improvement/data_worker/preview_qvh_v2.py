#!/usr/bin/env python3
"""Create three media-verified dev rows for interface integration."""

from pathlib import Path
import json

import build_qvh_v2 as qvh


SOURCE = Path("/home/inspur/aic_video_work/data_qvh_v2/source")
VIDEOS = Path("/home/inspur/aic_video_data/videos")
OUTPUT = Path("/home/inspur/aic_video_work/data_qvh_v2/preview_3_dev.jsonl")

train = qvh.load_jsonl(SOURCE / "highlight_train_release.jsonl")
val = qvh.load_jsonl(SOURCE / "highlight_val_release.jsonl")
cross = {qvh.source_group(row["vid"]) for row in train} & {qvh.source_group(row["vid"]) for row in val}
eligible = [
    row
    for row in val
    if qvh.source_group(row["vid"]) not in cross
    and not qvh.annotation_errors(row)
    and qvh.video_path_for(VIDEOS, row["vid"]).is_file()
]
dev, _ = qvh.partition_val_groups(eligible, qvh.SEED)
verified, rejected = qvh.select_verified(dev, 3, VIDEOS, {}, 3)
rows = [qvh.training_row(row, media, "dev", trusted=False) for row, media in verified]
qvh.write_jsonl(OUTPUT, rows)
print(json.dumps({
    "path": str(OUTPUT),
    "count": len(rows),
    "cross_boundary_groups_removed": len(cross),
    "rejected_before_first_3": rejected,
    "field_keys": sorted(rows[0]) if rows else [],
}, ensure_ascii=False, sort_keys=True))
for row in rows:
    print(json.dumps(row, ensure_ascii=False, sort_keys=True))
raise SystemExit(0 if len(rows) == 3 else 2)
