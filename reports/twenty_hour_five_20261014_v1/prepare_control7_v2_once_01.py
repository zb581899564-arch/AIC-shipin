"""Explicit failed-binder remaining recovery, preserving upstream completion."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

LOCAL = Path(__file__).resolve().parents[2]
R = '/home/inspur/aic_video_work/twenty_hour_five_20261014_v1'


def main():
    wrapper = (LOCAL / 'reports/twenty_hour_five_20261014_v1/run_cpu_finalization_control7_once_01.py').read_text()
    wrapper = wrapper.replace("ROOT = CAMPAIGN / 'cpu_finalization_control7_01'", "ROOT = CAMPAIGN / 'cpu_finalization_control7_02'")
    wrapper = wrapper.replace('temporal_family_package_bootstrap_control7_v1/', 'temporal_family_package_bootstrap_control7_v2/')
    wrapper = wrapper.replace('13a2148ce2741158f73a2ffb1a6807c3e90be63cfc3efaed2b63d664cfeeb93b',
                              '9b92209adac7ad78099405e8ee49b3271422ff0583bee510f7e3ecabf1f98b68')
    local_wrapper = LOCAL / 'reports/twenty_hour_five_20261014_v1/run_cpu_finalization_control7_v2_once_01.py'
    with local_wrapper.open('x', encoding='utf8', newline='\n') as f:
        f.write(wrapper)
    files = []
    for p in sorted((LOCAL / 'improvement/temporal_family_package_bootstrap_control7_v2').glob('*.py')):
        target = R + '/temporal_family_package_bootstrap_control7_v2/code/' + p.name
        body = p.read_bytes()
        files.append(dict(path=target, body=base64.b64encode(body).decode(), sha256=hashlib.sha256(body).hexdigest()))
    body = local_wrapper.read_bytes()
    files.append(dict(path=R + '/cpu_finalization_control7_02/run_once_01.py',
                      body=base64.b64encode(body).decode(), sha256=hashlib.sha256(body).hexdigest()))
    code = r'''
import base64,datetime as d,hashlib,json,os,pathlib,subprocess
R=pathlib.Path('__ROOT__');B=R/'temporal_family_package_bootstrap_control7_v2';W=R/'cpu_finalization_control7_02';C=R/'temporal_global_recovery_control7_v1';O=R/'cpu_finalization_control7_01'
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.flush();os.fsync(f.fileno())
assert json.loads((O/'binder/failure.json').read_text())['exit_code']!=0
assert json.loads((C/'run_01/completion.json').read_text())['status']=='PASS_CONTROL7_REMAINING_AGGREGATE_RECOVERY_NO_NEW_MODEL_OR_QA_NOT_QUALITY'
assert not B.exists() and not W.exists()
for row in __FILES__:
 p=pathlib.Path(row['path']);p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(row['body']);assert hashlib.sha256(b).hexdigest()==row['sha256'];compile(b,str(p),'exec')
 with p.open('xb') as f:f.write(b)
save(W/'registration.json',dict(schema='FAILED_BINDER_SCOPE_METADATA_REMAINING_RECOVERY_CONTROL7_V2',utc=d.datetime.now(d.timezone.utc).isoformat(),writer_ref=ref(W/'run_once_01.py'),old_failed_binder_failure_ref=ref(O/'binder/failure.json'),old_failed_binder_log_ref=ref(O/'binder/child.log'),old_failed_binder_config_path=str(R/'temporal_family_package_bootstrap_control7_v1/config_01.json'),old_failed_binder_config_sha256=ref(R/'temporal_family_package_bootstrap_control7_v1/config_01.json')['sha256'],new_model_first_QA_source_prepare_calls=0,old_successful_C7_global_not_repeated=True,old_binder_failure_preserved=True,new_projection_is_metadata_not_old_C6_completion=True))
old=R/'temporal_family_package_bootstrap_control7_v1/config_01.json';x=json.loads(old.read_text());x['schema']='TEMPORAL_FAMILY_PACKAGE_BOOTSTRAP_CONTROL7_V2';x['draft_status']='EXPLICIT_FAILED_BINDER_SCOPE_FIELD_REMAINING_RECOVERY_NO_MODELS';x['required_binder_code_files']={str(p):ref(p)['sha256'] for p in sorted((B/'code').glob('*.py'))};assert len(x['required_binder_code_files'])==4
x['additional_metadata_refs'] += [ref(W/'registration.json'),ref(O/'binder/failure.json')];x['_failed_binder_original_config_path']=str(old);x['_failed_binder_original_config_sha256']=ref(old)['sha256'];x['_old_failed_binder_not_reclassified']=True;save(B/'config_01.json',x)
argv=['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B','-u',str(W/'run_once_01.py'),'--stage','binder'];env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
with (W/'binder_wrapper.log').open('xb') as f:p=subprocess.Popen(argv,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
t=int((pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()[19]);launch=dict(pid=p.pid,start_ticks=t,argv=argv,config_ref=ref(B/'config_01.json'),utc=d.datetime.now(d.timezone.utc).isoformat());save(W/'binder_wrapper_launch.json',launch);print(json.dumps(launch))
'''.replace('__ROOT__', R).replace('__FILES__', repr(files))
    subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                    'aic-inspur-tailscale', 'python3 -B -'], input=code.encode(), check=True)


if __name__ == '__main__':
    main()
