"""One short read-only snapshot; no process signaling or implicit recovery."""
from pathlib import Path
import datetime as dt,json,subprocess
R=Path(__file__).resolve().parent
CODE='''from pathlib import Path
import json,datetime as dt,socket,subprocess
r=Path('/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1');s=r/'production_unique_09'
launch=json.loads((r/'production_unique_launch_09.json').read_text());pid=launch['pid'];p=Path('/proc')/str(pid)
handle=dict(expected_pid=pid,expected_start_ticks=launch['start_ticks'],live=False)
if p.exists():
 stat=(p/'stat').read_text().split();cmd=(p/'cmdline').read_bytes().split(b'\\0');argv=[v.decode() for v in cmd if v]
 handle.update(live=stat[21]==launch['start_ticks'] and argv==launch['argv'],actual_start_ticks=stat[21],argv=argv,state=stat[2],IO=(p/'io').read_text(),children=sorted({int(v) for q in (p/'task').glob('*/children') for v in q.read_text().split()}))
j=s/'gpu_01/journal.jsonl';rows=[json.loads(v) for v in j.read_text().splitlines()] if j.exists() else []
accepted=[v for v in rows if v['event']=='ACCEPTED'];begins=[v for v in rows if v['event']=='BEGIN']
seconds=None
if len(accepted)>5:
 seconds=(dt.datetime.fromisoformat(accepted[-1]['utc'])-dt.datetime.fromisoformat(accepted[0]['utc'])).total_seconds()/(len(accepted)-1)
failures={}
for q in [s/'chain_failure.json',s/'infer_failure.json',s/'output_qa_failure.json',r/'risk_finalization_15/failure.json']:
 if q.exists():failures[str(q.relative_to(r))]=json.loads(q.read_text())
packages=[]
for q in (r/'packages').glob('package_*/completion.json'):
 d=json.loads(q.read_text());packages.append({k:d[k] for k in ['arm','bytes','SHA256','frame_count','added_frames','removed_frames','quality_pass_claimed']})
print(json.dumps(dict(UTC=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),handle=handle,BEGIN=len(begins),ACCEPTED=len(accepted),ALIAS=sum(v['event']=='ALIAS_ADOPTED_NO_MODEL_CALL' for v in rows),last_event=rows[-1] if rows else None,observed_seconds_per_accepted=seconds,inference_finished=(s/'gpu_01/completion.json').exists(),all_first_QA_finished=(s/'completion.json').exists(),parent_natural_complete=(s/'chain_completion.json').exists(),failures=failures,packages=packages,GPU=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()),ensure_ascii=False))
'''
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','aic-inspur-tailscale','python3','-'],input=CODE,text=True,capture_output=True,check=True)
d=json.loads(res.stdout);stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');(R/('status_'+stamp+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(d,ensure_ascii=False))
