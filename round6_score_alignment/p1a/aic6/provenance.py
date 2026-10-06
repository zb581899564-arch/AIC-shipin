"""Round-6 P1a: hashes and provenance pinning.

Everything this package reads from the historical project is pinned here and
verified before use.  Modified protection targets fail closed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Repository root: <root>/round6_score_alignment/p1a/aic6/provenance.py
ROOT = Path(__file__).resolve().parents[3]

SPEC_VERSION = "aic_round6_p1a_internal_spec_v1"

# --- pinned copies of the existing internal evaluator (phase0 evidence) -------
# Source of truth for the *copies*; the vendored files under
# aic6/vendor/existing_internal_evaluator/ must hash identically.
PINNED_EVALUATOR_COPIES = {
    "schema.py": "0236f98731919e2675a6eb827453f3c20bb63d38f459fd6b1ddf0f813200f5a9",
    "internal_metric.py": "41ec9ecf274c5a2e140bb4d84a3803d9a3bfa3d41e65323f466a296896d92317",
    "__init__.py": "3b8123792150de4656a7f5ff60725979286757ff20a58018edb6986483b91140",
    "README.md": "4878fc1960e10aad56251996df5fd792a1d4ad9c8d1e3b11df8c2a6830cd5c80",
    "validate_predictions.py": "f34003df8638aa3a6b22a466c22bc2415b4387b6e1fd89a774e33ef5cdc1d980",
}

PHASE0_EVALUATOR_DIR = ROOT / "reports/round6_score_alignment/phase0/evidence/existing_internal_evaluator"
VENDOR_DIR = Path(__file__).resolve().parent / "vendor/existing_internal_evaluator"

# --- protected (read-only) historical inputs used by the replay --------------
PROTECTED_INPUTS = {
    "round5_predictions": (ROOT / "submissions/round5_s2_temporal_20260917/predictions.jsonl",
                           "f8f026a69c8f9fa676dd31a6ffcd375569842c59f4cb6fdcd8d4ced5d86cf3ef"),
    "round5_zip": (ROOT / "submissions/round5_s2_temporal_20260917/aic-round5-s2-temporal-20260917.zip",
                   "e5df99b8c3d32ec6d495ef1aada2b869478f307884ebeedca3df76def36c3584"),
    "round5_temporal_raw": (ROOT / "reports/temporal_round5/evidence/temporal_raw_v1.jsonl",
                            "3bc0fc59af87fc8542793e4419889b4cdf86a63c56e9c02c7ea19fdb1109cf72"),
    "spatial_base_lora_reader": (ROOT / "submissions/qwen3vl_lora_reader_20260912/predictions.jsonl",
                                 "a81a711878ffcd68db84dba4b530c4c051cd10cd82b1b4929f35bd06853ef471"),
    "test_metadata_index": (ROOT / "reports/round6_score_alignment/phase0/evidence/supervisor_test_metadata.json",
                            "7f38d3f7f29b7fc5d91a9762ecfea00e6fc84b583bf11b439ba4a853bf1ec428"),
}


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class ProvenanceError(RuntimeError):
    """Raised when a pinned or protected artifact no longer matches its recorded hash."""


def verify_evaluator_sources() -> dict:
    """Verify the vendored copies against the pinned hashes (fail closed)."""
    out = {"vendored": {}, "phase0": {}, "mismatches": []}
    for name, expected in PINNED_EVALUATOR_COPIES.items():
        for label, base in (("vendored", VENDOR_DIR), ("phase0", PHASE0_EVALUATOR_DIR)):
            path = base / name
            if not path.is_file():
                out["mismatches"].append({"where": label, "file": name, "error": "missing"})
                continue
            got = sha256_file(path)
            out[label][name] = got
            if got != expected:
                out["mismatches"].append({"where": label, "file": name,
                                          "expected": expected, "got": got})
    if out["mismatches"]:
        raise ProvenanceError(f"evaluator source hash mismatch: {out['mismatches'][:3]}")
    out["ok"] = True
    return out


def snapshot_protected() -> dict:
    """Hash every protected input; used before and after the run."""
    out = {}
    for key, (path, expected) in PROTECTED_INPUTS.items():
        got = sha256_file(path) if Path(path).is_file() else None
        out[key] = {"path": str(Path(path).relative_to(ROOT)).replace("\\", "/"),
                    "expected_sha256": expected, "observed_sha256": got,
                    "matches": got == expected}
    return out


def assert_protected_unchanged(before: dict, after: dict) -> list:
    problems = []
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key, {}), after.get(key, {})
        if b.get("observed_sha256") != a.get("observed_sha256"):
            problems.append({"input": key, "before": b.get("observed_sha256"),
                             "after": a.get("observed_sha256")})
        if not a.get("matches"):
            problems.append({"input": key, "error": "does not match recorded hash",
                             "observed": a.get("observed_sha256")})
    return problems


def input_manifest() -> dict:
    return {
        "spec_version": SPEC_VERSION,
        "evaluator_sources": {name: expected for name, expected in PINNED_EVALUATOR_COPIES.items()},
        "protected_inputs": {
            key: {"path": str(Path(path).relative_to(ROOT)).replace("\\", "/"), "sha256": expected}
            for key, (path, expected) in PROTECTED_INPUTS.items()
        },
    }


def write_json(path: Path | str, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
