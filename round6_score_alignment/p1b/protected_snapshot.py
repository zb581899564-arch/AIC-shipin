#!/usr/bin/env python3
"""P1b-fix: snapshot the hashes of everything this round must not change.

Run once before the fix and once after: any difference in a protected group is a
violation that must be reported, not silently accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports/round6_score_alignment/phase1b_fix"

PROTECTED_GLOBS = {
    "p1b_media": "round6_score_alignment/p1b/media/*.mp4",
    "phase1b_reports": "reports/round6_score_alignment/phase1b/*",
    "phase1b_ui_render": "reports/round6_score_alignment/phase1b/ui_render/*",
    "p1a_code": "round6_score_alignment/p1a/aic6/*.py",
    "p1a_tests": "round6_score_alignment/p1a/tests/*.py",
    "p1a_vendor": "round6_score_alignment/p1a/aic6/vendor/existing_internal_evaluator/*",
}
PROTECTED_FILES = [
    "round6_score_alignment/p1b/pilot_manifest.json",
    "round6_score_alignment/p1b/fingerprints.json",
    "round6_score_alignment/p1b/inventory_raw.json",
    "round6_score_alignment/p1b/remote_probe_raw.json",
    "round6_score_alignment/p1b/README_annotation.md",
    "submissions/round5_s2_temporal_20260917/predictions.jsonl",
    "submissions/round5_s2_temporal_20260917/aic-round5-s2-temporal-20260917.zip",
    "reports/temporal_round5/evidence/temporal_raw_v1.jsonl",
    "submissions/qwen3vl_lora_reader_20260912/predictions.jsonl",
    "reports/round6_score_alignment/phase0/evidence/supervisor_test_metadata.json",
    "AGENTS.md",
    "ROADMAP.md",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def snapshot() -> dict:
    out: dict[str, dict[str, str]] = {}
    for group, pattern in PROTECTED_GLOBS.items():
        out[group] = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p)
                      for p in sorted(ROOT.glob(pattern)) if p.is_file()}
    out["pinned_files"] = {rel: sha256(ROOT / rel) for rel in PROTECTED_FILES
                           if (ROOT / rel).is_file()}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=["before", "after"])
    args = parser.parse_args()
    payload = {"run_id": "round6_p1b_fix_20260917T1630Z", "phase": args.phase,
               "groups": snapshot()}
    path = OUT_DIR / f"protected_hashes_{args.phase}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {k: len(v) for k, v in payload["groups"].items()}
    print(json.dumps({"wrote": str(path.relative_to(ROOT)), "counts": counts,
                      "total": sum(counts.values())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
