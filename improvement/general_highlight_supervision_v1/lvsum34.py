"""Alternative original-publisher recordings after HF's actual direct-route failure."""
from concurrent.futures import ThreadPoolExecutor
from common import ROOT,read,ref,save
from lvsum20 import TARGET
from lvsum22 import probe

HOSTS={'media.delight.video','www.levitt.tv','scdn.rohde-schwarz.com','insidechassidus.org',
       'www.4dmm.org','cdn.innerself.com','broadband.indiaforums.com','www.biznews.com',
       'video-indiatoday.tosshub.com','www.integriti3d.com'}


def main():
    directory=ROOT/'lvsum34';directory.mkdir()
    inventory=read(TARGET/'inventory22.json')['sources']
    used={r['source']['url'] for r in read(ROOT/'media24/registration.json')['selected']}
    candidates=[r for r in inventory if r['host'] in HOSTS and r['url'] not in used and r['max_ms']<=1800000]
    old={r['source']['url']:r for r in read(TARGET/'publisher_routes23.json')}
    adopted=[old[r['url']] for r in candidates if r['url'] in old]
    fresh=[r for r in candidates if r['url'] not in old]
    save(directory/'registration.json',dict(candidates=candidates,
        adopted_successful_heads=[r['source']['url'] for r in adopted],
        source_choice='Previously unused, unmalformed, original organization/publisher recording; source SHA order',
        source_annotation=ref(TARGET/'annotations__lvsum_72_dataset.json'),
        no_old_LVSum7_or_Calgary403_retries=True,
        reason='Current HF metadata transport failed,0 media; alternatives on original publishers',
        scope='HEAD only before any new media/input/model registration',
        original_data_not_redistributed=True,no_automatic_training_or_production=True))
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(probe,fresh))
    routes=adopted+[r for r in results if r.get('status')==200]
    save(directory/'routes.json',routes);save(directory/'all_new_probes.json',results)
    viable=[r for r in routes if r.get('bytes') is not None and 0<r['bytes']<=300000000]
    save(directory/'completion.json',dict(state='ALTERNATIVE_ORIGINAL_PUBLISHER_HEADERS_COMPLETE',
        sources=len(candidates),accepted_heads=len(routes),bounded_viable_sources=len(viable),
        viable=viable,maximum_body_bytes=sum(r['bytes'] for r in viable),new_media_downloads=0,new_model_calls=0))
    print('ALTERNATIVE',len(viable),sum(r['bytes'] for r in viable),flush=True)


if __name__=='__main__':main()
