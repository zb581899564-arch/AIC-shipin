"""Deploy one explicit main-agent decision and start exactly one finite controller."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys

H=Path(__file__).resolve().parent
ACTION,CANDIDATE,FILE=sys.argv[1:]
assert ACTION in ('production','package') and CANDIDATE in ('critic','contrast')
d=json.loads(Path(FILE).read_text(encoding='utf-8'))
assert d['approved'] is True and d['candidate']==CANDIDATE
assert d['review_notes'].strip()
SUFFIX='08' if ACTION=='production' else '09'
source=r'''
from pathlib import Path
from datetime import datetime,timezone
import json,os,socket,subprocess,hashlib
R=Path('/home/inspur/aic_video_work/content_choice_20261019_v1')
assert socket.gethostname()=='inspur-NP5570M5'
assert json.loads((R/'user_resume_01.json').read_text())['explicit_human_resume'] is True
name=ACTION+'_'+CANDIDATE
assert not (R/(name+'_controller_started'+SUFFIX+'.json')).exists()
assert not (R/(name+'_launch'+SUFFIX+'.json')).exists()
if ACTION=='production':
 assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(), 'Do not conflict with active GPU work'
 review=R/('review_'+CANDIDATE)/'review.json';value=json.loads(review.read_text())
 assert value['status']=='ELIGIBLE_FOR_EXECUTION_REVIEW' and value['stop_reasons']==[]
 assert hashlib.sha256(review.read_bytes()).hexdigest()==DECISION['review_sha256']
else:
 comp=R/('production_'+CANDIDATE)/'completion.json'
 assert hashlib.sha256(comp.read_bytes()).hexdigest()==DECISION['production_sha256']
with (R/(name+'_decision'+SUFFIX+'.json')).open('x') as f:json.dump(DECISION,f,ensure_ascii=False,indent=2)
controller=R/(ACTION+'_controller'+SUFFIX+'.py')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if ACTION=='production' else '',PYTHONDONTWRITEBYTECODE='1')
with (R/(name+'_controller_parent'+SUFFIX+'.log')).open('x') as log:
 p=subprocess.Popen([PYTHON,'-B',str(controller),'--candidate',CANDIDATE],cwd=R/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
receipt=dict(utc=datetime.now(timezone.utc).isoformat(),status='EXPLICIT_MAIN_REVIEWED_STAGE_STARTED',candidate=CANDIDATE,action=ACTION,pid=p.pid,start_ticks=ticks,decision=DECISION,automatic_website_submission=False)
with (R/(name+'_launch'+SUFFIX+'.json')).open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt))
'''
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
source='\n'.join(k+'='+repr(v) for k,v in dict(ACTION=ACTION,CANDIDATE=CANDIDATE,SUFFIX=SUFFIX,DECISION=d,PYTHON=PY).items())+'\n'+source
r=subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale',PY+' -B -'],input=source,text=True,encoding='utf-8',capture_output=True,timeout=55)
with (H/(ACTION+'_'+CANDIDATE+'_launch_result'+SUFFIX+'.json')).open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),f,ensure_ascii=False,indent=2)
print(r.stdout);print(r.stderr);r.check_returncode()
