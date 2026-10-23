"""Explicit public physical-route reads, with bounded immutable receipts."""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import urllib.request

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK/'highlight_source_admission_20261021_v1'


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def ref(path):
    path = Path(path).resolve(strict=True)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def fetch(url, name, cap=2000000, headers=None):
    path = ROOT/'metadata'/name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError('Accepted source response must not be fetched again')
    request = urllib.request.Request(url, headers=dict({'User-Agent':'AIC-source-admission-research',
        'Accept':'*/*', 'Accept-Encoding':'identity'}, **(headers or {})))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=25) as response:
        peer = response.fp.raw._sock.getpeername()[0]
        route = subprocess.check_output(['ip','route','get',peer], text=True).strip()
        device = re.search(r'\bdev\s+(\S+)', route).group(1)
        if not ipaddress.ip_address(peer).is_global or not (Path('/sys/class/net')/device/'device').exists():
            raise ValueError('Public physical direct route cannot be verified')
        data = response.read(cap+1)
        if len(data)>cap:
            raise ValueError('Bounded source response exceeded registered cap')
        with path.open('xb') as stream:
            stream.write(data)
        save(path.with_suffix(path.suffix+'.route.json'), dict(url=url, final_url=response.url,
            peer=peer, route=route, physical_device=device, proxy_handler={},
            status=response.status, bytes=len(data), accepted=ref(path)))
    return path
