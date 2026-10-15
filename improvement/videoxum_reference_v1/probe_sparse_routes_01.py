"""HEAD-only immutable publisher routes for the frozen fresh source cohort."""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from pathlib import Path
import json
import requests

from stage_common_04 import read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/sparse_context_iteration_20261013_v1'


def probe(row):
    public = row['provider']['video_url']
    if public != 'https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+row['youtube_id']+'.mp4':
        raise ValueError('Unexpected public provider identity URL')
    response = requests.head(public, allow_redirects=True, timeout=(10, 40), headers={'Accept-Encoding': 'identity'})
    final = urlparse(response.url)
    if response.status_code != 200 or final.scheme != 'https' or not final.hostname.endswith('.cdn.hf.co'):
        raise ValueError('Registered normal publisher redirect unavailable: '+row['video_id'])
    size, etag = int(response.headers['Content-Length']), response.headers['ETag']
    if size != row['provider']['size_bytes'] or not etag:
        raise ValueError('Pinned public object size or version changed')
    return dict(video_id=row['video_id'], bytes=size, initial_public_url=public,
                publisher_redirect_url=response.url, etag=etag, body_downloads=0)


def main():
    out = REPORT/'new_confirm_routes_01.json'
    if out.exists():
        raise ValueError('Successful route inventory already exists; no repeated successful probe')
    reg_path = REPORT/'new_confirm_source_registration_01.json'
    reg = read(reg_path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        routes = list(pool.map(probe, reg['selection']+reg['ordered_engineering_reserves']))
    save(out, routes)
    save(REPORT/'new_confirm_route_acceptance_01.json', dict(status='PASS_PUBLIC_PUBLISHER_HEAD_SIZE_ETAG_ROUTES_NOT_MEDIA_NATIVE_ADMISSION',
         utc=utc(), source_registration_sha256=sha(reg_path), routes_sha256=sha(out), selected_sources=8,
         registered_pool_sources=len(routes), selected_bytes=reg['selected_media_payload_bytes'],
         maximum_pool_bytes=sum(x['bytes'] for x in routes), public_data_source_to_Linux_continuing_route_exception=True,
         Windows_video_body_bytes=0, Linux_video_body_bytes=0, new_model_calls=0, requires_native_and_CPU_acceptance=True))
    print(json.dumps(dict(status='PASS_FRESH_PUBLIC_HEAD_ROUTES',pool_sources=len(routes),
        selected_sources=8,selected_bytes=reg['selected_media_payload_bytes'],maximum_pool_bytes=sum(x['bytes'] for x in routes),video_body_bytes=0)))


if __name__ == '__main__':
    main()
