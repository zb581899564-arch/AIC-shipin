"""Shared immutable stage, source, release and admission contracts."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from improvement.native_preference_v1.contracts import (
    StageBudget, checked, digest, reference, require, same_reference, save_new,
    strict_load, successful_source_selections, utc_now)

BASE_COMMIT = "f343a92da467b0e9f4c2677bd2ab75ff88a09df7"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CANDIDATES = ("observation", "contrast", "critic")
FROZEN_PIPELINE = 8_782_557_449  # BASE + original TIME + inherited semantic head
CRITIC_PARAMETERS = 131


def stable_key(*parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sample_seed(source_sha256, uid, slot):
    require(slot in (1, 2), "Only two registered stochastic candidate slots")
    require(re.fullmatch(r"[0-9a-f]{64}", source_sha256) is not None,
            "Actual source SHA256 required for sampling identity")
    return int(stable_key(20261019, source_sha256, uid, slot)[:16], 16) & ((1 << 63) - 1)


def pipeline_parameters(candidate):
    require(candidate in CANDIDATES, "Unknown candidate")
    return FROZEN_PIPELINE + (CRITIC_PARAMETERS if candidate == "critic" else 0)


def validate_config(config):
    template = strict_load(HERE / "config.example.json")
    require(set(config) == set(template), "Missing or unregistered configuration field")
    require(re.fullmatch(r"[A-Za-z0-9_-]+", config.get("run_id", "")) is not None,
            "Explicit safe run_id required")
    require(Path(config["run_root"]).is_absolute(), "Absolute independent run_root required")
    for key, expected in template.items():
        if key in ("run_id", "run_root"):
            continue
        if key.startswith("max_") and key not in ("max_new_tokens", "max_segments"):
            require(type(config[key]) is int and 0 < config[key] <= expected,
                    "Finite budget may only be tightened: " + key)
        else:
            require(type(config[key]) is type(expected) and config[key] == expected,
                    "Frozen scientific setting changed: " + key)
    return config


def code_identity():
    manifest = strict_load(HERE / "code_manifest.json")
    require(manifest.get("schema") == "AIC_CONTENT_CHOICE_CODE_V1"
            and manifest.get("base_commit") == BASE_COMMIT, "Wrong release identity")
    own = manifest["files"]
    actual = {p.name for p in HERE.glob("*.py")} | {"config.example.json"}
    require(set(own) == actual, "Closed experiment code/config inventory changed")
    for name, sha in own.items():
        require(Path(name).name == name and digest(HERE / name) == sha,
                "Experiment code bytes changed: " + name)
    for name, sha in manifest["dependencies"].items():
        path = (REPO / name).resolve(strict=True)
        require(path.is_relative_to(REPO) and digest(path) == sha,
                "Frozen dependency changed: " + name)
    return dict(base_commit=BASE_COMMIT,
                manifest_ref=reference(HERE / "code_manifest.json"))


def bind_artifact(document, binding):
    require(document.get("code_identity") == binding["code_identity"],
            "Artifact uses a different executable release")
    for key in ("config_ref", "asset_manifest_ref"):
        require(key in document and same_reference(document[key], binding[key]),
                "Artifact/config/assets identity mismatch: " + key)
        checked(document[key])


def admission_gate(value, action, candidate, expected, workspace):
    require(expected and isinstance(expected, dict), "Admission must bind explicit artifacts")
    require(value.get("schema") == "AIC_CONTENT_CHOICE_ADMISSION_V1"
            and value.get("action") == action and value.get("candidate") == candidate
            and candidate in CANDIDATES and value.get("approved") is True,
            "Independent candidate-specific execution review required")
    require(isinstance(value.get("reviewed_by"), str) and value["reviewed_by"].strip()
            and isinstance(value.get("review_notes"), str) and value["review_notes"].strip(),
            "Explicit reviewer and substantive notes required")
    stamp = datetime.fromisoformat(value["reviewed_at"].replace("Z", "+00:00"))
    require(stamp.tzinfo is not None, "Timezone-aware review time required")
    for key, ref in expected.items():
        require(key in value and same_reference(value[key], ref), "Stale admission: " + key)
        checked(value[key], workspace)
    return value


def claim(config, manifest, name, binding):
    require(re.fullmatch(r"[a-z_]+", name) is not None, "Safe explicit stage name required")
    root = Path(config["run_root"]).resolve()
    workspace = Path(manifest["workspace_root"]).resolve(strict=True)
    require(root.is_relative_to(workspace) and root != workspace
            and root.name == config["run_id"], "Independent run root/name inside workspace required")
    # No writing into a model, historical asset, input lock or protected package directory.
    from improvement.native_preference_v1.assets import iter_refs
    for ref in iter_refs(manifest):
        path = Path(ref["path"]).resolve()
        require(not path.is_relative_to(root), "Output root already contains an adopted asset")
    model = Path(manifest["model_spec"]["model_dir"]).resolve()
    require(not root.is_relative_to(model), "Output cannot enter original model directory")
    root.mkdir(parents=True, exist_ok=True)
    directory = root / name
    directory.mkdir(exist_ok=False)
    save_new(directory / "claim.json", dict(stage=name, utc=utc_now(), **binding,
        automatic_retry=False, failure_to_empty=False, official_submission=False))
    return directory


def ordered_cases(store):
    """Stream exactly one complete source at a time, in native window order."""
    from fractions import Fraction
    return [uid for sid in sorted(store.source_ids,
                key=lambda s: stable_key(20261019, store.sources[s]["source_sha256"]))
            for uid in sorted(store.by_source[sid], key=lambda u:
                Fraction(store.requests[u]["plan"]["window_start_exact"]))]


def source_plan(store):
    return dict(source_ids=list(store.source_ids), case_ids=ordered_cases(store),
        source_sha256={sid: store.sources[sid]["source_sha256"] for sid in store.source_ids},
        request_refs=store.request_refs,
        clock_refs={sid: store.sources[sid]["clock_ref"] for sid in store.source_ids})
