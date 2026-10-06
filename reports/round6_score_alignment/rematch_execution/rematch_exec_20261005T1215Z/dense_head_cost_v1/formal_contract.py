"""Stdlib-only, fail-closed formal C admission. Never loads torch or media."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

PINNED_REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
FROZEN_TRAIN_SHA256 = "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf"
FROZEN_GROUPS_SHA256 = "3bfa284165cd088afb2b5872288e733053af192e6dec9926a2008ab795e34264"
PASS_DATA_STATUS = "PASS_C_FORMAL_BCE_SUPPORTED_WEAK_SUPERVISION"


class AdmissionRejected(RuntimeError):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise AdmissionRejected(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def bound_file(spec: dict, role: str) -> Path:
    require(isinstance(spec, dict), f"missing bound file: {role}")
    require(isinstance(spec.get("path"), str) and bool(spec["path"]), f"missing path: {role}")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", spec.get("sha256", ""))), f"missing SHA256: {role}")
    path = Path(spec["path"])
    require(path.is_file(), f"missing file: {role}: {path}")
    require(sha256(path) == spec["sha256"], f"bound file SHA256 mismatch: {role}")
    return path


def bound_json(spec: dict, role: str):
    require(isinstance(spec, dict) and Path(spec.get("path") or "").suffix == ".json",
            f"{role} requires metadata JSON, never a dev/confirm label JSONL")
    return read_json(bound_file(spec, role))


def train_bound_file(spec: dict, role: str) -> Path:
    require(isinstance(spec, dict) and spec.get("split") == "train", f"{role} must be explicitly train-only")
    name = Path(spec.get("path", "")).stem.lower()
    tokens = set(re.split(r"[^a-z0-9]+", name))
    require("train" in tokens and not (tokens & {"test", "dev", "confirm", "holdout", "val"}),
            f"refusing non-train manifest path: {role}")
    return bound_file(spec, role)


def positive_integer(value, name: str, allow_zero=False):
    require(type(value) is int and value >= (0 if allow_zero else 1), f"invalid frozen {name}")


def finite_positive(value, name: str, allow_zero=False):
    require(type(value) in (int, float) and math.isfinite(value)
            and value >= 0 and (allow_zero or value > 0), f"invalid frozen {name}")


def validate_config(config: dict) -> None:
    require(config.get("schema") == "aic_dense_formal_run_v1", "unrecognized formal run config schema")
    require(bool(config.get("run_id")), "missing run_id")
    for key in ("epochs", "max_optimizer_steps", "grad_accum", "seed", "max_frames", "decoder_threads",
                "max_sequence_length", "max_pixels"):
        positive_integer(config.get(key), key)
    positive_integer(config.get("warmup_optimizer_steps"), "warmup_optimizer_steps", allow_zero=True)
    require(config["warmup_optimizer_steps"] < config["max_optimizer_steps"], "warmup must end before step stop")
    for key in ("lr", "grad_clip_norm", "max_wall_seconds", "window_seconds", "grid_seconds",
                "decoder_pts_tolerance_seconds", "adam_beta1", "adam_beta2", "adam_eps"):
        finite_positive(config.get(key), key)
    finite_positive(config.get("weight_decay"), "weight_decay", allow_zero=True)
    finite_positive(config.get("min_lr_ratio"), "min_lr_ratio", allow_zero=True)
    require(config["min_lr_ratio"] <= 1, "invalid min_lr_ratio")
    require(config.get("scheduler") == "linear_warmup_decay", "scheduler must be explicitly frozen")
    require(config.get("optimizer") == "AdamW" and config["adam_beta1"] < 1 and config["adam_beta2"] < 1,
            "optimizer and AdamW betas must be explicitly frozen")
    require(config.get("stop_condition") in ("EPOCHS", "MAX_STEPS"), "explicit stop_condition required")
    require(config.get("precision") == "bf16" and config.get("attn_implementation") == "sdpa", "unreviewed precision/attention")
    require(config.get("gradient_checkpointing_use_reentrant") is False, "non-reentrant checkpointing is required")
    require(config.get("lora_rank") == 16 and config.get("lora_alpha") == 32,
            "unreviewed LoRA structure")
    require(config.get("lora_dropout") == 0.05, "LoRA dropout must be explicitly frozen at engineering value")
    require(config.get("revision") == PINNED_REVISION, "unapproved model revision")
    require(config.get("model_id") == "Qwen/Qwen3-VL-8B-Instruct", "unapproved model")
    require(config["window_seconds"] / config["grid_seconds"] <= 100, "too many grid queries")
    require(config["max_frames"] >= 2, "video requires at least a temporal pair")
    require(config["max_optimizer_steps"] >= 3, "at least three formal updates must be explicitly frozen")
    require(config["decoder_pts_tolerance_seconds"] <= 1e-3, "decoder PTS tolerance cannot hide temporal drift")
    output = PurePosixPath(config.get("out_dir", ""))
    allowed = PurePosixPath("/home/inspur/aic_video_work")
    require(output.is_absolute() and ".." not in output.parts and allowed in output.parents,
            "training output must remain under approved Linux development root")


def check_evidence(spec: dict, role: str) -> dict:
    require(isinstance(spec, dict) and spec.get("status") == "PASS", f"missing PASS evidence: {role}")
    evidence = bound_json(spec, role)
    require(evidence.get("status") == "PASS", f"underlying evidence does not pass: {role}")
    return evidence


def admit(admission_path: Path, config_path: Path) -> dict:
    """Return a frozen train-only contract or raise before any runtime import.

    The current STOP gate is rejected immediately, without opening train/media/weights.
    PASS certificates are the supervisor's evidence decisions, not invented by this entry.
    """
    admission = read_json(admission_path)
    require(admission.get("formal_c_bce_admitted") is True,
            "STOP: formal_c_bce_admitted must be explicitly true")
    require(admission.get("schema") == "aic_dense_formal_admission_v1"
            and admission.get("scope") == "FORMAL_C_TRAIN_ONLY", "missing train-only formal admission scope")
    gate = bound_json(admission.get("data_gate"), "data semantics gate")
    require(gate.get("status") == PASS_DATA_STATUS and gate.get("formal_c_bce_admitted") is True,
            f"STOP: data semantics gate is {gate.get('status', 'MISSING')}")
    for key in ("complete_observation_status", "generic_highlight_negative_semantics_status", "usage_basis_status"):
        require(gate.get(key) == "PASS", f"STOP: unproved {key}")
    positive_integer(gate.get("teacher_negative_rows"), "teacher_negative_rows")
    positive_integer(gate.get("verified_observation_rows"), "verified_observation_rows")
    positive_integer(gate.get("known_negative_frame_count"), "known_negative_frame_count")
    require(admission.get("run_config_sha256") == sha256(config_path), "run config is not bound to admission")
    config = read_json(config_path)
    validate_config(config)
    require(admission.get("run_id") == config["run_id"], "run_id mismatch")
    require(admission.get("training_manifest", {}).get("sha256") == gate.get("training_manifest_sha256"),
            "data gate not bound to target training manifest")
    frozen_spec = admission.get("frozen_train_manifest")
    require(isinstance(frozen_spec, dict) and frozen_spec.get("sha256") == FROZEN_TRAIN_SHA256,
            "unapproved replacement of frozen 704 train manifest")
    frozen_path = train_bound_file(frozen_spec, "frozen 704 train manifest")
    frozen = [json.loads(line) for line in frozen_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(frozen) == 704 and all(r.get("split") == "train" for r in frozen), "frozen train split changed")
    old_by_id = {r["sample_id"]: r for r in frozen}
    require(len(old_by_id) == 704, "duplicate frozen training sample_id")
    groups = sorted({r["youtube_id"] for r in frozen})
    groups_hash = hashlib.sha256(json.dumps(groups, separators=(",", ":")).encode()).hexdigest()
    require(len(groups) == 602 and groups_hash == FROZEN_GROUPS_SHA256, "frozen training source groups changed")
    isolation = bound_json(admission.get("source_isolation_certificate"), "source isolation certificate")
    require(isolation.get("status") == "PASS" and isolation.get("frozen_train_manifest_sha256") == FROZEN_TRAIN_SHA256
            and isolation.get("train_source_groups_sha256") == FROZEN_GROUPS_SHA256,
            "missing exact frozen-source isolation certificate")
    require(isolation.get("train_dev_source_group_intersection") == []
            and isolation.get("train_confirm_source_group_intersection") == [], "source split contamination")
    require(isolation.get("confirm_labels_read_by_this_admission") is False, "confirmation labels must remain unread")
    engineering = bound_json(admission.get("engineering_gate"), "real 8B engineering gate")
    require(engineering.get("status") == "PASS_REAL_8B_SYNTHETIC_ENGINEERING_ONLY"
            and engineering.get("revision") == PINNED_REVISION
            and engineering.get("parameter_inventory", {}).get("total") == 8_782_983_665,
            "real 8B engineering gate has not passed")
    manifest_path = train_bound_file(admission.get("training_manifest"), "dense training manifest")
    manifest_rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(bool(manifest_rows), "empty dense training manifest")
    seen, sources, indices, evidence = set(), {}, {}, {}
    known_cells = negative_cells = 0
    cell_count = math.ceil(config["window_seconds"] / config["grid_seconds"])
    for row in manifest_rows:
        row_id = row.get("window_id")
        require(isinstance(row_id, str) and row_id and row_id not in seen, "missing/duplicate window_id")
        seen.add(row_id)
        require(row.get("split") == "train" and row.get("label_status") == "WEAK_TEACHER", "nontrain/nonweak window")
        old = old_by_id.get(row.get("sample_id"))
        require(old is not None and row.get("source_group") == old["youtube_id"]
                and row.get("source_path") == old["source_path"], "window outside frozen train identity")
        require(row.get("pts_audit_status") == "PASS", "missing source PTS audit")
        source_hash = row.get("source_sha256", "")
        require(bool(re.fullmatch(r"[0-9a-f]{64}", source_hash)), "missing source media hash")
        source_path = row["source_path"]
        require(source_path not in sources or sources[source_path] == source_hash, "inconsistent source hash")
        sources[source_path] = source_hash
        index_spec = row.get("pts_index")
        index_key = json.dumps(index_spec, sort_keys=True)
        if index_key not in indices:
            indices[index_key] = bound_json(index_spec, "source PTS index")
        index = indices[index_key]
        require(index.get("status") == "PASS" and index.get("source_sha256") == source_hash,
                "PTS index not bound to source media")
        finite_positive(index.get("source_avg_fps"), "verified source_avg_fps metadata")
        starts, ends = index.get("frame_pts"), index.get("frame_end_pts")
        require(isinstance(starts, list) and isinstance(ends, list) and len(starts) == len(ends) and len(starts) >= 2,
                "missing complete source PTS vectors")
        require(index.get("source_frame_ids") == list(range(len(starts))), "PTS index must enumerate complete source frame axis")
        require(all(type(t) in (float, int) and math.isfinite(t) for t in starts + ends), "nonfinite PTS index")
        require(all(a < b for a, b in zip(starts, starts[1:]))
                and all(a < b for a, b in zip(starts, ends))
                and all(abs(a - b) <= 1e-7 for a, b in zip(ends[:-1], starts[1:])), "source PTS index does not tile source frames")
        ids, pts, frame_ends = row.get("frame_ids"), row.get("exact_frame_pts"), row.get("exact_frame_end_pts")
        require(isinstance(ids, list) and 2 <= len(ids) <= config["max_frames"] and len(ids) % 2 == 0,
                "preselected frames must be explicit bounded even temporal pairs")
        require(all(type(i) is int and 0 <= i < len(starts) for i in ids) and ids == sorted(set(ids)), "invalid selected source frame IDs")
        require(pts == [starts[i] for i in ids] and frame_ends == [ends[i] for i in ids], "selected PTS not exact indexed source PTS")
        left, right = row.get("window_start_pts"), row.get("window_end_pts")
        require(type(left) in (int, float) and type(right) in (int, float) and math.isfinite(left) and math.isfinite(right)
                and left < right and right - left <= config["window_seconds"], "invalid source window bounds")
        require(starts[0] <= left and right <= ends[-1], "source window exceeds audited PTS span")
        require(all(left <= p < right for p in pts), "selected frame outside its source window")
        for role in ("observation_evidence", "negative_semantics_evidence", "usage_basis_evidence"):
            spec = row.get(role)
            key = json.dumps(spec, sort_keys=True)
            if key not in evidence:
                evidence[key] = check_evidence(spec, role)
            require(evidence[key].get("source_sha256") == source_hash, f"{role} not bound to source")
        obs = evidence[json.dumps(row["observation_evidence"], sort_keys=True)]
        negative = evidence[json.dumps(row["negative_semantics_evidence"], sort_keys=True)]
        usage = evidence[json.dumps(row["usage_basis_evidence"], sort_keys=True)]
        require(obs.get("complete_observation") is True and obs.get("observed_start_pts", math.inf) <= left
                and obs.get("observed_end_pts", -math.inf) >= right, "teacher did not fully observe this window")
        require(negative.get("semantics") == "GENERIC_HIGHLIGHT_UNSELECTED_AFTER_COMPLETE_OBSERVATION"
                and negative.get("query_conditioned") is False and negative.get("forced_top_k") is False,
                "query/limited-selection negative semantics cannot authorize generic BCE")
        require(usage.get("rematch_training_use_permitted") is True, "source usage basis does not permit rematch training")
        grids = row.get("grid")
        require(isinstance(grids, list) and len(grids) == cell_count, "grid count differs from frozen run config")
        for i, cell in enumerate(grids):
            a, b = left + i * config["grid_seconds"], left + (i + 1) * config["grid_seconds"]
            require(cell.get("start_pts") == a and cell.get("end_pts_exclusive") == b
                    and type(cell.get("known")) is bool, "grid source bounds/mask mismatch")
            expected_ids = [j for j, p in enumerate(starts) if a <= p < b and left <= p < right]
            require(cell.get("source_frame_ids") == expected_ids, "grid does not replay every source frame")
            target = cell.get("target")
            if cell["known"]:
                require(b <= right and bool(expected_ids) and type(target) in (float, int)
                        and math.isfinite(target) and 0 <= target <= 1, "known cell has padding/invalid target")
                positive_integer(cell.get("known_negative_frame_count"), "known_negative_frame_count", allow_zero=True)
                positive_integer(cell.get("known_positive_frame_count"), "known_positive_frame_count", allow_zero=True)
                npos, nneg = cell["known_positive_frame_count"], cell["known_negative_frame_count"]
                require(npos + nneg == len(expected_ids) and abs(target - npos / len(expected_ids)) <= 1e-12,
                        "BCE target is not the source-frame binary label fraction")
                known_cells += 1
                negative_cells += int(nneg > 0)
            else:
                require(target is None, "UNKNOWN target must be null, never silently negative")
    require(known_cells > 0 and negative_cells > 0, "manifest lacks observed weak binary/negative supervision")
    model_receipt = bound_json(config.get("model_receipt"), "model receipt")
    require(model_receipt.get("status") == "COMPLETE_HASH_VERIFIED" and model_receipt.get("revision") == PINNED_REVISION
            and model_receipt.get("model_path") == config.get("model_dir"), "model download is not completed/pinned")
    return {"admission": admission, "config": config, "rows": manifest_rows, "sources": sources,
            "source_pts_indices": indices, "admission_sha256": sha256(admission_path),
            "config_sha256": sha256(config_path), "manifest_sha256": sha256(manifest_path),
            "frozen_train_manifest_sha256": FROZEN_TRAIN_SHA256,
            "train_source_groups_sha256": groups_hash, "known_cells": known_cells,
            "negative_supported_cells": negative_cells, "dev_confirm_labels_read": False}
