"""Explicit final missing bytes only after the bounded transport05 failure."""
import hashlib
import http.client
import ipaddress
import re
import subprocess
import urllib.error
import urllib.request
from control import ROOT, read, write, append, reference


def adopted_segments():
    files = [ROOT / 'weight_remaining03/prefix.bin', ROOT / 'transport_probe04/api_raw.bin']
    cursor = sum(p.stat().st_size for p in files)
    for path in sorted((ROOT / 'weight_remaining05').glob('*.bin'), key=lambda p: int(p.name.split('_')[0])):
        start, end = map(int, re.fullmatch(r'(\d+)_(\d+)\.bin', path.name).groups())
        size = path.stat().st_size
        if not size:
            continue
        if start != cursor or size > end - start + 1:
            raise ValueError('Original ranges are not a contiguous known prefix')
        files.append(path)
        cursor += size
    return files, cursor


def fetch_segment(opener, url, start, end, total, folder, counter):
    target = folder / (str(start) + '_' + str(end) + '.bin')
    with target.open('xb') as output:
        position = start
        while position <= end:
            counter[0] += 1
            if counter[0] > 12:
                raise ValueError('Explicit final12 request budget exhausted')
            begin = position
            record = dict(begin=begin, end=end, request=counter[0])
            request = urllib.request.Request(url, headers={'User-Agent': 'AIC-S0-final-direct-range',
                'Accept': 'application/vnd.github.raw+json', 'Range': f'bytes={begin}-{end}', 'Accept-Encoding': 'identity'})
            try:
                with opener.open(request, timeout=15) as response:
                    peer = response.fp.raw._sock.getpeername()[0]
                    route = subprocess.check_output(['ip', 'route', 'get', peer], text=True).strip()
                    if not ipaddress.ip_address(peer).is_global or ' dev eno2 ' not in ' ' + route + ' ':
                        raise ValueError('Direct physical public route not confirmed')
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {begin}-{end}/{total}':
                        raise ValueError('Exact remaining binary Range not supported')
                    record.update(peer=peer, route=route, rate_remaining=response.headers.get('X-RateLimit-Remaining'))
                    while position <= end:
                        try:
                            block = response.read(min(16384, end - position + 1))
                        except http.client.IncompleteRead as error:
                            if error.partial:
                                output.write(error.partial);output.flush();position += len(error.partial)
                            raise
                        if not block:
                            raise EOFError('Bounded server response ended before registered range')
                        output.write(block);output.flush();position += len(block)
                record.update(status='EXACT_RANGE_COMPLETE', completed_end=position - 1)
            except (ValueError, urllib.error.HTTPError):
                raise
            except (OSError, EOFError, http.client.IncompleteRead) as error:
                record.update(error=repr(error), remaining_start=position)
            append(ROOT / 'weight_ranges06.jsonl', record)
    return target


def main():
    if not (ROOT / 'weight_failure05.json').exists():
        raise ValueError('Only explicit original05 failure may enter this remaining recovery')
    base = read(ROOT / 'weight_registration02.json')
    total = base['expected_weight_bytes']
    files, cursor = adopted_segments()
    write(ROOT / 'weight_recovery_registration06.json', dict(status='FINAL_REMAINING_ONLY', expected=total,
        adopted_bytes=cursor, remaining_bytes=total - cursor, source=read(ROOT / 'weight_recovery_registration05.json')['source_url'],
        all_prior_ranges=[reference(p) for p in files], request_max=12, each_chunk_max=131072,
        no_fullfile_or_relay_fallback=True, old_failure05_preserved=True))
    folder = ROOT / 'weight_remaining06'
    folder.mkdir()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = read(ROOT / 'weight_recovery_registration06.json')['source']
    counter = [0]
    while cursor < total:
        end = min(total - 1, cursor + 131071)
        files.append(fetch_segment(opener, url, cursor, end, total, folder, counter))
        cursor = end + 1
        print('FINAL_WEIGHT', cursor, '/', total, flush=True)
    raw = b''.join(p.read_bytes() for p in files)
    if len(raw) != total or hashlib.sha1(('blob ' + str(total) + '\0').encode() + raw).hexdigest() != base['expected_git_blob']:
        raise ValueError('Full published model Git blob mismatch')
    (ROOT / 'weights').mkdir()
    path = ROOT / 'weights/author_mobilenet_gaic.pth'
    with path.open('xb') as stream:
        stream.write(raw)
    result = dict(status='PASS_EXACT_FULL_AUTHOR_WEIGHT_DIRECT', **reference(path),
        git_blob=base['expected_git_blob'], final_range_requests=counter[0], all_prior_successful_bytes_adopted=True,
        one_model=True, all_failed_partial_bytes_preserved=True)
    write(ROOT / 'weight_acceptance06.json', result)
    print(result)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        write(ROOT / 'weight_failure06.json', dict(error=repr(error), all_partial_bytes_preserved=True))
        raise
