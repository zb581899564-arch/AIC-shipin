"""Authorized Windows metadata-only exception; never reads an archive/media body."""
import hashlib
import json
from pathlib import Path
import ssl
import traceback
import urllib.error
import urllib.request

REPORT = Path(__file__).resolve().parents[2] / 'reports/t_branch_execution_20261022_v1'
TARGET = REPORT / 'windows_metadata10'
REPO = 'jhanglee/youtube-highlights-full'
BODY_BUDGET = 1536 * 1024  # Leave room below the authorized 2 MiB for transport overhead.


def save(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def identity(path):
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BoundedMetadata:
    def __init__(self):
        self.used = 0
        self.requests = []
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()))

    def get(self, url, name):
        remaining = BODY_BUDGET - self.used
        if remaining <= 1:
            raise ValueError('Metadata exception budget exhausted')
        request = urllib.request.Request(url, headers={'User-Agent': 'AIC-noncommercial-source-metadata',
                                                      'Accept-Encoding': 'identity'})
        with self.opener.open(request, timeout=25) as response:
            length = response.headers.get('Content-Length')
            if response.status != 200 or (length is not None and int(length) >= remaining):
                raise ValueError('Response is not bounded metadata; no body read')
            data = response.read(remaining)
            self.used += len(data)
            path = TARGET / name
            with path.open('xb') as stream:
                stream.write(data)
            if len(data) == remaining or (length is not None and len(data) != int(length)):
                raise ValueError('Metadata payload incomplete or reaches reserved cap')
            record = dict(url=url, final_url=response.url, status=response.status,
                          file=identity(path), strict_TLS=True,
                          route='Existing Windows network; non-direct/unknown explicitly authorized')
            self.requests.append(record)
            save(TARGET / (name + '.receipt.json'), record)
            return data

    def head_location(self, url):
        opener = urllib.request.build_opener(NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        request = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'AIC-noncommercial-source-metadata', 'Accept-Encoding': 'identity'})
        try:
            response = opener.open(request, timeout=25)
        except urllib.error.HTTPError as error:
            if error.code not in [301, 302, 303, 307, 308]:
                raise
            response = error
        with response:
            record = dict(url=url, status=response.code, headers=dict(response.headers),
                          body_bytes_read=0, media_not_downloaded=True)
            self.requests.append(dict(method='HEAD', **record))
            save(TARGET / 'archive_head_redirect.json', record)
            return record


def main():
    TARGET.mkdir()
    save(TARGET / 'authorization.json', dict(
        user_answer='允许这次≤2MiB元数据例外',
        user_question='Linux直连Hugging Face入口及三个公开DNS诊断均失败。是否允许这次仅通过Windows现有网络读取 jhanglee/youtube-highlights-full 的API、清单和CDN下载地址信息，总量不超过2MiB？可能消耗机场流量；不在Windows下载视频，视频仍须经Linux实核直连后才取小试成员。项目AGENTS.md要求非直连或路线不明的下载单独询问。',
        authorized_max_bytes=2097152, maximum_metadata_body_bytes=BODY_BUDGET,
        no_proxy_DNS_route_or_service_changes=True, no_video_or_model_body=True,
        source_repository=REPO))
    client = BoundedMetadata()
    try:
        api = json.loads(client.get('https://huggingface.co/api/datasets/' + REPO, 'api.json'))
        revision = api['sha']
        names = [r['rfilename'] for r in api.get('siblings', [])]
        save(TARGET / 'pinned_repository.json', dict(revision=revision, files=names,
            card=api.get('cardData'), gated=api.get('gated'), original_author=False))
        root = 'https://huggingface.co/datasets/' + REPO + '/resolve/' + revision + '/'
        for name in ['README.md', 'manifest.json', 'SHA256SUMS']:
            if name in names:
                client.get(root + name, name)
        archive = 'youtube_highlights_full.tar'
        if archive not in names:
            raise ValueError('Expected single original-media archive was not published')
        client.head_location(root + archive + '?download=true')
        save(TARGET / 'completion.json', dict(state='PINNED_METADATA_AND_REDIRECT_COMPLETE',
            metadata_body_bytes=client.used, requests=client.requests,
            archive_body_bytes=0, Linux_direct_media_check_still_required=True))
        print('METADATA10_COMPLETE', revision, client.used, flush=True)
    except Exception:
        save(TARGET / 'failure.json', dict(traceback=traceback.format_exc(),
            metadata_body_bytes=client.used, requests=client.requests,
            archive_body_bytes=0, no_automatic_retry=True))
        raise


if __name__ == '__main__':
    main()
