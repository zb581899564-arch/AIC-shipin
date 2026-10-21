"""Adopt code, resolve the same official asset using its Release API endpoint."""
import urllib.request
import urllib.parse
from common import ROOT, COMMIT, WEIGHT_BYTES, read, ref, write
from assets import BLOBS, DirectRedirect, connection, fetch


def main():
    assert read(ROOT / 'assets_remaining02_terminal.json')['exit_code'] == 1
    assert not list((ROOT / 'model').iterdir())
    write(ROOT / 'asset_remaining03_claim.json', dict(
          reason='Two browser endpoint requests timed out before any weight payload; API HEAD resolves same71848091 asset',
          successful_sources_adopted=True, weight_successes_before=0,
          direct_gate_unchanged=True, whole_model_GET_requests=1))
    url = 'https://api.github.com/repos/nbl97/X-CLIP_Model_Zoo/releases/assets/71848091'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DirectRedirect())
    request = urllib.request.Request(url, headers={'Accept': 'application/octet-stream',
          'User-Agent': 'AIC-research'}, method='HEAD')
    with opener.open(request, timeout=25) as response:
        final_url = response.geturl()
        route = connection(response)
        assert urllib.parse.urlparse(final_url).hostname == 'release-assets.githubusercontent.com'
        assert int(response.headers['Content-Length']) == WEIGHT_BYTES
        write(ROOT / 'downloads/api_asset_head03.json', dict(**route, bytes=WEIGHT_BYTES, asset_id=71848091))
    weight = fetch(final_url, ROOT / 'model/k400_32_8.pth', WEIGHT_BYTES, WEIGHT_BYTES)
    originals = list(BLOBS) + ['LICENSE', 'X-CLIP/README.md', 'X-CLIP/configs/k400/32_8.yaml']
    files = [ref(ROOT / 'author' / name) for name in originals]
    ports = [dict(original=ref(ROOT / 'author' / name), inference_port=ref(ROOT / 'runtime' / name))
             for name in BLOBS]
    write(ROOT / 'download_acceptance.json', dict(files=files, runtime=ports, weight=weight,
          author_commit=COMMIT, release_asset_id=71848091, publisher_digest=None,
          publisher_sha256_available=False, no_auto_download=True,
          preserved_failures=['assets_terminal.json','assets_remaining02_terminal.json'],
          explicit_recovery='asset_remaining03', repeated_successful_downloads=0))


if __name__ == '__main__':
    main()
