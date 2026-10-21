"""Small authorized SSH control deployment; no media or model transfer."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

H = Path(__file__).resolve().parent
names = ['clock_bridge19.py', 'render_remaining19.py', 'run_package_remaining19.py']
contents = {name: (H / name).read_bytes() for name in names}
for payload in contents.values():
    ast.parse(payload)
stream = io.BytesIO()
with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, payload in contents.items():
        archive.writestr(name, payload)
blob = stream.getvalue()
inventory = {name: dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
             for name, payload in contents.items()}

SOURCE = r'''
from pathlib import Path
from datetime import datetime, timezone
import base64,hashlib,io,json,os,shutil,socket,subprocess,zipfile
R=Path('/home/inspur/aic_video_work/content_choice_20261019_v1');W=R.parent
assert socket.gethostname()=='inspur-NP5570M5'
assert json.loads((R/'user_resume_01.json').read_text())['explicit_human_resume'] is True
assert not (R/'package_remaining_registration19.json').exists()
assert not (R/'package_contrast_remaining_controller_started19.json').exists()
assert (R/'package_contrast_controller_failure09.json').exists()
assert not (R/'package_contrast_controller_completion09.json').exists()
def ref(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,d):
 with Path(p).open('x') as f:json.dump(d,f,indent=2)
code=base64.b64decode(PAYLOAD);assert len(code)==BYTES and hashlib.sha256(code).hexdigest()==SHA
snap=dict(host=socket.gethostname(),utc=datetime.now(timezone.utc).isoformat(),load=os.getloadavg(),
 disk_free=shutil.disk_usage(R).free,memory=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith(('MemTotal:','MemAvailable:'))],
 gpu_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip())
assert not snap['gpu_apps']
# About100MB expected composition output, comfortably below live1.4GB; no fixed machine admission line.
assert snap['disk_free']>len(code)
archive=R/'incoming_package_remaining19.zip'
with archive.open('xb') as f:f.write(code)
dest=R/'package_recovery19';dest.mkdir(exist_ok=False)
with zipfile.ZipFile(io.BytesIO(code)) as z:
 assert set(z.namelist())==set(INVENTORY) and z.testzip() is None
 for n,v in INVENTORY.items():
  assert Path(n).name==n
  b=z.read(n);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
  with (dest/n).open('xb') as f:f.write(b)
refs={n:ref(dest/n) for n in INVENTORY}
reg=dict(approved=True,scope='REMAINING_CPU_COMPOSITION_ONLY_EXACT_FRAME_CLOCK_COMPATIBILITY',
 utc=datetime.now(timezone.utc).isoformat(),source_count=426,window_count=522,
 production_ref=ref(R/'production_contrast/completion.json'),production_assets_ref=ref(R/'production_assets.private.json'),
 original_failure_ref=ref(R/'package_contrast/failure.json'),
 successful_output_QA_ref=ref(R/'package_contrast/independent_production_output_qa.json'),
 successful_field_domain_ref=ref(R/'package_contrast/rendered/field_eligibility.json'),
 original_package_admission_ref=ref(R/'package_contrast.admission.json'),
 clock_diagnosis_ref=ref(R/'clock_interface_diagnosis18.json'),execution_code_refs=refs,resources=snap,
 change='Require all426 original exact native PTS arrays identical and every selected frame inside both bound endpoint domains. Keep both actual terminal policies unchanged and explicitly report eleven differences. No per-source overrides, no epsilon, no selected frame edits, no field extension. The original stronger full-endpoint-equality failure stays FAILED.',
 adoption='Reuse the first successful all522 token/input/native/source decision QA and field-domain PASS; no replays or model calls repeated. First remaining composition/11strict/ZIP only.',
 new_models=0,new_decode=0,successful_replay_repeated=0,baseline_40_47_unchanged=True,
 max_seconds=1800,automatic_website_submission=False)
assert reg['production_ref']['sha256']=='187674f27beda310b122b2456d8bd0cdbefaceffe7a4d07e6e49e8bf7914e1a1'
save(R/'package_remaining_registration19.json',reg)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(R/'code'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (R/'package_remaining19.log').open('x') as log:
 p=subprocess.Popen([PYTHON,'-B',str(dest/'run_package_remaining19.py')],cwd=R/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
launch=dict(status='EXPLICIT_REMAINING_CPU_PACKAGE19_STARTED',utc=datetime.now(timezone.utc).isoformat(),pid=p.pid,start_ticks=ticks,registration_ref=ref(R/'package_remaining_registration19.json'),deployment=dict(bytes=len(code),sha256=SHA,members=len(INVENTORY),crc_member_sha='PASS'),resources=snap)
save(R/'package_remaining_launch19.json',launch)
print(json.dumps(launch))
'''
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
source = '\n'.join(key + '=' + repr(value) for key, value in dict(
    PAYLOAD=base64.b64encode(blob).decode(), BYTES=len(blob),
    SHA=hashlib.sha256(blob).hexdigest(), INVENTORY=inventory, PYTHON=PY).items()) + '\n' + SOURCE
result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', 'aic-inspur-tailscale', PY + ' -B -'],
                        input=source, text=True, capture_output=True, timeout=55)
with (H / 'package_remaining_launch_result19.json').open('x', encoding='utf-8') as f:
    json.dump(dict(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr), f, ensure_ascii=False, indent=2)
print(result.stdout)
print(result.stderr)
result.check_returncode()
