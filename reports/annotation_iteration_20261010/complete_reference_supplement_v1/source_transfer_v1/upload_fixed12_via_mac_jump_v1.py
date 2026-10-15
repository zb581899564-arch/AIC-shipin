"""Upload the explicitly approved source ZIP through the online Mac SSH jump."""
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

LOCAL = Path(__file__).parent
ZIP = LOCAL / 'fixed12_native_sources.zip'
EXPECTED_BYTES = 196570456
EXPECTED_SHA = 'e723cf827240c66512065eba414ca1620964cc2a6bbcb45cbf0e44e42d60a084'
MANIFEST_SHA = '5f290da54346c7f1e3199cef3bdda10ce813becb60224780e29903198f5780c6'
REMOTE = '/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1'
RECEIPTS = LOCAL.parent / 'source_transfer_completed_v1'
SSH = ['ssh', '-J', 'macmini', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=20', 'aic-inspur-home']

def save_new(path, value):
    serialized = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(serialized)

def remote_python(source):
    # A hex source argument avoids nested Windows/SSH shell interpolation.
    command = "python3 -B -c 'exec(bytes.fromhex(\"" + source.encode().hex() + "\").decode())'"
    result = subprocess.run(SSH + [command], capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    return json.loads(result.stdout)

assert ZIP.stat().st_size == EXPECTED_BYTES
with ZIP.open('rb') as handle:
    digest = hashlib.file_digest(handle, 'sha256').hexdigest()
assert digest == EXPECTED_SHA
RECEIPTS.mkdir(exist_ok=False)
approval = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'authorization': 'User answered 批准上传并校验 to the exact 196570456-byte fixed12 source transfer question.',
    'scope': 'Upload, extract and SHA validation only; no training admission.',
    'route': 'Windows -> configured macmini SSH jump -> configured aic-inspur-home; strict host validation.',
    'mac_online_identity': 'choubkdeMac-Mini.local verified this turn; Mac workspace AGENTS read.',
    'linux_online_identity': 'inspur-NP5570M5 verified this turn; live CPU/GPU/RAM/disk inspected.',
    'approved_payload_bytes': EXPECTED_BYTES,
    'two_link_payload_bytes': 2 * EXPECTED_BYTES,
    'actual_billed_proxy_bytes': 'UNKNOWN_DEPENDS_ON_ROUTE_PLUS_PROTOCOL_OVERHEAD',
    'zip_sha256': EXPECTED_SHA,
    'new_model_calls': 0,
    'new_optimizer_updates': 0,
}
save_new(RECEIPTS / 'authorization_and_start.json', approval)
prepare = r'''
import json,socket
from pathlib import Path
root=Path('/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1')
assert socket.gethostname()=='inspur-NP5570M5'
anchor=Path('/home/inspur/aic_video_work')
assert anchor.resolve()==anchor and root.is_relative_to(anchor)
for p in [anchor,*list(root.parents)[:2],root]:
    assert not p.is_symlink()
assert not root.exists(), 'Expected a new destination; preserve existing outputs'
root.mkdir(parents=True,exist_ok=False)
stage=root/'source_transfer_v1';stage.mkdir()
print(json.dumps({'status':'PASS_NEW_SAFE_TRANSFER_DIRECTORY','root':str(root),'stage':str(stage)}))
'''
started = time.monotonic()
try:
    prepared = remote_python(prepare)
    save_new(RECEIPTS / 'remote_preparation.json', prepared)
    print(json.dumps(prepared), flush=True)
    target = REMOTE + '/source_transfer_v1/fixed12_native_sources.zip.part'
    copy = subprocess.run(['scp', '-J', 'macmini', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=20', str(ZIP), 'aic-inspur-home:' + target], capture_output=True, text=True, encoding='utf-8')
    save_new(RECEIPTS / 'scp_terminal.json', {'exit_code': copy.returncode, 'stdout': copy.stdout, 'stderr': copy.stderr, 'elapsed_seconds': time.monotonic()-started})
    assert copy.returncode == 0, copy.stderr
    verify = r'''
import hashlib,json,socket,stat,zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
root=Path('/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1')
stage=root/'source_transfer_v1';part=stage/'fixed12_native_sources.zip.part'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
assert socket.gethostname()=='inspur-NP5570M5' and root.resolve()==root
assert part.is_file() and not part.is_symlink() and part.stat().st_size==196570456
assert sha(part)=='e723cf827240c66512065eba414ca1620964cc2a6bbcb45cbf0e44e42d60a084'
final=stage/'fixed12_native_sources.zip';native=root/'native_sources';pending=root/'native_sources.part_v1'
assert not final.exists() and not native.exists() and not pending.exists()
pending.mkdir()
rows=[]
with zipfile.ZipFile(part) as archive:
    names=archive.namelist();assert len(names)==13 and len(set(names))==13
    for info in archive.infolist():
        p=PurePosixPath(info.filename)
        assert not p.is_absolute() and len(p.parts)==1 and p.name not in ('','.', '..') and '\\' not in info.filename
        assert not info.is_dir() and not (info.flag_bits & 1) and not stat.S_ISLNK(info.external_attr>>16)
    raw_manifest=archive.read('fixed12_sources_manifest.json')
    assert hashlib.sha256(raw_manifest).hexdigest()=='5f290da54346c7f1e3199cef3bdda10ce813becb60224780e29903198f5780c6'
    manifest=json.loads(raw_manifest);sources=manifest['sources']
    assert manifest['fixed_denominator']==24 and len(sources)==12 and len({s['source_id'] for s in sources})==12
    assert set(names)=={'fixed12_sources_manifest.json'}|{s['archive_name'] for s in sources}
    assert sum(s['bytes'] for s in sources)==196564489
    for source in sources:
        assert source['archive_name']==source['source_id']+'.mp4'
        info=archive.getinfo(source['archive_name']);assert info.file_size==source['bytes']
        destination=pending/source['archive_name'];h=hashlib.sha256();count=0
        with archive.open(info) as reader,destination.open('xb') as writer:
            for chunk in iter(lambda:reader.read(8<<20),b''):
                writer.write(chunk);h.update(chunk);count+=len(chunk)
        assert count==source['bytes'] and h.hexdigest()==source['sha256']
        assert sha(destination)==source['sha256'], 'Independent extracted-file reread mismatch'
        rows.append({'source_id':source['source_id'],'path':str(native/source['archive_name']),'bytes':count,'sha256':h.hexdigest(),'archive_CRC_and_SHA_pass':True,'extracted_file_SHA_pass':True})
    with (stage/'fixed12_sources_manifest.json').open('xb') as f:f.write(raw_manifest)
pending.rename(native);part.rename(final)
assert sha(final)=='e723cf827240c66512065eba414ca1620964cc2a6bbcb45cbf0e44e42d60a084'
receipt={'status':'PASS_FIXED12_SOURCE_UPLOAD_EXTRACTION_ALL_SHA_NOT_TRAINING','utc':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'route':'Windows -> macmini SSH jump -> aic-inspur-home','zip_path':str(final),'zip_bytes':final.stat().st_size,'zip_sha256':sha(final),'manifest_sha256':sha(stage/'fixed12_sources_manifest.json'),'source_count':12,'source_bytes':sum(r['bytes'] for r in rows),'sources':rows,'archive_names_exact':True,'archive_path_and_link_checks_pass':True,'all_CRC_and_source_SHA_pass':True,'all_extracted_file_SHA_pass':True,'new_model_calls':0,'new_optimizer_updates':0,'training_started':False,'original_local_preparation_receipt_preserved':True}
with (stage/'upload_validation_receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
'''
    receipt = remote_python(verify)
    save_new(RECEIPTS / 'upload_validation_receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
except BaseException as error:
    save_new(RECEIPTS / 'failure.json', {'utc': datetime.now(timezone.utc).isoformat(), 'error': repr(error), 'elapsed_seconds': time.monotonic()-started, 'partial_files_preserved': True, 'automatic_retry': False})
    raise
