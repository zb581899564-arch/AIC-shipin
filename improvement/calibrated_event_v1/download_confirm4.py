"""Download the four pre-registered public sources once; no media decode."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import datetime as dt
import hashlib
import json
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/calibrated_event_20261018_v1')
OUT = ROOT/'confirm4_01'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def ref(path):
    return dict(path=str(path), bytes=Path(path).stat().st_size, sha256=sha(path))


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    reg = json.loads((ROOT/'new4_confirmation_registration_01.json').read_text())
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00')), 'New work cutoff')
    require((ROOT/'download_recovery_registration_03.json').is_file(), 'Explicit zero-success public-CDN recovery required')
    require(not (OUT/'media_recovery_claim_03.json').exists(), 'Recovery already claimed')
    require(not list(OUT.glob('*_media_acceptance.json')), 'This zero-success recovery cannot redo accepted sources')
    OUT.mkdir(exist_ok=True)
    save(OUT/'media_recovery_claim_03.json', dict(utc=utc(), registration_ref=ref(ROOT/'new4_confirmation_registration_01.json'), code_ref=ref(Path(__file__)), pid=os.getpid()))
    media = OUT/'media'
    media.mkdir(exist_ok=True)
    route_rows = json.loads((ROOT/'public_cdn_header_routes_03.json').read_text())['routes']
    routes = {row['video_id']: row for row in route_rows}
    old = json.loads(Path('/home/inspur/aic_video_work/source_clear_residual_20261018_v1/registration.json').read_text())
    ids = set(reg['known_identity_snapshot']['youtube_ids'])
    known = set(reg['known_identity_snapshot']['known_media_sha256'])
    known.update(s['media']['sha256'] for s in old['sources'])
    require(not ids.intersection(s['youtube_id'] for s in reg['selection']), 'Known original source ID overlap')
    rows = []
    for i, source in enumerate(reg['selection']):
        name = source['video_id']
        public_url = source['provider_video_url']
        require(urllib.parse.urlsplit(public_url).netloc == 'huggingface.co' and public_url.endswith('/'+source['youtube_id']+'.mp4'), 'Registered public provider only')
        route = routes[name]
        require(route['public_url'] == public_url and route['status'] == 302 and route['head_only'], 'Exact public publisher HEAD redirect binding')
        url = route['redirect_url']
        parsed = urllib.parse.urlsplit(url)
        require(parsed.scheme == 'https' and parsed.hostname.endswith('.cdn.hf.co'), 'Normal public publisher CDN only; no DNS/proxy/route modification')
        expected = source['provider_size_bytes']
        accepted = None
        for attempt in range(3):
            partial = media/(name+'.attempt'+str(attempt+1)+'.partial')
            try:
                request = urllib.request.Request(url, headers={'User-Agent':'AIC-private-research/1.0'})
                with urllib.request.urlopen(request, timeout=60) as response, partial.open('xb') as f:
                    require(response.status == 200, 'Require complete response, no partial fallback')
                    count = 0
                    while True:
                        block = response.read(1024*1024)
                        if not block:
                            break
                        count += len(block)
                        require(count <= expected, 'Response exceeds fixed source byte inventory')
                        f.write(block)
                    final_host = urllib.parse.urlsplit(response.geturl()).netloc
                require(count == expected, 'Incomplete public media body')
                digest = sha(partial)
                require(digest not in known, 'Known training/formal/reference byte overlap')
                require(digest not in {v['media_ref']['sha256'] for v in rows}, 'Duplicate new confirmation bytes')
                final = media/(name+'.mp4')
                require(not final.exists(), 'Successful member must not be overwritten')
                partial.rename(final)
                accepted = dict(sid='C'+str(i).zfill(2), name=name, video_id=name, youtube_id=source['youtube_id'], author_duration_seconds=source['author_duration_seconds'], media_ref=ref(final), public_provider_url=public_url, response_final_host=final_host, selection_hash=source['selection_hash'], attempts=attempt+1, utc=utc())
                save(OUT/(accepted['sid']+'_media_acceptance.json'), accepted)
                rows.append(accepted)
                print(json.dumps(dict(accepted=name, bytes=count, source=i+1), ensure_ascii=False), flush=True)
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
                save(OUT/(name+'_cdn03_attempt'+str(attempt+1)+'_failure.json'), dict(error=repr(error), partial=str(partial), partial_bytes=partial.stat().st_size if partial.exists() else 0, utc=utc(), successful_members_untouched=True))
                if attempt == 2:
                    raise
                retry = 3
                if isinstance(error, urllib.error.HTTPError):
                    retry = min(120, max(3, int(error.headers.get('Retry-After', '3'))))
                time.sleep(retry)
        require(accepted is not None, 'No media success may become empty source')
        time.sleep(1.25)
    save(OUT/'media_completion.json', dict(status='PASS4_PUBLIC_PRIVATE_RESEARCH_MEDIA_SIZE_SHA_KNOWN_IDENTITY_ISOLATION', sources=rows, bytes=sum(v['media_ref']['bytes'] for v in rows), known_ID_count=len(ids), known_SHA_count=len(known), source_ID_intersection=0, known_byte_intersection=0, global_original_source_and_pretraining_independence='UNKNOWN', model_calls=0, native_decode=0, utc=utc()))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        save(OUT/('media_failure_'+str(os.getpid())+'.json'), dict(error=repr(error), traceback=traceback.format_exc(), successes_preserved=True, utc=utc()))
        raise
