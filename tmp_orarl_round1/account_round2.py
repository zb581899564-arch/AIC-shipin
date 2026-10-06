#!/usr/bin/env python3
"""Final round-2 accounting: GPU budget, disk delta, per-case cost."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

R1 = Path("/home/inspur/aic_video_work/orarl_round1")
R2 = Path("/home/inspur/aic_video_work/orarl_round2")
W = Path("/home/inspur/aic_video_work")
BASE = 39983165440  # work-root bytes measured at the start of round 2


def sh(c):
    return subprocess.check_output(c, shell=True, text=True).strip()


def main():
    recs = [json.loads(l) for l in (W / "improvement_round1/gpu_ledger.jsonl")
            .read_text().splitlines() if l.strip()]
    mine = [r for r in recs if r["name"].startswith("r2")]
    charged = 7200 + sum(r.get("charged_seconds", 0) for r in recs)
    work = int(sh(f"du -s -B1 {W}").split()[0])
    free = int(sh(f"df -B1 {W} | tail -1").split()[3])
    r2 = int(sh(f"du -s -B1 {R2}").split()[0])

    out = {
        "round2_gpu_jobs": [{"name": r["name"], "charged_seconds": round(r["charged_seconds"], 1),
                             "status": r["status"], "exit_code": r.get("exit_code"),
                             "sampled_peak_memory_mib": r.get("sampled_peak_memory_mib")}
                            for r in mine],
        "round2_gpu_seconds_total": round(sum(r["charged_seconds"] for r in mine), 1),
        "round2_gpu_cap_seconds": 2700,
        "campaign_records": len(recs),
        "campaign_charged_seconds": round(charged, 1),
        "campaign_charged_hours": round(charged / 3600, 4),
        "campaign_remaining_hours": round((86400 - charged) / 3600, 4),
        "disk": {
            "work_root_before_bytes": BASE, "work_root_now_bytes": work,
            "round2_dir_bytes": r2,
            "round2_new_bytes": work - BASE,
            "round2_new_gib": round((work - BASE) / 2 ** 30, 4),
            "round2_cap_gib": 3,
            "project_work_cap_gib": 80, "work_root_gib": round(work / 2 ** 30, 2),
            "fs_free_bytes": free, "fs_free_gib": round(free / 2 ** 30, 2),
        },
    }
    st = json.loads((R2 / "outputs/r2tr/run_status.json").read_text())
    sg = json.loads((R2 / "outputs/r2sg/run_status.json").read_text())
    out["results"] = {
        "sg": {"n_cases": sg["run"]["n_cases"], "n_success": sg["run"]["n_task_success"],
               "exit_code": sg["run"]["exit_code"]},
        "tracking": {"n_cases": st["run"]["n_cases"],
                     "n_success": st["run"]["n_task_success"],
                     "n_failed": st["run"]["n_failed"],
                     "exit_code": st["run"]["exit_code"]},
        "per_case_generate_seconds": {c["case_id"]: c.get("generate_seconds")
                                      for c in st["cases"]},
        "per_case_peak_mib": {c["case_id"]: c.get("peak_memory_allocated_mib")
                              for c in st["cases"]},
    }
    (R2 / "evidence/resource_accounting.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\nwrote", R2 / "evidence/resource_accounting.json")


if __name__ == "__main__":
    main()
