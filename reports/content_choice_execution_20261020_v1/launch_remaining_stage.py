"""Explicit independent post-check stage; no default training or production."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
MODE=sys.argv[1]
assert MODE in ('observation','train_fit')
DECISION=Path(sys.argv[2])
decision=json.loads(DECISION.read_text(encoding='utf-8'))
assert decision['approved'] is True and decision['mode']==MODE
assert decision['implementation_sha']=='cb6095cc3156319054f23e5a3ad5baeb5ed9d0c1'
assert decision['review_notes'].strip()
R='/home/inspur/aic_video_work/content_choice_20261019_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
source=r'''
from pathlib import Path
import hashlib,json,os,socket,subprocess
R=Path(RUN_ROOT)
def load(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p.resolve(strict=True)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,v):
 with p.open('x') as s:json.dump(v,s,ensure_ascii=False,indent=2)
assert socket.gethostname()=='inspur-NP5570M5'
if (R/'user_pause_01.json').exists():
 assert (R/'user_resume_01.json').exists(), 'Human pause: no new stage without explicit resume receipt'
 assert load(R/'user_resume_01.json')['explicit_human_resume'] is True
assert load(R/'check_control_completion.json')['status']=='CHECK_COLLECTION_AND_CONTRAST_REVIEW_COMPLETE'
assert not (R/'check_control_failure.json').exists()
assert not (R/(MODE+'_control_started.json')).exists() and not (R/(MODE+'_launch.json')).exists()
assert load(R/'collect_check/completion.json')['window_count']==43
assert load(R/'collect_check/completion.json')['source_count']==8
assert DECISION['check_completion_sha256']==ref(R/'collect_check/completion.json')['sha256']
assert DECISION['contrast_review_sha256']==ref(R/'review_contrast/review.json')['sha256']
DECISION['collect_check_ref']=ref(R/'collect_check/completion.json')
DECISION['contrast_review_ref']=ref(R/'review_contrast/review.json')
DECISION['code_manifest_ref']=ref(R/'code/improvement/content_choice_v1/code_manifest.json')
if MODE=='train_fit':
 cross=load(R/'review_contrast/review.json')['cross_source_evaluation']
 assert cross['oracle_macro']>max(cross['macro']['greedy']['f1'],cross['macro']['protected_proxy']['f1'])
 assert cross['rankings']['contrast']['source_coverage']==8
 assert cross['rankings']['raw']['source_coverage']==8
 save(R/'critic_train_admission.json',DECISION)
else:save(R/'independent_observation_admission.json',DECISION)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
with (R/(MODE+'_control_parent.log')).open('x') as log:
 p=subprocess.Popen([PYTHON,'-B',str(R/'control.py'),'--mode',MODE],cwd=R/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
receipt=dict(status='EXPLICIT_REVIEWED_NEXT_STAGE_STARTED',mode=MODE,pid=p.pid,start_ticks=ticks,decision=DECISION,automatic_production=False,new_zip=0)
save(R/(MODE+'_launch.json'),receipt);print(json.dumps(receipt))
'''
source='\n'.join(k+'='+repr(v) for k,v in dict(RUN_ROOT=R,PYTHON=PY,MODE=MODE,DECISION=decision).items())+'\n'+source
result=subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale',PY+' -B -'],input=source,text=True,encoding='utf-8',capture_output=True,timeout=50)
with (HERE/(MODE+'_launch_result_01.json')).open('x',encoding='utf-8') as s:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr),s,ensure_ascii=False,indent=2)
print(result.stdout);print(result.stderr);result.check_returncode()
