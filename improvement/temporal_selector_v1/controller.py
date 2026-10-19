"""Unique explicit phase chain; CPU children mask only themselves."""
import datetime as dt
import subprocess
import sys
import time
import traceback
from common import *


def run(stage,command,cpu=True):
    protocol=read(ROOT/'protocol.json')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(protocol['deadline_utc']),
            'Registered20h job window ended; no new stage')
    env=dict(os.environ,AIC_TEMPORAL_ROOT=str(ROOT),PYTHONDONTWRITEBYTECODE='1',
             PYTHONNOUSERSITE='1',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
             OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    if cpu:env['CUDA_VISIBLE_DEVICES']=''
    else:require(env.get('CUDA_VISIBLE_DEVICES','')!='','Parent actual CUDA must remain nonempty')
    log=ROOT/(stage+'.log')
    with log.open('x') as stream:
        child=subprocess.Popen([str(x) for x in command],cwd=ROOT,stdin=subprocess.DEVNULL,
                               stdout=stream,stderr=subprocess.STDOUT,env=env)
        stat=Path('/proc',str(child.pid),'stat').read_text();tail=stat[stat.rfind(')')+2:].split()
        row=dict(stage=stage,pid=child.pid,start_ticks=tail[19],command=list(map(str,command)),CPU_child=cpu,
                 parent_cuda=os.environ.get('CUDA_VISIBLE_DEVICES'),child_cuda=env.get('CUDA_VISIBLE_DEVICES'),utc=utc())
        write(ROOT/(stage+'_launch.json'),row);replace_state(dict(status='RUNNING',**row))
        code=child.wait()
    require(code==0,stage+' failed with exit '+str(code)+'; retain log and all successful stages')
    event('STAGE_NATURAL_COMPLETION',stage_name=stage,exit_code=code)


def gpu(phase,scope,max_seconds,planned):
    name='temporal_selector_'+phase+'_20261018_v1'
    remaining=int((dt.datetime.fromisoformat(read(ROOT/'protocol.json')['deadline_utc'])-
                   dt.datetime.now(dt.timezone.utc)).total_seconds())
    require(remaining>300,'Insufficient remaining registered job window')
    wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
    command=[PYTHON,'-B',wrapper,'--name',name,'--max-seconds',str(min(max_seconds,remaining)),
             '--planned-output-bytes',str(planned),'--capacity-reason',
             'Reuse accepted image tensors without decode or duplicate pixel storage; save pooled one-layer new TIME features only',
             '--queue-seconds','60','--',PYTHON,'-B','-u',ROOT/'code/features.py','infer',scope,phase]
    run('gpu_'+phase,command,cpu=False)
    write(ROOT/(phase+'_resource_acceptance.json'),gpu_terminal(name))
    run('output_QA_'+phase,[PYTHON,'-B',ROOT/'code/features.py','qa',scope,phase])


def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES','')!='','Unique parent actual CUDA index required')
    write(ROOT/'chain_started.json',dict(pid=os.getpid(),utc=utc(),new_goal=False,new_automation=False))
    run('review_regressions',[PYTHON,'-B',ROOT/'review_snapshot/tools/check_review_regressions.py'])
    run('mapping_tests',[PYTHON,'-B',ROOT/'code/test_mapping.py'])
    run('head_tests',[PYTHON,'-B',ROOT/'code/test_head.py'])
    run('prepare_external',[PYTHON,'-B','-u',ROOT/'code/data.py','external'])
    gpu('pilot32','external',3600,32*32*8192*4+8_000_000)
    pilot=read(ROOT/'pilot32_acceptance.json')
    require(pilot['status']=='PASS32_REAL_TIME_GROUP_FEATURES_AND_COST','32-window mapping/finite/cost milestone')
    # Choose workload from observed throughput and cached metadata, not a fixed free-resource threshold.
    acceptance=read(ROOT/'acceptance_external.json')
    from mapping import window_schedule
    old=read(PRODUCTION/'cpu_acceptance.json')
    production_windows=sum(len(window_schedule(s['feature_cells'])) for s in old['sources'])
    estimate=(acceptance['window_count']-32+production_windows)*pilot['mean_forward_seconds']*2+4*3600
    remaining=(dt.datetime.fromisoformat(read(ROOT/'protocol.json')['deadline_utc'])-dt.datetime.now(dt.timezone.utc)).total_seconds()
    write(ROOT/'measured_scale_decision.json',dict(pilot=reference(ROOT/'pilot32_acceptance.json'),
         external_windows=acceptance['window_count'],production_windows=production_windows,
         measured_compute_plus_CPU_QA_buffer_seconds=estimate,remaining_registered_seconds=remaining,
         permitted=estimate<remaining,dynamic_capacity_bytes=__import__('shutil').disk_usage(WORK).free,
         extra_feature_estimate_bytes=(acceptance['window_count']+production_windows)*32*8192*4+600_000_000))
    require(estimate<remaining,'Measured full scale exceeds this20h budget; preserve pilot, do not overrun or shrink QA')
    gpu('remaining_external','external',7200,acceptance['window_count']*32*8192*4+8_000_000)
    run('assemble_external',[PYTHON,'-B',ROOT/'code/train.py','assemble','--scope','external'])
    run('train_two_heads',[PYTHON,'-B','-u',ROOT/'code/train.py','train'])
    run('prepare_production',[PYTHON,'-B','-u',ROOT/'code/data.py','production'])
    production=read(ROOT/'acceptance_production.json')
    require(production['window_count']==production_windows,'New production workload differs from measured registration')
    gpu('production','production',21600,production_windows*32*8192*4+8_000_000)
    run('assemble_production',[PYTHON,'-B',ROOT/'code/train.py','assemble','--scope','production'])
    run('apply_two_heads',[PYTHON,'-B',ROOT/'code/train.py','apply'])
    run('package_two_candidates',[PYTHON,'-B','-u',ROOT/'code/package.py'])
    completion=read(ROOT/'completion.json')
    replace_state(dict(status=completion['status'],delivered_remote=len(completion['deliveries']),utc=utc()))
    write(ROOT/'chain_completion.json',dict(status='NATURAL_COMPLETE_ALL_REGISTERED_STAGES',
          completion=reference(ROOT/'completion.json'),utc=utc(),goal_created=False,automation_created=False))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        if not (ROOT/'chain_failure.json').exists():
            write(ROOT/'chain_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        replace_state(dict(status='FAILED_PRESERVE_ALL_EVIDENCE_NO_AUTOMATIC_RETRY',error=repr(error),utc=utc()))
        raise
