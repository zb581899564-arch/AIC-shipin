"""Single development role-ablation chain; no fresh acquisition or production."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback

import role_runtime as rt


def child(state,name,argv,allowed=(0,)):
    with (state/(name+'.log')).open('xb') as stream:
        result=subprocess.run(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdout=stream,stderr=subprocess.STDOUT)
    rt.require(result.returncode in allowed,'Actual remaining role stage failed: '+name)
    return result.returncode


def main(root):
    reg,protocol,helpers=rt.registration(root);io=helpers[0];io.host(cpu=False)
    rt.require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Only CPU children mask their own CUDA')
    state=root/'chain_01';state.mkdir(exist_ok=False)
    io.save(state/'started.json',dict(pid=os.getpid(),utc=io.utc(),registration_ref=io.ref(root/'registration.json'),
        parent_CUDA='0',new_media_or_prepare_or_input_QA=False,production_admitted=False))
    code=Path(__file__).parent/'role_runtime.py';stage='ADOPT_COMPLETE_SAME_INPUT_FIRST_QA'
    try:
        child(state,'admit',[sys.executable,'-B','-u',str(code),'admit','--root',str(root)])
        gate=io.read(root/'gpu_admission.json');legacy=io.legacy(load_old_registration(reg));legacy.deadline(gate)
        stage='UNIQUE_TEN_BASE_ONLY_ADMISSION_CALLS'
        from shutil import disk_usage
        resources=[]
        for cmd in [['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],
                    ['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],
                    ['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits']]:
            result=subprocess.run(cmd,capture_output=True,text=True);rt.require(result.returncode==0,'Read-only shared resource observation failed')
            resources.append(dict(argv=cmd,stdout=result.stdout,stderr=result.stderr))
        io.save(state/'resources_before_GPU.json',dict(utc=io.utc(),resources=resources,memory=Path('/proc/meminfo').read_text(),
            disk=list(disk_usage(root)),no_fixed_utilization_gate=True))
        rt.require(not (io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json')).exists(),'Unique role GPU already has terminal')
        argv=[sys.executable,'-B',str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',gate['gpu_job_name'],
            '--max-seconds',str(gate['max_seconds']),'--planned-output-bytes',str(16<<20),'--capacity-reason',
            '10 paired BASE-only admission calls; exact prior successful inputs/first QA adopted; no new encode/media; retain raw and output QA.',
            '--queue-seconds','1800','--',sys.executable,'-B','-u',str(code),'infer','--root',str(root)]
        io.save(state/'GPU_launch.json',dict(utc=io.utc(),argv=argv,admission_ref=io.ref(root/'gpu_admission.json')))
        with (state/'GPU.log').open('xb') as stream:result=subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT)
        rt.require(result.returncode==0,'Unique role job failure; never implicit retry');resource,sha=io.terminal(gate)
        stage='FIRST_OUTPUT_ONLY_QA'
        child(state,'output_QA',[sys.executable,'-B','-u',str(code),'qa','--root',str(root)])
        stage='FIXED_DEV_EIGHT_GATES'
        result=child(state,'comparison',[sys.executable,'-B','-u',str(code),'evaluate','--root',str(root)],allowed=(0,5))
        comparison=io.read(root/'comparison_01/result.json')
        expected='PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM' if result==0 else 'STOP_ADAPTER_ROLE_DEV_REJECTED'
        rt.require(comparison['status']==expected and (result==0)==all(comparison['conditions'].values()),'Fixed scientific result/exit mismatch')
        io.save(state/'completion.json',dict(status=expected,utc=io.utc(),comparison_ref=io.ref(root/'comparison_01/result.json'),
            resource_terminal_sha256=sha,actual_new_calls=10,first_input_QA_adopted=10,new_input_encoder_calls=0,
            no_new_fresh_or_fixed40_426_or_package=True,production_admitted=False))
    except BaseException as error:
        io.save(state/'failure.json',dict(stage=stage,error=repr(error),traceback=traceback.format_exc(),
            preserve_all_success=True,no_automatic_retry=True,no_UNKNOWN_or_EMPTY_fallback=True));raise


def load_old_registration(reg):
    return rt.load(Path(reg['prior_root'])/'registration.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();main(args.root.resolve())
