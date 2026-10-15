"""Freeze one independent fresh4 run after actual consensus development PASS."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT=Path(__file__).resolve().parent
WORK=REPORT.parents[1]
ROOT='/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1'
OLD='/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1'
INCOMING=ROOT+'/incoming_fresh_control_04.zip'


def remote(script,seconds=50):
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(script.encode()).decode()+'\'))"'
    if len(command)>31000:raise ValueError('Control command too long; do not silently shell-split')
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],capture_output=True,text=True,timeout=seconds)
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)


def main():
    pre=remote(r'''
import datetime,hashlib,json,os,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');assert socket.gethostname()=='inspur-NP5570M5'
assert not (r/'fresh_confirm_registration.json').exists() and not (r/'fresh_control_01').exists() and not (r/'confirm').exists()
assert not (r/'incoming_fresh_control_04.zip').exists(),'Prior unknown transfer must be inspected, not overwritten'
v=json.loads((r/'development_01/result.json').read_text());s=json.loads((r/'selection_before_fresh_confirmation.json').read_text())
assert v['status']=='PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM' and len(v['cases'])==8 and all(v['conditions'].values())
assert s['result_sha256']==hashlib.sha256((r/'development_01/result.json').read_bytes()).hexdigest() and s['fresh_confirm_metrics_examined'] is False
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  if any(str(r) in a for a in argv):owned.append(dict(pid=p.name,argv=argv))
 except OSError:pass
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),cpu_count=os.cpu_count(),load=list(os.getloadavg()),
 memory=pathlib.Path('/proc/meminfo').read_text(),disk=list(shutil.disk_usage(r)),owned=owned,
 external_commands=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:18],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 development_sha256=s['result_sha256'])))
'''.replace('__ROOT__',ROOT))
    with (REPORT/'fresh_resources_before_launch_04.json').open('x',encoding='utf8') as f:json.dump(pre,f,ensure_ascii=False,indent=2)
    code=WORK/'improvement/recall_consensus_verify40_46_v1'
    files={'code/'+p.name:p.read_bytes() for p in code.iterdir() if p.is_file() and p.suffix in ('.py','.md')}
    required=('prepare_fresh_reference.py','prepare_fresh_inputs.py','admit_fresh_inputs.py','model_common.py','pilot_runtime.py','pilot_verify.py','pilot_chain_fresh.py','fresh_control.py','evaluate_confirmation.py','input_fresh_notes.md')
    assert all('code/'+name in files for name in required)
    files['public_routes.json']=(REPORT/'public_routes.json').read_bytes()
    files['deployment_manifest_04.json']=json.dumps(dict(files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'fresh_control_04.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    data=bundle.read_bytes();assert len(data)<262144
    digest=hashlib.sha256(data).hexdigest()
    p=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=12',str(bundle),'aic-inspur-home:'+INCOMING],capture_output=True,text=True,timeout=60)
    if p.returncode:raise RuntimeError('Inspect remote size/SHA before any explicit remaining transfer: '+p.stderr)
    prior=json.loads((REPORT/'prior_media_and_routes_02.json').read_text(encoding='utf8'))['prior_media_receipts']
    prior_refs=[dict(path=x['path'],sha256=x['sha256']) for x in prior]
    script=r'''
import datetime as dt,hashlib,json,os,pathlib,shutil,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');old=pathlib.Path('__OLD__');bundle=r/'incoming_fresh_control_04.zip'
assert socket.gethostname()=='inspur-NP5570M5' and not (r/'fresh_confirm_registration.json').exists() and not (r/'confirm').exists()
assert bundle.stat().st_size==__SIZE__ and hashlib.sha256(bundle.read_bytes()).hexdigest()=='__SHA__'
with zipfile.ZipFile(bundle) as z:
 assert z.testzip() is None
 m=json.loads(z.read('deployment_manifest_04.json'))['files']
 assert set(z.namelist())==set(m)|{'deployment_manifest_04.json'}
 for name,row in m.items():
  key=pathlib.PurePosixPath(name);assert not key.is_absolute() and '..' not in key.parts
  b=z.read(name);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
  target=r/name
  if target.exists():assert target.is_file() and target.read_bytes()==b,'Never overwrite any prior deployed evidence'
  else:
   target.parent.mkdir(exist_ok=True,parents=True)
   with target.open('xb') as f:f.write(b)
 with (r/'deployment_manifest_04.json').open('xb') as f:f.write(z.read('deployment_manifest_04.json'))
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'code'))
import model_common as io,prepare_fresh_reference as source
files={};codes={}
def add(path,digest=None,code=False):
 p=pathlib.Path(path);assert p.is_file() and p.is_relative_to(io.HOME_ROOT)
 actual=io.sha(p);assert digest is None or actual==digest
 files[str(p)]=actual
 if code:codes[str(p)]=actual
 return dict(path=str(p),sha256=actual)
for p in (r/'code').iterdir():
 if p.is_file() and p.suffix in ('.py','.md'):add(p,code=p.suffix=='.py')
native=io.HOME_ROOT/'videoxum_reference_iteration_20261013_v1/code'
for name in ('native_profile_01.py','native_profile_04.py'):add(native/name,code=True)
metric=old/'code/evaluate_pilot.py'
add(metric,io.read(r/'deployment_manifest.json')['adopted_readonly_dependencies'][str(metric)],code=True)
for p in io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG),str(io.RUNTIME)}:add(p)
for name in ('cv_contract.py','cv_grammar.py','cv_tokens.py'):add(io.CV_CODE/name,code=True)
add(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py',code=True)
refs={}
for key,p in [('protocol_ref',r/'protocol.json'),('authorization_ref',r/'USER_AUTHORIZATION.json'),('development_selection_ref',r/'selection_before_fresh_confirmation.json'),('development_result_ref',r/'development_01/result.json'),('public_routes_ref',r/'public_routes.json'),('prior_source_registration_ref',old/'new8_source_registration_01.json')]:refs[key]=add(p)
add(r/'official_rule_check_01.json');registry=io.read(refs['prior_source_registration_ref']['path'])
prior_refs=__PRIOR_REFS__;prior_ids=set()
for ref in prior_refs:
 add(ref['path'],ref['sha256']);prior_ids.add(io.read(ref['path'])['video_id'])
assert len(prior_ids)==10
selected,reserves=source.expected_candidate_rows(registry,prior_ids)
for name in ('annotation_file','known_exclusions'):add(registry[name+'_path'],registry[name+'_sha256'])
now=dt.datetime.now(dt.timezone.utc)
reg=dict(schema='RECALL_CONSENSUS_FRESH4_REFERENCE_REGISTRATION_V1',status='REGISTERED_FIRST_FRESH_CONFIRM_MEDIA_NATIVE_REFERENCE',group='confirm',registered_at_utc=now.isoformat(),
 expected_accepted_sources=4,maximum_media_pool_bytes=24392052,windows_video_body_bytes=0,route_acquisition_method='HEAD',
 selection=selected,ordered_engineering_reserves=reserves,selected_confirm_ids=[x['video_id'] for x in selected],ordered_confirm_engineering_reserve_ids=[x['video_id'] for x in reserves],
 annotation_file_path=registry['annotation_file_path'],annotation_file_sha256=registry['annotation_file_sha256'],known_exclusions_path=registry['known_exclusions_path'],known_exclusions_sha256=registry['known_exclusions_sha256'],
 old_exposed_and_reserved_ids=sorted(set(registry['old_exposed_and_reserved_ids'])|prior_ids),prior_media_receipts=prior_refs,expected_prior_media_count=10,
 runtime=dict(native_frames=64,max_input_tokens=16384,max_output_tokens=256,baseline_window_seconds='30',candidate_window_seconds='15',candidate_stride_seconds='15/2',B0_prompt_sha256=io.PROMPT_SHA,grammar_allow_empty=True,model_parameters=io.MODEL_PARAMETERS,enabled_TIME_layers=144,base_sha256=io.BASE_SHA,adapter_sha256=io.ADAPTER_SHA),
 gpu_budget=dict(confirm_B0_max_seconds=1800,confirm_VERIFY_max_seconds=2400,per_group_max_B0_actual_calls=48,per_group_max_VERIFY_actual_calls=240),
 deadline=(now+dt.timedelta(hours=6)).isoformat(),required_files=files,required_code_files=codes,**refs)
io.save(r/'fresh_confirm_registration.json',reg)
source.registration(r);io.fresh_gate(r,'confirm')
for name in io.JOBS.values():
 assert not (io.RUN/'controller'/(name+'.resource.json')).exists(),'Unique job already has terminal'
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert gpu and gpu[0].strip().isdigit()
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONDONTWRITEBYTECODE='1')
python=io.HOME_ROOT/'env/qwen3vl_isolated_20260910/bin/python'
argv=[str(python),'-B','-u',str(r/'code/fresh_control.py'),'--root',str(r)]
claim=r/'fresh_chain_launch_claim_04.json';io.save(claim,dict(utc=io.utc(),argv=argv,registration_sha256=io.sha(r/'fresh_confirm_registration.json'),parent_CUDA=env['CUDA_VISIBLE_DEVICES']))
with (r/'fresh_control_04.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=pathlib.Path('/proc')/str(p.pid)/'stat';ticks=stat.read_text().split(') ',1)[1].split()[19]
receipt=dict(utc=io.utc(),root=str(r),pid=p.pid,start_ticks=ticks,argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__SIZE__,bundle_sha256='__SHA__',CRC_member_SHA_passed=True,registration_sha256=io.sha(r/'fresh_confirm_registration.json'),
 protocol_sha256=io.sha(r/'protocol.json'),development_result_sha256=io.sha(r/'development_01/result.json'),selected_ids=reg['selected_confirm_ids'],reserved_pool_bytes=24392052,
 actual_model_calls_at_launch=0,production_admitted=False,no_fixed40_426_or_package_started=True)
io.save(r/'fresh_chain_launch_04.json',receipt);print(json.dumps(receipt))
'''.replace('__ROOT__',ROOT).replace('__OLD__',OLD).replace('__SIZE__',str(len(data))).replace('__SHA__',digest).replace('__PRIOR_REFS__',repr(prior_refs))
    result=remote(script,seconds=60)
    with (REPORT/'fresh_deployment_launch_04.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
