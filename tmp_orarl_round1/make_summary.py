#!/usr/bin/env python3
"""Produce the compact, report-ready summary of this round's artifacts."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

R = Path("/home/inspur/aic_video_work/orarl_round1")
W = Path("/home/inspur/aic_video_work")
BASE_WORK_BYTES = 20961681408  # measured before this round started


def sh(c):
    return subprocess.check_output(c, shell=True, text=True).strip()


def main():
    run = json.load(open(R / "outputs/run_status.json"))
    ov = json.load(open(R / "outputs/overlay_manifest.json"))
    pre = json.load(open(R / "evidence/preflight.json"))
    wsha = json.load(open(R / "evidence/weight_sha256_manifest.json"))
    cpu = json.load(open(R / "evidence/offline_load_probe.json"))
    man = json.load(open(R / "evidence/sample_manifest.json"))

    work_now = int(sh(f"du -s -B1 {W}").split()[0])
    free_now = int(sh(f"df -B1 {W} | tail -1").split()[3])
    recs = [json.loads(l) for l in (W / "improvement_round1/gpu_ledger.jsonl").read_text().splitlines()
            if l.strip()]
    mine = [r for r in recs if r["name"].startswith("orarl_r1_verify")]
    charged_total = 7200 + sum(r.get("charged_seconds", 0) for r in recs)

    s = {
        "round": "orarl_round1",
        "generated_utc": sh("date -u +%FT%TZ"),
        "model": {"path": str(R / "model/Video-ORA-4B"),
                  "revision": "01850297d5ab2adaaf130f700ed7cec52993d956",
                  "dir_bytes": int(sh(f"du -s -B1 {R}/model/Video-ORA-4B").split()[0]),
                  "files": [f["file"] for f in wsha["files"] if f.get("present")],
                  "all_required_sha256_match_official": wsha["all_required_local_bytes_match_official_lfs"]},
        "source": {"path": str(R / "src/OraRL"), "commit": pre["source"]["head"],
                   "commit_match": pre["source"]["commit_match"],
                   "dirty": pre["source"]["dirty"]},
        "env": {"path": str(R / "env/orarl_hf"),
                "python": "3.11.10", "torch": "2.10.0+cu129",
                "transformers": "5.5.4", "qwen_vl_utils": "0.0.14",
                "decord": "0.6.0", "attn_implementation": "sdpa",
                "dir_bytes": int(sh(f"du -s -B1 {R}/env/orarl_hf").split()[0])},
        "hardware": pre["hardware"],
        "cpu_offline_load": cpu["steps"].get("from_pretrained(device_map=cpu, offline)", {}).get("value"),
        "cpu_all_ok": cpu["all_ok"],
        "samples": {
            "source_video": man["source"]["path"],
            "source_sha256": man["source"]["sha256"],
            "clip": man["derived_clip"]["path"],
            "clip_sha256": man["derived_clip"]["sha256"],
            "clip_duration_sec": man["derived_clip"]["duration_sec"],
            "clip_nb_frames": man["derived_clip"]["nb_frames"],
            "clip_fps": man["derived_clip"]["fps_avg"],
            "source_offset_sec": man["derived_clip"]["source_offset_sec"],
            "frame": man["derived_frame"]["path"],
            "frame_sha256": man["derived_frame"]["sha256"],
            "frame_wh": [man["derived_frame"]["width"], man["derived_frame"]["height"]],
            "task_inputs_are_not_ground_truth": True,
        },
        "tasks": {},
        "gpu_budget": {
            "round_jobs": [{"name": r["name"], "charged_seconds": round(r["charged_seconds"], 1),
                            "status": r["status"], "exit_code": r.get("exit_code"),
                            "sampled_peak_memory_mib": r.get("sampled_peak_memory_mib")}
                           for r in mine],
            "round_gpu_seconds_total": round(sum(r["charged_seconds"] for r in mine), 1),
            "round_gpu_cap_seconds": 1800,
            "campaign_records": len(recs),
            "campaign_charged_seconds": round(charged_total, 1),
            "campaign_budget_seconds": 86400,
            "campaign_remaining_hours": round((86400 - charged_total) / 3600, 4),
        },
        "disk": {
            "work_root_bytes_before": BASE_WORK_BYTES,
            "work_root_bytes_now": work_now,
            "round_delta_bytes": work_now - BASE_WORK_BYTES,
            "round_delta_gib": round((work_now - BASE_WORK_BYTES) / 2 ** 30, 3),
            "round_cap_gib": 25,
            "project_work_cap_gib": 80,
            "fs_free_bytes": free_now,
            "fs_free_gib": round(free_now / 2 ** 30, 2),
        },
    }

    for t in ("spatial_grounding", "temporal_grounding", "tracking"):
        r = run["tasks"].get(t, {})
        s["tasks"][t] = {
            "status": r.get("status"), "valid": r.get("valid"),
            "prompt": r.get("prompt"),
            "sampling_profile": r.get("sampling_profile"),
            "input_ids_len": r.get("input_ids_len"),
            "grid_thw": r.get("grid_thw"),
            "generate_seconds": r.get("generate_seconds"),
            "output_tokens": r.get("output_tokens"),
            "peak_memory_allocated_mib": r.get("peak_memory_allocated_mib"),
            "raw_output": (r.get("raw_output") or "")[:2000],
            "parsed": r.get("parsed"),
            "parse_errors": r.get("parse_errors"),
            "parse_warnings": r.get("parse_warnings"),
            "sampled_frames": {k: v for k, v in (r.get("sampled_frames") or {}).items()
                               if k not in ("secondN_vs_sampled_time",)},
            "input_media_probe": r.get("input_media_probe"),
            "exception": r.get("exception"),
        }
    s["overlays"] = ov
    s["run_meta"] = {k: run.get(k) for k in
                     ("started_utc", "finished_utc", "model_load_seconds",
                      "model_memory_allocated_mib_after_load", "model_param_dtype",
                      "deviations", "framework")}

    dest = R / "outputs/round_summary.json"
    dest.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(s, indent=2, ensure_ascii=False))
    print("\nwrote", dest)


if __name__ == "__main__":
    main()
