"""Synthetic metadata-only fixtures; not competition or weak-label data."""
from __future__ import annotations
import json
from fractions import Fraction
from pathlib import Path
from a_contract import sha, write_json
from pts_contract import BRANCH_CFR, BRANCH_NATIVE


def make_fixture(root, native_ids=(), kind="NONTEST_FROZEN8"):
    count = 8 if kind == "NONTEST_FROZEN8" else 426
    rows, records = [], []
    registry_path = root/"clock_registry.json"
    for i in range(count):
        vid = str(i)
        native = vid in set(native_ids)
        n, fps, origin = 65, 30, 4140
        tick = Fraction(1, 90000)
        ticks = [origin+j*3000+(18000 if native and j >= 33 else 0) for j in range(n)]
        ends = [t+3000 for t in ticks]
        relative = [(t-origin)*tick for t in ticks]
        duration = (ends[-1]-origin)*tick if native else Fraction(n, fps)
        row = {"video_id": vid, "source_group": "synthetic_group_"+vid,
               "source_path": "/synthetic_media/"+vid+".mp4", "source_sha256": str(i%10)*64,
               "width": 64, "height": 64, "n_frames": n, "fps_num": fps, "fps_den": 1,
               "targetRatioWH": [9,16], "scope_start_sec": 0.0, "scope_end_sec": float(duration),
               "clock_branch": BRANCH_NATIVE if native else BRANCH_CFR, "clock_record_id": vid}
        arrays = {"schema": "aic_source_clock_arrays_v1", "video_id": vid,
                  "source_sha256": row["source_sha256"], "n_frames": n, "raw_time_base": str(tick),
                  "raw_first_pts_ticks": origin, "native_pts_ticks": ticks,
                  "source_relative_pts": [float(t) for t in relative],
                  "source_relative_pts_rational": [str(t) for t in relative],
                  "native_frame_end_pts_ticks": ends if native else None}
        path = root/(vid+".clock_arrays.json")
        write_json(path, arrays)
        records.append({"video_id": vid, "source_sha256": row["source_sha256"], "n_frames": n,
                        "fps_num": fps, "fps_den": 1, "identity_pass": True, "cfr_eligible": not native,
                        "native_clock_usable": native, "raw_time_base": str(tick), "raw_first_pts_ticks": origin,
                        "decord_clock_mode": "SOURCE_RELATIVE_PTS", "duration_seconds": float(duration),
                        "native_end_sec": float(duration) if native else None,
                        "terminal_evidence": {"kind": "NATIVE_LAST_FRAME_PACKET_DURATION" if native else "LEGACY_CFR_N_DIV_FPS"},
                        "decord_binding": {"start_pass": True, "end_pass": native,
                                           "legacy_interval_pass": not native, "float_dtype": "float32"},
                        "clock_arrays": {"path": str(path), "sha256": sha(path)}, "failures": []})
        rows.append(row)
    registry = {"schema": "aic_source_clock_registry_v4", "kind": kind, "expected_count": count,
                "input_manifest_sha256": "e"*64, "all_identity_pass": True, "all_sources_usable": True,
                "failed_video_ids": [], "inference_allowed": False, "records": records}
    write_json(registry_path, registry)
    manifest = {"schema": "aic_rematch_A_input_v2", "kind": kind, "expected_count": count,
                "input_contract": {"status": "APPROVED_METADATA_ONLY", "data_use_evidence": "SYNTHETIC_ONLY",
                                   "target_ratio_evidence": "SYNTHETIC_ONLY", "metadata_role_evidence": "SYNTHETIC_ONLY",
                                   "contest_jsonl_values_used": False},
                "input_manifest_sha256": "e"*64, "clock_registry": {"path": str(registry_path), "sha256": sha(registry_path)},
                "allowed_source_roots": ["/synthetic_media"], "records": rows}
    return manifest, registry, registry_path


def temporal_for(manifest, clocks):
    from pts_contract import window_schedule, BRANCH_NATIVE
    output = []
    for row in manifest["records"]:
        clock = clocks[row["video_id"]]
        windows = []
        for start, end in window_schedule(row, manifest["kind"], clock):
            window = {"start_sec": start, "end_sec": end, "output_valid": True, "status": "MODEL_OK",
                      "parse_errors": [], "parsed_segments": [[0.0, end-start]]}
            if clock["branch"] == BRANCH_NATIVE:
                window["clock_record_sha256"] = clock["clock_record_sha256"]
            windows.append(window)
        output.append({"video_id": row["video_id"], "n_frames": row["n_frames"],
                       "targetRatioWH": row["targetRatioWH"], "video_path": row["source_path"],
                       "fps": row["fps_num"]/row["fps_den"], "windows": windows})
    return output
