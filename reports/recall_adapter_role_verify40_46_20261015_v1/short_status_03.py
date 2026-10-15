"""One bounded actual-argv/I/O/terminal snapshot, no quality recomputation."""
import datetime as dt
import json
from pathlib import Path
import socket
import subprocess

ROOT=Path('/home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1')
assert socket.gethostname()=='inspur-NP5570M5'
value=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),processes=[],stages={})
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        if str(ROOT) not in argv:continue
        stat=(p/'stat').read_text().rsplit(')',1)[1].split()
        value['processes'].append(dict(pid=int(p.name),ppid=int(stat[1]),state=stat[0],start_ticks=stat[19],argv=argv,io=(p/'io').read_text()))
    except (OSError,ProcessLookupError):pass
for rel in ['chain_01','gpu_01','output_qa_01','comparison_01']:
    p=ROOT/rel
    if not p.exists():continue
    row={}
    for name in ['completion.json','failure.json','result.json']:
        q=p/name
        if q.is_file():
            v=json.loads(q.read_text());row[name]={k:v[k] for k in ['status','utc','stage','calls','actual_new_calls','error','conditions','macro','new_decisions','paired_decisions'] if k in v}
            if name=='failure.json':row[name]['traceback_tail']=v.get('traceback','')[-3500:]
    if (p/'attempts.jsonl').is_file():
        rows=[json.loads(line) for line in (p/'attempts.jsonl').read_text().splitlines() if line.strip()]
        row['BEGIN']=sum(x['event']=='BEGIN' for x in rows);row['ACCEPTED']=sum(x['event']=='ACCEPTED' for x in rows)
    row['direct_json_files']=len(list(p.glob('*.json')))
    value['stages'][rel]=row
value['gpu']=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
print(json.dumps(value,ensure_ascii=False))
