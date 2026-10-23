"""Explicit remaining author metadata and independent archive route check; adopt commit."""
import base64
import http.client
import socket
import ssl
import subprocess
from urllib.parse import urlparse
import zlib

from common import ROOT,read,ref,save,fetch,route_for
from author_qv43 import TARGET,ARCHIVE


def main():
    if 'timed out' not in read(TARGET/'failure.json')['error']:
        raise ValueError('Expected43 metadata-only timeout differs')
    sha=read(TARGET/'commit.json')['sha']
    save(TARGET/'remaining44_registration.json',dict(adopted_commit=ref(TARGET/'commit.json'),
        prior_failure=ref(TARGET/'failure.json'),
        repair='Use official GitHub contents API only for missing text; independently probe exact author archive IPv4',
        no_successful_source_or_media_repeated=True,no_global_network_change=True))
    headers=TARGET/'archive44_head.headers'
    command=['curl','--noproxy','*','--ipv4','--head','--location','--max-redirs','3','--proto','=https','--proto-redir','=https',
        '--connect-timeout','6','--max-time','20','--silent','--show-error','--dump-header',str(headers),'--output','/dev/null',
        '--write-out','%{remote_ip}|%{http_code}|%{url_effective}',ARCHIVE]
    process=subprocess.run(command,capture_output=True,text=True,timeout=25)
    peer,status,url=process.stdout.strip().split('|',2)
    lines=headers.read_text().splitlines();lengths=[int(l.split(':',1)[1]) for l in lines if l.lower().startswith('content-length:')]
    head=dict(url=ARCHIVE,final_url=url,exit=process.returncode,status=status,
        bytes=lengths[-1] if lengths else None,stderr=process.stderr,body_bytes=0)
    if process.returncode==0:head.update(route_for(peer))
    save(TARGET/'archive44_head.json',head);print('AUTHOR_HEAD44',head,flush=True)
    text_refs=[]
    for remote,name in [('data/README.md','author_data_README44.md'),('data/LICENSE','annotation_LICENSE44')]:
        api=TARGET/(name+'.api.json')
        fetch('https://api.github.com/repos/jayleicn/moment_detr/contents/'+remote+'?ref='+sha,api,100000)
        data=read(api)
        if data.get('encoding')!='base64':raise ValueError('Exact author file encoding differs')
        payload=base64.b64decode(data['content'])
        if len(payload)!=data['size']:raise ValueError('Author file declared size differs')
        with (TARGET/name).open('xb') as out:out.write(payload)
        text_refs.append(ref(TARGET/name))
    if ARCHIVE not in (TARGET/'author_data_README44.md').read_text():raise ValueError('Pinned author raw link differs')
    if head['exit'] or head['status']!='200' or not head['bytes']:
        save(TARGET/'completion44.json',dict(state='AUTHOR_METADATA_COMPLETE_ARCHIVE_DIRECT_ROUTE_NOT_ADMITTED',
            original_author_files=text_refs,head=head,new_media_bytes=0,new_model_calls=0));return
    parsed=urlparse(url);connection=http.client.HTTPSConnection(parsed.hostname,timeout=20,context=ssl.create_default_context())
    connection._create_connection=lambda addr,timeout,source_address=None:socket.create_connection((peer,addr[1]),timeout,source_address)
    try:
        connection.connect();route=route_for(connection.sock.getpeername()[0])
        connection.request('GET',parsed.path,headers={'Range':'bytes=0-65535','Accept-Encoding':'identity','User-Agent':'AIC-noncommercial-research'})
        response=connection.getresponse()
        if response.status!=206 or response.getheader('Content-Range')!=f"bytes 0-65535/{head['bytes']}":
            raise ValueError('Exact Range ignored; no full download permitted')
        data=response.read(65537)
        if len(data)!=65536:raise ValueError('Bounded prefix incomplete')
        path=TARGET/'original_prefix_00044.bin'
        with path.open('xb') as out:out.write(data)
        decoded=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(data,4<<20)
        block=decoded[:512]
        if len(block)!=512:raise ValueError('First original tar header absent')
        expected=int(block[148:156].strip(b'\0 ') or b'0',8)
        if expected!=sum(block[:148])+8*32+sum(block[156:]):raise ValueError('Original tar header checksum differs')
        first=dict(name=block[:100].split(b'\0',1)[0].decode(),size=int(block[124:136].rstrip(b'\0 ') or b'0',8),type=block[156:157].decode())
        save(TARGET/'prefix44_receipt.json',dict(accepted=ref(path),range=[0,65535],**route,
            original_tar_header_checksum=True,full_gzip_CRC='UNAVAILABLE_FOR_PARTIAL_PREFIX'))
        save(TARGET/'completion44.json',dict(state='DIRECT_ORIGINAL_AUTHOR_ARCHIVE_PREFIX_ADMITTED',
            head=head,first_header=first,prefix_bytes=65536,source_files=text_refs,new_model_calls=0))
        print('ORIGINAL_AUTHOR_PREFIX44',first,flush=True)
    finally:connection.close()


if __name__=='__main__':
    try:main()
    except Exception as error:
        save(TARGET/'remaining44_failure.json',dict(error=repr(error),traceback=__import__('traceback').format_exc(),no_full_archive_fallback=True));raise
