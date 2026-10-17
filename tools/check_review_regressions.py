"""Run the October 17 correctness regressions with only synthetic CPU inputs.

Each check runs in its own process so historical modules with generic names do
not leak through sys.modules. No launcher, model, media, or result ZIP is opened.
"""
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "improvement/midnight_five_package_v1/check_pure.py",
    "improvement/midnight_five_package_v1/check_production_evidence.py",
    "improvement/midnight_production_unique_v3/check_pure.py",
)


def main():
    for relative in CHECKS:
        print(f"Checking {relative}", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / relative)],
                cwd=ROOT,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            print(f"FAIL: check exceeded 60 seconds: {relative}", file=sys.stderr)
            return 1
        if result.returncode:
            print(f"FAIL: {relative} exited {result.returncode}", file=sys.stderr)
            return 1
    print(f"PASS: {len(CHECKS)} synthetic CPU check programs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
