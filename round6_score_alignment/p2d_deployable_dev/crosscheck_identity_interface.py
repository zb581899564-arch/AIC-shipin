"""Cross-check inference decode identity and coincident historical P1 outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from p2d_core import load_jsonl, sha256_file

ROOT = Path(__file__).resolve().parents[2]
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"
PINNED = {
    "dev_frames.jsonl": "711fd3c8d0c960957bd519c13654e0f38f53296cda83cc2edb2f182982551c84",
    "p1_predictions.jsonl": "cc2778747c0a7bdab88bea70fabe6dab181c75850bc5cd53936b386dbb4a61d3",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    out = Path(args.evidence_dir).resolve()
    target = out / "identity_interface_crosscheck.json"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite {target}")
    for name, expected in PINNED.items():
        observed = sha256_file(WEAK / name)
        if observed != expected:
            raise RuntimeError(f"protected input changed: {name} {observed}")
    identity = json.loads((out / "source_identity_pts.json").read_text(encoding="utf-8"))
    raw = load_jsonl(out / "raw_inference.jsonl")
    raw_by_key = {(row["video_id"], int(row["source_frame"])): row for row in raw}
    probe_rows = []
    for video in identity["videos"]:
        for probe in video["probe_checks"]:
            key = (video["video_id"], int(probe["source_frame"]))
            inferred = raw_by_key.get(key)
            probe_rows.append({
                "video_id": key[0], "source_frame": key[1],
                "inference_output_present": inferred is not None,
                "matches_sequential_decode": bool(inferred) and inferred.get("decoded_pixel_sha256") == probe.get("sequential_pixel_sha256"),
                "matches_random_seek_decode": bool(inferred) and inferred.get("decoded_pixel_sha256") == probe.get("random_seek_pixel_sha256"),
            })

    frame_by_sample = {row["sample_key"]: row for row in load_jsonl(WEAK / "dev_frames.jsonl")}
    p1_by_key = {}
    for row in load_jsonl(WEAK / "p1_predictions.jsonl"):
        meta = frame_by_sample[row["sample_key"]]
        p1_by_key[(row["video_id"], int(meta["source_frame"]))] = row
    coincidences = []
    for key in sorted(set(raw_by_key) & set(p1_by_key)):
        new, old = raw_by_key[key], p1_by_key[key]
        old_box = [int(v) for v in old["box_xywh"][:3]] if old.get("box_xywh") else None
        coincidences.append({
            "video_id": key[0], "source_frame": key[1],
            "p1_sample_key": old["sample_key"],
            "new_status": new.get("status"), "p1_valid": old.get("output_valid"),
            "box_exact_match": new.get("box_xyw") == old_box,
            "raw_output_exact_match": new.get("raw_output") == old.get("raw_output"),
            "use": "IDENTITY_INTERFACE_CROSSCHECK_ONLY_NOT_COVERAGE_FILL",
        })
    report = {
        "schema": "aic6_p2d_identity_interface_crosscheck_v1",
        "decode_probe_count": len(probe_rows),
        "decode_probe_all_match": all(row["inference_output_present"]
                                      and row["matches_sequential_decode"]
                                      and row["matches_random_seek_decode"] for row in probe_rows),
        "decode_probes": probe_rows,
        "historical_p1_coincident_frames": len(coincidences),
        "historical_p1_box_exact_matches": sum(row["box_exact_match"] for row in coincidences),
        "historical_p1_raw_exact_matches": sum(row["raw_output_exact_match"] for row in coincidences),
        "historical_p1_note": "Coincident P1 rows are cross-checks only and never fill a P2-D frame.",
        "historical_p1_rows": coincidences,
        "protected_input_hashes": PINNED,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "decode_probe_count", "decode_probe_all_match", "historical_p1_coincident_frames",
        "historical_p1_box_exact_matches", "historical_p1_raw_exact_matches")}, indent=2))
    return 0 if report["decode_probe_all_match"] else 6


if __name__ == "__main__":
    raise SystemExit(main())
