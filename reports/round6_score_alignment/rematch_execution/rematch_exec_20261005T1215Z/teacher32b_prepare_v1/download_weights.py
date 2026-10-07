"""Download the two pinned teacher artifacts with resume and full SHA verification.

Windows is only a transfer staging host. This process does not load a model,
access videos, generate labels, or apply the superseded project disk quota.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import time
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
CHUNK = 8 * 2**20


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b''):
            result.update(chunk)
    return result.hexdigest()


def download_file(recipe, row, asset_dir, update):
    name = row['path']
    if Path(name).name != name or not name.endswith('.gguf'):
        raise ValueError('invalid pinned artifact name')
    target = asset_dir / name
    partial = target.with_suffix(target.suffix + '.incomplete')
    expected = row['size_bytes']
    if target.exists():
        if target.stat().st_size != expected or sha(target) != row['lfs_sha256']:
            raise ValueError('existing final artifact identity differs')
        return dict(path=str(target), bytes=expected, sha256=row['lfs_sha256'], status='PASS_PINNED_BYTES_SHA256')
    failures = []
    for attempt in range(1, 7):
        offset = partial.stat().st_size if partial.exists() else 0
        if offset > expected:
            raise ValueError('partial exceeds official artifact size')
        if offset == expected:
            break
        remaining = sum(max(0, r['size_bytes'] - ((asset_dir/r['path']).stat().st_size if (asset_dir/r['path']).exists()
                            else (asset_dir/(r['path']+'.incomplete')).stat().st_size if (asset_dir/(r['path']+'.incomplete')).exists() else 0))
                        for r in recipe['files'])
        if shutil.disk_usage(asset_dir).free < remaining:
            raise OSError('actual staging filesystem cannot cover remaining pinned artifacts')
        url = 'https://huggingface.co/' + recipe['repo'] + '/resolve/' + recipe['revision'] + '/' + name
        # Fresh resolve prevents a cached, expired signed redirect. Never log its final URL.
        url += '?download=true&aic_request=' + uuid.uuid4().hex
        headers = {'User-Agent': 'aic-pinned-teacher-download/1.0', 'Accept-Encoding': 'identity'}
        if offset:
            headers['Range'] = 'bytes=' + str(offset) + '-'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
                status = response.status
                if status == 206:
                    content_range = response.headers.get('Content-Range', '')
                    if not content_range.startswith('bytes ' + str(offset) + '-') or not content_range.endswith('/' + str(expected)):
                        raise ValueError('server range does not match pinned artifact')
                elif status == 200:
                    # A server ignoring Range must replace the owned partial, never append.
                    offset = 0
                else:
                    raise ValueError('unexpected download HTTP status')
                mode = 'ab' if offset else 'wb'
                last = 0.0
                with partial.open(mode) as stream:
                    while True:
                        chunk = response.read(CHUNK)
                        if not chunk:
                            break
                        if offset + len(chunk) > expected:
                            raise ValueError('server artifact exceeds pinned size')
                        stream.write(chunk)
                        offset += len(chunk)
                        if time.monotonic() - last >= 2:
                            stream.flush()
                            update(name, offset, expected, attempt, failures)
                            last = time.monotonic()
                    stream.flush()
                    os.fsync(stream.fileno())
                if offset != expected:
                    raise OSError('short artifact response; resumable partial retained')
            break
        except ValueError:
            raise
        except Exception as exc:
            failures.append({'attempt': attempt, 'type': type(exc).__name__, 'http_code': getattr(exc, 'code', None)})
            update(name, partial.stat().st_size if partial.exists() else 0, expected, attempt, failures)
            if attempt == 6:
                raise RuntimeError('bounded artifact download retries exhausted') from None
            time.sleep(min(5 * attempt, 30))
    update(name, expected, expected, attempt, failures, phase='VERIFYING_FULL_SHA256')
    if partial.stat().st_size != expected or sha(partial) != row['lfs_sha256']:
        raise ValueError('pinned official artifact SHA256 mismatch; partial preserved')
    partial.replace(target)
    return dict(path=str(target), bytes=expected, sha256=row['lfs_sha256'], status='PASS_PINNED_BYTES_SHA256')


def main():
    import msvcrt
    lock = (HERE/'download.lock').open('a+b')
    lock.seek(0)
    if not lock.read(1):
        lock.write(b'1'); lock.flush()
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    if (HERE/'download_completion.json').exists():
        raise RuntimeError('download already has a completion receipt; do not relaunch')
    recipe = json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    assets = HERE/'assets'; assets.mkdir(exist_ok=True)
    completed = []
    start = time.monotonic()
    def update(name, done, total, attempt, failures, phase='DOWNLOADING_PINNED_TEACHER_WEIGHTS'):
        write(HERE/'download_progress.json',dict(status=phase, utc=utc(), pid=os.getpid(),
            file=name, file_bytes_downloaded=done, file_expected_bytes=total,
            total_expected_bytes=sum(r['size_bytes'] for r in recipe['files']),
            total_completed_bytes=sum(r['bytes'] for r in completed), elapsed_seconds=time.monotonic()-start,
            attempt=attempt, failures=failures, project_disk_quota_bytes=None,
            staging_host='Windows', inference_host='Linux', Mac_used=False, model_loaded=False))
    write(HERE/'download_registration.json',dict(pid=os.getpid(),utc=utc(),recipe_sha256=sha(HERE/'recipe.json'),
         project_disk_quota_bytes=None,initial_free_bytes=shutil.disk_usage(assets).free,Mac_used=False))
    try:
        for row in recipe['files']:
            completed.append(download_file(recipe,row,assets,update))
        result=dict(status='PASS_ALL_PINNED_TEACHER_WEIGHTS_DOWNLOADED',utc=utc(),pid=os.getpid(),files=completed,
                    total_bytes=sum(r['bytes'] for r in completed),Mac_used=False,model_loaded=False,labels_generated=False)
    except Exception as exc:
        result=dict(status='STOP_TEACHER_DOWNLOAD',utc=utc(),pid=os.getpid(),failure_type=type(exc).__name__,
                    failure=str(exc),completed_files=completed,partials_preserved=True,Mac_used=False)
    write(HERE/'download_completion.json',result)
    write(HERE/'download_progress.json',result)
    return 0 if result['status'].startswith('PASS_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
