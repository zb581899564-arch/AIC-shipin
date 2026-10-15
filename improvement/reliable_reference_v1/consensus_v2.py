"""Conservative agreement on observed frames; never interpolate sparse labels."""
import sys
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/reliable_reference_20261012_v1'
KIND=sys.argv[1]
assert KIND in ('dense02','supplement01','supplement_dense01')

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def validate_review(review,materials):
    assert review['level']=='AI_REVIEWED_SILVER_NOT_HUMAN_GOLD'
    assert review['prediction_blind'] is True
    cases={c['case_id']:c for c in review['cases']}
    assert len(cases)==len(review['cases'])==len(materials)
    assert set(cases)==set(materials)
    for name,c in cases.items():
        m=materials[name];n=len(m['observations'])
        expected={Path(s['path']).name for s in m['sheets']}
        assert {Path(p).name for p in c['pages_viewed']}==expected,(name,'pages')
        assert len(c['pages_viewed'])==len(expected)
        assert c['scene_summary'].strip()
        keep=set()
        for e in c['events']:
            assert e['description'].strip() and e['evidence']
            ids=e['core_ids'];assert len(ids)==len(set(ids))
            assert all(type(i) is int and 0<=i<n for i in ids)
            keep.update(ids)
            for side in ('start','end'):
                band=e[side+'_band_ids'];censored=e['boundary_censored_'+side]
                assert type(censored) is bool
                if band is not None:
                    assert not censored and len(band)==2
                    assert all(type(i) is int for i in band) and 0<=band[0]<=band[1]<n
                if censored:assert band is None
            sb,eb=e['start_band_ids'],e['end_band_ids']
            if sb is not None and eb is not None:
                assert sb[0]<=eb[1],(name,'reversed boundary bands')
        ordinary=set()
        for a,b in c['ordinary_id_ranges']:
            assert type(a) is type(b) is int and 0<=a<=b<n
            ordinary.update(range(a,b+1))
        assert not (keep&ordinary),(name,'self-conflicting labels',sorted(keep&ordinary))
        c['_keep'],c['_ordinary']=keep,ordinary
    return cases

def main():
    materials={m['case_id']:m for m in read(REPORT/(KIND+'_materials/preparation_receipt.json'))['records']}
    ar=read(REPORT/('reviewer_a_'+KIND+'.json'));br=read(REPORT/('reviewer_b_'+KIND+'.json'))
    assert ar['reviewer']=='A' and br['reviewer']=='B'
    a=validate_review(ar,materials);b=validate_review(br,materials)
    rows=[]
    for name in sorted(materials):
        m=materials[name];ca,cb=a[name],b[name]
        keep=ca['_keep']&cb['_keep'];ordinary=ca['_ordinary']&cb['_ordinary']
        conflicts=(ca['_keep']&cb['_ordinary'])|(cb['_keep']&ca['_ordinary'])
        assert not keep&ordinary
        matches=[];used_b=set()
        for ea in ca['events']:
            options=sorted([(len(set(ea['core_ids'])&set(eb['core_ids'])),j,eb) for j,eb in enumerate(cb['events']) if j not in used_b],key=lambda x:(x[0],-x[1]),reverse=True)
            if not options or options[0][0]==0:continue
            _,j,eb=options[0];used_b.add(j)
            core=set(ea['core_ids'])&set(eb['core_ids'])
            bands={};both=True
            for side in ('start','end'):
                x,y=ea[side+'_band_ids'],eb[side+'_band_ids']
                if x is None or y is None or ea['boundary_censored_'+side] or eb['boundary_censored_'+side] or max(x[0],y[0])>min(x[1],y[1]):
                    bands[side]=None;both=False
                else:
                    lo,hi=min(x[0],y[0]),max(x[1],y[1])
                    if 'dense' in KIND and m['observations'][hi]['ordinal']-m['observations'][lo]['ordinal']!=hi-lo:
                        bands[side]=None;both=False
                    else:bands[side]=[m['observations'][lo]['exact_pts'],m['observations'][hi]['exact_pts']]
            widths={s:float(F(v[1])-F(v[0])) if v else None for s,v in bands.items()}
            matches.append(dict(description_a=ea['description'],description_b=eb['description'],core_ids=sorted(core),start_band_exact=bands['start'],end_band_exact=bands['end'],boundary_width_seconds=widths,both_boundaries_observed=both,dense_verified=bool('dense' in KIND and both)))
        labels=['KEEP' if i in keep else 'ORDINARY' if i in ordinary else 'UNKNOWN' for i in range(len(m['observations']))]
        rows.append(dict(case_id=name,source_group=m['source_group'],source_sha256=m['source_sha256'],sample_labels=labels,observations=m['observations'],counts={s:labels.count(s) for s in ('KEEP','ORDINARY','UNKNOWN')},conflict_ids=sorted(conflicts),matched_events=matches))
    coverage=dict(sources=len(rows),keep_sources=sum(bool(c['counts']['KEEP']) for c in rows),ordinary_sources=sum(bool(c['counts']['ORDINARY']) for c in rows),both_boundary_events=sum(e['both_boundaries_observed'] for c in rows for e in c['matched_events']),**{s:sum(c['counts'][s] for c in rows) for s in ('KEEP','ORDINARY','UNKNOWN')})
    coverage_pass=coverage['keep_sources']>=12 and coverage['ordinary_sources']>=8 and coverage['both_boundary_events']>=12
    result=dict(status='INITIAL_AGREEMENT_DENSE_REVIEW_REQUIRED' if coverage_pass else 'STOP_INITIAL_REFERENCE_COVERAGE_INSUFFICIENT',reference_level='AI_REVIEWED_SILVER_NOT_HUMAN_GOLD',rows=rows,coverage=coverage,initial_coverage_pass=coverage_pass,reference_quality_pass=False,dense_verification_completed=False,review_sha256={s:sha(REPORT/f'reviewer_{s}_{KIND}.json') for s in ('a','b')},historical_formal_quality_failed_preserved=True,candidate_predictions_read=False,new_model_calls=0,optimizer_updates=0)
    with (REPORT/(KIND+'_consensus.json')).open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':main()
