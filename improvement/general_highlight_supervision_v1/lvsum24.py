"""Acquire eight new original recordings, with route verification before media reads."""
from collections import Counter
import http.client
from pathlib import Path
import shutil
import socket
import ssl
import time
import traceback
from urllib.parse import urlparse

from common import ROOT, read, ref, save, route_for
from lvsum20 import TARGET

MEDIA = ROOT/'media24'


def acquire(row):
    sid='L'+row['source']['source_hash'][:12]
    path=MEDIA/(sid+'.mp4');partial=MEDIA/(sid+'.partial')
    url=row['final_url'];parsed=urlparse(url)
    if parsed.scheme!='https':raise ValueError('Only strict original HTTPS source')
    peer=row['public_peer']
    connection=http.client.HTTPSConnection(parsed.hostname,timeout=25,context=ssl.create_default_context())
    connection._create_connection=lambda address,timeout,source_address=None: socket.create_connection((peer,address[1]),timeout,source_address)
    headers={'User-Agent':'Mozilla/5.0 AIC-noncommercial-research','Accept-Encoding':'identity'}
    if row.get('etag'):headers['If-Match']=row['etag']
    started=time.monotonic()
    try:
        connection.connect()
        actual=route_for(connection.sock.getpeername()[0])
        connection.request('GET',parsed.path+('?' + parsed.query if parsed.query else ''),headers=headers)
        response=connection.getresponse()
        if response.status!=200 or int(response.getheader('Content-Length','-1'))!=row['bytes']:
            raise ValueError('Original object status or length differs from registered HEAD')
        save(MEDIA/(sid+'_connected.json'),dict(url=url,registered_head=row,**actual,
            TLS_server_name=parsed.hostname,strict_certificate=True,before_first_media_read=True))
        count=0
        with partial.open('xb') as out:
            while count<row['bytes']:
                block=response.read(min(1<<18,row['bytes']-count))
                if not block:break
                out.write(block);count+=len(block)
                if time.monotonic()-started>360:raise TimeoutError('Bounded original source download elapsed; partial retained')
        if count!=row['bytes'] or response.read(1):raise ValueError('Incomplete or oversized original media')
        if path.exists():raise FileExistsError('Successful media cannot be acquired again')
        partial.rename(path)
        result=dict(sid=sid,source=row['source'],media=ref(path),route=actual,
            publisher_object_etag=response.getheader('ETag'),elapsed_seconds=time.monotonic()-started)
        save(MEDIA/(sid+'_acceptance.json'),result)
        print('MEDIA_ACCEPTED',sid,row['source']['host'],count,flush=True)
        return result
    finally:
        connection.close()


def main():
    MEDIA.mkdir()
    accepted=read(TARGET/'publisher_routes23.json')
    candidates=[row for row in accepted if 0<row['bytes']<=200000000]
    candidates.sort(key=lambda row:row['source']['source_hash'])
    selected=candidates[:8]
    if len(selected)!=8:raise ValueError('Eight new raw recordings not available under bounded scope')
    baseline=ref('/home/inspur/aic_video_work/semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    if baseline['bytes']!=384630 or baseline['sha256']!='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3':
        raise ValueError('Protected40.47 changed')
    total=sum(r['bytes'] for r in selected);free=shutil.disk_usage(ROOT).free
    if free<total+2*24857564:raise ValueError('Actual media and minimum downstream footprint exceed available capacity')
    save(MEDIA/'registration.json',dict(selected=selected,total_media_bytes=total,
        independent_recordings=8,distinct_publishers=len({r['source']['host'] for r in selected}),
        roles={r['source']['source_hash']:('development' if i<5 else 'held_recording') for i,r in enumerate(selected)},
        publisher_overlap_across_roles_possible=True,global_content_or_pretraining_overlap='UNKNOWN',
        original_annotation=ref(TARGET/'annotations__lvsum_72_dataset.json'),
        author_commit=read(TARGET/'commit.json')['sha'],protected_baseline=baseline,
        no_quality_metric_seen=True,source_choice='First8 valid original-publisher sources by registered SHA, object<=200MB; no quality selection',
        payload_scope_adjustment='Earlier HEAD admissibility150MB was metadata screening; bounded media protocol now explicitly200MB per source to include184217538B original documentary',
        research_scope='Local noncommercial human-summary preference supervision; never explicit ordinary',
        all_reviewers_required=True,no_original_media_labels_or_adaptations_redistributed=True,
        no_closed_service_or_426_in_this_stage=True,actual_free_bytes=free))
    rows=[];failures=[]
    for row in selected:
        try:rows.append(acquire(row))
        except Exception as error:
            failure=dict(source=row['source'],error=repr(error),traceback=traceback.format_exc())
            failures.append(failure);save(MEDIA/('L'+row['source']['source_hash'][:12]+'_failure.json'),failure)
            print('MEDIA_FAILED',row['source']['host'],repr(error),flush=True)
    save(MEDIA/'completion.json',dict(state='MEDIA_COMPLETE' if not failures else 'PARTIAL_MEDIA_REQUIRES_EXPLICIT_REMAINING',
        accepted=rows,failures=failures,successful_sources=len(rows),downloaded_bytes=sum(r['media']['bytes'] for r in rows),
        no_silent_retries=True,no_new_GPU=True,baseline_unchanged=True))


if __name__=='__main__':main()
