"""Independent serialized-output replay through the frozen P2 strict loader."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P2 = ROOT / "round6_score_alignment/p2_joint_coverage"
if str(P2) not in sys.path:
    sys.path.insert(0, str(P2))

from aic6.scoring import load_predictions  # noqa: E402
from p2d_core import load_jsonl, sha256_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    out = Path(args.evidence_dir).resolve()
    target = out / "strict_format_validation.json"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite {target}")
    requests = load_jsonl(out / "inference_requests.jsonl")
    identity = json.loads((out / "source_identity_pts.json").read_text(encoding="utf-8"))
    media = {row["video_id"]: row["metadata"] for row in identity["videos"]}
    by_video = {}
    for row in requests:
        by_video.setdefault(row["video_id"], []).append(row)
    index = {
        video_id: {
            "video_id": video_id,
            "targetRatioWH": [9.0, 16.0],
            "width": int(rows[0]["source_width"]),
            "height": int(rows[0]["source_height"]),
            "n_frames": int(media[video_id]["n_frames"]),
        }
        for video_id, rows in by_video.items()
    }
    expected = {(row["video_id"], int(row["source_frame"])) for row in requests}
    arms = {}
    all_ok = True
    for arm, filename in (("qwen", "qwen_composed_dev.jsonl"),
                          ("center", "center_composed_dev.jsonl")):
        path = out / filename
        loaded = load_predictions(path, index)
        keys = {(video_id, frame) for video_id, frames in loaded.rows.items()
                for frame in frames}
        line_rows = load_jsonl(path)
        ids = [row.get("video_id") for row in line_rows]
        ratio_ok = all(row.get("targetRatioWH") == [9, 16] for row in line_rows)
        exact = keys == expected
        video_records_ok = len(ids) == len(index) and len(set(ids)) == len(index) \
            and set(ids) == set(index)
        ok = loaded.ok and exact and video_records_ok and ratio_ok
        all_ok = all_ok and ok
        arms[arm] = {
            "path": filename,
            "sha256": sha256_file(path),
            "strict_loader_ok": loaded.ok,
            "issues": loaded.validation["issues"],
            "exact_selected_key_set": exact,
            "video_records_ok": video_records_ok,
            "target_ratio_ok": ratio_ok,
            "prediction_count": sum(loaded.n_pred_by_video.values()),
            "duplicate_frame_count": sum(loaded.duplicate_frames.values()),
            "ok": ok,
        }
    report = {
        "schema": "aic6_p2d_strict_format_validation_v1",
        "status": "PASS_STRICT_FORMAT" if all_ok else "FAIL_STRICT_FORMAT",
        "official_status": "NOT_OFFICIAL_SCORE",
        "expected_videos": len(index),
        "expected_selected_frames": len(expected),
        "arms": arms,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all_ok else 5


if __name__ == "__main__":
    raise SystemExit(main())
