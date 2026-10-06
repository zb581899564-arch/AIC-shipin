#!/usr/bin/env python3
"""Run a bounded 2x2 temporal diagnostic without creating new supervision.

The four arms use the same source-disjoint QVHighlights dev rows:
base/LoRA x query-conditioned/generic prompt.  Query-conditioned duration F1
is an in-domain diagnostic.  Generic-prompt scores against query-conditioned
windows are recorded only as an OOD transfer stress test and are never called
AIC highlight accuracy.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any, Iterable


ROOT = Path("/home/inspur/aic_video_work")
HERE = ROOT / "round3_20260912" / "temporal_query_transfer"
DEV = ROOT / "data_qvh_confirmed_20260910" / "dev.jsonl"
GATE = ROOT / "data_qvh_confirmed_20260910" / "gate" / "training_gate.json"
SOURCE_ATTESTATION = ROOT / "data_qvh_confirmed_20260910" / "source_attestation.json"
MODEL = ROOT / "models" / "Qwen3-VL-4B-Instruct"
ADAPTER = ROOT / "training_round2_20260910" / "formal_v1" / "best"
PYTHON = ROOT / "env" / "qwen3vl_isolated_20260910" / "bin" / "python"
EXPECTED = {
    str(DEV): "6a9feadadc62834c4843d805aff8d6b5aad895134cd154ad0d75990fc680acd6",
    str(ADAPTER / "adapter_model.safetensors"): "678c45d362020df887936f9623bb2a955feb006fc3ec2ef66885a47bb6f06ba3",
    str(ADAPTER / "adapter_config.json"): "75f7929d56cc483193d911101573cb71c4a112d278be5acf1c19e80af49858e9",
    str(ROOT / "inference_v2" / "baseline_v2.py"): "be00177024135ba10bb4bad36c39ee3dd6502eef3494810a4b8e49008f04a9d9",
    str(ROOT / "inference_v2" / "qwen_io.py"): "2e501be2c5bc99f1dab4efe9f71491f42c6732f26df1d5bc912cba2ea89a70f3",
    str(ROOT / "inference_v2" / "temporal.py"): "74b3a611731b70ae724db9ec360e195b4de32edc2fe393c7dada58d0277f54b3",
}


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_no}: row is not an object")
                rows.append(value)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def write_jsonl_once(path: Path, rows: list[dict[str, Any]]) -> None:
    rendered = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"refusing to replace a different frozen index: {path}")
        return
    path.write_text(rendered, encoding="utf-8")


def validate_and_select(num_groups: int, seed: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    observed = {path: sha256(Path(path)) for path in EXPECTED}
    mismatch = {path: {"expected": EXPECTED[path], "observed": value}
                for path, value in observed.items() if value != EXPECTED[path]}
    if mismatch:
        raise RuntimeError(f"immutable input hash mismatch: {json.dumps(mismatch, sort_keys=True)}")
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    if not (gate.get("passed") is True and gate.get("alignment_verified") is True):
        raise RuntimeError("QVHighlights accepted-data gate is not passed/aligned")
    if gate.get("task_type") != "query_moment_retrieval":
        raise RuntimeError("unexpected task type")
    if gate.get("cross_split_source_group_overlap") != {
        "dev__holdout": [], "train__dev": [], "train__holdout": []
    }:
        raise RuntimeError("source-group split overlap is no longer empty")
    attestation = json.loads(SOURCE_ATTESTATION.read_text(encoding="utf-8"))
    limitations = attestation.get("limitations", [])
    required_limitation = "Query-conditioned temporal auxiliary training only; not AIC crop ground truth"
    if required_limitation not in limitations:
        raise RuntimeError("source attestation no longer carries the required semantic limitation")

    rows = read_jsonl(DEV)
    if len(rows) != 100:
        raise RuntimeError(f"expected 100 accepted dev rows, got {len(rows)}")
    by_group: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not (row.get("trusted_identity") is True and row.get("alignment_verified") is True):
            raise RuntimeError(f"untrusted or unaligned dev row: {row.get('video_id')}")
        if row.get("split") != "dev" or row.get("official_split") != "val":
            raise RuntimeError(f"unexpected split identity: {row.get('video_id')}")
        if row.get("task_type") != "query_moment_retrieval":
            raise RuntimeError(f"unexpected row task type: {row.get('video_id')}")
        if not isinstance(row.get("query"), str) or not row["query"].strip():
            raise RuntimeError(f"missing query: {row.get('video_id')}")
        if row.get("answer", {}).get("segments") != row.get("relevant_windows"):
            raise RuntimeError(f"answer is not query-conditioned relevant_windows: {row.get('video_id')}")
        duration = row.get("duration_sec")
        if not isinstance(duration, (int, float)) or not math.isfinite(float(duration)) or duration <= 0:
            raise RuntimeError(f"invalid duration: {row.get('video_id')}")
        if not Path(str(row.get("video_path", ""))).is_file():
            raise RuntimeError(f"missing media: {row.get('video_path')}")
        group = str(row.get("source_group", ""))
        if not group:
            raise RuntimeError("missing source_group")
        by_group.setdefault(group, []).append(row)
    if not 1 <= num_groups <= len(by_group):
        raise ValueError(f"num-groups must be 1..{len(by_group)}")

    def rank(text: str) -> str:
        return hashlib.sha256(f"{seed}:{text}".encode("utf-8")).hexdigest()

    selected: list[dict[str, Any]] = []
    for group in sorted(by_group, key=rank)[:num_groups]:
        selected.append(min(by_group[group], key=lambda row: rank(str(row["video_id"]))))
    selected.sort(key=lambda row: str(row["video_id"]))
    if len({str(row["source_group"]) for row in selected}) != len(selected):
        raise RuntimeError("selection is not one-row-per-source-group")
    manifest = {
        "schema_version": "round3_temporal_query_transfer_v1",
        "created_utc": utc(),
        "seed": seed,
        "selected_rows": len(selected),
        "selected_source_groups": len({str(row["source_group"]) for row in selected}),
        "video_ids": [str(row["video_id"]) for row in selected],
        "source_groups": [str(row["source_group"]) for row in selected],
        "source_split": "QVHighlights official val -> accepted dev",
        "task_type": "query_moment_retrieval",
        "target_semantics": "official query-conditioned relevant_windows",
        "generic_arm_semantics": "OOD prompt-transfer stress test against query-conditioned reference; not AIC generic-highlight validation",
        "query_free_supervision": "NOT_AVAILABLE; no training is performed",
        "bbox_ground_truth": "NOT_AVAILABLE",
        "hashes": observed,
    }
    return selected, manifest


def union(intervals: Iterable[Iterable[float]]) -> list[tuple[float, float]]:
    clean = sorted((float(x[0]), float(x[1])) for x in intervals if len(x) == 2 and float(x[1]) > float(x[0]))
    out: list[list[float]] = []
    for start, end in clean:
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(a, b) for a, b in out]


def length(intervals: Iterable[tuple[float, float]]) -> float:
    return sum(end - start for start, end in intervals)


def overlap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    i = j = 0
    total = 0.0
    while i < len(a) and j < len(b):
        total += max(0.0, min(a[i][1], b[j][1]) - max(a[i][0], b[j][0]))
        if a[i][1] <= b[j][1]:
            i += 1
        else:
            j += 1
    return total


def score_arm(index: list[dict[str, Any]], prediction_path: Path, semantics: str) -> dict[str, Any]:
    gt = {str(row["video_id"]): union(row["answer"]["segments"]) for row in index}
    preds = {str(row["video_id"]): row for row in read_jsonl(prediction_path)} if prediction_path.exists() else {}
    per_video: list[dict[str, Any]] = []
    for video_id in sorted(gt):
        row = preds.get(video_id)
        status = str(row.get("status")) if row else "missing"
        pred = union(row.get("segments_sec", [])) if row and status in {"ok", "valid_empty"} else []
        inter = overlap(gt[video_id], pred)
        gt_len, pred_len = length(gt[video_id]), length(pred)
        precision = inter / pred_len if pred_len else 0.0
        recall = inter / gt_len if gt_len else (1.0 if not pred_len else 0.0)
        f1 = 2 * inter / (gt_len + pred_len) if gt_len + pred_len else 1.0
        duration = float(next(row0["duration_sec"] for row0 in index if str(row0["video_id"]) == video_id))
        per_video.append({
            "video_id": video_id, "status": status, "precision": precision,
            "recall": recall, "f1": f1, "gt_seconds": gt_len,
            "pred_seconds": pred_len, "predicted_duration_ratio": pred_len / duration,
        })
    available = [row for row in per_video if row["status"] != "missing"]
    return {
        "semantics": semantics,
        "expected_videos": len(per_video),
        "completed_videos": len(available),
        "invalid_videos": sum(row["status"] == "invalid" for row in available),
        "valid_empty_videos": sum(row["status"] == "valid_empty" for row in available),
        "mean_precision": statistics.fmean(row["precision"] for row in available) if available else None,
        "mean_recall": statistics.fmean(row["recall"] for row in available) if available else None,
        "mean_duration_union_f1": statistics.fmean(row["f1"] for row in available) if available else None,
        "mean_predicted_duration_ratio": statistics.fmean(row["predicted_duration_ratio"] for row in available) if available else None,
        "per_video": per_video,
    }


def write_report(index: list[dict[str, Any]], arms: list[dict[str, Any]]) -> None:
    summaries: dict[str, Any] = {}
    for arm in arms:
        summaries[arm["name"]] = score_arm(index, arm["out"], arm["score_semantics"])
    comparisons: dict[str, Any] = {}
    for left, right, name in [
        ("base_query", "lora_query", "adapter_minus_base_query"),
        ("base_generic", "lora_generic", "adapter_minus_base_generic_stress"),
        ("base_generic", "base_query", "query_minus_generic_base"),
        ("lora_generic", "lora_query", "query_minus_generic_lora"),
    ]:
        lrows = {row["video_id"]: row for row in summaries[left]["per_video"] if row["status"] != "missing"}
        rrows = {row["video_id"]: row for row in summaries[right]["per_video"] if row["status"] != "missing"}
        common = sorted(set(lrows) & set(rrows))
        deltas = [rrows[key]["f1"] - lrows[key]["f1"] for key in common]
        comparisons[name] = {
            "direction": f"{right} - {left}", "paired_videos": len(common),
            "mean_f1_delta": statistics.fmean(deltas) if deltas else None,
            "median_f1_delta": statistics.median(deltas) if deltas else None,
            "wins_ties_losses": {
                "wins": sum(value > 1e-12 for value in deltas),
                "ties": sum(abs(value) <= 1e-12 for value in deltas),
                "losses": sum(value < -1e-12 for value in deltas),
            },
        }
    if "lora_query_128" in summaries:
        lrows = {row["video_id"]: row for row in summaries["lora_query"]["per_video"] if row["status"] != "missing"}
        rrows = {row["video_id"]: row for row in summaries["lora_query_128"]["per_video"] if row["status"] != "missing"}
        common = sorted(set(lrows) & set(rrows))
        deltas = [rrows[key]["f1"] - lrows[key]["f1"] for key in common]
        comparisons["lora_128_minus_64_query"] = {
            "direction": "lora_query_128 - lora_query",
            "paired_videos": len(common),
            "mean_f1_delta": statistics.fmean(deltas) if deltas else None,
            "median_f1_delta": statistics.median(deltas) if deltas else None,
            "wins_ties_losses": {
                "wins": sum(value > 1e-12 for value in deltas),
                "ties": sum(abs(value) <= 1e-12 for value in deltas),
                "losses": sum(value < -1e-12 for value in deltas),
            },
        }
    write_json(HERE / "report.json", {
        "schema_version": "round3_temporal_query_transfer_report_v1",
        "updated_utc": utc(),
        "primary_decision_metric": "paired mean duration-union F1 delta: lora_query - base_query on QVHighlights query-conditioned dev",
        "generic_metric_warning": "Generic arms are OOD stress tests scored against query-conditioned windows; they do not measure AIC generic-highlight quality.",
        "arms": summaries,
        "paired_comparisons": comparisons,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-groups", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260912)
    parser.add_argument("--include-lora-query-128", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    HERE.mkdir(parents=True, exist_ok=True)
    index, manifest = validate_and_select(args.num_groups, args.seed)
    index_path = HERE / f"dev_{args.num_groups}groups_seed{args.seed}.jsonl"
    write_jsonl_once(index_path, index)
    manifest["index_path"] = str(index_path)
    manifest["index_sha256"] = sha256(index_path)
    manifest_path = HERE / "manifest.json"
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        stable_keys = ("seed", "selected_rows", "video_ids", "source_groups", "index_sha256")
        if any(prior.get(key) != manifest.get(key) for key in stable_keys):
            raise RuntimeError("existing manifest selects a different experiment; refusing overwrite")
    write_json(manifest_path, manifest)

    arms = []
    arm_specs = [
        ("base_query", True, False, 64, "IN_DOMAIN_QVH_QUERY_CONDITIONED"),
        ("lora_query", True, True, 64, "IN_DOMAIN_QVH_QUERY_CONDITIONED"),
        ("base_generic", False, False, 64, "OOD_GENERIC_PROMPT_VS_QUERY_REFERENCE_ONLY"),
        ("lora_generic", False, True, 64, "OOD_GENERIC_PROMPT_VS_QUERY_REFERENCE_ONLY"),
    ]
    if args.include_lora_query_128:
        arm_specs.append(("lora_query_128", True, True, 128, "IN_DOMAIN_QVH_QUERY_128_FRAME_SAMPLING"))
    for name, query_aware, adapter, max_frames, semantics in arm_specs:
        arm_dir = HERE / "runs" / name
        arm_dir.mkdir(parents=True, exist_ok=True)
        arms.append({
            "name": name, "query_aware": query_aware, "adapter": adapter,
            "max_frames": max_frames,
            "score_semantics": semantics, "out": arm_dir / "temporal_predictions.jsonl",
            "raw": arm_dir / "raw.jsonl", "log": arm_dir / "run.log",
        })
    if args.prepare_only:
        if not (HERE / "report.json").exists():
            write_report(index, arms)
        print(json.dumps({
            "status": "prepared",
            "manifest": str(manifest_path),
            "index": str(index_path),
            "arms": [arm["name"] for arm in arms],
        }, ensure_ascii=False))
        return 0

    existing_outputs = [
        str(arm["out"]) for arm in arms
        if arm["out"].exists() and arm["out"].stat().st_size > 0
    ]
    if existing_outputs:
        raise RuntimeError(
            "formal run refuses existing non-empty temporal outputs; choose a new round/job directory: "
            + json.dumps(existing_outputs)
        )
    write_report(index, arms)

    env = dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               TOKENIZERS_PARALLELISM="false", PYTHONPATH=str(ROOT))
    for arm in arms:
        command = [
            str(PYTHON), "-m", "inference_v2.baseline_v2",
            "--index", str(index_path), "--temporal-only", "--temporal-policy", "multi",
            "--constrained-json", "--detect-fps", "2", "--max-video-frames", str(arm["max_frames"]),
            "--max-pixels", "131072", "--detect-tokens", "256",
            "--temporal-out", str(arm["out"]), "--raw-out", str(arm["raw"]),
        ]
        if arm["query_aware"]:
            command.append("--query-aware")
        if arm["adapter"]:
            command.extend(["--temporal-adapter", str(ADAPTER)])
        started = time.monotonic()
        with arm["log"].open("a", encoding="utf-8") as log:
            log.write("\nCOMMAND " + json.dumps(command) + "\n")
            log.flush()
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, check=False)
        write_json(arm["log"].with_suffix(".status.json"), {
            "arm": arm["name"], "returncode": completed.returncode,
            "elapsed_seconds": time.monotonic() - started, "finished_utc": utc(),
            "command": command,
        })
        write_report(index, arms)
        if completed.returncode != 0:
            raise RuntimeError(f"arm {arm['name']} failed; see {arm['log']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
