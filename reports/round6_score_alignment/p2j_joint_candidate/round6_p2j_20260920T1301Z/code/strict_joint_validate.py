"""Independent replay of a P2-J prediction file through the frozen strict loader."""
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
from p2j_core import canonical_ratio, read_jsonl, sha256_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--source-identity", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("refusing to overwrite strict validation")
    selected = read_jsonl(args.selected)
    identity = json.loads(args.source_identity.read_text(encoding="utf-8"))
    media = {row["video_id"]: row["metadata"] for row in identity["videos"]}
    by_video = {}
    for row in selected:
        by_video.setdefault(row["video_id"], []).append(row)
    ratios = {video_id: canonical_ratio(rows[0]["target_ratio_wh"])
              for video_id, rows in by_video.items()}
    if any(any(canonical_ratio(row["target_ratio_wh"]) != ratios[video_id] for row in rows)
           for video_id, rows in by_video.items()):
        raise ValueError("one video has inconsistent target ratios")
    index = {
        video_id: {"video_id": video_id, "targetRatioWH": ratios[video_id],
                   "width": int(rows[0]["source_width"]), "height": int(rows[0]["source_height"]),
                   "n_frames": int(media[video_id]["n_frames"])}
        for video_id, rows in by_video.items()
    }
    loaded = load_predictions(args.predictions, index)
    expected = {(r["video_id"], int(r["source_frame"])) for r in selected}
    actual = {(video_id, frame) for video_id, frames in loaded.rows.items() for frame in frames}
    lines = read_jsonl(args.predictions)
    ids = [r.get("video_id") for r in lines]
    record_ok = len(ids) == len(set(ids)) == len(index) and set(ids) == set(index)
    ratio_ok = all(r.get("targetRatioWH") == ratios.get(r.get("video_id")) for r in lines)
    ok = loaded.ok and expected == actual and record_ok and ratio_ok
    report = {
        "status": "PASS_STRICT_FORMAT" if ok else "FAIL_STRICT_FORMAT",
        "official_status": "NOT_OFFICIAL_SCORE",
        "selected_sha256": sha256_file(args.selected),
        "source_identity_sha256": sha256_file(args.source_identity),
        "predictions_sha256": sha256_file(args.predictions),
        "strict_loader_ok": loaded.ok, "issues": loaded.validation["issues"],
        "exact_selected_key_set": expected == actual, "video_records_ok": record_ok,
        "target_ratio_ok": ratio_ok, "expected_frames": len(expected),
        "prediction_frames": sum(loaded.n_pred_by_video.values()),
        "duplicate_frames": sum(loaded.duplicate_frames.values()),
        "missing": len(expected - actual), "extra": len(actual - expected),
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 5


if __name__ == "__main__":
    raise SystemExit(main())
