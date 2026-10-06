"""Apply the frozen R7 development or confirmation gate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from r7_core import decide_gate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostics", type=Path, required=True)
    ap.add_argument("--stage", choices=("dev", "confirm"), required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise RuntimeError("refusing to overwrite gate result")
    data = json.loads(args.diagnostics.read_text(encoding="utf-8"))
    if data.get("stage") != args.stage:
        raise ValueError("diagnostic stage mismatch")
    result = decide_gate(data, args.stage)
    result["diagnostics_sha256"] = hashlib.sha256(
        args.diagnostics.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"].endswith("_PASS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
