"""One new same-input adapter-role dev10; no old successful execution repeated."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT=Path(__file__).resolve().parent
WORK=REPORT.parents[1]
ROOT='/home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1'
PRIOR='/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1'
SSH=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -']


def remote(code):
    value=subprocess.run(SSH,input=code,text=True,encoding='utf8',capture_output=True,timeout=90)
    if value.returncode:raise RuntimeError('Inspect retained exact state before any explicit recovery; no automatic retry: '+value.stderr[-5000:])
    return json.loads(value.stdout)


def save(name,value):
    with (REPORT/name).open('x',encoding='utf8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def main():
    assert not (REPORT/'dev_launch_02.json').exists()
    pre=remote(r'''
import datetime as dt,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');prior=pathlib.Path('__PRIOR__');h=r.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists() and not (h/'incoming_adapter_role_02.zip').exists()
read=lambda p:json.loads(pathlib.Path(p).read_text())
assert read(prior/'fresh_01/confirm/chain_02/completion.json')['status']=='STOP_POSITIVE_CONFIRM_REJECTED'
assert not (prior/'fresh_01/confirm/chain_02/failure.json').exists()
assert read(prior/'dev/POSITIVE/gpu_01/completion.json')['calls']==read(prior/'dev/POSITIVE/input_qa_01/completion.json')['calls']==read(prior/'dev/POSITIVE/output_qa_01/completion.json')['calls']==10
ac=h/'twenty_hour_five_20261014_v1/local_boundary_base_dev_v1/code/bd_contract.py'
assert ac.is_file(),'Retained proven PEFT context contract required; do not change adapter semantics'
peft=h/'env/qwen3vl_isolated_20260910/lib/python3.10/site-packages/peft/peft_model.py';assert peft.is_file()
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(r) in argv or str(prior) in argv:
   stat=(p/'stat').read_text().rsplit(')',1)[1].split();owned.append(dict(pid=p.name,ppid=stat[1],state=stat[0],start_ticks=stat[19],argv=argv,io=(p/'io').read_text()))
 except OSError:pass
assert not owned
run=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z';job='recall_base_positive_admission_dev10_20261015_v1'
assert not (run/'controller'/(job+'.resource.json')).exists() and not any(x['name']==job for x in [json.loads(y) for y in (h/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if y.strip()])
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),owned=owned,
 disk=list(shutil.disk_usage(h)),memory=pathlib.Path('/proc/meminfo').read_text(),
 tasks=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],capture_output=True,text=True,check=True).stdout.splitlines()[:20],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 unchanged_successful_inputs_adopted=10,new_input_encodes=0,new_model_call_budget=10,old_scientific_STOP_preserved=True)))
'''.replace('__ROOT__',ROOT).replace('__PRIOR__',PRIOR))
    save('resources_before_dev_02.json',pre)
    files={}
    for path in (WORK/'improvement/recall_adapter_role_v1').iterdir():
        if path.is_file() and path.suffix in ('.py','.md'):
            if path.suffix=='.py':ast.parse(path.read_text(encoding='utf8'))
            files['code/'+path.name]=path.read_bytes()
    assert len([x for x in files if x.endswith('.py')])==3
    for name in ['protocol.json','USER_AUTHORIZATION.json','official_rule_check_01.json']:files[name]=(REPORT/name).read_bytes()
    files['manifest.json']=json.dumps(dict(files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'dev_control_02.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest();assert len(data)<131072
    sent=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',str(bundle),'aic-inspur-home:'+ROOT.rsplit('/',1)[0]+'/incoming_adapter_role_02.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:raise RuntimeError('Unknown transfer outcome, inspect remote size/SHA before explicit recovery: '+sent.stderr)
    value=remote(r'''
import ast,datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');prior=pathlib.Path('__PRIOR__');h=r.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bundle=h/'incoming_adapter_role_02.zip';assert bundle.stat().st_size==__BYTES__ and sha(bundle)=='__SHA__'
with zipfile.ZipFile(bundle) as archive:
 assert len(archive.namelist())==len(set(archive.namelist())) and archive.testzip() is None
 manifest=json.loads(archive.read('manifest.json'))['files'];assert set(archive.namelist())==set(manifest)|{'manifest.json'}
 for name,row in manifest.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  data=archive.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 r.mkdir()
 for name in manifest:
  p=r/name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as stream:stream.write(archive.read(name))
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'code'))
import role_runtime as rt
oldlock=json.loads((prior/'source_lock_dev_POSITIVE.json').read_text());required=dict(oldlock['files'])
def add(p,expected=None):
 p=pathlib.Path(p).resolve();assert p.is_relative_to(h) and p.is_file()
 actual=sha(p);assert expected is None or actual==expected
 assert str(p) not in required or required[str(p)]==actual,'Adopted frozen original bytes changed'
 required[str(p)]=actual;return dict(path=str(p),sha256=actual)
for p in (r/'code').glob('*.py'):ast.parse(p.read_text());add(p)
for p in (prior/'code').glob('*.py'):add(p)
for p in [r/'USER_AUTHORIZATION.json',r/'official_rule_check_01.json',prior/'source_lock_dev_POSITIVE.json',prior/'registration.json',
          prior/'dev/POSITIVE/cpu_01/completion.json',prior/'dev/POSITIVE/gpu_01/completion.json',prior/'dev/POSITIVE/gpu_01/model_identity.json',
          prior/'dev/POSITIVE/gpu_01/attempts.jsonl',prior/'dev/POSITIVE/verification_export.json',prior/'gpu_admission_dev_POSITIVE.json',
          prior/'dev/chain_01/completion.json',prior/'fresh_01/confirm/chain_02/completion.json',prior/'confirm/comparison_01/result.json']:
 add(p)
refs=dict(protocol_ref=add(r/'protocol.json'),prior_protocol_ref=add(prior/'protocol_v2.json'),prior_result_ref=add(prior/'dev/comparison_01/result.json'),
 prior_input_QA_ref=add(prior/'dev/POSITIVE/input_qa_01/completion.json'),prior_output_QA_ref=add(prior/'dev/POSITIVE/output_qa_01/completion.json'),
 activation_contract_ref=add(h/'twenty_hour_five_20261014_v1/local_boundary_base_dev_v1/code/bd_contract.py'))
add(h/'env/qwen3vl_isolated_20260910/lib/python3.10/site-packages/peft/peft_model.py')
oldreg=json.loads((prior/'registration.json').read_text())
for name,digest in oldreg['required_files'].items():add(name,digest)
oldgate=json.loads((prior/'gpu_admission_dev_POSITIVE.json').read_text());run=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
add(run/'controller'/(oldgate['gpu_job_name']+'.resource.json'))
for p in (run/'resource_unlimited_v1_20261007').glob('*.py'):add(p)
now=dt.datetime.now(dt.timezone.utc)
reg=dict(status='REGISTERED_ADAPTER_ROLE_DEV10_SAME_INPUT_V1',group='dev',candidate=rt.CANDIDATE,activation_role=rt.ROLE,
 model_parameters=8782459120,optimizer_updates=0,reference_available_to_inference=False,production_admitted=False,fresh_confirmation_admitted=False,
 prior_root=str(prior),prior_code_dir=str(prior/'code'),required_files=required,deadline=(now+dt.timedelta(hours=3)).isoformat(),
 gpu_budget=dict(max_actual_calls=10,max_seconds=1200,gpu_job_name='recall_base_positive_admission_dev10_20261015_v1'),**refs)
with (r/'registration.json').open('x') as f:json.dump(reg,f,indent=2)
rt.registration(r)
indices=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert indices and indices[0].strip()=='0'
env=dict(os.environ,CUDA_VISIBLE_DEVICES=indices[0].strip(),PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'code/role_chain.py'),'--root',str(r)]
io=rt.modules(r)[0];io.save(r/'launch_claim_02.json',dict(utc=io.utc(),argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],registration_sha256=sha(r/'registration.json')))
with (r/'chain_02.log').open('xb') as log:parent=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(parent.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=io.utc(),host=socket.gethostname(),pid=parent.pid,start_ticks=stat[19],argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'registration.json'),protocol_sha256=refs['protocol_ref']['sha256'],
 new_call_budget=10,successful_inputs_and_first_QA_adopted=10,new_input_or_media_operations=0,activation_role=rt.ROLE,
 actual_physical_parameters=8782459120,production_admitted=False,fresh_confirmation_admitted=False,no_Goal_or_automation=True)
io.save(r/'launch_02.json',value);print(json.dumps(value))
'''.replace('__ROOT__',ROOT).replace('__PRIOR__',PRIOR).replace('__BYTES__',str(len(data))).replace('__SHA__',digest))
    save('dev_launch_02.json',value)
    print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':main()
