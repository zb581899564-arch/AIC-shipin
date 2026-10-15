"""Deploy once after a fresh host/resource snapshot; never relaunch index or GPU."""
import io
import json
import shlex
import subprocess
import zipfile
from pathlib import Path

from stage_common_04 import sha, utc

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/videoxum_reference_iteration_20261013_v1'
REMOTE = '/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o',
       'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', 'aic-inspur-home']


def ssh_script(script, raw=None):
    result = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(script)], input=raw,
                            capture_output=True, check=True)
    return json.loads(result.stdout)


def main():
    if (REPORT/'media_batch_01_control_deployment.json').exists() or (REPORT/'media_batch_registration_01.json').exists():
        raise ValueError('Batch registration/deployment exists; inspect actual state, do not relaunch')
    script = '''import pathlib,json,os,socket,subprocess,shutil
base=pathlib.Path(REMOTE)
assert socket.gethostname()=='inspur-NP5570M5'
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  args=[a.decode() for a in (p/'cmdline').read_bytes().split(b'\\0') if a]
  if any(a.startswith(str(base)+'/code/') for a in args):owned.append({'pid':int(p.name),'argv':args})
 except (OSError,UnicodeError):pass
print(json.dumps({'hostname':socket.gethostname(),'cpu_count':os.cpu_count(),'load':os.getloadavg(),
 'memory':pathlib.Path('/proc/meminfo').read_text(),'disk':list(shutil.disk_usage(base)),
 'jobs':subprocess.run(['ps','-eo','pid,ppid,pcpu,pmem,args','--sort=-pcpu'],capture_output=True,text=True).stdout[:20000],
 'gpu':subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True).stdout,
 'actual_owned_commands':owned,
 'index_state':json.loads((base/'archive_index_01/state.json').read_text()),
 'media_launch_exists':(base/'media_batch_01_launch_claim.json').exists()}))'''.replace('REMOTE', repr(REMOTE))
    live = ssh_script(script)
    if live['media_launch_exists']:
        raise ValueError('Remote batch already claimed; inspect rather than duplicate')
    # The current scope has only two small located members; no GPU or parallel heavy CPU child.
    sources = read_local('metadata_export_01/metadata_02/source_registration_01.json')['selection']
    found = live['index_state']['members_found']
    members = [{'video_id': row['video_id'], 'member': found[row['video_id']]}
               for row in sources if row['video_id'] in found]
    if not members:
        raise ValueError('No located frozen members')
    with (REPORT/'media_batch_01_host_resources.json').open('x', encoding='utf-8') as stream:
        json.dump(live, stream, indent=2)
    scope = dict(status='PRIVATE_PUBLIC_DATASET_RESEARCH_ACCESS_SCOPE_NOT_VIDEO_COPYRIGHT_TRANSFER',
        registered_utc=utc(), purpose='PRIVATE_EXTERNAL_REFERENCE_VALIDATION_NO_TRAINING_OR_MEDIA_REDISTRIBUTION',
        human_route_authorization='允许直接从linux下载，以后不要问我，你这个路线除外',
        annotation_license='Author VideoXum Apache-2.0 annotation only',
        media_origin='ActivityNet public YouTube source IDs; community HF archive pinned revision',
        author_research_access_source='http://activity-net.org/download.html',
        mirror_source='https://huggingface.co/datasets/friedrichor/ActivityNet_Captions',
        mirror_revision='aaaa81b07a7417e3b1ad7ad0eb588ee7960d4c92',
        media_blanket_license_verified=False, media_redistribution_permitted=False,
        exact_author_original_byte_identity_verified=False,
        judgment='Small private research acquisition for identity/native-clock validation; public hosting is not a blanket copyright license.',
        access_credentials_or_restriction_bypass=False, new_model_calls=0, new_training=False,
        downstream_quality_or_submission_admission=False,
        primary_source_evidence_index_sha256=sha(REPORT/'primary_source_evidence_index_01.json'))
    scope_path = REPORT/'media_use_scope_04.json'
    scope_path.write_text(json.dumps(scope, ensure_ascii=False, indent=2), encoding='utf-8')
    files = {'media_use_scope_04.json': scope_path}
    for name in ('stage_common_04.py','native_profile_01.py','native_profile_04.py',
                 'download_media_batch_04.py','prepare_media_batch_04.py','media_native_batch_chain_04.py'):
        files['code/'+name] = Path(__file__).parent/name
    for name in ('FOLLOWUP_PROTOCOL_02.md','NATIVE_MAPPING_CONTRACT_03.md','PROFILE_SCOPE_ADDENDUM_03.md'):
        files[name] = REPORT/name
    manifest = {name:dict(bytes=path.stat().st_size, sha256=sha(path)) for name,path in files.items()}
    required = {name:item['sha256'] for name,item in manifest.items()}
    required.update({'metadata_02/source_registration_01.json':sha(REPORT/'metadata_export_01/metadata_02/source_registration_01.json'),
                     'metadata_03/selected_human_references_01.json':sha(REPORT/'metadata_export_01/metadata_03/selected_human_references_01.json'),
                     'known_source_exclusions_01.json':sha(REPORT/'known_source_exclusions_01.json')})
    index_reg = read_local('archive_index_registration_01.json')
    reg = dict(status='REGISTERED_LOCATED_MEMBERS_MEDIA_AND_CPU_PREPARATION_ONLY', utc=utc(),
        source_registration_sha256=required['metadata_02/source_registration_01.json'],
        media_use_scope_sha256=required['media_use_scope_04.json'],
        exclusions_sha256=required['known_source_exclusions_01.json'],
        routes_path=REMOTE+'/archive_part_redirects_01.json', routes_sha256=index_reg['normal_CDN_routes_sha256'],
        regular_part_bytes=index_reg['regular_part_bytes'], part_etags=live['index_state']['part_etags'],
        index_snapshot_sha256=sha(REPORT/'media_batch_01_host_resources.json'),
        members=members, total_member_bytes=sum(row['member']['member_bytes'] for row in members),
        output_directory='media_batch_01', cpu_directory='cpu_batch_01', chain_directory='media_native_chain_01',
        required_files=required, full_part_download=False, all20_GPU_gate_unchanged=True,
        new_model_calls=0, new_optimizer_updates=0)
    reg_path = REPORT/'media_batch_registration_01.json'
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding='utf-8')
    files['media_batch_registration_01.json'] = reg_path
    manifest['media_batch_registration_01.json'] = dict(bytes=reg_path.stat().st_size, sha256=sha(reg_path))
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name,path in files.items():z.writestr(name,path.read_bytes())
        z.writestr('manifest.json',json.dumps(manifest,indent=2))
    raw = archive.getvalue()
    archive_path = REPORT/'media_batch_01_control.zip'
    with archive_path.open('xb') as stream:stream.write(raw)
    deploy = '''import datetime,hashlib,io,json,os,pathlib,socket,subprocess,sys,zipfile
base=pathlib.Path(REMOTE)
assert socket.gethostname()=='inspur-NP5570M5'
assert not (base/'media_batch_01_launch_claim.json').exists()
raw=sys.stdin.buffer.read()
assert len(raw)==SIZE and hashlib.sha256(raw).hexdigest()==DIGEST
z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
manifest=json.loads(z.read('manifest.json'))
assert set(z.namelist())==set(manifest)|{'manifest.json'}
for name,item in manifest.items():
 target=base/name;assert target.resolve().is_relative_to(base.resolve())
 data=z.read(name);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
 if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256'],'Never overwrite an existing different stage file'
for name in manifest:
 target=base/name
 if not target.exists():
  target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(z.read(name))
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'members':manifest}
with (base/'media_batch_01_control_deployment.json').open('x') as f:json.dump(receipt,f,indent=2)
argv=[PY,'-B',str(base/'code/media_native_batch_chain_04.py'),str(base/'media_batch_registration_01.json')]
with (base/'media_batch_01_launch_claim.json').open('x') as f:json.dump({'utc':receipt['utc'],'argv':argv,'new_model_calls':0},f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
log=(base/'media_native_chain_01.log').open('xb')
p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
launch={'utc':receipt['utc'],'pid':p.pid,'argv':argv,'status':'ONE_CPU_MEDIA_BATCH_CHAIN_LAUNCHED_NOT_ACCEPTANCE'}
with (base/'media_batch_01_launch.json').open('x') as f:json.dump(launch,f,indent=2)
print(json.dumps({'transfer':receipt,'launch':launch}))'''
    import hashlib
    deploy = deploy.replace('REMOTE',repr(REMOTE)).replace('SIZE',str(len(raw))).replace('DIGEST',repr(hashlib.sha256(raw).hexdigest())).replace('PY',repr(PY))
    receipt = ssh_script(deploy, raw)
    if receipt['transfer']['members'] != manifest or receipt['transfer']['sha256'] != sha(archive_path):
        raise ValueError('Actual deployed control does not match local bytes')
    with (REPORT/'media_batch_01_control_deployment.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    print(json.dumps(dict(control_bytes=len(raw), registered_member_bytes=reg['total_member_bytes'],
                          sources=len(members), launch=receipt['launch'])))


def read_local(name):
    return json.loads((REPORT/name).read_text(encoding='utf-8-sig'))


if __name__ == '__main__':
    main()
