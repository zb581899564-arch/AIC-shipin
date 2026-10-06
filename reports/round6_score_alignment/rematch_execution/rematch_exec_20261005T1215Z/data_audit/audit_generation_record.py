"""Audit the teacher record carried by allowed R7 train/dev labels only."""
from __future__ import annotations
import collections
import hashlib
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
R7 = ROOT / "reports/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z"
RAW = ROOT / "reports/round6_score_alignment/training_alignment_20260917/train.source_copy.jsonl"


def main():
    allowed = {row["row_index"]: row for split in ("train", "dev")
               for row in map(json.loads, (R7 / "inputs" / f"{split}_temporal.jsonl").read_text(encoding="utf-8").splitlines())}
    metadata_counts = collections.defaultdict(collections.Counter)
    counts = collections.Counter()
    timeline_keys = collections.Counter()
    row_records = []
    all_timeline_scores = collections.Counter()
    all_positive_confidence_scores = collections.Counter()
    with RAW.open("rb") as stream:
        for index, line in enumerate(stream):
            if index not in allowed:
                continue
            raw = json.loads(line)
            row = allowed[index]
            if raw["video_id"] != row["video_id"]:
                raise RuntimeError("raw identity mismatch")
            for section, keys in {
                "provenance": ("license", "source", "n_seed_repeats", "prompt_version", "prompt_fingerprint", "annotator_config_sha256", "temporal_fps", "spatial_fps"),
                "quality": ("timeline_coverage", "trajectory_coverage", "status", "spatial_source", "annotation_mode", "n_repeats"),
            }.items():
                for key in keys:
                    metadata_counts[f"{section}.{key}"].update([json.dumps(raw.get(section, {}).get(key), ensure_ascii=False)])
            timeline = raw.get("teacher_signals", {}).get("timeline") or []
            times = [float(point["time_sec"]) for point in timeline]
            scores = [float(point["highlight_score"]) for point in timeline]
            confidence = [float(point["confidence"]) for point in timeline]
            finite = all(math.isfinite(v) for v in times + scores + confidence)
            if not finite:
                raise RuntimeError("nonfinite teacher timeline")
            strictly_sorted = all(b > a for a, b in zip(times, times[1:]))
            for point in timeline:
                timeline_keys.update(point.keys())
                all_timeline_scores.update([str(point["highlight_score"])])
                if float(point["confidence"]) > 0:
                    all_positive_confidence_scores.update([str(point["highlight_score"])])
            zero_confidence = [i for i, value in enumerate(confidence) if value == 0]
            zero_score = [i for i, value in enumerate(scores) if value == 0]
            duration = float(row["clip_duration_sec"])
            candidate_segments = raw.get("teacher_signals", {}).get("candidate_segments") or []
            record = {
                "sample_id": row["sample_id"], "split": row["split"], "source_group": row["source_group"],
                "raw_line": index + 1, "timeline_points": len(timeline),
                "clip_duration_sec": duration, "timeline_first_sec": times[0] if times else None,
                "timeline_last_sec": times[-1] if times else None,
                "last_minus_clip_duration_sec": times[-1] - duration if times else None,
                "timeline_times_strictly_increasing": strictly_sorted,
                "first_point_at_zero": bool(times and abs(times[0]) <= 1e-9),
                "zero_confidence_points": len(zero_confidence),
                "zero_confidence_only_last": zero_confidence == [len(timeline) - 1],
                "zero_score_points": len(zero_score),
                "last_point_zero_confidence_and_score": bool(times and confidence[-1] == 0 and scores[-1] == 0),
                "positive_confidence_zero_score_points": sum(c > 0 and s == 0 for c, s in zip(confidence, scores)),
                "positive_confidence_low_score_below_0_5_points_descriptive_only": sum(c > 0 and s < 0.5 for c, s in zip(confidence, scores)),
                "descriptions_nonempty": sum(bool(point.get("description")) for point in timeline),
                "phases_nonempty": sum(bool(point.get("phase")) for point in timeline),
                "candidate_segments_count": len(candidate_segments),
                "summary_nonempty": bool(raw.get("teacher_signals", {}).get("summary")),
                "quality_claims_timeline_coverage": raw.get("quality", {}).get("timeline_coverage"),
                "provenance_license_nonempty": bool(raw.get("provenance", {}).get("license")),
                "prompt_text_present": any(k in raw or k in raw.get("provenance", {}) for k in ("prompt", "system_prompt", "user_prompt", "prompt_text")),
                "actual_observation_manifest_present": any(k in raw or k in raw.get("provenance", {}) for k in ("observed_frames", "observed_pts", "observation_spans", "media_request", "video_request")),
                "raw_response_finish_reason_present": any(k in raw or k in raw.get("provenance", {}) for k in ("finish_reason", "raw_response", "completion_tokens", "truncated")),
                "teacher_scores_usable_as_bce_negative": False,
                "note": "timeline and coverage fields describe a transformed label record; no generator/prompt/response contract proves the teacher observed or exhaustively labeled these spans",
            }
            row_records.append(record)
            counts["rows"] += 1
            counts["timeline_points"] += len(timeline)
            counts["positive_confidence_points"] += sum(c > 0 for c in confidence)
            counts["zero_confidence_points"] += len(zero_confidence)
            counts["positive_confidence_zero_score_points"] += record["positive_confidence_zero_score_points"]
            counts["positive_confidence_low_score_below_0_5_points_descriptive_only"] += record["positive_confidence_low_score_below_0_5_points_descriptive_only"]
            for key in ("timeline_times_strictly_increasing", "first_point_at_zero", "zero_confidence_only_last", "last_point_zero_confidence_and_score", "provenance_license_nonempty", "prompt_text_present", "actual_observation_manifest_present", "raw_response_finish_reason_present", "summary_nonempty"):
                counts[key + "_rows"] += int(record[key])
            counts["empty_candidate_segments_rows"] += int(len(candidate_segments) == 0)
            counts["rows_any_timeline_description"] += int(record["descriptions_nonempty"] > 0)
            counts["rows_any_timeline_phase"] += int(record["phases_nonempty"] > 0)
    result = {
        "status": "TRANSFORMED_DENSE_TEACHER_SCORES_PRESENT_SEMANTIC_CONTRACT_UNKNOWN",
        "counts": dict(counts),
        "metadata_counts": {key: dict(value) for key, value in metadata_counts.items()},
        "timeline_point_key_counts": dict(timeline_keys),
        "score_histogram_all_points": dict(all_timeline_scores),
        "score_histogram_positive_confidence_points": dict(all_positive_confidence_scores),
        "last_minus_clip_duration_min_sec": min(row["last_minus_clip_duration_sec"] for row in row_records),
        "last_minus_clip_duration_max_sec": max(row["last_minus_clip_duration_sec"] for row in row_records),
        "inspected_raw_rows": len(row_records), "confirm_rows_parsed": 0,
        "threshold_0_5_note": "descriptive count only; no threshold chosen, trained, or used to classify negative labels",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    for name, value, jsonl in (("generation_record_rows.jsonl", row_records, True), ("generation_record_summary.json", result, False)):
        with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
            if jsonl:
                for row in value:
                    stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            else:
                json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
                stream.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
