"""One missing manifest within the same approved metadata-only allowance."""
import hashlib
import json
from pathlib import Path
import urllib.request

BASE = Path(__file__).resolve().parents[2] / 'reports/t_branch_execution_20261022_v1'


def main():
    old = BASE / 'windows_metadata10'
    output = BASE / 'windows_manifest11'
    output.mkdir()
    terminal = json.loads((old / 'completion.json').read_text(encoding='utf8'))
    pinned = json.loads((old / 'pinned_repository.json').read_text(encoding='utf8'))
    used = terminal['metadata_body_bytes']
    cap = 1536 * 1024 - used
    name = 'archive_manifest.json'
    if name not in pinned['files']:
        raise ValueError('Pinned repository did not advertise the exact manifest')
    url = ('https://huggingface.co/datasets/jhanglee/youtube-highlights-full/resolve/'
           + pinned['revision'] + '/' + name)
    request = urllib.request.Request(url, headers={'User-Agent': 'AIC-noncommercial-source-metadata',
                                                  'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(request, timeout=25) as response:
        length = response.headers.get('Content-Length')
        if response.status != 200 or (length and int(length) >= cap):
            raise ValueError('Not bounded manifest metadata; no body read')
        data = response.read(cap)
        with (output / name).open('xb') as stream:
            stream.write(data)
        if len(data) == cap or (length and len(data) != int(length)):
            raise ValueError('Incomplete or oversized manifest; retain received bytes')
        json.loads(data)
    record = dict(state='ADDITIONAL_MANIFEST_COMPLETE', pinned_revision=pinned['revision'],
                  original_authorization=str(old / 'authorization.json'),
                  adopted_metadata_body_bytes=used, new_metadata_bytes=len(data),
                  cumulative_metadata_body_bytes=used + len(data),
                  maximum_authorized_bytes=2097152, media_body_bytes=0,
                  manifest_sha256=hashlib.sha256(data).hexdigest(), strict_TLS=True,
                  existing_Windows_network_no_configuration_changes=True)
    with (output / 'completion.json').open('x', encoding='utf8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
