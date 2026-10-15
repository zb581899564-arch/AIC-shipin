"""New bounded source stage after frozen actual role dev PASS; no model call."""
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
    assert not (REPORT/'fresh_media_launch_07.json').exists()
    pre=remote(r'''
import datetime as dt,json,pathlib,shutil,socket,subprocess
main=pathlib.Path('__MAIN__');r=pathlib.Path('__ROOT__');prior=pathlib.Path('__PRIOR__')
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists() and not (main/'incoming_fresh_media_07.zip').exists()
read=lambda p:json.loads(pathlib.Path(p).read_text())
result=read(main/'comparison_01/result.json');chain=read(main/'chain_01/completion.json');selection=read(main/'selection_before_new_confirmation.json')
assert result['status']==chain['status']=='PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM'
assert len(result['cases'])==4 and len(result['conditions'])==8 and all(x is True for x in result['conditions'].values())
assert selection['status']=='PASS_ROLE_DEV_FROZEN_REQUIRES_NEW_UNEXPOSED_CONFIRMATION' and selection['new_confirm_metrics_examined'] is False
assert not (main/'chain_01/failure.json').exists()
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(main) in argv:
   stat=(p/'stat').read_text().rsplit(')',1)[1].split();owned.append(dict(pid=p.name,ppid=stat[1],state=stat[0],start_ticks=stat[19],argv=argv,io=(p/'io').read_text()))
 except OSError:pass
assert not owned
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),actual_dev_complete_PASS=True,
 owned=owned,disk=list(shutil.disk_usage(main)),memory=pathlib.Path('/proc/meminfo').read_text(),
 tasks=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],capture_output=True,text=True,check=True).stdout.splitlines()[:15],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 registered_selected_media_bytes=17756735,registered_maximum_pool_bytes=23841657,Windows_video_body_bytes=0)))
'''.replace('__MAIN__',MAIN).replace('__ROOT__',ROOT).replace('__PRIOR__',PRIOR))
    save('fresh_media_resources_07.json',pre)
    code=WORK/'improvement/recall_adapter_role_fresh_media_v1/role_media.py';ast.parse(code.read_text(encoding='utf8'))
    files={'media_code/role_media.py':code.read_bytes(),
        'source_candidates.json':(REPORT/'fresh_source_candidates_05.json').read_bytes(),
        'public_routes.json':(REPORT/'fresh_public_routes_06.json').read_bytes(),
        'existing_dependency_refs.json':(WORK/'reports/recall_positive_admission_verify40_46_20261015_v1/fresh_existing_dependency_refs_11.json').read_bytes()}
    files['manifest.json']=json.dumps(dict(files={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'fresh_media_control_07.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,value in files.items():z.writestr(name,value)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest();assert len(data)<131072
    sent=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',str(bundle),'aic-inspur-home:'+MAIN+'/incoming_fresh_media_07.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:raise RuntimeError('Inspect unknown transfer outcome before explicit recovery: '+sent.stderr)
    value=remote(r'''
import datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
main=pathlib.Path('__MAIN__');r=pathlib.Path('__ROOT__');prior=pathlib.Path('__PRIOR__');h=main.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bundle=main/'incoming_fresh_media_07.zip';assert bundle.stat().st_size==__BYTES__ and sha(bundle)=='__SHA__'
with zipfile.ZipFile(bundle) as z:
 assert len(z.namelist())==len(set(z.namelist())) and z.testzip() is None
 manifest=json.loads(z.read('manifest.json'))['files'];assert set(z.namelist())==set(manifest)|{'manifest.json'}
 for name,row in manifest.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  data=z.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 r.mkdir()
 for name in manifest:
  p=r/name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as stream:stream.write(z.read(name))
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'media_code'));import role_media as m
deps=m.read(r/'existing_dependency_refs.json');required={}
def add(path,expected=None):
 p=pathlib.Path(path).resolve();assert p.is_relative_to(h) and p.is_file()
 actual=sha(p);assert expected is None or expected==actual
 assert str(p) not in required or required[str(p)]==actual
 required[str(p)]=actual;return dict(path=str(p),sha256=actual)
refs=dict(protocol_ref=add(main/'protocol.json'),authorization_ref=add(main/'USER_AUTHORIZATION.json'),
 development_result_ref=add(main/'comparison_01/result.json'),development_selection_ref=add(main/'selection_before_new_confirmation.json'),
 development_chain_ref=add(main/'chain_01/completion.json'),development_registration_ref=add(main/'registration.json'),
 source_candidates_ref=add(r/'source_candidates.json'),public_routes_ref=add(r/'public_routes.json'),
 annotation_file_ref=add(deps['annotation_file_path'],deps['annotation_file_sha256']),known_exclusions_ref=add(deps['known_exclusions_path'],deps['known_exclusions_sha256']),
 media_helper_ref=add(prior/'fresh_01/media_code/positive_media.py','831f4d3e0da2a9351a172b080157622bcfc5debd12444df60e047ff04f6818eb'))
add(r/'media_code/role_media.py');add(r/'existing_dependency_refs.json');add(main/'official_rule_check_01.json')
for ref in deps['native_profile_refs']:add(ref['path'],ref['sha256'])
scopes=[add(ref['path'],ref['sha256']) for ref in deps['source_scope_refs']]
prior_refs=[add(ref['path'],ref['sha256']) for ref in deps['all14_media_receipts']]
positive_media=m.read(prior/'fresh_01/reference_01/completion.json')
for row in positive_media['accepted']:prior_refs.append(add(pathlib.Path(row['media']['path']).parent/'media_receipt.json'))
assert len(prior_refs)==18 and len({x['path'] for x in prior_refs})==18
candidate=m.read(r/'source_candidates.json')
gate=m.read(main/'gpu_admission.json');add(main/'gpu_01/completion.json');add(main/'output_qa_01/completion.json')
resourcep=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(gate['gpu_job_name']+'.resource.json');resource=m.read(resourcep);add(resourcep)
ledger=[json.loads(x) for x in (h/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
assert resource['status']=='completed' and resource['exit_code']==0 and [x for x in ledger if x['name']==gate['gpu_job_name']]==[resource]
reg=dict(schema='ROLE_FIRST_FRESH_MEDIA_REGISTRATION_V1',status='REGISTERED_ROLE_FIRST_FRESH_MEDIA_NATIVE',group='confirm',registered_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 expected_accepted_sources=4,maximum_media_pool_bytes=23841657,windows_video_body_bytes=0,production_admitted=False,
 selection=candidate['selection'],ordered_engineering_reserves=candidate['ordered_engineering_reserves'],required_files=required,
 prior18_media_receipts=prior_refs,source_scope_refs=scopes,purpose='NONCOMMERCIAL_STUDENT_PRIVATE_RESEARCH_ONLY',public_author_to_Linux_route_continuously_authorized=True,**refs)
with (r/'media_registration.json').open('x') as f:json.dump(reg,f,indent=2)
m.registration(r)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'media_code/role_media.py'),'--root',str(r)]
with (r/'media_claim_07.json').open('x') as f:json.dump(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),argv=argv,registration_sha256=sha(r/'media_registration.json')),f,indent=2)
with (r/'media_07.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),pid=p.pid,start_ticks=stat[19],argv=argv,
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'media_registration.json'),
 selected_media_bytes=17756735,maximum_pool_bytes=23841657,Windows_video_body_bytes=0,new_model_calls=0,production_admitted=False)
with (r/'media_launch_07.json').open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
'''.replace('__MAIN__',MAIN).replace('__ROOT__',ROOT).replace('__PRIOR__',PRIOR).replace('__BYTES__',str(len(data))).replace('__SHA__',digest))
    save('fresh_media_launch_07.json',value);print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':main()
