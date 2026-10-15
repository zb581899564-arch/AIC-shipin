"""Authorized one small-code deployment; launch CPU metadata once, no media."""
import hashlib
import io
import json
import shlex
import subprocess
import zipfile
from pathlib import Path

LOCAL = Path(__file__).resolve().parents[2]
REPORT = LOCAL/'reports/twenty_hour_five_20261014_v1/critic'
SCOPE = LOCAL/'reports/twenty_hour_five_20261014_v1/charades_metadata_protocol_01.json'
CODE = Path(__file__).with_name('metadata_index.py')
REMOTE = '/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o',
       'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2', 'aic-inspur-home']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    scope_raw = SCOPE.read_bytes()
    protocol = json.loads(scope_raw.decode('utf-8-sig'))
    assert protocol['approved'] and protocol['scope'] == 'CHARADES_METADATA_AND_ARCHIVE_DIRECTORY_ONLY'
    assert protocol['root'] == REMOTE and not protocol['media_bodies_authorized_in_this_stage']
    assert not protocol['new_GPU_authorized_in_this_stage']
    protocol['script_sha256'] = sha(CODE.read_bytes())
    protocol['parent_scope_protocol_sha256'] = sha(scope_raw)
    protocol['max_annotation_expanded_bytes'] = 256 << 20
    frozen = REPORT/'charades_metadata_protocol_frozen_01.json'
    save(frozen, protocol)
    files = {'code/metadata_index.py': CODE, 'metadata_protocol_01.json': frozen,
             'charades_http_01.json': REPORT/'charades_http_01.json'}
    assert sha(files['charades_http_01.json'].read_bytes()) == protocol['http_receipt_sha256']
    members = {name:dict(bytes=path.stat().st_size, sha256=sha(path.read_bytes())) for name,path in files.items()}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name,path in files.items():
            archive.writestr(name, path.read_bytes())
        archive.writestr('manifest.json', json.dumps(members, sort_keys=True))
    raw = buffer.getvalue()
    control = REPORT/'charades_metadata_control_01.zip'
    with control.open('xb') as stream:
        stream.write(raw)
    boot = r'''import datetime,hashlib,io,json,os,shutil,socket,subprocess,sys,zipfile
from pathlib import Path
base=Path(REMOTE_ROOT)
assert socket.gethostname()=='inspur-NP5570M5'
assert not base.exists(),'New root already exists: inspect, never repeat deployment'
raw=sys.stdin.buffer.read()
assert len(raw)==CONTROL_BYTES and hashlib.sha256(raw).hexdigest()==CONTROL_SHA
archive=zipfile.ZipFile(io.BytesIO(raw));assert archive.testzip() is None
manifest=json.loads(archive.read('manifest.json'))
assert set(archive.namelist())==set(manifest)|{'manifest.json'}
for name,item in manifest.items():
 target=base/name
 assert target.resolve().is_relative_to(base.resolve())
 data=archive.read(name)
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
protocol=json.loads(archive.read('metadata_protocol_01.json'))
assert protocol['approved'] and protocol['scope']=='CHARADES_METADATA_AND_ARCHIVE_DIRECTORY_ONLY'
assert not protocol['media_bodies_authorized_in_this_stage'] and not protocol['new_GPU_authorized_in_this_stage']
assert protocol['script_sha256']==manifest['code/metadata_index.py']['sha256']
disk=shutil.disk_usage(base.parent)
assert disk.free>protocol['max_metadata_payload_bytes']+protocol['max_annotation_expanded_bytes']
resources={'hostname':socket.gethostname(),'load_average':os.getloadavg(),'disk_free_bytes':disk.free}
resources['memory']=Path('/proc/meminfo').read_text().splitlines()[:6]
resources['active_processes']=subprocess.run(['ps','-eo','pid,ppid,pcpu,pmem,comm','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:21]
gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True)
resources['gpu_readonly']={'returncode':gpu.returncode,'stdout':gpu.stdout.strip()}
base.mkdir()
for name in manifest:
 target=base/name;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(archive.read(name))
utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt={'status':'PASS_UNIQUE_CHARADES_METADATA_SMALL_CONTROL_CRC_SIZE_SHA_MEMBERS','utc':utc,'control_bytes':len(raw),'control_sha256':hashlib.sha256(raw).hexdigest(),'members':manifest,'resources':resources,'scope':protocol['scope']}
with (base/'control_deployment_01.json').open('x') as f:json.dump(receipt,f,indent=2)
argv=[PYTHON_BIN,'-B',str(base/'code/metadata_index.py'),'--root',str(base)]
with (base/'metadata_launch_claim_01.json').open('x') as f:json.dump({'argv':argv,'utc':utc,'protocol_sha256':manifest['metadata_protocol_01.json']['sha256'],'media_downloads':0,'new_model_calls':0},f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
log=(base/'metadata_run_01.log').open('xb')
p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
launch={'status':'ONE_CPU_METADATA_AND_ZIP64_INDEX_LAUNCHED_NOT_ACCEPTANCE','pid':p.pid,'argv':argv,'utc':utc,'new_model_calls':0,'media_downloads':0}
with (base/'metadata_launch_01.json').open('x') as f:json.dump(launch,f,indent=2)
print(json.dumps({'transfer':{k:v for k,v in receipt.items() if k!='resources'},'resource_snapshot_saved':True,'launch':launch}))
'''
    boot = boot.replace('REMOTE_ROOT', repr(REMOTE)).replace('CONTROL_BYTES', str(len(raw)))
    boot = boot.replace('CONTROL_SHA', repr(sha(raw))).replace('PYTHON_BIN', repr(PY))
    outcome = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(boot)], input=raw, capture_output=True)
    if outcome.returncode:
        save(REPORT/'charades_metadata_deployment_failure_01.json',
             dict(returncode=outcome.returncode, stdout=outcome.stdout.decode(errors='replace'),
                  stderr=outcome.stderr.decode(errors='replace'), control_bytes=len(raw), control_sha256=sha(raw),
                  repeated_deployment=False))
        raise RuntimeError('Remote deployment failed; preserve local control and diagnose before recovery')
    result = json.loads(outcome.stdout)
    assert result['transfer']['control_sha256'] == sha(raw) and result['transfer']['members'] == members
    save(REPORT/'charades_metadata_deployment_01.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
