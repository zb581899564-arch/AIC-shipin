"""Explicit failure-only preclaim recovery; never retransfers successful metadata."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

LOCAL = Path(__file__).resolve().parents[2]
REPORT = LOCAL/'reports/twenty_hour_five_20261014_v1/critic'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15',
       '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-home']


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def main():
    raw = Path(__file__).with_name('prepare_smoke_02.py').read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    boot = r'''import hashlib,json,os,subprocess,sys
from pathlib import Path
base=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/boundary_smoke_admit_v1')
v2=base.parent/'local_boundary_v2'
sep=Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/twenty_hour_metadata_separation_01/v_fVg3StD8LL0_W000.json')
oldlog=base/'metadata_join_registration_01.log';text=oldlog.read_text()
assert "ValueError: Invalid isoformat string: '2026-10-14T11:56:40Z'" in text
assert not (base/'metadata_registration_claim_01.json').exists()
assert not sep.exists() and not (v2/'registration_smoke_input_01.json').exists() and not (v2/'plan_01').exists()
deployment=json.loads((base/'control_deployment_01.json').read_text())
assert deployment['sha256']=='7cb9e92478aafc640462146b8fd49478cf0d416a96e53a353fd38b85695684f4'
raw=sys.stdin.buffer.read();assert len(raw)==SCRIPT_BYTES and hashlib.sha256(raw).hexdigest()==SCRIPT_SHA
path=base/'code/prepare_smoke_02.py'
with path.open('xb') as f:f.write(raw)
claim={'status':'EXPLICIT_PRECLAIM_DATETIME_PARSE_RECOVERY_ONLY','old_log_sha256':hashlib.sha256(oldlog.read_bytes()).hexdigest(),
 'original_control_sha256':deployment['sha256'],'new_script_bytes':len(raw),'new_script_sha256':SCRIPT_SHA,
 'metadata_transferred_again':False,'old_script_preserved':True,'previous_join_calls':0,'previous_plan_calls':0}
with (base/'recovery_02.json').open('x') as f:json.dump(claim,f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
with (base/'metadata_join_registration_02.log').open('xb') as log:
 r=subprocess.run([PYTHON_BIN,'-B',str(path)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env)
if r.returncode:
 failure=json.loads((base/'failure_02.json').read_text()) if (base/'failure_02.json').exists() else {'error':'failed before claim'}
 print(json.dumps({'recovery':claim,'failure':failure,'returncode':r.returncode}));sys.exit(r.returncode)
print(json.dumps({'recovery':claim,'completion':json.loads((base/'completion_02.json').read_text())}))
'''
    boot = boot.replace('SCRIPT_BYTES', str(len(raw))).replace('SCRIPT_SHA', repr(digest)).replace('PYTHON_BIN', repr(PY))
    result = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(boot)],input=raw,capture_output=True)
    if result.returncode:
        save(REPORT/'boundary_smoke_failure_02.json',dict(returncode=result.returncode,
            stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace')))
        raise RuntimeError('Explicit recovery failed; retain all partials, no automatic retry')
    receipt = json.loads(result.stdout)
    save(REPORT/'boundary_smoke_completion_02.json',receipt)
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    main()
