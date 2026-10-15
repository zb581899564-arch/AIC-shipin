"""Only key names/existence/counts from the named production metadata roots."""
import shlex
import subprocess

PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15',
       '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-home']
code = r'''import hashlib,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
here=run/'balanced_two_window_risk_v3'
plan=json.loads((here/'input_01/rematch_plan.json').read_text());job=plan['jobs'][0];part=job['windows'][0]
digest=hashlib.sha256(json.dumps(job['video_id'],sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()).hexdigest()
same=part['window']==part['base_window']
p=here/('rematch_01/aliases/'+digest+'/0.json' if same else 'rematch_01/local/'+digest+'/0/BW/done.json')
done=json.loads(p.read_text()); assembled=here/'rematch_01/temporal.jsonl'
first=json.loads(next(x for x in assembled.open() if x.strip()))
item=first['windows'][0]
shape={'plan_keys':list(plan),'job_keys':list(job),'metadata_keys':list(job['metadata']),'part_keys':list(part),'window_keys':list(part['window']),'done_keys':list(done),'assembled_row_keys':list(first),'assembled_window_keys':list(item),'video_identity_keys':list(item.get('video_identity',{})),'native_processor_keys':list(item.get('video_identity',{}).get('native_processor_identity',{})),'input_ref':plan.get('input_ref'),'named_cache_roots':[]}
for q in [here/'rematch_01',run/'b_score_aligned_package_v4/rematch_01',run/'teacher_student_autopilot_v14/cache_01',run/'teacher_student_autopilot_v14/input_01']:
 shape['named_cache_roots'].append({'path':str(q),'exists':q.exists(),'immediate_children':[{'name':z.name,'directory':z.is_dir()} for z in q.iterdir()] if q.exists() else []})
print(json.dumps(shape))
'''
if __name__=='__main__':
    r=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)],capture_output=True,check=True)
    print(r.stdout.decode(),end='')
