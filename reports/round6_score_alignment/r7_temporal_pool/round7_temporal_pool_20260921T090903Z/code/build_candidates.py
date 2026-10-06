"""Build the pre-PTS R7 temporal candidate manifest from frozen inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from r7_core import validate_segments


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--mapping", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.out_dir / "candidate_manifest.jsonl"
    report_path = args.out_dir / "preaudit_report.json"
    if manifest.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite pre-audit outputs")

    labels, mappings = read_jsonl(args.labels), read_jsonl(args.mapping)
    if len(labels) != 987 or len(mappings) != 987:
        raise RuntimeError("frozen inputs must both contain 987 rows")
    candidates, rejected = [], []
    for index, (label, mapping) in enumerate(zip(labels, mappings)):
        reasons: list[str] = []
        if mapping.get("row_index") != index:
            reasons.append("mapping_row_index_mismatch")
        if label.get("video_id") != mapping.get("video_id"):
            reasons.append("video_id_mismatch")
        clip = label.get("clip") or {}
        if clip.get("source_vid") != mapping.get("source_vid"):
            reasons.append("source_vid_mismatch")
        source_path = mapping.get("source_path")
        if not source_path:
            reasons.append("missing_source_path")
        elif Path(source_path).stem != clip.get("source_vid"):
            reasons.append("source_stem_mismatch")
        if mapping.get("status") not in {"usable", "time_uncertain"}:
            reasons.append(f"mapping_status:{mapping.get('status')}")
        start, end = clip.get("start_sec"), clip.get("end_sec")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   for v in (start, end)) or not 0 <= float(start) < float(end):
            reasons.append("invalid_clip_bounds")
            duration = 0.0
        else:
            start, end = float(start), float(end)
            duration = end - start
        raw_segments = label.get("segments") or []
        segments = []
        for segment in raw_segments:
            try:
                a, b = float(segment["start_sec"]), float(segment["end_sec"])
                segments.append([a, b])
                if abs(float(segment["source_start_sec"]) - (start + a)) > 1e-5:
                    reasons.append("source_start_formula_mismatch")
                if abs(float(segment["source_end_sec"]) - (start + b)) > 1e-5:
                    reasons.append("source_end_formula_mismatch")
            except (KeyError, TypeError, ValueError):
                reasons.append("malformed_segment")
        reasons.extend(validate_segments(segments, duration))
        if reasons:
            rejected.append({"row_index": index, "video_id": label.get("video_id"),
                             "reasons": sorted(set(reasons))})
            continue
        source_probe = mapping.get("source_probe") or {}
        candidates.append({
            "sample_id": f"{mapping['youtube_id']}__r{index}",
            "row_index": index,
            "video_id": label["video_id"],
            "youtube_id": mapping["youtube_id"],
            "source_group": mapping["source_group"],
            "source_vid": mapping["source_vid"],
            "source_path": source_path,
            "source_avg_fps": source_probe.get("avg_fps"),
            "source_declared_frames": source_probe.get("nb_frames"),
            "source_declared_duration_sec": source_probe.get("duration_sec"),
            "clip_start_sec": start,
            "clip_end_sec": end,
            "clip_duration_sec": duration,
            "segments_clip_local": segments,
            "n_segments": len(segments),
            "mapping_status": mapping["status"],
            "spatial_mapping_status": mapping["status"],
            "label_status": "WEAK_TEACHER",
            "annotation_source": "api_doubao_doubao-seed-2-1-pro-260628",
        })

    with manifest.open("x", encoding="utf-8") as stream:
        for row in candidates:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "status": "PRE_PTS_CANDIDATES_FROZEN",
        "input_hashes": {"labels": sha256(args.labels), "mapping": sha256(args.mapping)},
        "input_rows": {"labels": len(labels), "mapping": len(mappings)},
        "candidate_rows": len(candidates),
        "candidate_groups": len({r["youtube_id"] for r in candidates}),
        "candidate_mapping_status": {
            status: sum(r["mapping_status"] == status for r in candidates)
            for status in ("usable", "time_uncertain")},
        "rejected_rows": len(rejected),
        "rejections": rejected,
        "candidate_manifest_sha256": sha256(manifest),
        "policy": "WEAK_TEACHER temporal-only candidates; PTS audit required before use",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
