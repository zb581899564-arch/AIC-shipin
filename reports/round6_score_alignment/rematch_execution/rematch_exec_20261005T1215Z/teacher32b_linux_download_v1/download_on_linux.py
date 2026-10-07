"""Pinned teacher weights: model payload goes from official CDN to Linux only."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(name, value):
    path = HERE / name
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            result.update(chunk)
    return result.hexdigest()


def download(row, url, total_done, total_expected):
    target = HERE / 'assets' / row['path']
    part = target.with_suffix(target.suffix + '.incomplete')
    expected = row['size_bytes']
    if target.exists():
        if target.stat().st_size != expected or sha(target) != row['lfs_sha256']:
            raise RuntimeError('existing final weight failed identity; preserve it')
        return {'path': str(target), 'bytes': expected, 'sha256': row['lfs_sha256']}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    last_update = 0
    for attempt in range(1, 7):
        offset = part.stat().st_size if part.exists() else 0
        if offset > expected:
            raise RuntimeError('owned partial exceeds pinned size; preserve it')
        if offset == expected:
            break
        if shutil.disk_usage(HERE).free < expected - offset:
            raise RuntimeError('actual filesystem cannot cover remaining weight')
        headers = {'User-Agent': 'AIC-pinned-Linux-download/1'}
        if offset:
            headers['Range'] = 'bytes=' + str(offset) + '-'
        request = urllib.request.Request(url, headers=headers)
        try:
            with opener.open(request, timeout=45) as response:
                status = response.status
                if status == 206:
                    content_range = response.headers.get('Content-Range', '')
                    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', content_range)
                    if not match or int(match[1]) != offset or int(match[3]) != expected:
                        raise ValueError('mismatched HTTP range; preserve partial')
                elif status == 200 and offset == 0:
                    length = response.headers.get('Content-Length')
                    if length is not None and int(length) != expected:
                        raise ValueError('pinned HTTP size mismatch')
                else:
                    # Do not silently repeat a whole paid transfer if Range was ignored.
                    raise ValueError('resume was not honored; preserve partial without redownload')
                with part.open('ab' if offset else 'xb') as stream:
                    while True:
                        chunk = response.read(min(8 << 20, expected - offset + 1))
                        if not chunk:
                            break
                        if offset + len(chunk) > expected:
                            raise ValueError('payload exceeds pinned size')
                        stream.write(chunk)
                        offset += len(chunk)
                        now = time.monotonic()
                        if now - last_update >= 2:
                            stream.flush()
                            write('progress.json', {'status': 'DOWNLOADING_OFFICIAL_CDN_ON_LINUX',
                                  'utc': utc(), 'pid': os.getpid(), 'file': row['path'],
                                  'file_bytes': offset, 'file_expected_bytes': expected,
                                  'total_downloaded_bytes': total_done + offset,
                                  'total_expected_bytes': total_expected, 'attempt': attempt,
                                  'payload_receiver': 'Linux', 'Windows_payload_transfer': False,
                                  'application_proxy_disabled': True})
                            last_update = now
                    stream.flush()
                    os.fsync(stream.fileno())
                if offset != expected:
                    raise OSError('incomplete HTTP response; resumable partial retained')
            break
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            # Log types and HTTP status, never temporary signed URL credentials.
            write('retry.json', {'utc': utc(), 'file': row['path'], 'attempt': attempt,
                                'failure_type': type(error).__name__,
                                'http_code': getattr(error, 'code', None),
                                'partial_bytes': part.stat().st_size if part.exists() else 0})
            if isinstance(error, urllib.error.HTTPError) and error.code in (401, 403):
                raise RuntimeError('official signed CDN target expired or denied; no fallback download') from None
            if attempt == 6:
                raise RuntimeError('bounded resumable network retries exhausted') from None
            time.sleep(min(5 * attempt, 30))
    write('progress.json', {'status': 'VERIFYING_COMPLETE_WEIGHT_SHA256', 'utc': utc(),
                           'pid': os.getpid(), 'file': row['path'], 'total_expected_bytes': total_expected})
    if part.stat().st_size != expected or sha(part) != row['lfs_sha256']:
        raise RuntimeError('downloaded weight identity failed; preserve bytes without another bulk download')
    part.replace(target)
    return {'path': str(target), 'bytes': expected, 'sha256': row['lfs_sha256']}


def main():
    lock = (HERE / 'download.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    authorization = json.loads((HERE / 'authorization.json').read_text())
    if authorization.get('Linux_original_download_approved') is not True:
        raise RuntimeError('user network authorization missing')
    recipe = json.loads((HERE / 'recipe.json').read_text())
    targets = json.loads((HERE / 'private_cdn_targets.json').read_text())
    expected = {row['path'] for row in recipe['files']}
    if set(targets['urls']) != expected:
        raise RuntimeError('official target file set differs')
    for url in targets['urls'].values():
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not (parsed.hostname.endswith('.hf.co') or
                                            parsed.hostname.endswith('.xethub.hf.co')):
            raise RuntimeError('target is not an official HTTPS model CDN')
    with (HERE / 'registration.json').open('x') as stream:
        json.dump({'pid': os.getpid(), 'utc': utc(), 'recipe_sha256': sha(HERE / 'recipe.json'),
                   'authorization_sha256': sha(HERE / 'authorization.json'),
                   'model_payload_host': 'Linux', 'Mac_used': False}, stream)
    (HERE / 'assets').mkdir(exist_ok=True)
    receipts = []
    try:
        for row in recipe['files']:
            receipts.append(download(row, targets['urls'][row['path']],
                                     sum(r['bytes'] for r in receipts), recipe['total_bytes']))
        result = {'status': 'PASS_PINNED_TEACHER_WEIGHTS_ON_LINUX', 'utc': utc(), 'files': receipts,
                  'total_bytes': sum(r['bytes'] for r in receipts), 'Windows_payload_transfer': False,
                  'Mac_used': False, 'model_loaded': False}
    except Exception as error:
        result = {'status': 'STOP_LINUX_TEACHER_DOWNLOAD', 'utc': utc(),
                  'failure_type': type(error).__name__, 'reason': str(error),
                  'completed_files': receipts, 'partials_preserved': True}
    write('completion.json', result)
    return 0 if result['status'].startswith('PASS_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
