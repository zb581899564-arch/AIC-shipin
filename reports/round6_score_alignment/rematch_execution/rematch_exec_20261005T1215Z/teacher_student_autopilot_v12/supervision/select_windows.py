"""CPU-only, label-independent natural-window selection from the frozen R7 sources.

This writes preparation receipts, never labels, never starts an inference job.
Only the two pinned train/dev identity manifests are opened; confirm is not opened.
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
MEDIA_ROOT = Path("/home/inspur/aic_video_data/videos")
PINNED = {
    "train": (704, 602, "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf"),
    "dev": (104, 96, "53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700"),
}
COUNTS = {"first": {"train": 128, "dev": 32}, "expanded": {"train": 512, "dev": 64}}
SEED = "aic-complete-window-supervision-20261007-v1"
WINDOW_SECONDS = 30.0
MAX_FRAMES = 64


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 2**20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_digest(*values):
    return hashlib.sha256("\0".join(map(str, (SEED, *values))).encode()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def load_identities(path, split):
    count, groups, digest = PINNED[split]
    require(sha256(path) == digest, "fixed R7 " + split + " manifest byte identity mismatch")
    original = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(original) == count and all(r.get("split") == split for r in original), "fixed split population mismatch")
    # Project only source identity: clip bounds and old positive segments never select a window.
    identities = [{key: row[key] for key in ("sample_id", "video_id", "youtube_id", "source_group", "source_path")}
                  for row in original]
    require(len({r["sample_id"] for r in identities}) == count, "duplicate original sample identity")
    require(len({r["youtube_id"] for r in identities}) == groups, "fixed YouTube group population mismatch")
    for row in identities:
        require(all(isinstance(v, str) and v for v in row.values()), "missing source identity")
        path_text = PurePosixPath(row["source_path"])
        require(path_text.is_absolute() and ".." not in path_text.parts and PurePosixPath("/home/inspur/aic_video_data/videos") in path_text.parents,
                "source outside approved non-test video root")
    return identities


def validate_isolation(train, dev):
    # R7 source_group is a downloaded clip id. youtube_id is the larger leakage unit.
    require(not ({r["youtube_id"] for r in train} & {r["youtube_id"] for r in dev}), "YouTube train/dev leakage")
    require(not ({r["source_path"] for r in train} & {r["source_path"] for r in dev}), "media train/dev leakage")


def rank_sources(rows, split):
    grouped = {}
    for row in rows:
        group = grouped.setdefault(row["youtube_id"], {})
        source = group.setdefault(row["source_path"], {"source_path": row["source_path"],
            "source_group": row["youtube_id"], "youtube_id": row["youtube_id"],
            "downloaded_clip_group": row["source_group"], "parent_sample_ids": [], "parent_video_ids": []})
        require(source["downloaded_clip_group"] == row["source_group"], "conflicting clip identity")
        source["parent_sample_ids"].append(row["sample_id"])
        source["parent_video_ids"].append(row["video_id"])
    order = sorted(grouped, key=lambda group: stable_digest("group", split, group))
    output = []
    for rank, group in enumerate(order):
        paths = sorted(grouped[group], key=lambda path: stable_digest("media", split, group, path))
        source = dict(grouped[group][paths[0]])
        source.update(split=split, source_rank=rank,
                      parent_sample_ids=sorted(source["parent_sample_ids"]),
                      parent_video_ids=sorted(source["parent_video_ids"]))
        output.append(source)
    return output


def parse_clock_frames(frames):
    require(isinstance(frames, list) and len(frames) >= 2, "incomplete full-source clock scan")
    points = []
    for frame in frames:
        text = frame.get("best_effort_timestamp_time")
        require(text not in (None, "N/A"), "missing frame PTS; never drop an unknown frame")
        point = float(text)
        require(math.isfinite(point), "nonfinite frame PTS")
        points.append(point)
    require(all(b > a for a, b in zip(points, points[1:])), "nonincreasing presentation timestamps")
    # The exclusive last endpoint comes from the actual final frame duration, not FPS or old clip bounds.
    last_duration_text = frames[-1].get("pkt_duration_time", frames[-1].get("duration_time"))
    require(last_duration_text not in (None, "N/A"), "actual final-frame duration unavailable; STOP clock")
    last_duration = float(last_duration_text)
    require(math.isfinite(last_duration) and last_duration > 0, "invalid actual final-frame duration")
    deltas = [b - a for a, b in zip(points, points[1:])]
    clock = {"clock_contract": "FULL_SOURCE_PRESENTATION_PTS_WITH_ACTUAL_FINAL_FRAME_DURATION_V1",
        "frame_count": len(points), "first_pts_sec": points[0], "last_pts_sec": points[-1],
        "last_frame_duration_sec": last_duration, "last_frame_duration_field":
            "pkt_duration_time" if "pkt_duration_time" in frames[-1] else "duration_time",
        "pts_end_exclusive_sec": points[-1] + last_duration,
        "max_frame_gap_sec": max(deltas), "median_frame_gap_sec": statistics.median(deltas),
        "pts_sequence_sha256": hashlib.sha256(json.dumps(points, separators=(",", ":")).encode()).hexdigest(),
        "increasing_pts": True, "all_frame_pts_present": True, "clock_scan_full_source": True}
    return points, clock


def probe_source(path_text, ffprobe, timeout):
    path = Path(path_text).resolve(strict=True)
    root = MEDIA_ROOT.resolve(strict=True)
    require(root in path.parents and path.is_file(), "resolved source escapes approved media root")
    before = path.stat()
    digest = sha256(path)
    result = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp_time,pkt_duration_time,duration_time", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=timeout)
    points, clock = parse_clock_frames(json.loads(result.stdout).get("frames"))
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "media changed during clock scan")
    clock.update(source_path=str(path), source_sha256=digest, media_bytes=after.st_size,
                 ffprobe=ffprobe, frame_metadata_decode_performed=True,
                 pixels_exported_or_inspected=False, gpu_used=False)
    return points, clock


def natural_windows(first_pts, end_pts):
    require(finite(first_pts) and finite(end_pts) and end_pts > first_pts, "invalid source PTS extent")
    count = math.ceil((end_pts - first_pts) / WINDOW_SECONDS - 1e-12)
    return [(first_pts + i * WINDOW_SECONDS, min(first_pts + (i + 1) * WINDOW_SECONDS, end_pts))
            for i in range(count)]


def window_index(source, count):
    # Fixed structural strata cover beginnings, interiors and endings without viewing labels/content.
    band = source["source_rank"] % 3
    if count <= 2 or band == 0:
        return 0 if band == 0 else count - 1
    if band == 2:
        return count - 1
    return 1 + int(stable_digest("interior", source["split"], source["source_group"]), 16) % (count - 2)


def spaced_indices(start, stop, limit=MAX_FRAMES):
    require(type(start) is int and type(stop) is int and stop > start and limit >= 2, "empty eligible frame range")
    count = stop - start
    if count <= limit:
        return list(range(start, stop))
    # Deterministic integer arithmetic includes the first and last eligible source frame.
    return [start + i * (count - 1) // (limit - 1) for i in range(limit)]


def make_window(source, points, clock):
    bounds = natural_windows(clock["first_pts_sec"], clock["pts_end_exclusive_sec"])
    ordinal = window_index(source, len(bounds))
    start, end = bounds[ordinal]
    lower, upper = bisect.bisect_left(points, start), bisect.bisect_left(points, end)
    indices = spaced_indices(lower, upper)
    actual_pts = [points[i] for i in indices]
    role = "source_beginning" if ordinal == 0 else "source_end" if ordinal == len(bounds) - 1 else "interior"
    window_id = "complete_" + stable_digest(source["split"], source["source_path"], clock["source_sha256"], ordinal)[:24]
    return {"schema": "aic_complete_window_selection_v1", **source, "window_id": window_id,
        "source_sha256": clock["source_sha256"], "clock_sequence_sha256": clock["pts_sequence_sha256"],
        "source_clock_first_pts_sec": clock["first_pts_sec"],
        "source_clock_end_exclusive_sec": clock["pts_end_exclusive_sec"],
        "window_ordinal": ordinal, "source_natural_window_count": len(bounds),
        "window_pts_start_sec": start, "window_pts_end_exclusive_sec": end,
        "window_duration_sec": end - start, "window_stride_sec": WINDOW_SECONDS,
        "window_geometry": "30S_NONOVERLAP_FULL_SOURCE_CLOCK_TAIL_ALLOWED",
        "structural_stratum": role, "eligible_source_frame_count": upper - lower,
        "planned_source_frame_ordinals": indices, "planned_actual_pts_sec": actual_pts,
        "planned_max_sample_gap_sec": max((b - a for a, b in zip(actual_pts, actual_pts[1:])), default=0.0),
        "first_eligible_pts_sec": points[lower], "last_eligible_pts_sec": points[upper - 1],
        "observation_status": "PLANNED_ONLY_NOT_DECODED_OR_LABELLED", "label_status": "UNLABELLED",
        "old_positive_segments_used": False, "semantic_strata_claimed": False,
        "data_use_evidence": "Inherited approved R7 train/dev sources; no new licensing claim"}


def write_jsonl(path, rows):
    with Path(path).open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")


def output_directory(path):
    resolved = Path(path).resolve()
    require(HERE in resolved.parents, "outputs must stay inside the owned supervision directory")
    require(not resolved.exists(), "never overwrite an existing selection run")
    resolved.mkdir(parents=True)
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--dev-manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--tier", choices=COUNTS, default="first")
    parser.add_argument("--ffprobe", default=None)
    parser.add_argument("--source-timeout", type=int, default=240)
    args = parser.parse_args()
    require(args.source_timeout > 0, "invalid clock-scan timeout")
    identities = {split: load_identities(getattr(args, split + "_manifest"), split) for split in ("train", "dev")}
    validate_isolation(identities["train"], identities["dev"])
    ffprobe = args.ffprobe or shutil.which("ffprobe")
    require(ffprobe and Path(ffprobe).is_file(), "existing ffprobe required; do not install automatically")
    out = output_directory(args.out_dir)
    receipt = {"schema": "aic_complete_window_selection_receipt_v1", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "CPU_SELECTION_IN_PROGRESS", "tier": args.tier, "counts_requested": COUNTS[args.tier],
        "seed": SEED, "manifests": {split: {"path": str(getattr(args, split + "_manifest")),
            "sha256": PINNED[split][2], "rows": PINNED[split][0], "youtube_groups": PINNED[split][1]}
            for split in ("train", "dev")},
        "confirm_opened": False, "contest_assets_opened": False, "gpu_used": False,
        "labels_generated": False, "old_label_values_used_for_selection": False,
        "old_r7_json_loaded_only_to_extract_whitelisted_identity_fields": True,
        "selection_unit": "ONE_NATURAL_WINDOW_PER_DISTINCT_YOUTUBE_GROUP",
        "first_is_prefix_of_expanded": True, "not_all_windows_in_source_are_sent_to_teacher": True,
        "source_clock_scan": "FULL_SOURCE_PRESENTATION_TIMESTAMPS_NO_PIXEL_INFERENCE"}
    clocks, selected = [], {"train": [], "dev": []}
    try:
        for split in ("train", "dev"):
            candidates = rank_sources(identities[split], split)[:COUNTS[args.tier][split]]
            require(len(candidates) == COUNTS[args.tier][split], "insufficient approved distinct source groups")
            for source in candidates:
                points, clock = probe_source(source["source_path"], ffprobe, args.source_timeout)
                clocks.append({"split": split, "source_group": source["source_group"], **clock})
                selected[split].append(make_window(source, points, clock))
                print(json.dumps({"split": split, "completed": len(selected[split]), "requested": len(candidates)}), flush=True)
        validate_isolation(selected["train"], selected["dev"])
        for split in ("train", "dev"):
            write_jsonl(out / ("selected_" + split + ".jsonl"), selected[split])
        write_jsonl(out / "source_clocks.jsonl", clocks)
        receipt.update(status="PASS_CPU_SELECTION_UNLABELLED", counts={k: len(v) for k, v in selected.items()},
            structural_strata={split: {kind: sum(r["structural_stratum"] == kind for r in rows)
                for kind in ("source_beginning", "interior", "source_end")} for split, rows in selected.items()},
            files={name: sha256(out / name) for name in ("selected_train.jsonl", "selected_dev.jsonl", "source_clocks.jsonl")})
    except Exception as exc:
        receipt.update(status="STOP_CPU_SELECTION_CLOCK_OR_IDENTITY", reason=f"{type(exc).__name__}: {exc}",
                       completed_unlabelled_counts={k: len(v) for k, v in selected.items()})
        (out / "selection_receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        raise
    (out / "selection_receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
