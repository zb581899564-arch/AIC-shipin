"""Exclusive small receipts and verified direct requests for the independent T root."""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import urllib.request

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK / 't_branch_execution_20261022_v1'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def identity(path):
    path = Path(path).resolve(strict=True); digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''): digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def check(ref):
    result = identity(ref['path'])
    if result['sha256'] != ref['sha256'] or ('bytes' in ref and result['bytes'] != ref['bytes']):
        raise ValueError('Bound input identity differs')
    return Path(ref['path'])


def public_route(peer):
    if not ipaddress.ip_address(peer).is_global:
        raise ValueError('Actual source peer is not a public address')
    route = subprocess.check_output(['ip', 'route', 'get', peer], text=True).strip()
    match = re.search(r'\bdev\s+(\S+)', route)
    if match is None or not (Path('/sys/class/net') / match[1] / 'device').exists():
        raise ValueError('Actual source route is not physical/direct')
    return dict(peer=peer, route=route, physical_device=match[1], proxy_handler={})


def fetch(url, destination, cap, headers=None):
    path = Path(destination)
    if path.exists() or path.with_suffix(path.suffix + '.partial').exists():
        raise FileExistsError('Do not repeat accepted or ambiguous source acquisition')
    request = urllib.request.Request(url, headers=dict({'User-Agent': 'AIC-academic-T-source-admission',
        'Accept-Encoding': 'identity'}, **(headers or {})))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=25) as response:
        route = public_route(response.fp.raw._sock.getpeername()[0])
        declared = response.headers.get('Content-Length')
        if declared is not None and int(declared) > cap:
            raise ValueError('Declared payload exceeds the registered byte cap')
        partial = path.with_suffix(path.suffix + '.partial'); total = 0
        with partial.open('xb') as stream:
            while True:
                block = response.read(min(1 << 18, cap + 1 - total))
                if not block: break
                total += len(block)
                if total > cap: raise ValueError('Actual payload exceeds cap; retain partial')
                stream.write(block)
        if declared is not None and total != int(declared): raise ValueError('Incomplete declared payload')
        partial.rename(path)
        receipt = dict(url=url, final_url=response.url, status=response.status,
            source=identity(path), headers=dict(response.headers), **route)
        save(path.with_name(path.name + '.route.json'), receipt)
        return receipt
