#!/usr/bin/env python3
"""One-off: make the P1a consumption check run BOTH universes.

P1a's scorer treats a reference that does not cover the scored universe as
NOT_COMPUTABLE (its coverage check runs before the sparse branch), and treats a
sparse reference as SPARSE_DIAGNOSTIC with no score.  Both behaviours are the ones
the fix must demonstrate, so the check now reports them side by side:

  A) universe == annotated sample only      -> SPARSE_DIAGNOSTIC, score null
  B) universe includes an unannotated video -> NOT_COMPUTABLE, score null
"""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parent / "run_fix_validation.py"
text = p.read_text(encoding="utf-8")

old_call = '''    consumption = p1a_consumption(E2E / "step2_restored_reference.json", e2e_manifest)'''
new_call = '''    consumption = {
        "sparse_reference_with_matching_universe": p1a_consumption(
            E2E / "step2_restored_reference.json", e2e_manifest,
            universe=["S01"], label="A: universe == annotated sample"),
        "sparse_reference_with_unannotated_video": p1a_consumption(
            E2E / "step2_restored_reference.json", e2e_manifest,
            universe=["S01", "S02"], label="B: universe includes the unannotated S02"),
        "expected": ("A -> SPARSE_DIAGNOSTIC with score null (sparse semantics preserved); "
                     "B -> NOT_COMPUTABLE with score null (unannotated video never treated as "
                     "empty ground truth)"),
    }'''
assert old_call in text
text = text.replace(old_call, new_call)

old_def = '''def p1a_consumption(export_path: Path, manifest: dict) -> dict:'''
new_def = '''def p1a_consumption(export_path: Path, manifest: dict, universe=None, label="") -> dict:'''
assert old_def in text
text = text.replace(old_def, new_def)

old_index = '''        index = {s["sample_id"]: {"video_id": s["sample_id"],'''
new_index = '''        keep = set(universe) if universe else {s["sample_id"] for s in manifest["samples"]}
        index = {s["sample_id"]: {"video_id": s["sample_id"],'''
assert old_index in text
text = text.replace(old_index, new_index)

old_loop = '''                 for s in manifest["samples"]}'''
new_loop = '''                 for s in manifest["samples"] if s["sample_id"] in keep}'''
assert old_loop in text
text = text.replace(old_loop, new_loop, 1)

old_return = '''    return {"status": result["status"], "score": result["score"],
            "sparse_block": (result.get("sparse") or {}).get("evidence_status"),
            "expected": "SPARSE_DIAGNOSTIC with score null (never a full-video joint score)"}'''
new_return = '''    return {"label": label, "universe": sorted(keep), "status": result["status"],
            "score": result["score"],
            "sparse_evidence": (result.get("sparse") or {}).get("evidence_status"),
            "reasons": result.get("reasons")}'''
assert old_return in text
text = text.replace(old_return, new_return)

fail_old = '''    bad_artifacts = [a["artifact"] for a in artifact_checks if not a.get("pass")]
    if bad_artifacts:
        failure_causes.append({"where": "e2e artifacts", "ids": bad_artifacts})'''
fail_new = '''    bad_artifacts = [a["artifact"] for a in artifact_checks if not a.get("pass")]
    if bad_artifacts:
        failure_causes.append({"where": "e2e artifacts", "ids": bad_artifacts})
    expect_status = {"sparse_reference_with_matching_universe": ("SPARSE_DIAGNOSTIC", None),
                     "sparse_reference_with_unannotated_video": ("NOT_COMPUTABLE", None)}
    for key, (status, score) in expect_status.items():
        got = consumption.get(key) or {}
        if got.get("status") != status or got.get("score") != score:
            failure_causes.append({"where": f"p1a consumption {key}",
                                   "expected": [status, score],
                                   "got": [got.get("status"), got.get("score")]})'''
assert fail_old in text
text = text.replace(fail_old, fail_new)

p.write_text(text, encoding="utf-8")
print("p1a consumption now checks both universes")
