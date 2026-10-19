"""One CPU packaging deployment; uses completed width and existing global job."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'reports/sprint45_20261016_v1'
members = {p.name: p.read_bytes() for p in HERE.glob('*.py') if p.name != 'deploy_control.py'}
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, content in members.items():
        archive.writestr(name, content)
payload = buffer.getvalue()
packet = REPORT / 'width_package_control.zip'
packet.write_bytes(payload)
digest = hashlib.sha256(payload).hexdigest()
remote = '/home/inspur/aic_video_work/incoming_sprint45_width_package_control_01.zip'
subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', str(packet),
                'aic-inspur-home:' + remote], check=True, timeout=90)
code = r'''
import ast,datetime,hashlib,json,os,pathlib,shutil,subprocess,zipfile
W=pathlib.Path('/home/inspur/aic_video_work');root=W/'sprint45_width_packages_20261016_v1'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
assert subprocess.check_output(['hostname']).decode().strip()=='inspur-NP5570M5'
incoming=pathlib.Path(REMOTE)
assert sha(incoming)==EXPECTED and incoming.stat().st_size==SIZE
assert not root.exists(),'Existing package root: inspect, never duplicate launch'
width=W/'sprint45_native16_width_production_20261016_v1'
assert json.loads((width/'chain_completion.json').read_text())['status']=='PASS_NATIVE16_WIDTH_MODEL_OUTPUTS_READY_FOR_ENGINEERING_PACK'
run=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
adopt=W/'semantic_context_production_20261016_v1'
with zipfile.ZipFile(incoming) as z:
 assert z.testzip() is None and set(z.namelist())==set(MEMBERS)
 for n in z.namelist():
  assert '/' not in n and '\\' not in n and hashlib.sha256(z.read(n)).hexdigest()==MEMBERS[n]
  ast.parse(z.read(n),filename=n)
 root.mkdir();(root/'code').mkdir()
 for n in z.namelist():(root/'code'/n).write_bytes(z.read(n))
training=W/'sprint45_spatial_width602_20261016_v1'
field=W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'
rules=W/'sprint45_current_official_rules_20261016_v1/official_rule_check_before_package.json'
scoring=run/'baseline_a_pts_v1/vendor/frozen_strict_loader/aic6/scoring.py'
history=json.loads((adopt/'production_registration.json').read_text())['historical_prediction_sha256']
template=dict(schema='SPRINT45_WIDTH_TWO_RISK_PACKAGES_V1',offline_effect_gate_required=False,
 online_effect='UNKNOWN',actual_total_parameters=8782590234,official_rule_check=ref(rules),
 baseline=ref(adopt/'package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'),source_field_inputs=ref(field),
 width_head=ref(training/'fit/final_head.pt'),width_normalization=ref(training/'fit/normalization.npz'),
 native_apply_module=ref(width/'code/native_apply.py'),native_apply_dependency=ref(width/'code/prod_common.py'),
 run_root=str(run),frozen_strict_loader_scoring_sha256=sha(scoring),historical_canonical_sha256=history)
registration=dict(width_root=str(width),global_root=str(W/'sprint45_global_context_20261016_v1'),
 max_wait_seconds=21600,package_registration_template=template)
(root/'controller_registration.json').write_text(json.dumps(registration,indent=2)+'\n')
resource=dict(host='inspur-NP5570M5',disk_free_bytes=shutil.disk_usage(root).free,
 memory_available=[l for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')][0],
 load=pathlib.Path('/proc/loadavg').read_text().strip(),CPU_only=True,new_model_calls=0)
py=W/'env/qwen3vl_isolated_20260910/bin/python';env=os.environ.copy()
env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
command=[str(py),'-B','-u',str(root/'code/controller.py'),'--root',str(root)]
with (root/'stdout.log').open('xb') as out,(root/'stderr.log').open('xb') as err:
 p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,start_new_session=True)
receipt=dict(root=str(root),pid=p.pid,start_ticks=pathlib.Path('/proc',str(p.pid),'stat').read_text().split()[21],
 command=command,code_bytes=SIZE,code_sha256=EXPECTED,member_sha256=MEMBERS,CRC=True,
 registration=ref(root/'controller_registration.json'),resource=resource,
 UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
(root/'chain_launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
code = 'REMOTE=' + repr(remote) + '\nEXPECTED=' + repr(digest) + '\nSIZE=' + str(len(payload)) + '\nMEMBERS=' + repr({n: hashlib.sha256(d).hexdigest() for n, d in members.items()}) + '\n' + code
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                         'aic-inspur-home', 'python3 -'], input=code, text=True,
                        capture_output=True, timeout=60)
(REPORT / 'width_package_deploy_stdout.txt').write_text(result.stdout, encoding='utf-8')
(REPORT / 'width_package_deploy_stderr.txt').write_text(result.stderr, encoding='utf-8')
print(result.stdout)
print(result.stderr)
result.check_returncode()
(REPORT / 'width_package_launch.json').write_text(json.dumps(json.loads(result.stdout), ensure_ascii=False, indent=2), encoding='utf-8')
