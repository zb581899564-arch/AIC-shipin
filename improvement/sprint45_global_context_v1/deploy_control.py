"""Deploy one small control archive and launch once through the existing alias."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

BASE = Path(__file__).resolve().parent
REPORT = BASE.parents[1] / 'reports/sprint45_20261016_v1'
files = {p.name: p.read_bytes() for p in BASE.glob('*.py') if p.name != 'deploy_control.py'}
files['package_global.py'] = (BASE.parent / 'sprint45_pack_v1/package_global.py').read_bytes()
packet = io.BytesIO()
with zipfile.ZipFile(packet, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in files.items():
        z.writestr(name, data)
raw = packet.getvalue()
archive = REPORT / 'global_context_control.zip'
archive.write_bytes(raw)
expected = hashlib.sha256(raw).hexdigest()
remote = '/home/inspur/aic_video_work/incoming_sprint45_global_context_control_01.zip'
subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', str(archive),
                'aic-inspur-home:' + remote], check=True, timeout=90)
code = r'''
import ast,hashlib,json,os,pathlib,shutil,subprocess,zipfile,datetime,sys
W=pathlib.Path('/home/inspur/aic_video_work')
root=W/'sprint45_global_context_20261016_v1'
incoming=pathlib.Path(REMOTE)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
assert subprocess.check_output(['hostname']).decode().strip()=='inspur-NP5570M5'
assert sha(incoming)==EXPECTED and incoming.stat().st_size==SIZE
assert not root.exists(),'Existing root requires inspection; never duplicate launch'
with zipfile.ZipFile(incoming) as z:
 assert z.testzip() is None and set(z.namelist())==set(MEMBERS)
 for n in z.namelist():
  assert '/' not in n and '\\' not in n and hashlib.sha256(z.read(n)).hexdigest()==MEMBERS[n]
  ast.parse(z.read(n),filename=n)
 root.mkdir();(root/'code').mkdir()
 for n in z.namelist():(root/'code'/n).write_bytes(z.read(n))
sys.path.insert(0,str(root/'code'))
from global_context_common import REQUIRED_CONTROLS
run=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
adopt=W/'semantic_context_production_20261016_v1'
baseline=adopt/'package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
rules=W/'sprint45_current_official_rules_20261016_v1/official_rule_check_before_package.json'
field=W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'
history=json.loads((adopt/'production_registration.json').read_text())['historical_prediction_sha256']
template=dict(schema='SPRINT45_GLOBAL_TWO_RISK_PACKAGES_V1',offline_effect_gate_required=False,
 online_effect='UNKNOWN',actual_total_parameters=8782557449,official_rule_check=ref(rules),
 source_field_inputs=ref(field),baseline=ref(baseline),run_root=str(run),historical_canonical_sha256=history)
protocol=dict(schema='GLOBAL_LOCAL_BINARY_CONTEXT_EXPLORATION_V1',adopted_root=str(adopt),
 adopted_cpu_acceptance=ref(adopt/'cpu_acceptance.json'),adopted_metadata=ref(adopt/'metadata.json'),
 current_baseline=ref(baseline),frozen_model_config=ref(run/'b_score_aligned_package_v4/config.json'),
 controls=REQUIRED_CONTROLS,budget=dict(max_GPU_seconds=10800,queue_seconds=7200,
 new_control_cache_estimate_bytes=1073741824,no_new_decoders=True,no_new_image_processors=True),
 run_root=str(run),package_registration_template=template)
(root/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
resource=dict(host='inspur-NP5570M5',free_bytes=shutil.disk_usage(root).free,
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader']).decode().strip(),
 shared_GPU_queued=True,existing_pixels_reused=True)
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
py=W/'env/qwen3vl_isolated_20260910/bin/python'
command=[str(py),'-B','-u',str(root/'code/controller.py'),'--root',str(root)]
with (root/'stdout.log').open('xb') as out,(root/'stderr.log').open('xb') as err:
 process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,start_new_session=True)
ticks=pathlib.Path('/proc',str(process.pid),'stat').read_text().split()[21]
receipt=dict(root=str(root),pid=process.pid,start_ticks=ticks,command=command,
 deployment=dict(code_bytes=SIZE,code_sha256=EXPECTED,CRC=True,member_sha256=MEMBERS,
 protocol=ref(root/'protocol.json')),resource_plan=resource,new_fivefold=False,new_proxy_gate=False,
 UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
(root/'chain_launch.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
'''
code = 'REMOTE=' + repr(remote) + '\nEXPECTED=' + repr(expected) + '\nSIZE=' + str(len(raw)) + '\nMEMBERS=' + repr({n: hashlib.sha256(d).hexdigest() for n, d in files.items()}) + '\n' + code
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                         'aic-inspur-home', 'python3 -'], input=code, text=True,
                        capture_output=True, timeout=60)
(REPORT / 'global_context_deploy_stdout.txt').write_text(result.stdout, encoding='utf-8')
(REPORT / 'global_context_deploy_stderr.txt').write_text(result.stderr, encoding='utf-8')
print(result.stdout)
print(result.stderr)
result.check_returncode()
receipt = json.loads(result.stdout)
(REPORT / 'global_context_launch.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
