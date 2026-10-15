"""Freeze native-frame ranges from blind facts, never candidate predictions."""
import json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/reliable_reference_20261012_v1'
selection=json.loads((OUT/'source_selection.json').read_text())
sources={r['case_id']:r for r in selection['rows']}
reviews=[json.loads((OUT/f'reviewer_{s}.json').read_text()) for s in ('a','b')]
initial=json.loads((OUT/'initial_consensus.json').read_text())
rows=[]
for c in initial['rows']:
    if not (c['counts']['KEEP'] or c['counts']['ORDINARY']):continue
    m=c['observations']; ranges=[]
    for i,s in enumerate(c['sample_labels']):
        if s in ('KEEP','ORDINARY'):
            t=F(m[i]['exact_pts']);ranges.append([t-F(1),t+F(1)])
    for review in reviews:
        r=next(x for x in review['cases'] if x['case_id']==c['case_id'])
        for e in r['events']:
            if not e['core_ids']:continue
            for side in ('start','end'):
                b=e[side+'_band_ids']
                if b:ranges.append([F(m[b[0]]['exact_pts'])-1,F(m[b[1]]['exact_pts'])+1])
                elif e['boundary_censored_'+side]:
                    edge=F(sources[c['case_id']]['clip_'+side])
                    ranges.append([edge-2,edge+2])
    merged=[]
    for a,b in sorted(ranges):
        if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
        else:merged.append([a,b])
    r=dict(sources[c['case_id']]);r['ranges_exact']=[[str(a),str(b)] for a,b in merged]
    rows.append(r)
result=dict(status='BLIND_NATIVE_EVIDENCE_RANGES_REGISTERED',rows=rows,candidate_predictions_read=False,
            initial_reference_failed_preserved=True,selection_reason='Initial agreed points, both review boundary bands and censored core context')
with (OUT/'dense_anchor_registration.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(cases=len(rows),ranges=sum(len(r['ranges_exact']) for r in rows))))
