"""Acquire one fixed author PANN checkpoint and tiny frontend source archive."""
from datetime import datetime, timezone
import hashlib
import ipaddress
import subprocess
import time
import traceback
import urllib.request
import zipfile
from common import ROOT, read, write, reference


def receive(url, path, size, checksum, algorithm, budget):
    start = time.monotonic()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers={'Accept': '*/*',
        'Accept-Encoding': 'identity', 'User-Agent': 'AIC-fixed-author-model-direct'})
    partial = path.with_suffix(path.suffix+'.partial')
    try:
        with opener.open(request, timeout=25) as response:
            peer = response.fp.raw._sock.getpeername()[0]
            route = subprocess.check_output(['ip', 'route', 'get', peer], text=True).strip()
            if not ipaddress.ip_address(peer).is_global or ' dev eno2 ' not in ' '+route+' ':
                raise ValueError('Direct physical public peer not verified')
            if response.status != 200:
                raise ValueError('Initial full-file response must be200')
            write(path.with_suffix(path.suffix+'.route.json'), dict(url=url, final_url=response.url,
                peer=peer, route=route, proxy_handler={}, expected_bytes=size))
            count = 0
            with partial.open('xb') as output:
                while True:
                    if time.monotonic()-start > budget:
                        raise TimeoutError('Registered download wall budget exceeded')
                    block = response.read(1 << 20)
                    if not block:
                        break
                    count += len(block)
                    if count > size:
                        raise ValueError('Published exact size exceeded')
                    output.write(block)
                    output.flush()
                    if count % (16 << 20) == 0:
                        print('ACQUIRED_BYTES', count, '/', size, flush=True)
            if count != size:
                raise EOFError('Incomplete published file; partial retained')
        digest = hashlib.new(algorithm, partial.read_bytes()).hexdigest()
        if digest != checksum:
            raise ValueError('Published checksum mismatch')
        partial.rename(path)
        write(path.with_suffix(path.suffix+'.acceptance.json'), dict(status='PASS_EXACT_AUTHOR_FILE',
            file=reference(path), published_checksum=algorithm+':'+checksum,
            elapsed_seconds=time.monotonic()-start))
    except BaseException as error:
        write(path.with_suffix(path.suffix+'.failure.json'), dict(error=repr(error),
            traceback=traceback.format_exc(), partial_bytes=partial.stat().st_size if partial.exists() else 0,
            automatic_retry=False))
        raise


def main():
    record = read(ROOT/'author/zenodo_record04.json')
    weight = next(x for x in record['files'] if x['key']=='Cnn14_DecisionLevelAtt_mAP=0.425.pth')
    if record['metadata']['license']['id'] != 'cc-by-4.0':
        raise ValueError('Checkpoint-use terms changed')
    wheel = next(x for x in read(ROOT/'author/torchlibrosa_pypi.json')['urls'] if x['filename'].endswith('.whl'))
    write(ROOT/'acquisition04_registration.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        model=weight, wheel=dict(filename=wheel['filename'], bytes=wheel['size'], sha256=wheel['digests']['sha256']),
        purpose='Frozen timed audio events research, eight retained external excerpts, no official data',
        model_download_budget_seconds=900, code=reference(__file__),
        baseline_unchanged=True, download_route='Explicit empty ProxyHandler and actual physical public peer per response'))
    receive(wheel['url'], ROOT/'author'/wheel['filename'], wheel['size'], wheel['digests']['sha256'], 'sha256', 60)
    with zipfile.ZipFile(ROOT/'author'/wheel['filename']) as archive:
        if archive.testzip() is not None:
            raise ValueError('Frontend archive CRC failed')
        for name in ['torchlibrosa/stft.py', 'torchlibrosa/augmentation.py',
                     'torchlibrosa-0.1.0.dist-info/LICENSE']:
            with (ROOT/'author'/name.replace('/', '__')).open('xb') as stream:
                stream.write(archive.read(name))
    receive(weight['links']['self'], ROOT/'PANN_Cnn14_DecisionLevelAtt.pth',
        weight['size'], weight['checksum'].split(':')[1], 'md5', 900)
    write(ROOT/'acquisition04_completion.json', dict(status='PASS_ONE_DIRECT_PANN_AND_FRONTEND_SOURCE',
        weight=reference(ROOT/'PANN_Cnn14_DecisionLevelAtt.pth'), no_global_install=True))


if __name__ == '__main__':
    main()
