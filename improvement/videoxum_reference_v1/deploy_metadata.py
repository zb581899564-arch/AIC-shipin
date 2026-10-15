"""One independent, small-control deployment and CPU-only metadata launch."""
import hashlib
import io
import json
import shlex
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/videoxum_reference_iteration_20261013_v1'
REMOTE = '/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o',
       'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', 'aic-inspur-home']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    files = {'code/metadata_stage.py': Path(__file__).parent / 'metadata_stage.py',
             'code/reference_intervals.py': Path(__file__).parent / 'reference_intervals.py'}
    for name in ('PROTOCOL.md', 'metadata_registration_01.json', 'known_source_exclusions_01.json',
                 'reference_admission_01.json'):
        files[name] = REPORT / name
    manifest = {name: {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                for name, p in files.items()}
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for name, path in files.items():
            out.writestr(name, path.read_bytes())
        out.writestr('manifest.json', json.dumps(manifest, indent=2))
    raw = archive.getvalue()
    with (REPORT / 'metadata_control_01.zip').open('xb') as stream:
        stream.write(raw)
    code = '''import datetime,hashlib,io,json,os,socket,subprocess,sys,zipfile
from pathlib import Path
base=Path(REMOTE)
assert socket.gethostname()=='inspur-NP5570M5'
assert not base.exists(),'Independent root already exists; inspect rather than repeat launch'
raw=sys.stdin.buffer.read()
assert len(raw)==SIZE and hashlib.sha256(raw).hexdigest()==DIGEST
archive=zipfile.ZipFile(io.BytesIO(raw))
assert archive.testzip() is None
manifest=json.loads(archive.read('manifest.json'))
assert set(archive.namelist())==set(manifest)|{'manifest.json'}
for name,item in manifest.items():
 target=base/name
 assert target.resolve().is_relative_to(base.resolve())
 data=archive.read(name)
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
base.mkdir()
for name in manifest:
 target=base/name
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(archive.read(name))
receipt={'status':'PASS_NEW_METADATA_SMALL_CONTROL_BYTES_SHA_CRC_MEMBERS','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'members':manifest,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (base/'control_deployment_01.json').open('x') as f:json.dump(receipt,f,indent=2)
with (base/'metadata_launch_claim_01.json').open('x') as f:json.dump({'utc':receipt['utc'],'argv':[PY,'-B',str(base/'code/metadata_stage.py')],'CUDA_VISIBLE_DEVICES':'','new_model_calls':0},f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
log=(base/'metadata_stage_01.log').open('xb')
p=subprocess.Popen([PY,'-B',str(base/'code/metadata_stage.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
launch={'status':'ONE_CPU_METADATA_STAGE_LAUNCHED_NOT_ACCEPTANCE','pid':p.pid,'argv':[PY,'-B',str(base/'code/metadata_stage.py')],'utc':receipt['utc'],'control_sha256':receipt['sha256'],'new_model_calls':0}
with (base/'metadata_launch_01.json').open('x') as f:json.dump(launch,f,indent=2)
print(json.dumps({'transfer':receipt,'launch':launch}))
'''
    code = code.replace('REMOTE', repr(REMOTE)).replace('SIZE', str(len(raw))).replace('DIGEST', repr(sha(raw)))
    # PY is a literal placeholder in this private deployment script, not an environment variable.
    code = code.replace('PY', repr(PY))
    result = subprocess.run(SSH + [PY + ' -B -c ' + shlex.quote(code)], input=raw,
                            capture_output=True, check=True)
    receipt = json.loads(result.stdout)
    assert receipt['transfer']['members'] == manifest
    assert receipt['transfer']['sha256'] == sha(raw)
    with (REPORT / 'control_deployment_01.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    state_path = REPORT / 'current_state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state.update(stage='AUTHOR_METADATA_DOWNLOAD_CPU_STAGE_RUNNING',
                 remote_base=REMOTE, unique_metadata_launch='metadata_launch_01.json',
                 small_control_transfer='control_deployment_01.json',
                 updated_utc=receipt['launch']['utc'])
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'transfer_bytes': len(raw), 'transfer_sha256': sha(raw), 'launch': receipt['launch']}))


if __name__ == '__main__':
    main()
