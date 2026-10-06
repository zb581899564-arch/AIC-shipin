"""Download a pinned public model through a reachable mirror, verify official hashes."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import quote

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL = RUN / 'controller'
REV = '0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
REPO = 'Qwen/Qwen3-VL-8B-Instruct'
CAP = 80 * 2**30

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write(name, data):
    path = CTRL / name
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)

def hash_file(path, git_blob=False):
    h = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        h.update(f'blob {path.stat().st_size}\0'.encode())
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8*2**20), b''):
            h.update(block)
    return h.hexdigest()

def allocated(path):
    return int(subprocess.check_output(['du', '-s', '-B1', str(path)], text=True).split()[0])

def download():
    manifest_path = CTRL / 'hf_model_info.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('sha') != REV or manifest.get('id') != REPO:
        raise RuntimeError('official manifest identity mismatch')
    if manifest.get('cardData', {}).get('license') != 'apache-2.0':
        raise RuntimeError('public model permission gate failed')
    selected = [f for f in manifest['siblings'] if f['rfilename'].endswith(('.json','.safetensors','.txt','.jinja')) or f['rfilename'] in ('README.md','LICENSE')]
    size = sum(f['size'] for f in selected)
    reserve = size + max(f['size'] for f in selected) + 2*2**30
    free = shutil.disk_usage(ROOT).free
    before = allocated(RUN)
    if reserve + before > CAP or free < reserve:
        raise RuntimeError(f'capacity insufficient for measured preparation: reserve={reserve}, current_run={before}, free={free}')
    started = time.monotonic()
    state = dict(status='DOWNLOADING', started_utc=utc(), repo=REPO, revision=REV,
        metadata_source='https://huggingface.co/api/models/'+REPO+'/revision/'+REV+'?blobs=true',
        official_manifest_sha256=hash_file(manifest_path), transport_source='https://hf-mirror.com',
        identity_verification='Every file verified against official pinned manifest: LFS SHA256 or Git blob SHA1',
        license='apache-2.0', expected_model_bytes=size, predicted_increment_peak_bytes=reserve,
        free_before=free, completed=[], gpu_used=False)
    write('model_download_v2_status.json', state)
    destination = RUN / 'models/Qwen3-VL-8B-Instruct'
    destination.mkdir(parents=True, exist_ok=True)
    try:
        for item in sorted(selected, key=lambda f:(f['rfilename'].endswith('.safetensors'), f['rfilename'])):
            name = item['rfilename']
            rel = Path(name)
            if rel.is_absolute() or '..' in rel.parts:
                raise RuntimeError('unsafe public manifest path')
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(path.suffix+'.partial')
            remaining = int(7200 - (time.monotonic()-started))
            if remaining <= 0:
                raise TimeoutError('2h preparation wall-time limit')
            if allocated(RUN) > CAP:
                raise RuntimeError('80GiB new-run occupancy boundary exceeded')
            state.update(active_file=name, updated_utc=utc())
            write('model_download_v2_status.json', state)
            url = 'https://hf-mirror.com/'+REPO+'/resolve/'+REV+'/'+quote(name, safe='/')
            subprocess.run(['curl','--fail','--location','--silent','--show-error',
                '--connect-timeout','20','--max-time',str(remaining),
                '--retry','2','--continue-at','-',url,'--output',str(partial)], check=True)
            if partial.stat().st_size != item['size']:
                raise RuntimeError('file byte mismatch: '+name)
            lfs = item.get('lfs')
            expected = lfs['sha256'] if lfs else item['blobId']
            actual = hash_file(partial, git_blob=not bool(lfs))
            if actual != expected:
                raise RuntimeError('official pinned content hash mismatch: '+name)
            digest = actual if lfs else hash_file(partial)
            partial.replace(path)
            state['completed'].append(dict(name=name, bytes=item['size'], sha256=digest,
                official_content_hash=actual, verification='lfs_sha256' if lfs else 'git_blob_sha1'))
            state.update(updated_utc=utc(), elapsed_seconds=time.monotonic()-started,
                         new_run_occupied_bytes=allocated(RUN))
            write('model_download_v2_status.json',state)
            print(json.dumps({'verified_file':name,'bytes':item['size'],'elapsed_seconds':round(time.monotonic()-started,2)}),flush=True)
        state.update(status='COMPLETE_HASH_VERIFIED', finished_utc=utc(),
            model_path=str(destination), elapsed_seconds=time.monotonic()-started, active_file=None)
        write('model_download_v2_status.json',state)
        print('COMPLETE_HASH_VERIFIED',flush=True)
    except BaseException as exc:
        state.update(status='FAILED',error_type=type(exc).__name__,error=str(exc),finished_utc=utc())
        write('model_download_v2_status.json',state)
        raise

def launch():
    with (CTRL/'model_download_v2.log').open('x') as log:
        proc = subprocess.Popen([sys.executable,'-B','-u',__file__,'download'],
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=RUN,start_new_session=True)
    receipt=dict(pid=proc.pid,started_utc=utc(),script_sha256=hash_file(Path(__file__)),gpu_used=False)
    write('model_download_v2_launch.json',receipt)
    print(json.dumps(receipt))

if __name__=='__main__':
    launch() if sys.argv[1:] == ['launch'] else download()
