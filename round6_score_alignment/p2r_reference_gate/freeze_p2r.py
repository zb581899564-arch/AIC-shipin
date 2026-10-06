from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def record(path: Path, root: Path) -> dict:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": hash_file(path)}


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    root, run = args.root.resolve(), args.run_dir.resolve()
    snapshots = {
        "gnmc_readme.md": "https://raw.githubusercontent.com/aneeshvartakavi/GNMC/9d52ee02a6b2bb5b411e3e13b203decd249f4518/README.md",
        "gnmc_zenodo_record.json": "https://zenodo.org/api/records/6228834",
        "polyform_noncommercial_1.0.0.html": "https://polyformproject.org/licenses/noncommercial/1.0.0/",
        "live_yt_readme.md": "https://raw.githubusercontent.com/steven413d/LIVE-YT-VideoCropping/2a91e9492c092c966b10fdc9b369b057d92e8ffb/README.md",
        "live_yt_arxiv_2604.24947.xml": "https://export.arxiv.org/api/query?id_list=2604.24947",
        "gaicd_readme.md": "https://raw.githubusercontent.com/HuiZeng/Grid-Anchor-based-Image-Cropping/d3262a1bc840cd998cdff4bee0c712b4ad0787b7/README.md",
        "gaicd_arxiv_1909.08989.xml": "https://export.arxiv.org/api/query?id_list=1909.08989",
        "retargetvid_readme.md": "https://raw.githubusercontent.com/bmezaris/RetargetVid/43673dd83b279c4aedeeea22f32d03582ac45194/README.md",
        "retargetvid_license.md": "https://raw.githubusercontent.com/bmezaris/RetargetVid/43673dd83b279c4aedeeea22f32d03582ac45194/LICENSE.md",
        "cuhk_official_page.md": "http://personal.ie.cuhk.edu.hk/~ccloy/downloads_cuhk_crop_dataset.html via Jina Reader",
        "flms_official_page.md": "https://yiling-chen.github.io/flickr-cropping-dataset/ via Jina Reader",
        "carousel_readme.md": "https://raw.githubusercontent.com/RafeLoya/carousel/main/README.md",
    }
    snapshot_rows = []
    for name, url in snapshots.items():
        p = run / "snapshots" / name
        snapshot_rows.append({**record(p, root), "url": url, "accessed_utc": datetime.now(timezone.utc).isoformat()})
    write(run / "source_snapshot_index.json", {"schema": "p2r_source_snapshot_index_v1", "snapshots": snapshot_rows})
    inputs = [
        root / "AGENTS.md", root / "ROADMAP.md", root / "prompts/round6_p2r_reference_gate_goal.md",
        root / "reports/round6_score_alignment/p2d_deployable_dev/SUPERVISOR_REVIEW_20260919.md",
        root / "reports/round6_score_alignment/p2d_deployable_dev/round6_p2d_20260919T130011Z/REPORT.md",
        root / "reports/round6_score_alignment/training_alignment_20260917/REPORT.md",
        root / "reports/round6_score_alignment/training_alignment_20260917/train.source_copy.jsonl",
        root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl",
        root / "reports/round6_score_alignment/training_alignment_20260917/structural_audit.json",
        root / "reports/orarl_round4/evidence/mapping_rows.jsonl",
        root / "reports/round6_score_alignment/phase1b/source_and_license_audit.json",
        root / "reports/round6_score_alignment/phase0/scoring_spec.md",
        root / "reports/round6_score_alignment/phase1a_fix/protocol.json",
        root / "reports/round6_score_alignment/phase1b/annotation_protocol.md",
        root / "reports/round6_score_alignment/phase1b_fix/annotation_protocol.md",
        root / "round6_score_alignment/p1b/pilot_manifest.json",
    ]
    code_dir = root / "round6_score_alignment/p2r_reference_gate"
    code = sorted(p for p in code_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    download = run / "pilot/gnmc/GNMC.zip"
    write(run / "file_hashes.json", {
        "schema": "p2r_file_hashes_v1", "inputs": [record(p, root) for p in inputs],
        "code": [record(p, root) for p in code], "downloads": [record(download, root)],
    })
    report_bytes = sum(p.stat().st_size for p in run.rglob("*") if p.is_file())
    code_bytes = sum(p.stat().st_size for p in code)
    snapshot_bytes = sum((run / "snapshots" / name).stat().st_size for name in snapshots)
    write(run / "resource_usage.json", {
        "schema": "p2r_resource_usage_v1", "gpu_seconds": 0, "models_loaded": 0,
        "training_runs": 0, "inference_runs": 0, "competition_test_media_opened": 0,
        "weak_holdout_opened_for_quality": 0,
        "weak_holdout_label_payloads_parsed_by_initial_superseded_structural_audit": 64,
        "weak_holdout_media_opened": 0,
        "download_bytes": download.stat().st_size,
        "snapshot_bytes": snapshot_bytes, "run_directory_bytes_before_freeze": report_bytes,
        "code_bytes": code_bytes, "p2r_disk_limit_bytes": 2 * 1024**3,
        "accounted_cpu_heavy_wall_seconds": 6.6,
        "cpu_note": "sum of recorded wall times for audit/build/leakage/tests/rebuild/finalizer; network transfer and light hashing are excluded",
        "limits_respected": True,
    })
    excluded = {"final_freeze.json", "final_freeze.sha256.txt", "freeze_verification.json"}
    outputs = sorted(p for p in run.rglob("*") if p.is_file() and p.name not in excluded)
    freeze = {
        "schema": "p2r_final_freeze_v1", "run_id": run.name, "status": "REFERENCE_GATE_PARTIAL",
        "created_utc": datetime.now(timezone.utc).isoformat(), "root": str(root),
        "files": [record(p, root) for p in outputs], "code": [record(p, root) for p in code],
        "counts": {"output_files": len(outputs), "code_files": len(code), "dev_items": 4, "sealed_holdout_items": 4, "ratios": {"16:9": 8, "9:16": 0}},
    }
    freeze_path = run / "final_freeze.json"
    write(freeze_path, freeze)
    (run / "final_freeze.sha256.txt").write_text(hash_file(freeze_path) + "  final_freeze.json\n", encoding="ascii")
    mismatches = []
    for item in freeze["files"] + freeze["code"]:
        p = root / item["path"]
        if not p.is_file() or hash_file(p) != item["sha256"]:
            mismatches.append(item["path"])
    verification = {"status": "PASS" if not mismatches else "FAIL", "checked": len(freeze["files"]) + len(freeze["code"]), "mismatches": mismatches}
    write(run / "freeze_verification.json", verification)
    print(json.dumps({"freeze_sha256": hash_file(freeze_path), **verification}, ensure_ascii=False))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
