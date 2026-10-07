"""Once-only Z execution, current Linux capacity and frozen Mac reservation."""
from common import *
import datetime as dt
import os
import shutil
import subprocess
import time
import traceback
from resource_contract import admit_capacity

def checkpoint(stage,**extra):
    value=dict(stage=stage,utc=dt.datetime.now(dt.timezone.utc).isoformat(),pid=os.getpid(),uploaded=False,**extra)
    progress(HERE,value);return value

def capacity(planned):
    linux=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    return admit_capacity(read(HERE/'quota_plan.json'),linux,shutil.disk_usage(ROOT).free,planned,base_dir=HERE)

def gpu(script,stage,scope,out,maximum,planned):
    verify();evidence=capacity(planned)
    name='rematch_NEXT8B_v1_'+scope+'_'+stage+'_01'
    write(HERE/(name+'.admission.json'),dict(authorized=True,user_request='按照这个结论先修代码制定路线并执行',
        source_lock_sha256=sha(HERE/'source_lock.json'),capacity=evidence,max_seconds=maximum,planned_output_bytes=planned,official_upload_authorized=False))
    command=[sys.executable,'-B',str(HERE/'gpu_run.py'),'--name',name,'--max-seconds',str(maximum),
        '--planned-output-bytes',str(planned),'--capacity-reason','Frozen Mac total 28GiB plus 1GiB shared scratch; current Linux outputs fit 51GiB quota',
        '--queue-seconds','1800','--',sys.executable,'-B',str(HERE/script),stage,scope,str(out)]
    checkpoint('RUNNING_'+scope.upper()+'_'+stage.upper(),job=name,capacity=evidence)
    with (HERE/(name+'.wrapper.log')).open('x') as stream:
        p=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,cwd=RUN)
    resource=RUN/'controller'/(name+'.resource.json')
    require(p.returncode==0 and resource.exists() and read(resource)['status']=='completed','GPU phase failed: '+name)

def cpu(stage,scope,out,timeout):
    verify();capacity(700000000 if scope=='rematch' else 60000000)
    checkpoint('RUNNING_'+scope.upper()+'_'+stage.upper())
    with (HERE/(scope+'_'+stage+'.log')).open('x') as stream:
        p=subprocess.run([sys.executable,'-B',str(HERE/'production.py'),stage,scope,str(out)],cwd=RUN,
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
    require(p.returncode==0,'CPU phase failed: '+scope+' '+stage)

def main():
    write(HERE/'continuation_registration.json',dict(pid=os.getpid(),utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_lock_sha256=sha(HERE/'source_lock.json')))
    try:
        verify()
        require(read(HERE/'cpu_02/processor_acceptance.json')['status']=='PASS_REAL_PROCESSOR_AND_EMPTY_TARGET','processor acceptance missing')
        gpu('engine.py','probe','synthetic',HERE/'probe_01',3600,30000000)
        gpu('engine.py','aligned_dev','open_dev',HERE/'dev_01',14400,60000000)
        for scope in ('nontest','rematch'):
            out=HERE/(scope+'_01');out.mkdir()
            gpu('engine.py','temporal',scope,out,14400,60000000)
            cpu('scheduling',scope,out,7200)
            schedule=read(out/'schedule.stage.json')
            anchors=schedule['anchors'];frames=schedule['field_frames'];selected=schedule['selected_frames']
            measure=read(HERE/'nontest_01/spatial.stage.json') if scope=='rematch' else None
            # Whole-source anchors, measured same-model non-test cost; no 4B/Mac timing assumption.
            maximum=3600 if measure is None else max(3600,int(anchors*measure['measured_seconds_per_anchor']*2+1200))
            planned=anchors*6000+selected*2500+20000000
            write(HERE/(scope+'_spatial_registration.json'),dict(anchors=anchors,field_frames=frames,selected_frames=selected,
                maximum_seconds=maximum,planned_output_bytes=planned,measured_nontest_seconds_per_anchor=None if measure is None else measure['measured_seconds_per_anchor']))
            if anchors:gpu('production.py','spatial',scope,out,maximum,planned)
            else:subprocess.run([sys.executable,'-B',str(HERE/'production.py'),'spatial',scope,str(out)],check=True,cwd=RUN)
            cpu('finish',scope,out,1800)
            report=read(out/'package.stage.json')
            require(report['video_records']==(8 if scope=='nontest' else 426) and report['issues']==[],'strict source denominator failed')
            if scope=='nontest':checkpoint('PASS_NONTEST8_COMPLETE_NEW_CONTRACT',evidence_sha256=sha(out/'package.stage.json'))
        candidate=HERE/'rematch_01/candidate_Z_8B.zip'
        result=checkpoint('PASS_COMPLETE_426_Z8B_READY_FOR_DELIVERY',candidate=str(candidate),candidate_sha256=sha(candidate),
            candidate_bytes=candidate.stat().st_size,videos=426,official_score=None,new_T_training_started=False)
    except Exception as exc:
        result=checkpoint('STOP_NEXT8B_V1',failure_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
    write(HERE/'completion.json',result)
    return 0 if result['stage'].startswith('PASS_COMPLETE_426') else 1

if __name__=='__main__':raise SystemExit(main())
