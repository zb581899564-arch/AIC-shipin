"""CPU-only semantic inventory; parses only frozen R7 train/dev raw rows.

No media decode, no confirmation labels, no PTS audit, no split generation.
The clip bounds are an audit domain, NEVER a teacher-observation assertion.
"""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
R7 = WORKSPACE / "reports/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z"
RAW = WORKSPACE / "reports/round6_score_alignment/training_alignment_20260917/train.source_copy.jsonl"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_new(name, value, jsonl=False):
    path = OUT / name
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        if jsonl:
            for row in value:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")


def union(pairs):
    result = []
    for start, end in sorted(pairs):
        if not result or start > result[-1][1]:
            result.append([start, end])
        else:
            result[-1][1] = max(result[-1][1], end)
    return result


def complement(pairs, duration):
    result, cursor = [], 0.0
    for start, end in union(pairs):
        if start > cursor:
            result.append([cursor, start])
        cursor = end
    if cursor < duration:
        result.append([cursor, duration])
    return result


def main():
    allowed, split_rows, paths = {}, {}, {}
    for split in ("train", "dev"):
        path = R7 / "inputs" / f"{split}_temporal.jsonl"
        paths[split] = path
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        split_rows[split] = rows
        for row in rows:
            if row["split"] != split or row["row_index"] in allowed:
                raise RuntimeError("frozen split mismatch or duplicate raw row index")
            allowed[row["row_index"]] = row
    groups = {split: {row["youtube_id"] for row in rows} for split, rows in split_rows.items()}
    if groups["train"] & groups["dev"]:
        raise RuntimeError("train/dev source leakage")
    if len(split_rows["train"]) != 704 or len(split_rows["dev"]) != 104:
        raise RuntimeError("unexpected frozen train/dev cardinalities")

    schemas = collections.defaultdict(collections.Counter)
    scalar_counts = collections.defaultdict(collections.Counter)
    selected = {}
    # The forbidden rows are skipped in bytes before JSON decoding or parsing.
    with RAW.open("rb") as stream:
        for raw_index, line in enumerate(stream):
            if raw_index not in allowed:
                continue
            raw = json.loads(line)
            row = allowed[raw_index]
            if raw["video_id"] != row["video_id"] or raw["clip"]["source_vid"] != row["source_vid"]:
                raise RuntimeError("raw/frozen identity mismatch")
            actual = [[float(segment["start_sec"]), float(segment["end_sec"])] for segment in raw["segments"]]
            if actual != row["segments_clip_local"]:
                raise RuntimeError("raw/frozen segment mismatch")
            selected[raw_index] = raw
            schemas["top_level"].update(raw.keys())
            for section in ("clip", "provenance", "quality", "teacher_signals"):
                value = raw.get(section)
                if isinstance(value, dict):
                    schemas[section].update(value.keys())
                    for key, item in value.items():
                        if isinstance(item, dict):
                            schemas[f"{section}.{key}"].update(item.keys())
                        if key in {"seed_model", "spatial_fps", "mode", "version", "annotation_mode", "finish_reason", "task", "task_type", "temporal_fps", "sampling_fps", "fps", "complete", "is_complete", "exhaustive", "top_k", "max_segments", "max_tokens"}:
                            if isinstance(item, (str, bool, int, float)) or item is None:
                                scalar_counts[f"{section}.{key}"].update([json.dumps(item, ensure_ascii=False)])
            for key in ("annotation_mode", "schema_version", "dataset_split"):
                scalar_counts[key].update([json.dumps(raw.get(key), ensure_ascii=False)])
    if set(selected) != set(allowed):
        raise RuntimeError("allowed raw row missing")

    semantics, stats = [], {}
    for split, rows in split_rows.items():
        split_seconds = positive_seconds = unknown_seconds = 0.0
        segment_histogram = collections.Counter()
        for row in rows:
            raw = selected[row["row_index"]]
            duration = float(row["clip_duration_sec"])
            positives = union(row["segments_clip_local"])
            unresolved = complement(positives, duration)
            positive = sum(end - start for start, end in positives)
            unknown = sum(end - start for start, end in unresolved)
            split_seconds += duration
            positive_seconds += positive
            unknown_seconds += unknown
            segment_histogram.update([str(row["n_segments"])])
            semantics.append({
                "sample_id": row["sample_id"], "row_index": row["row_index"], "split": split,
                "source_group": row["source_group"], "youtube_id": row["youtube_id"],
                "source_vid": row["source_vid"], "raw_label_file": str(RAW), "raw_line": row["row_index"] + 1,
                "clip_start_sec": row["clip_start_sec"], "clip_end_sec": row["clip_end_sec"],
                "clip_duration_sec": duration, "audit_domain_clip_local": [0.0, duration],
                "audit_domain_is_teacher_observation": False,
                "verified_teacher_observation_spans_clip_local": [],
                "teacher_observation_status": "UNKNOWN",
                "weak_positive_spans_clip_local": positives,
                "unselected_spans_clip_local": unresolved,
                "unselected_semantics": "UNKNOWN", "teacher_negative_spans_clip_local": [],
                "general_highlight_selection_semantics": "UNKNOWN",
                "forced_top_k_status": "UNKNOWN_TEACHER_PROMPT_NOT_AVAILABLE",
                "teacher_output_truncation_status": "UNKNOWN_NO_RAW_RESPONSE_OR_FINISH_REASON",
                "license_status": "EXISTING_LOCAL_WEAK_RESEARCH_BOUNDARY_ONLY_NO_ITEM_LICENSE",
                "official_share_origin_status": "DOWNLOAD_LOG_AND_PRIOR_USER_CONFIRMATION_NOT_ITEM_PERMISSION",
                "annotation_source": row["annotation_source"], "label_status": "WEAK_TEACHER",
                "bce_formal_training_eligible": False,
                "evidence_notes": ["clip bounds and PTS do not certify exhaustive annotation", "positive union is not teacher observation", "raw source metadata audited only for this frozen train/dev row"],
            })
        stats[split] = {
            "rows": len(rows), "source_groups": len(groups[split]),
            "clip_seconds_sum_over_rows": split_seconds,
            "weak_positive_seconds_sum_over_rows": positive_seconds,
            "unselected_unknown_seconds_sum_over_rows": unknown_seconds,
            "nonempty_positive_rows": len(rows), "segment_count_histogram": dict(segment_histogram),
            "verified_observation_rows": 0, "teacher_negative_rows": 0,
            "bce_formal_training_eligible_rows": 0,
        }
    summary = {
        "status": "STOP_C_FORMAL_BCE_UNKNOWN_NEGATIVE_SEMANTICS",
        "audited_rows": len(allowed), "source_groups": len(groups["train"] | groups["dev"]),
        "train_dev_group_intersection": [], "outer_split_changed": False,
        "confirmation_label_file_opened": False, "confirmation_label_rows_parsed": 0,
        "raw_rows_parsed": len(selected), "raw_other_rows_not_decoded_or_parsed": True,
        "media_decoded": False, "pts_audit_rerun": False, "gpu_used": False,
        "statistics": stats,
        "schema_key_counts": {section: dict(counts) for section, counts in schemas.items()},
        "scalar_field_counts": {field: dict(counts) for field, counts in scalar_counts.items()},
        "input_hashes": {split: sha256(path) for split, path in paths.items()},
        "raw_file_sha256_byte_identity_only": sha256(RAW),
        "script_sha256": sha256(Path(__file__)),
        "counting_note": "seconds sum clip rows; overlapping same-source clips are not deduplicated; no verified observed or negative exposure is inferred",
    }
    write_new("teacher_semantics_train_dev.jsonl", semantics, jsonl=True)
    write_new("teacher_semantics_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
