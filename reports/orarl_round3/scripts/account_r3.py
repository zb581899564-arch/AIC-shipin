#!/usr/bin/env python3
"""Round-3 final accounting."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

R3 = Path("/home/inspur/aic_video_work/orarl_round3")
W = Path("/home/inspur/aic_video_work")
BASE = 40047255552  # work-root bytes at the start of round 3


def sh(c):
    return subprocess.check_output(c, shell=True, text=True).strip()


def main():
    recs = [json.loads(l) for l in (W / "improvement_round1/gpu_ledger.jsonl")
            .read_text().splitlines() if l.strip()]
    mine = [r for r in recs if r["name"].startswith("r3s")]
    charged = 7200 + sum(r.get("charged_seconds", 0) for r in recs)
    work = int(sh(f"du -s -B1 {W}").split()[0])
    free = int(sh(f"df -B1 {W} | tail -1").split()[3])
    r3 = int(sh(f"du -s -B1 {R3}").split()[0])

    s2 = json.loads((R3 / "outputs/r3s2/run_status.json").read_text())
    s1 = json.loads((R3 / "outputs/r3s1/run_status.json").read_text())
    met = json.loads((R3 / "evidence/r3_metrics.json").read_text())

    out = {
        "round3_gpu_jobs": [{"name": r["name"], "charged_seconds": round(r["charged_seconds"], 1),
                             "status": r["status"], "exit_code": r.get("exit_code"),
                             "sampled_peak_memory_mib": r.get("sampled_peak_memory_mib")}
                            for r in mine],
        "round3_gpu_seconds_total": round(sum(r["charged_seconds"] for r in mine), 1),
        "round3_gpu_cap_seconds": 2700,
        "campaign_records": len(recs),
        "campaign_charged_seconds": round(charged, 1),
        "campaign_charged_hours": round(charged / 3600, 4),
        "campaign_remaining_hours": round((86400 - charged) / 3600, 4),
        "disk": {
            "work_root_before_bytes": BASE, "work_root_now_bytes": work,
            "round3_dir_bytes": r3, "round3_new_bytes": work - BASE,
            "round3_new_gib": round((work - BASE) / 2 ** 30, 4),
            "round3_cap_gib": 3, "project_work_cap_gib": 80,
            "work_root_gib": round(work / 2 ** 30, 2),
            "fs_free_bytes": free, "fs_free_gib": round(free / 2 ** 30, 2),
        },
        "runs": {
            "r3s2": {"n_cases": s2["run"]["n_cases"], "n_success": s2["run"]["n_task_success"],
                     "exit_code": s2["run"]["exit_code"],
                     "model_load_seconds": s2["run"].get("model_load_seconds")},
            "r3s1": {"n_cases": s1["run"]["n_cases"], "n_success": s1["run"]["n_task_success"],
                     "n_failed": s1["run"]["n_failed"], "exit_code": s1["run"]["exit_code"],
                     "model_load_seconds": s1["run"].get("model_load_seconds")},
        },
        "timing": {
            "s2_generate_seconds_total": round(sum(c.get("generate_seconds") or 0
                                                   for c in s2["cases"]), 1),
            "s2_generate_seconds_mean": round(
                sum(c.get("generate_seconds") or 0 for c in s2["cases"]) / len(s2["cases"]), 2),
            "s1_generate_seconds_mean": round(
                sum(c.get("generate_seconds") or 0 for c in s1["cases"]) / len(s1["cases"]), 2),
            "peak_memory_mib_r3s2": max((c.get("peak_memory_allocated_mib") or 0)
                                        for c in s2["cases"]),
            "peak_memory_mib_r3s1": max((c.get("peak_memory_allocated_mib") or 0)
                                        for c in s1["cases"]),
        },
        "headline_metrics": {
            "S2_public_refcoco": {k: met["s2"]["public_refcoco"][k] for k in
                                  ("n_requested", "valid_output_ratio", "iou_mean", "iou_median",
                                   "iou_min", "iou_max", "iou_ge_0.5", "center_err_mean",
                                   "area_ratio_median")},
            "S2_synthetic_keyframe": {k: met["s2"]["synthetic_keyframe"][k] for k in
                                      ("n_requested", "valid_output_ratio", "iou_mean",
                                       "iou_median", "iou_min", "iou_max", "iou_ge_0.5",
                                       "center_err_mean", "area_ratio_median")},
            "S1_vs_S0": [{"sample_id": r["sample_id"],
                          "init_slot_iou": r["init_slot_iou"],
                          "S1_M1": r["S1_M1_bin_start"], "S0_M1": r["S0_M1_bin_start"],
                          "d_M1": r["S1_minus_S0_M1_bin_start"],
                          "d_M2": r["S1_minus_S0_M2_bin_mid"],
                          "d_M3": r["S1_minus_S0_M3_bin_end"],
                          "S1_never_exceeds_S0_under_ANY_mapping":
                              r["S1_never_exceeds_S0_under_ANY_mapping"]}
                         for r in met["s1_vs_s0"]],
        },
    }
    (R3 / "evidence/r3_accounting.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\nwrote", R3 / "evidence/r3_accounting.json")


if __name__ == "__main__":
    main()
