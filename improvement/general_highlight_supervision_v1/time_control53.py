"""Remaining model calls only after a zero-call namespace failure; science unchanged."""
import json
import os
from pathlib import Path
import subprocess
import traceback
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import RUN,PY,WRAPPER,checked

ROOT=ADMISSION/'time_control53';CODE=Path(__file__).parent
JOB='sportclip_diving_original_TIME_control_20261022_remaining53'


def stage(name,max_seconds):
    command=[str(PY),'-B','-u',str(CODE/'time_entry53.py'),name]
    if name=='gpu':
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('Protect external GPU task')
        save(ROOT/'resource_admission.json',dict(compute_apps=apps,GPU=subprocess.check_output(['nvidia-smi'],text=True),
            RAM=subprocess.check_output(['free','-b'],text=True),disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            reason='Ten existing native64 real CPU caches independently accepted; prior native64 peak21.9GB and no external GPU; namespace checked before paid call, Java protected'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds',str(max_seconds),'--planned-output-bytes','16000000',
            '--capacity-reason','Only remaining first10 originalTIME calls; CPU caches and canonical namespace checked, prior0-model failure fee deducted',
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
    ROOT.mkdir();old=ADMISSION/'time_control51'
    old_job='sportclip_diving_original_TIME_control_20261022_remaining51'
    failure_log=RUN/'controller'/(old_job+'.log')
    if "name 'require' is not defined" not in failure_log.read_text() or list((old/'outputs').glob('*/raw.json')):
        raise ValueError('Expected zero-model namespace failure differs')
    prior=read(RUN/'controller'/(old_job+'.resource.json'))
    if prior['status']!='failed' or prior['exit_code']==0:raise ValueError('Prior unique terminal differs')
    registration=read(old/'registration.json');protocol=read(old/'protocol.json');cpu=read(old/'CPU_completion.json')
    save(ROOT/'protocol.json',protocol);save(ROOT/'registration.json',registration);save(ROOT/'CPU_completion.json',cpu)
    remaining=protocol['GPU_seconds_max']-prior['charged_seconds']
    save(ROOT/'remaining_registration.json',dict(prior_failure=ref(old/'failure.json'),failure_detail=ref(failure_log),
        adopted_CPU_completion=ref(old/'CPU_completion.json'),adopted_windows=cpu['windows'],
        prior_successful_model_calls=0,prior_fee=prior['charged_seconds'],remaining_GPU_seconds=remaining,
        only_repair='Load canonical original B common/helper namespace before importing original runtime; no source/inputs/weights/recipe change',
        original_prepare_not_repeated=True,old_failures_preserved=True))
    stage('check',remaining)
    names=['common.py','time_control50_common.py','time_control50_gpu.py','time_control50_review.py','time_entry53.py','time_control53.py']
    save(ROOT/'source_input_lock.json',dict(code={name:ref(CODE/name) for name in names},
        protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),CPU=ref(ROOT/'CPU_completion.json'),
        new_independent_adoption_QA=ref(ROOT/'independent_adopted_CPU_QA53.json'),wrapper=ref(WRAPPER)))
    stage('gpu',remaining)
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
        raise ValueError('Natural remaining GPU terminal / unique ledger differs')
    stage('review',remaining);checked(registration['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(ROOT/'review.json')['state'],review=ref(ROOT/'review.json'),
        GPU_seconds=record['charged_seconds'],prior_failed_GPU_seconds=prior['charged_seconds'],
        actual_first_calls=cpu['windows'],CPU_inputs_not_repeated=True,baseline_unchanged=True,new_ZIP=0))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),keep_all_success=True))
        raise
