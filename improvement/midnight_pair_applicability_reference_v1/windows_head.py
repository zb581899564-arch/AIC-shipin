"""One anonymous metadata-only HEAD per frozen original six public objects."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
import requests

def main(candidates_path, output):
    payload = Path(candidates_path).read_bytes(); candidates = json.loads(payload)
    output = Path(output); output.mkdir(exist_ok=False)
    class NoCredentials(requests.auth.AuthBase):
        def __call__(self, request):
            return request
    routes = []
    for index, row in enumerate(candidates['selection']+candidates['ordered_engineering_reserves']):
        url = row['provider']['video_url']
        try:
            response = requests.head(url, allow_redirects=True, timeout=(10,45), auth=NoCredentials(),
                headers={'Accept-Encoding':'identity'})
            for value in [*response.history,response]:
                loc = urlparse(value.url)
                if not (loc.scheme=='https' and loc.username is None and loc.password is None
                    and (loc.hostname=='huggingface.co' or loc.hostname.endswith('.cdn.hf.co'))):
                    raise ValueError('Public source HEAD escaped publisher route')
            route = dict(video_id=row['video_id'], initial_public_url=url, metadata_only=True,
                bytes=row['provider']['size_bytes'], checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                head_status=response.status_code,
                head_history=[dict(status=v.status_code,url=v.url,location=v.headers.get('Location')) for v in response.history])
            if response.status_code==404:
                route['status']='PUBLIC_OBJECT_404'
            else:
                if not(response.status_code==200 and urlparse(response.url).hostname.endswith('.cdn.hf.co')
                    and int(response.headers['Content-Length'])==row['provider']['size_bytes'] and response.headers.get('ETag')):
                    raise ValueError('HEAD status/length/ETag mismatch')
                route.update(status='PINNED_NORMAL_PUBLIC_REDIRECT',publisher_redirect_url=response.url,etag=response.headers['ETag'])
            with (output/('%02d_%s.json'%(index,row['video_id']))).open('x',encoding='utf8') as f:json.dump(route,f,indent=2)
            routes.append(route)
            print(row['video_id'],route['status'],route['bytes'],flush=True)
        except BaseException as error:
            with (output/'failure.json').open('x',encoding='utf8') as f:json.dump(dict(video_id=row['video_id'],error=type(error).__name__,no_retry=True,successful_HEAD_receipts_preserved=True),f)
            raise
    with (output/'public_routes.json').open('x',encoding='utf8') as f:
        json.dump(dict(routes=routes,windows_video_body_bytes=0,requests_method='HEAD',anonymous_no_credentials=True,
            no_retry=True,source_candidates_sha256=hashlib.sha256(payload).hexdigest()),f,indent=2)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidates',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();main(a.candidates,a.output)
