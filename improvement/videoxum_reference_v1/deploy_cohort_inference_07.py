"""One waiting original-B controller with the actual current GPU index."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

from deploy_direct_media_05 import REPORT, REMOTE, PY, ssh_script, fresh_host_snapshot
from stage_common_04 import sha, utc


def main():
    if (REPORT/'cohort_inference_registration_07.json').exists():
        raise ValueError('Inference registration already exists; inspect, never duplicate launch')
    snapshot=fresh_host_snapshot('cohort_inference_host_resources_07.json')
    gpu_rows=[x.split(',') for x in snapshot['gpu'].splitlines() if x.strip()]
    if not gpu_rows:raise ValueError('No actual visible GPU index')
    gpu_index=gpu_rows[0][0].strip()
    if not gpu_index.isdigit():raise ValueError('Actual GPU index is not verifiable')
    prior_name='human_summe20_original_b_native64_20261013_v1'
    prior_path='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/'+prior_name+'.resource.json'
    evidence=ssh_script('import json,pathlib,hashlib\np=pathlib.Path('+repr(prior_path)+')\nb=p.read_bytes();print(json.dumps({"resource":json.loads(b),"sha256":hashlib.sha256(b).hexdigest()}))')
    if evidence['resource']['status']!='completed' or evidence['resource']['exit_code'] or evidence['resource']['name']!=prior_name:
        raise ValueError('Prior original B budget evidence not completed')
    files={}
    for name in ('cohort_run_common_07.py','admit_cohort_inputs_07.py','infer_cohort_07.py','replay_cohort_07.py','chain_cohort_07.py'):
        files['code/'+name]=Path(__file__).parent/name
    implementations={REMOTE+'/'+name:sha(path) for name,path in files.items()}
    for name in ('stage_common_04.py','native_profile_01.py','native_profile_04.py','prepare_media_batch_06.py'):
        implementations[REMOTE+'/code/'+name]=sha(Path(__file__).parent/name)
    for name in ('direct_cohort_registration_06.json','FOLLOWUP_PROTOCOL_02.md','NATIVE_MAPPING_CONTRACT_03.md','PROFILE_SCOPE_ADDENDUM_03.md'):
        implementations[REMOTE+'/'+name]=sha(REPORT/name)
    reg=dict(status='REGISTERED20_ORIGINAL_B_ONCE_AFTER_ALL_NATIVE_CPU_GATES',utc=utc(),sources=20,
        unique_gpu_name='videoxum20_original_b_native64_20261013_v1',implementation_files=implementations,
        model_parameters=8782459120,new_optimizer_updates=0,new_training=False,
        candidate='L16',baseline='D8_USER_REPORTED40.44',reference_labels_available_to_model=False,
        prior_gpu_name=prior_name,prior_resource_path=prior_path,prior_resource_sha256=evidence['sha256'],
        prior_cost_seconds=evidence['resource']['charged_seconds'],prior_windows=116,queue_seconds=3600,
        actual_parent_CUDA_VISIBLE_DEVICES=gpu_index,CPU_children_CUDA_VISIBLE_DEVICES='',
        actual_call_budget='Exactly actual registered CPU-accepted window count, frozen before first B answer',
        duplicate_successful_calls_forbidden=True,requires_source_lock_and_unique_shared_gpu_wrapper=True,
        all20_independent_CPU_review_before_GPU=True,independent_full_CPU_replay_after_GPU=True)
    p=REPORT/'cohort_inference_registration_07.json';p.write_text(json.dumps(reg,indent=2),encoding='utf-8');files[p.name]=p
    manifest={name:dict(bytes=path.stat().st_size,sha256=sha(path)) for name,path in files.items()}
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name,path in files.items():z.writestr(name,path.read_bytes())
        z.writestr('manifest.json',json.dumps(manifest,indent=2))
    raw=archive.getvalue()
    with (REPORT/'cohort_inference_control_07.zip').open('xb') as stream:stream.write(raw)
    script='''import datetime,hashlib,io,json,os,pathlib,socket,subprocess,sys,zipfile
b=pathlib.Path(REMOTE);assert socket.gethostname()=='inspur-NP5570M5'
assert not (b/'cohort_inference_launch_claim_07.json').exists()
raw=sys.stdin.buffer.read();assert len(raw)==SIZE and hashlib.sha256(raw).hexdigest()==DIGEST
z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m)|{'manifest.json'}
for name,item in m.items():
 p=b/name;assert p.resolve().is_relative_to(b.resolve())
 data=z.read(name);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
for name in m:
 p=b/name
 if not p.exists():
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(z.read(name))
reg=json.loads((b/'cohort_inference_registration_07.json').read_text())
for path,digest in reg['implementation_files'].items():assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==digest
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert reg['actual_parent_CUDA_VISIBLE_DEVICES'] in [x.strip() for x in gpu]
ledger=pathlib.Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
assert not any(json.loads(x)['name']==reg['unique_gpu_name'] for x in ledger.read_text().splitlines() if x.strip())
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'members':m}
argv=[PY,'-B',str(b/'code/chain_cohort_07.py')]
with (b/'cohort_inference_launch_claim_07.json').open('x') as f:json.dump({'utc':receipt['utc'],'argv':argv,'parent_CUDA':reg['actual_parent_CUDA_VISIBLE_DEVICES']},f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=reg['actual_parent_CUDA_VISIBLE_DEVICES']
log=(b/'cohort_inference_chain_07.log').open('xb')
p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
launch={'utc':receipt['utc'],'pid':p.pid,'argv':argv,'status':'ONE_REGISTERED_PARENT_WAITING_ORIGINAL_CPU_GATES_NOT_GPU_RESULT'}
with (b/'cohort_inference_launch_07.json').open('x') as f:json.dump({'transfer':receipt,'launch':launch},f,indent=2)
print(json.dumps({'transfer':receipt,'launch':launch}))'''
    script=script.replace('REMOTE',repr(REMOTE)).replace('SIZE',str(len(raw))).replace('DIGEST',repr(hashlib.sha256(raw).hexdigest())).replace('PY',repr(PY))
    receipt=ssh_script(script,raw)
    if receipt['transfer']['sha256']!=hashlib.sha256(raw).hexdigest() or receipt['transfer']['members']!=manifest:
        raise ValueError('Actual registered inference control transfer changed')
    with (REPORT/'cohort_inference_control_deployment_07.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    print(json.dumps({'control_bytes':len(raw),'actual_parent_GPU_index':gpu_index,'launch':receipt['launch']}))


if __name__=='__main__':main()
