"""Add one bounded CPU/package continuation; never alter/relaunch formal GPU."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;REPORT=HERE.parents[1]/'reports/bottleneck_24h_20261019_v1'
value=(HERE/'complete_packages43.py').read_bytes();ast.parse(value.decode('utf-8-sig'))
script=r'''
import base64,datetime,hashlib,json,os,pathlib,subprocess
W=pathlib.Path('/home/inspur/aic_video_work');R=W/'five_summary_sprint_20261019_v41';C=R/'code_completion43'
assert os.uname().nodename=='inspur-NP5570M5' and (R/'generation_registration41.json').exists()
assert not C.exists() and not (R/'completion_extension_registration43.json').exists(),'Existing finite continuation: inspect, no duplicate launch'
def ref(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_text())
def save(p,d):
 with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
data=base64.b64decode('__VALUE__');assert hashlib.sha256(data).hexdigest()=='__SHA__'
C.mkdir();code=C/'complete_packages43.py';code.write_bytes(data)
reg=read(R/'generation_registration41.json');inputs=read(pathlib.Path(reg['package_inputs_ref']['path']))
field_bytes=pathlib.Path(inputs['source_field_files']['field_frames.jsonl']['path']).stat().st_size
pred_bytes=pathlib.Path(reg['protected_baseline_ref']['path']).stat().st_size*40
estimate=5*(field_bytes*2+pred_bytes+pathlib.Path(inputs['metadata']['path']).stat().st_size)
ext=dict(schema='BOUNDED_FIVE_PACKAGE_COMPLETION43',root=str(R),code_ref=ref(code),
 generation_registration_ref=ref(R/'generation_registration41.json'),formal_launch_ref=ref(R/'formal_chain_launch41.json'),
 review_policy_ref=ref(R/'bounded_package_review_policy43.json'),final_set_addendum_ref=ref(R/'final_set_review_addendum44.json'),
 package_output_estimate_bytes=estimate,estimate_basis=dict(full_field_bytes=field_bytes,upper_prediction_json_bytes=pred_bytes,packages=5),
 one_finite_CPU_completion_not_scheduler=True,new_goal=False,new_automation=False,
 no_GPU_or_training_or_input_output_replay=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(R/'completion_extension_registration43.json',ext)
cmd=[reg['python'],'-B',str(code),'--registration',str(R/'completion_extension_registration43.json')]
with (R/'completion_chain43.log').open('xb') as f:
 proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
launch=dict(pid=proc.pid,start_ticks=pathlib.Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19],command=cmd,
 registration_ref=ref(R/'completion_extension_registration43.json'),waiting_for_unique_legal_formal_chain=True,
 role_guard_registered_when_formal_output_count=0,final_set_addendum_registered_when_formal_output_count=29,
 no_output_content_read_for_guards=True,reviewer_type='DETERMINISTIC_REGISTERED_ENGINEERING_COLLAPSE_REVIEW',
 semantic_quality_review=False,external_new_confirmation=False,new_GPU_calls=0,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(R/'completion_chain43_launch.json',launch);print(json.dumps(launch,ensure_ascii=False))
'''.replace('__VALUE__',base64.b64encode(value).decode()).replace('__SHA__',hashlib.sha256(value).hexdigest())
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ConnectionAttempts=1','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',
    'aic-inspur-tailscale','python3 -'],input=script,text=True,capture_output=True,timeout=45,encoding='utf-8')
print(result.stdout);print(result.stderr);result.check_returncode()
with (REPORT/'five_sprint_completion_launch43.json').open('x',encoding='utf-8') as f:json.dump(json.loads(result.stdout.strip().splitlines()[-1]),f,ensure_ascii=False,indent=2)
