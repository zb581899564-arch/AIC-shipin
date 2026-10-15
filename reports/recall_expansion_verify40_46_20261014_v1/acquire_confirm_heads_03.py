"""First fixed-confirm public-object HEAD metadata; Windows video body is zero."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT/'new8_source_registration_01.json'
OUTPUT = ROOT/'confirm_public_routes_03.json'


def main():
    if OUTPUT.exists():
        raise ValueError('Existing successful HEAD metadata must be reused')
    registry = json.loads(REGISTRY.read_text(encoding='utf8'))
    rows = [x for x in registry['selection']+registry['ordered_engineering_reserves'] if x['group'] == 'confirm']
    assert len(rows) == 8 and len({x['video_id'] for x in rows}) == 8
    result = dict(utc=datetime.now(timezone.utc).isoformat(), windows_video_body_bytes=0,
                  source_registration_sha256=hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), routes=[])
    try:
        for row in rows:
            url = row['provider']['video_url']
            assert url == 'https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+row['youtube_id']+'.mp4'
            with requests.head(url, allow_redirects=False, timeout=(10, 25),
                               headers={'Accept-Encoding': 'identity'}) as first:
                if first.status_code == 404:
                    route = dict(video_id=row['video_id'], status='PUBLIC_OBJECT_404',
                        bytes=row['provider']['size_bytes'], initial_public_url=url, metadata_only=True)
                else:
                    assert first.status_code in (301, 302, 303, 307, 308), first.status_code
                    target = urljoin(url, first.headers['Location'])
                    parsed = urlparse(target)
                    assert parsed.scheme == 'https' and parsed.hostname.endswith('.cdn.hf.co')
                    with requests.head(target, allow_redirects=True, timeout=(10, 25),
                                       headers={'Accept-Encoding': 'identity'}) as final:
                        parsed = urlparse(final.url)
                        assert final.status_code == 200 and parsed.hostname.endswith('.cdn.hf.co'), final.status_code
                        assert int(final.headers['Content-Length']) == row['provider']['size_bytes']
                        route = dict(video_id=row['video_id'], status='PINNED_NORMAL_PUBLIC_REDIRECT',
                            bytes=row['provider']['size_bytes'], initial_public_url=url,
                            publisher_redirect_url=final.url, etag=final.headers['ETag'], metadata_only=True)
            result['routes'].append(route)
            print(json.dumps({k:route[k] for k in ('video_id', 'status', 'bytes')}, ensure_ascii=False), flush=True)
            time.sleep(0.5)
    except Exception as error:
        result.update(status='FAILED_CONFIRM_HEAD_METADATA_NOT_MEDIA_OR_SOURCE_REPLACEMENT', error=repr(error))
        with (ROOT/'confirm_HEAD_failure_03.json').open('x', encoding='utf8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        raise
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status='PASS_FIXED_CONFIRM_PUBLIC_HEAD_METADATA_ONLY',
        members=len(result['routes']), bytes=OUTPUT.stat().st_size, windows_video_body_bytes=0)))


if __name__ == '__main__':
    main()
