"""Freeze R7 train/dev/confirm manifests before any R7 model output."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from r7_core import SEED, select_stratified_groups, stable_key


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def summarize(rows: list[dict]) -> dict:
    return {
        "rows": len(rows),
        "groups": len({r["youtube_id"] for r in rows}),
        "mapping_status": dict(Counter(r["mapping_status"] for r in rows)),
        "segment_count": dict(Counter(str(r["n_segments"]) for r in rows)),
        "duration_bins": dict(Counter(
            "le10" if r["clip_duration_sec"] <= 10 else
            "10to20" if r["clip_duration_sec"] <= 20 else "gt20"
            for r in rows)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pts-audit", type=Path, required=True)
    ap.add_argument("--old-train", type=Path, required=True)
    ap.add_argument("--old-dev", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    expected = ["train_temporal.jsonl", "dev_temporal.jsonl", "confirm_temporal.jsonl",
                "smoke_temporal.jsonl", "split_freeze.json"]
    if any((args.out_dir / name).exists() for name in expected):
        raise RuntimeError("refusing to overwrite frozen R7 manifests")

    audited = read_jsonl(args.pts_audit)
    passed = [r for r in audited if r.get("pts_audit_status") == "PASS"]
    if not passed:
        raise RuntimeError("no PTS-audited candidates")
    if len({r["row_index"] for r in passed}) != len(passed):
        raise RuntimeError("duplicate audited row_index")
    old_train, old_dev = read_jsonl(args.old_train), read_jsonl(args.old_dev)
    historical_groups = {r["youtube_id"] for r in old_train + old_dev}
    if len(historical_groups) != 409:
        raise RuntimeError(f"historical P2-T2 exposure changed: {len(historical_groups)}")

    split = select_stratified_groups(passed, historical_groups, 96, 96, SEED)
    outputs = {"train": [], "dev": [], "confirm": []}
    for row in passed:
        group = row["youtube_id"]
        target = "dev" if group in split["dev"] else (
            "confirm" if group in split["confirm"] else "train")
        out = dict(row)
        out["split"] = target
        out["diagnostic_status"] = (
            "MODEL_UNSEEN_FIXED_WEAK_DIAGNOSTIC" if target != "train"
            else "WEAK_TEACHER_TRAIN")
        out["historical_p2t2_group_exposure"] = group in historical_groups
        outputs[target].append(out)
    for name in outputs:
        outputs[name].sort(key=lambda r: (r["youtube_id"], r["row_index"]))

    group_sets = {name: {r["youtube_id"] for r in rows}
                  for name, rows in outputs.items()}
    if group_sets["train"] & group_sets["dev"] or group_sets["train"] & group_sets["confirm"] \
            or group_sets["dev"] & group_sets["confirm"]:
        raise RuntimeError("source group leakage")
    if group_sets["dev"] & historical_groups or group_sets["confirm"] & historical_groups:
        raise RuntimeError("diagnostic group has P2-T2 train/dev exposure")
    if len(group_sets["dev"]) != 96 or len(group_sets["confirm"]) != 96:
        raise RuntimeError("diagnostic group cardinality changed")

    train_path = args.out_dir / "train_temporal.jsonl"
    dev_path = args.out_dir / "dev_temporal.jsonl"
    confirm_path = args.out_dir / "confirm_temporal.jsonl"
    write_jsonl(train_path, outputs["train"])
    write_jsonl(dev_path, outputs["dev"])
    write_jsonl(confirm_path, outputs["confirm"])

    smoke_groups = sorted(group_sets["train"],
                          key=lambda g: stable_key("smoke", g, SEED))[:16]
    smoke = []
    for group in smoke_groups:
        smoke.append(min((r for r in outputs["train"] if r["youtube_id"] == group),
                         key=lambda r: r["row_index"]))
    smoke_path = args.out_dir / "smoke_temporal.jsonl"
    write_jsonl(smoke_path, smoke)

    paths = {"train": train_path, "dev": dev_path, "confirm": confirm_path,
             "smoke": smoke_path}
    report = {
        "status": "FROZEN_BEFORE_R7_MODEL_OUTPUT",
        "seed": SEED,
        "metric_status": "WEAK_TEACHER_NOT_OFFICIAL_GROUND_TRUTH",
        "passed_rows": len(passed),
        "passed_groups": len({r["youtube_id"] for r in passed}),
        "historical_p2t2_groups": len(historical_groups),
        "model_unseen_candidate_groups": len(split["model_unseen_candidates"]),
        "splits": {name: summarize(rows) for name, rows in outputs.items()},
        "strata": split["strata"],
        "group_overlap": {
            "train_dev": len(group_sets["train"] & group_sets["dev"]),
            "train_confirm": len(group_sets["train"] & group_sets["confirm"]),
            "dev_confirm": len(group_sets["dev"] & group_sets["confirm"]),
            "dev_historical": len(group_sets["dev"] & historical_groups),
            "confirm_historical": len(group_sets["confirm"] & historical_groups),
        },
        "input_hashes": {
            "pts_audit": sha256(args.pts_audit),
            "old_train": sha256(args.old_train),
            "old_dev": sha256(args.old_dev),
        },
        "manifest_hashes": {name: sha256(path) for name, path in paths.items()},
        "holdout_disclosure": (
            "All labels and preliminary split metadata have been exposed. Dev and confirm "
            "are model-unseen fixed weak diagnostics, not blind or human ground truth."),
    }
    (args.out_dir / "split_freeze.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
