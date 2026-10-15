"""Unique authorized small-control deployment, metadata join and pure plan only."""
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import zipfile

LOCAL = Path(__file__).resolve().parents[2]
REPORT = LOCAL/'reports/twenty_hour_five_20261014_v1/critic'
REMOTE = '/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/boundary_smoke_admit_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o',
       'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2', 'aic-inspur-home']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    files = {
        'code/prepare_smoke.py': Path(__file__).with_name('prepare_smoke.py'),
        'historical_provenance/frozen_test_identity_catalog.json':
            LOCAL/'reports/boundary_refinement_20261012_v1/input_01/metadata.json',
        'historical_provenance/existing_runtime_readonly_01.json':
            LOCAL/'reports/human_reference_iteration_20261013_v1/existing_runtime_readonly_01.json',
        'historical_provenance/existing_runtime_dependency_followup_01.json':
            LOCAL/'reports/human_reference_iteration_20261013_v1/existing_runtime_dependency_followup_01.json'}
    snapshot = json.loads((LOCAL/'reports/human_reference_iteration_20261013_v1/known_identity_snapshot_01.json').read_text())
    expected = ['frozen_test_identity_catalog_sha256', 'current_remote_readonly_receipt_sha256', 'dependency_followup_sha256']
    for path, field in zip(list(files.values())[1:], expected):
        assert digest(path.read_bytes()) == snapshot[field]
    members = {name: dict(bytes=path.stat().st_size, sha256=digest(path.read_bytes()))
               for name, path in files.items()}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in files.items():
            archive.writestr(name, path.read_bytes())
        archive.writestr('manifest.json', json.dumps(members, sort_keys=True))
    payload = stream.getvalue()
    with (REPORT/'boundary_smoke_control_01.zip').open('xb') as output:
        output.write(payload)
    boot = r'''import hashlib,io,json,os,shutil,socket,subprocess,sys,zipfile
from pathlib import Path
base=Path(REMOTE_ROOT)
assert socket.gethostname()=='inspur-NP5570M5'
assert not base.exists(),'Control already deployed: inspect rather than repeat'
raw=sys.stdin.buffer.read()
assert len(raw)==PAYLOAD_BYTES and hashlib.sha256(raw).hexdigest()==PAYLOAD_SHA
archive=zipfile.ZipFile(io.BytesIO(raw));assert archive.testzip() is None
manifest=json.loads(archive.read('manifest.json'))
assert set(archive.namelist())==set(manifest)|{'manifest.json'}
for name,item in manifest.items():
 target=base/name;assert target.resolve().is_relative_to(base.resolve())
 data=archive.read(name)
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
resources={'hostname':socket.gethostname(),'load_average':os.getloadavg(),'disk_available_bytes':shutil.disk_usage(base.parent).free,
 'memory':Path('/proc/meminfo').read_text().splitlines()[:6],
 'peers':subprocess.run(['ps','-eo','pid,ppid,pcpu,pmem,comm','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:15]}
base.mkdir()
for name in manifest:
 target=base/name;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(archive.read(name))
deployment={'status':'PASS_SMALL_CONTROL_CRC_SIZE_SHA_MEMBERS_NOT_MODEL_ADMISSION','bytes':len(raw),
 'sha256':hashlib.sha256(raw).hexdigest(),'members':manifest,'resources':resources}
with (base/'control_deployment_01.json').open('x') as f:json.dump(deployment,f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
argv=[PYTHON_BIN,'-B',str(base/'code/prepare_smoke.py')]
with (base/'metadata_join_registration_01.log').open('xb') as log:
 result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env)
if result.returncode:
 failure=json.loads((base/'failure_01.json').read_text()) if (base/'failure_01.json').exists() else {'error':'script failed before claim'}
 print(json.dumps({'control_bytes':len(raw),'control_sha256':hashlib.sha256(raw).hexdigest(),'metadata_join_failed':failure,'returncode':result.returncode}))
 sys.exit(result.returncode)
print(json.dumps({'control_bytes':len(raw),'control_sha256':hashlib.sha256(raw).hexdigest(),
 'completion':json.loads((base/'completion_01.json').read_text())}))
'''
    boot = boot.replace('REMOTE_ROOT', repr(REMOTE)).replace('PAYLOAD_BYTES', str(len(payload)))
    boot = boot.replace('PAYLOAD_SHA', repr(digest(payload))).replace('PYTHON_BIN', repr(PY))
    result = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(boot)], input=payload, capture_output=True)
    if result.returncode:
        save(REPORT/'boundary_smoke_failure_01.json', dict(returncode=result.returncode,
            stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'),
            control_bytes=len(payload), control_sha256=digest(payload), repeated=False))
        raise RuntimeError('Unique metadata/plan stage failed; inspect partials before recovery')
    receipt = json.loads(result.stdout)
    assert receipt['control_bytes'] == len(payload) and receipt['control_sha256'] == digest(payload)
    save(REPORT/'boundary_smoke_completion_01.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
