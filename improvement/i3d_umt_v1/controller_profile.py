"""One authorized download -> one registered shared-GPU engineering profile."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from provenance import reference, write_new

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PYTHON = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE_DIR = WRAPPER.parent.parent / 'controller'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'
JOB = 'i3d_umt_raw4_pretrained_profile_20261021_v07'


def stage(name, command, gpu=False):
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '',
                       PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2',
                       MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1')
    started = time.monotonic()
    with (ROOT / f'{name}.log').open('x') as log:
        child = subprocess.Popen(list(map(str, command)), cwd=ROOT, env=environment,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        start_ticks = Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        write_new(ROOT / f'{name}_launch.json', dict(pid=child.pid, start_ticks=start_ticks,
                                                  argv=list(map(str, command))))
        code = child.wait()
    write_new(ROOT / f'{name}_terminal.json', dict(exit_code=code, seconds=time.monotonic() - started))
    if code:
        raise RuntimeError(f'{name} naturally failed; preserve partials, no automatic retry')


def main():
    write_new(ROOT / 'controller07_claim.json', dict(argv=sys.argv, scope='DOWNLOAD_AND_RAW_PROFILE_ONLY'))
    stage('download07', [PYTHON, '-B', ROOT / 'acquire_weight_direct07.py', '--root', ROOT])
    source_lock = dict(
        acquisition_authorization=reference(ROOT / 'weight_authorization.json'),
        weight=reference(ROOT / 'weights/I3D_8x8_R50.pyth'),
        direct_route=reference(ROOT / 'weight_direct_route.json'),
        code={n: reference(ROOT / n) for n in ['profile_gpu.py', 'runtime.py', 'provenance.py']},
        CPU=reference(ROOT / 'cpu04_completion.json'),
        inputs=reference(ROOT / 'raw_profile03/completion.json'),
        wrapper=reference(WRAPPER),
        counts=dict(i3d_forwards=4, untrained_umt_forwards=2, updates=0, official_data=0),
        max_gpu_seconds=120, planned_new_profile_bytes=16 * 1024**2,
        quality_claim=False, automatic_training_or_production=False,
    )
    assert source_lock['wrapper']['sha256'] == '9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec'
    resource = RESOURCE_DIR / f'{JOB}.resource.json'
    assert not resource.exists(), 'Never duplicate a registered GPU job'
    write_new(ROOT / 'profile_source_lock07.json', source_lock)
    stage('profile07', [PYTHON, '-B', WRAPPER, '--name', JOB, '--max-seconds', '120',
                       '--planned-output-bytes', str(source_lock['planned_new_profile_bytes']),
                       '--capacity-reason',
                       'GPU empty live; four accepted RGB clips, 34.3M auxiliary params, <=16MiB new profile output; no Qwen load or outside task changes',
                       '--queue-seconds', '0', '--', PYTHON, '-B', ROOT / 'profile_gpu.py', '--root', ROOT], gpu=True)
    record = json.loads(resource.read_text())
    ledger_rows = [json.loads(s) for s in LEDGER.read_text().splitlines() if s.strip()]
    assert record['status'] == 'completed' and record['exit_code'] == 0
    assert [row for row in ledger_rows if row.get('name') == JOB] == [record]
    output = ROOT / 'pretrained_profile04/completion.json'
    result = json.loads(output.read_text())
    assert result['actual_i3d_feature_forwards'] == 4 and result['actual_untrained_umt_forwards'] == 2
    write_new(ROOT / 'controller07_completion.json', dict(
        status='PRETRAINED_RAW_PROFILE_COMPLETE_NO_QUALITY_CLAIM', profile=reference(output),
        resource=reference(resource), unique_ledger='PASS',
        charged_seconds=record.get('charged_seconds'),
        sampled_peak_memory_mib=record.get('sampled_peak_memory_mib'),
        training_updates=0, production_allowed=False,
    ))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write_new(ROOT / 'controller07_failure.json', dict(status='ACTUAL_FAILURE_NO_AUTO_RETRY',
                                                          traceback=traceback.format_exc()))
        raise
