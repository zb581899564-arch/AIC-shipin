"""Small immutable receipts and source-verified, proxy-free metadata reads."""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import urllib.request

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK / 'general_highlight_supervision_20261021_v1'


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


def route_for(peer):
    route = subprocess.check_output(['ip', 'route', 'get', peer], text=True).strip()
    device = re.search(r'\bdev\s+(\S+)', route).group(1)
    if not ipaddress.ip_address(peer).is_global or not (Path('/sys/class/net') / device / 'device').exists():
        raise ValueError('Public peer and physical direct route not verified')
    return dict(public_peer=peer, route=route, physical_device=device, proxy_handler={})


def fetch(url, path, cap):
    path = Path(path)
    request = urllib.request.Request(url, headers={
        'User-Agent': 'AIC-noncommercial-source-research', 'Accept-Encoding': 'identity'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    partial = path.with_name(path.name + '.partial')
    with opener.open(request, timeout=25) as response:
        route = route_for(response.fp.raw._sock.getpeername()[0])
        declared = response.headers.get('Content-Length')
        if declared is not None and int(declared) > cap:
            raise ValueError('Declared source response exceeds bounded scope')
        count = 0
        with partial.open('xb') as stream:
            while True:
                data = response.read(min(1 << 18, cap + 1 - count))
                if not data:
                    break
                count += len(data)
                if count > cap:
                    raise ValueError('Source response exceeds bounded scope')
                stream.write(data)
        if declared is not None and count != int(declared):
            raise ValueError('Declared source length differs')
        if path.exists():
            raise FileExistsError('Successful source acquisition cannot be repeated')
        partial.rename(path)
        receipt = dict(url=url, final_url=response.url, status=response.status,
                       accepted=ref(path), **route)
        save(path.with_name(path.name + '.route.json'), receipt)
        return receipt
