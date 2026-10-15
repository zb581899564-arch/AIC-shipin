"""Read-only validation of Gemini's raw real-frame annotations."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import argparse

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent / "antigravity_label_probe_20261009"
INPUT = PROJECT / "input/real_tvsum_v1"
OUTPUT = PROJECT / "output/real_tvsum_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    global OUTPUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--report", type=Path, default=ROOT / "validation.json")
    args = parser.parse_args()
    OUTPUT = args.output
    manifest_path = INPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    expected = {r["local_index"]: r for r in manifest["frames"]}
    issues, rows, files = [], [], []
    for index in range(8):
        path = OUTPUT / f"batch_{index:02d}.json"
        if not path.is_file():
            issues.append({"file": path.name, "issue": "MISSING_BATCH"})
            continue
        files.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
        try:
            batch = json.loads(path.read_text(encoding="utf-8-sig"))
            batch_rows = batch["frames"]
            if len(batch_rows) != 6:
                issues.append({"file": path.name, "issue": "BATCH_COUNT", "actual": len(batch_rows)})
            for row in batch_rows:
                rows.append(row)
                if row.get("local_index") not in range(index * 6, index * 6 + 6):
                    issues.append({"file": path.name, "issue": "WRONG_BATCH_INDEX", "index": row.get("local_index")})
        except (ValueError, KeyError, TypeError) as exc:
            issues.append({"file": path.name, "issue": "JSON_OR_SCHEMA", "error": str(exc)})
    counts = Counter(r.get("local_index") for r in rows)
    if set(counts) != set(expected) or any(n != 1 for n in counts.values()):
        issues.append({"issue": "FRAME_COVERAGE", "missing": sorted(set(expected) - set(counts)),
                       "extra": [x for x in counts if x not in expected],
                       "duplicate_indices": [x for x, n in counts.items() if n > 1]})
    highlight_counts, crop_state_counts = Counter(), Counter()
    crop_count = valid_crop_count = 0
    pts_errors, boxes = [], []
    for row in rows:
        index = row.get("local_index")
        if index not in expected:
            continue
        source = expected[index]
        if row.get("frame_index") != source["frame_index"]:
            issues.append({"index": index, "issue": "SOURCE_FRAME_IDENTITY"})
        if Path(str(row.get("observed_file", "")).replace("\\", "/")).name != source["file"]:
            issues.append({"index": index, "issue": "OBSERVED_FILENAME"})
        try:
            delta = abs(float(row["pts_seconds"]) - source["pts_seconds"])
            pts_errors.append(delta)
            if not math.isfinite(delta) or delta > 1e-6:
                issues.append({"index": index, "issue": "PTS_VALUE", "error_seconds": delta})
        except (ValueError, KeyError, TypeError):
            issues.append({"index": index, "issue": "PTS_MISSING_OR_INVALID"})
        state = row.get("highlight_state")
        highlight_counts[state] += 1
        if state not in ("KEEP", "NO_HIGHLIGHT", "UNKNOWN"):
            issues.append({"index": index, "issue": "HIGHLIGHT_STATE"})
        for key in ("visible_content", "highlight_reason"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                issues.append({"index": index, "issue": "MISSING_TEXT", "field": key})
        crops = row.get("crops", [])
        if not isinstance(crops, list):
            issues.append({"index": index, "issue": "CROPS_NOT_LIST"})
            continue
        ratios = [tuple(c.get("targetRatioWH", [])) for c in crops]
        if Counter(ratios) != Counter({(16, 9): 1, (9, 16): 1}):
            issues.append({"index": index, "issue": "CROP_RATIO_COVERAGE", "ratios": ratios})
        for crop in crops:
            crop_count += 1
            crop_state = crop.get("state")
            crop_state_counts[crop_state] += 1
            ratio = crop.get("targetRatioWH", [])
            box = crop.get("box_xyw")
            if crop_state == "UNKNOWN":
                if box is not None:
                    issues.append({"index": index, "ratio": ratio, "issue": "UNKNOWN_BOX_NOT_NULL"})
                continue
            if crop_state != "CROP" or not isinstance(box, list) or len(box) != 3:
                issues.append({"index": index, "ratio": ratio, "issue": "CROP_STATE_OR_BOX"})
                continue
            try:
                if any(isinstance(v, bool) for v in box) or tuple(ratio) not in ((16, 9), (9, 16)):
                    raise ValueError("Invalid numeric box or ratio")
                x, y, w = [Fraction(str(v)) for v in box]
                h = w * ratio[1] / ratio[0]
                valid = x >= 0 and y >= 0 and w > 0 and x + w <= source["width"] and y + h <= source["height"]
                boxes.append({"index": index, "ratio": ratio, "xywh": [float(x), float(y), float(w), float(h)], "valid": valid})
                if valid:
                    valid_crop_count += 1
                else:
                    issues.append({"index": index, "ratio": ratio, "issue": "OUT_OF_BOUNDS", "xywh": boxes[-1]["xywh"]})
            except (ValueError, TypeError, ZeroDivisionError) as exc:
                issues.append({"index": index, "ratio": ratio, "issue": "BOX_NUMBER", "error": str(exc)})
    input_unchanged = all(sha(INPUT / r["file"]) == r["png_sha256"] for r in expected.values())
    manifest_unchanged = sha(manifest_path) == sha(ROOT / "input/manifest.json")
    if not input_unchanged or not manifest_unchanged:
        issues.append({"issue": "INPUT_HASH_CHANGED"})
    summary_path = OUTPUT / "summary.json"
    summary = None
    if summary_path.is_file():
        files.append({"path": str(summary_path), "bytes": summary_path.stat().st_size, "sha256": sha(summary_path)})
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
            for key, actual in (("observed_count", 48), ("output_frame_count", len(rows)), ("crops_count", crop_count),
                                ("crop_unknown_count", crop_state_counts["UNKNOWN"])):
                if summary.get(key) != actual:
                    issues.append({"issue": "SUMMARY_MISMATCH", "field": key, "actual": actual, "declared": summary.get(key)})
            declared_counts = summary.get("highlight_state_counts", {})
            if not isinstance(declared_counts, dict) or Counter(declared_counts) != highlight_counts:
                issues.append({"issue": "SUMMARY_MISMATCH", "field": "highlight_state_counts",
                               "actual": dict(highlight_counts), "declared": declared_counts})
            if summary.get("source_id") != manifest["source_id"]:
                issues.append({"issue": "SUMMARY_SOURCE_ID"})
            observed = summary.get("observed_files", [])
            expected_files = Counter(r["file"] for r in expected.values())
            if not isinstance(observed, list) or Counter(Path(str(v).replace("\\", "/")).name for v in observed) != expected_files:
                issues.append({"issue": "SUMMARY_OBSERVED_FILES"})
        except (ValueError, TypeError) as exc:
            issues.append({"issue": "SUMMARY_JSON", "error": str(exc)})
    else:
        issues.append({"issue": "MISSING_SUMMARY"})
    report = {"status": "PASS_RAW_FRAME_IDENTITY_AND_CROP_GEOMETRY" if not issues else "RAW_ANNOTATION_ISSUES_FOUND",
              "utc": datetime.now(timezone.utc).isoformat(), "source_id": manifest["source_id"],
              "frames_expected": 48, "frames_found": len(rows), "unique_frame_indices": len(counts),
              "crop_tasks": crop_count, "valid_nonempty_crops": valid_crop_count,
              "highlight_state_counts": dict(highlight_counts), "crop_state_counts": dict(crop_state_counts),
              "maximum_pts_error_seconds": max(pts_errors, default=None),
              "pts_serialization_tolerance_seconds": 1e-6, "input_png_hashes_unchanged": input_unchanged,
              "manifest_hash_unchanged": manifest_unchanged, "raw_files": files, "issues": issues, "boxes": boxes,
              "semantic_accuracy": "NOT_MEASURED_NO_INDEPENDENT_REFERENCE",
              "per_file_visual_tool_reads": "VERIFY_SEPARATELY_FROM_TOOL_TRANSCRIPT"}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("raw_files", "boxes")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
