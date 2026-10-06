"""Build the P2-T2-selected source-frame manifest for the frozen P2-D videos."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from p2j_core import read_jsonl, selected_source_frames, sha256_file, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p2d-selected", type=Path, required=True)
    parser.add_argument("--p2t-dev", type=Path, required=True)
    parser.add_argument("--p2t-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite joint slice")
    p2d = read_jsonl(args.p2d_selected)
    frozen_ids = sorted({r["video_id"] for r in p2d})
    if len(frozen_ids) != 8:
        raise ValueError("expected the frozen eight-video P2-D slice")
    metadata = {}
    for row in p2d:
        item = {k: row[k] for k in ("video_id", "youtube_id", "source_path", "source_fps",
                                     "source_width", "source_height", "target_ratio_wh",
                                     "clip_start_sec", "clip_end_sec")}
        if row["video_id"] in metadata and metadata[row["video_id"]] != item:
            raise ValueError("inconsistent P2-D metadata")
        metadata[row["video_id"]] = item
    dev = {r["video_id"]: r for r in read_jsonl(args.p2t_dev)}
    predictions = {r["video_id"]: r for r in read_jsonl(args.p2t_output)}
    rows = []
    per_video = []
    for video_id in frozen_ids:
        label, prediction, meta = dev[video_id], predictions[video_id], metadata[video_id]
        if not prediction.get("output_valid") or prediction.get("parsed_segments") is None:
            raise ValueError(f"invalid P2-T2 output for frozen video {video_id}")
        if label["source_path"] != meta["source_path"]:
            raise ValueError("source identity mismatch")
        frames = selected_source_frames(label["clip_start_sec"], label["clip_end_sec"],
                                        float(meta["source_fps"]),
                                        prediction["parsed_segments"])
        if not frames:
            raise ValueError(f"empty P2-T2 selection for {video_id}")
        for frame in frames:
            record = dict(meta)
            record["source_frame"] = frame
            record["temporal_source"] = "P2T2_FINAL_ADAPTER"
            record["request_key"] = f"{video_id}#src{frame}"
            canonical = json.dumps({k: record[k] for k in sorted(record) if k != "request_sha256"},
                                   ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            record["request_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            rows.append(record)
        per_video.append({"video_id": video_id, "youtube_id": meta["youtube_id"],
                          "segments": prediction["parsed_segments"], "selected_frames": len(frames),
                          "first_frame": frames[0], "last_frame": frames[-1]})
    write_jsonl(args.output, rows)
    summary = {
        "status": "P2T2_JOINT_SLICE_PREPARED",
        "p2d_selected_sha256": sha256_file(args.p2d_selected),
        "p2t_dev_sha256": sha256_file(args.p2t_dev),
        "p2t_output_sha256": sha256_file(args.p2t_output),
        "output_sha256": sha256_file(args.output),
        "videos": len(frozen_ids), "source_groups": len({metadata[v]["youtube_id"] for v in frozen_ids}),
        "selected_frames": len(rows), "per_video": per_video,
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
