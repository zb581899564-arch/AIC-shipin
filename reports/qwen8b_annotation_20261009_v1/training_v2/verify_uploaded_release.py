"""Independent safe extraction and verification of the exact approved release."""
import hashlib
import json
import os
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path('/home/inspur/aic_video_work')
ZIP = ROOT / 'datasets/qwen8b_annotation_20261009_v2.incoming.zip'
DEST = ROOT / 'datasets/qwen8b_annotation_20261009_v2'
ZIP_SHA = '45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c'
MANIFEST_SHA = 'adfe72e2318ec11913175fefb2ba987393d8f442a097efc16b2474a112b94ba1'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

assert ROOT.resolve(strict=True) == ROOT
assert ZIP.resolve(strict=True) == ZIP and ZIP.stat().st_size == 1269695818
assert sha(ZIP) == ZIP_SHA
assert DEST.parent.resolve(strict=True) == DEST.parent
assert not DEST.exists() and not DEST.is_symlink(), 'Never overwrite an existing release'
with zipfile.ZipFile(ZIP) as archive:
    infos = archive.infolist()
    names = [i.filename for i in infos]
    assert len(names) == 6353 and len(set(names)) == len(names)
    for info in infos:
        path = PurePosixPath(info.filename)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
        assert path.as_posix() == info.filename and ':' not in info.filename
        assert not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16)
    raw = archive.read('training_v2/selected_manifest.json')
    assert hashlib.sha256(raw).hexdigest() == MANIFEST_SHA
    manifest = json.loads(raw)
    assert len(manifest['files']) == 6352
    assert set(names) == set(manifest['files']) | {'training_v2/selected_manifest.json'}
    expanded = sum(i.file_size for i in infos)
    disk = os.statvfs(DEST.parent)
    assert disk.f_bavail * disk.f_frsize > expanded, 'Insufficient actual extraction capacity'
    DEST.mkdir()
    for index, info in enumerate(infos):
        target = DEST / info.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        assert target.parent.resolve(strict=True).is_relative_to(DEST)
        h = hashlib.sha256()
        size = 0
        with archive.open(info) as source, target.open('xb') as out:
            for block in iter(lambda: source.read(1 << 20), b''):
                out.write(block)
                h.update(block)
                size += len(block)
        assert size == info.file_size
        if info.filename in manifest['files']:
            expected = manifest['files'][info.filename]
            assert size == expected['bytes'] and h.hexdigest() == expected['sha256']
        if index % 1000 == 0:
            print(json.dumps({'stage':'SAFE_EXTRACT_CRC_SHA','files_done':index+1,'total_files':len(infos)}),flush=True)
import importlib.util
spec = importlib.util.spec_from_file_location('release_verify', DEST / 'training_v2/verify_bundle.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
extracted = module.verify(DEST)
receipt = {'utc':datetime.now(timezone.utc).isoformat(),
           'status':'PASS_REMOTE_ZIP_CRC_SAFE_EXTRACTION_ALL_SELECTED_FILE_HASHES',
           'zip':str(ZIP),'zip_bytes':ZIP.stat().st_size,'zip_sha256':ZIP_SHA,
           'destination':str(DEST),'manifest_sha256':MANIFEST_SHA,'archive_files':6353,
           'extracted_selected':extracted,'expanded_bytes':expanded,
           'model_weights_loaded':False,'optimizer_started':False}
with (DEST/'upload_verification.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,indent=2)
print(json.dumps(receipt),flush=True)
