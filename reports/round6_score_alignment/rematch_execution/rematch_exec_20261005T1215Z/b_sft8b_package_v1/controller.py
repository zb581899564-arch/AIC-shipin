"""Single registered continuation: fixed dev -> non-test -> rematch -> strict package."""
from runtime import *
import datetime as dt
import os
import subprocess
import time
import traceback
import shutil

def checkpoint(stage,**extra):
    value=dict(stage=stage,utc=dt.datetime.now(dt.timezone.utc).isoformat(),pid=os.getpid(),uploaded=False,**extra)
    temp=HERE/'latest.tmp';temp.write_text(json.dumps(value,indent=2));temp.replace(HERE/'latest.json')
    print(json.dumps(value),flush=True);return value

def capacity(planned):
    deadline=time.monotonic()+600
    while True:
        if (HERE/'mac_capacity_latest.json').exists():
            mac=read(HERE/'mac_capacity_latest.json')
            age=time.time()-dt.datetime.fromisoformat(mac['utc'].replace('Z','+00:00')).timestamp()
            if mac.get('status')=='PASS_LIVE_MAC_ROOT' and 0<=age<=300:break
        checkpoint('WAITING_FRESH_MAC_CAPACITY')
        require(time.monotonic()<deadline,'live Mac capacity evidence unavailable; no bypass')
        time.sleep(15)
    linux=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    remaining_mac=1100000000
    projected=linux+mac['work_bytes']+remaining_mac+planned
    require(projected<=80*2**30 and shutil.disk_usage(ROOT).free>=planned,'combined dynamic capacity insufficient')
    return dict(linux_work_bytes=linux,mac=mac,remaining_mac_full_bytes=remaining_mac,planned_output_bytes=planned,combined_peak_bytes=projected)

def run_gpu(stage,scope,out,maximum,planned):
    verify()
    evidence=capacity(planned)
    name='rematch_B8B_'+scope+'_'+stage+'_01'
    write(HERE/(name+'.admission.json'),dict(authorized=True,user_request='生成一下包中',stage=stage,scope=scope,
        output=str(out),source_lock_sha256=sha(HERE/'source_lock.json'),dev_decision_sha256=sha(RUN/'temporal_sft8b_dev_v1/decision.json'),
        dynamic_capacity=evidence,max_seconds=maximum,planned_output_bytes=planned,uploaded=False))
    command=[sys.executable,'-B',str(RUN/'controller/gpu_run.py'),'--name',name,'--max-seconds',str(maximum),
        '--planned-output-bytes',str(planned),'--capacity-reason','Combined live Linux/Mac roots plus registered remaining Mac full and bounded phase outputs',
        '--queue-seconds','1800','--',sys.executable,'-B',str(HERE/'runtime.py'),stage,scope,str(out)]
    checkpoint('RUNNING_'+scope.upper()+'_'+stage.upper(),job=name,capacity=evidence)
    with (HERE/(name+'.wrapper.log')).open('x') as f:
        result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=RUN)
    resource=read(RUN/'controller'/(name+'.resource.json')) if (RUN/'controller'/(name+'.resource.json')).exists() else {}
    require(result.returncode==0 and resource.get('status')=='completed' and resource.get('exit_code')==0 and resource.get('stop_reason') is None,'GPU phase failed: '+name)

def run_cpu(stage,scope,out,timeout):
    checkpoint('RUNNING_'+scope.upper()+'_'+stage.upper())
    with (HERE/(scope+'_'+stage+'.log')).open('x') as f:
        p=subprocess.run([sys.executable,'-B',str(HERE/'production.py'),stage,scope,str(out)],
            stdout=f,stderr=subprocess.STDOUT,cwd=RUN,timeout=timeout)
    require(p.returncode==0,'CPU phase failed: '+scope+' '+stage)

def main():
    write(HERE/'continuation_registration.json',dict(pid=os.getpid(),utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        source_lock_sha256=sha(HERE/'source_lock.json')))
    result=None
    try:
        verify();checkpoint('WAITING_REGISTERED_FIXED_DEV')
        deadline=time.monotonic()+14400+2100
        dev_resource=RUN/'controller/rematch_sft8b_dev_01.resource.json'
        while not dev_resource.exists():
            require(time.monotonic()<deadline,'fixed dev resource receipt missing')
            time.sleep(15)
        decision=read(RUN/'temporal_sft8b_dev_v1/decision.json')
        require(decision['status']=='PASS_FROZEN_WEAK_DEV_GATE','frozen dev gate STOP; no test inference')
        require(read(dev_resource)['status']=='completed','fixed dev resource failed')
        checkpoint('PASS_FIXED_DEV_GATE',weak_metrics=decision['comparisons'],paired=decision['paired'])
        nontest=HERE/'nontest_01';nontest.mkdir()
        run_gpu('temporal','nontest',nontest,3600,30000000)
        run_cpu('scheduling','nontest',nontest,1800)
        run_gpu('spatial','nontest',nontest,3600,50000000)
        run_cpu('finish','nontest',nontest,600)
        require(read(nontest/'package.stage.json')['video_records']==8,'NONTEST8 denominator changed')
        checkpoint('PASS_NONTEST8_COMPLETE_8B_ENGINEERING',evidence_sha256=sha(nontest/'package.stage.json'))
        rematch=HERE/'rematch_01';rematch.mkdir()
        # Fixed 426/521 production time stage; only engineering grammar and pinned adapter change.
        run_gpu('temporal','rematch',rematch,14400,100000000)
        run_cpu('scheduling','rematch',rematch,7200)
        schedule=read(rematch/'schedule.stage.json');measure=read(nontest/'spatial.stage.json')
        anchors=schedule['anchors'];frames=schedule['selected_frames']
        maximum=max(3600,int(anchors*measure['measured_seconds_per_anchor']*2+1200))
        planned=frames*2500+anchors*6000+20000000
        # Real counts and measured same-model non-test cost, no 4B speed assumption.
        write(HERE/'rematch_spatial_cost_registration.json',dict(anchors=anchors,selected_frames=frames,
            measured_8b_seconds_per_anchor=measure['measured_seconds_per_anchor'],max_seconds=maximum,
            planned_output_bytes=planned,non_test_evidence_sha256=sha(nontest/'spatial.stage.json')))
        run_gpu('spatial','rematch',rematch,maximum,planned)
        run_cpu('finish','rematch',rematch,1800)
        package=read(rematch/'package.stage.json');candidate=rematch/'candidate_B_8B.zip'
        require(package['video_records']==426 and package['issues']==[] and sha(candidate)==package['zip_sha256'], 'complete426 candidate identity failed')
        result=checkpoint('PASS_COMPLETE_426_8B_PACKAGE_READY_FOR_DELIVERY',candidate=str(candidate),
            candidate_sha256=sha(candidate),candidate_bytes=candidate.stat().st_size,
            selected_frames=frames,anchors=anchors,videos=426,package_evidence_sha256=sha(rematch/'package.stage.json'))
    except Exception as exc:
        result=checkpoint('STOP_B8B_PACKAGE_CONTINUATION',failure_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
    write(HERE/'completion.json',result)
    return 0 if result['stage'].startswith('PASS_COMPLETE_426') else 1

if __name__=='__main__':raise SystemExit(main())
