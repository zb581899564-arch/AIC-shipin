#!/usr/bin/env python3
"""Offline synthetic P1b export -> Python validator -> read-only P1a consumer."""
from __future__ import annotations

import json
from pathlib import Path

import frame_server
from run_fix_validation import p1a_consumption
from validate_exports import validate_export

ROOT = Path(__file__).resolve().parents[2]
P1B = Path(__file__).resolve().parent
OUT = ROOT / "reports/round6_score_alignment/phase1b_fix2"
MANIFEST = ROOT / "reports/round6_score_alignment/phase1b_fix/ui_e2e/synthetic_manifest.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    s = manifest["samples"][0]
    frame_server.load_samples([MANIFEST])
    info = frame_server.decode_frame(frame_server.SAMPLES[s["sample_id"]], 64)["info"]
    loc = {"method": "decoded_frame", "frame": 64, "decoded_index": info["index"],
           "decoded_pts_sec": info["pts_sec"], "time_base_sec": info["time_base_sec"],
           "image_sha256": info["sha256"], "sample_id": s["sample_id"],
           "media_sha256": s["sha256_local"], "request_version": 1,
           "estimated_error_frames": 0}
    export = {
        "schema": "p1b_annotation_export_v2", "core_version": "p1b_core_v2",
        "interval_semantics": "half_open_end_exclusive",
        "seconds_semantics": "nominal_frame_over_manifest_fps_not_decoded_pts",
        "sample_id": s["sample_id"],
        "media": {"sha256": s["sha256_local"], "target_ratio_wh": s["target_ratio_wh"]},
        "annotation_status": "HAS_HIGHLIGHT", "confirm_no_highlight": False,
        "intervals": [{"start_frame": 64, "end_frame_exclusive": 65,
                       "start_sec": 64 / s["fps"], "end_sec": 65 / s["fps"],
                       "start_provenance": loc,
                       "end_provenance": dict(loc, derived="end_frame_exclusive = last_kept_frame + 1")}],
        "keyframes": [{"frame": 64, "box_xyw": [30, 20, 200], "provenance": loc}],
        "identity": {"annotator": "OFFLINE_SYNTHETIC_INTERFACE_FIXTURE"},
        "exportable_as_reference": True,
    }
    path = OUT / "offline_synthetic_export.json"
    path.write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verdict = validate_export(export, manifest)
    a = p1a_consumption(path, manifest, universe=["S01"], label="synthetic sparse only")
    b = p1a_consumption(path, manifest, universe=["S01", "S02"],
                        label="synthetic sparse plus unannotated")
    result = {"run_id": "round6_p1b_fix2_20260917T0951Z",
              "scope": "programmatic synthetic interface fixture, not browser download or human label",
              "python_validator": {"valid": verdict["valid"], "problems": verdict["problems"]},
              "p1a_sparse_only": a, "p1a_with_unannotated": b}
    (OUT / "offline_consumer_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"validator": verdict["valid"], "sparse": a["status"],
                      "unannotated": b["status"]}))
    return 0 if (verdict["valid"] and a["status"] == "SPARSE_DIAGNOSTIC" and
                 b["status"] == "NOT_COMPUTABLE" and a["score"] is None and
                 b["score"] is None) else 2


if __name__ == "__main__":
    raise SystemExit(main())
