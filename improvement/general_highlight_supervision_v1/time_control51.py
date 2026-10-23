"""Explicit zero-input import recovery; adopt protocol, new root, no successful work repeats."""
import json
import os
from pathlib import Path
import subprocess
import traceback
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import RUN,PY,WRAPPER,checked

ROOT=ADMISSION/'time_control51'
CODE=Path(__file__).parent
JOB='sportclip_diving_original_TIME_control_20261022_remaining51'


def stage(name):
    command=[str(PY),'-B','-u',str(CODE/'time_entry51.py'),name]
    if name=='gpu':
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('Protect external GPU workload')
        save(ROOT/'resource_admission.json',dict(compute_apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'],text=True),RAM=subprocess.check_output(['free','-b'],text=True),
            disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            reason='12 first originalTIME windows, previous native64 actual21.9GB, no external compute; already accepted compressed CPU payload and Java CPU protected'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','600','--planned-output-bytes','16000000',
            '--capacity-reason','First originalTIME held-sport control; explicit0-input import recovery adopts unchanged protocol, no successful model repeated',
            '--queue-seconds','0','--']+command
    with (ROOT/(name+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if name=='gpu' else '',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        save(ROOT/(name+'_launch.json'),dict(command=command,pid=process.pid,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(name+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual remaining stage failed: '+name)


def main():
    ROOT.mkdir();old=ADMISSION/'time_control50'
    if "No module named 'exact_pts'" not in (old/'prepare.log').read_text() or list(old.glob('inputs/*/CPU_acceptance.json')):
        raise ValueError('Expected zero-input import failure differs')
    protocol=read(old/'protocol.json');registration=read(old/'registration.json')
    save(ROOT/'protocol.json',protocol);save(ROOT/'registration.json',registration)
    save(ROOT/'remaining_registration.json',dict(prior_failure=ref(old/'failure.json'),prior_stage_log=ref(old/'prepare.log'),
        old_protocol=ref(old/'protocol.json'),old_registration=ref(old/'registration.json'),
        actual_prior_successful_inputs=0,actual_prior_GPU_calls=0,
        only_repair='Explicit existing baseline_a_pts_v1 and temporal_sft8b_v1 import paths before legacy runtime; independent remaining directory',
        no_scientific_protocol_change=True))
    stage('prepare');cpu=read(ROOT/'CPU_completion.json')
    if not 0<cpu['windows']<=protocol['unique_new_calls_max']:raise ValueError('Actual fixed window denominator differs')
    names=['common.py','time_control50_common.py','time_control50_prepare.py','time_control50_gpu.py','time_control50_review.py','time_entry51.py','time_control51.py']
    save(ROOT/'source_input_lock.json',dict(code={n:ref(CODE/n) for n in names},
        CPU=ref(ROOT/'CPU_completion.json'),protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),
        recovery=ref(ROOT/'remaining_registration.json'),wrapper=ref(WRAPPER)))
    stage('gpu')
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
        raise ValueError('Natural GPU terminal / unique ledger differs')
    stage('review');checked(registration['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],review=ref(ROOT/'review.json'),
        GPU_seconds=record['charged_seconds'],actual_new_calls=cpu['windows'],new_ZIP=0,baseline_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),keep_successes_and_raw=True))
        raise
