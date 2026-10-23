"""Frozen new daily-activity recordings from retained author metadata, HEADs only."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import re
import urllib.request

from common import ROOT,WORK,read,ref,save,route_for

TARGET=ROOT/'fresh_videoxum30'
OLD=WORK/'videoxum_reference_iteration_20261013_v1'
INCLUDE=re.compile(r'\b(cook\w*|kitchen|bak\w*|wash\w*|clean\w*|paint\w*|draw\w*|makeup|make.up|hair\w*|knit\w*|sew\w*|garden\w*|plant\w*|danc\w*|guitar|piano|drum\w*|sing\w*|repair\w*|wood\w*|brush\w*|shav\w*|iron\w*|dog|cat|pet\w*|laundry|dish\w*|craft\w*)\b',re.I)
EXCLUDE=re.compile(r'\b(competi\w*|tournament|stadium|soccer|football|basketball|baseball|golf|boxing|wrestl\w*|fenc\w*|tennis|ski\w*|skate\w*|surf\w*|vault\w*|diving|gymnast\w*|racing|race|athlet\w*)\b',re.I)


def original_ids(value):
    result=set()
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='youtube_id' and isinstance(item,str):result.add(item)
            result.update(original_ids(item))
    elif isinstance(value,list):
        for item in value:result.update(original_ids(item))
    elif isinstance(value,str) and re.fullmatch(r'v_[A-Za-z0-9_-]{11}',value):result.add(value[2:])
    return result


def exposures():
    exclusions=read(OLD/'known_source_exclusions_01.json')
    known=set(exclusions['youtube_ids']);bindings=[];absent=[]
    paths=[OLD/'effective20_source_registration_05.json',OLD/'direct_pool_inventory_06.json',
        OLD/'direct_cohort_06/completion.json',
        WORK/'sparse_context_iteration_20261013_v1/new_confirm_source_registration_01.json',
        WORK/'recall_expansion_verify40_46_20261014_v1/new8_source_registration_01.json']
    for path in paths:
        if path.exists():known.update(original_ids(read(path)));bindings.append(ref(path))
        else:absent.append(str(path))
    asset=WORK/'native_preference_20261019_v1/assets.private.json'
    if asset.exists():
        info=read(asset);bindings.append(ref(asset))
        source=info.get('source_registration_ref')
        if source:
            path=__import__('pathlib').Path(source['path'])
            if ref(path)['sha256']!=source['sha256']:raise ValueError('Historical source registration changed')
            known.update(original_ids(read(path)));bindings.append(ref(path))
    return known,dict(known_exclusions=ref(OLD/'known_source_exclusions_01.json'),
        bindings=bindings,absent_optional_files=absent,global_exposure_or_reposted_content='UNKNOWN')


def head(source):
    url='https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/'+source['youtube_id']+'.mp4'
    result=dict(source=source,initial_public_url=url,media_bytes=0)
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request=urllib.request.Request(url,method='HEAD',headers={
            'User-Agent':'AIC-noncommercial-research','Accept-Encoding':'identity','Cache-Control':'no-cache'})
        with opener.open(request,timeout=15) as response:
            direct=route_for(response.fp.raw._sock.getpeername()[0])
            length=response.headers.get('Content-Length')
            result.update(status=response.status,bytes=int(length) if length else None,
                etag=response.headers.get('ETag'),final_url=response.url,**direct)
            result['media_admissible']=(response.status==200 and length is not None and 0<int(length)<=40000000)
    except Exception as error:result.update(error=repr(error),media_admissible=False)
    print('NEW_SOURCE_HEAD',source['video_id'],result.get('status'),result.get('bytes'),result.get('error','')[:160],flush=True)
    return result


def main():
    TARGET.mkdir();author=OLD/'metadata_02/val_videoxum.json'
    identity=ref(author)
    if identity['sha256']!='2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556':
        raise ValueError('Retained original author annotations differ')
    known,evidence=exposures();candidates=[]
    for row in read(author):
        vid=row['video_id'];youtube=vid[2:] if vid.startswith('v_') else vid
        text=' '.join(row['tsum'])
        if youtube in known or not 30<=float(row['duration'])<=180 or EXCLUDE.search(text) or not INCLUDE.search(text):continue
        if len(row['timestamps'])!=len(row['vsum']) or any(len(event)!=10 for event in row['vsum']):continue
        candidates.append(dict(video_id=vid,youtube_id=youtube,duration_seconds=row['duration'],
            source_hash=hashlib.sha256(('FRESH-DAILY-VXM30/'+youtube).encode()).hexdigest(),
            category_cues=sorted(set(x.lower() for x in INCLUDE.findall(text))),
            original_caption_diagnostic=text[:700]))
    candidates.sort(key=lambda r:r['source_hash']);pool=candidates[:48]
    save(TARGET/'registration.json',dict(original_author_annotation=identity,
        exclusions=evidence,known_excluded_ids=len(known),eligible_count=len(candidates),
        frozen_pool=pool,scope='Only new noncompetitive daily-activity source admission; no model metric or annotation rewriting',
        source_choice='Fixed caption-domain regex then independent source SHA; no observed score or model-output selection',
        target_sources=32,development_sources=24,held_sources=8,
        publisher='TornadoLabs/activitynet',publisher_revision='bc9c567ea67be43daf443cddb832ed983e5ccae5',
        upstream_rights='Academic source terms; underlying uploader ownership unchanged; no raw redistribution',
        original_author_annotation_license='Apache-2.0, not a blanket video copyright relicense',
        new_scope='Bounded local noncommercial research; new training requires separate source/input protocol',
        user_source_download_policy='Only actual public direct physical route; no proxy fallback',
        raw_vsum_units='Original continuous seconds, 10 raters; onehot1fps not stretched',
        labels='Shortened caption-event summaries, not explicit ordinary; outside caption coverage UNKNOWN',
        no_GPU_or_training_here=True,no_42GB_archive_scan=True))
    with ThreadPoolExecutor(max_workers=3) as pool_executor:results=list(pool_executor.map(head,pool))
    save(TARGET/'routes.json',results)
    selected=[r for r in results if r.get('media_admissible')][:32]
    save(TARGET/'completion.json',dict(state='NEW_SOURCE_ROUTE_ADMISSION_COMPLETE' if len(selected)==32 else 'INSUFFICIENT_DIRECT_NEW_SOURCES_NO_TRAINING',
        selected=selected,selected_sources=len(selected),selected_media_bytes=sum(r['bytes'] for r in selected),
        new_media_downloads=0,new_model_calls=0,all_original_annotations_reused_without_download=True))
    print('FRESH_SOURCE_RESULT',len(candidates),len(selected),sum(r['bytes'] for r in selected),flush=True)


if __name__=='__main__':main()
