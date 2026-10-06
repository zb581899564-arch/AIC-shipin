from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from protected_boundary import identity_digest


RUN_ID = "round6_p2r9_20260920T040552Z"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_weak_holdout_identities(path: Path) -> list[dict[str, Any]]:
    identities = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("split") != "holdout":
            continue
        identities.append({
            "row_index": row["row_index"],
            "video_id": row["video_id"],
            "source_vid": row["source_vid"],
            "youtube_id": row["youtube_id"],
        })
    return identities


def extract_gnmc_item_ids_without_reference_parse(path: Path) -> list[str]:
    item_ids = []
    pattern = re.compile(r'"item_id"\s*:\s*("(?:[^"\\]|\\.)*")')
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = pattern.search(line)
        if match is None:
            raise RuntimeError("GNMC exposed manifest line lacks item_id")
        item_ids.append(json.loads(match.group(1)))
    return item_ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=False)

    required_inputs = [
        "AGENTS.md",
        "ROADMAP.md",
        "prompts/round6_p2r9_native_portrait_reference_goal.md",
        "prompts/round6_p2r_reference_gate_goal.md",
        "reports/round6_score_alignment/p2r_reference_gate/SUPERVISOR_REVIEW_20260920.md",
        "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/REPORT.md",
        "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/candidate_registry.json",
        "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/source_and_usage_audit.json",
        "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/boundary_incident.json",
        "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/final_freeze.json",
        "reports/round6_score_alignment/p2d_deployable_dev/SUPERVISOR_REVIEW_20260919.md",
        "reports/round6_score_alignment/training_alignment_20260917/REPORT.md",
        "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl",
        "reports/round6_score_alignment/phase1b/source_and_license_audit.json",
        "reports/round6_score_alignment/phase0/scoring_spec.md",
        "reports/round6_score_alignment/phase1b/annotation_protocol.md",
        "reports/round6_score_alignment/phase1b_fix/annotation_protocol.md",
        "reports/temporal_round5/evidence/split_manifest.json",
        "reports/round6_score_alignment/phase1b/training_cardinality_audit.json",
    ]
    input_paths = [root / rel for rel in required_inputs]
    missing = [p.relative_to(root).as_posix() for p in input_paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"required frozen inputs missing: {missing}")

    weak_path = root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl"
    weak_ids = parse_weak_holdout_identities(weak_path)
    if len(weak_ids) != 64:
        raise RuntimeError(f"expected 64 weak holdout identities, got {len(weak_ids)}")

    gnmc_path = root / "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/sealed_holdout_manifest.jsonl"
    gnmc_ids = extract_gnmc_item_ids_without_reference_parse(gnmc_path)
    if len(gnmc_ids) != 4:
        raise RuntimeError(f"expected 4 exposed GNMC identities, got {len(gnmc_ids)}")

    old_holdout_sha = "e2c8d0cf0838c3188fb1e1a98d27d633b8e551c577f3b7d7bb5d39090d7ad193"
    blocked_identity_digests = sorted(
        [identity_digest("round6_weak_holdout", row) for row in weak_ids]
        + [identity_digest("p2r_gnmc_exposed_sealed", {"item_id": item_id}) for item_id in gnmc_ids]
    )
    registry = {
        "schema": "p2r9_protected_input_registry_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "policy": "deny exposed or previously used rows from process_sealed_holdout; identities are stored only as salted-free SHA-256 digests and no reference payload is copied",
        "categories": [
            {
                "name": "round6_weak_holdout_64",
                "count": 64,
                "status": "EXPOSED_WEAK_HOLDOUT_NEVER_SEALED",
                "identity_digest_count": len(weak_ids),
                "reference_payload_read": False,
                "source_file_sha256": sha256_file(weak_path),
            },
            {
                "name": "p2r_gnmc_exposed_sealed_4",
                "count": 4,
                "status": "REFERENCE_AUDIT_ONLY_NEVER_SEALED",
                "identity_digest_count": len(gnmc_ids),
                "reference_payload_read": False,
                "identity_extraction": "regex extracts item_id only; JSON reference payload is never parsed",
                "source_file_sha256": sha256_file(gnmc_path),
            },
            {
                "name": "temporal_round5_historical_holdout_88",
                "count": 88,
                "source_groups": 80,
                "status": "PREVIOUSLY_USED_HISTORICAL_DIAGNOSTIC_NEVER_SEALED",
                "local_payload_available": False,
                "dataset_sha256": old_holdout_sha,
                "blocking_scope": "entire dataset hash and known provenance namespace",
            },
        ],
        "blocked_identity_sha256": blocked_identity_digests,
        "blocked_dataset_sha256": [old_holdout_sha],
        "blocked_provenance_markers": [
            "/temporal_round5/data/holdout.jsonl",
            "round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl#holdout",
            "p2r_reference_gate/round6_p2r_20260919t154701z/sealed_holdout_manifest.jsonl",
        ],
        "counts": {"blocked_identity_digests": len(blocked_identity_digests), "blocked_dataset_hashes": 1},
    }
    write_json(run_dir / "protected_input_registry.json", registry)

    inventory = []
    excluded_roots = {".git", "__pycache__"}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in excluded_roots for part in path.parts):
            continue
        inventory.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
        })
    write_json(run_dir / "workspace_inventory_presearch.json", {
        "schema": "p2r9_workspace_inventory_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(inventory),
        "files": inventory,
    })
    write_json(run_dir / "input_freeze_presearch.json", {
        "schema": "p2r9_input_freeze_v1",
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": [record(path, root) for path in input_paths],
        "p2r_final_freeze_sha256": sha256_file(root / "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/final_freeze.json"),
        "workspace_is_git_repository": False,
    })
    write_json(run_dir / "search_protocol_frozen.json", {
        "schema": "p2r9_search_protocol_v1",
        "frozen_before_online_candidate_search": True,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "priority": ["LIVE-YT Video Cropping", "GAICD", "MIR-Thumb", "bounded new first-party candidates"],
        "questions": [
            "Is native 9:16 human-composition annotation first-party and byte-bound?",
            "Are annotation, data, and underlying-media terms explicit for local noncommercial competition research diagnosis?",
            "Can at least 8 independent source groups be frozen as 4 dev plus 4 process-sealed?",
            "Can source identity and bounded AIC overlap be checked without opening competition test media?",
        ],
        "new_candidate_queries": [
            "native 9:16 human crop annotation dataset official",
            "portrait vertical video reframing human annotation dataset official",
            "9:16 image cropping human crop boxes dataset official",
            "vertical video composition crop trajectory dataset official",
        ],
        "stop_conditions": [
            "complete first-party review of the three fixed-priority candidates",
            "run the four frozen new-candidate queries and inspect only plausible first-party leads",
            "stop after 12 new plausible leads or when two consecutive query families yield no qualifying new lead",
            "do not broaden to detection, tracking, segmentation, saliency, aesthetics-only, or algorithm-only boxes",
            "do not download candidate media before all written qualification gates pass",
        ],
        "download_gates": {"metadata_per_candidate_bytes": 104857600, "total_new_bytes": 3221225472, "single_media_bytes": 524288000},
    })
    print(json.dumps({
        "status": "PASS",
        "run_id": RUN_ID,
        "protected_counts": {"weak": len(weak_ids), "gnmc": len(gnmc_ids), "historical": 88},
        "input_count": len(input_paths),
        "workspace_file_count": len(inventory),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

