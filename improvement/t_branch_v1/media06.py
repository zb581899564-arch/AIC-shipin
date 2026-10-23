"""First acquisition of four new original-publisher objects; no retries."""
import http.client
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import time
import traceback
from urllib.parse import urlparse

from t_io import ROOT, WORK, identity, public_route, read, save

TARGET = ROOT / 'media06'


def acquire(row):
    sid = 'L' + row['source']['source_hash'][:12]
    destination = TARGET / (sid + '.mp4')
    partial = TARGET / (sid + '.partial')
    parsed = urlparse(row['final_url'])
    if parsed.scheme != 'https':
        raise ValueError('Only registered original HTTPS objects are accepted')
    connection = http.client.HTTPSConnection(parsed.hostname, timeout=30,
                                              context=ssl.create_default_context())
    connection._create_connection = lambda address, timeout, source_address=None: socket.create_connection(
        (row['peer'], address[1]), timeout, source_address)
    started = time.monotonic()
    try:
        connection.connect()
        route = public_route(connection.sock.getpeername()[0])
        headers = {'User-Agent': 'AIC-noncommercial-T-source-admission', 'Accept-Encoding': 'identity'}
        if row['headers'].get('ETag'):
            headers['If-Match'] = row['headers']['ETag']
        connection.request('GET', parsed.path + ('?' + parsed.query if parsed.query else ''), headers=headers)
        response = connection.getresponse()
        if response.status != 200 or int(response.getheader('Content-Length', '-1')) != row['declared_bytes']:
            raise ValueError('Publisher object no longer matches its registered successful HEAD')
        save(TARGET / (sid + '_connected.json'), dict(
            source=row, **route, TLS_server_name=parsed.hostname, strict_certificate=True,
            connected_before_media_body_read=True, proxy=None))
        count = 0
        with partial.open('xb') as stream:
            while count < row['declared_bytes']:
                block = response.read(min(1 << 18, row['declared_bytes'] - count))
                if not block:
                    break
                stream.write(block)
                count += len(block)
                if time.monotonic() - started > 600:
                    raise TimeoutError('Registered per-source acquisition bound elapsed; retain partial')
        if count != row['declared_bytes'] or response.read(1):
            raise ValueError('Original object truncated or larger than bound')
        if destination.exists():
            raise FileExistsError('Do not replace a successful original media object')
        partial.rename(destination)
        result = dict(sid=sid, source=row['source'], media=identity(destination),
                      route=route, elapsed_seconds=time.monotonic() - started)
        save(TARGET / (sid + '_acceptance.json'), result)
        print('T_MEDIA06_ACCEPTED', sid, count, flush=True)
        return result
    finally:
        connection.close()


def main():
    TARGET.mkdir()
    headers = ROOT / 'source_alternatives05/headers.json'
    rows = [r for r in read(headers) if r.get('status') == 200]
    if len(rows) != 4 or len({r['source']['host'] for r in rows}) != 4:
        raise ValueError('Four independent original publishers were not available')
    total = sum(r['declared_bytes'] for r in rows)
    if total != 981518808:
        raise ValueError('Registered four-source exact media budget differs')
    disk = shutil.disk_usage(ROOT)
    clock_budget = len(rows) * 24000000
    if disk.free < total + clock_budget:
        raise ValueError('Measured free space does not fit these media and bounded native clocks')
    save(TARGET / 'registration.json', dict(
        selected=rows, media_bytes=total, bounded_native_clock_bytes=clock_budget,
        current_free_bytes=disk.free, source_headers=identity(headers),
        annotation=identity(WORK / 'general_highlight_supervision_20261021_v1/lvsum20/annotations__lvsum_72_dataset.json'),
        scope='First raw objects and native-clock admission; no model or training',
        research_use='Local student noncommercial research; original author pointers, no redistribution',
        underlying_media_rights_retained_by_publishers=True,
        summary_unselected_is_UNKNOWN_not_ordinary=True, roles_not_chosen_by_quality=True,
        resource_snapshot=dict(host=socket.gethostname(),
            tasks=subprocess.check_output(['ps', '-eo', 'pid,ppid,stat,pcpu,pmem,args', '--sort=-pcpu'], text=True)[:16000],
            RAM=subprocess.check_output(['free', '-b'], text=True),
            GPU=subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.used,memory.free,utilization.gpu', '--format=csv,noheader'], text=True))))
    accepted, failed = [], []
    for row in rows:
        try:
            accepted.append(acquire(row))
        except Exception:
            record = dict(source=row['source'], traceback=traceback.format_exc(), no_automatic_retry=True)
            save(TARGET / ('L' + row['source']['source_hash'][:12] + '_failure.json'), record)
            failed.append(record)
    save(TARGET / 'completion.json', dict(
        state='MEDIA_COMPLETE' if not failed else 'PARTIAL_MEDIA_PRESERVED',
        accepted=accepted, failed=failed, no_new_model_calls=True))


if __name__ == '__main__':
    main()
