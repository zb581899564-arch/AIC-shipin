"""One new whole-source semantic probe, with first CPU inputs and unique shared GPU job."""
import os
from pathlib import Path
import subprocess
import time
import traceback
from common import ROOT,WORK,read,ref,save
from pilot_common28 import WRAPPER,RUN,PY,checked

TARGET=ROOT/'speech_rank42'
JOB='whole_source_ASR_semantic_rank4_20261022_v42'
CODE=Path(__file__).parent


def execute(script,name,gpu=False):
    command=[str(PY),'-B','-u',str(CODE/script)]
    parent=TARGET if TARGET.exists() else ROOT
    if gpu:
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
        if apps.strip():raise RuntimeError('External GPU compute present; protect it')
        save(TARGET/'resource_admission.json',dict(GPU=subprocess.check_output(['nvidia-smi'],text=True),
            RAM=subprocess.check_output(['free','-b'],text=True),disk=subprocess.check_output(['df','-B1',str(ROOT)],text=True),
            actual_compute_apps=apps,reason='One original frozen8B,8 pure-text calls; prior model peak21GB on48GB GPU, no competing compute; CPU ASR completed, Java untouched'))
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','900','--planned-output-bytes','2000000',
            '--capacity-reason','One protected original8B with same loaded tensors;8 first whole-source text inputs, no optimizer/vision/WhisperGPU; actual no-conflict snapshot saved',
            '--queue-seconds','0','--']+command
    with (parent/(name+'.log')).open('x') as log:
        process=subprocess.Popen(command,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
        save(parent/(name+'_launch.json'),dict(pid=process.pid,command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code=process.wait()
    save(parent/(name+'_terminal.json'),dict(exit_code=code))
    if code:raise RuntimeError('First whole-speech stage actually failed: '+name)
    if gpu:
        record=read(RUN/'controller'/(JOB+'.resource.json'))
        rows=[__import__('json').loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
        if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
            raise ValueError('Natural GPU terminal/unique ledger differs')
        return record


def main():
    if not (ROOT/'speech_chain38/completion.json').exists():raise ValueError('New actual ASR chain not complete')
    execute('speech_inputs39.py','speech_inputs39')
    save(TARGET/'source_input_lock.json',dict(registration=ref(TARGET/'registration.json'),
        code={name:ref(CODE/name) for name in ['common.py','pilot_common28.py','score_contract39.py','speech_inputs39.py','speech_gpu40.py','speech_review41.py','speech_chain42.py']},
        wrapper=ref(WRAPPER),native_inputs=ref(ROOT/'speech36/input_acceptance.json'),ASR=ref(ROOT/'speech36/ASR_completion.json')))
    record=execute('speech_gpu40.py','gpu',True);execute('speech_review41.py','review')
    checked(read(ROOT/'media24/registration.json')['protected_baseline'])
    review=read(TARGET/'review.json')
    save(TARGET/'completion.json',dict(state=review['state'],review=ref(TARGET/'review.json'),
        GPU_seconds=record['charged_seconds'],new8B_calls=8,new_training=0,new_ZIP=0,
        baseline40_47_unchanged=True,no_automatic_production=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        save(ROOT/'speech42_failure.json',dict(traceback=traceback.format_exc(),no_silent_retry=True));raise
