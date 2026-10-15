"""Explicit ROOT deployment commands. No retry, replacement, video upload or GPU admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
import zipfile

LINUX_TEXT = '/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1'
LINUX = Path(LINUX_TEXT)
PYTHON = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
STAGE = LINUX/'deployment_metadata_v1'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def save(p, value):
    with Path(p).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def utc():
    return datetime.now(timezone.utc).isoformat()

def members(z):
    result = {}
    for info in z.infolist():
        name = info.filename
        parts = PurePosixPath(name).parts
        need(info.orig_filename == name and name and '\\' not in name and ':' not in name and not name.startswith('/') and
             all(p not in ('', '.', '..') for p in name.split('/')) and
             '/'.join(parts) == name, 'unsafe ZIP name: '+name)
        mode = info.external_attr >> 16
        need(not info.is_dir() and not stat.S_ISLNK(mode) and
             stat.S_IFMT(mode) in (0, stat.S_IFREG), 'nonregular ZIP member: '+name)
        need(not (info.flag_bits & 1) and name not in result, 'encrypted/duplicate ZIP member')
        payload = z.read(info)  # Decompression verifies each member CRC.
        result[name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), crc32=info.CRC)
    need(z.testzip() is None, 'ZIP CRC differs')
    return result

def verify_archive(zip_path, manifest):
    need(Path(zip_path).stat().st_size == manifest['zip']['bytes'] and
         sha(zip_path) == manifest['zip']['sha256'], 'ZIP binding differs')
    with zipfile.ZipFile(zip_path) as z:
        actual = members(z)
    need(actual == manifest['files'], 'ZIP file manifest differs')

def prepare(a):
    """Verify existing ROOT projection; do not create/redecode scientific inputs."""
    source = Path(a.projection).resolve(strict=True)
    root = Path(__file__).resolve().parent.parent
    need(sha(a.root_admission) == a.expected_root_admission, 'ROOT admission SHA differs')
    receipt = read(source/'projection_receipt.json')
    need(receipt['status'] == 'PASS_LOCAL_SEMANTICALLY_EXACT_LINUX_METADATA_PROJECTION_NOT_TRANSFERRED_NOT_TRAINING'
         and receipt['windows'] == 24 and len(receipt['evaluation_windows']) == 12, 'projection admission differs')
    b = receipt['original_registry']
    need(sha(b['path']) == b['sha256'], 'original registry drift')
    admission = read(a.root_admission)
    need(admission['registry_binding'] == b and
         admission['denominator'] == dict(total=24,qualified=20,rejected=4,pending=0) and
         admission['train_windows'] == 8 and admission['evaluation_windows'] == 12 and
         admission['fully_known_locked'] == 6 and admission['original_silver_actual_verified'] is True,
         'ROOT final actual24 registry/silver admission required')
    registry = read(b['path']); rows = registry.get('records', registry)
    need(len(rows) == 24 and sum(bool(row.get('reference')) for row in rows.values()) == 20 and
         sum(row.get('training_admitted') is True for row in rows.values()) == 8,
         '20 admitted references +4 rejected /8 train required')
    for row in rows.values():
        if row.get('reference'):
            rb = row['reference']; need(sha(rb['path']) == rb['sha256'], 'registry reference source drift')
    projected_rows = read(source/'reference_registry.json')['records']
    need(set(projected_rows) == set(rows) and all(
        {k:v for k,v in rows[key].items() if k!='reference'} ==
        {k:v for k,v in projected_rows[key].items() if k!='reference'} for key in rows), 'registry state/role projection changed')
    prefix = LINUX_TEXT+'/inputs/'
    def projected(binding):
        need(binding['path'].startswith(prefix), 'projection path outside inputs')
        p = source/binding['path'][len(prefix):]
        need(p.resolve().is_relative_to(source) and sha(p) == binding['sha256'], 'projected binding drift')
        return p
    for binding in receipt['bindings']:
        op = binding['operation']
        if op == 'BYTE_EXACT_COPY':
            need(sha(binding['original_path']) == binding['original_sha256'] == binding['linux_sha256'], 'original source drift')
            projected(dict(path=binding['linux_path'], sha256=binding['linux_sha256']))
        elif op == 'ONLY_TOP_LEVEL_BOUND_EVIDENCE_PATH_PROJECTION':
            old = read(projected(binding['original_reference'])); new = read(projected(binding['projected_reference']))
            need({k:v for k,v in old.items() if k!='evidence'} == {k:v for k,v in new.items() if k!='evidence'}, 'reference semantics changed')
            need(set(old['evidence']) == set(new['evidence']), 'evidence keys changed')
            for key in old['evidence']:
                need(sha(old['evidence'][key]['path']) == old['evidence'][key]['sha256'] == new['evidence'][key]['sha256'], 'evidence original drift')
                projected(new['evidence'][key])
        elif op == 'ONLY_REFERENCE_SHA_PROJECTION':
            oldb = binding['original_sidecar']; need(sha(oldb['path']) == oldb['sha256'], 'sidecar source drift')
            old = read(oldb['path']); new = read(projected(binding['projected_sidecar']))
            need({k:v for k,v in old.items() if k!='reference_sha256'} == {k:v for k,v in new.items() if k!='reference_sha256'}, 'target literal changed')
        else:
            raise ValueError('unknown projection operation')
    runtime = {p.name:sha(p) for p in (root/'runtime').glob('*.py')}
    need(len(runtime) == 23 and {p.name:sha(p) for p in (source/'runtime').glob('*.py')} == runtime, 'current23 runtime SHA differs')
    with zipfile.ZipFile(a.zip) as z:
        files = members(z)
    need(not any(p.is_symlink() for p in source.rglob('*')), 'projection symlink forbidden')
    disk = {p.relative_to(source).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in source.rglob('*') if p.is_file()}
    need(set(disk) == set(files) and all(disk[n] == {k:files[n][k] for k in ('bytes','sha256')} for n in disk), 'ZIP differs from verified projection')
    config = read(source/'config.json')
    need(config['execution_python'] == PYTHON and len(config['source_files']) == 12, 'runtime/source count differs')
    need(sha(a.source_upload_receipt) == a.expected_source_upload_receipt, 'actual source upload receipt changed')
    uploaded = read(a.source_upload_receipt)
    need(uploaded['status'] == 'PASS_FIXED12_SOURCE_UPLOAD_EXTRACTION_ALL_SHA_NOT_TRAINING' and
         uploaded['source_count'] == 12 and len(uploaded['sources']) == 12 and
         {s['sha256']:dict(path=s['path'],sha256=s['sha256']) for s in uploaded['sources']} == config['source_files'] and
         all(s['archive_CRC_and_SHA_pass'] is True and s['extracted_file_SHA_pass'] is True for s in uploaded['sources']),
         'actual uploaded12 source identity differs')
    manifest = dict(schema='ROOT_METADATA_DEPLOYMENT_V1', status='PASS_LOCAL_PROJECTED_METADATA_CRC_SHA_SOURCE_RUNTIME23_NOT_TRANSFERRED', utc=utc(),
        zip=dict(bytes=Path(a.zip).stat().st_size,sha256=sha(a.zip)), files=files, runtime_sha256=runtime,
        deployment_script_sha256=sha(__file__), root_admission=dict(path=str(Path(a.root_admission).resolve()),sha256=a.expected_root_admission),
        original_registry=b, target_inputs=LINUX_TEXT+'/inputs', source_files=config['source_files'],
        actual_source_upload_receipt=dict(path=str(Path(a.source_upload_receipt).resolve()),sha256=a.expected_source_upload_receipt),
        projection_source_upload_still_required_is_generic_static_field_satisfied_by_actual_receipt=True,
        source_videos_already_uploaded=True, automatic_retry=False, new_model_calls=0, new_optimizer_updates=0)
    save(a.output,manifest)
    digest = sha(a.output)
    stage = LINUX_TEXT+'/deployment_metadata_v1'
    remote = PYTHON+' -B '+stage+'/deploy_metadata.py'
    shared = ' --zip '+stage+'/metadata.zip --manifest '+stage+'/manifest.json --expected-manifest '+digest
    quote = lambda s: "'"+str(s).replace("'","''")+"'"
    commands = dict(upload='& '+quote(Path(__file__).parent/'upload_metadata.ps1')+' -Zip '+quote(Path(a.zip).resolve())+
        ' -Manifest '+quote(Path(a.output).resolve())+' -ExpectedManifest '+quote(digest)+' -RootAuthorizeUpload',
        accept="ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home '"+remote+' accept'+shared+"'",
        start_requires_actual_remote_acceptance_sha="ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home '"+
            remote+' start'+shared+' --expected-acceptance <ACTUAL_ACCEPTANCE_SHA> --root-authorize-start'+"'")
    print(json.dumps(dict(status=manifest['status'],manifest=str(Path(a.output).resolve()),sha256=digest,files=len(files),
        runtime_files=23,uploaded=False,root_commands=commands),ensure_ascii=False,indent=2))

def verified_stage(a):
    need(sys.platform == 'linux' and Path(__file__).resolve().parent == STAGE, 'registered Linux staging script required')
    need(not LINUX.is_symlink() and not STAGE.is_symlink() and
         Path(a.zip) == STAGE/'metadata.zip' and Path(a.manifest) == STAGE/'manifest.json' and
         not Path(a.zip).is_symlink() and not Path(a.manifest).is_symlink(), 'literal staging paths required')
    need(sha(a.manifest) == a.expected_manifest, 'manifest SHA differs')
    m = read(a.manifest)
    need(m['schema'] == 'ROOT_METADATA_DEPLOYMENT_V1' and m['target_inputs'] == str(LINUX/'inputs') and
         m['automatic_retry'] is False and m['source_videos_already_uploaded'] is True and len(m['runtime_sha256']) == 23,
         'deployment manifest contract differs')
    need(sha(__file__) == m['deployment_script_sha256'], 'deployment script changed')
    verify_archive(a.zip,m)
    return m

def offline():
    env = os.environ.copy()
    env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
               TOKENIZERS_PARALLELISM='false',PYTHONNOUSERSITE='1')
    return env

def accept(a):
    m = verified_stage(a)
    target = LINUX/'inputs'
    need(not target.exists() and not target.is_symlink(), 'inputs already exists; never replace/retry')
    for binding in m['source_files'].values():
        p = Path(binding['path'])
        need(p.parent == LINUX/'native_sources' and not p.is_symlink() and p.is_file() and sha(p) == binding['sha256'], 'already uploaded native source SHA differs')
    save(STAGE/'accept_attempt.json',dict(utc=utc(),manifest_sha256=a.expected_manifest,automatic_retry=False))
    target.mkdir(exist_ok=False)
    with zipfile.ZipFile(a.zip) as z:
        for name,b in m['files'].items():
            p = target/name
            need(p.resolve().is_relative_to(target.resolve()), 'extraction escape')
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(z.read(name))
            need(sha(p) == b['sha256'] and p.stat().st_size == b['bytes'], 'extracted file differs')
    verify_inputs(m)
    lock = LINUX/'source_lock.json'
    need(not lock.exists() and not (LINUX/'source_lock.creation_receipt.json').exists(), 'lock already exists')
    commands = [[PYTHON,'-B',str(target/'runtime/freeze_inputs.py'),'--config',str(target/'config.json'),'--output',str(lock)]]
    with (STAGE/'freeze.log').open('x',encoding='utf-8') as log:
        result = subprocess.run(commands[0],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=LINUX,env=offline())
    need(result.returncode == 0 and lock.is_file(), 'freeze failed; preserve log/partial without retry')
    digest = sha(lock)
    commands.append([PYTHON,'-B',str(target/'runtime/train.py'),'--config',str(target/'config.json'),'--lock',str(lock),'--expected-lock',digest,'--check-only'])
    with (STAGE/'check_only.log').open('x',encoding='utf-8') as log:
        result = subprocess.run(commands[1],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=LINUX,env=offline())
    need(result.returncode == 0, 'check-only failed; no pipeline start')
    check = json.loads((STAGE/'check_only.log').read_text().strip().splitlines()[-1])
    need(check['status'] == 'PASS_STATIC_ADMISSION_ONLY' and all(check[k] is False for k in ('decoder_started','processor_started','model_started')), 'check-only receipt differs')
    save(STAGE/'acceptance.json',dict(status='PASS_REMOTE_METADATA_SHA_LOCK_STATIC_CHECK_ONLY_NOT_STARTED',utc=utc(),manifest_sha256=a.expected_manifest,
        source_lock=dict(path=str(lock),sha256=digest),files=m['files'],commands=commands,check_only=check,
        source_videos_reuploaded=False,model_started=False,pipeline_started=False,automatic_retry=False))
    print(json.dumps(dict(status='PASS_REMOTE_METADATA_SHA_LOCK_STATIC_CHECK_ONLY_NOT_STARTED',acceptance_sha256=sha(STAGE/'acceptance.json'),source_lock_sha256=digest)))

def verify_inputs(m):
    target = LINUX/'inputs'
    actual = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
    need(actual == set(m['files']) and not any(p.is_symlink() for p in target.rglob('*')), 'inputs file set/symlink changed')
    for name,b in m['files'].items():
        p = target/name
        need(sha(p) == b['sha256'] and p.stat().st_size == b['bytes'], 'input SHA changed: '+name)
    need({p.name:sha(p) for p in (target/'runtime').glob('*.py')} == m['runtime_sha256'], 'runtime23 changed')

def start(a):
    need(a.root_authorize_start, 'explicit ROOT --root-authorize-start required')
    m = verified_stage(a); verify_inputs(m)
    receipt = STAGE/'acceptance.json'
    need(sha(receipt) == a.expected_acceptance, 'actual remote acceptance SHA differs')
    r = read(receipt)
    need(r['status'] == 'PASS_REMOTE_METADATA_SHA_LOCK_STATIC_CHECK_ONLY_NOT_STARTED' and r['manifest_sha256'] == a.expected_manifest, 'remote acceptance invalid')
    lock = LINUX/'source_lock.json'; need(sha(lock) == r['source_lock']['sha256'], 'source lock changed')
    for path,digest in read(lock)['files'].items():need(sha(path) == digest, 'locked input changed: '+path)
    for name in ('pipeline_01','train_01','evaluate_01','candidate_01','native_inputs_01'):
        need(not (LINUX/name).exists(), 'existing stage forbids new startup: '+name)
    command = [PYTHON,'-B',str(LINUX/'inputs/runtime/pipeline_controller.py'),'--config',str(LINUX/'inputs/config.json'),
               '--lock',str(lock),'--expected-lock',sha(lock)]
    save(STAGE/'start_attempt.json',dict(utc=utc(),root_explicit_action='--root-authorize-start',command=command,
        acceptance_sha256=a.expected_acceptance,source_lock_sha256=sha(lock),automatic_retry=False))
    with (STAGE/'pipeline.nohup.log').open('x',encoding='utf-8') as log:
        process = subprocess.Popen(['nohup']+command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            cwd=LINUX,env=offline(),start_new_session=True)
    time.sleep(0.5)
    actual = Path('/proc')/str(process.pid)/'cmdline'
    observed = actual.read_bytes().split(b'\0') if actual.exists() else []
    observed = [x.decode('utf-8') for x in observed if x]
    record = dict(status='STARTED_NOT_VALIDATED' if process.poll() is None else 'STOP_EARLY_EXIT_NO_RETRY',utc=utc(),pid=process.pid,
        requested_command=command,actual_proc_cmdline=observed,immediate_exit_code=process.poll(),source_lock_sha256=sha(lock),
        acceptance_sha256=a.expected_acceptance,offline_environment={k:offline()[k] for k in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE','TOKENIZERS_PARALLELISM','PYTHONNOUSERSITE')},
        gpu_admission='UNCHANGED_PIPELINE_SHARED_RUNNER_ACTUAL_LIVE_ADMISSION',automatic_retry=False)
    save(STAGE/'startup.json',record)
    print(json.dumps(record))
    need(record['status'] == 'STARTED_NOT_VALIDATED' and observed == command, 'startup actual process differs; do not relaunch')

def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='mode',required=True)
    q = sub.add_parser('prepare')
    for name in ('projection','zip','root-admission','expected-root-admission','source-upload-receipt','expected-source-upload-receipt','output'):q.add_argument('--'+name,required=True)
    for mode in ('accept','start'):
        q = sub.add_parser(mode)
        for name in ('zip','manifest','expected-manifest'):q.add_argument('--'+name,required=True)
        if mode == 'start':
            q.add_argument('--expected-acceptance',required=True);q.add_argument('--root-authorize-start',action='store_true')
    a = p.parse_args(); globals()[a.mode](a)

if __name__ == '__main__':main()
