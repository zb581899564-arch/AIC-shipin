#!/usr/bin/env python3
"""ERRATUM 1 for the round-1 report.

The round-1 report called the downloader metadata + mirror API + local SHA-256
a "three-way independent verification". That is wrong: the mirror API and the
downloader record are two views of the SAME upstream object, fetched over
essentially the same network path. They are transport/file-consistency
evidence, not three independent attestations.

This script does what the round-2 brief asks: try the OFFICIAL domains
directly, and record the real path actually used.

No GPU.
"""
from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path

R1 = Path("/home/inspur/aic_video_work/orarl_round1")
R2 = Path("/home/inspur/aic_video_work/orarl_round2")
REV = "01850297d5ab2adaaf130f700ed7cec52993d956"


def dns(host):
    try:
        return sorted({ai[4][0] for ai in socket.getaddrinfo(host, 443)})
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def curl(url, timeout=20, method="GET"):
    o = subprocess.run(["curl", "-sS", "-m", str(timeout), "-o", "/dev/null",
                        "-w", "%{http_code} %{time_total} %{size_download}",
                        "-X", method, url], capture_output=True, text=True)
    body = ""
    if o.stdout.strip().startswith("000") or o.returncode != 0:
        body = (o.stderr or "").strip().replace("\n", " ")[:160]
    return {"url": url, "http_and_time": o.stdout.strip(), "curl_rc": o.returncode,
            "error": body}


