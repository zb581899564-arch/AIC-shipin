"""Round-6 P2 joint coverage: hashes and provenance pinning.

The P2 delivery path is a *separate* module from P1a: it reuses the P1a
conventions (timebase / segments / compose / scoring) from its own copy, and
adds the coverage gate that keeps new-frame old-box copying bounded and
auditable.

Everything this package reads from the historical project is pinned here and
verified before use.  Modified protection targets fail closed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Repository root: <root>/round6_score_alignment/p2_joint_coverage/aic6/provenance.py
ROOT = Path(__file__).resolve().parents[3]

SPEC_VERSION = "aic_round6_p2_internal_spec_v1"

# --- protected (read-only) historical inputs ---------------------------------
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
    # Weak-dev-pilot artifacts are *recorded* inputs (hashed in the manifest for
    # drift detection) but not frozen at any earlier stage, so they are observed
    # and pinned on the first P2 run rather than verified against older pins.
    "weak_dev_pilot_freeze": (ROOT / "reports/round6_score_alignment/weak_dev_pilot/freeze_record.json",
                              None),
    "weak_dev_pilot_dev_frames": (ROOT / "reports/round6_score_alignment/weak_dev_pilot/dev_frames.jsonl",
                                  "711fd3c8d0c960957bd519c13654e0f38f53296cda83cc2edb2f182982551c84"),
    "weak_dev_pilot_dev_temporal": (ROOT / "reports/round6_score_alignment/weak_dev_pilot/dev_temporal.jsonl",
                                    "242a3a0475f6c5b66cd2a25deef88f3b477f3f6ea5f4d22984c1a12830d3bd3c"),
    "weak_dev_pilot_temporal_s2": (ROOT / "reports/round6_score_alignment/weak_dev_pilot/temporal_S2.jsonl",
                                   None),
    "weak_dev_pilot_p1_predictions": (ROOT / "reports/round6_score_alignment/weak_dev_pilot/p1_predictions.jsonl",
                                      None),
}


def _resolve_freeze_hashes() -> None:
    """Pin the frozen dev frame manifest against its own freeze record.

    ``dev_frames.jsonl`` and ``dev_temporal.jsonl`` carry the SHA-256 recorded in
    ``freeze_record.json`` at freeze time.  The other weak-dev-pilot files were
    produced after that freeze, so they are hashed on first observation in the
    P2 protocol rather than pinned to an earlier value.
    """
    freeze = ROOT / "reports/round6_score_alignment/weak_dev_pilot/freeze_record.json"
    if freeze.is_file():
        record = json.loads(freeze.read_text(encoding="utf-8"))
        sha = record.get("sha256") or {}
        if sha.get("dev_frames.jsonl"):
            PROTECTED_INPUTS["weak_dev_pilot_dev_frames"] = (
                PROTECTED_INPUTS["weak_dev_pilot_dev_frames"][0], sha["dev_frames.jsonl"])
        if sha.get("dev_temporal.jsonl"):
            PROTECTED_INPUTS["weak_dev_pilot_dev_temporal"] = (
                PROTECTED_INPUTS["weak_dev_pilot_dev_temporal"][0], sha["dev_temporal.jsonl"])


_resolve_freeze_hashes()


# First-observation pins for post-freeze weak-dev-pilot outputs (recorded by the
# first P2 run and verified from then on).
FIRST_OBSERVATION_PINS = {
    "weak_dev_pilot_freeze": "4596a51705341237aa34a9c6d505a6aa4a75aa8668d472ea047ae7cbf38a8d3e",
    "weak_dev_pilot_temporal_s2": "ca51e6d49e2394dcef28dc1b651e9803646ae8921a97e6f669632cc082e73903",
    "weak_dev_pilot_p1_predictions": "cc2778747c0a7bdab88bea70fabe6dab181c75850bc5cd53936b386dbb4a61d3",
}
for _key, _pin in FIRST_OBSERVATION_PINS.items():
    _path, _ = PROTECTED_INPUTS[_key]
    PROTECTED_INPUTS[_key] = (_path, _pin)


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class ProvenanceError(RuntimeError):
    """Raised when a pinned or protected artifact no longer matches its recorded hash."""


def snapshot_protected(*, verify_expected: bool = True) -> dict:
    """Hash every protected input; used before and after each run."""
    out = {}
    for key, (path, expected) in PROTECTED_INPUTS.items():
        got = sha256_file(path) if Path(path).is_file() else None
        entry = {"path": str(Path(path).relative_to(ROOT)).replace("\\", "/")
                 if Path(path).is_relative_to(ROOT) else str(path),
                 "observed_sha256": got}
        if verify_expected:
            entry["expected_sha256"] = expected
            entry["matches"] = got == expected
        out[key] = entry
    return out


def assert_protected_unchanged(before: dict, after: dict) -> list:
    problems = []
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key, {}), after.get(key, {})
        if b.get("observed_sha256") != a.get("observed_sha256"):
            problems.append({"input": key, "before": b.get("observed_sha256"),
                             "after": a.get("observed_sha256")})
        if a.get("matches") is False:
            problems.append({"input": key, "error": "does not match recorded hash",
                             "observed": a.get("observed_sha256")})
    return problems


def verify_pinned_protected_inputs() -> list:
    """Check the pinned historical inputs (the five round-5/phase0 artifacts)."""
    pinned = ("round5_predictions", "round5_zip", "round5_temporal_raw",
              "spatial_base_lora_reader", "test_metadata_index")
    problems = []
    for key in pinned:
        path, expected = PROTECTED_INPUTS[key]
        got = sha256_file(path) if Path(path).is_file() else None
        if got != expected:
            problems.append({"input": key, "expected": expected, "observed": got})
    return problems


def input_manifest() -> dict:
    return {
        "spec_version": SPEC_VERSION,
        "protected_inputs": {
            key: {"path": str(Path(path).relative_to(ROOT)).replace("\\", "/")
                  if Path(path).is_relative_to(ROOT) else str(path), "sha256": expected}
            for key, (path, expected) in PROTECTED_INPUTS.items()
        },
    }


def write_json(path: Path | str, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
