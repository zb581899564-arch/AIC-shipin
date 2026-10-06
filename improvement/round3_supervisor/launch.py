from pathlib import Path
import json,subprocess,datetime,hashlib
r=Path('/home/inspur/aic_video_work'); out=r/'round3_20260912'; py=str(r/'env/qwen3vl_isolated_20260910/bin/python')
script=out/'temporal_query_transfer/run_contrast.py'
text=script.read_text()
assert 'qwen3vl_isolated_20260910' in text
cmd=[py,str(r/'improvement_round1/budget_run.py'),'--name','r3_temporal_2x2_12g','--max-seconds','3600','--',py,str(script),'--num-groups','12','--include-lora-query-128']
with (out/'launch.log').open('x') as log:
 p=subprocess.Popen(cmd,cwd=r,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
record={'pid':p.pid,'command':cmd,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'status':'dispatched_not_accepted','best_official_score_user_reported':43.48}
(out/'launch.json').write_text(json.dumps(record,indent=2)); print(json.dumps(record))
