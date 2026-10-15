"""One first independent ROLE confirmation; existing four media/clocks adopted."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from deploy_dev_02 import remote,save

REPORT=Path(__file__).resolve().parent;WORK=REPORT.parents[1]
MAIN='/home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1'
ROOT=MAIN+'/fresh_01'
PRIOR='/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1'


def main():
    assert not (REPORT/'fresh_chain_launch_09.json').exists()
    subprocess.run(['python','-B',str(REPORT/'check_fresh_controls_08.py')],check=True)
    pre=remote(r'''
import datetime as dt,hashlib,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');main=r.parent
assert socket.gethostname()=='inspur-NP5570M5'
assert not any((r/name).exists() for name in ['code','confirm','positive_fresh_registration.json','chain_launch_claim_09.json'])
assert not any((main/name).exists() for name in ['registration_confirm.json','confirm_code','incoming_fresh_chain_09.zip'])
read=lambda p:json.loads(pathlib.Path(p).read_text())
v=read(r/'reference_01/completion.json');dev=read(main/'comparison_01/result.json')
assert v['status']=='PASS_ROLE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU' and len(v['accepted'])==4 and v['actual_new_model_calls']==0
assert len(dev['conditions'])==8 and all(x is True for x in dev['conditions'].values())
assert dev['status']==read(main/'chain_01/completion.json')['status']=='PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM'
assert not (r/'reference_01/failure.json').exists()
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(main) in cmd:
   stat=(p/'stat').read_text().rsplit(')',1)[1].split()
   owned.append(dict(pid=p.name,ppid=stat[1],state=stat[0],start_ticks=stat[19],argv=cmd,io=(p/'io').read_text()))
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
    save('fresh_chain_resources_before_launch_09.json',pre)
    files={}
    for folder,prefix in [('recall_adapter_role_fresh_v1','fresh_01/code'),('recall_adapter_role_confirm_v1','confirm_code')]:
        for path in (WORK/'improvement'/folder).glob('*.py'):
            ast.parse(path.read_text(encoding='utf8'));files[prefix+'/'+path.name]=path.read_bytes()
    assert len(files)==20
    files['fresh_controls_review_08.md']=(REPORT/'fresh_controls_review_08.md').read_bytes()
    files['manifest.json']=json.dumps(dict(files={n:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for n,v in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'fresh_chain_control_09.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest();assert len(data)<262144
    sent=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',str(bundle),'aic-inspur-home:'+MAIN+'/incoming_fresh_chain_09.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:raise RuntimeError('Unknown transfer result: inspect exact remote bytes before explicit recovery: '+sent.stderr)
    value=remote(r'''
import ast,datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');main=r.parent;h=main.parent;prior=pathlib.Path('__PRIOR__')
assert socket.gethostname()=='inspur-NP5570M5' and not (r/'code').exists() and not (r/'positive_fresh_registration.json').exists()
assert not (main/'confirm_code').exists() and not (main/'registration_confirm.json').exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bundle=main/'incoming_fresh_chain_09.zip';assert bundle.stat().st_size==__BYTES__ and sha(bundle)=='__SHA__'
with zipfile.ZipFile(bundle) as z:
 assert len(z.namelist())==len(set(z.namelist())) and z.testzip() is None
 m=json.loads(z.read('manifest.json'))['files'];assert set(z.namelist())==set(m)|{'manifest.json'}
 for name,row in m.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  target=main/name;assert not target.exists(),'Never overwrite any deployed evidence'
  data=z.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 for name in m:
  target=main/name;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as stream:stream.write(z.read(name))
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'code'))
import model_common as io
from fresh_registration import registration,media_files
devreg=io.read(main/'registration.json');mediareg=io.read(r/'media_registration.json');template=io.read(prior/'registration.json')
required={}
for source in (devreg['required_files'],mediareg['required_files'],template['required_files']):
 for path,expected in source.items():
  assert path not in required or required[path]==expected,'Frozen dependency conflict'
  required[path]=expected
def add(path,expected=None):
 path=pathlib.Path(path).resolve();assert path.is_relative_to(h) and path.is_file()
 actual=sha(path);assert expected is None or actual==expected
 assert str(path) not in required or required[str(path)]==actual,'Frozen dependency changed'
 required[str(path)]=actual;return dict(path=str(path),sha256=actual)
for directory in [r/'code',main/'confirm_code',main/'code',r/'media_code']:
 for path in directory.glob('*.py'):ast.parse(path.read_text());add(path)
for path in io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG),str(io.RUNTIME)}:add(path)
for name in ['cv_contract.py','cv_tokens.py','cv_grammar.py']:add(io.CV_CODE/name)
for path in (io.RUN/'resource_unlimited_v1_20261007').glob('*.py'):add(path)
add(main/'fresh_controls_review_08.md');add(main/'official_rule_check_01.json')
refs=dict(protocol_ref=add(main/'protocol.json'),authorization_ref=add(main/'USER_AUTHORIZATION.json'),
 development_registration_ref=add(main/'registration.json'),dev_selection_ref=add(main/'selection_before_new_confirmation.json'),
 dev_result_ref=add(main/'comparison_01/result.json'),source_registration_ref=add(r/'media_registration.json'),
 reference_completion_ref=add(r/'reference_01/completion.json'),positive_template_registration_ref=add(prior/'registration.json'),
 activation_contract_ref=add(devreg['activation_contract_ref']['path'],devreg['activation_contract_ref']['sha256']),
 role_runtime_ref=add(main/'code/role_runtime.py'))
processor_source=h/'env/qwen3vl_isolated_20260910/lib/python3.10/site-packages/transformers/models/qwen3_vl/video_processing_qwen3_vl.py'
processor_ref=add(processor_source);config=io.read(io.CONFIG);now=dt.datetime.now(dt.timezone.utc)
jobs=dict(B0=dict(max_actual_calls=48,max_seconds=1800,gpu_job_name='recall_role_fresh4_b0_20261015_v1'),
 VERIFY=dict(max_actual_calls=240,max_seconds=2400,gpu_job_name='recall_role_fresh4_verify_20261015_v1'),
 POSITIVE=dict(max_actual_calls=80,max_seconds=1200,gpu_job_name='recall_role_fresh4_admission_20261015_v1'))
for row in jobs.values():assert not (io.RUN/'controller'/(row['gpu_job_name']+'.resource.json')).exists()
reg=dict(status='REGISTERED_ROLE_FIRST_FRESH_CONFIRM_V1',group='confirm',registered_at_utc=now.isoformat(),
 model_parameters=8782459120,optimizer_updates=0,source_scope='EXTERNAL_NONTEST_ONLY',reference_available_to_inference=False,
 production_admitted=False,frozen_positive_code_dir=str(main/'confirm_code'),required_files=required,
 capacity_contract=dict(video_size=config['video_size'],processor_source_path=processor_ref['path'],processor_source_sha256=processor_ref['sha256']),
 deadline=(now+dt.timedelta(hours=6)).isoformat(),gpu_budget=jobs,**refs)
io.save(r/'positive_fresh_registration.json',reg)
registration(r);_,reference=media_files(r,reg)
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert gpu and gpu[0].strip()=='0'
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'code/fresh_chain.py'),'--root',str(r),'--positive-root',str(main)]
io.save(r/'chain_launch_claim_09.json',dict(utc=io.utc(),argv=argv,registration_sha256=sha(r/'positive_fresh_registration.json'),parent_CUDA=env['CUDA_VISIBLE_DEVICES']))
with (r/'chain_09.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=io.utc(),host=socket.gethostname(),pid=p.pid,start_ticks=stat[19],argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'positive_fresh_registration.json'),
 actual_media_sources_adopted=4,actual_media_bytes_adopted=reference['actual_new_media_payload_bytes'],
 protocol_sha256=reg['protocol_ref']['sha256'],new_model_calls_at_launch=0,old_success_repeated=False,production_admitted=False,
 no_fixed40_426_or_package_started=True)
io.save(r/'chain_launch_09.json',value);print(json.dumps(value))
'''.replace('__ROOT__',ROOT).replace('__PRIOR__',PRIOR).replace('__BYTES__',str(len(data))).replace('__SHA__',digest))
    save('fresh_chain_launch_09.json',value);print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':main()
