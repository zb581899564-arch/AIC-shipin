"""Acquire exactly one registered checkpoint only after explicit human approval."""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import subprocess
import urllib.request

from profile_gpu import WEIGHT_BYTES, WEIGHT_URL
from provenance import reference, write_new


def verify_direct_response(response):
    """Observe the actual TLS peer and egress; do not edit host networking."""
    peer = response.fp.raw._sock.getpeername()[0]
    if not ipaddress.ip_address(peer).is_global:
        raise ValueError('Nonpublic peer; direct route not established')
    routes = json.loads(subprocess.check_output(['ip', '-j', 'route', 'get', peer], text=True))
    device = routes[0].get('dev', '')
    if not device or any(t in device.lower() for t in ['tun', 'tap', 'tailscale', 'easytier', 'wg', 'warp']):
        raise ValueError('Relay/tunnel or unknown egress requires fresh user approval')
    if not (Path('/sys/class/net') / device / 'device').exists():
        raise ValueError('Physical egress not established; do not assume zero relay')
    if response.geturl() != WEIGHT_URL:
        raise ValueError('Unregistered download redirect')
    return dict(status='OBSERVED_DIRECT_TLS_PUBLIC_CDN_PHYSICAL_EGRESS', tls_peer=peer,
                route=routes, proxy_handler='EXPLICIT_EMPTY_NO_PROXY',
                limitation='Local socket and route evidence; no assertion about unobservable upstream routing')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    auth = json.loads((root / 'weight_authorization.json').read_text())
    if auth.get('source') != 'USER_EXPLICIT_ASYNC_REPLY' or not auth.get('human_answer', '').strip():
        raise ValueError('No explicit human authorization')
    if auth['authorized_model'] != dict(url=WEIGHT_URL, bytes=WEIGHT_BYTES):
        raise ValueError('Wrong model scope')
    output = root / 'weights'
    output.mkdir()
    write_new(output / 'claim.json', dict(authorization=reference(root / 'weight_authorization.json'),
                                         url=WEIGHT_URL, expected_bytes=WEIGHT_BYTES))
    partial = output / 'I3D_8x8_R50.pyth.partial'
    h, size = hashlib.sha256(), 0
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(WEIGHT_URL, timeout=40) as response, partial.open('xb') as stream:
        route = verify_direct_response(response)
        write_new(root / 'weight_direct_route.json', route)
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > WEIGHT_BYTES:
                raise ValueError('Registered byte scope exceeded')
            h.update(chunk)
            stream.write(chunk)
    if size != WEIGHT_BYTES:
        raise ValueError('Incomplete weight; keep partial, no automatic retry')
    target = output / 'I3D_8x8_R50.pyth'
    partial.rename(target)
    write_new(root / 'weight_acceptance.json', dict(path=str(target), bytes=size, sha256=h.hexdigest(),
                                                   url=WEIGHT_URL, no_other_models_downloaded=True))


if __name__ == '__main__':
    main()
