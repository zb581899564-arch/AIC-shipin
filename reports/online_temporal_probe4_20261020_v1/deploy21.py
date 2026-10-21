"""Freeze fingerprints and deploy one bounded Linux-only four-package CPU job."""
import ast
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

H = Path(__file__).resolve().parent
WORK = H.parents[1]
items = []
for p in (WORK / 'deliveries').glob('*/*.zip'):
    try:
        with zipfile.ZipFile(p) as z:
            if z.namelist() != ['predictions.jsonl']:
                continue
            rows = [json.loads(s) for s in z.read('predictions.jsonl').splitlines() if s.strip()]
        if len(rows) != 426 or len({r['video_id'] for r in rows}) != 426:
            continue
        relevant = [{k: r[k] for k in ['video_id', 'targetRatioWH', 'predictions']}
                    for r in sorted(rows, key=lambda r: r['video_id'])]
        checksum = hashlib.sha256(json.dumps(relevant, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        items.append(dict(name=p.parent.name + '/' + p.name, canonical_sha256=checksum,
                          frames=sum(len(r['predictions']) for r in rows)))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError):
        continue
history = dict(utc=datetime.now(timezone.utc).isoformat(),
    status='PREDICTION_FINGERPRINTS_ONLY_NO_QUALITY_METRICS', packages=items)
with (H / 'history_fingerprints21.json').open('x', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
contents = {n: (H / n).read_bytes() for n in ['risk_four21.py', 'protocol21.json', 'history_fingerprints21.json']}
contents['clock_bridge19.py'] = (H.parent / 'content_choice_execution_20261020_v1/clock_bridge19.py').read_bytes()
for name, blob in contents.items():
    if name.endswith('.py'):
        ast.parse(blob)
inventory = {n: dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest()) for n, b in contents.items()}
stream = io.BytesIO()
with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, b in contents.items():
        z.writestr(n, b)
blob = stream.getvalue()
SOURCE = r'''
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,io,json,os,shutil,socket,subprocess,zipfile
W=Path('/home/inspur/aic_video_work');P=W/'content_choice_20261019_v1';R=W/'online_temporal_probe4_20261020_v1'
assert socket.gethostname()=='inspur-NP5570M5'
assert not R.exists(),'Inspect existing stage; do not redeploy or repeat'
snap=dict(utc=datetime.now(timezone.utc).isoformat(),host=socket.gethostname(),load=os.getloadavg(),
 disk_free=shutil.disk_usage(W).free,memory=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith(('MemTotal:','MemAvailable:'))],
 gpu_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True),
 task_argv=subprocess.check_output(['ps','-eo','pid,ppid,stat,args'],text=True))
assert snap['disk_free']>400000000,'Registered output estimate cannot fit, no cleanup implied'
snap['task_argv']=[s for s in snap['task_argv'].splitlines() if str(W) in s][-15:]
def ref(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,d):
 with Path(p).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
data=base64.b64decode(PAYLOAD);assert len(data)==BYTES and hashlib.sha256(data).hexdigest()==SHA
R.mkdir();code=R/'code';code.mkdir()
with (R/'incoming_control21.zip').open('xb') as f:f.write(data)
with zipfile.ZipFile(io.BytesIO(data)) as z:
 assert set(z.namelist())==set(INVENTORY) and z.testzip() is None
 for n,v in INVENTORY.items():
  assert Path(n).name==n
  b=z.read(n);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
  target=(code/n) if n.endswith('.py') else (R/n)
  with target.open('xb') as f:f.write(b)
reg=dict(utc=datetime.now(timezone.utc).isoformat(),approved=True,new_model_calls=0,new_training=0,
 code_refs={n:ref(code/n) for n in INVENTORY if n.endswith('.py')},
 protocol_ref=ref(R/'protocol21.json'),history_fingerprints_ref=ref(R/'history_fingerprints21.json'),
 production_ref=ref(P/'production_contrast/completion.json'),
 production_assets_ref=ref(P/'production_assets.private.json'),
 first_output_QA_ref=ref(P/'package_contrast/independent_production_output_qa.json'),
 critic_weights_ref=ref(P/'fit/critic_weights.json'),
 baseline_ref=ref(W/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'),
 prior_critic_stop_ref=ref(P/'review_critic/review.json'),prior_contrast_failure_score=33.33,
 risk_override='Direct human four online-probe authorization replaces quality gates only for this new prospective risk stage; old STOP and score feedback remain unchanged.',
 estimated_max_output_bytes=400000000,max_cpu_seconds=1800,resources=snap,
 local_proxy_score_runs=0,new_goal=False,new_automation=False,automatic_submission=False)
assert reg['production_ref']['sha256']=='187674f27beda310b122b2456d8bd0cdbefaceffe7a4d07e6e49e8bf7914e1a1'
assert reg['critic_weights_ref']['sha256']=='8250a44585c6cad2d51f7c49dbdf6520eeb2c86d5ad32d2e05e32792b8e2c66e'
assert reg['baseline_ref']['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
save(R/'registration21.json',reg)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
with (R/'run21.log').open('x') as log:
 p=subprocess.Popen([PYTHON,'-B',str(code/'risk_four21.py')],cwd=code,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
launch=dict(status='FOUR_RISK_CPU_PACKAGES_STARTED_NO_NEW_INFERENCE',utc=datetime.now(timezone.utc).isoformat(),pid=p.pid,start_ticks=ticks,
 registration_ref=ref(R/'registration21.json'),control_bytes=len(data),control_sha256=SHA,crc_member_sha='PASS',resources={k:v for k,v in snap.items() if k!='task_argv'})
save(R/'launch21.json',launch)
print(json.dumps(launch))
'''
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
source = '\n'.join(k + '=' + repr(v) for k, v in dict(PAYLOAD=base64.b64encode(blob).decode(),
    BYTES=len(blob), SHA=hashlib.sha256(blob).hexdigest(), INVENTORY=inventory, PYTHON=PY).items()) + '\n' + SOURCE
r = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', 'aic-inspur-tailscale', PY + ' -B -'],
    input=source, text=True, encoding='utf-8', capture_output=True, timeout=55)
with (H / 'launch_result21.json').open('x', encoding='utf-8') as f:
    json.dump(dict(exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr), f, ensure_ascii=False, indent=2)
print(r.stdout); print(r.stderr); r.check_returncode()
