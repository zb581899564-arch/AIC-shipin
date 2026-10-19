"""Windows necessary small code deployment and once-only strict SSH launch."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'bottleneck_24h_v1'
REPORT = HERE.parents[1]/'reports/bottleneck_24h_20261019_v1'
own = ('base_pilot41.py','review_pilot41.py','run_pilot_chain41.py')
helpers = ('summary_generate.py','summary_contract.py','summary_context_pixels.py','summary_grammar6.py','summary_output.py','evaluate_summary.py')
files = {name:(HERE/name).read_bytes() for name in own}
files.update({name:(OLD/name).read_bytes() for name in helpers})
for name, value in files.items(): ast.parse(value.decode('utf-8-sig'), filename=name)
contents = io.BytesIO()
with zipfile.ZipFile(contents,'w',zipfile.ZIP_DEFLATED) as z:
    for name, value in files.items(): z.writestr(name,value)
archive = contents.getvalue(); members = {name:hashlib.sha256(value).hexdigest() for name,value in files.items()}
payload = base64.b64encode(archive).decode('ascii')
script = r'''
import base64,datetime,hashlib,io,json,os,pathlib,shutil,subprocess,zipfile
W=pathlib.Path('/home/inspur/aic_video_work');P=W/'bottleneck_24h_20261019_v1';R=W/'five_summary_sprint_20261019_v41'
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
assert os.uname().nodename=='inspur-NP5570M5'
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
assert not apps,'External GPU work; do not launch or interfere'
assert not R.exists(),'New root already exists; inspect, never blind repeat deploy/launcher'
payload=base64.b64decode('__PAYLOAD__'); assert len(payload)==__SIZE__ and hashlib.sha256(payload).hexdigest()=='__SHA__'
expected=__MEMBERS__
z=zipfile.ZipFile(io.BytesIO(payload)); assert z.testzip() is None and set(z.namelist())==set(expected)
for n in z.namelist():
 assert pathlib.PurePosixPath(n).name==n and hashlib.sha256(z.read(n)).hexdigest()==expected[n]
R.mkdir(); (R/'deployment_01.zip').write_bytes(payload); C=R/'code_pilot41';C.mkdir()
for n in z.namelist():
 with (C/n).open('xb') as f:f.write(z.read(n))
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,d):
 with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
old=read(P/'summary_generation_registration_10.json')
reg={k:old[k] for k in ['first_dev_input_acceptance_ref','model_config_ref','initial_TIME_ref','pixel_dictionary_ref','pixel_codec_ref','baseline_human_adoption_ref']}
reg.update(schema='FIVE_SUMMARY_BASE_PILOT_V41',root=str(R),code={n:ref(C/n) for n in expected},
 python=str(W/'env/qwen3vl_isolated_20260910/bin/python'),gpu_index=0,
 gpu_wrapper_ref=ref(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
 job_name='five_summary_base43_original_frozen_20261019_v41',max_gpu_seconds=1200,
 model_start_cutoff_utc='2026-10-19T11:52:37Z',deadline_utc='2026-10-19T15:52:37Z',
 planned_output_bytes=16777216,planned_ram_bytes=42949672960,
 adopted_TIME_output_QA_ref=ref(P/'summary_generation_10/INIT_TIME/first_independent_output_QA.json'),
 adopted_TIME_completion_ref=ref(P/'summary_generation_10/INIT_TIME/completion.json'),
 collapse_check=dict(maximum_empty_sources=2,minimum_fraction_baseline_f1=0.5,minimum_fraction_baseline_recall=0.5,
  purpose='Broad known-collapse exclusion, not old proxyF1 promotion; frozen before new BASE43 outputs'),
 policies={'1':'B|(T&C)','2':'B&(T|C)','3':'T','4':'C','5':'(B&(T|C))|(T&C)'},
 user_authorization='现在开始启动',baseline40_47_unchanged=True,optimizer_updates=0,new_goal=False,new_automation=False)
save(R/'registration_pilot41.json',reg)
save(R/'deployment_acceptance41.json',dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),CRC=True,members=expected,code_ref={n:ref(C/n) for n in expected}))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
cmd=[reg['python'],'-B',str(C/'run_pilot_chain41.py'),'--registration',str(R/'registration_pilot41.json')]
with (R/'pilot_chain41.log').open('xb') as f:
 proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=str(C),env=env,start_new_session=True)
ticks=pathlib.Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19]
launch=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,start_ticks=ticks,command=cmd,registration_ref=ref(R/'registration_pilot41.json'),deployment_bytes=len(payload),deployment_sha256=hashlib.sha256(payload).hexdigest(),new_BASE_calls_registered=43,adopted_TIME_calls=43)
save(R/'pilot_chain_launch41.json',launch)
print(json.dumps(launch,ensure_ascii=False))
'''
script = script.replace('__PAYLOAD__',payload).replace('__SIZE__',str(len(archive))).replace('__SHA__',hashlib.sha256(archive).hexdigest()).replace('__MEMBERS__',repr(members))
result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ConnectionAttempts=1',
    '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-tailscale','python3 -'],
    input=script,text=True,capture_output=True,timeout=55,encoding='utf-8')
print(result.stdout); print(result.stderr)
if result.returncode: raise SystemExit(result.returncode)
launch = json.loads(result.stdout.strip().splitlines()[-1])
REPORT.mkdir(exist_ok=True,parents=True)
with (REPORT/'five_sprint_pilot_launch41.json').open('x',encoding='utf-8') as f:json.dump(launch,f,ensure_ascii=False,indent=2)
