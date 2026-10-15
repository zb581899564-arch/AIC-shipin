"""Unobserved external source catalogue, independent of prediction contents."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/reliable_reference_20261012_v1'
d=json.loads((ROOT/'reports/boundary_refinement_20261012_v1/developer_readonly_export.json').read_text(encoding='utf-8-sig'))
old=json.loads((OUT/'source_selection.json').read_text())
used={r['source_group'] for r in old['rows']}
excluded=set(d['prior_teacher_source_intersection'])
by_group={}
for e in sorted(d['entries'],key=lambda e:e['video_id']):
    if e['source_key'] not in excluded and e['source_group'] not in used:
        by_group.setdefault(e['source_group'],e)
ranked=sorted(by_group,key=lambda g:hashlib.sha256(('RELIABLE_REFERENCE_V1:'+g).encode()).hexdigest())
rows=[]
for i,g in enumerate(ranked):
    e=by_group[g]
    rows.append(dict(case_id=f'S{i+1:02d}',video_id=e['video_id'],source_group=g,source_key=e['source_key'],clip_start=e['clip_start'],clip_end=e['clip_end'],clock_sha256=e['clock_sha256']))
result=dict(status='SOURCE_CATALOG_ONLY_NOT_REFERENCE_LABELS',rows=rows,sources=len(rows),prediction_blind=True,previously_exposed_development=True,new_model_calls=0)
with (OUT/'supplement_catalog_selection.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(sources=len(rows))))
