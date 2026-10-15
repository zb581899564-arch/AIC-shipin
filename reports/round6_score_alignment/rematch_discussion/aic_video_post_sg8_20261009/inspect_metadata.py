"""Read-only /proc and registered developer plan schema; no media/model import."""
import json, hashlib, os, socket, shutil
from pathlib import Path
from datetime import datetime, timezone
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
p = RUN/'context_advisory_v1/input_01/developer_plan.json'
d = json.loads(p.read_bytes())
jobs = d['developer_jobs']
owned = []
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit(): continue
    try:
        args = (proc/'cmdline').read_bytes().split(b'\0')
        args = [x.decode(errors='replace') for x in args if x]
        if any(str(RUN) in a and a.endswith('.py') for a in args):
            st = (proc/'stat').read_text().split(') ',1)[1].split()
            owned.append(dict(pid=int(proc.name),ppid=int(st[1]),pgid=int(st[2]),state=st[0],command=args))
    except (FileNotFoundError, PermissionError, ProcessLookupError): pass
multi = [j for j in jobs if len(j['windows'])>1]
result = dict(utc=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),
    plan_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),top_keys=list(d),records=len(jobs),
    groups=len({j['source_group'] for j in jobs}),windows=sum(len(j['windows']) for j in jobs),
    multi_records=len(multi),multi_groups=len({j['source_group'] for j in multi}),
    multi_window_counts=[len(j['windows']) for j in multi],job_keys=list(jobs[0]),
    sample_window=multi[0]['windows'][0] if multi else None,
    source_clock_type=type(d['source_clocks']).__name__,
    source_clock_sample=(next(iter(d['source_clocks'].values())) if isinstance(d['source_clocks'],dict) else d['source_clocks'][0]),owned=owned,
    disk_free=shutil.disk_usage(RUN).free,new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0,remote_writes=0)
print(json.dumps(result,ensure_ascii=False))
