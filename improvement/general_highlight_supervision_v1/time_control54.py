"""First GPU execution only; adopt53 CPU QA, repair wrapper integer budget argument."""
import json
import math
import os
from pathlib import Path
import subprocess
import traceback
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import RUN,PY,WRAPPER,checked

ROOT=ADMISSION/'time_control54';DATA=ADMISSION/'time_control53';CODE=Path(__file__).parent
JOB='sportclip_diving_original_TIME_control_20261022_remaining54'


def execute(stage, command, gpu=False):
    with (ROOT/(stage+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
        save(ROOT/(stage+'_launch.json'),dict(command=command,pid=process.pid,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(ROOT/(stage+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('Actual remaining stage failed: '+stage)


def main():
    ROOT.mkdir()
    if 'invalid int value' not in (DATA/'gpu.log').read_text() or list((DATA/'outputs').glob('*/raw.json')):
        raise ValueError('Expected wrapper-argument-only0-model failure differs')
    if read(DATA/'independent_adopted_CPU_QA53.json')['state']!='PASS':raise ValueError('Prior actual CPU QA not passed')
    prior_name='sportclip_diving_original_TIME_control_20261022_remaining51'
    prior=read(RUN/'controller'/(prior_name+'.resource.json'))
    maximum=math.floor(read(DATA/'protocol.json')['GPU_seconds_max']-prior['charged_seconds'])
    save(ROOT/'registration.json',dict(source=read(DATA/'registration.json')['source'],
        prior_failure=ref(DATA/'failure.json'),argument_failure_log=ref(DATA/'gpu.log'),
        adopted_CPU_QA=ref(DATA/'independent_adopted_CPU_QA53.json'),source_input_lock=ref(DATA/'source_input_lock.json'),
        model_data_root=str(DATA),prior_successful_model_calls=0,integer_remaining_seconds=maximum,
        only_repair='Round down remaining wrapper argument to declared integer type; no CPU check/decode/processor/model success repeated',
        prior_fee=prior['charged_seconds'],new_code=ref(Path(__file__))))
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
    if apps.strip():raise RuntimeError('Protect shared external GPU workload')
    save(ROOT/'resource_admission.json',dict(compute_apps=apps,GPU=subprocess.check_output(['nvidia-smi'],text=True),
        RAM=subprocess.check_output(['free','-b'],text=True),disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
        reason='Actual10 accepted native64 inputs; prior21.9GB model peak and no other compute, no new large inputs; Java CPU protected'))
    command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds',str(maximum),'--planned-output-bytes','16000000',
        '--capacity-reason','Only first10 originalTIME calls; independent actual CPU check adopted, namespace repaired and integer remaining budget validated',
        '--queue-seconds','0','--',str(PY),'-B','-u',str(CODE/'time_entry53.py'),'gpu']
    execute('gpu',command,True)
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
        raise ValueError('Natural remaining GPU terminal/unique ledger differs')
    execute('review',[str(PY),'-B','-u',str(CODE/'time_entry53.py'),'review'])
    checked(read(DATA/'registration.json')['protected_baseline'])
    save(ROOT/'completion.json',dict(state=read(DATA/'review.json')['state'],time_review=ref(DATA/'review.json'),
        CPU_audit=ref(DATA/'independent_CPU_audit.json'),selections=ref(DATA/'selections.npz'),
        model_data_root=str(DATA),new_model_calls=read(DATA/'gpu_completion.json')['actual_calls'],
        GPU_seconds=record['charged_seconds'],prior_GPU_failure_seconds=prior['charged_seconds'],new_ZIP=0,baseline_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_repeat_success=True))
        raise
