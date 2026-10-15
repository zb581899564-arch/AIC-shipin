"""Conditional B0-only fixed40 chain; never registers or starts a later layer."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback

import facts_common as io
from registration import registration, ref


def child(state,name,argv):
    io.save(state/(name+'_launch.json'),dict(argv=argv,utc=io.utc(),CPU_child_only_CUDA_hidden=True))
    with (state/(name+'.log')).open('xb') as log:
        result=subprocess.run(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdout=log,stderr=subprocess.STDOUT)
    io.require(result.returncode==0,'Actual fixed40 stage failed; preserve successes and stop without fallback: '+name)


def main(root):
    io.host(cpu=False);io.require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Parent explicit CUDA0 required')
    root=io.root_path(root);reg=registration(root);state=root/'chain_01';state.mkdir(exist_ok=False)
    io.save(state/'started.json',dict(pid=os.getpid(),utc=io.utc(),registration_ref=ref(root/'role_fixed40_registration.json'),
        parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],B0_only=True,production_admitted=False))
    code=Path(__file__).parent;stage='PRIMARY'
    try:
        child(state,'prepare',[sys.executable,'-B','-u',str(code/'input_stages.py'),'prepare','--root',str(root)])
        stage='FIRST_ALL_INPUT_QA_PRE_GPU';child(state,'first_input_QA',[sys.executable,'-B','-u',str(code/'input_stages.py'),'first_qa','--root',str(root)])
        count=reg['gpu_budget']['max_actual_calls']
        if count:
            stage='B0_GPU_ADMISSION';budget=reg['gpu_budget'];io.require(not (io.RUN/'controller'/(budget['gpu_job_name']+'.resource.json')).exists(),'Unique new job already has terminal; no rerun')
            gate=dict(status='PASS_ROLE_FIXED40_B0_GPU_ADMISSION',stage='B0',group='facts',registration_ref=ref(root/'role_fixed40_registration.json'),
                cpu_ref=ref(root/'cpu_acceptance.json'),source_lock_ref=ref(root/'source_lock_B0.json'),expected_input_count=count,
                gpu_job_name=budget['gpu_job_name'],max_seconds=budget['max_seconds'],deadline=reg['deadline'])
            gate_path=root/'gpu_admission_B0.json';io.save(gate_path,gate)
            io.accepted_b0(root,'facts');io.deadline(gate)
            from native import resource_snapshot
            observations=[]
            for command in (['ps','-eo','pid,ppid,stat,args'],['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],
                ['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits']):
                value=subprocess.run(command,capture_output=True,text=True);io.require(value.returncode==0,'Actual shared-resource observation failed')
                observations.append(dict(argv=command,stdout=value.stdout,stderr=value.stderr))
            io.save(state/'resources_before_GPU.json',dict(snapshot=resource_snapshot(root),observations=observations,fixed_resource_threshold_applied=False))
            stage='UNIQUE_B0_GPU'
            argv=[sys.executable,'-B',str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',budget['gpu_job_name'],
                '--max-seconds',str(budget['max_seconds']),'--planned-output-bytes',str(32<<20),'--capacity-reason',
                str(count)+' registered missing fixed40 B0 inputs; all new first input QA completed; output/raw QA only.',
                '--queue-seconds','1800','--',sys.executable,'-B','-u',str(code/'b0_runtime.py'),'infer','--root',str(root),'--group','facts']
            io.save(state/'GPU_launch.json',dict(argv=argv,utc=io.utc(),admission_ref=ref(gate_path)))
            with (state/'GPU.log').open('xb') as log:result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
            io.require(result.returncode==0,'Unique actual shared GPU wrapper failed; no retry');io.terminal(gate)
            stage='FIRST_B0_OUTPUT_ONLY_QA';child(state,'output_QA',[sys.executable,'-B','-u',str(code/'b0_runtime.py'),'replay','--root',str(root),'--group','facts'])
        stage='COMPLETE_P_UPPER_BOUND';child(state,'fact_check',[sys.executable,'-B','-u',str(code/'fact_check.py'),'--root',str(root)])
        result=io.read(root/'result.json');io.require(result['status'] in ('B0_UPPER_BOUND_SUFFICIENT','INCONCLUSIVE_PENDING_REGISTERED_VERIFY'),'Explicit sufficient/inconclusive first-layer state required')
        io.save(state/'completion.json',dict(status=result['status'],result_ref=ref(root/'result.json'),B0_only=True,
            next_level_started=False,production_admitted=False,complete_positive_recipe_executed=False))
    except BaseException as error:
        io.save(state/'failure.json',dict(stage=stage,error=repr(error),traceback=traceback.format_exc(),
            preserve_all_raw_and_success=True,no_automatic_retry=True,no_UNKNOWN_or_EMPTY_fallback=True,next_level_started=False));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);args=parser.parse_args();main(args.root)
