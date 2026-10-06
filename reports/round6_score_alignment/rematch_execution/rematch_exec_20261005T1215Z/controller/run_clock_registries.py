"""Explicit CPU-only complete-clock re-audit and bound non-test registry."""
from pathlib import Path
import subprocess
import sys

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CODE = RUN/'baseline_pts_v4'

if __name__ == '__main__':
    subprocess.run([sys.executable, '-B', str(CODE/'scan_native_clock.py'),
        '--manifest', str(RUN/'baseline_a/m0_finalize_01/clean_manifest_426.json'),
        '--v3-receipt', str(RUN/'baseline_pts_v3/scan_01/pts_origin_receipt.json'),
        '--endpoint-addendum', str(CODE/'endpoint_addendum_01/addendum_receipt.json'),
        '--expected-addendum-sha256', 'cb5189e59b7b8deed72086e42bd206ec369367c427eff35b72f70373b8c3c83b',
        '--output-root', str(CODE/'scan_01')], check=True)
    subprocess.run([sys.executable, '-B', str(CODE/'build_nontest_registry.py'),
        '--manifest', str(RUN/'baseline_a/inputs/non_test_frozen8.json'),
        '--collector-receipt', str(RUN/'controller/nontest_clock_numeric_01/nontest_numeric_receipt.json'),
        '--output-root', str(CODE/'nontest_registry_01')], check=True)
    print('PASS_CLOCK_REGISTRIES_METADATA_ONLY_NO_INFERENCE_ADMISSION', flush=True)
