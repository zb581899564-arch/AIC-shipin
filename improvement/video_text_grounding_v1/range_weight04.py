"""Direct, disjoint byte-range completion of the same author weight."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import shutil
import threading
import time
import urllib.request
import zipfile
from common import ROOT, COMMIT, WEIGHT_BYTES, read, checked, ref, write
from assets import BLOBS, DirectRedirect, connection

LOCK = threading.Lock()


def fetch_part(url, interval):
    start, stop = interval
    target = ROOT / 'weight_ranges04' / f'{start:09}_{stop:09}.bin'
    partial = target.with_suffix('.partial')
    assert not target.exists() and not partial.exists()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DirectRedirect())
    request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{stop - 1}',
                                     'User-Agent': 'AIC-research'})
    began = time.monotonic()
    with opener.open(request, timeout=40) as response:
        route = connection(response)
        assert response.status == 206
        assert response.headers['Content-Range'] == f'bytes {start}-{stop - 1}/{WEIGHT_BYTES}'
        size = 0
        with partial.open('xb') as stream:
            while data := response.read(65536):
                size += len(data)
                assert size <= stop - start
                stream.write(data)
                if time.monotonic() - began > 1200:
                    raise TimeoutError('Registered range transfer duration exceeded; preserve bytes')
    assert size == stop - start
    partial.rename(target)
    result = dict(start=start, stop=stop, file=ref(target), route=route,
                  seconds=time.monotonic() - began)
    with LOCK:
        with (ROOT / 'weight_range_success04.jsonl').open('a') as stream:
            stream.write(json.dumps(result) + '\n')
    return result


def asset_url():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), DirectRedirect())
    request = urllib.request.Request(
        'https://api.github.com/repos/nbl97/X-CLIP_Model_Zoo/releases/assets/71848091',
        headers={'Accept': 'application/octet-stream', 'User-Agent': 'AIC-research'}, method='HEAD')
    with opener.open(request, timeout=25) as response:
        assert int(response.headers['Content-Length']) == WEIGHT_BYTES
        write(ROOT / 'downloads/range_head04.json', connection(response))
        return response.geturl()


def assemble(pieces):
    temporary = ROOT / 'model/k400_32_8.assembled04'
    position = 0
    with temporary.open('xb') as output:
        for part in sorted(pieces, key=lambda r: r['start']):
            assert part['start'] == position
            path = checked(part['file'])
            assert path.stat().st_size == part['stop'] - part['start']
            with path.open('rb') as source:
                shutil.copyfileobj(source, output, 1048576)
            position = part['stop']
    assert position == WEIGHT_BYTES and temporary.stat().st_size == WEIGHT_BYTES
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
    final = ROOT / 'model/k400_32_8.pth'
    assert not final.exists()
    temporary.rename(final)
    return ref(final)


def main():
    registration = read(ROOT / 'recovery_registration04.json')
    assert read(ROOT / 'assets_remaining03_terminal.json')['exit_code'] == -15
    prefix, tail = registration['prefix'], registration['tail']
    checked(prefix['file']); checked(tail['file'])
    assert prefix['start'] == 0 and prefix['stop'] < tail['start'] and tail['stop'] == WEIGHT_BYTES
    assert shutil.disk_usage(ROOT).free > 2 * WEIGHT_BYTES + 90000000
    (ROOT / 'weight_ranges04').mkdir()
    size = 8 * 1024 * 1024
    intervals = [(a, min(a + size, tail['start'])) for a in range(prefix['stop'], tail['start'], size)]
    write(ROOT / 'weight_range_plan04.json', dict(parts=intervals, adopted=[prefix, tail],
          max_connections=8, no_overlapping_ranges=True, automatic_retries=0))
    url = asset_url()
    pieces = [prefix, tail]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_part, url, interval) for interval in intervals]
        for future in as_completed(futures):
            pieces.append(future.result())
    weight = assemble(pieces)
    originals = list(BLOBS) + ['LICENSE', 'X-CLIP/README.md', 'X-CLIP/configs/k400/32_8.yaml']
    write(ROOT / 'download_acceptance.json', dict(files=[ref(ROOT / 'author' / p) for p in originals],
          runtime=[dict(original=ref(ROOT / 'author' / p), inference_port=ref(ROOT / 'runtime' / p)) for p in BLOBS],
          author_commit=COMMIT, weight=weight, release_asset_id=71848091,
          publisher_sha256_available=False, zip_CRC=True, repeated_successful_bytes=0,
          previous_prefix_and_probe_adopted=True, explicit_transport_upgrade='remaining04',
          scientific_protocol_unchanged=True))


if __name__ == '__main__':
    main()
