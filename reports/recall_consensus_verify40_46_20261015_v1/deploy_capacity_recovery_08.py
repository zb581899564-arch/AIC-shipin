"""Explicit remaining first-input recovery; adopt4 media/clocks and32-plan."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT=Path(__file__).resolve().parent
WORK=REPORT.parents[1]
ROOT='/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1'


def remote(script,seconds=50):
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(script.encode()).decode()+'\'))"'
    assert len(command)<31000
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],capture_output=True,text=True,timeout=seconds)
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)


def main():
    pre=remote(r'''
import datetime,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');assert socket.gethostname()=='inspur-NP5570M5'
f=json.loads((r/'confirm/inputs_01/failure.json').read_text());m=json.loads((r/'confirm/reference_01/completion.json').read_text())
assert f['stage']=='RGB_UNION' and f['successful_entries']==[] and f['complete_sources']==[] and f['actual_primary_encode_calls_started']==f['actual_primary_encode_calls_returned']==0
assert len(m['accepted'])==4 and m['actual_new_model_calls']==0
assert len(json.loads((r/'confirm/inputs_01/view_plan.json').read_text())['unique_views'])==32
assert not (r/'recovery_v2').exists() and not (r/'incoming_capacity_recovery_08.zip').exists() and not (r/'fresh_recovery_registration_02.json').exists()
assert not (r/'confirm/B0').exists() and not (r/'confirm/VERIFY').exists()
assert not list((r/'confirm/inputs_01').rglob('proof.json')) and not list((r/'confirm/inputs_01').rglob('frames.npz')) and not list((r/'confirm/inputs_01').rglob('rgb_union.json'))
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),disk=list(shutil.disk_usage(r)),memory=pathlib.Path('/proc/meminfo').read_text(),
 active_commands=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:16],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 new_model_calls=0,retained_media_native=4,adopted_plan_views=32)))
'''.replace('__ROOT__',ROOT))
    with (REPORT/'capacity_recovery_preflight_08.json').open('x',encoding='utf8') as s:json.dump(pre,s,ensure_ascii=False,indent=2)
    directory=WORK/'improvement/recall_consensus_recovery_v2'
    files={'code/'+p.name:p.read_bytes() for p in directory.iterdir() if p.is_file() and p.suffix in ('.py','.md')}
    files['capacity_recovery_evidence_07.json']=(REPORT/'capacity_recovery_evidence_07.json').read_bytes()
    files['manifest.json']=json.dumps(dict(files={name:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for name,v in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'capacity_recovery_08.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,v in files.items():z.writestr(name,v)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest();assert len(data)<262144
    incoming=ROOT+'/incoming_capacity_recovery_08.zip'
    p=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=12',str(bundle),'aic-inspur-home:'+incoming],capture_output=True,text=True,timeout=60)
    if p.returncode:raise RuntimeError('Inspect outcome, do not automatically retransmit: '+p.stderr)
    receipt=remote(r'''
import datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');target=r/'recovery_v2';bundle=r/'incoming_capacity_recovery_08.zip'
assert socket.gethostname()=='inspur-NP5570M5' and not target.exists() and not (r/'fresh_recovery_registration_02.json').exists()
assert bundle.stat().st_size==__SIZE__ and hashlib.sha256(bundle.read_bytes()).hexdigest()=='__SHA__'
with zipfile.ZipFile(bundle) as z:
 assert z.testzip() is None
 m=json.loads(z.read('manifest.json'))['files'];assert set(z.namelist())==set(m)|{'manifest.json'}
 for name,row in m.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  value=z.read(name);assert len(value)==row['bytes'] and hashlib.sha256(value).hexdigest()==row['sha256']
 target.mkdir();z.extractall(target)
sys.dont_write_bytecode=True;sys.path.insert(0,str(target/'code'))
import model_common as io
original_path=r/'fresh_confirm_registration.json';original=io.read(original_path);files=dict(original['required_files'])
for p,digest in files.items():assert io.sha(p)==digest
def add(path):
 p=pathlib.Path(path);assert p.is_file() and p.is_relative_to(io.HOME_ROOT)
 digest=io.sha(p);assert str(p) not in files or files[str(p)]==digest;files[str(p)]=digest
 return dict(path=str(p),sha256=digest)
codes={}
for p in (target/'code').iterdir():
 if p.is_file() and p.suffix in ('.py','.md'):
  ref=add(p)
  if p.suffix=='.py':codes[ref['path']]=ref['sha256']
refs={}
for key,p in [('original_registration_ref',original_path),('original_input_failure_ref',r/'confirm/inputs_01/failure.json'),('original_input_launch_ref',r/'confirm/inputs_01/launch_claim.json'),('original_implementation_closure_ref',r/'confirm/inputs_01/implementation_closure.json'),('original_source_clocks_ref',r/'confirm/inputs_01/source_clocks.json'),('original_view_plan_ref',r/'confirm/inputs_01/view_plan.json'),('original_reference_pointer_ref',r/'reference_completion_confirm.json'),('original_reference_completion_ref',r/'confirm/reference_01/completion.json'),('capacity_evidence_ref',target/'capacity_recovery_evidence_07.json')]:refs[key]=add(p)
refs['processor_source_ref']=add(io.HOME_ROOT/'env/qwen3vl_isolated_20260910/lib/python3.10/site-packages/transformers/models/qwen3_vl/video_processing_qwen3_vl.py')
add(r/'fresh_control_01/failure.json');add(r/'confirm/chain_01/failure.json');add(r/'fresh_chain_launch_04.json')
reg=dict(original);reg.update(schema='RECALL_CONSENSUS_FRESH_RECOVERY_EXECUTION_V2',status='REGISTERED_EXPLICIT_FIRST_INPUT_CAPACITY_RECOVERY',
 registered_at_utc=io.utc(),required_files=files,required_code_files=codes,
 known_completed=dict(source_RGB_decode_passes=0,primary_processor_encodes=0,first_independent_input_replays=0,model_calls=0),
 no_successful_media_native_or_plan_repeated=True,scientific_protocol_unchanged=True,**refs)
io.save(r/'fresh_recovery_registration_02.json',reg)
io.fresh_gate(r,'confirm')
for name in io.JOBS.values():assert not (io.RUN/'controller'/(name+'.resource.json')).exists()
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines();assert gpu and gpu[0].strip().isdigit()
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONDONTWRITEBYTECODE='1')
python=io.HOME_ROOT/'env/qwen3vl_isolated_20260910/bin/python'
argv=[str(python),'-B','-u',str(target/'code/pilot_chain_recovery.py'),'--root',str(r),'--group','confirm']
io.save(r/'capacity_recovery_launch_claim_08.json',dict(utc=io.utc(),argv=argv,registration_sha256=io.sha(r/'fresh_recovery_registration_02.json'),parent_CUDA=env['CUDA_VISIBLE_DEVICES']))
with (r/'capacity_recovery_08.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
ticks=(pathlib.Path('/proc')/str(p.pid)/'stat').read_text().split(') ',1)[1].split()[19]
value=dict(utc=io.utc(),pid=p.pid,start_ticks=ticks,argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],bundle_bytes=__SIZE__,bundle_sha256='__SHA__',CRC_member_SHA_passed=True,
 registration_sha256=io.sha(r/'fresh_recovery_registration_02.json'),original_registration_sha256=refs['original_registration_ref']['sha256'],
 protocol_sha256=io.sha(r/'protocol.json'),media_native_success_adopted=4,original32_view_plan_adopted=True,new_model_calls_at_launch=0,production_admitted=False)
io.save(r/'capacity_recovery_launch_08.json',value);print(json.dumps(value))
'''.replace('__ROOT__',ROOT).replace('__SIZE__',str(len(data))).replace('__SHA__',digest),seconds=60)
    with (REPORT/'capacity_recovery_launch_08.json').open('x',encoding='utf8') as s:json.dump(receipt,s,ensure_ascii=False,indent=2)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
