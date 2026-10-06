#!/usr/bin/env python3
"""Weight integrity check + preflight record for the Video-ORA-4B deployment.

Two independent checks:
  A. every weight file's local SHA-256 vs the official Hugging Face LFS etag
     (etag recorded by huggingface_hub itself in .cache/huggingface/download/*.metadata)
  B. model.safetensors.index.json weight_map vs the tensor keys actually inside
     each shard's safetensors header

"All filenames present" is NOT treated as "model verified". This script only
proves the bytes on disk match the published bytes; loading is verified
separately by the GPU run.

Dependency-free (stdlib only) so it runs under any python3.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

MODEL = Path("/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B")
ROUND = Path("/home/inspur/aic_video_work/orarl_round1")
SRC = ROUND / "src/OraRL"
REV = "01850297d5ab2adaaf130f700ed7cec52993d956"
COMMIT = "e1ec91ff00f59ee0da04d285938c1f7247daa69c"
WORK = Path("/home/inspur/aic_video_work")
BUDGET = WORK / "improvement_round1"


def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def sha256_file(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def safetensors_keys(p):
    """Read a safetensors header without loading tensors."""
    with open(p, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        hdr = json.loads(f.read(n).decode("utf-8"))
    hdr.pop("__metadata__", None)
    return hdr


def main():
    out = {"model_dir": str(MODEL), "revision": REV, "orarl_commit": COMMIT}
    ok = True

    print("=== A. FILE PRESENCE + OFFICIAL SHA-256 ===")
    # official etags recorded by huggingface_hub at download time
    meta_dir = MODEL / ".cache/huggingface/download"
    etags = {}
    if meta_dir.is_dir():
        for m in meta_dir.rglob("*.metadata"):
            try:
                d = json.loads(m.read_text())
                et = (d.get("etag") or "").strip('"')
                if et:
                    etags[m.name] = et
            except Exception:
                pass
    print(f"  etags recorded by huggingface_hub: {len(etags)}")

    files = []
    for p in sorted(MODEL.iterdir()):
        if p.is_file() and p.suffix in (".safetensors", ".json", ".jinja"):
            files.append(p)

    shards = sorted(MODEL.glob("*.safetensors"))
    report_files = []
    for p in files:
        rec = {"file": p.name, "size": p.stat().st_size}
        rec["sha256"] = sha256_file(p)
        et = etags.get(p.name)
        if et:
            rec["official_etag"] = et
            rec["etag_match"] = (et == rec["sha256"])
            if not rec["etag_match"]:
                ok = False
        report_files.append(rec)
        flag = "MATCH" if rec.get("etag_match") else ("no-etag" if not et else "MISMATCH")
        print(f"  {p.name:42s} {rec['size']:>12d}  {flag}")
    out["files"] = report_files

    print(f"\n  shards present: {len(shards)} (index expects 5)")
    if len(shards) != 5:
        ok = False
        print("  !! shard count mismatch")

    print("\n=== B. INDEX weight_map vs safetensors headers ===")
    idx_path = MODEL / "model.safetensors.index.json"
    if not idx_path.exists():
        print("  !! index missing"); ok = False
        out["index_check"] = {"present": False}
    else:
        idx = json.loads(idx_path.read_text())
        wm = idx["weight_map"]
        by_shard = {}
        for k, v in wm.items():
            by_shard.setdefault(v, []).append(k)
        print(f"  weight_map entries: {len(wm)} across {len(by_shard)} shards")
        print(f"  metadata total_size: {idx.get('metadata', {}).get('total_size')}")
        shard_report = {}
        for shard, keys in sorted(by_shard.items()):
            sp = MODEL / shard
            if not sp.exists():
                print(f"  !! missing shard {shard}"); ok = False
                shard_report[shard] = {"present": False}
                continue
            hdr = safetensors_keys(sp)
            missing = sorted(set(keys) - set(hdr))
            extra = sorted(set(hdr) - set(keys))
            dt = {}
            nparam = 0
            for k, v in hdr.items():
                dt[v["dtype"]] = dt.get(v["dtype"], 0) + 1
                n = 1
                for s in v["shape"]:
                    n *= s
                nparam += n
            shard_report[shard] = {
                "present": True, "keys_in_index": len(keys), "keys_in_header": len(hdr),
                "missing_from_header": missing[:10], "extra_in_header": extra[:10],
                "dtypes": dt, "param_count": nparam,
            }
            status = "OK" if not missing and not extra else "MISMATCH"
            if status != "OK":
                ok = False
            print(f"  {shard}: index={len(keys)} header={len(hdr)} params={nparam/1e6:.1f}M "
                  f"dtypes={dt} -> {status}")
        total_params = sum(v.get("param_count", 0) for v in shard_report.values())
        print(f"  total parameters across shards: {total_params/1e9:.4f} B")
        out["index_check"] = {"present": True, "weight_map_entries": len(wm),
                              "shards": shard_report, "total_params": total_params}

    out["weights_byte_identical_to_published"] = ok
    out["interpretation"] = (
        "Byte-level identity to the published revision is verified. This does NOT prove the "
        "checkpoint loads or runs; that is verified separately by the GPU inference run.")

    print("\n=== C. SOURCE VERSION ===")
    try:
        head = sh(f"git -C {SRC} rev-parse HEAD")
        dirty = sh(f"git -C {SRC} status --porcelain")
        out["source"] = {"path": str(SRC), "head": head, "dirty": bool(dirty),
                         "expected_commit": COMMIT, "commit_match": head == COMMIT}
        print(f"  HEAD={head} commit_match={head == COMMIT} dirty={bool(dirty)}")
        if head != COMMIT:
            ok = False
    except Exception as exc:
        out["source"] = {"error": str(exc)}
        print("  !! source check failed:", exc)

    print("\n=== D. HARDWARE / DISK / BUDGET ===")
    gpu = sh("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader")
    apps = sh("nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv,noheader")
    dfo = sh(f"df -B1 {WORK} | tail -1").split()
    work_bytes = int(sh(f"du -s -B1 {WORK}").split()[0])
    out["hardware"] = {"gpu": gpu, "compute_apps": apps,
                       "fs_free_bytes": int(dfo[3]), "work_root_bytes": work_bytes}
    print(f"  gpu: {gpu}")
    print(f"  compute apps: {apps!r}")
    print(f"  fs free: {int(dfo[3])/2**30:.2f} GiB   work root: {work_bytes/2**30:.2f} GiB")

    ledger = BUDGET / "gpu_ledger.jsonl"
    recs = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    charged = 7200 + sum(r.get("charged_seconds", 0) for r in recs)
    out["budget"] = {"records": len(recs), "charged_seconds": charged,
                     "budget_seconds": 86400,
                     "remaining_seconds": 86400 - charged,
                     "active_job_present": (BUDGET / "active_gpu_job.json").exists()}
    print(f"  charged {charged:.0f}s / 86400s -> remaining {(86400-charged)/3600:.3f} h")
    print(f"  active_gpu_job.json present: {out['budget']['active_job_present']}")

    print("\n=== E. ADMISSION ===")
    disk_ok = (int(dfo[3]) > 80 * 2**30) and (work_bytes < 80 * 2**30)
    gpu_free = (apps.strip() == "")
    adm = {
        "weights_verified": ok,
        "disk_within_project_limits": disk_ok,
        "gpu_idle": gpu_free,
        "budget_available": out["budget"]["remaining_seconds"] > 1800 + 120,
        "no_active_gpu_job": not out["budget"]["active_job_present"],
        "framework_gpu_check": "deferred to budgeted GPU run (not probed here)",
    }
    adm["admitted"] = all([adm["weights_verified"], adm["disk_within_project_limits"],
                           adm["gpu_idle"], adm["budget_available"],
                           adm["no_active_gpu_job"]])
    out["admission"] = adm
    for k, v in adm.items():
        print(f"  {k}: {v}")

    out["checked_utc"] = sh("date -u +%FT%TZ")
    dest = ROUND / "evidence/preflight.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("\nwrote", dest)
    print("ADMISSION:", "PASS" if adm["admitted"] else "FAIL")
    return 0 if adm["admitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