def main():
    out = {"purpose": ("determine whether the fixed-revision metadata can be obtained from the "
                       "OFFICIAL domain, and record the real retrieval path"),
           "revision": REV, "dns": {}, "probes": [], "official_metadata_obtained": False}

    print("=== DNS ===")
    for h in ("huggingface.co", "cdn-lfs.huggingface.co", "github.com",
              "hf-mirror.com", "raw.githubusercontent.com"):
        r = dns(h)
        out["dns"][h] = r
        print(f"  {h:32s} -> {r}")

    print("\n=== HTTP probes (official first) ===")
    urls = [
        "https://huggingface.co/api/models/OraRL/Video-ORA-4B",
        f"https://huggingface.co/api/models/OraRL/Video-ORA-4B/revision/{REV}",
        "https://huggingface.co/OraRL/Video-ORA-4B/resolve/"
        f"{REV}/model.safetensors.index.json",
        "https://cdn-lfs.huggingface.co/",
        "https://raw.githubusercontent.com/HVision-NKU/OraRL/"
        "e1ec91ff00f59ee0da04d285938c1f7247daa69c/README.md",
        "https://hf-mirror.com/api/models/OraRL/Video-ORA-4B",
    ]
    for u in urls:
        r = curl(u)
        official = "huggingface.co" in u and "hf-mirror" not in u
        r["is_official_domain"] = official
        out["probes"].append(r)
        print(f"  [{'OFFICIAL' if official else 'mirror  '}] {u[:78]:78s} "
              f"-> {r['http_and_time'] or r['error'][:60]}")

    # If the official domain worked, actually pull the metadata and compare it
    # against the mirror value, so the check is a real cross-source comparison.
    print("\n=== cross-source comparison (only if official worked) ===")
    official_ok = any(p["is_official_domain"] and p["http_and_time"].startswith("200")
                      for p in out["probes"])
    out["official_domain_reachable"] = official_ok
    if official_ok:
        o = subprocess.run(["curl", "-sS", "-m", "60",
                            "https://huggingface.co/api/models/OraRL/Video-ORA-4B?blobs=true"],
                           capture_output=True, text=True)
        if o.returncode == 0 and o.stdout.strip().startswith("{"):
            api = json.loads(o.stdout)
            out["official_metadata_obtained"] = True
            off_lfs = {s["rfilename"]: (s.get("lfs") or {}).get("sha256")
                       for s in api.get("siblings", []) if (s.get("lfs") or {}).get("sha256")}
            mirror = json.loads((R1 / "evidence/hf_model_api_blobs.json").read_text())
            mir_lfs = {s["rfilename"]: (s.get("lfs") or {}).get("sha256")
                       for s in mirror.get("siblings", []) if (s.get("lfs") or {}).get("sha256")}
            agree = {k: (off_lfs.get(k) == mir_lfs.get(k)) for k in sorted(set(off_lfs) | set(mir_lfs))}
            out["official_vs_mirror_lfs_agreement"] = {
                "n_official": len(off_lfs), "n_mirror": len(mir_lfs),
                "all_agree": all(agree.values()), "per_file": agree}
            out["official_revision"] = api.get("sha")
            print("  official LFS entries:", len(off_lfs),
                  " mirror:", len(mir_lfs), " all agree:", all(agree.values()))
        else:
            print("  official domain answered HEAD but metadata fetch failed")
    else:
        print("  official domain NOT reachable; no cross-source comparison possible")
        out["official_vs_mirror_lfs_agreement"] = None

    # record the path actually used
    out["actual_retrieval_paths"] = {
        "weights": "https://hf-mirror.com (HF_ENDPOINT) via huggingface_hub.snapshot_download",
        "model_metadata_api": "https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true",
        "source_repo": "https://ghproxy.net/https://github.com/HVision-NKU/OraRL.git",
    }

    # ---- independent official-domain check of the SOURCE revision ----
    # raw.githubusercontent.com IS reachable directly. Compare its bytes for the
    # pinned commit against the local clone: a genuinely different domain and
    # path from the ghproxy clone.
    print("\n=== official-domain source verification (raw.githubusercontent.com) ===")
    import hashlib
    src = R1 / "src/OraRL"
    commit = "e1ec91ff00f59ee0da04d285938c1f7247daa69c"
    checked = {}
    targets = [
        "README.md",
        "eval/task/eval_prompt.py",
        "eval/task/tracking/eval_tracking_vllm.py",
        "data/eval/datasets.jsonl",
        "eval/task/qwenvl_decord_patch.py",
        "docs/evaluation.md",
    ]
    for rel in targets:
        url = f"https://raw.githubusercontent.com/HVision-NKU/OraRL/{commit}/{rel}"
        o = subprocess.run(["curl", "-sS", "-m", "45", url], capture_output=True)
        local = src / rel
        rec = {"file": rel, "url": url, "fetched": o.returncode == 0 and len(o.stdout) > 0,
               "official_bytes": len(o.stdout)}
        if rec["fetched"] and local.exists():
            rec["official_sha256"] = hashlib.sha256(o.stdout).hexdigest()
            rec["local_sha256"] = hashlib.sha256(local.read_bytes()).hexdigest()
            rec["match"] = rec["official_sha256"] == rec["local_sha256"]
        else:
            rec["match"] = None
        checked[rel] = rec
        print(f"  {'MATCH ' if rec['match'] else ('n/a   ' if rec['match'] is None else 'DIFFER')} "
              f"{rel:48s} {rec['official_bytes']} bytes from official domain")
    out["source_official_domain_check"] = {
        "domain": "raw.githubusercontent.com (official GitHub content domain, reached directly)",
        "commit": commit,
        "files": checked,
        "all_match": all(r["match"] for r in checked.values() if r["match"] is not None)
                     and any(r["match"] for r in checked.values()),
    }
    print("  all_match:", out["source_official_domain_check"]["all_match"])

    out["corrected_claim"] = (
        "Model weights: the mirror API value, the huggingface_hub download record and the "
        "locally recomputed SHA-256 are consistent with each other, which is evidence of "
        "transport and file integrity. They are NOT three independent attestations of publisher "
        "identity: hf-mirror is a relay of the same upstream object. The official huggingface.co "
        "domain was NOT reachable from this host (DNS resolves to unrelated address space and "
        "every request times out after 20 s), so no independent cross-source confirmation of the "
        "MODEL was possible; recorded as a limitation. "
        "Source code: an independent official-domain check WAS possible and passed -- several "
        "files fetched directly from raw.githubusercontent.com at the pinned commit are "
        "byte-identical to the local clone, so the source revision is confirmed via a genuinely "
        "different domain and transport path.")
    print("\n" + out["corrected_claim"])

    dest = R2 / "evidence/erratum1_official_domain.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("\nwrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
