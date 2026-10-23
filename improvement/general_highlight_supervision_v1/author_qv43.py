"""New original-author QVHighlights archive admission: HEAD plus bounded prefix only."""
import gzip
import http.client
from pathlib import Path
import socket
import ssl
import struct
import urllib.request
from urllib.parse import urlparse
import zlib

from common import ROOT,read,ref,save,fetch,route_for

TARGET=ROOT/'author_qv43'
ARCHIVE='https://nlp.cs.unc.edu/data/jielei/qvh/qvhilights_videos.tar.gz'


def main():
    TARGET.mkdir()
    commit=fetch('https://api.github.com/repos/jayleicn/moment_detr/commits/main',TARGET/'commit.json',300000)
    sha=read(TARGET/'commit.json')['sha']
    for remote,name in [('data/README.md','author_data_README.md'),('data/LICENSE','annotation_LICENSE')]:
        fetch('https://raw.githubusercontent.com/jayleicn/moment_detr/'+sha+'/'+remote,TARGET/name,100000)
    if ARCHIVE not in (TARGET/'author_data_README.md').read_text():raise ValueError('Original author raw link differs')
    save(TARGET/'registration.json',dict(author='jayleicn/moment_detr',commit=sha,
        author_README=ref(TARGET/'author_data_README.md'),archive=ARCHIVE,
        scope='HEAD and first65536B original gzip prefix only; no full archive fallback, no model or training',
        old_uncertain_media_not_reused_or_relabelled=True,known_train_test_exclusion_required=True,
        labels='Original2sec relevant_clip_ids and3 actual0..4 human saliency votes; query-conditional',
        unknown='Outside annotated query spans UNKNOWN, not explicit generic ordinary',
        no_query_or_score_inference_from_official_test=True))
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request=urllib.request.Request(ARCHIVE,method='HEAD',headers={'User-Agent':'AIC-noncommercial-research','Accept-Encoding':'identity'})
    with opener.open(request,timeout=15) as response:
        route=route_for(response.fp.raw._sock.getpeername()[0]);size=response.headers.get('Content-Length')
        head=dict(url=ARCHIVE,final_url=response.url,status=response.status,
            bytes=int(size) if size else None,etag=response.headers.get('ETag'),
            last_modified=response.headers.get('Last-Modified'),accept_ranges=response.headers.get('Accept-Ranges'),**route)
    save(TARGET/'archive_head.json',head);print('AUTHOR_ARCHIVE_HEAD',head,flush=True)
    if head['status']!=200 or not head['bytes']:raise ValueError('Bounded archive access not admitted')
    request=urllib.request.Request(ARCHIVE,headers={'Range':'bytes=0-65535','Accept-Encoding':'identity','User-Agent':'AIC-noncommercial-research'})
    with opener.open(request,timeout=20) as response:
        route=route_for(response.fp.raw._sock.getpeername()[0])
        if response.status!=206 or response.headers.get('Content-Range')!=f"bytes 0-65535/{head['bytes']}":
            raise ValueError('Source ignored exact Range; do not download whole archive')
        data=response.read(65537)
        if len(data)!=65536:raise ValueError('Original bounded gzip prefix incomplete')
        path=TARGET/'original_prefix_000.bin'
        with path.open('xb') as out:out.write(data)
        save(TARGET/'prefix_receipt.json',dict(archive_head=ref(TARGET/'archive_head.json'),
            accepted=ref(path),range=[0,65535],**route,full_archive_GZIP_CRC='NOT_AVAILABLE_FOR_PARTIAL_PREFIX'))
    decoded=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(data,4<<20)
    headers=[]
    if len(decoded)>=512:
        block=decoded[:512];name=block[:100].split(b'\0',1)[0].decode(errors='replace')
        field=block[124:136].rstrip(b'\0 ');member_size=int(field or b'0',8)
        expected=int(block[148:156].strip(b'\0 ') or b'0',8)
        checksum=sum(block[:148])+8*32+sum(block[156:])
        headers.append(dict(name=name,size=member_size,type=block[156:157].decode(errors='replace'),
            original_tar_header_checksum_pass=expected==checksum))
    save(TARGET/'completion.json',dict(state='ORIGINAL_AUTHOR_DIRECT_ARCHIVE_PREFIX_ADMITTED',
        archive_head=head,first_tar_headers=headers,prefix_bytes=65536,original_gzip_prefix=True,
        full_archive_downloaded=False,no_media_member_yet_accepted=True,new_model_calls=0))
    print('ORIGINAL_AUTHOR_PREFIX',headers,flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        if TARGET.exists():save(TARGET/'failure.json',dict(error=repr(error),traceback=__import__('traceback').format_exc(),no_full_archive_fallback=True))
        raise
