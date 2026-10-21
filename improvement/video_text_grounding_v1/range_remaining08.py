"""Complete only three zero-payload expired-signature ranges; adopt all successes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import threading
import time
import urllib.request
from common import ROOT, COMMIT, WEIGHT_BYTES, read, checked, ref, write
from assets import BLOBS, DirectRedirect, connection
from range_weight04 import assemble

LOCK = threading.Lock()


def fresh_url():
    # API redirects may be cached beyond their signed CDN validity. The nonce
    # changes neither repository nor asset identity and is not a proxy route.
    url = ('https://api.github.com/repos/nbl97/X-CLIP_Model_Zoo/releases/assets/71848091'
           f'?aic_remaining08={time.time_ns()}')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DirectRedirect())
    request = urllib.request.Request(url, headers={'Accept': 'application/octet-stream',
                  'User-Agent': 'AIC-research'}, method='HEAD')
    with opener.open(request, timeout=25) as response:
        assert int(response.headers['Content-Length']) == WEIGHT_BYTES
        write(ROOT / 'downloads/range_head08.json', connection(response))
        return response.geturl()


def missing_part(url, interval):
    start, stop = interval
    target = ROOT / 'weight_ranges08' / f'{start:09}_{stop:09}.bin'
    temporary = target.with_suffix('.partial')
    assert not target.exists() and not temporary.exists()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DirectRedirect())
    request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{stop - 1}',
                                    'User-Agent': 'AIC-research'})
    with opener.open(request, timeout=40) as response:
        observed = connection(response)
        assert response.status == 206
        assert response.headers['Content-Range'] == f'bytes {start}-{stop - 1}/{WEIGHT_BYTES}'
        size = 0
        with temporary.open('xb') as stream:
            while chunk := response.read(65536):
                size += len(chunk)
                assert size <= stop - start
                stream.write(chunk)
    assert size == stop - start
    temporary.rename(target)
    row = dict(start=start, stop=stop, file=ref(target), route=observed, recovery='08')
    with LOCK:
        with (ROOT / 'weight_range_success08.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
    return row


def main():
    registration = read(ROOT / 'recovery_registration08.json')
    checked(registration['old_success_ledger'])
    old = [json.loads(s) for s in (ROOT / 'weight_range_success04.jsonl').read_text().splitlines() if s.strip()]
    assert len(old) == 90
    assert read(ROOT / 'assets_remaining04_terminal.json')['exit_code'] == 1
    adopted = [registration['prefix'], registration['tail']] + old
    for part in adopted:
        checked(part['file'])
    (ROOT / 'weight_ranges08').mkdir()
    url = fresh_url()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(missing_part, url, span) for span in registration['missing']]
        for future in as_completed(futures):
            adopted.append(future.result())
    weight = assemble(adopted)
    names = list(BLOBS) + ['LICENSE','X-CLIP/README.md','X-CLIP/configs/k400/32_8.yaml']
    write(ROOT / 'download_acceptance.json', dict(files=[ref(ROOT / 'author' / p) for p in names],
          runtime=[dict(original=ref(ROOT / 'author' / p), inference_port=ref(ROOT / 'runtime' / p)) for p in BLOBS],
          author_commit=COMMIT, weight=weight, release_asset_id=71848091,
          publisher_sha256_available=False, zip_CRC=True, repeated_successful_bytes=0,
          adopted_successful_ranges=90, new_missing_ranges=3, explicit_recovery='remaining08',
          original403_and_ledgers_preserved=True, scientific_protocol_unchanged=True))


if __name__ == '__main__':
    main()
