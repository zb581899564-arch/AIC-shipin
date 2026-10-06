"""Read-only acceptance check for the completed weak-dev pilot artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


JOBS = ["r6weak_spatial_base", "r6weak_temporal_base", "r6weak_temporal_s2",
        "r6weak_spatial_smoke", "r6weak_spatial_smoke_dev"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    workspace = Path(__file__).resolve().parents[2]
    out = workspace / "reports" / "round6_score_alignment" / "weak_dev_pilot"
    freeze = read(out / "freeze_record.json")
    assert all(digest(out / name) == expected for name, expected in freeze["sha256"].items())
    split = [json.loads(s) for s in (workspace / "reports" / "round6_score_alignment" /
             "training_alignment_20260917" / "weak_split_manifest.jsonl").read_text(
                 encoding="utf-8").splitlines() if s.strip()]
    assert [sum(r["split"] == name for r in split) for name in ("train", "dev", "holdout")] == [372, 82, 64]
    source_splits = {}
    for row in split:
        source_splits.setdefault(row["youtube_id"], set()).add(row["split"])
    assert all(len(value) == 1 for value in source_splits.values())
    dev_pts, smoke_pts = read(out / "dev_pts_gate.json"), read(out / "smoke_pts_gate.json")
    assert dev_pts["status"] == smoke_pts["status"] == "PTS_GATE_PASS"
    assert dev_pts["frames"] == 272 and smoke_pts["frames"] == 16
    assert not dev_pts["failures"] and not smoke_pts["failures"]
    assert dev_pts["manifest_sha256"] == freeze["sha256"]["dev_frames.jsonl"]
    assert smoke_pts["manifest_sha256"] == freeze["sha256"]["smoke_frames.jsonl"]
    spatial = read(out / "spatial_run.json")
    adapter_run = read(out / "smoke_adapter_dev_predictions.run.json")
    base_time = read(out / "temporal_BASE.run.json")
    s2_time = read(out / "temporal_S2.run.json")
    for name, report in (("p1_predictions.jsonl", spatial),
                         ("smoke_adapter_dev_predictions.jsonl", adapter_run),
                         ("temporal_BASE.jsonl", base_time),
                         ("temporal_S2.jsonl", s2_time)):
        assert digest(out / name) == report["output_sha256"], name
    train = read(out / "smoke_train_report.json")
    assert train["loss_finite"] and train["training_rows"] == 16
    assert train["optimizer_steps"] == 20 and train["examples_seen"] == 320
    assert adapter_run["adapter_sha256"] == train["adapter_sha256"]
    assert digest(out / "smoke_adapter" / "adapter_model.safetensors") == train["adapter_sha256"]
    assert (out / "smoke_adapter" / "adapter_config.json").is_file()
    overlap = read(out / "s2_overlap.json")
    assert overlap["dev_rows_with_historical_source_exposure"] == 63
    spatial_metrics = read(out / "weak_spatial_p0_p1.json")
    temporal_metrics = read(out / "weak_temporal_base_s2.json")
    comparison = read(out / "smoke_adapter_comparison.json")
    assert spatial_metrics["frames"] == comparison["frames"] == 272
    assert temporal_metrics["dev_videos"] == 82
    assert comparison["full_training_gate"] == "STOP_KEEP_BASE"
    assert not (out / "holdout_predictions.jsonl").exists()
    resources = [read(out / "resources" / (name + ".resource.json")) for name in JOBS]
    assert all(r["status"] == "completed" and r["exit_code"] == 0 for r in resources)
    for a, b in zip(resources, resources[1:]):
        assert abs(b["prior_charged_seconds"] -
                   (a["prior_charged_seconds"] + a["charged_seconds"])) < 1e-5
    round_gpu = sum(r["charged_seconds"] for r in resources)
    cumulative_gpu = resources[-1]["prior_charged_seconds"] + resources[-1]["charged_seconds"]
    assert round_gpu < 4 * 3600 and cumulative_gpu < 24 * 3600
    summary = {"status": "ACCEPTED_STOP_KEEP_BASE", "input_hashes_match": True,
               "raw_output_hashes_match": True, "pts_gates_pass": True,
               "resource_jobs": len(resources), "new_gpu_seconds": round_gpu,
               "project_gpu_seconds": cumulative_gpu, "project_gpu_hours": cumulative_gpu / 3600,
               "remaining_project_gpu_hours": (24 * 3600 - cumulative_gpu) / 3600,
               "holdout_untouched": True, "source_splits_disjoint": True,
               "adapter_sha256": train["adapter_sha256"],
               "adapter_local_remote_hash_match": True,
               "official_score": None}
    (out / "acceptance.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
