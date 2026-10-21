"""Acquire pinned author assets over observed direct routes; no silent retries."""
import base64
import hashlib
import ipaddress
import json
from pathlib import Path
import shutil
import subprocess
import urllib.parse
import urllib.request

from common import ROOT, PREVIOUS, COMMIT, WEIGHT_BYTES, WEIGHT_URL, read, ref, write

BLOBS = {
    'models/xclip.py': 'ca5070f9eaeb9c4b4e559e830e6c22c5c29d5f1b',
    'models/cct.py': 'e0727ab48ede67b1ef9f244fd6254508c3e89c31',
    'models/mit.py': '4633f6269fc00ac61ec92ced1dec239d503597b9',
    'models/prompt.py': 'd969e3b92a5c63d5c18914c83f7ddf8cfcb0c407',
    'clip/model.py': '566c9ee42a043e09b8ab12b6fa4a37489ee91c2e',
}
ALLOWED_HOSTS = {'github.com', 'api.github.com', 'release-assets.githubusercontent.com'}


def connection(response):
    peer = response.fp.raw._sock.getpeername()[0]
    route = json.loads(subprocess.check_output(['ip', '-j', 'route', 'get', peer], text=True))
    device = route[0]['dev']
    assert ipaddress.ip_address(peer).is_global
    assert (Path('/sys/class/net') / device / 'device').exists()
    assert not any(x in device.lower() for x in ['tun', 'tap', 'tailscale', 'wg', 'warp', 'easytier'])
    return dict(peer=peer, route=route, explicit_empty_proxy=True,
                response_host=urllib.parse.urlparse(response.geturl()).hostname)


class DirectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        assert urllib.parse.urlparse(url).hostname in ALLOWED_HOSTS
        observed = connection(response)
        with (ROOT / 'downloads/redirects.jsonl').open('a') as stream:
            stream.write(json.dumps(observed) + '\n')
        return super().redirect_request(request, response, code, message, headers, url)


def fetch(url, path, maximum, exact=None):
    assert urllib.parse.urlparse(url).hostname in ALLOWED_HOSTS
    partial = path.with_suffix(path.suffix + '.partial')
    assert not path.exists() and not partial.exists()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DirectRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'AIC-external-research/1.0'})
    with opener.open(request, timeout=45) as response:
        write(path.with_suffix(path.suffix + '.route.json'), connection(response))
        size = 0
        with partial.open('xb') as stream:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                assert size <= maximum
                stream.write(chunk)
    assert size > 0 and (exact is None or size == exact)
    partial.rename(path)
    return ref(path)


def author_file(relative, blob=None):
    tag = relative.replace('/', '_')
    meta = ROOT / 'downloads' / (tag + '.api.json')
    url = (f'https://api.github.com/repos/microsoft/VideoX/git/blobs/{blob}' if blob
           else f'https://api.github.com/repos/microsoft/VideoX/contents/{relative}?ref={COMMIT}')
    fetch(url, meta, 300000)
    item = read(meta)
    data = base64.b64decode(item['content'])
    sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert sha == item['sha'] and len(data) == item['size']
    assert blob is None or sha == blob
    path = ROOT / 'author' / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
    return dict(**ref(path), git_blob=sha, author_commit=COMMIT)


def inference_port():
    changes = []
    for relative in BLOBS:
        original = ROOT / 'author' / relative
        text = original.read_text()
        # Only initialization/import wiring changes. Every tensor is subsequently
        # loaded strictly from the checkpoint; no author forward is modified.
        text = text.replace('from timm.models.layers import trunc_normal_',
                            'from torch.nn.init import trunc_normal_')
        text = text.replace('from einops import rearrange\n', '')
        text = text.replace('sys.path.append("../")', '# no global import-path mutation')
        target = ROOT / 'runtime' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x') as stream:
            stream.write(text)
        changes.append(dict(original=ref(original), inference_port=ref(target)))
    for package in ['clip', 'models']:
        (ROOT / 'runtime' / package / '__init__.py').write_text(
            '"""Scoped author inference modules; automatic download entrypoints excluded."""\n')
    return changes


def main():
    write(ROOT / 'asset_claim.json', dict(model=WEIGHT_URL, bytes=WEIGHT_BYTES,
          direct_only=True, commit=COMMIT, extra_model_or_dependency_downloads=0))
    for name in ['downloads', 'author', 'runtime', 'model']:
        (ROOT / name).mkdir()
    assert shutil.disk_usage(ROOT).free > WEIGHT_BYTES + 110000000
    files = [author_file(name, sha) for name, sha in BLOBS.items()]
    for relative in ['LICENSE', 'X-CLIP/README.md', 'X-CLIP/configs/k400/32_8.yaml']:
        files.append(author_file(relative))
    assert 'Permission is hereby granted' in (ROOT / 'author/LICENSE').read_text()
    release = ROOT / 'downloads/release.json'
    fetch('https://api.github.com/repos/nbl97/X-CLIP_Model_Zoo/releases/tags/v1.0', release, 300000)
    item = next(x for x in read(release)['assets'] if x['name'] == 'k400_32_8.pth')
    assert item['id'] == 71848091 and item['size'] == WEIGHT_BYTES
    assert item['browser_download_url'] == WEIGHT_URL
    ports = inference_port()
    weight = fetch(WEIGHT_URL, ROOT / 'model/k400_32_8.pth', WEIGHT_BYTES, WEIGHT_BYTES)
    write(ROOT / 'download_acceptance.json', dict(files=files, runtime=ports, weight=weight,
          release_asset_id=item['id'], publisher_digest=item.get('digest'),
          publisher_sha256_available=False, no_auto_download=True,
          reused_tokenizer_git_blob='0a66286b7d5019c6e221932a813768038f839c91',
          reused_BPE_git_blob='7b5088a527f720063f044eb928eee315f63b2fc0'))


if __name__ == '__main__':
    main()
