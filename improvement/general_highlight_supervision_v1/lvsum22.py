"""Record malformed sources without editing labels; probe bounded original publishers."""
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import urllib.request
from urllib.parse import urlparse

from common import ROOT, read, ref, save, route_for
from lvsum20 import TARGET

PUBLISHERS = {
    'ndtvod.pc.cdn.bitgravity.com': 'NDTV publisher news CDN',
    'scdn.rohde-schwarz.com': 'Rohde & Schwarz original instrumentation demonstration',
    'calgaryjournal.ca': 'Calgary Journal original documentary',
    'berlin-ak.ftp.media.ccc.de': 'CCC original conference recording',
    'cba.mit.edu': 'MIT Center for Bits and Atoms original talk',
    'www.machinerytube.com': 'MachineryTube machine demonstration',
    'dlmultimedia.esa.int': 'ESA original science documentary',
    'www.jmhs.hereford.sch.uk': 'JMHS school original travel recording',
    'www.jwolf.com': 'Jazz Organ original performance recording',
    'nobel-videocdn01.azureedge.net': 'Nobel Prize original archival speech CDN',
}


def inventory():
    grouped = defaultdict(list)
    for row in read(TARGET / 'annotations__lvsum_72_dataset.json'):
        grouped[row['video_path']].append(row)
    sources, rejected = [], []
    for url, annotations in grouped.items():
        segments = [s for a in annotations for s in a['summary_timestamps']]
        invalid = [(s['start_time'], s['end_time']) for s in segments
                   if not 0 <= s['start_time'] < s['end_time']]
        record = dict(url=url, host=urlparse(url).hostname,
            ids=sorted({a['video_id'] for a in annotations}), annotators=len(annotations),
            max_ms=max(s['end_time'] for s in segments),
            source_hash=hashlib.sha256(('LVSum-nonsport-v1/' + url).encode()).hexdigest())
        if invalid:
            rejected.append(dict(**record, invalid_original_intervals=invalid,
                decision='EXCLUDE_WHOLE_SOURCE_NO_LABEL_REPAIR_OR_REVIEWER_SELECTION'))
        else:
            sources.append(record)
    sources.sort(key=lambda r:r['source_hash'])
    return dict(sources=sources, rejected=rejected, original_sources=len(grouped),
                all_valid_sources=len(sources), original_annotation=ref(TARGET / 'annotations__lvsum_72_dataset.json'))


def probe(row):
    result = dict(source=row, body_bytes=0)
    try:
        req = urllib.request.Request(row['url'], method='HEAD', headers={
            'User-Agent':'Mozilla/5.0 AIC-noncommercial-research', 'Accept-Encoding':'identity'})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=12) as response:
            route = route_for(response.fp.raw._sock.getpeername()[0])
            length = response.headers.get('Content-Length')
            result.update(status=response.status, bytes=int(length) if length else None,
                etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'),
                final_url=response.url, content_type=response.headers.get('Content-Type'), **route)
            result['media_route_admissible'] = (response.status==200 and length is not None
                and 0 < int(length) <= 150000000 and response.url.startswith('https://'))
    except Exception as error:
        result.update(error=repr(error), media_route_admissible=False)
    print('HEAD', row['host'], result.get('status'), result.get('bytes'), result.get('error',''), flush=True)
    return result


def main():
    result = inventory()
    save(TARGET / 'inventory22.json', result)
    candidates = [row for row in result['sources'] if row['host'] in PUBLISHERS and row['max_ms'] <= 1200000]
    save(TARGET / 'publisher_probe22_registration.json', dict(candidates=candidates,
        original_publishers=PUBLISHERS, no_model_or_quality_metrics=True,
        scope='HEAD only; public original publisher pointers; no mirrored cartoons or untraceable YouTube copies',
        time='Use exact original milliseconds /1000, no stretching or endpoint clipping',
        research_use='User confirmed student/noncommercial; CC BY-NC-ND annotations retained locally',
        no_original_data_redistribution=True, no_media_rights_blanket_relicense_claim=True,
        exclusion='Entire malformed source excluded, all raters retained elsewhere',
        maximum_probe_sources=len(candidates)))
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(probe,candidates))
    save(TARGET / 'publisher_probe22.json',results)
    save(TARGET / 'completion22.json',dict(state='ORIGINAL_PUBLISHER_ROUTE_PROBE_COMPLETE',
        malformed_sources=len(result['rejected']), valid_sources=len(result['sources']),
        candidates=len(candidates), viable=sum(r['media_route_admissible'] for r in results),
        media_bytes=0, model_calls=0, old_successful_downloads_not_repeated=True))


if __name__ == '__main__':
    main()
