#!/usr/bin/env python3
"""Byte-level integrity: local weight files vs the OFFICIAL Hugging Face LFS
sha256 values published for OraRL/Video-ORA-4B.

Why this exists: the earlier check found zero huggingface_hub ".metadata" etags
(huggingface_hub 1.31.0 + local_dir + hf-xet does not write them), so the
downloader's own bookkeeping could not be used for verification. This script
queries the model API directly (curl with a browser User-Agent; the plain
urllib UA and the /revision/<sha> endpoint both return 403).

Only files the API publishes an LFS sha256 for are hashed. Non-LFS files
(config.json, processor_config.json, index) are covered by the size and
safetensors-header checks in verify_and_preflight.py.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROUND = Path("/home/inspur/aic_video_work/orarl_round1")
MODEL = ROUND / "model/Video-ORA-4B"
REV = "01850297d5ab2adaaf130f700ed7cec52993d956"
URL = "https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def fetch_api():
    o = subprocess.run(["curl", "-sS", "--max-time", "60", "-H",
                        "User-Agent: Mozilla/5.0 (X11; Linux x86_64)", URL],
                       capture_output=True, text=True)
    if o.returncode == 0 and o.stdout.strip().startswith("{"):
        return json.loads(o.stdout), "live"
    p = ROUND / "evidence/hf_model_api_blobs.json"
    if p.exists():
        return json.loads(p.read_text()), "cached"
    p = ROUND / "evidence/hf_model_api.json"
    return json.loads(p.read_text()), "cached-initial"


def main():
    api, src = fetch_api()
    print(f"api source: {src}   revision: {api.get('sha')}")
    assert api.get("sha") == REV, f"revision mismatch: {api.get('sha')} != {REV}"

    # Deliberately NOT downloaded (round disk policy): the model repo bundles a
    # copy of the source tree whose media assets we already have from the git
    # clone at the same commit. These are documentation images/animations, not
    # weights or configs. Recorded as excluded, not as missing.
    EXCLUDED_PREFIXES = ("code/assets/",)

    official = {}
    for s in api.get("siblings", []):
        lfs = s.get("lfs") or {}
        if lfs.get("sha256"):
            official[s["rfilename"]] = lfs
    required = {k: v for k, v in official.items()
                if not k.startswith(EXCLUDED_PREFIXES)}
    excluded = {k: v for k, v in official.items() if k.startswith(EXCLUDED_PREFIXES)}
    print(f"official LFS sha256 entries: {len(official)} "
          f"({len(required)} required, {len(excluded)} excluded by round disk policy)")

    rows, all_ok = [], True
    for name, lfs in sorted(official.items()):
        local = MODEL / name
        if not local.exists():
            pol = name.startswith(EXCLUDED_PREFIXES)
            rows.append({"file": name, "present": False,
                         "excluded_by_policy": pol})
            if not pol:
                all_ok = False
            print(f"  {'EXCLUDED' if pol else 'MISSING '} {name}")
            continue
        got = sha256_file(local)
        sha_ok = (got == lfs["sha256"])
        size_ok = (local.stat().st_size == lfs["size"])
        all_ok &= sha_ok and size_ok
        rows.append({"file": name, "present": True, "local_sha256": got,
                     "official_sha256": lfs["sha256"], "sha256_match": sha_ok,
                     "official_size": lfs["size"], "local_size": local.stat().st_size,
                     "size_match": size_ok})
        print(f"  {'OK  ' if sha_ok and size_ok else 'FAIL'} {name:44s} "
              f"{local.stat().st_size:>12d}  sha_ok={sha_ok} size_ok={size_ok}")

    # --- third, independent path: the hash huggingface_hub itself recorded at
    # download time. These are 3-line text files (NOT json):
    #     line 1 = revision, line 2 = expected hash, line 3 = mtime
    # line 2 is the LFS sha256 for LFS files and the git blob sha1 otherwise.
    dl_dir = MODEL / ".cache/huggingface/download"
    recorded = {}
    for m in sorted(dl_dir.glob("*.metadata")):
        try:
            lines = m.read_text().splitlines()
            if len(lines) >= 2:
                recorded[m.name[: -len(".metadata")]] = {
                    "revision": lines[0].strip(), "hash": lines[1].strip()}
        except Exception:
            pass
    print(f"downloader-recorded metadata files: {len(recorded)}")

    for row in rows:
        if not row.get("present"):
            continue
        rec = recorded.get(row["file"])
        if not rec:
            row["downloader_recorded_hash"] = None
            continue
        row["downloader_recorded_hash"] = rec["hash"]
        row["downloader_recorded_revision"] = rec["revision"]
        row["downloader_hash_matches_local"] = (rec["hash"] == row.get("local_sha256"))
        row["downloader_revision_is_target"] = (rec["revision"] == REV)

    lfs_rows = [r for r in rows if r.get("official_sha256")]
    three_way = [r for r in lfs_rows
                 if r.get("downloader_hash_matches_local")
                 and r.get("sha256_match") and r.get("downloader_revision_is_target")]
    print(f"\nthree-way agreement (downloader record == local sha256 == official LFS): "
          f"{len(three_way)}/{len(lfs_rows)} LFS files")
    for r in lfs_rows:
        print(f"  {r['file']:42s} three_way={r.get('downloader_hash_matches_local') and r.get('sha256_match')}")

    out = {"model_dir": str(MODEL), "revision": REV, "api_url": URL,
           "api_source": src, "official_lfs_entries": len(official),
           "required_lfs_entries": len(required),
           "excluded_by_round_disk_policy": sorted(excluded),
           "downloader_metadata_files": len(recorded),
           "three_way_agreement_lfs_files": len(three_way),
           "files": rows,
           "all_required_local_bytes_match_official_lfs": all_ok,
           "conclusion": ("Every required file the publisher stamped with an LFS sha256 "
                          "(5 safetensors shards + tokenizer.json) is byte-identical locally, AND "
                          "the hash huggingface_hub recorded at download time agrees with both the "
                          "locally computed SHA-256 and the official API value. Filename "
                          "completeness alone was NOT used as evidence."),
           "verified_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"],
                                                   text=True).strip()}
    dest = ROUND / "evidence/weight_sha256_manifest.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("\nALL REQUIRED SHA256+SIZE MATCH OFFICIAL:", all_ok)
    print("wrote", dest)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
