"""Unbound read-only inspector. Never imports production or calls models."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ENTRY='context_advisory_v1'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text()) if Path(p).is_file() else None


def command(args):
    result=subprocess.run(args, capture_output=True,text=True,timeout=15)
    return {'exit':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()}


def capture():
    assert socket.gethostname()=='inspur-NP5570M5'
    here=ROOT/ENTRY
    allproc={}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            stat=(p/'stat').read_text(); tail=stat[stat.rfind(')')+2:].split()
            argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace').strip()
            allproc[int(p.name)]={'pid':int(p.name),'ppid':int(tail[1]),'pgid':int(tail[2]),'state':tail[0], 'full_command':argv}
        except (OSError,ValueError):pass
    owned={pid for pid,row in allproc.items() if str(here) in row['full_command'] and '.py' in row['full_command']}
    while True:
        more={pid for pid,row in allproc.items() if row['ppid'] in owned}
        if more<=owned:break
        owned|=more
    processes=[]
    for pid in sorted(owned):
        row=allproc[pid]; p=Path('/proc')/str(pid)
        try:row['io']=(p/'io').read_text()
        except OSError:row['io']=None
        try:row['open_files']=[os.readlink(f) for f in (p/'fd').iterdir()][:24]
        except OSError:row['open_files']=[]
        processes.append(row)
    artifacts={str(p.relative_to(here)):{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
        for p in here.rglob('*') if p.is_file() and 'prelock_repairs' not in p.parts and '__pycache__' not in p.parts}
    stages={};stage_read_utc={}
    names=['progress.json','completion.json','execution_failure.json','scientific_stop.json','registration.json','start.json',
        'prepared.json','preflight.json','cpu_build_acceptance.json','fallback_s_inventory.json','fallback_b_diagnostic_handoff.json',
        'nontest_01/progress.json','nontest_01/nontest.completion.json','nontest_01/nontest.report.json','nontest_01/package.stage.json',
        'nontest_01/independent_validation.json','developer_01/progress.json','developer_01/pilot.completion.json','developer_01/full.completion.json',
        'developer_01/pilot.report.json','developer_01/full.report.json','rematch_01/progress.json','rematch_01/rematch.completion.json',
        'rematch_01/package.stage.json','rematch_01/independent_validation.json','final_acceptance.json',
        'nontest_01/nontest.model.json','developer_01/pilot.model.json','developer_01/full.model.json',
        'rematch_01/rematch.model.json']
    for name in names:
        if (here/name).is_file():
            stages[name]=read(here/name)
            stage_read_utc[name]=dt.datetime.now(dt.timezone.utc).isoformat()
    model_receipts={name:{'sha256':sha(here/name),'model_identity':value,
        'read_utc':stage_read_utc[name]} for name,value in stages.items() if name.endswith('.model.json')}
    model_identities=[r['model_identity'] for r in model_receipts.values()]
    done=[];failures=[]
    for p in here.rglob('done.json'):
        row=read(p); bindings=row.get('bound_files',{})
        done.append({'path':str(p),'sha256':sha(p),'output_valid':row.get('output_valid'),
            'kind':'overview' if 'overview' in p.parts else 'local', 'arm':row.get('arm'),
            'status':row.get('status'), 'events_count':len(row.get('events',{}).get('events',[])) if 'overview' in p.parts else None,
            'bound_files_SHA_pass':all(Path(k).is_file() and sha(k)==v for k,v in bindings.items()),
            'model_identity_matches_actual_receipt':bool(model_identities) and all(row.get('model_identity')==m for m in model_identities),
            'request_sha256':row.get('request_sha256'),'input_tokens':row.get('input_tokens'),
            'output_tokens':row.get('output_tokens'),'generation_seconds':row.get('generation_seconds')})
    for p in here.rglob('*.failure.json'):failures.append({'path':str(p),'sha256':sha(p),'failure':read(p)})
    resources={name:{'resource':read(ROOT/'controller'/('aic_CAD_v1_'+name+'.resource.json')),
        'queue':read(ROOT/'controller'/('aic_CAD_v1_'+name+'.queue.json'))} for name in ('nontest','pilot','full','rematch')}
    ledger=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    lines=[json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
    active=read(ledger.parent/'active_gpu_job.json')
    lock=read(here/'source_lock.json')
    space=os.statvfs(here)
    snapshot={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'host':socket.gethostname(),'entry':ENTRY,
        'source_lock_sha256':sha(here/'source_lock.json') if lock else None,'frozen_files':len(lock['files']) if lock else 0,
        'processes':processes,'process_sample_is_not_persistent_identity':True,'artifacts':artifacts,'stages':stages,
        'stage_read_utc':stage_read_utc,'model_receipts':model_receipts,
        'all_done_model_identity_matches_actual_receipts':all(x['model_identity_matches_actual_receipt'] for x in done),
        'done_count':len(done),'done':done,
        'done_by_kind':{kind:sum(x['kind']==kind for x in done) for kind in ('overview','local')},
        'local_done_by_arm':{arm:sum(x['arm']==arm for x in done) for arm in ('B1','B0','N','R','X')},
        'all_done_bound_SHA_pass':all(x['bound_files_SHA_pass'] and x['output_valid'] for x in done),
        'failures':failures,'resources':resources,'active_gpu_job':active,
        'GPU_ledger':{'lines':len(lines),'sha256':sha(ledger),'historical_offset':7200,
            'owned_rows':[x for x in lines if x.get('name','').startswith('aic_CAD_v1_')]},
        'gpu':command(['nvidia-smi','--query-gpu=index,name,utilization.gpu,memory.used,memory.total','--format=csv,noheader']),
        'gpu_compute':command(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader']),
        'cpu_RAM':command(['free','-b']),'cpu_load':Path('/proc/loadavg').read_text().strip(),
        'disk_available_bytes':space.f_bavail*space.f_frsize,'new_training_updates':0,'official_score':None,
        'sequential_component_snapshot_not_atomic':True}
    return snapshot


if __name__=='__main__':print(json.dumps(capture(),ensure_ascii=False))
