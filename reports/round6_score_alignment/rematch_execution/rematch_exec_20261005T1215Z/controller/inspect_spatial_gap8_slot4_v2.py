"""Unbound, read-only Linux component snapshot. No model/decoder imports."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
HERE=RUN/'spatial_gap8_pchip_slot4_v2'

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as s:
        for b in iter(lambda:s.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())

def capture():
    assert socket.gethostname()=='inspur-NP5570M5'
    result=dict(utc=utc(),host=socket.gethostname(),route=HERE.name,non_atomic_component_reads=True)
    artifacts={}
    for p in HERE.rglob('*'):
        if p.is_file():
            s=p.stat();artifacts[str(p.relative_to(HERE))]=dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns)
    result['artifacts']=artifacts
    result['stages']={};result['stage_read_utc']={};result['component_sha256']={}
    names=['progress.json','source_lock.json','start.json','registration.json','preflight.json',
        'g0_asset_handoff.json','g0_native_processor.json','g0_new_field_contract.json','g0_exposure_review.json',
        'g0_runtime_consumer_cpu.json','g0_engineering_cpu.json','g0_admission.json','input_01/inventory_summary.json','input_01/seal_receipt.json',
        'input_01/cache_recipe_admission.json','diagnostic_01/model.json','diagnostic_01/first_real_acceptance.json',
        'diagnostic_01/engineering_completion.json','diagnostic_01/inference_completion.json','diagnostic_01/report.json',
        'nontest_01/package.stage.json','nontest_01/independent_validation.json',
        'rematch_01/package.stage.json','rematch_01/independent_validation.json','scientific_stop.json',
        'execution_failure.json','completion.json','final_acceptance.json']
    for name in names:
        p=HERE/name;result['stage_read_utc'][name]=utc()
        if not p.exists():result['stages'][name]=None;continue
        value=read(p);result['component_sha256'][name]=sha(p)
        if name=='source_lock.json':
            result['frozen_files']=len(value['files']);result['source_lock_sha256']=sha(p)
            value={k:v for k,v in value.items() if k not in ('files','quick_files')}
        for key in ['files','scopes','model_files','groups','requests','predictions','matched_rows','accepted',
                    'accepted_probe_caches','rejected_other_recipe_matches','all_matching_8B_authorities','input_tensors','prefix']:
            if key in value:
                x=value.pop(key);value[key+'_count']=len(x) if hasattr(x,'__len__') else None
        result['stages'][name]=value
    result.setdefault('frozen_files',0);result.setdefault('source_lock_sha256',None)
    done=list((HERE/'diagnostic_01/new').glob('*/done.json'))
    raw=list((HERE/'diagnostic_01/new').glob('*/raw.json'))
    replay=list((HERE/'diagnostic_01/new').glob('*/cpu_replay.json'))
    reused=list((HERE/'diagnostic_01/reused').glob('*.json'))
    bindings=True;errors=[]
    for p in done:
        d=read(p)
        for name,key in [('raw.json','raw_sha256'),('cpu_replay.json','cpu_replay_sha256')]:
            if sha(p.parent/name)!=d[key]:bindings=False;errors.append(str(p))
        inp=HERE/'input_01/observations'/d['request']['anchor_request_sha256']/'input.json'
        bindings&=sha(inp)==d['input_receipt_sha256'] and sha(HERE/'diagnostic_01/model.json')==d['model_receipt_sha256']
    result.update(done_count=len(done),raw_count=len(raw),cpu_replay_count=len(replay),reused_probe_count=len(reused),
        all_done_bound_SHA_pass=bindings,done_binding_errors=errors,done_count_read_utc=utc(),
        failures=[str(p.relative_to(HERE)) for p in HERE.rglob('*failure*.json')],
        new_optimizer_updates=0,new_time_calls=0,new_32B_calls=0,new_overview_calls=0)
    # All complete argv identities, then PPID descendants; never infer from old PID.
    table={};old={n:[] for n in ['native_round_alignment_v1','nested_density_v1','b_prompt_recovery_v1',
        'b_boundary_diagnostic_v1','context_advisory_v1','teacher_student_autopilot_v14','spatial_gap8_pchip_slot4_v1']}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
            if not args:continue
            stat=(p/'stat').read_text().rsplit(')',1)[1].split()
            row=dict(pid=int(p.name),ppid=int(stat[1]),pgid=int(stat[2]),state=stat[0],full_command=args,
                user_ticks=int(stat[11]),system_ticks=int(stat[12]))
            table[int(p.name)]=row
            if 'python' in Path(args[0]).name:
                for n in old:
                    if any(a.startswith(str(RUN/n)+'/') for a in args):old[n].append(row)
        except (OSError,ValueError):pass
    owned={pid for pid,r in table.items() if 'python' in Path(r['full_command'][0]).name and
        any(a.startswith(str(HERE)+'/') for a in r['full_command'])}
    while True:
        before=set(owned);owned|={pid for pid,r in table.items() if r['ppid'] in owned}
        if before==owned:break
    processes=[]
    for pid in sorted(owned):
        r=table[pid];p=Path('/proc')/str(pid)
        try:r['io']=(p/'io').read_text()
        except OSError:r['io']=None
        fds=[]
        try:
            for f in list((p/'fd').iterdir())[:20]:
                try:fds.append(os.readlink(f))
                except OSError:pass
        except OSError:pass
        r['open_files_sample']=fds;processes.append(r)
    result['processes']=processes;result['old_route_owned_commands']=old;result['process_read_utc']=utc()
    if not (result['stages'].get('progress.json') or {}).get('stage') and any(
        any(a.endswith('/sg8_engineering_register.py') for a in r['full_command']) for r in processes):
        result['actual_execution_stage']='RUNNING_CPU_V2_ENGINEERING_REGISTRATION_SHA_VERIFICATION'
    root=Path('/home/inspur/aic_video_work');campaign=root/'improvement_round1'
    ledger=read_ledger=[json.loads(x) for x in (campaign/'gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
    active=campaign/'active_gpu_job.json'
    result['shared_active']=read(active) if active.exists() else None
    resource=RUN/'controller/aic_SG8_slot4_v2_diagnostic.resource.json'
    v=read(resource) if resource.exists() else None
    result['resource']=v
    result['GPU_ledger']=dict(lines=len(ledger),sha256=sha(campaign/'gpu_ledger.jsonl'),read_utc=utc(),
        historical_offset=ledger[0].get('prior_charged_seconds'),owned_rows=[r for r in ledger if r['name']=='aic_SG8_slot4_v2_diagnostic'],
        unique_terminal_match=(sum(r==v for r in ledger)==1 if v else None))
    result['GPU']=subprocess.check_output(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip()
    result['compute']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],text=True).strip()
    result['meminfo_head']=Path('/proc/meminfo').read_text().splitlines()[:5]
    result['disk_free_bytes']=shutil.disk_usage(root).free;result['resource_read_utc']=utc()
    protected=[]
    for lp in RUN.glob('*/source_lock.json'):
        lock=read(lp)
        for field in ('files','production_files'):
            values=lock.get(field,{})
            paths=values if isinstance(values,dict) else [x['path'] for x in values]
            for p in paths:
                if str(p).endswith('/AGENTS.md') or str(p).endswith('/STATUS_AUTOPILOT_20261007.md') or str(p)==str(HERE/'CONTINUE.md'):
                    protected.append(str(p))
    result['protected_handoff_paths']=sorted(set(protected))
    return result
