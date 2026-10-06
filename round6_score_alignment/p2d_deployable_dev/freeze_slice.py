"""Freeze the P2-D source-independent complete development slice on CPU."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

from p2d_core import load_jsonl, sha256_file, write_jsonl

ROOT = Path(__file__).resolve().parents[2]
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"
P2 = ROOT / "reports/round6_score_alignment/p2_joint_coverage"

PINNED = {
    "dev_temporal.jsonl": "242a3a0475f6c5b66cd2a25deef88f3b477f3f6ea5f4d22984c1a12830d3bd3c",
    "dev_frames.jsonl": "711fd3c8d0c960957bd519c13654e0f38f53296cda83cc2edb2f182982551c84",
    "temporal_S2.jsonl": "ca51e6d49e2394dcef28dc1b651e9803646ae8921a97e6f669632cc082e73903",
    "p2_infer_requests_v2_source_grid.jsonl": "cefffbc9d92d31f5d3f2b464fe44a39272b9499d46e6f4e2342a5d5efa684a02",
    "p2_v3_freeze.json": "43d6fafb17f208662458656fbe1020080e16b18db1a23ba6d2d237e84993ec96",
}
SEED = 20260919


def parse_s2_segments(row: dict) -> list[tuple[float, float]]:
    try:
        payload = json.loads(row["raw_output"])
    except Exception as exc:
        raise ValueError(f"{row['video_id']}: invalid frozen S2 JSON: {exc}") from exc
    segments = payload.get("segments")
    if not isinstance(segments, list) or len(segments) > 5:
        raise ValueError(f"{row['video_id']}: invalid segment list")
    duration = float(row["clip_duration_sec"])
    parsed = []
    for segment in segments:
        if not isinstance(segment, list) or len(segment) != 2:
            raise ValueError(f"{row['video_id']}: invalid segment")
        a, b = float(segment[0]), float(segment[1])
        if not math.isfinite(a + b) or a < 0 or b <= a or b > duration + 1e-6:
            raise ValueError(f"{row['video_id']}: out-of-range segment {segment}")
        parsed.append((a, b))
    return parsed


def tie_key(video_id: str, youtube_id: str) -> str:
    return hashlib.sha256(f"{SEED}:{youtube_id}:{video_id}".encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    freeze_path = out_dir / "freeze_manifest.json"
    requests_path = out_dir / "inference_requests.jsonl"
    selected_path = out_dir / "selected_frames.jsonl"
    if any(path.exists() for path in (freeze_path, requests_path, selected_path)):
        raise FileExistsError("refusing to overwrite an existing P2-D freeze")

    paths = {
        "dev_temporal.jsonl": WEAK / "dev_temporal.jsonl",
        "dev_frames.jsonl": WEAK / "dev_frames.jsonl",
        "temporal_S2.jsonl": WEAK / "temporal_S2.jsonl",
        "p2_infer_requests_v2_source_grid.jsonl": P2 / "p2_infer_requests_v2_source_grid.jsonl",
        "p2_v3_freeze.json": P2 / "round6_p2_freeze_v3_final_20260918T1600Z.json",
    }
    observed = {name: sha256_file(path) for name, path in paths.items()}
    mismatches = {name: {"expected": PINNED[name], "observed": value}
                  for name, value in observed.items() if value != PINNED[name]}
    if mismatches:
        raise RuntimeError(f"protected input hash mismatch: {mismatches}")

    dev_temporal = load_jsonl(paths["dev_temporal.jsonl"])
    dev_frames = load_jsonl(paths["dev_frames.jsonl"])
    s2_rows = {row["video_id"]: row for row in load_jsonl(paths["temporal_S2.jsonl"])}
    full_requests = load_jsonl(paths["p2_infer_requests_v2_source_grid.jsonl"])
    temporal_by_vid = {row["video_id"]: row for row in dev_temporal}
    first_frame = {}
    weak_by_key = {}
    for row in dev_frames:
        first_frame.setdefault(row["video_id"], row)
        weak_by_key[(row["video_id"], int(row["source_frame"]))] = row

    recomputed: set[tuple[str, int]] = set()
    for row in dev_temporal:
        vid = row["video_id"]
        meta = first_frame[vid]
        fps = float(meta["source_fps"])
        source_start = math.ceil(float(row["clip_start_sec"]) * fps)
        source_end = math.floor(float(row["clip_end_sec"]) * fps)
        for a, b in parse_s2_segments(s2_rows[vid]):
            lo, hi = math.ceil(a * fps), math.ceil(b * fps)
            recomputed.update((vid, frame) for frame in range(
                source_start + max(0, lo),
                source_start + min(source_end - source_start + 1, hi)))
    manifest_keys = [(row["video_id"], int(row["source_frame"])) for row in full_requests]
    if len(manifest_keys) != len(set(manifest_keys)) or set(manifest_keys) != recomputed:
        raise RuntimeError("v3 source-frame selection does not exactly match independent reconstruction")

    overlap_ids = set(json.loads((WEAK / "s2_overlap.json").read_text(encoding="utf-8"))[
        "overlap_video_ids"])
    counts: dict[str, int] = {}
    rows_by_vid: dict[str, list[dict]] = {}
    for row in full_requests:
        counts[row["video_id"]] = counts.get(row["video_id"], 0) + 1
        rows_by_vid.setdefault(row["video_id"], []).append(row)
    candidates = []
    for vid, count in counts.items():
        temporal = temporal_by_vid[vid]
        candidates.append({
            "video_id": vid,
            "youtube_id": temporal["youtube_id"],
            "selected_frames": count,
            "historical_s2_source_exposure": vid in overlap_ids,
            "tie_sha256": tie_key(vid, temporal["youtube_id"]),
        })

    chosen = []
    for exposure in (True, False):
        stratum = sorted((row for row in candidates
                          if row["historical_s2_source_exposure"] is exposure),
                         key=lambda row: (row["selected_frames"], row["tie_sha256"]))
        used_groups = set()
        for row in stratum:
            if row["youtube_id"] in used_groups:
                continue
            chosen.append(row)
            used_groups.add(row["youtube_id"])
            if len(used_groups) == 4:
                break
        if len(used_groups) != 4:
            raise RuntimeError(f"unable to select four unique source groups for exposure={exposure}")
    chosen_ids = {row["video_id"] for row in chosen}
    if len({row["youtube_id"] for row in chosen}) != 8:
        raise RuntimeError("selected source groups are not independent")

    request_rows = []
    selected_rows = []
    for row in full_requests:
        if row["video_id"] not in chosen_ids:
            continue
        request = dict(row)
        request["request_key"] = f"{row['video_id']}#src{int(row['source_frame'])}"
        request["request_sha256"] = hashlib.sha256(json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        request_rows.append(request)
        weak = weak_by_key.get((row["video_id"], int(row["source_frame"])))
        selected_rows.append({
            **request,
            "youtube_id": temporal_by_vid[row["video_id"]]["youtube_id"],
            "clip_start_sec": temporal_by_vid[row["video_id"]]["clip_start_sec"],
            "clip_end_sec": temporal_by_vid[row["video_id"]]["clip_end_sec"],
            "source_fps": float(first_frame[row["video_id"]]["source_fps"]),
            "weak_roi_xywh": weak["weak_roi_xywh"] if weak else None,
            "weak_label_status": "WEAK_TEACHER" if weak else None,
        })
    write_jsonl(requests_path, request_rows)
    write_jsonl(selected_path, selected_rows)

    selection_records = []
    for row in sorted(candidates, key=lambda item: item["video_id"]):
        selection_records.append({
            **row,
            "selected": row["video_id"] in chosen_ids,
            "reason": ("selected: four smallest complete clips in historical-exposure stratum"
                       if row["video_id"] in chosen_ids and row["historical_s2_source_exposure"] else
                       "selected: four smallest complete clips in historically-unexposed stratum"
                       if row["video_id"] in chosen_ids else
                       "not selected by frozen stratum count/tie rule"),
        })
    result = {
        "schema": "aic6_p2d_freeze_v1",
        "run_id": args.run_id,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "CPU_SLICE_FROZEN",
        "official_status": "NOT_OFFICIAL_SCORE",
        "selection_rule": {
            "seed": SEED,
            "description": "partition by historical S2 source exposure; within each stratum sort by complete S2-selected source-frame count then sha256(seed:youtube_id:video_id); take four unique youtube_id groups",
            "uses_current_spatial_output": False,
            "uses_weak_iou": False,
            "allows_truncation": False,
        },
        "source_frame_rule": "sf=ceil(clip_start_sec*source_fps); each frozen S2 [a,b) selects range(sf+ceil(a*fps), sf+ceil(b*fps)); clamp to clip end",
        "source_grid_matches_v3_manifest": True,
        "input_hashes": observed,
        "selected_videos": chosen,
        "selected_video_count": len(chosen),
        "selected_source_group_count": len({row["youtube_id"] for row in chosen}),
        "selected_source_frames": len(request_rows),
        "historical_exposure_counts": {
            "exposed": sum(row["historical_s2_source_exposure"] for row in chosen),
            "unexposed": sum(not row["historical_s2_source_exposure"] for row in chosen),
        },
        "all_candidates": selection_records,
        "frozen_comparison": {
            "qwen": "unmodified Qwen3-VL-4B-Instruct predict_focus, real same-frame inference",
            "center": "maximum legal 9:16 crop centered at normalized (0.5,0.5)",
            "failure_policy": "model/decode/parse/box failure remains failure; never legal empty and never center fallback",
            "shot_policy": "no trusted shot map; infer every selected frame independently",
        },
        "prior_throughput": {
            "frames": 6186,
            "wall_seconds_including_load": 3940.46,
            "frames_per_second": 6186 / 3940.46,
            "estimated_wall_seconds_for_slice": len(request_rows) / (6186 / 3940.46) + 15,
        },
        "request_manifest": {"path": requests_path.name, "sha256": sha256_file(requests_path)},
        "selected_frames_manifest": {"path": selected_path.name, "sha256": sha256_file(selected_path)},
    }
    freeze_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "videos": len(chosen),
                      "source_groups": 8, "frames": len(request_rows),
                      "freeze_sha256": sha256_file(freeze_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

