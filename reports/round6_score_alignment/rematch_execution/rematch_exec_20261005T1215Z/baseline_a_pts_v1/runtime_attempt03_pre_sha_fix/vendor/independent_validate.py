"""Second, independent validation pass using the frozen P1a/P2 strict loader."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata_ratio(value) -> list[int]:
    values = value if isinstance(value, list) else str(value).split()
    return [int(values[0]), int(values[1])]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-loader-root", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("refusing to overwrite independent validation")
    sys.path.insert(0, str(args.strict_loader_root))
    from aic6.scoring import load_predictions  # type: ignore

    meta_rows = json.loads(args.metadata.read_text(encoding="utf-8"))["records"]
    index = {
        str(row["video_id"]): {
            "video_id": str(row["video_id"]),
            "targetRatioWH": metadata_ratio(row["targetRatioWH"]),
            "width": int(row["width"]),
            "height": int(row["height"]),
            "n_frames": int(row["n_frames"]),
        }
        for row in meta_rows
    }
    selected = read_jsonl(args.selected)
    predictions = read_jsonl(args.predictions)
    provenance = read_jsonl(args.provenance)
    loaded = load_predictions(args.predictions, index)
    expected = {(str(row["video_id"]), int(row["source_frame"])) for row in selected}
    actual = {(video_id, frame) for video_id, frames in loaded.rows.items() for frame in frames}
    predicted_boxes = {
        (str(row["video_id"]), int(item["frame"])): item["bboxes"]
        for row in predictions for item in row["predictions"]
    }
    provenance_boxes = {
        (str(row["video_id"]), int(row["source_frame"])): row["box_xyw"]
        for row in provenance
    }
    ids = [str(row.get("video_id")) for row in predictions]
    ratios_ok = all(row.get("targetRatioWH") == index[str(row.get("video_id"))]["targetRatioWH"]
                    for row in predictions if str(row.get("video_id")) in index)
    ordered = all([item["frame"] for item in row["predictions"]] ==
                  sorted(item["frame"] for item in row["predictions"])
                  for row in predictions)
    with zipfile.ZipFile(args.zip, "r") as archive:
        archive_names = archive.namelist()
        archived = archive.read("predictions.jsonl") if archive_names == ["predictions.jsonl"] else b""
    checks = {
        "strict_loader_ok": loaded.ok,
        "video_record_set_exact": len(ids) == len(set(ids)) == len(index) and set(ids) == set(index),
        "selected_key_set_exact": expected == actual,
        "ratio_fields_exact": ratios_ok,
        "frames_sorted": ordered,
        "provenance_key_set_exact": set(provenance_boxes) == expected,
        "provenance_boxes_match_predictions": provenance_boxes == predicted_boxes,
        "provenance_all_legal": all(row.get("legal") is True for row in provenance),
        "provenance_sources_allowed": all(row.get("spatial_source") in
                                          {"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}
                                          for row in provenance),
        "archive_single_file": archive_names == ["predictions.jsonl"],
        "archive_roundtrip_exact": hashlib.sha256(archived).hexdigest() == sha256(args.predictions),
    }
    ok = all(checks.values()) and not loaded.validation["issues"]
    scoring_path = args.strict_loader_root / "aic6" / "scoring.py"
    report = {
        "status": "PASS_INDEPENDENT_STRICT_VALIDATION" if ok else "FAIL_INDEPENDENT_STRICT_VALIDATION",
        "official_status": "NOT_SCORED_NOT_UPLOADED",
        "checks": checks,
        "strict_loader_issues": loaded.validation["issues"],
        "video_records": len(predictions),
        "expected_frames": len(expected),
        "prediction_frames": sum(loaded.n_pred_by_video.values()),
        "duplicate_frames": sum(loaded.duplicate_frames.values()),
        "missing": len(expected - actual),
        "extra": len(actual - expected),
        "ratios": {
            "16:9": sum(row["targetRatioWH"] == [16, 9] for row in predictions),
            "9:16": sum(row["targetRatioWH"] == [9, 16] for row in predictions),
        },
        "strict_loader_sha256": sha256(scoring_path),
        "predictions_sha256": sha256(args.predictions),
        "provenance_sha256": sha256(args.provenance),
        "zip_sha256": sha256(args.zip),
        "archive_names": archive_names,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 5


if __name__ == "__main__":
    raise SystemExit(main())
