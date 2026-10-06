"""Verify the historical v2 subset byte-for-byte without modifying it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from aic6.subset import regenerate_subset_bytes

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "reports/round6_score_alignment/p2_joint_coverage"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", type=Path,
                        default=EVIDENCE / "p2_infer_requests_v2_source_grid.jsonl")
    parser.add_argument("--subset", type=Path,
                        default=EVIDENCE / "p2_infer_requests_v2_subset.jsonl")
    args = parser.parse_args()
    regenerated = regenerate_subset_bytes(args.full.read_bytes(),
                                          seed=20260918, n_gaps=6000)
    expected = args.subset.read_bytes()
    result = {
        "byte_exact": regenerated == expected,
        "regenerated_sha256": hashlib.sha256(regenerated).hexdigest(),
        "historical_sha256": hashlib.sha256(expected).hexdigest(),
        "seed": 20260918,
        "sampled_gaps": 6000,
        "selection_rule": "Python random.Random(seed).sample over ordered NEEDS_INFERENCE rows; retain all CONTROL_SAME_FRAME rows; preserve original row order and bytes",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["byte_exact"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
