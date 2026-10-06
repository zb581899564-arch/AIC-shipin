#!/usr/bin/env python3
"""Compare the two independent draft validators on the Node-generated cases."""
from __future__ import annotations

import json
from pathlib import Path

from validate_exports import draft_problems

ROOT = Path(__file__).resolve().parents[2]
P1B = Path(__file__).resolve().parent
OUT = ROOT / "reports/round6_score_alignment/phase1b_fix2"


def main() -> int:
    manifest = json.loads((P1B / "pilot_manifest.json").read_text(encoding="utf-8"))
    cases = json.loads((OUT / "draft_common_cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        problems = draft_problems(case["draft"], manifest)
        valid = not problems
        rows.append({"name": case["name"], "js_valid": case["js_valid"],
                     "python_valid": valid, "match": case["js_valid"] == valid,
                     "python_problems": problems})
    result = {"run_id": "round6_p1b_fix2_20260917T0951Z", "results": rows,
              "matched": sum(row["match"] for row in rows), "total": len(rows)}
    (OUT / "draft_common_compare.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"matched": result["matched"], "total": result["total"]}))
    return 0 if result["matched"] == result["total"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
