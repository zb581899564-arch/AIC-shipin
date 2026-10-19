"""CPU-only stage, budget and promotion contracts for this single pilot."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time


SCHEMA = "AIC_NATIVE_PREFERENCE_V1"
ADMISSION_SCHEMA = "AIC_NATIVE_PREFERENCE_ADMISSION_V1"
BASE_COMMIT = "42c0a72cf49b5d51784d1ee162630f8b74ccd294"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_load(path):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Nonfinite JSON: " + value)

    def finite_float(value):
        result = float(value)
        require(math.isfinite(result), "Nonfinite JSON number: " + value)
        return result

    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=object_pairs, parse_constant=nonfinite,
                      parse_float=finite_float)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            result.update(block)
    return result.hexdigest()


def reference(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file(), "Reference must be a file")
    return dict(path=str(path), sha256=digest(path), bytes=path.stat().st_size)


def checked(reference_value, root=None):
    require(isinstance(reference_value, dict), "Explicit path/SHA reference required")
    path = Path(reference_value["path"]).resolve(strict=True)
    if root is not None:
        require(path.is_relative_to(Path(root).resolve(strict=True)), "Reference escaped work root")
    require(path.is_file() and digest(path) == reference_value["sha256"], "Reference bytes changed: " + str(path))
    if "bytes" in reference_value:
        require(type(reference_value["bytes"]) is int and path.stat().st_size == reference_value["bytes"],
                "Reference size changed: " + str(path))
    return path


def save_new(path, value):
    path = Path(path)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return reference(path)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_config(config):
    require(config.get("schema") == SCHEMA, "Wrong mechanism configuration schema")
    require(re.fullmatch(r"[A-Za-z0-9_-]+", config.get("run_id", "")), "Explicit safe run_id required")
    root = Path(config["run_root"])
    require(root.is_absolute(), "run_root must be absolute")
    fixed = dict(train_source_count=8, train_pairs_per_source=4, check_pairs_per_source=2,
                 max_seed_candidates_per_source=128, max_check_sources=8, max_check_windows=64,
                 updates=16, grad_accum=2, max_new_tokens=512, max_segments=6,
                 counterfactual="ONE_NATIVE_ORDINAL_REFLECTION",
                 pair_budget="EXACT_EQUAL_NATIVE_FRAMES_AND_SUFFIX_TOKENS",
                 generation="GREEDY_ORIGINAL_SIX_SEGMENT_GRAMMAR_ALLOW_EMPTY",
                 production_selection="REPLACE_TIME_THEN_INTERSECT_FROZEN_SPATIAL_DOMAIN",
                 checkpoint="FINAL_ONLY", historical_exposure=True,
                 automatic_production=False, automatic_submission=False)
    for name, expected in fixed.items():
        require(type(config.get(name)) is type(expected) and config[name] == expected,
                "Frozen mechanism/control setting changed: " + name)
    require(type(config.get("seed")) is int and config["seed"] == 20261019, "Fixed pilot seed required")
    for name, expected in (("learning_rate", 1e-5), ("beta", .1)):
        require(type(config.get(name)) in (int, float) and math.isfinite(config[name]) and config[name] == expected,
                "Frozen optimizer setting changed: " + name)
    limits = dict(max_prepare_seconds=1800, max_pilot_seconds=3600, max_production_seconds=7200,
                  max_output_bytes=1073741824, max_top_level_forwards=66000,
                  max_production_top_level_forwards=307200,
                  max_production_sources=426, max_production_windows=600)
    for name, maximum in limits.items():
        require(type(config.get(name)) is int and 0 < config[name] <= maximum,
                "Invalid or expanded finite budget: " + name)
    require(config["updates"] * config["grad_accum"] ==
            config["train_source_count"] * config["train_pairs_per_source"],
            "Exactly one registered pass over the fixed pair list required")
    return config


def same_reference(first, second):
    return (str(Path(first["path"]).resolve()), first["sha256"]) == (
        str(Path(second["path"]).resolve()), second["sha256"])


def validate_admission(admission, action, expected_refs, *, root=None):
    require(isinstance(expected_refs, dict) and expected_refs,
            "Admission must bind a nonempty explicit artifact set")
    require(admission.get("schema") == ADMISSION_SCHEMA and admission.get("action") == action
            and admission.get("approved") is True, "Separate explicit " + action + " admission required")
    require(isinstance(admission.get("reviewed_by"), str) and admission["reviewed_by"].strip()
            and isinstance(admission.get("review_notes"), str) and admission["review_notes"].strip(),
            "A completed execution-agent review must be recorded")
    stamp = datetime.fromisoformat(admission["reviewed_at"].replace("Z", "+00:00"))
    require(stamp.tzinfo is not None, "Timezone-aware review time required")
    for name, expected in expected_refs.items():
        require(name in admission and same_reference(admission[name], expected),
                "Admission is stale or binds a different " + name)
        checked(admission[name], root)
    return admission


class StageBudget:
    """The shared GPU wrapper is the hard process deadline; this checks in-process work."""

    def __init__(self, directory, seconds, output_bytes, forward_limit):
        self.directory = Path(directory)
        self.started = time.monotonic()
        self.seconds, self.output_bytes, self.forward_limit = seconds, output_bytes, forward_limit
        self.forward_count = 0
        self.last_size_check = self.started
        self.last_output_bytes = 0
        self.peak_observed_output_bytes = 0

    def check(self, *, forward=False, force_disk=False):
        self.forward_count += int(forward)
        elapsed = time.monotonic() - self.started
        require(elapsed <= self.seconds, "Finite stage wall-clock budget exhausted")
        require(self.forward_count <= self.forward_limit, "Registered top-level forward budget exhausted")
        if force_disk or time.monotonic() - self.last_size_check > 10:
            size = sum(path.stat().st_size for path in self.directory.rglob("*") if path.is_file())
            self.last_output_bytes = size
            self.peak_observed_output_bytes = max(self.peak_observed_output_bytes, size)
            require(size <= self.output_bytes, "Finite new output disk budget exhausted")
            self.last_size_check = time.monotonic()

    def snapshot(self):
        return dict(elapsed_seconds=time.monotonic() - self.started,
                    top_level_forward_calls=self.forward_count,
                    max_seconds=self.seconds, max_output_bytes=self.output_bytes,
                    last_observed_output_bytes=self.last_output_bytes,
                    peak_observed_output_bytes=self.peak_observed_output_bytes,
                    max_top_level_forwards=self.forward_limit)


def claim_stage(run_root, stage, binding):
    require(stage in {"prepare", "pilot", "review", "production", "package"}, "Unknown claim stage")
    root = Path(run_root)
    root.mkdir(parents=True, exist_ok=True)
    directory = root / stage
    directory.mkdir(exist_ok=False)
    save_new(directory / "claim.json", dict(stage=stage, utc=utc_now(), **binding,
                                            automatic_retry=False, failed_output_to_empty=False))
    return directory


def successful_source_selections(records, expected_sources):
    require(set(records) == set(expected_sources), "Missing/extra sources cannot become empty predictions")
    for sid, row in records.items():
        require(row.get("status") == "ACCEPTED", "Failed source cannot be packaged: " + sid)
        values = row.get("selected_ordinals")
        require(isinstance(values, list) and all(type(i) is int and i >= 0 for i in values)
                and values == sorted(set(values)), "One sorted unique native frame set per source required")
    return records
