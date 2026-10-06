"""Read source container presentation timestamps for frozen training sample frames."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()


def main(manifest_path: str, output_path: str):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    rows = []
    for sample in manifest:
        source = Path(sample["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents:
            raise ValueError("source outside training root")
        wanted = {f["source_frame_estimate"]: f for f in sample["frames"]}
        p = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "frame=best_effort_timestamp_time",
                            "-of", "csv=p=0", str(source)], capture_output=True,
                           text=True, timeout=120, check=True)
        pts = []
        for line in p.stdout.splitlines():
            token = line.strip().split(",")[0]
            if token and token != "N/A":
                pts.append(float(token))
        for n, item in wanted.items():
            if n >= len(pts):
                raise RuntimeError(f"frame {n} outside actual decoded PTS {len(pts)}")
            rows.append({"row_index": sample["row_index"], "video_id": sample["video_id"],
                         "mapped_source_frame": n, "mapped_source_time_sec": item["source_time_sec"],
                         "source_pts_sec": pts[n],
                         "abs_time_difference_sec": abs(pts[n] - item["source_time_sec"])})
        print(sample["video_id"], flush=True)
    Path(output_path).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
