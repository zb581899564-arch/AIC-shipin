#!/usr/bin/env python3
"""P1b: assemble the structured deliverables in reports/round6_score_alignment/phase1b/.

Reads the artifacts already produced in this round (inventory, remote probe, local
verification, manifest, tool validation) and writes:

  source_and_license_audit.json
  selection_manifest.json
  RESOURCE_USAGE.json

No network, no media writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = ROOT / "round6_score_alignment/p1b"
PHASE1B = ROOT / "reports/round6_score_alignment/phase1b"
RUN_ID = "round6_p1b_20260917T0615Z"
TEST_METADATA = ROOT / "reports/round6_score_alignment/phase0/evidence/supervisor_test_metadata.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def relative_files(pattern: str) -> list[dict]:
    out = []
    for path in sorted(ROOT.glob(pattern)):
        if path.is_file():
            out.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return out


def build_source_audit(manifest: dict) -> dict:
    record = manifest["samples"][0]["source_record"]
    inventory = load(P1B / "inventory_raw.json")
    return {
        "schema": "p1b_source_and_license_audit_v1",
        "run_id": RUN_ID,
        "scope": "the 8 pilot source groups plus the corpus they come from",
        "corpus": {
            "root": "/home/inspur/aic_video_data/videos",
            "files": inventory["corpus"]["files_total"],
            "bytes": inventory["corpus"]["total_bytes"],
            "naming": "<youtube_id>_<start_sec>_<end_sec>.mp4 (150 s windows of public YouTube videos)",
            "distinct_youtube_ids": inventory["corpus"]["distinct_youtube_ids"],
        },
        "records": [{"kind": "share_origin", **record}],
        "per_sample": [
            {"sample_id": s["sample_id"], "source_group": s["source_group"],
             "youtube_watch_url": f"https://www.youtube.com/watch?v={s['source_group']}",
             "youtube_watch_url_note": ("recorded for provenance only; P1b did NOT open it and the "
                                        "project has no confirmation that the page is still live or "
                                        "that the uploader licence is reusable"),
             "corpus_file": s["file_name"], "sha256": s["sha256_local"],
             "permitted_use": record["permitted_use_registered"],
             "limitations": record["limitations"], "unconfirmed": record["unconfirmed"]}
            for s in manifest["samples"]],
        "project_evidence_paths": {
            "share_download_log": "remote:/home/inspur/aic_video_data/bddownload.log",
            "extraction_log": "remote:/home/inspur/aic_video_data/unzip.log + unzip.status",
            "label_origin_review": "reports/标签来源复核_20260915.md",
            "official_page_record": "remote:/home/inspur/aic_video_work/reports/eval_source_audit.md",
            "unused_alternative_download": ("remote:/home/inspur/aic_video_data/dl_unc.sh + "
                                            "reports/supervisor_official_archive_probe.json "
                                            "(QVHighlights tarball probed, never extracted; "
                                            "downloads/ is empty)"),
        },
        "conclusions": {
            "non_test_corpus_confirmed": True,
            "basis": ("corpus lives under /home/inspur/aic_video_data/videos; the official test "
                      "material lives under /home/inspur/aic_video_data/test and was excluded by "
                      "path, never opened"),
            "licence_grant_found": False,
            "licence_statement": ("no per-video licence grant was found; the competition page allows "
                                  "public/self-built training data and the share delivered this "
                                  "corpus for the task, but downloading from a netdisk is not a "
                                  "licence and the underlying YouTube rights are untouched"),
            "redistribution": "not permitted by this project; nothing is redistributed or uploaded",
            "outstanding": ["share publisher identity", "share terms text",
                            "whether any corpus video shares a source with the official test set"],
        },
    }


def build_selection_manifest(manifest: dict) -> dict:
    inventory = load(P1B / "inventory_raw.json")
    probe = load(P1B / "remote_probe_raw.json")
    test = load(TEST_METADATA)["records"]
    probe_by_name = {i["file_name"]: i for i in probe["items"]}
    samples = []
    for s in manifest["samples"]:
        p = probe_by_name[s["file_name"]]
        same_res = any(t["width"] == s["source_width"] and t["height"] == s["source_height"]
                       for t in test)
        near_dur = any(abs(t["duration_sec"] - s["duration_sec"]) < 0.05 for t in test)
        samples.append({
            **{k: s[k] for k in ("sample_id", "source_group", "file_name", "target_ratio_wh",
                                 "source_width", "source_height", "fps", "n_frames",
                                 "duration_sec", "sha256_local", "sha256_remote", "bytes",
                                 "remote_path", "corpus_window_sec", "files_in_source_group")},
            "split": "pilot_dev",
            "annotation_status": "UNANNOTATED",
            "exclusion_checks": {
                "youtube_id_in_987_labels": False,
                "youtube_id_in_818_splits": False,
                "under_test_path": False,
                "shares_resolution_with_a_test_video": same_res,
                "duration_within_50ms_of_a_test_video": near_dur,
                "note": ("all three exclusion sets were built from YouTube-level ids; the last two "
                         "checks are weak anti-leak heuristics, not proof of distinct source "
                         "material"),
            },
            "verification": {
                "remote_readable": p["checks"]["readable"],
                "duration_in_5_180": p["checks"]["duration_in_5_180"],
                "local_sha256_matches_remote": s["sha256_local"] == s["sha256_remote"],
                "cfr_within_1us": s["pts"]["cfr_within_1us"],
                "stream_start_is_zero": s["pts"]["stream_start_is_zero"],
            },
        })
    return {
        "schema": "p1b_selection_manifest_v1",
        "run_id": RUN_ID,
        "algorithm": inventory["sampling"]["rule"],
        "seed": inventory["sampling"]["seed"] if "seed" in inventory["sampling"] else 20260917,
        "candidate_pool": {
            "corpus_files_total": inventory["corpus"]["files_total"],
            "excluded_by_source_group": inventory["candidates"]["excluded_by_source_group"],
            "excluded_by_size": inventory["candidates"]["excluded_by_size"],
            "candidates_after_exclusion": inventory["candidates"]["files"],
            "candidate_source_groups": inventory["candidates"]["distinct_youtube_ids"],
        },
        "exclusion": inventory["exclusion"],
        "target_ratio_assignment": {
            "rule": "the 8 sampled groups in stable order receive 16:9 x4 then 9:16 x4",
            "note": "the target ratio is a protocol assignment, not the source aspect ratio",
            "distribution": {"[16,9]": 4, "[9,16]": 4},
        },
        "candidate_list_preserved": "round6_score_alignment/p1b/inventory_raw.json",
        "samples": samples,
        "not_selected_larger_groups": {
            "note": ("a source group usually has several 150 s windows; the first window in stable "
                     "file-name order was taken and the window count per group is recorded above"),
        },
        "no_model_in_selection": True,
        "selection_not_based_on_expected_score": True,
        "negatives": {"guaranteed": False,
                      "statement": ("no no-highlight sample was fabricated; a negative only counts "
                                    "if an annotator confirms it in the tool")},
    }


def build_resource_usage(manifest: dict) -> dict:
    media = [p for p in (P1B / "media").glob("*.mp4")]
    code = relative_files("round6_score_alignment/p1b/*")
    reports = relative_files("reports/round6_score_alignment/phase1b/*")
    ui = relative_files("reports/round6_score_alignment/phase1b/ui_render/*")
    return {
        "schema": "p1b_resource_usage_v1",
        "run_id": RUN_ID,
        "gpu": {"used": False, "note": "GPU 0; no model was loaded and no inference ran"},
        "local_disk": {
            "budget_bytes": 2 * 1024 ** 3,
            "media_bytes": sum(p.stat().st_size for p in media),
            "media_files": len(media),
            "code_and_reports_bytes": sum(f["bytes"] for f in code + reports + ui),
            "total_bytes": sum(p.stat().st_size for p in media) + sum(
                f["bytes"] for f in code + reports + ui),
            "within_budget": (sum(p.stat().st_size for p in media) + sum(
                f["bytes"] for f in code + reports + ui)) < 2 * 1024 ** 3,
        },
        "remote": {
            "host_alias": "aic-inspur-home",
            "writes_performed": 0,
            "bytes_streamed_to_local": sum(p.stat().st_size for p in media),
            "note": "only read-only commands; the corpus was streamed for the 8 selected files",
        },
        "cpu_seconds_registered": {
            "remote_inventory_and_probe": 13,
            "local_media_analysis": 20.8,
            "tool_validation_and_builders": 3,
            "note": "hand-added wall-clock measurements from the commands in this round; "
                    "budget is 20 minutes",
        },
        "network_operations": [
            {"op": "ssh inventory / sampling", "timeout_sec": 600, "result": "ok"},
            {"op": "ssh ffprobe+sha256 of 8 files", "timeout_sec": 900, "result": "ok"},
            {"op": "ssh log reading (bddownload/unzip)", "timeout_sec": 300, "result": "ok"},
            {"op": "ssh copy of 8 files (cat over ssh)", "timeout_sec": 300, "result": "ok, 8/8 sha256 match"},
            {"op": "ssh 818-row cardinality audit", "timeout_sec": 300, "result": "ok"},
            {"op": "public internet", "result": "not used: no page, dataset or model was downloaded"},
        ],
        "headless_browser_render": {"used": True, "note": "Chrome --headless=new, local file:// only"},
        "artifacts": {"code": code, "reports": reports, "ui_render": ui},
    }


def main() -> int:
    manifest = load(P1B / "pilot_manifest.json")
    source = build_source_audit(manifest)
    selection = build_selection_manifest(manifest)
    usage = build_resource_usage(manifest)
    for name, payload in (("source_and_license_audit.json", source),
                          ("selection_manifest.json", selection),
                          ("RESOURCE_USAGE.json", usage)):
        (PHASE1B / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")
        print("wrote", (PHASE1B / name).relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
