"""Small immutable receipts and explicit direct author-source acquisition."""
import hashlib
import ipaddress
import json
from pathlib import Path
import subprocess
import urllib.request

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK / 'sprint_audio_events_20261021_v1'
OLD = WORK / 'bottleneck_24h_20261019_v1/audio_semantic23'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def reference(path):
    path = Path(path).resolve(strict=True)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def checked(value):
    path = Path(value['path']).resolve(strict=True)
    if not path.is_relative_to(WORK) or reference(path) != value:
        raise ValueError('Frozen asset differs or leaves project root')
    return path


def direct_get(url, name, limit=2000000):
    """Persist one bounded metadata response; never proxy or silent retry."""
    target = ROOT / 'author' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError('Do not repeat accepted source acquisition')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers={'User-Agent': 'AIC-direct-author-audit',
        'Accept': 'application/vnd.github+json', 'Accept-Encoding': 'identity'})
    with opener.open(request, timeout=25) as response:
        peer = response.fp.raw._sock.getpeername()[0]
        route = subprocess.check_output(['ip', 'route', 'get', peer], text=True).strip()
        if not ipaddress.ip_address(peer).is_global or ' dev eno2 ' not in ' '+route+' ':
            raise ValueError('Physical public direct route not confirmed')
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Bounded metadata size exceeded')
        with target.open('xb') as stream:
            stream.write(data)
        write(target.with_suffix(target.suffix+'.route.json'), dict(url=url,
            final_url=response.url, peer=peer, route=route, proxy_handler={},
            response_status=response.status, accepted=reference(target)))
    return target
