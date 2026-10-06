"""Read-only inventory and project-local, pinned public model preparation. No GPU."""
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
REPO = 'Qwen/Qwen3-VL-8B-Instruct'
REVISION = '0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
CAP = 80 * 2**30

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(name, payload):
    path = RUN / 'controller' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)

def command(args):
    result = subprocess.run(args, text=True, capture_output=True, timeout=90)
    return {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}

def usage():
    return int(subprocess.check_output(['du', '-s', '-B1', str(ROOT)], text=True).split()[0])

def inventory():
    versions = {}
    for package in ['torch', 'transformers', 'peft', 'qwen-vl-utils', 'huggingface-hub', 'safetensors', 'accelerate', 'decord', 'av']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    ledger = ROOT / 'improvement_round1/gpu_ledger.jsonl'
    records = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    payload = {
        'checked_utc': utc(), 'hostname': socket.gethostname(), 'versions': versions,
        'gpu': command(['nvidia-smi']),
        'compute_processes': command(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader']),
        'processes': command(['ps', '-eo', 'pid,user,etimes,pcpu,pmem,args', '--sort=-pcpu']),
        'memory': command(['free', '-b']), 'disk': shutil.disk_usage(ROOT)._asdict(),
        'work_allocated_bytes': usage(),
        'policy': json.loads((ROOT / 'resource_policy.json').read_text()),
        'gpu_seconds_with_preserved_offset': 7200 + sum(item['charged_seconds'] for item in records),
        'gpu_ledger_records': len(records),
        'unreconciled_active_job_exists': (ROOT / 'improvement_round1/active_gpu_job.json').exists(),
        'old_coordination_note': 'Historical coordination.json training/submission/balance fields are not current authorization or current-day quota.',
    }
    save('resource_before.json', payload)
    print(json.dumps({key: payload[key] for key in ['checked_utc', 'hostname', 'versions', 'disk', 'work_allocated_bytes', 'gpu_seconds_with_preserved_offset', 'unreconciled_active_job_exists']}, ensure_ascii=False), flush=True)

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 2**20), b''):
            digest.update(block)
    return digest.hexdigest()

def download():
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE'):
        os.environ.pop(key, None)
    cache = RUN / 'cache'
    os.environ.update(HF_HOME=str(cache / 'hf'), HF_HUB_CACHE=str(cache / 'hub'),
        HF_XET_CACHE=str(cache / 'xet'), HF_HUB_DISABLE_XET='1',
        HF_HUB_ETAG_TIMEOUT='45', HF_HUB_DOWNLOAD_TIMEOUT='90',
        XDG_CACHE_HOME=str(cache), TMPDIR=str(RUN / 'tmp'))
    (RUN / 'tmp').mkdir(parents=True, exist_ok=True)
    from huggingface_hub import HfApi, hf_hub_download
    started = time.monotonic()
    baseline = usage()
    status = {'started_utc': utc(), 'repo': REPO, 'revision': REVISION,
              'status': 'METADATA_REQUEST', 'work_bytes_before': baseline,
              'route': 'Public HF network download on Linux; controller deployment via Mac mini',
              'gpu_used': False}
    save('model_download_status.json', status)
    try:
        info = HfApi().model_info(REPO, revision=REVISION, files_metadata=True, token=False)
        if info.sha != REVISION:
            raise RuntimeError('revision identity mismatch')
        card = info.card_data.to_dict() if info.card_data is not None else {}
        if card.get('license') != 'apache-2.0':
            raise RuntimeError('model license is not the verified Apache-2.0 contract')
        selected = [s for s in info.siblings if s.rfilename.endswith(('.json', '.safetensors', '.txt', '.jinja')) or s.rfilename in ('LICENSE', 'README.md')]
        for item in selected:
            p = Path(item.rfilename)
            if p.is_absolute() or '..' in p.parts:
                raise RuntimeError('unsafe repository path')
        expected = sum(item.size or 0 for item in selected)
        # Include incomplete HTTP file plus a same-sized retry and small runtime artifacts.
        reserve = expected * 2 + 2 * 2**30
        free = shutil.disk_usage(ROOT).free
        if reserve > CAP or free < reserve:
            raise RuntimeError(f'predicted simultaneous preparation capacity insufficient: {reserve}, free={free}')
        status.update(status='DOWNLOADING', license=card['license'], expected_download_bytes=expected,
                      predicted_peak_increment_bytes=reserve, free_bytes_before=free,
                      repo_files=[{'name': s.rfilename, 'bytes': s.size,
                                   'lfs_sha256': (s.lfs.sha256 if s.lfs else None)} for s in selected], completed=[])
        save('model_download_status.json', status)
        print(json.dumps({k: status[k] for k in ['status', 'license', 'expected_download_bytes', 'predicted_peak_increment_bytes'] }), flush=True)
        destination = RUN / 'models/Qwen3-VL-8B-Instruct'
        # Metadata before shards; sequential download minimizes duplicated disk/network work.
        for item in sorted(selected, key=lambda s: (s.rfilename.endswith('.safetensors'), s.rfilename)):
            if time.monotonic() - started > 7200:
                raise TimeoutError('preparation worker 2h frozen wall-time limit')
            added = usage() - baseline
            if added > CAP:
                raise RuntimeError('80GiB increment boundary exceeded')
            path = Path(hf_hub_download(REPO, item.rfilename, revision=REVISION,
                local_dir=destination, cache_dir=cache / 'hub', token=False))
            digest = sha256(path)
            if item.size is not None and path.stat().st_size != item.size:
                raise RuntimeError(f'byte count mismatch: {item.rfilename}')
            if item.lfs and digest != item.lfs.sha256:
                raise RuntimeError(f'LFS SHA-256 mismatch: {item.rfilename}')
            status['completed'].append({'name': item.rfilename, 'bytes': path.stat().st_size, 'sha256': digest})
            status.update(updated_utc=utc(), elapsed_seconds=time.monotonic() - started,
                          work_increment_bytes=usage() - baseline)
            save('model_download_status.json', status)
            print(json.dumps({'completed_file': item.rfilename, 'bytes': path.stat().st_size,
                              'elapsed_seconds': round(time.monotonic()-started, 2)}), flush=True)
        status.update(status='COMPLETE_HASH_VERIFIED', finished_utc=utc(), model_path=str(destination),
                      elapsed_seconds=time.monotonic()-started)
        save('model_download_status.json', status)
        print('COMPLETE_HASH_VERIFIED', flush=True)
    except BaseException as exc:
        status.update(status='FAILED', finished_utc=utc(), error_type=type(exc).__name__,
                      error=str(exc), elapsed_seconds=time.monotonic()-started)
        save('model_download_status.json', status)
        raise

def launch_download():
    log_path = RUN / 'controller/model_download.log'
    with log_path.open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', '-u', __file__, 'download8b'],
            cwd=RUN, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=True)
    receipt = {'started_utc': utc(), 'pid': child.pid, 'executable': sys.executable,
               'script_sha256': sha256(Path(__file__)), 'log': str(log_path),
               'gpu_job': False, 'model': REPO, 'revision': REVISION}
    save('model_download_launch.json', receipt)
    print(json.dumps(receipt), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['inventory', 'download8b', 'launch_download'])
    arguments = parser.parse_args()
    if arguments.action == 'inventory':
        inventory()
    elif arguments.action == 'download8b':
        download()
    else:
        launch_download()
