"""Run this release's synthetic CPU checks; never load a model or admit a GPU job."""
if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "improvement.native_preference_v1"

import argparse
import importlib.util
import io
from pathlib import Path
import platform
import sys
import time
import unittest

from .contracts import save_new, utc_now
from .run import code_identity


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    started, stamp = time.monotonic(), utc_now()
    identity = code_identity()
    compiled = []
    for path in sorted(Path(__file__).resolve().parent.glob("*.py")):
        compile(path.read_bytes(), str(path), "exec")
        compiled.append(path.name)
    modules = ["test_preference", "test_contracts", "test_assets", "test_pipeline",
               "test_runtime_integration", "test_reference_adoption", "torch_checks.PureChecks"]
    suite = unittest.defaultTestLoader.loadTestsFromNames(
        ["improvement.native_preference_v1." + module for module in modules])
    transcript = io.StringIO()
    result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(suite)
    print(transcript.getvalue(), end="")
    report = dict(schema="AIC_NATIVE_PREFERENCE_LOCAL_CPU_REPORT_V1",
        status="PASS_CPU_ONLY" if result.wasSuccessful() and not result.skipped else "FAIL",
        started_utc=stamp, completed_utc=utc_now(), elapsed_seconds=time.monotonic()-started,
        python=sys.version, platform=platform.platform(), command="check_cpu.py --output EXPLICIT_NEW_PATH",
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        skipped=len(result.skipped), compiled_python_files=compiled, code_identity=identity,
        log=transcript.getvalue(), torch_installed=importlib.util.find_spec("torch") is not None,
        real_linux_assets_used=False, actual_qwen_calls=0, actual_gpu_updates=0,
        simulation="Pilot integration checks mock only model/input boundaries; they are not Qwen/GPU results",
        not_run=["Actual Torch CPU gate (separate torch_checks.py command)",
                 "Real Linux asset preflight and candidate preparation", "Qwen forward/backward",
                 "Actual adapter update/save/reload", "Real free generation or proxy measurement",
                 "Official production inference", "Original renderer and its 11 strict checks",
                 "Official submission or score"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_new(args.output, report)
    return 0 if report["status"] == "PASS_CPU_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
