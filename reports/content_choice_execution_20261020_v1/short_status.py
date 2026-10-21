"""One bounded read-only remote snapshot, no watcher or raw transfer."""
from pathlib import Path
import json
import subprocess
import sys
CODE = r'''
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,os,shutil,socket,subprocess
W=Path('/home/inspur/aic_video_work');R=W/'content_choice_20261019_v1'
out=dict(utc=datetime.now(timezone.utc).isoformat(),host=socket.gethostname(),disk_free=shutil.disk_usage(W).free)
def load(p):return json.loads(p.read_text())
def brief(d):return {k:v for k,v in d.items() if k in ['status','phase','error','error_type','pid','start_ticks','counts','source_count','window_count','control_windows_adopted','expected_actual_calls','both_absolute_logps_fell','actual_new_qwen_calls','changed_input_windows','adopted_unchanged_windows','scientific_stop','resource_ref','baseline_ref','candidate','stop_reasons','budget','actual_pipeline_parameters']}
for name in ['cpu_control_completion.json','cpu_control_failure.json','check_control_completion.json','check_control_failure.json','observation_control_completion.json','observation_control_failure.json','train_fit_control_completion.json','train_fit_control_failure.json','collect_check/completion.json','collect_check/failure.json','collect_train/completion.json','collect_train/failure.json','observation/completion.json','observation/failure.json','fit/completion.json','fit/failure.json','review_contrast/review.json','review_critic/review.json','review_observation/review.json']:
 p=R/name
 if p.exists():
  d=load(p);out[name]=brief(d)
  if 'cross_source_evaluation' in d:
   q=d['cross_source_evaluation'];out[name]['summary']={k:q[k] for k in ['macro','effects','rankings','oracle_macro','mean_regret','candidate_pool'] if k in q}
  if 'out_of_fold_evaluation' in d and d['out_of_fold_evaluation'] is not None:out[name]['LOSO_summary']={k:d['out_of_fold_evaluation'][k] for k in ['macro','effects','rankings','oracle_macro','mean_regret'] if k in d['out_of_fold_evaluation']}
for name in ['collect_check','collect_train','observation']:
 p=R/name/'events.jsonl'
 if p.exists():
  rows=[]
  for s in p.read_text().splitlines():
   try:rows.append(json.loads(s))
   except json.JSONDecodeError:pass
  out[name+'_progress']=dict(events=len(rows),event_types=dict(Counter(r.get('event',r.get('kind','UNKNOWN')) for r in rows)),last_event_meta={k:v for k,v in rows[-1].items() if k in ['event','kind','uid','scope','source_id','counts','seconds','utc']} if rows else None,accepted_windows=len(list((R/name).glob('window_*.json'))))
owned=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  raw=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
  if str(R) not in raw and 'content_choice_20261019_v1_collect' not in raw and 'temporal_production_control_v5/code/controller.py' not in raw:continue
  if '-B -'==raw.strip().split('python')[-1].strip():continue
  s=(p/'stat').read_text().rsplit(')',1)[1].split()
  child=set()
  for task in (p/'task').iterdir():
   try:child.update((task/'children').read_text().split())
   except (FileNotFoundError,ProcessLookupError,PermissionError):pass
  owned.append(dict(pid=int(p.name),state=s[0],ppid=int(s[1]),start_ticks=s[19],argv=raw,children_all_threads=sorted(child),io=(p/'io').read_text().splitlines()[:4]))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
out['actual_processes']=owned
out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
out['gpu_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
print(json.dumps(out))
'''
result = subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale',
    '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],
    input=CODE,text=True,capture_output=True,timeout=45)
print(result.stdout); print(result.stderr,file=sys.stderr)
result.check_returncode()
if len(sys.argv)>1:
    d=json.loads(result.stdout)
    with (Path(__file__).resolve().parent/sys.argv[1]).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
