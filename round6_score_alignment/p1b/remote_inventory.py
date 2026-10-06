#!/usr/bin/env python3
"""P1b step 1-3: read-only corpus inventory, exclusion sets and deterministic sampling.

Reads (remote, read-only):
  /home/inspur/aic_video_data/labels/train.jsonl                 (987 label rows)
  /home/inspur/aic_video_work/temporal_round5/data/{train,dev,holdout}.jsonl (818 rows)
  /home/inspur/aic_video_work/orarl_round4/evidence/mapping_rows.jsonl
  /home/inspur/aic_video_data/videos/**/*.mp4                    (file names + sizes only)

Prints a compact JSON summary to stdout.  Writes nothing.
"""
from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path

DATA = Path("/home/inspur/aic_video_data")
WORK = Path("/home/inspur/aic_video_work")
VIDEOS = DATA / "videos"
LABELS = DATA / "labels/train.jsonl"
SPLITS = [WORK / "temporal_round5/data" / f"{n}.jsonl" for n in ("train", "dev", "holdout")]
MAPPING = WORK / "orarl_round4/evidence/mapping_rows.jsonl"
TEST_ROOT = DATA / "test"
SEED = 20260917
NAME_RE = re.compile(r"^(?P<yt>.+?)_(?P<ws>\d+(?:\.\d+)?)_(?P<we>\d+(?:\.\d+)?)$")
SIZE_MIN = 3_000_000
SIZE_MAX = 40_000_000


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def youtube_id_from_source_vid(source_vid: str) -> str:
    m = NAME_RE.match(source_vid or "")
    return m.group("yt") if m else (source_vid or "")


def main() -> int:
    out = {"seed": SEED, "source": {}}

    label_groups, label_rows, label_video_ids = set(), 0, set()
    for row in read_jsonl(LABELS):
        label_rows += 1
        prov = row.get("provenance") or {}
        clip = row.get("clip") or {}
        # label `source_group` is WINDOW level (e.g. "<yt>_210.0_360.0") while the corpus file
        # name carries the YouTube id, so exclusion has to be done on the parsed YouTube id.
        video_id = youtube_id_from_source_vid(clip.get("source_vid") or "")
        if video_id:
            label_video_ids.add(video_id)
        if prov.get("source_group"):
            label_groups.add(str(prov["source_group"]))
    out["source"]["label_rows"] = label_rows
    out["source"]["label_source_groups_window_level"] = len(label_groups)
    out["source"]["label_youtube_ids"] = len(label_video_ids)

    split_groups, split_rows = set(), 0
    split_detail = {}
    for path in SPLITS:
        rows = 0
        for row in read_jsonl(path):
            rows += 1
            split_rows += 1
            if row.get("youtube_id"):
                split_groups.add(str(row["youtube_id"]))
        split_detail[path.name] = rows
    out["source"]["split_rows"] = split_rows
    out["source"]["split_detail"] = split_detail
    out["source"]["split_source_groups"] = len(split_groups)

    mapping_status = {}
    mapping_groups = set()
    for row in read_jsonl(MAPPING):
        mapping_status[row.get("status")] = mapping_status.get(row.get("status"), 0) + 1
        if row.get("youtube_id"):
            mapping_groups.add(str(row["youtube_id"]))
    out["source"]["mapping_status"] = mapping_status
    out["source"]["mapping_source_groups"] = len(mapping_groups)

    excluded = label_video_ids | split_groups | mapping_groups
    out["exclusion"] = {
        "label_youtube_ids": len(label_video_ids),
        "mapping_youtube_ids": len(mapping_groups),
        "split_youtube_ids": len(split_groups),
        "union_youtube_ids": len(excluded),
        "basis": "union of YouTube-level ids from the 987 label rows, the round-4 mapping and "
                 "the 818 split rows; exclusion is applied to the YouTube id parsed from the "
                 "corpus file name",
        "test_root": str(TEST_ROOT),
        "test_root_files": sum(1 for _ in TEST_ROOT.rglob("*") if _.is_file()),
        "test_root_excluded": True,
    }

    files = []
    for path in VIDEOS.rglob("*.mp4"):
        name = path.name
        m = NAME_RE.match(path.stem)
        yt = m.group("yt") if m else None
        try:
            size = path.stat().st_size
        except OSError:
            continue
        files.append({"name": name, "path": str(path), "youtube_id": yt, "bytes": size,
                      "window": [float(m.group("ws")), float(m.group("we"))] if m else None})
    out["corpus"] = {
        "files_total": len(files),
        "files_unparseable_name": sum(1 for f in files if f["youtube_id"] is None),
        "distinct_youtube_ids": len({f["youtube_id"] for f in files if f["youtube_id"]}),
        "total_bytes": sum(f["bytes"] for f in files),
    }

    candidates = [f for f in files
                  if f["youtube_id"] and f["youtube_id"] not in excluded
                  and SIZE_MIN <= f["bytes"] <= SIZE_MAX]
    out["candidates"] = {
        "files": len(candidates),
        "distinct_youtube_ids": len({f["youtube_id"] for f in candidates}),
        "excluded_by_source_group": sum(1 for f in files if f["youtube_id"] in excluded),
        "excluded_by_size": sum(1 for f in files if f["youtube_id"]
                                and f["youtube_id"] not in excluded
                                and not (SIZE_MIN <= f["bytes"] <= SIZE_MAX)),
    }

    by_group = {}
    for f in sorted(candidates, key=lambda x: (x["youtube_id"], x["name"])):
        by_group.setdefault(f["youtube_id"], []).append(f)
    groups = sorted(by_group)
    rng = random.Random(SEED)
    chosen = rng.sample(groups, 8) if len(groups) >= 8 else groups
    chosen = sorted(chosen)                     # stable report order
    targets = [[16, 9], [16, 9], [16, 9], [16, 9], [9, 16], [9, 16], [9, 16], [9, 16]]
    out["sampling"] = {
        "rule": ("group by youtube_id; drop groups whose youtube_id appears in the 987 label "
                 "rows or the 818 split rows; size window 3-40 MB; stable sort by "
                 "(youtube_id, filename); random.Random(20260917).sample(8 distinct groups)"),
        "candidate_groups": len(groups),
        "selected": [{"youtube_id": g, "target_ratio_wh": t,
                      "files_in_group": len(by_group[g]),
                      "first_file": by_group[g][0]["name"],
                      "first_file_bytes": by_group[g][0]["bytes"],
                      "window": by_group[g][0]["window"]}
                     for g, t in zip(chosen, targets)],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
