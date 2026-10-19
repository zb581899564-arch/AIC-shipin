"""Run this release's necessary synthetic CPU checks, never actual model jobs."""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "improvement.content_choice_v1"

import argparse
import contextlib
import importlib.metadata
import io
from pathlib import Path
import platform
import sys
import time
import unittest

from .contracts import code_identity, reference, save_new, utc_now


TEST_GROUPS = (
    "test_runtime.PureRuntimeChecks",
    "test_observation.PureObservationTests",
    "test_selection", "test_critic", "test_evaluate", "test_adoption",
    "test_render", "test_verification", "test_driver", "test_reuse",
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    identity = code_identity()
    names = [__package__ + "." + name for name in TEST_GROUPS]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    log, started = io.StringIO(), time.monotonic()
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    elapsed = time.monotonic() - started
    log_path = args.output.with_suffix(".log")
    with log_path.open("x", encoding="utf-8") as stream:
        stream.write(log.getvalue())
    success = result.wasSuccessful() and not result.skipped and "torch" not in sys.modules
    report = dict(schema="AIC_CONTENT_CHOICE_SYNTHETIC_CPU_RESULTS_V1",
        status="PASS_SYNTHETIC_CPU" if success else "FAIL_SYNTHETIC_CPU", utc=utc_now(),
        code_identity=identity, python=platform.python_version(), numpy=importlib.metadata.version("numpy"),
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        skipped=len(result.skipped), elapsed_seconds=elapsed,
        test_groups=list(TEST_GROUPS), log_ref=reference(log_path),
        torch_imported="torch" in sys.modules, qwen_calls=0, model_downloads=0, media_decodes=0,
        gpu_updates=0, official_sources_processed=0, new_submission_zips=0,
        synthetic_renderer_uses_real_inherited_strict_subprocess=True,
        boundaries="Synthetic NumPy/receipt fixtures only; adoption/driver heavy boundaries explicitly mocked",
        real_torch_tensor_checks="NOT_RUN_HERE_SEPARATE_MANDATORY_TORCH_GATE",
        actual_private_assets="NOT_RUN", actual_candidate_training="NOT_RUN",
        actual_qwen_inference="NOT_RUN", mechanism_quality="NOT_RUN", official_score="NOT_MEASURED")
    saved = save_new(args.output, report)
    print(__import__("json").dumps(dict(status=report["status"], tests_run=result.testsRun,
                                      elapsed_seconds=elapsed, output=saved), ensure_ascii=False))
    if not success:
        print(log.getvalue(), file=sys.stderr)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
