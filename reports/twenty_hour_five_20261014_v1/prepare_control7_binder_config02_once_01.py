"""Remaining correction of JSON-list typing, retaining the failed config."""
import base64
import hashlib
from pathlib import Path
import subprocess

LOCAL = Path(__file__).resolve().parents[2]


def main():
    p = LOCAL / 'reports/twenty_hour_five_20261014_v1/run_cpu_finalization_control7_v2_once_01.py'
    code = p.read_text().replace("ROOT = CAMPAIGN / 'cpu_finalization_control7_02'", "ROOT = CAMPAIGN / 'cpu_finalization_control7_03'")
    code = code.replace('temporal_family_package_bootstrap_control7_v2/config_01.json',
                        'temporal_family_package_bootstrap_control7_v2/config_02.json')
    new = p.with_name('run_cpu_finalization_control7_config02_once_01.py')
    with new.open('x', encoding='utf8', newline='\n') as f:
        f.write(code)
    b = new.read_bytes()
    remote = r'''
import base64,hashlib,json,os,pathlib,subprocess,datetime as d
R=pathlib.Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1');B=R/'temporal_family_package_bootstrap_control7_v2';W=R/'cpu_finalization_control7_03';O=R/'cpu_finalization_control7_02';P=R/'temporal_family_native_package_v3'
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.flush();os.fsync(f.fileno())
assert json.loads((O/'binder/failure.json').read_text())['exit_code']!=0
assert all(not (P/n).exists() for n in ['history.json','package_inputs.json','technical_preparation_receipt.json','source_package_lock.json','package_admission.json'])
W.mkdir(exist_ok=False);b=base64.b64decode('__BODY__');assert hashlib.sha256(b).hexdigest()=='__SHA__';p=W/'run_once_01.py';compile(b,str(p),'exec');p.write_bytes(b)
save(W/'registration.json',dict(schema='FAILED_JSON_METADATA_LIST_TYPE_REMAINING_CONFIG_RECOVERY_V1',writer_ref=ref(p),old_failure_ref=ref(O/'binder/failure.json'),old_failure_log_ref=ref(O/'binder/child.log'),old_config_path=str(B/'config_01.json'),old_config_sha256=ref(B/'config_01.json')['sha256'],configurator_code_ref=ref(R/'temporal_family_package_bootstrap_control7_v1/configurator_01.py'),code_identity_still_bound=True,new_model_or_QA_calls=0,old_successes_not_repeated=True,change='Remove .py from JSON-only list; bind exact .py through this retained JSON reference instead'))
x=json.loads((B/'config_01.json').read_text());bad=[v for v in x['additional_metadata_refs'] if pathlib.Path(v['path']).suffix!='.json'];assert len(bad)==1 and bad[0]['path']==str(R/'temporal_family_package_bootstrap_control7_v1/configurator_01.py')
x['additional_metadata_refs']=[v for v in x['additional_metadata_refs'] if pathlib.Path(v['path']).suffix=='.json'];x['additional_metadata_refs'].append(ref(W/'registration.json'));x['_explicit_failed_json_list_type_recovery']=True;save(B/'config_02.json',x)
argv=['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B','-u',str(W/'run_once_01.py'),'--stage','binder']
with (W/'binder_wrapper.log').open('xb') as f:p=subprocess.Popen(argv,cwd=R,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
t=int((pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()[19]);v=dict(pid=p.pid,start_ticks=t,argv=argv,config_ref=ref(B/'config_02.json'),utc=d.datetime.now(d.timezone.utc).isoformat());save(W/'binder_wrapper_launch.json',v);print(json.dumps(v))
'''.replace('__BODY__', base64.b64encode(b).decode()).replace('__SHA__', hashlib.sha256(b).hexdigest())
    subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                    'aic-inspur-tailscale', 'python3 -B -'], input=remote.encode(), check=True)


if __name__ == '__main__':
    main()
