"""Apply the pre-registered P2-T acceptance gate to frozen diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decide(data: dict) -> dict:
    base = data["per_arm"]["BASE"]
    fresh = data["per_arm"]["P2T_FRESH"]
    paired = data["paired"]["P2T_FRESH_minus_BASE"]
    checks = {
        "group_macro_f1_gain_at_least_0_03": paired["mean"] >= 0.03,
        "paired_ci95_lower_bound_above_zero": paired["ci95"][0] > 0,
        "valid_rate_not_lower_than_base": fresh["valid_rate"] >= base["valid_rate"],
    }
    return {
        "status": "ACCEPT_P2T_FRESH" if all(checks.values()) else "STOP_KEEP_BASE",
        "metric_status": "WEAK_TEACHER_DIAGNOSTIC_NOT_OFFICIAL_SCORE",
        "checks": checks,
        "base_group_macro_f1": base["group_macro_f1"],
        "fresh_group_macro_f1": fresh["group_macro_f1"],
        "fresh_minus_base": paired,
        "base_valid_rate": base["valid_rate"],
        "fresh_valid_rate": fresh["valid_rate"],
        "interpretation": "This selects the temporal component for further non-test engineering only; it is not an official-score claim or test-set authorization.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostics", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.diagnostics.read_text(encoding="utf-8"))
    out = decide(data)
    out["diagnostics_sha256"] = sha256(args.diagnostics)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out["status"] == "ACCEPT_P2T_FRESH" else 3


if __name__ == "__main__":
    raise SystemExit(main())
