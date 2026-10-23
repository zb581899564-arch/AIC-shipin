"""Adopt cached author metadata; probe only new original-publisher URLs."""
from concurrent.futures import ThreadPoolExecutor
import traceback
import urllib.request

from t_io import ROOT, WORK, identity, public_route, read, save

OLD = WORK / 'general_highlight_supervision_20261021_v1'
HOSTS = {
    'www.math.stonybrook.edu': 'Original university mathematics lecture',
    'livestream.rggs.qld.edu.au': 'Original school recording',
    'video.thegamerimages.com': 'Original TheGamer publisher recording',
    'static-mt-rv-v1.gamespot.com': 'Original GameSpot publisher recording',
    'ht.cdn.turner.com': 'Original TCM publisher introduction',
}


def probe(row):
    result = dict(source=row, requested_body_bytes=0)
    request = urllib.request.Request(row['url'], method='HEAD', headers={
        'User-Agent': 'AIC-noncommercial-source-audit', 'Accept-Encoding': 'identity'})
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=15) as response:
            route = public_route(response.fp.raw._sock.getpeername()[0])
            length = response.headers.get('Content-Length')
            result.update(status=response.status, declared_bytes=int(length) if length else None,
                          final_url=response.url, headers=dict(response.headers), **route)
    except Exception:
        result['error'] = traceback.format_exc()
    print('SOURCE05_HEAD', row['host'], result.get('status'), result.get('declared_bytes'), flush=True)
    return result


def main():
    output = ROOT / 'source_alternatives05'
    output.mkdir()
    inventory = OLD / 'lvsum20/inventory22.json'
    histories = [OLD / path for path in [
        'lvsum20/publisher_probe22.json', 'lvsum20/publisher_routes23.json',
        'lvsum34/all_new_probes.json']]
    attempted = {r['source']['url'] for p in histories if p.exists() for r in read(p)}
    candidates = [r for r in read(inventory)['sources']
                  if r['host'] in HOSTS and r['url'] not in attempted]
    save(output / 'registration.json', dict(
        adopted_author_inventory=identity(inventory), prior_probes=[identity(p) for p in histories if p.exists()],
        original_publisher_scope=HOSTS, candidates=candidates, maximum_requests=len(candidates),
        scope='HEAD only; no repeated old requests or new media/training permission inferred',
        labels='Human summaries are preference/positive intervals; unselected remains UNKNOWN',
        underlying_media_rights_not_relicensed_by_annotation_license=True,
        no_Google_YouTube_or_HF_retry=True))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(probe, candidates))
    save(output / 'headers.json', results)
    save(output / 'completion.json', dict(
        state='NEW_ORIGINAL_PUBLISHER_HEADERS_COMPLETE', source_count=len(candidates),
        accepted=sum(r.get('status') == 200 for r in results), media_downloads=0,
        no_model_or_training_calls=True))


if __name__ == '__main__':
    main()
