"""One bounded first BASE43 job and first CPU review; no automatic production."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback
from summary_generate import read, ref, bound, save, RUN, W
from summary_contract import require


def run(path):
    reg = read(path); root = Path(reg['root'])
    require(reg['schema'] == 'FIVE_SUMMARY_BASE_PILOT_V41' and os.uname().nodename == 'inspur-NP5570M5', 'New exact schema/host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == str(reg['gpu_index']), 'Parent actual CUDA index')
    for name, reference in reg['code'].items():
        require(bound(reference) == Path(__file__).resolve().parent/name, 'All frozen pilot code')
    apps = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
    mem = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    snapshot = dict(host=os.uname().nodename, gpu_apps=apps, disk_free=shutil.disk_usage(W).free,
        mem_available=int(mem['MemAvailable'].split()[0])*1024, load=os.getloadavg())
    require(not apps and snapshot['disk_free'] > reg['planned_output_bytes'] and
            snapshot['mem_available'] > reg['planned_ram_bytes'], 'Live no-conflict and actual working/output fit')
    save(root/'pilot_chain_claim41.json',dict(pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        argv=Path('/proc/self/cmdline').read_bytes().replace(b'\0',b' ').decode(),resources=snapshot,registration_ref=ref(path)))
    job = reg['job_name']; resource = RUN/'controller'/(job+'.resource.json')
    ledger_path = W/'improvement_round1/gpu_ledger.jsonl'
    old = [json.loads(x) for x in ledger_path.read_text().splitlines() if x.strip() and json.loads(x).get('name') == job]
    require(not resource.exists() and not old, 'Unique new named wrapper only')
    command = [reg['python'],str(bound(reg['gpu_wrapper_ref'])),'--name',job,'--max-seconds',str(reg['max_gpu_seconds']),
        '--planned-output-bytes',str(reg['planned_output_bytes']),'--capacity-reason',
        'First BASE43 same accepted external dual-view inputs; shared frozen BASE+disabled originalTIME, no labels/training/media. '+json.dumps(snapshot),
        '--queue-seconds','60','--',reg['python'],'-B',str(bound(reg['code']['base_pilot41.py'])),'--registration',str(path)]
    save(root/'pilot_gpu_launch41.json',dict(command=command,resources=snapshot,utc=datetime.now(timezone.utc).isoformat()))
    with (root/'pilot_gpu_wrapper41.log').open('xb') as stream:
        result = subprocess.run(command,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
    require(result.returncode == 0, 'BASE pilot wrapper failed; preserve all successes and raw, no automatic retry')
    terminal = read(resource)
    ledger = [json.loads(x) for x in ledger_path.read_text().splitlines() if x.strip() and json.loads(x).get('name') == job]
    require(terminal['status'] == 'completed' and terminal['exit_code'] == 0 and ledger == [terminal], 'Natural unique GPU terminal')
    with (root/'pilot_first_review41.log').open('xb') as stream:
        review = subprocess.run([reg['python'],'-B',str(bound(reg['code']['review_pilot41.py'])),'--registration',str(path)],
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    require(review.returncode == 0, 'First output QA/evaluation failed, no automatic replay')
    comparison = read(root/'pilot_comparison41.json')
    save(root/'pilot_chain_completion41.json',dict(status='BASE43_FIRST_QA_COMPARISON_COMPLETE_MAIN_REVIEW_REQUIRED',
        comparison_ref=ref(root/'pilot_comparison41.json'),resource_ref=ref(resource),unique_ledger_equal=True,
        broad_collapse_check_pass=comparison['broad_collapse_check_pass'],macro=comparison['macro'],production_allowed=False,
        new_fit=0,optimizer_updates=0,actual_new_BASE_calls=43,adopted_TIME_calls=43,automatic_formal=False,
        utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--registration',required=True); path = Path(p.parse_args().registration)
    try: run(path)
    except BaseException as error:
        root = path.parent
        if not (root/'pilot_chain_failure41.json').exists():
            save(root/'pilot_chain_failure41.json',dict(error=repr(error),traceback=traceback.format_exc(),
                preserve_raw_and_success=True,automatic_retry=False,utc=datetime.now(timezone.utc).isoformat()))
        raise
