"""Strictly validate 174 official-format rows and build a single-file ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.zip.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite package")
    metadata = {str(x["video_id"]): x for x in
                json.loads(args.metadata.read_text(encoding="utf-8"))["records"]}
    issues, seen, total = [], set(), 0
    lines = [x for x in args.predictions.read_text(encoding="utf-8").splitlines() if x.strip()]
    for line_number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except Exception as exc:
            issues.append({"line": line_number, "code": "BAD_JSON", "detail": str(exc)})
            continue
        vid = row.get("video_id")
        if not isinstance(vid, str) or vid not in metadata or vid in seen:
            issues.append({"line": line_number, "code": "BAD_VIDEO_ID", "detail": vid})
            continue
        seen.add(vid)
        meta = metadata[vid]
        ratio = [int(x) for x in str(meta["targetRatioWH"]).split()]
        if row.get("targetRatioWH") != ratio or not isinstance(row.get("predictions"), list):
            issues.append({"line": line_number, "code": "BAD_ROW_CONTRACT", "detail": vid})
            continue
        frames = set()
        for item in row["predictions"]:
            total += 1
            frame, box = item.get("frame"), item.get("bboxes")
            if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame < int(meta["n_frames"]):
                issues.append({"line": line_number, "code": "BAD_FRAME", "detail": f"{vid}:{frame}"})
                continue
            if frame in frames:
                issues.append({"line": line_number, "code": "DUPLICATE_FRAME", "detail": f"{vid}:{frame}"})
            frames.add(frame)
            if (not isinstance(box, list) or len(box) != 3 or
                    any(isinstance(x, bool) or not isinstance(x, int) for x in box)):
                issues.append({"line": line_number, "code": "BAD_BOX", "detail": f"{vid}:{frame}"})
                continue
            x, y, width = box
            crop_height = width * ratio[1] / ratio[0]
            if not (width > 0 and x >= 0 and y >= 0 and x + width <= int(meta["width"])
                    and math.isfinite(crop_height) and crop_height > 0
                    and y + crop_height <= int(meta["height"]) + 1e-7):
                issues.append({"line": line_number, "code": "ILLEGAL_BOX", "detail": f"{vid}:{frame}:{box}"})
    if len(lines) != 174 or seen != set(metadata):
        issues.append({"code": "VIDEO_SET_MISMATCH", "detail": {"lines": len(lines),
                                                                    "seen": len(seen)}})
    if issues:
        report = {"status": "FAIL_STRICT_FORMAT", "issues": issues, "uploaded": False}
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 5
    args.zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.zip, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        archive.write(args.predictions, arcname="predictions.jsonl")
    with zipfile.ZipFile(args.zip, "r") as archive:
        names = archive.namelist()
        extracted = archive.read("predictions.jsonl")
    report = {
        "status": "PASS_STRICT_FORMAT_AND_PACKAGE", "official_status": "NOT_SCORED_NOT_UPLOADED",
        "video_records": 174, "prediction_frames": total, "issues": [],
        "ratios": {"16:9": sum(str(x["targetRatioWH"]) == "16 9" for x in metadata.values()),
                   "9:16": sum(str(x["targetRatioWH"]) == "9 16" for x in metadata.values())},
        "archive_names": names, "archive_single_file": names == ["predictions.jsonl"],
        "roundtrip_matches": hashlib.sha256(extracted).hexdigest() == sha(args.predictions),
        "predictions_sha256": sha(args.predictions), "zip_sha256": sha(args.zip),
        "zip_bytes": args.zip.stat().st_size, "uploaded": False,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
