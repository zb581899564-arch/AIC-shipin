"""Bounded single controller; adopt CPU completion, then unique shared GPU jobs."""
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

from common import ENGINEERING, ROOT, WORK, checked, read, reference, write_new

PY = WORK/'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE = WRAPPER.parent.parent/'controller'
LEDGER = WORK/'improvement_round1/gpu_ledger.jsonl'


def stage(name,script,gpu=False,budget=0):
    env = dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    command = [str(PY),'-u','-B',str(ROOT/'code'/script)]
    job = f'i3d_umt_crossdata12_{name}_20261021_v1'
    resource = RESOURCE/f'{job}.resource.json'
    if gpu:
        assert not resource.exists(), 'Do not repeat registered GPU job'
        command = [str(PY),'-B',str(WRAPPER),'--name',job,'--max-seconds',str(budget),
                   '--planned-output-bytes','150000000','--capacity-reason',
                   'Real accepted RGB profile on33 external sources; I3D28M frozen or UMT6.2M only, previous short profile223MiB; no Qwen load, no outside process changes',
                   '--queue-seconds','0','--']+command
    started=time.monotonic()
    with (ROOT/f'{name}.log').open('x') as log:
        p=subprocess.Popen(command,env=env,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        write_new(ROOT/f'{name}_launch.json',dict(pid=p.pid,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],argv=command))
        code=p.wait()
    write_new(ROOT/f'{name}_terminal.json',dict(exit_code=code,seconds=time.monotonic()-started))
    if code:
        raise RuntimeError(f'{name} failed, no automatic retry')
    if gpu:
        record=read(resource)
        rows=[json.loads(s) for s in LEDGER.read_text().splitlines() if s.strip()]
        assert record['status']=='completed' and record['exit_code']==0
        assert [r for r in rows if r.get('name')==job]==[record]


def main():
    write_new(ROOT/'controller_claim.json',dict(scope='CPU gates -> first features -> one final fit -> held review; NEVER automatic426'))
    launch=read(ROOT/'prepare_launch13.json')
    proc=Path(f'/proc/{launch["pid"]}/stat')
    while not (ROOT/'input_acceptance.json').exists():
        if not proc.exists() or proc.read_text().rsplit(')',1)[1].split()[19]!=launch['start_ticks']:
            raise RuntimeError('Preparation ended without authoritative acceptance; inspect actual log, no relaunch')
        time.sleep(5)
    # Code/input/source/model locks precede all new GPU work.
    checked(read(ROOT/'registration.json')['protected_baseline'])
    code={p.name:reference(p) for p in sorted((ROOT/'code').glob('*.py'))}
    lock=dict(protocol=reference(ROOT/'protocol.json'),code=code,
              inputs=reference(ROOT/'input_acceptance.json'),sources=reference(ROOT/'registration.json'),
              wrapper=reference(WRAPPER),weight=read(ENGINEERING/'weight_acceptance.json'),
              model_parameters=8816809946,old_profile=reference(ENGINEERING/'controller07_completion.json'))
    assert lock['wrapper']['sha256']=='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec'
    write_new(ROOT/'source_input_lock.json',lock)
    # New differentiable-path CPU checks were completed exactly once before launch13.
    assert read(ROOT/'new_cpu_contracts.json')['status']=='PASS'
    stage('features','features.py',True,1200)
    stage('fit','fit_and_review.py',True,1200)
    checked(read(ROOT/'registration.json')['protected_baseline'])
    write_new(ROOT/'completion.json',dict(status='PILOT_COMPLETE_NOT_PRODUCTION',
              review=reference(ROOT/'review.json'),features=reference(ROOT/'feature_acceptance.json'),
              updates=400,new_zip=0,baseline_unchanged=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write_new(ROOT/'failure.json',dict(status='REAL_FAILURE_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()))
        raise
