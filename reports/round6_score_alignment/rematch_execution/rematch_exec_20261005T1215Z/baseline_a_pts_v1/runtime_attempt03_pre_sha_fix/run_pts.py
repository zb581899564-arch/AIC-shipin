#!/usr/bin/env python3
"""Stage-by-stage A_NATIVE_PTS_COMPAT_V1; supervisor owns GPU admission.

All artifacts are exclusive-create. Rematch execution needs an approved clean
metadata manifest; JSONL role UNKNOWN always blocks before source access.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from a_contract import (ADAPTER_SHA256, compose, keyset, package, read_rows,
                        sha, validate_predictions, write_json, write_rows)
from pts_contract import VARIANT, load_clocks, legacy_manifest, select_frames

HERE = Path(__file__).resolve().parent
CONFIG_SHA256 = "137a60e3efae567794105bac8d2fcb4288c7d1b289ab4ad1d0a81e2ba11c5414"


def verify_vendor():
    lock = json.loads((HERE/"vendor_lock.json").read_text(encoding="utf-8"))
    for item in lock["files"]:
        if sha(HERE/item["path"]) != item["sha256"]:
            raise RuntimeError("frozen vendor source hash mismatch")
    for lock_name in ("snapshot_lock.json", "additional_frozen_dependencies.json", "source_lock.json"):
        locked = json.loads((HERE/lock_name).read_text(encoding="utf-8"))
        for item in locked["files"]:
            if sha(HERE/item["path"]) != item["sha256"]:
                raise RuntimeError("A-PTS source snapshot or production hash mismatch")


def verify_models(config):
    if config.get("adapter_sha256") != ADAPTER_SHA256 or sha(Path(config["adapter"])/"adapter_model.safetensors") != ADAPTER_SHA256:
        raise RuntimeError("P2-T2 adapter identity mismatch")
    for name, expected in config["model_hashes"].items():
        if sha(Path(config["base_model"])/name) != expected:
            raise RuntimeError("4B base model identity mismatch")
    if sha(config["spatial_baseline"]) != config["spatial_baseline_sha256"]:
        raise RuntimeError("frozen native spatial implementation identity mismatch")


def verify_admission(path, manifest_sha256, kind, run_dir, registry_sha256, stage):
    if path is None:
        raise ValueError("GPU stage needs main supervisor resource/admission evidence")
    a = json.loads(Path(path).read_text(encoding="utf-8"))
    expected_stage = "A_PTS_NONTEST_E2E" if kind == "NONTEST_FROZEN8" else "A_PTS_REMATCH426_INFERENCE"
    if (a.get("variant") != VARIANT or a.get("clock_registry_sha256") != registry_sha256 or
            a.get("source_lock_sha256") != sha(HERE/"source_lock.json") or
            a.get("stage") != expected_stage or a.get("authorized") is not True or
            a.get("manifest_sha256") != manifest_sha256 or
            a.get("run_dir") != str(Path(run_dir).resolve()) or
            a.get("resource_preflight_pass") is not True or
            a.get("shared_gpu_queue_approved") is not True or
            a.get("disk_peak_within_80gib") is not True or
            a.get("budget_runner_required") is not True):
        raise ValueError("GPU admission evidence incomplete or refers to another run")
    if not isinstance(a.get("allowed_stages"), list) or stage not in a["allowed_stages"]:
        raise ValueError("A-PTS stage is outside the registered admission scope")
    if stage == "spatial" and a.get("space_inference_admitted") is not True:
        raise ValueError("space inference needs separate admission after actual anchor counts")
    if kind == "REMATCH426":
        import re
        if (a.get("non_test_e2e_pass") is not True or a.get("synthetic_processor_pass") is not True or
                a.get("synthetic_decoder_pass") is not True or
                any(not isinstance(a.get(k), str) or not re.fullmatch(r"[0-9a-f]{64}", a[k]) for k in
                    ("non_test_evidence_sha256", "synthetic_processor_evidence_sha256", "synthetic_decoder_evidence_sha256"))):
            raise ValueError("new A-PTS rematch needs real non-test and synthetic identity acceptance")
    # Registration does not replace the live serialized resource ledger.
    active_path = Path("/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json")
    if os.name != "posix" or not active_path.exists():
        raise ValueError("GPU execution needs the shared serialized resource wrapper on Linux")
    active = json.loads(active_path.read_text(encoding="utf-8"))
    ancestors, pid = set(), os.getpid()
    for _ in range(32):
        ancestors.add(pid)
        if pid <= 1:
            break
        stat = Path(f"/proc/{pid}/stat").read_text()
        pid = int(stat.rsplit(")", 1)[1].split()[1])
    if active.get("child_pid") not in ancestors or active.get("runner_pid") not in ancestors:
        raise ValueError("active GPU reservation belongs to another process")
    return a


def invoke(script, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-B", str(script), *map(str, args)], check=True, env=env)


def exact_selected_metadata(manifest, selected):
    meta = {r["video_id"]: r for r in legacy_manifest(manifest)["records"]}
    for row in selected:
        m = meta.get(str(row["video_id"]))
        if (m is None or row["source_path"] != m["source_path"] or
                row["source_width"] != m["width"] or row["source_height"] != m["height"] or
                row["source_n_frames"] != m["n_frames"] or row["target_ratio_wh"] != m["targetRatioWH"] or
                abs(row["fps"]-m["fps_num"]/m["fps_den"]) > 1e-6 or
                not 0 <= row["source_frame"] < m["n_frames"]):
            raise ValueError("selected frame source contract changed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["preflight", "temporal", "select", "shots", "anchors", "spatial", "compose", "package"], required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--expected-manifest-sha256", required=True)
    ap.add_argument("--config", type=Path, default=HERE/"config_a.json")
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--admission", type=Path)
    ap.add_argument("--clock-registry", type=Path, required=True)
    ap.add_argument("--expected-clock-registry-sha256", required=True)
    ap.add_argument("--static-only", action="store_true")
    args = ap.parse_args()
    if sha(args.manifest) != args.expected_manifest_sha256:
        raise ValueError("manifest identity changed")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clocks = load_clocks(manifest, args.clock_registry, args.expected_clock_registry_sha256)
    metadata = {r["video_id"]: r for r in manifest["records"]}
    projected_manifest = legacy_manifest(manifest)
    verify_vendor()
    if sha(args.config) != CONFIG_SHA256:
        raise ValueError("frozen A configuration changed")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    run = args.run_dir.resolve()
    if os.name == "posix" and not Path("/home/inspur/aic_video_work") in run.parents:
        raise ValueError("Linux outputs must remain under aic_video_work")
    run.mkdir(parents=True, exist_ok=True)
    record_path = run/(args.stage+".stage.json")
    if record_path.exists():
        raise FileExistsError("stage already recorded; use a new run ID")
    p = lambda name: run/name
    temporal, selected, shots = p("temporal.jsonl"), p("selected.jsonl"), p("shots.jsonl")
    requests, outputs = p("anchor_requests.jsonl"), p("anchor_output.jsonl")
    predictions, provenance = p("predictions.jsonl"), p("provenance.jsonl")
    metadata_file = p("metadata.json")
    if not metadata_file.exists():
        write_json(metadata_file, {"records": list(metadata.values()), "errors": []})
    elif json.loads(metadata_file.read_text(encoding="utf-8")).get("records") != list(metadata.values()):
        raise ValueError("run metadata is bound to a different manifest")
    if args.static_only and args.stage != "preflight":
        raise ValueError("static-only is for preflight")
    if args.stage == "preflight":
        if not args.static_only:
            verify_models(config)
            roots = [Path(r).resolve(strict=True) for r in manifest["allowed_source_roots"]]
            for r in metadata.values():
                source = Path(r["source_path"]).resolve(strict=True)
                if not any(root in source.parents for root in roots) or sha(source) != r["source_sha256"]:
                    raise ValueError("real source path/hash mismatch")
        result = {"status": "PASS_STATIC_INPUT_VENDOR" if args.static_only else "PASS_REAL_INPUT_MODEL_IDENTITY",
                  "expected_count": len(metadata), "media_decoded": False}
    elif args.stage == "temporal":
        verify_admission(args.admission, args.expected_manifest_sha256, manifest["kind"], run, args.expected_clock_registry_sha256, "temporal")
        invoke(HERE/"infer_temporal_pts.py", "--manifest", args.manifest,
               "--expected-manifest-sha256", args.expected_manifest_sha256,
               "--config", args.config, "--output", temporal, "--admission", args.admission,
               "--clock-registry", args.clock_registry, "--expected-clock-registry-sha256", args.expected_clock_registry_sha256)
        result = json.loads(p("temporal.jsonl.run.json").read_text(encoding="utf-8"))
    elif args.stage == "select":
        chosen = select_frames(manifest, read_rows(temporal), clocks)
        write_rows(selected, chosen)
        result = {"status": "PASS_EXACT_SELECTION", "selected_frames": len(chosen), "invalid_windows": 0}
    elif args.stage == "shots":
        exact_selected_metadata(manifest, read_rows(selected))
        allowed = [part for root in manifest["allowed_source_roots"] for part in ("--allowed-root", root)]
        invoke(HERE/"detect_shots_pts.py", "--selected", selected,
               "--output", shots, "--summary", p("shots.summary.json"), *allowed,
               "--manifest", args.manifest, "--expected-manifest-sha256", args.expected_manifest_sha256,
               "--clock-registry", args.clock_registry, "--expected-clock-registry-sha256", args.expected_clock_registry_sha256)
        result = json.loads(p("shots.summary.json").read_text(encoding="utf-8"))
    elif args.stage == "anchors":
        exact_selected_metadata(manifest, read_rows(selected))
        invoke(HERE/"vendor/build_anchors.py", "--selected", selected, "--shots", shots,
               "--max-gap", 8, "--output", requests, "--summary", p("anchors.summary.json"))
        result = json.loads(p("anchors.summary.json").read_text(encoding="utf-8"))
    elif args.stage == "spatial":
        verify_admission(args.admission, args.expected_manifest_sha256, manifest["kind"], run, args.expected_clock_registry_sha256, "spatial")
        verify_models(config)
        exact_selected_metadata(manifest, read_rows(selected))
        # Separate process loads the same immutable 4B base WITHOUT time LoRA.
        invoke(HERE/"infer_anchors_pts.py", "--requests", requests,
               "--expected-requests-sha256", sha(requests), "--output", outputs,
               "--manifest", args.manifest, "--expected-manifest-sha256", args.expected_manifest_sha256,
               "--clock-registry", args.clock_registry, "--expected-clock-registry-sha256", args.expected_clock_registry_sha256)
        result = json.loads(p("anchor_output.jsonl.run.json").read_text(encoding="utf-8"))
    elif args.stage == "compose":
        chosen = read_rows(selected)
        exact_selected_metadata(manifest, chosen)
        rows, prov = compose(projected_manifest, chosen, read_rows(shots), read_rows(requests), read_rows(outputs))
        write_rows(predictions, rows)
        write_rows(provenance, prov)
        result = validate_predictions(projected_manifest, rows, keyset(chosen), prov)
        result["status"] = "PASS_COMPLETE_COMPOSITION"
    else:
        chosen, rows, prov = read_rows(selected), read_rows(predictions), read_rows(provenance)
        exact_selected_metadata(manifest, chosen)
        # Recompute complete provenance from anchors, not just format validation.
        rebuilt_rows, rebuilt_prov = compose(projected_manifest, chosen, read_rows(shots), read_rows(requests), read_rows(outputs))
        if rows != rebuilt_rows or prov != rebuilt_prov:
            raise ValueError("candidate changed after complete composition")
        result = validate_predictions(projected_manifest, rows, keyset(chosen), prov)
        if p("candidate_A_PTS.zip").exists():
            raise FileExistsError("candidate already exists")
        pending_zip = p("candidate_A_PTS.PENDING_VALIDATION.zip")
        result.update(package(predictions, pending_zip))
        invoke(HERE/"vendor/independent_validate.py", "--strict-loader-root", HERE/"vendor/frozen_strict_loader",
               "--metadata", metadata_file, "--selected", selected, "--predictions", predictions,
               "--provenance", provenance, "--zip", pending_zip,
               "--report", p("independent_validation.json"))
        pending_zip.rename(p("candidate_A_PTS.zip"))
        result["status"] = "PASS_FORMAT_PROVENANCE_PACKAGE_NOT_OFFICIALLY_SCORED"
    result.update(variant=VARIANT, strict_original_A=False,
                  clock_registry_sha256=args.expected_clock_registry_sha256,
                  source_lock_sha256=sha(HERE/"source_lock.json"),
                  stage=args.stage, manifest_sha256=args.expected_manifest_sha256,
                  config_sha256=sha(args.config), uploaded=False)
    write_json(record_path, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
