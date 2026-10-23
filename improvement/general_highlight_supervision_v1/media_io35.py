"""Bounded new original-object receiver; validate TLS, peer, route and size before reads."""
import http.client
from pathlib import Path
import socket
import ssl
import time
from urllib.parse import urlparse
from common import ref,save,route_for


def receive(row,path,wall_seconds=360):
    path=Path(path);partial=path.with_suffix('.partial');parsed=urlparse(row['final_url'])
    if parsed.scheme!='https':raise ValueError('Only registered original HTTPS object allowed')
    connection=http.client.HTTPSConnection(parsed.hostname,timeout=25,context=ssl.create_default_context())
    connection._create_connection=lambda address,timeout,source_address=None:socket.create_connection((row['public_peer'],address[1]),timeout,source_address)
    headers={'User-Agent':'Mozilla/5.0 AIC-noncommercial-research','Accept-Encoding':'identity'}
    if row.get('etag'):headers['If-Match']=row['etag']
    started=time.monotonic()
    try:
        connection.connect();route=route_for(connection.sock.getpeername()[0])
        connection.request('GET',parsed.path+('?' + parsed.query if parsed.query else ''),headers=headers)
        response=connection.getresponse()
        save(path.with_suffix('.connected.json'),dict(status=response.status,
            length=response.getheader('Content-Length'),registered_bytes=row['bytes'],
            original_url=row['source']['url'],final_url=row['final_url'],**route,
            TLS_server_name=parsed.hostname,strict_certificate=True,before_first_media_read=True))
        if response.status!=200 or int(response.getheader('Content-Length','-1'))!=row['bytes']:
            raise ValueError('Actual original object status/length differs; no body accepted')
        count=0
        with partial.open('xb') as out:
            while count<row['bytes']:
                block=response.read(min(1<<18,row['bytes']-count))
                if not block:break
                out.write(block);count+=len(block)
                if time.monotonic()-started>wall_seconds:raise TimeoutError('New media bounded download elapsed; partial retained')
        if count!=row['bytes'] or response.read(1):raise ValueError('Actual byte extent differs')
        if path.exists():raise FileExistsError('Accepted object cannot be downloaded again')
        partial.rename(path)
        return dict(media=ref(path),route=route,etag=response.getheader('ETag'),seconds=time.monotonic()-started)
    finally:connection.close()
