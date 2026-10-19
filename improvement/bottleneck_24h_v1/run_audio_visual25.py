"""Finite ASR-text pilot after existing loss20/43 sequence, no production."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback

W=Path('/home/inspur/aic_video_work');P=W/'bottleneck_24h_20261019_v1'
R=P/'audio_semantic23';N=P/'summary_objective_v20'
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY=str(W/'env/qwen3vl_isolated_20260910/bin/python')


def read(p):return json.loads(Path(p).read_text())


def ref(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb')as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())


def bound(r):
    p=Path(r['path']);assert p.is_relative_to(W)and ref(p)==r;return p


def save(p,v):
    with Path(p).open('x')as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())


def cpu(reg,phase):
    with(R/('audio_visual_%s25.log'%phase)).open('xb')as f:
        result=subprocess.run([PY,'-B',str(bound(reg['code_ref'])),'--phase',phase],
            stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    save(R/('audio_visual_%s_terminal25.json'%phase),dict(exit_code=result.returncode,automatic_retry=False))
    assert result.returncode==0,'Actual CPU failure; no retry or failure-to-empty'


def main():
    assert os.uname().nodename=='inspur-NP5570M5'and os.environ.get('CUDA_VISIBLE_DEVICES')not in(None,'')
    reg=read(R/'audio_visual_registration_25.json');assert bound(reg['parent_code_ref'])==Path(__file__).resolve()
    save(R/'audio_visual_claim25.json',dict(pid=os.getpid(),registration_ref=ref(R/'audio_visual_registration_25.json'),
        no_training_launch=True,no_automatic_production_or_package=True))
    cpu(reg,'prepare')
    count=read(R/'first_audio_visual_input_acceptance25.json')['new_model_calls_required']
    if count:
        # Scheduling dependency only. No repeated training/INIT/43/CPU metrics.
        launch=read(bound(reg['existing_after_training_launch_ref']));missing=0
        while not(N/'after_training_completion_21.json').exists():
            assert not(N/'after_training_failure_21.json').exists(),'Existing main chain failed; do not take its GPU turn'
            assert datetime.now(timezone.utc)<datetime(2026,10,19,11,52,37,tzinfo=timezone.utc)
            proc=Path('/proc')/str(launch['pid'])
            try:
                argv=(proc/'cmdline').read_bytes().decode().strip('\0').split('\0')
                ticks=int((proc/'stat').read_text().rsplit(') ',1)[1].split()[19])
                live=argv==launch['argv']and ticks==launch['start_ticks']
            except(FileNotFoundError,ProcessLookupError):live=False
            missing=0 if live else missing+1;assert missing<4,'Existing dependency handle missing; stop without model retry'
            time.sleep(30)
        done=read(N/'after_training_completion_21.json')
        assert done['status']=='COMPLETE_LOSS_ONLY20_NEW43_COMPARISON_REQUIRES_MAIN_REVIEW'
        resources=dict(host=os.uname().nodename,load=os.getloadavg(),disk_free=shutil.disk_usage(W).free,
            memory_available=int(next(line for line in Path('/proc/meminfo').read_text().splitlines()if line.startswith('MemAvailable:')).split()[1])*1024,
            GPU=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True).strip(),
            GPU_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip())
        assert not resources['GPU_apps'],'External job active; no interference or model launch'
        assert resources['disk_free']>reg['planned_output_bytes']and resources['memory_available']>reg['host_working_estimate']
        job=reg['job_name'];resource=RUN/'controller'/(job+'.resource.json')
        assert not resource.exists()and not any(json.loads(line).get('name')==job for line in(W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()if line.strip())
        command=[PY,str(bound(reg['gpu_wrapper_ref'])),'--name',job,'--max-seconds','600',
            '--planned-output-bytes',str(reg['planned_output_bytes']),'--capacity-reason',
            'Fixed8 external ASR-text pilot; '+str(count)+' genuinely new originalTIME calls, remaining validASR-abstentions adopt old visual. '
            'No train or new images. Actual original pipeline+ASR under9B; frozenCPU inputs accepted. '+json.dumps(resources),
            '--queue-seconds','120','--',PY,'-B',str(bound(reg['code_ref'])),'--phase','generate']
        save(R/'audio_visual_gpu_launch25.json',dict(command=command,resources=resources,main_dependency_completion_ref=ref(N/'after_training_completion_21.json')))
        with(R/'audio_visual_gpu_wrapper25.log').open('xb')as log:
            result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES=resources['GPU'].split(',')[0].strip(),PYTHONDONTWRITEBYTECODE='1'))
        assert result.returncode==0,'Actual new pilotGPU failure; preserve every raw, no retry'
    cpu(reg,'evaluate')
    save(R/'audio_visual_completion25.json',dict(status='COMPLETE_FIXED8_AUDIO_TEXT_COMPARISON_REQUIRES_MAIN_REVIEW',
        comparison_ref=ref(R/'audio_visual_comparison25.json'),new_model_calls=count,training_updates=0,
        automatic426=False,automatic_package=False,official_improvement_asserted=False))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        p=R/('audio_visual_parent_failure25_%s.json'%os.getpid())
        if not p.exists():save(p,dict(error=repr(error),traceback=traceback.format_exc(),automatic_retry=False,successes_preserved=True))
        raise
