"""Single bounded source-admitted pilot; no old stage relaunch or production."""
import os
from pathlib import Path
import subprocess
import time
import traceback

from pilot15_common import ADMISSION, ROOT, WORK, ENGINEERING, checked, read, ref, save

PY=WORK/'env/qwen3vl_isolated_20260910/bin/python'
RUN=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
JOB='upm_sportclip4_matched_HL_supervision_20261021_v16'
CODE=Path(__file__).parent


def stage(name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/('pilot15_'+name+'.py'))]
    if gpu:
        if ref(WRAPPER)['sha256']!='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
            raise ValueError('Shared wrapper differs')
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('External compute workload present; no automatic competing launch')
        save(ROOT/'resource_admission.json',dict(actual_compute_apps=apps,
            GPU_snapshot=subprocess.check_output(['nvidia-smi'],text=True),
            actual_memory=subprocess.check_output(['free','-b'],text=True),
            capacity_reason='Only accepted I3D28M and UMT6.2M; prior I3D actual223MiB,4 sources, no Qwen load; protect external tasks'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','600',
            '--planned-output-bytes','65000000','--capacity-reason',
            'Fresh direct author4 dense-HL sources; frozen I3D and one UMT fit; no8B load, prior I3D223MiB, external apps absent; actual capacity saved',
            '--queue-seconds','0','--']+command
    with (ROOT/(name+'.log')).open('x') as log:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        save(ROOT/(name+'_launch.json'),dict(pid=process.pid,command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(name+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual first stage failed: '+name)
    if gpu:
        import json
        record=read(RUN/'controller'/(JOB+'.resource.json'))
        rows=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
        if record['status']!='completed' or record['exit_code']!=0 or [row for row in rows if row.get('name')==JOB]!=[record]:
            raise ValueError('GPU natural terminal/unique ledger differs')


def main():
    save(ROOT/'controller_claim.json',dict(pid=os.getpid(),single_pilot=True,no_production=True))
    start=time.monotonic()
    while not (ADMISSION/'native_remaining14_completion.json').exists():
        if (ADMISSION/'native_remaining14_failure.json').exists():raise ValueError('Native admission actually failed')
        if time.monotonic()-start>600:raise TimeoutError('Bounded asset wait elapsed')
        time.sleep(2)
    stage('checks');stage('prepare')
    save(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),
        code={p.name:ref(p) for p in CODE.glob('*.py')},
        adopted_old_code={name:ref(ENGINEERING/name) for name in ['runtime.py','profile_gpu.py','prepare_raw.py']},
        inputs=ref(ROOT/'input_acceptance.json'),registration=ref(ROOT/'registration.json'),
        original_native_admission=ref(ADMISSION/'native_remaining14_completion.json'),wrapper=ref(WRAPPER)))
    stage('gpu',True);stage('review')
    checked(read(ROOT/'registration.json')['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],review=ref(ROOT/'review.json'),
        new_ZIP=0,baseline40_47_unchanged=True,no_automatic_production=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_automatic_retry=True))
        raise
