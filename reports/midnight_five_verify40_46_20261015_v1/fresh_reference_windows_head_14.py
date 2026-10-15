"""One anonymous Windows HEAD per original registered object; no media body."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback
from urllib.parse import urlparse

REPORT = Path(__file__).resolve().parent
ROOT = '/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/relative_confirm'


def save(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    folder = REPORT/'fresh_reference_windows_head_14'; folder.mkdir(exist_ok=False)
    code = """from pathlib import Path
import hashlib,json
r=Path('"""+ROOT+"""');p=r/'source_candidates.json';d=json.loads(p.read_text());f=r/'control_09/failure.json'
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert json.loads(f.read_text())['stage']=='CURRENT_SIX_HEAD_ROUTES'
print(json.dumps(dict(source_candidates_ref=ref(p),rows=d['selection']+d['ordered_engineering_reserves'],old_failure_ref=ref(f),selected_bytes=d['selected_media_bytes'],maximum_pool_bytes=d['maximum_pool_bytes'])))
"""
    value = subprocess.run(['ssh', 'aic-inspur-tailscale', 'python3', '-'], input=code, capture_output=True, text=True, check=True)
    sources = json.loads(value.stdout); save(folder/'existing_successful_selection.json', sources)
    import requests
    class NoCredentials(requests.auth.AuthBase):
        def __call__(self, request):
            return request
    session = requests.Session(); session.max_redirects = 6
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
    routes, current = [], None
    save(folder/'started.json', dict(UTC=dt.datetime.now(dt.timezone.utc).isoformat(),
        operation='HEAD_ONLY_ON_SAME_ORIGINAL_SIX_URLS', source_candidates_ref=sources['source_candidates_ref'],
        old_failed_control_ref=sources['old_failure_ref'], successful_source_selection_repeated=False,
        Windows_media_body_bytes=0, requests_default_trust_env=session.trust_env, no_proxy_or_DNS_changes=True))
    try:
        for index, row in enumerate(sources['rows']):
            current = row['video_id']; url = row['provider']['video_url']
            response = session.head(url, allow_redirects=True, timeout=(10, 45), auth=NoCredentials(), headers={'Accept-Encoding': 'identity'})
            for value in [*response.history, response]:
                parsed = urlparse(value.url)
                assert parsed.scheme == 'https' and parsed.username is None and parsed.password is None
                assert parsed.hostname == 'huggingface.co' or parsed.hostname.endswith('.cdn.hf.co')
            route = dict(video_id=current, initial_public_url=url, bytes=row['provider']['size_bytes'], metadata_only=True,
                checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(), head_status=response.status_code,
                head_history=[dict(status=x.status_code, url=x.url, location=x.headers.get('Location')) for x in response.history])
            if response.status_code == 404:
                route['status'] = 'PUBLIC_OBJECT_404'
            else:
                assert response.status_code == 200 and urlparse(response.url).hostname.endswith('.cdn.hf.co')
                assert int(response.headers['Content-Length']) == row['provider']['size_bytes'] and response.headers.get('ETag')
                route.update(status='PINNED_NORMAL_PUBLIC_REDIRECT', publisher_redirect_url=response.url, etag=response.headers['ETag'])
            routes.append(route); save(folder/('route_%02d.json'%index), route)
            print(json.dumps(dict(source=current, status=route['status'], bytes=route['bytes'], successful_HEAD_count=len(routes))), flush=True)
        output = REPORT/'fresh_reference_current_routes_14.json'
        save(output, dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), windows_video_body_bytes=0,
            route_method='Same original six object anonymous Windows HEAD; Linux direct GET exact public publisher CDN; explicit remaining recovery',
            source_candidates_ref=sources['source_candidates_ref'], prior_failed_control_ref=sources['old_failure_ref'], routes=routes,
            actual_HTTP_retries=0, network_configuration_changes=0, selected_source_or_order_changed=False))
        data = output.read_bytes(); save(folder/'completion.json', dict(status='PASS_SIX_CURRENT_WINDOWS_HEAD_METADATA_NOT_MEDIA',
            metadata_path=str(output), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), successful_HEAD_count=6, windows_media_body_bytes=0))
        print(json.dumps(dict(status='PASS', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), Windows_media_body_bytes=0)), flush=True)
    except BaseException as error:
        message, trace = repr(error), traceback.format_exc()
        for route in routes:
            if route.get('publisher_redirect_url'):
                message = message.replace(route['publisher_redirect_url'], '<PUBLISHER_CDN>')
                trace = trace.replace(route['publisher_redirect_url'], '<PUBLISHER_CDN>')
        save(folder/'failure.json', dict(status='STOP_FIRST_HEAD_FAILURE_NO_RETRY', current=current, successful_HEAD_count=len(routes),
            error=message, traceback=trace, preserve_all_successful=True, windows_media_body_bytes=0))
        raise


if __name__ == '__main__':
    main()
