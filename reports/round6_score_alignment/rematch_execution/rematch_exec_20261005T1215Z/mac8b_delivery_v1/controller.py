"""Once-only Mac adapter GPU probe, fixed dev, NONTEST8, and complete submission."""
from runtime import *
import datetime as dt
import os
import shutil
import subprocess
import traceback

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
            if mac.get('status')=='PASS_LIVE_MAC_ROOT' and 0<=age<=300: break
        checkpoint('WAITING_FRESH_MAC_CAPACITY')
        require(time.monotonic()<deadline,'fresh Mac capacity unavailable; no bypass');time.sleep(15)
    linux=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    combined=linux+mac['work_bytes']+planned
    require(combined<=80*2**30 and shutil.disk_usage(ROOT).free>=planned,'combined dynamic occupancy insufficient')
    return dict(linux_work_bytes=linux,mac=mac,remaining_mac_training_bytes=0,planned_output_bytes=planned,combined_peak_bytes=combined)

def run_gpu(stage,scope,out,maximum,planned):
    verify();evidence=capacity(planned);name='rematch_MAC8B_v1_'+scope+'_'+stage+'_01'
    write(HERE/(name+'.admission.json'),dict(authorized=True,user_request='mac的开发测评和提交包尽早完成',stage=stage,scope=scope,
        output=str(out),source_lock_sha256=sha(HERE/'source_lock.json'),dynamic_capacity=evidence,
        max_seconds=maximum,planned_output_bytes=planned,uploaded=False))
    child=[sys.executable,'-B',str(HERE/'dev/evaluate.py'),'evaluate'] if stage=='dev' else [sys.executable,'-B',str(HERE/'runtime.py'),stage,scope,str(out)]
    command=[sys.executable,'-B',str(RUN/'controller/gpu_run.py'),'--name',name,'--max-seconds',str(maximum),
        '--planned-output-bytes',str(planned),'--capacity-reason','Mac-final lowres route, live combined roots plus stage outputs',
        '--queue-seconds','1800','--',*child]
    checkpoint('RUNNING_'+scope.upper()+'_'+stage.upper(),job=name,capacity=evidence)
    with (HERE/(name+'.wrapper.log')).open('x') as log:
        result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=RUN)
    resource=read(RUN/'controller'/(name+'.resource.json'))
    require(result.returncode==0 and resource['status']=='completed' and resource['exit_code']==0 and resource['stop_reason'] is None,'GPU gate failed: '+name)

def run_cpu(stage,scope,out):
    checkpoint('RUNNING_'+scope.upper()+'_'+stage.upper())
    with (HERE/(scope+'_'+stage+'.log')).open('x') as log:
        result=subprocess.run([sys.executable,'-B',str(HERE/'production.py'),stage,scope,str(out)],
            stdout=log,stderr=subprocess.STDOUT,cwd=RUN,timeout=7200 if stage=='scheduling' else 1800)
    require(result.returncode==0,'CPU phase failed: '+scope+' '+stage)

def main():
    write(HERE/'continuation_registration.json',dict(pid=os.getpid(),utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_lock_sha256=sha(HERE/'source_lock.json')))
    try:
        verify()
        run_gpu('long_probe','nontest',HERE/'long_probe_01',3600,30000000)
        run_gpu('dev','dev',HERE/'dev',14400,100000000)
        decision=read(HERE/'dev/decision.json');require(decision['status']=='PASS_FROZEN_WEAK_DEV_GATE','fixed Mac dev STOP')
        checkpoint('PASS_MAC_FIXED_DEV_GATE',comparisons=decision['comparisons'],paired=decision['paired'])
        nontest=HERE/'nontest_01';nontest.mkdir()
        run_gpu('temporal','nontest',nontest,3600,30000000)
        run_cpu('scheduling','nontest',nontest)
        run_gpu('spatial','nontest',nontest,3600,30000000)
        run_cpu('finish','nontest',nontest)
        require(read(nontest/'package.stage.json')['video_records']==8,'NONTEST8 incomplete')
        checkpoint('PASS_MAC_NONTEST8_COMPLETE_ENGINEERING',evidence_sha256=sha(nontest/'package.stage.json'))
        out=HERE/'rematch_01';out.mkdir()
        run_gpu('temporal','rematch',out,14400,100000000)
        temporal=read(out/'temporal.stage.json');require(temporal['videos']==426 and temporal['windows']==521 and temporal['invalid_windows']==0,'complete temporal denominator failed')
        run_cpu('scheduling','rematch',out)
        schedule=read(out/'schedule.stage.json');measure=read(nontest/'spatial.stage.json')
        frames=schedule['selected_frames'];anchors=schedule['anchors']
        maximum=max(3600,int(anchors*measure['measured_seconds_per_anchor']*2+1200))
        planned=frames*2500+anchors*6000+20000000
        write(HERE/'rematch_spatial_cost_registration.json',dict(anchors=anchors,selected_frames=frames,
            measured_8b_seconds_per_anchor=measure['measured_seconds_per_anchor'],max_seconds=maximum,
            planned_output_bytes=planned,non_test_evidence_sha256=sha(nontest/'spatial.stage.json')))
        run_gpu('spatial','rematch',out,maximum,planned)
        run_cpu('finish','rematch',out)
        package=read(out/'package.stage.json');candidate=out/'candidate_MAC_8B.zip'
        require(package['video_records']==426 and package['issues']==[] and sha(candidate)==package['zip_sha256'],'complete package failed')
        result=checkpoint('PASS_COMPLETE_426_8B_PACKAGE_READY_FOR_DELIVERY',candidate=str(candidate),candidate_sha256=sha(candidate),candidate_bytes=candidate.stat().st_size,
            selected_frames=frames,anchors=anchors,videos=426,package_evidence_sha256=sha(out/'package.stage.json'),trained_on='MAC_MPS',inference_on='LINUX_CUDA')
    except Exception as exc:
        result=checkpoint('STOP_MAC8B_DELIVERY',failure_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
    write(HERE/'completion.json',result)
    return 0 if result['stage'].startswith('PASS_COMPLETE_426') else 1

if __name__=='__main__': raise SystemExit(main())
