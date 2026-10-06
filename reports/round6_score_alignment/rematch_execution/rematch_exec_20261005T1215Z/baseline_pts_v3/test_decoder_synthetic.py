#!/usr/bin/env python3
"""Optional bounded CPU self-test using freshly generated black synthetic clips.

Never reads contest media. Uses existing FFmpeg/FFprobe/Decord only; installs
nothing, exports/displays no frame images, and never changes production code.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from a_contract import sha, write_json
from numeric_source_worker import read_numeric_source
from scan_source_origin import audit_numeric, verify_dependencies
from time_origin_core import probe_indices

HERE = Path(__file__).resolve().parent


def generate(ffmpeg, path, vf=None, offset=None):
    command = [str(ffmpeg), "-nostdin", "-n", "-v", "error", "-f", "lavfi",
               "-i", "color=c=black:s=64x64:r=30:d=2", "-an", "-c:v", "libx264",
               "-bf", "0", "-pix_fmt", "yuv420p", "-video_track_timescale", "16000"]
    if vf:
        command.extend(["-vf", vf, "-vsync", "0"])
    if offset:
        command.extend(["-output_ts_offset", offset])
    command.append(str(path))
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    return command


def registered_row(name, numeric, source, forced_fps=None):
    return {"video_id": name, "source_sha256": sha(source), "source_path": str(source),
            "width": 64, "height": 64, "n_frames": len(numeric["raw_pts_sec"]),
            "fps_num": forced_fps or numeric["ffprobe_fps_num"],
            "fps_den": 1 if forced_fps else numeric["ffprobe_fps_den"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--ffmpeg", type=Path, required=True)
    ap.add_argument("--ffprobe", type=Path, required=True)
    ap.add_argument("--decord-num-threads", type=int, default=0)
    args = ap.parse_args()
    root = args.output_root.resolve()
    if HERE not in root.parents:
        raise ValueError("synthetic evidence must stay inside baseline_pts_v3")
    if root.exists():
        raise FileExistsError("preserve prior synthetic evidence")
    if args.decord_num_threads < 0:
        raise ValueError("invalid Decord worker count")
    for binary in (args.ffmpeg, args.ffprobe):
        if not binary.is_file():
            raise ValueError("existing FFmpeg/FFprobe executable required; no installation")
    production_hashes = verify_dependencies()
    root.mkdir(parents=True)
    records, failures = [], []
    healthy = None
    specs = [("cfr_zero", None, None), ("cfr_origin_046", None, "0.046"),
             ("vfr_gap", "setpts=PTS+if(gte(N\\,30)\\,0.4/TB\\,0)", None)]
    for name, vf, offset in specs:
        record = {"case": name, "pass": False}
        path = root/(name+".mp4")
        try:
            command = generate(args.ffmpeg, path, vf, offset)
            numeric = read_numeric_source(path, args.ffprobe, args.decord_num_threads)
            row = registered_row(name, numeric, path)
            audit = audit_numeric(row, numeric)
            write_json(root/(name+".numeric.json"), numeric)
            record.update(ffmpeg_command=command, source_sha256=sha(path),
                          numeric_sha256=sha(root/(name+".numeric.json")), audit=audit)
            if name == "vfr_gap":
                record["pass"] = (not audit["pass"] and
                                  "NORMALIZED_CFR_ERROR_EXCEEDS_UNCHANGED_ONE_FRAME_TOLERANCE" in audit["failures"])
            else:
                record["pass"] = audit["pass"] and row["n_frames"] == 60
                if name == "cfr_origin_046":
                    record["pass"] = (record["pass"] and
                                      abs(audit["raw_first_pts_sec"]-0.046) <= audit["stream_origin_binding_tolerance_sec"] and
                                      abs(audit["raw_first_pts_sec"]) > audit["one_frame_tolerance_sec"])
                    healthy = (row, numeric) if record["pass"] else None
        except Exception as exc:
            record["exception"] = type(exc).__name__+": "+str(exc)
        if not record["pass"]:
            failures.append(name)
        records.append(record)
        write_json(root/(name+".case.json"), record)
    corrupt = {"case": "bad_non_probe_timestamp", "pass": False}
    if healthy is not None:
        row, numeric = copy.deepcopy(healthy)
        candidate = next(i for i in range(3, row["n_frames"]-3) if i not in probe_indices(row["n_frames"]))
        numeric["decord_timestamps"][candidate][0] += 0.002
        audit = audit_numeric(row, numeric)
        corrupt.update(corrupted_source_frame=candidate, audit=audit,
                       pass_criterion="reject a changed all-frame timestamp outside representative probes")
        corrupt["pass"] = (not audit["pass"] and
                           "DECORD_RAW_OR_SOURCE_RELATIVE_ORIGIN_BINDING_FAILED" in audit["failures"])
        write_json(root/"bad_non_probe_timestamp.numeric.json", numeric)
    else:
        corrupt["exception"] = "healthy real nonzero-origin CFR prerequisite not passed"
    if not corrupt["pass"]:
        failures.append(corrupt["case"])
    records.append(corrupt)
    write_json(root/"bad_non_probe_timestamp.case.json", corrupt)
    receipt = {"schema": "aic_pts_origin_real_decoder_synthetic_cpu_v1",
               "status": "PASS_REAL_DECODER_SYNTHETIC_ONLY" if not failures else "BLOCK_REAL_DECODER_SYNTHETIC",
               "records": records, "failed_cases": failures, "source_code": production_hashes,
               "test_file_sha256": sha(__file__), "ffmpeg_sha256": sha(args.ffmpeg),
               "ffprobe_sha256": sha(args.ffprobe), "contest_media_read": False, "labels_read": False,
               "models_run": False, "GPU_used": False, "images_exported_or_displayed": False,
               "synthetic_black_media_generated": True, "pixels_may_be_decoded_internally": True,
               "decord_num_threads": args.decord_num_threads, "inference_allowed": False}
    write_json(root/"synthetic_decoder_receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "failed_cases": failures,
                      "receipt_sha256": sha(root/"synthetic_decoder_receipt.json")}))
    return 0 if not failures else 4


if __name__ == "__main__":
    raise SystemExit(main())
