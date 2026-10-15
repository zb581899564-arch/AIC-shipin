"""One first-confirmation chain, after the actual fixed4 media/native PASS."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT=Path(__file__).resolve().parent
WORK=REPORT.parents[1]
MAIN='/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1'
ROOT=MAIN+'/fresh_01'
SSH=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
     '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -']


def remote(code):
    p=subprocess.run(SSH,input=code,text=True,encoding='utf8',capture_output=True,timeout=90)
    if p.returncode:raise RuntimeError('Inspect exact retained state, never retry a launcher blindly: '+p.stderr[-5000:])
    return json.loads(p.stdout)


def save(name,value):
    with (REPORT/name).open('x',encoding='utf8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def main():
    assert not (REPORT/'fresh_chain_launch_15.json').exists()
    pre=remote(r'''
import datetime as dt,hashlib,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');main=r.parent
assert socket.gethostname()=='inspur-NP5570M5'
assert not any((r/name).exists() for name in ['code','confirm','positive_fresh_registration.json','incoming_fresh_chain_15.zip'])
assert not (main/'registration_confirm.json').exists()
v=json.loads((r/'reference_01/completion.json').read_text())
assert v['status']=='PASS_POSITIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU' and len(v['accepted'])==4 and v['actual_new_model_calls']==0
assert not (r/'reference_01/failure.json').exists()
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(r) in cmd:owned.append(dict(pid=p.name,argv=cmd))
 except OSError:pass
assert not owned
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),owned=owned,
 disk=list(shutil.disk_usage(r)),memory=pathlib.Path('/proc/meminfo').read_text(),
 tasks=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],capture_output=True,text=True,check=True).stdout.splitlines()[:20],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 accepted_ids=[x['video_id'] for x in v['accepted']],media_bytes=v['actual_new_media_payload_bytes'],
 reference_completion_sha256=hashlib.sha256((r/'reference_01/completion.json').read_bytes()).hexdigest())))
'''.replace('__ROOT__',ROOT))
    save('fresh_chain_resources_before_launch_15.json',pre)
    directory=WORK/'improvement/recall_positive_fresh_v1'
    files={}
    for path in directory.iterdir():
        if path.is_file() and path.suffix in ('.py','.md'):
            if path.suffix=='.py':ast.parse(path.read_text(encoding='utf8'))
            files['code/'+path.name]=path.read_bytes()
    assert {'code/fresh_chain.py','code/fresh_registration.py','code/model_common.py','code/prepare_inputs.py',
            'code/first_input_qa.py','code/pilot_runtime.py','code/pilot_verify.py','code/verify_input_qa.py'}<=set(files)
    files['fresh_reference_registration_review_07.md']=(REPORT/'fresh_reference_registration_review_07.md').read_bytes()
    files['manifest.json']=json.dumps(dict(files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'fresh_chain_control_15.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest();assert len(data)<262144
    sent=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        str(bundle),'aic-inspur-home:'+ROOT+'/incoming_fresh_chain_15.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:raise RuntimeError('Transfer outcome unknown; inspect remote size/SHA before explicit recovery: '+sent.stderr)
    value=remote(r'''
import ast,datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');main=r.parent;h=main.parent
assert socket.gethostname()=='inspur-NP5570M5' and not (r/'code').exists() and not (r/'positive_fresh_registration.json').exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bundle=r/'incoming_fresh_chain_15.zip';assert bundle.stat().st_size==__BYTES__ and sha(bundle)=='__SHA__'
with zipfile.ZipFile(bundle) as z:
 assert len(z.namelist())==len(set(z.namelist())) and z.testzip() is None
 m=json.loads(z.read('manifest.json'))['files'];assert set(z.namelist())==set(m)|{'manifest.json'}
 for name,row in m.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  target=r/name;assert not target.exists(),'Never overwrite a deployed file'
  data=z.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 for name in m:
  target=r/name;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as stream:stream.write(z.read(name))
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'code'))
import model_common as io
from fresh_registration import registration,media_files
devreg=io.read(main/'registration.json');mediareg=io.read(r/'media_registration.json')
required=dict(devreg['required_files']);required.update(mediareg['required_files'])
def add(path,expected=None):
 path=pathlib.Path(path).resolve();assert path.is_relative_to(h) and path.is_file()
 actual=sha(path);assert expected is None or actual==expected
 assert str(path) not in required or required[str(path)]==actual,'Frozen dependency changed'
 required[str(path)]=actual;return dict(path=str(path),sha256=actual)
for path in (r/'code').glob('*.py'):ast.parse(path.read_text());add(path)
for path in (main/'code').glob('*.py'):add(path)
for path in (r/'media_code').glob('*.py'):add(path)
for path in io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG),str(io.RUNTIME)}:add(path)
for name in ['cv_contract.py','cv_tokens.py','cv_grammar.py']:add(io.CV_CODE/name)
for path in (io.RUN/'resource_unlimited_v1_20261007').glob('*.py'):add(path)
add(r/'fresh_reference_registration_review_07.md');add(main/'official_rule_check_01.json')
refs=dict(protocol_ref=add(main/'protocol_v2.json'),authorization_ref=add(main/'USER_AUTHORIZATION.json'),
 development_registration_ref=add(main/'registration.json'),dev_selection_ref=add(main/'dev/selection_before_confirmation.json'),
 dev_result_ref=add(main/'dev/comparison_01/result.json'),source_registration_ref=add(r/'media_registration.json'),
 reference_completion_ref=add(r/'reference_01/completion.json'))
processor_source=h/'env/qwen3vl_isolated_20260910/lib/python3.10/site-packages/transformers/models/qwen3_vl/video_processing_qwen3_vl.py'
processor_ref=add(processor_source);config=io.read(io.CONFIG)
now=dt.datetime.now(dt.timezone.utc)
jobs=dict(B0=dict(max_actual_calls=48,max_seconds=1800,gpu_job_name='recall_positive_fresh4_b0_20261015_v1'),
 VERIFY=dict(max_actual_calls=240,max_seconds=2400,gpu_job_name='recall_positive_fresh4_verify_20261015_v1'),
 POSITIVE=dict(max_actual_calls=80,max_seconds=1200,gpu_job_name='recall_positive_fresh4_admission_20261015_v1'))
for row in jobs.values():assert not (io.RUN/'controller'/(row['gpu_job_name']+'.resource.json')).exists()
reg=dict(status='REGISTERED_POSITIVE_FIRST_FRESH_CONFIRM_V1',group='confirm',registered_at_utc=now.isoformat(),
 model_parameters=8782459120,optimizer_updates=0,source_scope='EXTERNAL_NONTEST_ONLY',reference_available_to_inference=False,
 production_admitted=False,frozen_positive_code_dir=str(main/'code'),required_files=required,
 capacity_contract=dict(video_size=config['video_size'],processor_source_path=processor_ref['path'],processor_source_sha256=processor_ref['sha256']),
 deadline=(now+dt.timedelta(hours=6)).isoformat(),gpu_budget=jobs,**refs)
io.save(r/'positive_fresh_registration.json',reg)
registration(r);_,reference=media_files(r,reg)
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert gpu and gpu[0].strip()=='0'
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'code/fresh_chain.py'),'--root',str(r),'--positive-root',str(main)]
io.save(r/'chain_launch_claim_15.json',dict(utc=io.utc(),argv=argv,registration_sha256=sha(r/'positive_fresh_registration.json'),parent_CUDA=env['CUDA_VISIBLE_DEVICES']))
with (r/'chain_15.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=io.utc(),host=socket.gethostname(),pid=p.pid,start_ticks=stat[19],argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'positive_fresh_registration.json'),
 actual_media_sources_adopted=4,actual_media_bytes_adopted=reference['actual_new_media_payload_bytes'],
 protocol_sha256=reg['protocol_ref']['sha256'],new_model_calls_at_launch=0,old_success_repeated=False,production_admitted=False,
 no_fixed40_426_or_package_started=True)
io.save(r/'chain_launch_15.json',value);print(json.dumps(value))
'''.replace('__ROOT__',ROOT).replace('__BYTES__',str(len(data))).replace('__SHA__',digest))
    save('fresh_chain_launch_15.json',value)
    print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':main()
