"""Finite accepted input -> two-role shared GPU -> first QA, then main review."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback
from generate_formal41 import read, bound, ref, save, W, RUN, require


def snapshot():
    memory = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    return dict(host=os.uname().nodename,load=os.getloadavg(),disk_free=shutil.disk_usage(W).free,
        mem_available=int(memory['MemAvailable'].split()[0])*1024,
        gpu_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip(),
        gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True).strip())


def cpu(reg, path, name, code):
    root = Path(reg['root']); current = snapshot()
    require(current['disk_free'] > reg['stage_output_estimates'][name] and
            current['mem_available'] > reg['stage_RAM_estimates'][name], 'Actual declared output/working set fit')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')), 'Original final boundary')
    save(root/(name+'_resource41.json'),current)
    with (root/(name+'41.log')).open('xb') as stream:
        result = subprocess.run([reg['python'],'-B',str(bound(reg['code'][code])),'--registration',str(path)],
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    save(root/(name+'_terminal41.json'),dict(exit_code=result.returncode,automatic_retry=False,utc=datetime.now(timezone.utc).isoformat()))
    require(result.returncode == 0, name+' failed; preserve successes, no automatic repeat')


def run(path):
    reg=read(path);root=Path(reg['root']);require(reg['schema']=='FIVE_SUMMARY_SPRINT_V41','Explicit sprint schema')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')==str(reg['gpu_index']) and os.uname().nodename=='inspur-NP5570M5','Actual CUDA parent/host')
    for name,reference in reg['code'].items():require(bound(reference)==Path(__file__).resolve().parent/name,'All frozen source code')
    current=snapshot();require(not current['gpu_apps'],'Protect external GPU jobs')
    save(root/'formal_chain_claim41.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        argv=Path('/proc/self/cmdline').read_bytes().replace(b'\0',b' ').decode(),registration_ref=ref(path),resources=current))
    cpu(reg,path,'first_inputs','prepare_formal41.py')
    gatepath=root/'formal_inputs_41/input_acceptance.json';gate=read(gatepath)
    require(gate['status']=='PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS_41' and gate['sources']==426 and gate['windows']==522,'All522 first actual CPU acceptance')
    generated=dict(reg,first_input_acceptance_ref=ref(gatepath),input_phase_registration_ref=ref(path),input_prepared_ref=gate['prepared_ref'])
    generation_path=root/'generation_registration41.json';save(generation_path,generated)
    require(datetime.now(timezone.utc)<datetime.fromisoformat(reg['model_start_cutoff_utc'].replace('Z','+00:00')),'No new formal model past original cutoff')
    current=snapshot();require(not current['gpu_apps'],'Protect external GPU work before unique wrapper')
    require(current['disk_free']>reg['stage_output_estimates']['generation'] and current['mem_available']>reg['stage_RAM_estimates']['generation'],'Actual generation fits')
    resource=RUN/'controller'/(reg['job_name']+'.resource.json'); ledgerpath=W/'improvement_round1/gpu_ledger.jsonl'
    prior=[json.loads(x) for x in ledgerpath.read_text().splitlines() if x.strip() and json.loads(x).get('name')==reg['job_name']]
    require(not resource.exists() and not prior,'Only one new shared GPU wrapper')
    command=[reg['python'],str(bound(reg['gpu_wrapper_ref'])),'--name',reg['job_name'],'--max-seconds',str(reg['max_gpu_seconds']),
        '--planned-output-bytes',str(reg['stage_output_estimates']['generation']),'--capacity-reason',
        'First admitted frozen originalTIME522+BASE522 after every first input QA; shared BASE, no training/media/teacher. '+json.dumps(current),
        '--queue-seconds','60','--',reg['python'],'-B',str(bound(reg['code']['generate_formal41.py'])),'--registration',str(generation_path)]
    save(root/'formal_gpu_launch41.json',dict(command=command,resources=current,registration_ref=ref(generation_path),input_acceptance_ref=ref(gatepath),utc=datetime.now(timezone.utc).isoformat()))
    with (root/'formal_gpu_wrapper41.log').open('xb') as stream:
        result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
    require(result.returncode==0,'Formal shared GPU failed; preserve all raw and successful calls, no retry')
    terminal=read(resource);ledger=[json.loads(x) for x in ledgerpath.read_text().splitlines() if x.strip() and json.loads(x).get('name')==reg['job_name']]
    require(terminal['status']=='completed' and terminal['exit_code']==0 and ledger==[terminal],'Unique natural terminal/ledger')
    cpu(generated,generation_path,'first_output_QA','qa_outputs41.py')
    qapath=root/'first_independent_output_QA41.json';qa=read(qapath)
    require(qa['status']=='PASS_BOTH_ROLES_FIRST_INDEPENDENT_TOKEN_GRAMMAR_NATIVE_QA_41','All1044 first output QA')
    save(root/'formal_chain_completion41.json',dict(status='BOTH_FORMAL_ROLES_FIRST_QA_COMPLETE_PACKAGE_MAIN_REVIEW_PENDING',
        output_QA_ref=ref(qapath),resource_ref=ref(resource),unique_ledger_equal=True,actual_outputs=1044,
        roles={k:{a:v[a] for a in ('valid_empty_windows','raw_selected_native_frames','empty_source_ids','all_sources_empty')} for k,v in qa['roles'].items()},
        package_started=False,website_submitted=False,utc=datetime.now(timezone.utc).isoformat()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--registration',required=True);path=Path(p.parse_args().registration)
    try:run(path)
    except BaseException as error:
        root=path.parent
        if not (root/'formal_chain_failure41.json').exists():
            save(root/'formal_chain_failure41.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_raw_and_success=True,
                automatic_retry=False,failure_to_empty=False,utc=datetime.now(timezone.utc).isoformat()))
        raise
