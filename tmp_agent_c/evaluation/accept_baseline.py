"""Format-only acceptance report for baseline prediction artifacts.

This tool deliberately does not compute a contest score.  The fixed media
metadata is an index (not ground truth), and the official evaluator source and
test labels are unavailable to this workspace.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

try:
    from .schema import load_jsonl_records, load_media_metadata, validate_submission_records
except ImportError:  # direct ``python accept_baseline.py`` invocation
    from schema import load_jsonl_records, load_media_metadata, validate_submission_records


DEFAULT_METADATA = "/home/inspur/aic_video_work/reports/supervisor_test_metadata.json"
DEFAULT_ROOT = "/home/inspur/aic_video_work"


def _jsonl_status_candidates(prediction_path: Path) -> List[Path]:
    directory = prediction_path.parent
    candidates = [
        prediction_path.with_name(prediction_path.name + ".status.jsonl"),
        prediction_path.with_name("status.jsonl"),
        prediction_path.with_name(prediction_path.stem + ".status.jsonl"),
    ]
    result: List[Path] = []
    seen = set()
    for item in candidates:
        if item not in seen and item.is_file():
            result.append(item)
            seen.add(item)
    return result


def _read_status(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {
            "available": False,
            "path": None,
            "line_count": 0,
            "parse_issues": [],
            "status_counts": {},
            "records": [],
        }
    records: List[Mapping[str, Any]] = []
    parse_issues: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                parse_issues.append({"line": line_number, "code": "BLANK_LINE"})
                continue
            try:
                value = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                parse_issues.append({"line": line_number, "code": "JSON_PARSE", "message": str(exc)})
                continue
            if not isinstance(value, Mapping):
                parse_issues.append({"line": line_number, "code": "ROW_SHAPE"})
                continue
            records.append(value)
    counts = Counter(str(item.get("status", "missing")) for item in records)
    return {
        "available": True,
        "path": str(path),
        "line_count": len(records) + len(parse_issues),
        "parse_issues": parse_issues,
        "status_counts": dict(sorted(counts.items())),
        "records": records,
    }


def _read_run_summary(path: Path) -> Dict[str, Any]:
    summary_path = path.with_name("run_summary.json")
    if not summary_path.is_file():
        return {"available": False, "path": None, "value": None}
    try:
        value = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "available": True,
            "path": str(summary_path),
            "value": None,
            "parse_error": str(exc),
        }
    return {"available": True, "path": str(summary_path), "value": value}


def _issue_summary(issues: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    issues = list(issues)
    by_code = Counter(str(item.get("code", "UNKNOWN")) for item in issues)
    by_severity = Counter(str(item.get("severity", "unknown")) for item in issues)
    return {
        "count": len(issues),
        "by_code": dict(sorted(by_code.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "examples": issues[:10],
    }


def _row_ids(
    records: Iterable[Any], metadata_ids: set[str]
) -> Tuple[List[str], Counter, Dict[str, int], Dict[str, int]]:
    ids: List[str] = []
    occurrences: Counter = Counter()
    empty_counts: Dict[str, int] = {"known": 0, "unknown": 0, "malformed": 0}
    prediction_counts: Dict[str, int] = {"known": 0, "unknown": 0, "malformed": 0}
    for value in records:
        if not isinstance(value, Mapping) or value.get("video_id") is None:
            empty_counts["malformed"] += 1
            prediction_counts["malformed"] += 1
            continue
        video_id = str(value["video_id"])
        ids.append(video_id)
        occurrences[video_id] += 1
        predictions = value.get("predictions")
        bucket = "known" if video_id in metadata_ids else "unknown"
        if isinstance(predictions, list):
            prediction_counts[bucket] += len(predictions)
            if not predictions:
                empty_counts[bucket] += 1
        else:
            empty_counts["malformed"] += 1
            prediction_counts["malformed"] += 1
    return ids, occurrences, empty_counts, prediction_counts


def _empty_failure_summary(
    records: Iterable[Any], metadata_ids: set[str], status: Mapping[str, Any]
) -> Dict[str, Any]:
    status_by_id: Dict[str, str] = {}
    status_records = status.get("records", [])
    for item in status_records:
        if isinstance(item, Mapping) and item.get("video_id") is not None:
            status_by_id.setdefault(str(item["video_id"]), str(item.get("status", "missing")))
    empty_by_status: Counter = Counter()
    empty_ids: List[str] = []
    for value in records:
        if not isinstance(value, Mapping) or value.get("video_id") is None:
            continue
        predictions = value.get("predictions")
        if isinstance(predictions, list) and not predictions:
            video_id = str(value["video_id"])
            bucket = status_by_id.get(video_id, "status_unknown")
            if video_id not in metadata_ids:
                bucket = "unknown_video_id"
            empty_by_status[bucket] += 1
            empty_ids.append(video_id)
    failed_ids = [
        str(item["video_id"])
        for item in status_records
        if isinstance(item, Mapping)
        and item.get("video_id") is not None
        and str(item.get("status", "")) == "failed"
    ]
    return {
        "empty_prediction_records": len(empty_ids),
        "empty_prediction_ids_sample": empty_ids[:20],
        "empty_by_status": dict(sorted(empty_by_status.items())),
        "failed_status_records": len(failed_ids),
        "failed_status_ids_sample": failed_ids[:20],
        "separation": (
            "available"
            if status.get("available") and not status.get("parse_issues")
            else "unavailable_or_malformed"
        ),
    }


def _validate_output(path: Path, metadata: Mapping[str, Any]) -> Dict[str, Any]:
    records, parse_issues = load_jsonl_records(path)
    # Pass metadata IDs to the helper without making it part of its public API.
    ids, occurrences, empty_counts, prediction_counts = _row_ids(records, set(metadata))
    strict = validate_submission_records(records, metadata, require_complete=True)
    partial = validate_submission_records(records, metadata, require_complete=False)
    status_paths = _jsonl_status_candidates(path)
    status = _read_status(status_paths[0] if status_paths else None)
    run_summary = _read_run_summary(path)
    missing = sorted(set(metadata) - set(ids))
    unknown = sorted(set(ids) - set(metadata))
    duplicate_ids = sorted(video_id for video_id, count in occurrences.items() if count > 1)
    strict_summary = strict.as_dict(include_predictions=False)
    partial_summary = partial.as_dict(include_predictions=False)
    strict_summary.pop("rows", None)
    partial_summary.pop("rows", None)
    strict_issues = strict_summary.pop("issues", [])
    partial_issues = partial_summary.pop("issues", [])
    strict_summary["issues_summary"] = _issue_summary(strict_issues)
    partial_summary["issues_summary"] = _issue_summary(partial_issues)
    all_issues = list(strict.issues) + list(parse_issues)
    if strict.ok and not parse_issues:
        format_status = "PASS_FORMAT_ONLY"
    elif partial.ok and not parse_issues:
        format_status = "PARTIAL_COVERAGE_FORMAT_ONLY"
    else:
        format_status = "FAIL_FORMAT"
    status_ids = {
        str(item["video_id"])
        for item in status.get("records", [])
        if isinstance(item, Mapping) and item.get("video_id") is not None
    }
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "format_status": format_status,
        "ground_truth_used": False,
        "score": None,
        "coverage": {
            "expected_video_count": len(metadata),
            "output_line_count": len(records) + len(parse_issues),
            "output_unique_video_count": len(set(ids)),
            "missing_video_count": len(missing),
            "missing_video_ids_sample": missing[:20],
            "unknown_video_count": len(unknown),
            "unknown_video_ids_sample": unknown[:20],
            "duplicate_video_line_count": len(duplicate_ids),
            "duplicate_video_ids_sample": duplicate_ids[:20],
        },
        "predictions": {
            "valid_prediction_count_strict": strict.valid_prediction_count,
            "valid_prediction_count_partial": partial.valid_prediction_count,
            "known_empty_prediction_videos": empty_counts["known"],
            "unknown_empty_prediction_videos": empty_counts["unknown"],
            "malformed_prediction_rows": empty_counts["malformed"],
            "raw_prediction_count_known": prediction_counts["known"],
            "raw_prediction_count_unknown": prediction_counts["unknown"],
        },
        "strict_validation": strict_summary,
        "partial_validation": partial_summary,
        "parse_issues": parse_issues[:20],
        "issue_summary": _issue_summary(all_issues),
        "status_sidecar": {
            key: value for key, value in status.items() if key != "records"
        },
        "run_summary": run_summary,
        "empty_failure_separation": _empty_failure_summary(records, set(metadata), status),
        "status_coverage": {
            "status_unique_video_count": len(status_ids),
            "output_ids_without_status_count": len(set(ids) - status_ids),
            "status_ids_without_output_count": len(status_ids - set(ids)),
        },
    }


def _discover(root: Path) -> List[Path]:
    return sorted(
        path for path in root.glob("runs/**/predictions.jsonl")
        if path.is_file()
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--predictions", action="append", default=[], help="label=prediction.jsonl; repeatable")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    metadata = load_media_metadata(args.metadata)
    explicit: List[Tuple[str, Path]] = []
    for item in args.predictions:
        if "=" in item:
            label, raw_path = item.split("=", 1)
        else:
            raw_path = item
            label = Path(raw_path).parent.name
        explicit.append((label, Path(raw_path)))
    if explicit:
        candidates = explicit
    else:
        candidates = [(path.parent.name, path) for path in _discover(Path(args.root))]

    outputs: List[Dict[str, Any]] = []
    for label, path in candidates:
        if not path.is_file():
            outputs.append({"label": label, "path": str(path), "format_status": "MISSING", "score": None})
            continue
        result = _validate_output(path, metadata)
        result["label"] = label
        outputs.append(result)

    total_frames = sum(meta.n_frames for meta in metadata.values())
    result = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "acceptance_type": "format_only",
        "official_evaluator": {
            "source_found": False,
            "status": "unavailable",
            "score_computed": False,
            "note": "Official evaluator source/test labels were not available; no official or internal score is claimed here.",
        },
        "metadata": {
            "source": str(args.metadata),
            "is_ground_truth": False,
            "video_count": len(metadata),
            "indexed_frame_count": total_frames,
        },
        "static_review": {
            "script": "/home/inspur/aic_video_work/inference/baseline_qwen3vl.py",
            "status": "PASS_AFTER_VIDEO_METADATA_PATCH",
            "verified_contract": {
                "process_vision_info": "return_video_metadata=True",
                "tuple_split": "(video, metadata) split before processor",
                "processor_kwargs": "video_metadata=list, do_sample_frames=False",
                "source_frame_indices_and_fps": "retained for Qwen3-VL timestamp construction",
            },
            "cpu_processor_regression": {
                "status": "PASS",
                "sampled_frames": 64,
                "source_total_frames": 4500,
                "source_fps": 30.0,
                "source_first_last_frame": [0, 4499],
                "timestamp_span_sec_after_temporal_merge": [1.1833333333, 148.7833333333],
                "missing_metadata_default24_span_sec": [0.0208333333, 2.6041666667],
            },
            "prior_train10_diagnostic": {
                "run": "/home/inspur/aic_video_work/runs/baseline_qwen3vl_train10",
                "warning": "Qwen3VL missing video_metadata default fps=24",
                "videos": 10,
                "predictions": 94,
                "format_or_score_status": "not_accepted",
            },
            "metadata_smoke_after_patch": {
                "run": "/home/inspur/aic_video_work/runs/baseline_qwen3vl_metadata_smoke",
                "status": "PASS_TIME_AXIS",
                "sampling_records": 1,
                "sampled_frames": 64,
                "source_last_frame": 4495,
                "last_timestamp_sec": 149.9831666667,
                "default_fps_warning_observed": False,
            },
        },
        "outputs": outputs,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "output_count": len(outputs), "metadata_videos": len(metadata)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
