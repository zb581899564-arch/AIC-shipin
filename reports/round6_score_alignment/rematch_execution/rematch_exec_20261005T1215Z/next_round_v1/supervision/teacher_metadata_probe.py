"""Read only public HF JSON metadata and small config files; never fetch weights.

Only stdlib is used. No token, model library, HF cache, installation or GPU call.
The capacity inputs are a dated main-controller measurement, not live admission.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import urllib.request

from select_windows import HERE, require

BASE = "Qwen/Qwen3-VL-32B-Instruct"
REVISIONS = {BASE: "0cfaf48183f594c314753d30a4c4974bc75f3ccb",
             BASE + "-GGUF": "e3e1fe0c76de7ee58ea65db420c643adfe2e457c"}
LIMIT = 80 * 2**30
LINUX_BYTES = 50_907_619_328
MAC_BYTES = 28_053_655_552
Q4 = "Qwen3VL-32B-Instruct-Q4_K_M.gguf"
MMPROJ = "mmproj-Qwen3VL-32B-Instruct-F16.gguf"


def get_json(url):
    # Whitelisted metadata endpoint: no weight URLs, user tokens or implicit cache client.
    require(url.startswith("https://huggingface.co/api/models/") or url.endswith("/config.json"), "only metadata URLs allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "aic-read-only-teacher-metadata/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read(2**20 + 1)
    require(len(raw) <= 2**20, "metadata response exceeds one MiB limit")
    return json.loads(raw)


def read_metadata():
    output = []
    for repo, revision in REVISIONS.items():
        url = "https://huggingface.co/api/models/" + repo + "/revision/" + revision + "?blobs=true"
        info = get_json(url)
        require(info.get("sha") == revision and info.get("id") == repo, "official pinned revision identity differs")
        files = [{"path": f["rfilename"], "size_bytes": f.get("size"), "lfs_sha256": (f.get("lfs") or {}).get("sha256")}
                 for f in info.get("siblings", [])]
        require(all(type(f["size_bytes"]) is int and f["size_bytes"] >= 0 for f in files), "official file-size metadata incomplete")
        weights = [f for f in files if f["path"].endswith((".safetensors", ".gguf"))]
        model = {"repo": repo, "revision": revision, "metadata_url": url,
            "model_card_url": "https://huggingface.co/" + repo + "/blob/" + revision + "/README.md",
            "authority": "OFFICIAL_QWEN_PUBLISHER", "last_modified": info.get("lastModified"),
            "license_declared": (info.get("cardData") or {}).get("license"),
            "safetensors_parameters": info.get("safetensors"), "files": files,
            "all_repo_weight_files_bytes": sum(f["size_bytes"] for f in weights)}
        if repo == BASE:
            config_url = "https://huggingface.co/" + repo + "/resolve/" + revision + "/config.json"
            model.update(config=get_json(config_url), config_url=config_url,
                         bf16_selected_weight_files=weights, bf16_total_weight_bytes=sum(f["size_bytes"] for f in weights))
        else:
            selected = [f for name in (Q4, MMPROJ) for f in weights if f["path"] == name]
            require(len(selected) == 2, "official selected Q4/vision projector missing")
            model.update(selected_recipe="Q4_K_M_LANGUAGE_PLUS_F16_VISION_PROJECTOR", selected_weight_files=selected,
                         selected_weight_bytes=sum(f["size_bytes"] for f in selected))
        output.append(model)
    return output


def capacity(metadata):
    quant = next(row for row in metadata if row["repo"].endswith("-GGUF"))
    final_bytes = quant["selected_weight_bytes"]
    largest = max(f["size_bytes"] for f in quant["selected_weight_files"])
    occupied = LINUX_BYTES + MAC_BYTES
    # This is a scenario estimate, not a measured new downloader/cache implementation.
    return {"status": "STOP_32B_TEACHER_CAPACITY", "download_admitted": False,
        "capacity_evidence_kind": "MAIN_CONTROLLER_LIVE_MEASUREMENT_RELAYED_20261007",
        "linux_work_bytes": LINUX_BYTES, "mac_work_bytes": MAC_BYTES,
        "combined_work_bytes": occupied, "cap_bytes": LIMIT, "cap_gib": 80,
        "remaining_bytes_before_new_teacher": LIMIT - occupied,
        "remaining_gib_before_new_teacher": (LIMIT - occupied) / 2**30,
        "selected_final_weight_bytes": final_bytes, "selected_final_weight_gib": final_bytes / 2**30,
        "ideal_zero_duplicate_zero_cache_lower_bound_new_bytes": final_bytes,
        "ideal_combined_peak_lower_bound_bytes": occupied + final_bytes,
        "ideal_shortfall_bytes": occupied + final_bytes - LIMIT,
        "conservative_hub_cache_plus_local_copy_plus_one_stale_largest_partial_bytes": 2 * final_bytes + largest,
        "cache_estimate_is_not_actual_runtime_peak": True,
        "cache_estimation_notes": [
            "A same-filesystem streaming .incomplete-to-final rename could avoid a second copy; this route has not been verified",
            "A hub blob cache plus independent local model copy duplicates weights; one stale largest partial is separately reserved in the conservative scenario",
            "Xet chunk cache, runtime installation, temporary decode frames, tokenizer/config files and generation receipts need additional explicit accounting",
            "Even the impossible zero-overhead lower bound exceeds current headroom; no downloader is admitted",
            "Never download BF16 weights first to quantize, download the whole GGUF repository, delete assets or silently replace the 32B teacher with the same 8B"],
        "gpu_or_ram_runtime_feasibility": "NOT_VERIFIED_NO_WEIGHT_LOAD_OR_GPU_PROBE",
        "runtime_blocker": "Existing inspected Linux environment has no llama-cpp-python or llama-cli; no environment installation authorized",
        "next_action": "Deliver CPU preparation only. Without explainable positive/explicit-empty supervision by first workday, STOP_T and proceed with Z; M already delivered"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    require(HERE in target.parents and not target.exists(), "metadata output must be fresh and inside supervision")
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata = read_metadata()
    report = {"schema": "aic_readonly_32b_teacher_metadata_v1", "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "metadata_only": True, "weight_bytes_downloaded": 0, "gpu_used": False,
        "models": metadata, "capacity": capacity(metadata),
        "installed_or_deleted_anything": False, "same_8b_teacher_fallback": False}
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked_utc": report["checked_utc"], "models": [{"repo": row["repo"], "revision": row["revision"],
        "selected_weight_bytes": row.get("selected_weight_bytes", row.get("bf16_total_weight_bytes"))} for row in metadata],
        "capacity": report["capacity"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
