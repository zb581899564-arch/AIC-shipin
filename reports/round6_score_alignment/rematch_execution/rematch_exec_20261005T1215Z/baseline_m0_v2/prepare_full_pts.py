#!/usr/bin/env python3
"""Separate automatic source-PTS identity gate; no image exports/models/labels.

Preserves original source bytes, source IDs and A's CFR conversion. An ambiguous
source blocks instead of adapting timing rules to contest content.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from a_contract import sha, validate_manifest, write_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--expected-manifest-sha256", required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--ffprobe", type=Path, default=Path("/home/inspur/anaconda3/envs/Andy/bin/ffprobe"))
    args = ap.parse_args()
    if sha(args.manifest) != args.expected_manifest_sha256:
        raise ValueError("manifest identity changed")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    if manifest["kind"] != "REMATCH426":
        raise ValueError("only registered rematch sources allowed here")
    root = args.output_root.resolve()
    if args.output_root.exists():
        raise FileExistsError("preserve previous PTS evidence; use a new output root")
    if sys.platform.startswith("linux") and not Path("/home/inspur/aic_video_work") in root.parents:
        raise ValueError("PTS outputs must stay under aic_video_work")
    root.mkdir(parents=True)
    records, failed = [], False
    for index, r in enumerate(manifest["records"], 1):
        if sha(r["source_path"]) != r["source_sha256"]:
            raise ValueError("source byte identity changed")
        output = root/(r["video_id"]+".pts.tsv")
        fps, count, first, previous, maximum = r["fps_num"]/r["fps_den"], 0, None, None, 0.0
        monotonic, numeric = True, True
        with output.open("x", encoding="utf-8") as stream:
            proc = subprocess.Popen([str(args.ffprobe), "-v", "error", "-select_streams", "v:0", "-show_frames",
                                     "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0",
                                     r["source_path"]], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            try:
                for line in proc.stdout:
                    value = line.strip().split(",", 1)[0]
                    if not value:
                        continue
                    try:
                        pts = float(value)
                    except ValueError:
                        numeric = False
                        break
                    if not math.isfinite(pts):
                        numeric = False
                        break
                    first = pts if first is None else first
                    monotonic = monotonic and (previous is None or pts > previous)
                    err = abs((pts-first)-count/fps)
                    maximum = max(maximum, err)
                    stream.write(f"{count}\t{pts:.9f}\n")
                    count, previous = count+1, pts
                if not numeric:
                    proc.terminate()
                code = proc.wait(timeout=60)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=30)
        tolerance = 1/fps+1e-6  # Existing source-frame identity tolerance, not quality tuning.
        ok = code == 0 and numeric and monotonic and count == r["n_frames"] and maximum <= tolerance and first is not None and abs(first) <= tolerance
        records.append({"video_id": r["video_id"], "source_sha256": r["source_sha256"], "pts_count": count,
                        "pts_monotonic": monotonic, "pts_numeric": numeric, "first_pts_sec": first,
                        "max_cfr_error_sec": maximum, "one_frame_tolerance_sec": tolerance,
                        "pts_file_sha256": sha(output), "pass": ok})
        print(f"PTS identity {index}/426 pass={ok}", flush=True)
        if not ok:
            failed = True
            break
    report = {"status": "BLOCK_SOURCE_PTS_IDENTITY" if failed else "PASS_CFR_WITH_LEGACY_ONE_FRAME_TOLERANCE",
              "input_manifest_sha256": args.expected_manifest_sha256, "records": records,
              "media_images_exported_or_displayed": False, "ffprobe_frame_metadata_scan": True,
              "models_run": False, "labels_read": False}
    write_json(root/"pts_receipt.json", report)
    if not failed:
        manifest["input_contract"]["source_pts_status"] = report["status"]
        manifest["input_contract"]["source_pts_evidence"] = str(root/"pts_receipt.json")+" SHA256 "+sha(root/"pts_receipt.json")
        write_json(root/"clean_manifest_426_pts.json", manifest)
        print("PTS-manifest SHA256", sha(root/"clean_manifest_426_pts.json"), flush=True)
    return 4 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
