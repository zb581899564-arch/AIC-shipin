"""Deploy one small new code bundle and launch one independently registered dev chain.

Never overwrites/retries an existing deployment or launcher. All prior computation
is adopted read-only. Large inputs, model and evidence remain on Linux.
"""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

WORK = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
HOME = '/home/inspur/aic_video_work'
ROOT = HOME+'/recall_positive_admission_verify40_46_20261015_v1'
PRIOR = HOME+'/recall_expansion_verify40_46_20261014_v1'
NAME = 'recall_positive_novelparts_dev10_20261015_v1'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=10',
       '-o', 'ServerAliveCountMax=2', 'aic-inspur-home', 'python3 -']


def remote(code, seconds=60):
    value = subprocess.run(SSH, input=code, text=True, encoding='utf8',
                           capture_output=True, timeout=seconds)
    if value.returncode:
        raise RuntimeError('Inspect and retain remote state before any explicit recovery: '+value.stderr[-6000:])
    return json.loads(value.stdout)


def save(name, value):
    with (REPORT/name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def main():
    assert not (REPORT/'deployment_launch_04.json').exists()
    pre = remote(r'''
import datetime as dt,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');h=r.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
assert not (h/'incoming_positive_admission_dev_04.zip').exists()
assert not (h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/__JOB__.resource.json').exists()
ps=subprocess.run(['ps','-eo','pid,ppid,stat,args','--width','4000'],capture_output=True,text=True,check=True).stdout
assert not any(str(r) in line for line in ps.splitlines())
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),
 disk=list(shutil.disk_usage(h)),meminfo=pathlib.Path('/proc/meminfo').read_text(),
 processes=ps,gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 static_capacity_threshold_applied=False)))
'''.replace('__ROOT__', ROOT).replace('__JOB__', NAME))
    save('deployment_preflight_04.json', pre)
    # Actual estimated extra output is prompt tokens and small evidence, not a
    # new RGB/model copy. A shared GPU lock remains the only launcher authority.
    # The operator reviews actual external tasks and this workload's observed
    # peak; an empty app list is not a permanent resource-admission threshold.
    assert pre['host'] == 'inspur-NP5570M5'
    directory = WORK/'improvement/recall_positive_admission_v1'
    files = {}
    for path in directory.iterdir():
        if path.is_file() and path.suffix in ('.py', '.md'):
            if path.suffix == '.py':
                ast.parse(path.read_text(encoding='utf8'))
            files['code/'+path.name] = path.read_bytes()
    assert {'code/positive_chain.py','code/positive_contract.py','code/positive_io.py',
            'code/positive_runtime.py','code/positive_evaluate.py'} <= set(files)
    for name in ('protocol_v2.json', 'USER_AUTHORIZATION.json', 'official_rule_check_01.json',
                 'reference_candidates.json', 'reference_review.md', 'novel_visibility_inventory_03.json'):
        files[name] = (REPORT/name).read_bytes()
    manifest = {name:dict(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
                for name, value in files.items()}
    files['manifest.json'] = json.dumps(dict(files=manifest), sort_keys=True).encode()
    bundle = REPORT/'dev_control_04.zip'
    with zipfile.ZipFile(bundle, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    data = bundle.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    incoming = HOME+'/incoming_positive_admission_dev_04.zip'
    sent = subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
        '-o','ConnectTimeout=10',str(bundle),'aic-inspur-home:'+incoming],
        capture_output=True,text=True,timeout=60)
    if sent.returncode:
        raise RuntimeError('SCP result unknown; inspect exact remote file before any explicit recovery: '+sent.stderr)
    result = remote(r'''
import ast,datetime as dt,hashlib,importlib.util,json,os,pathlib,socket,subprocess,sys,zipfile
h=pathlib.Path('__HOME__');r=pathlib.Path('__ROOT__');old=pathlib.Path('__PRIOR__')
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
incoming=h/'incoming_positive_admission_dev_04.zip'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert incoming.stat().st_size==__BYTES__ and sha(incoming)=='__SHA__'
with zipfile.ZipFile(incoming) as z:
 assert len(set(z.namelist()))==len(z.namelist()) and z.testzip() is None
 m=json.loads(z.read('manifest.json'))['files'];assert set(z.namelist())==set(m)|{'manifest.json'}
 for name,row in m.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  value=z.read(name);assert len(value)==row['bytes'] and hashlib.sha256(value).hexdigest()==row['sha256']
 r.mkdir();z.extractall(r)
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'code'))
import positive_io as io
required={}
def ref(path):
 path=pathlib.Path(path).resolve();assert path.is_relative_to(h) and path.is_file()
 value=sha(path);required[str(path)]=value
 return dict(path=str(path),sha256=value)
legacy_ref=ref(old/'code/model_common.py')
spec=importlib.util.spec_from_file_location('_deploy_positive_legacy',legacy_ref['path']);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
for path in legacy.runtime_dependencies()|legacy.processor_assets()|{str(legacy.CONFIG)}:ref(path)
for path in (legacy.RUN/'resource_unlimited_v1_20261007').glob('*.py'):ref(path)
for path in (r/'code').glob('*.py'):ast.parse(path.read_text());ref(path)
protocol_ref=ref(r/'protocol_v2.json');auth_ref=ref(r/'USER_AUTHORIZATION.json')
for name in ['official_rule_check_01.json','reference_candidates.json','reference_review.md','novel_visibility_inventory_03.json']:ref(r/name)
token_ref=ref(legacy.CV_CODE/'cv_tokens.py');ref(legacy.CV_CODE/'cv_contract.py')
metrics_ref=ref(old/'code/evaluate_pilot.py')
cohort=dict(prior_root=str(old),prior_group='dev',source_names=['v_vfJnUQ9Tax0','v_8tlLBffNjf8','v__CMIO5R_OGA','v_voaGOm-rl9Y'],
 old_cpu_admission=ref(old/'cpu_acceptance_dev.json'),
 old_b0=dict(admission=ref(old/'gpu_admission_dev_B0.json'),gpu_completion=ref(old/'dev/B0/gpu_01/completion.json'),replay_completion=ref(old/'dev/B0/replay_01/completion.json')),
 old_verify=dict(admission=ref(old/'gpu_admission_dev_VERIFY.json'),gpu_completion=ref(old/'dev/VERIFY/gpu_01/completion.json'),replay_completion=ref(old/'dev/VERIFY/replay_01/completion.json'),export=ref(old/'dev/VERIFY/verification_export.json')),
 reference_completion=ref(old/'reference_completion_dev.json'))
now=dt.datetime.now(dt.timezone.utc)
reg=dict(status='REGISTERED_POSITIVE_ADMISSION_V1',stage_group='dev',registered_at_utc=now.isoformat(),
 baseline_sha256='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543',model_parameters=8782459120,
 source_scope='EXTERNAL_NONTEST_ONLY',reference_available_to_inference=False,optimizer_updates=0,production_admitted=False,
 protocol_ref=protocol_ref,authorization_ref=auth_ref,legacy_model_common_ref=legacy_ref,legacy_token_module_ref=token_ref,
 proxy_metrics_ref=metrics_ref,required_files=required,adopted_source_groups=dict(dev=[cohort]),
 gpu_budget=dict(dev=dict(max_actual_calls=10,max_seconds=1200,gpu_job_name='__JOB__',deadline=(now+dt.timedelta(hours=2)).isoformat())))
io.save(r/'registration.json',reg)
io.registration(r,'dev')
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert gpu and gpu[0].strip()=='0'
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'code/positive_chain.py'),'--root',str(r),'--group','dev']
io.save(r/'chain_launch_claim_04.json',dict(utc=io.utc(),argv=argv,registration_ref=io.ref(r/'registration.json'),parent_CUDA=env['CUDA_VISIBLE_DEVICES']))
with (r/'chain_04.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=io.utc(),host=socket.gethostname(),pid=p.pid,start_ticks=stat[19],argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'registration.json'),
 protocol_sha256=protocol_ref['sha256'],old_B0_adopted=26,old_VERIFY_adopted=37,new_candidate_denominator=10,
 production_admitted=False,new_model_calls_at_launch=0,old_success_repeated=False)
io.save(r/'chain_launch_04.json',value);print(json.dumps(value))
'''.replace('__HOME__',HOME).replace('__ROOT__',ROOT).replace('__PRIOR__',PRIOR)
        .replace('__BYTES__',str(len(data))).replace('__SHA__',digest).replace('__JOB__',NAME), seconds=60)
    save('deployment_launch_04.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
