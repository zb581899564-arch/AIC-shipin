"""A single registered external group: CPU gates, two GPU jobs, QA, proxy.

Never starts production, replaces a failed stage, changes rules, or publishes.
Confirmation is a separate first launch after the frozen development pass.
"""
import argparse
import datetime as dt
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import model_common as io


def snapshot(root):
    return dict(utc=io.utc(),host=__import__('socket').gethostname(),cpu_count=os.cpu_count(),
        load=list(os.getloadavg()),memory=Path('/proc/meminfo').read_text(),disk=list(shutil.disk_usage(root)),
        active_processes=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,pmem,rss,comm','--sort=-pcpu'],
            capture_output=True,text=True,check=True).stdout.splitlines()[:18],
        gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout)


def child(root,state,name,args,cpu=True):
    argv=[sys.executable,'-B','-u',str(root/'code'/name),*args]
    env=dict(os.environ)
    if cpu:env['CUDA_VISIBLE_DEVICES']=''
    path=state/(name+'.'+args[0]+'.log')
    with path.open('xb') as log:
        result=subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
    io.require(result.returncode==0,'Real child failed, preserve its output and successful work: '+name)


def verify_lock(root,group):
    cpu_path=root/group/'VERIFY/cpu_01/completion.json';cpu=io.read(cpu_path)
    files=dict(io.read(root/('source_lock_'+group+'_B0.json'))['files'])
    def add(path,digest=None):
        p=io.checked(path,digest);actual=io.sha(p)
        io.require(str(p) not in files or files[str(p)]==actual,'Previously frozen evidence changed')
        files[str(p)]=actual
    add(cpu_path);add(cpu['requests_path'],cpu['requests_sha256'])
    for prefix in ['b0_cpu_acceptance','b0_source_lock','b0_admission','b0_gpu_completion','b0_replay_completion']:
        add(cpu['bindings'][prefix+'_path'],cpu['bindings'][prefix+'_sha256'])
    for entry in cpu['entries']:
        add(entry['input_path'],entry['input_sha256']);add(entry['proof_path'],entry['proof_sha256'])
        proof=io.read(entry['proof_path']);request=io.read(entry['input_path'])
        for prefix in ['token_cache','original_vision_cache']:add(proof[prefix+'_path'],proof[prefix+'_sha256'])
        for ref in request['original_evidence'].values():add(ref['path'],ref['sha256'])
    for path,digest in io.code_files().items():add(path,digest)
    io.save(root/('source_lock_'+group+'_VERIFY.json'),dict(files=files,group=group,stage='VERIFY',utc=io.utc()))
    return cpu_path


def admit(root,state,group,stage,protocol,deadline):
    cpu_path=root/('cpu_acceptance_'+group+'.json') if stage=='B0' else verify_lock(root,group)
    cpu=io.read(cpu_path);count=len(cpu['entries'])
    maximum=protocol['gpu_budget']['per_group_max_'+stage+'_actual_calls']
    io.require(0<count<=maximum,'Actual complete stage input budget exceeded or empty')
    lock_path=root/('source_lock_'+group+'_'+stage+'.json')
    io.validate_lock(lock_path,set(io.code_files())|io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG),str(cpu_path)})
    resource=snapshot(root);io.save(state/('resources_before_'+stage+'.json'),resource)
    # No fixed capacity percentage or GiB gate. gpu_run owns the shared lock,
    # rejects impossible actual capacity, and queues instead of stealing jobs.
    job='recall_verify40_46_small4_'+group+'_'+stage.lower()+'_20261014_v1'
    io.require(not (io.RUN/'controller'/(job+'.resource.json')).exists(),'Job already has a terminal; never repeat')
    gate=dict(status=io.ADMISSION_STATUS,group=group,stage=stage,expected_input_count=count,gpu_job_name=job,
        deadline=deadline,cpu_acceptance_path=str(cpu_path),cpu_acceptance_sha256=io.sha(cpu_path),
        source_lock_path=str(lock_path),source_lock_sha256=io.sha(lock_path),source_scope='EXTERNAL_NONTEST_ONLY',
        model_parameters=io.MODEL_PARAMETERS,optimizer_updates=0,reference_available_to_inference=False,
        protocol_sha256=io.sha(root/'protocol.json'),authorization_sha256=io.sha(root/'USER_AUTHORIZATION.json'))
    io.save(root/('gpu_admission_'+group+'_'+stage+'.json'),gate)
    return gate


