"""Fail-closed verification for the frozen R7 train/dev/confirm manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--old-train", type=Path, required=True)
    parser.add_argument("--old-dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError("refusing to overwrite frozen-input verification")

    freeze_path = args.inputs / "split_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    paths = {
        "train": args.inputs / "train_temporal.jsonl",
        "dev": args.inputs / "dev_temporal.jsonl",
        "confirm": args.inputs / "confirm_temporal.jsonl",
        "smoke": args.inputs / "smoke_temporal.jsonl",
    }
    rows = {name: read_jsonl(path) for name, path in paths.items()}
    issues: list[str] = []
    for name in ("train", "dev", "confirm"):
        part = rows[name]
        if len({r["video_id"] for r in part}) != len(part):
            issues.append(f"{name}:duplicate_video_id")
        if any(r.get("split") != name for r in part):
            issues.append(f"{name}:split_marker_mismatch")
        if any(r.get("pts_audit_status") != "PASS" for r in part):
            issues.append(f"{name}:nonpassing_pts")
        if any(r.get("temporal_mapping_status") != "TEMPORAL_SECONDS_USABLE"
               for r in part):
            issues.append(f"{name}:temporal_status_mismatch")

    groups = {name: {r["youtube_id"] for r in rows[name]}
              for name in ("train", "dev", "confirm")}
    for left, right in (("train", "dev"), ("train", "confirm"),
                        ("dev", "confirm")):
        if groups[left] & groups[right]:
            issues.append(f"source_leakage:{left}:{right}")
    if len(groups["dev"]) != 96 or len(groups["confirm"]) != 96:
        issues.append("diagnostic_group_cardinality")

    historical = {
        row["youtube_id"]
        for path in (args.old_train, args.old_dev)
        for row in read_jsonl(path)
    }
    if len(historical) != 409:
        issues.append(f"historical_group_count:{len(historical)}")
    if groups["dev"] & historical:
        issues.append("dev_historical_exposure")
    if groups["confirm"] & historical:
        issues.append("confirm_historical_exposure")

    smoke_groups = {r["youtube_id"] for r in rows["smoke"]}
    if len(rows["smoke"]) != 16 or len(smoke_groups) != 16:
        issues.append("smoke_not_16_unique_groups")
    if not smoke_groups <= groups["train"]:
        issues.append("smoke_outside_train")
    if any(r.get("mapping_status") == "time_uncertain" and
           r.get("spatial_mapping_status") != "time_uncertain"
           for name in ("train", "dev", "confirm") for r in rows[name]):
        issues.append("time_uncertain_spatial_status_changed")

    hashes = {name: sha256(path) for name, path in paths.items()}
    if hashes != freeze.get("manifest_hashes"):
        issues.append("manifest_hash_mismatch")
    result = {
        "status": "R7_FROZEN_INPUTS_VERIFIED" if not issues else "R7_FROZEN_INPUTS_INVALID",
        "issues": issues,
        "rows": {name: len(value) for name, value in rows.items()},
        "groups": {name: len(value) for name, value in groups.items()},
        "historical_groups": len(historical),
        "manifest_hashes": hashes,
        "split_freeze_sha256": sha256(freeze_path),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
