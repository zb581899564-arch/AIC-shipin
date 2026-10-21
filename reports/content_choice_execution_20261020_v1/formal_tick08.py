"""Read-only compact current formal and critic status."""
import json
from pathlib import Path
import subprocess
import sys

CODE=r'''
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,subprocess,shutil
W=Path('/home/inspur/aic_video_work');R=W/'content_choice_20261019_v1'
out=dict(utc=datetime.now(timezone.utc).isoformat(),disk_free=shutil.disk_usage(W).free)
def ref(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def metrics(q):
 v={k:q[k] for k in ['macro','oracle_macro','mean_regret'] if k in q}
 v['rankings']={role:{k:r[k] for k in ['source_macro','source_coverage','total_sources']} for role,r in q.get('rankings',{}).items()}
 v['effects']={role:{k:r[k] for k in ['added','removed','changed','source_wins','source_losses','source_ties','false_empty_sources']} for role,r in q.get('effects',{}).items()}
 return v
for name in ['train_fit_control_completion.json','train_fit_control_failure.json','fit/completion.json','fit/failure.json','review_critic/review.json','review_critic/failure.json',
 'production_contrast_controller_completion08.json','production_contrast_controller_failure08.json','production_contrast/completion.json','production_contrast/failure.json',
 'production_critic_controller_completion08.json','critic_reuse_controller_failure11.json','production_critic/completion.json','production_critic/failure.json',
 'package_contrast_controller_completion09.json','package_contrast_controller_failure09.json','package_contrast/completion.json','package_contrast/failure.json',
 'package_critic_controller_completion09.json','package_critic_controller_failure09.json','package_critic/completion.json','package_critic/failure.json']:
 p=R/name
 if not p.exists():continue
 d=json.loads(p.read_text());v={k:x for k,x in d.items() if k in ['status','phase','error','error_type','stop_reasons','source_count','window_count','counts','actual_linear_solves','learned_deployed_parameters','actual_pipeline_parameters','execution_mode','resource_ref','scientific_stop']}
 v['ref']=ref(p)
 if name=='fit/completion.json':
  v['weights_ref']=d.get('weights_ref');v['LOSO']=metrics(d['out_of_fold_evaluation'])
 if name=='review_critic/review.json':
  for field in ['cross_source_evaluation','out_of_fold_evaluation']:
   q=d[field];v[field]=metrics(q)
 if 'receipt' in d:v['package_receipt']=d['receipt']
 out[name]=v
for name in ['production_contrast','production_critic']:
 p=R/name/'events.jsonl'
 if not p.exists():continue
 rows=[]
 for s in p.read_text().splitlines():
  try:rows.append(json.loads(s))
  except json.JSONDecodeError:pass
 last=next((x for x in reversed(rows) if 'counts' in x),{})
 out[name+'_progress']=dict(accepted_windows=len(list((R/name).glob('window_*.json'))),events=dict(Counter(x['event'] for x in rows)),
   last_event=rows[-1]['event'] if rows else None,last_counts=last.get('counts'))
out['gpu_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
print(json.dumps(out))
'''
r=subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],input=CODE,text=True,capture_output=True,timeout=55)
print(r.stdout);print(r.stderr,file=sys.stderr);r.check_returncode()
if len(sys.argv)>1:
 with (Path(__file__).resolve().parent/sys.argv[1]).open('x',encoding='utf-8') as f:json.dump(json.loads(r.stdout),f,ensure_ascii=False,indent=2)