def gpu(root,state,group,stage,gate,protocol):
    script='pilot_runtime.py' if stage=='B0' else 'pilot_verify.py'
    seconds=protocol['gpu_budget'][group+'_'+stage+'_max_seconds']
    command=[sys.executable,'-B',str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name',gate['gpu_job_name'],'--max-seconds',str(seconds),'--planned-output-bytes',str(32<<20),
        '--capacity-reason',str(gate['expected_input_count'])+' genuinely new external same-B calls; accepted CPU caches already exist; only raw tokens, grammar outputs and first replay proofs added.',
        '--queue-seconds','1800','--',sys.executable,'-B','-u',str(root/'code'/script),'infer','--root',str(root),'--group',group]
    io.save(state/('gpu_launch_'+stage+'.json'),dict(argv=command,utc=io.utc(),admission_sha256=io.sha(root/('gpu_admission_'+group+'_'+stage+'.json'))))
    with (state/('gpu_'+stage+'.log')).open('xb') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    io.require(result.returncode==0,'Actual unique GPU wrapper failed; no automatic rerun')
    io.terminal(gate)


def main(root,group):
    io.host(cpu=False)
    if group=='confirm':
        selected=io.read(root/'dev/selection_before_confirmation.json')
        io.require(selected['status']=='PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and
                   selected['protocol_sha256']==io.sha(root/'protocol.json'),'No frozen dev admission')
    state=root/group/'chain_01';state.mkdir(exist_ok=False)
    io.save(state/'started.json',dict(pid=os.getpid(),utc=io.utc(),parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],
        protocol_sha256=io.sha(root/'protocol.json'),controller_sha256=io.sha(__file__)))
    protocol=io.read(root/'protocol.json');deadline=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=4)).isoformat()
    current='CPU_PREPARATION'
    try:
        child(root,state,'prepare_inputs.py',['--root',str(root),'--group',group])
        current='INDEPENDENT_CPU_ADMISSION';child(root,state,'admit_inputs.py',['--root',str(root),'--group',group])
        current='B0';gate=admit(root,state,group,'B0',protocol,deadline);gpu(root,state,group,'B0',gate,protocol)
        current='B0_REPLAY';child(root,state,'pilot_runtime.py',['replay','--root',str(root),'--group',group])
        current='VERIFY_PREPARE';child(root,state,'pilot_verify.py',['prepare','--root',str(root),'--group',group])
        verify=io.read(root/group/'VERIFY/cpu_01/completion.json')
        if not verify['entries']:
            io.save(state/'completion.json',dict(status='STOP_LEGAL_EMPTY_NO_CANDIDATES_OR_NEW_RECALL',group=group,
                B0_calls=len(io.read(root/('cpu_acceptance_'+group+'.json'))['entries']),VERIFY_calls=0,production_admitted=False))
            return
        current='VERIFY';gate=admit(root,state,group,'VERIFY',protocol,deadline);gpu(root,state,group,'VERIFY',gate,protocol)
        current='VERIFY_REPLAY';child(root,state,'pilot_verify.py',['replay','--root',str(root),'--group',group])
        current='PROXY_EVALUATION'
        argv=[sys.executable,'-B',str(root/'code/evaluate_pilot.py'),'--root',str(root),'--group',group]
        with (state/'comparison.log').open('xb') as log:result=subprocess.run(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdout=log,stderr=subprocess.STDOUT)
        io.require(result.returncode in (0,5),'Actual proxy evaluation engineering failure')
        comparison=io.read(root/group/'comparison_01/result.json')
        io.save(state/'completion.json',dict(status='COMPLETE_EXTERNAL_GROUP_PROXY_PASS_PENDING_FIXED_FACTS' if result.returncode==0 else 'STOP_EXTERNAL_RECALL_PROXY_REJECTED',
            group=group,utc=io.utc(),comparison_sha256=io.sha(root/group/'comparison_01/result.json'),
            B0_calls=len(io.read(root/('cpu_acceptance_'+group+'.json'))['entries']),VERIFY_calls=len(verify['entries']),
            proxy_result=comparison['status'],production_admitted=False,no_426_model_or_package_started=True))
    except BaseException as error:
        io.save(state/'failure.json',dict(stage=current,error=repr(error),traceback=traceback.format_exc(),utc=io.utc(),
            preserve_all_success=True,do_not_repeat_successful_calls=True,production_admitted=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--group',choices=['dev','confirm'],required=True)
    args=parser.parse_args();main(args.root,args.group)
