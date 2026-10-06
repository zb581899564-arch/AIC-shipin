"""Actual frozen A admission refusal before framework/GPU entry."""
import hashlib
import importlib.abc
import json
from pathlib import Path
import runpy
import sys

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL = RUN/'controller'
attempted = []

class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch','numpy','decord','peft','transformers'}:
            attempted.append(fullname)
            raise RuntimeError('runtime import before identity rejection: '+fullname)

if __name__ == '__main__':
    admission = CTRL/'a_rematch_temporal_01.admission.json'
    if admission.exists():
        raise RuntimeError('refusing to overwrite an existing admission')
    sys.meta_path.insert(0, NoRuntime())
    error = None
    try:
        runpy.run_path(str(CTRL/'admit_a_temporal.py'), run_name='__main__')
    except RuntimeError as exc:
        error = str(exc)
    expected = 'all-426 frozen source identity gate not accepted; no inference admission'
    passed = error == expected and not attempted and not admission.exists()
    report = {'status': 'PASS_ORIGINAL_A_BLOCK_BEFORE_RUNTIME' if passed else 'FAIL_BLOCK_VERIFICATION',
        'actual_error': error, 'runtime_import_attempts': attempted,
        'created_admission': admission.exists(), 'GPU_job_launched': False,
        'prior_receipt_sha256': hashlib.sha256((RUN/'baseline_pts_v3/scan_01/pts_origin_receipt.json').read_bytes()).hexdigest(),
        'admission_script_sha256': hashlib.sha256((CTRL/'admit_a_temporal.py').read_bytes()).hexdigest()}
    with (CTRL/'a_original_identity_block_receipt.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report))
    raise SystemExit(0 if passed else 1)
