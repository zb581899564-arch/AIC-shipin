"""Private read-only live state, exact newly written bytes and terminal accounting."""
import json,hashlib,subprocess,socket,os
from pathlib import Path
from datetime import datetime,timezone

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ROOT=RUN/'balanced_two_window_risk_v3'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def capture():
    assert socket.gethostname()=='inspur-NP5570M5'
    stages={};digests={};component_utc={}
    for name in ('start.json','registration.json','prepared.json','preflight.json','progress.json','first_real_acceptance.json',
        'execution_failure.json','completion.json','final_acceptance.json','engineering_handoff.json','cpu_acceptance.json','prefix_cpu_acceptance.json','nontest_01/nontest.completion.json',
        'developer_01/developer.completion.json','developer_01/report.json','developer_01/model.json',
        'rematch_01/model.json','rematch_01/rematch.completion.json'):
        p=ROOT/name;component_utc[name]=utc()
        stages[name]=read(p) if p.is_file() else None
        if stages[name] is not None and name in ('cpu_acceptance.json','prefix_cpu_acceptance.json','engineering_handoff.json'):
            stages[name]={k:v for k,v in stages[name].items() if k not in ('proofs','cases','inputs','files','rows','checksums')}
        if p.is_file():digests[name]=sha(p)
    scopes={};all_bound=True
    for scope in ('nontest','developer','rematch'):
        out=ROOT/(scope+'_01');done=list(out.rglob('done.json'));raw=list(out.rglob('raw.json'))
        failures=list(out.rglob('*.failure.json'));model=read(out/'model.json') if (out/'model.json').exists() else None
        for p in done:
            v=read(p);all_bound &= all(sha(f)==s for f,s in v['bound_files'].items())
            expected_model=model or read(ROOT/'input_01/resume_manifest.json')['model_identity']
            all_bound &= ((model is not None or v.get('exact_success_recovered_from_previous_version') is True) and v['model_identity']==expected_model and v['output_valid'] is True)
        recovered=sum(read(p).get('exact_success_recovered_from_previous_version') is True for p in done)
        data=dict(read_utc=utc(),fresh_done=len(done)-recovered,recovered_exact_prior_done=recovered,accepted_route_done=len(done),raw=len(raw),failures=len(failures),all_done_bound_sha=all_bound)
        for name in ('replay_acceptance.json','temporal.stage.json','schedule.stage.json','spatial.stage.json','package.stage.json','independent_validation.json'):
            p=out/name
            if p.exists():
                v=read(p)
                if name=='replay_acceptance.json':v={k:x for k,x in v.items() if k!='proofs'}|{'accepted_new_requests':len(v['proofs'])}
                data[name]=v;digests[scope+'/'+name]=sha(p)
        candidates=list(out.glob('candidate_*8B.zip'))
        data['candidate_archives']=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in candidates]
        scopes[scope]=data
    processes=[];old_processes=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
            command=' '.join(args)
            if 'python' not in command and 'llama' not in command:continue
            cwd=Path(os.readlink(p/'cwd'))
            paths=[(Path(x) if Path(x).is_absolute() else cwd/x).resolve() for x in args if x.endswith('.py')]
            owned=any(ROOT==x.parent or ROOT in x.parents for x in paths)
            in_project=owned or any(RUN==x.parent or RUN in x.parents for x in paths)
            if not in_project:continue
            stat=(p/'stat').read_text().split();row=dict(pid=int(p.name),ppid=int(stat[3]),pgid=int(stat[4]),command=command,
                io=(p/'io').read_text(),open_files=[os.readlink(x) for x in (p/'fd').iterdir() if x.exists()][:20])
            (processes if owned else old_processes).append(row)
        except (OSError,ProcessLookupError,FileNotFoundError):pass
    shared=Path('/home/inspur/aic_video_work/improvement_round1');ledger_path=shared/'gpu_ledger.jsonl'
    ledger_bytes=ledger_path.read_bytes();ledger_read_utc=utc()
    ledger=[json.loads(x) for x in ledger_bytes.splitlines() if x.strip()];resources={}
    for name in ('developer','rematch'):
        runname='aic_BW_risk_v3_'+name;p=RUN/'controller'/(runname+'.resource.json')
        value=read(p) if p.exists() else None
        resources[name]=dict(receipt=value,sha256=sha(p) if value else None,
            unique_terminal_match=(len([r for r in ledger if r.get('name')==runname])==1 and [r for r in ledger if r.get('name')==runname][0]==value) if value else None)
    lock_path=ROOT/'source_lock.json';lock=read(lock_path) if lock_path.exists() else None
    frozen_bad=[]
    if lock:
        for path,wanted in lock['files'].items():
            if not Path(path).is_file() or sha(path)!=wanted:frozen_bad.append(path)
    artifacts={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
    return dict(utc=utc(),hostname=socket.gethostname(),stages=stages,component_read_utc=component_utc,component_sha256=digests,
        scopes=scopes,all_new_done_bound_sha=all_bound,processes=processes,other_project_processes=old_processes,
        GPU=subprocess.check_output(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total','--format=csv,noheader'],text=True).strip(),
        memory=Path('/proc/meminfo').read_text(),disk_free_bytes=__import__('shutil').disk_usage(RUN).free,
        shared_active=read(shared/'active_gpu_job.json') if (shared/'active_gpu_job.json').exists() else None,
        ledger=dict(lines=len(ledger),sha256=hashlib.sha256(ledger_bytes).hexdigest(),read_utc=ledger_read_utc,historical_offset=7200),resources=resources,
        source_lock_sha256=sha(lock_path) if lock else None,frozen_files=len(lock['files']) if lock else 0,
        all_frozen_sha_pass=not frozen_bad,frozen_bad=frozen_bad,artifacts=artifacts,non_atomic_component_reads=True,
        new_optimizer_updates=0,official_score=None)
