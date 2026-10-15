"""Select sources without inspecting predictions or legacy teacher labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/reliable_reference_20261012_v1'
export = ROOT / 'reports/boundary_refinement_20261012_v1/developer_readonly_export.json'
d = json.loads(export.read_text(encoding='utf-8-sig'))
excluded = set(d['prior_teacher_source_intersection'])
by_group = {}
for entry in sorted(d['entries'], key=lambda e: e['video_id']):
    if entry['source_key'] not in excluded:
        by_group.setdefault(entry['source_group'], entry)
ranked = sorted(by_group, key=lambda g: hashlib.sha256(('RELIABLE_REFERENCE_V1:' + g).encode()).hexdigest())
assert len(ranked) >= 20
rows = []
for index, group in enumerate(ranked[:20]):
    e = by_group[group]
    rows.append(dict(case_id=f'R{index+1:02d}', role='screen' if index < 12 else 'confirm',
                     video_id=e['video_id'], source_group=group, source_key=e['source_key'],
                     clip_start=e['clip_start'], clip_end=e['clip_end'], clock_sha256=e['clock_sha256']))
result = dict(status='FROZEN_SOURCE_SELECTION_NOT_LABEL_ADMISSION', rows=rows,
              available_nonintersection_groups=len(ranked), selection_prediction_independent=True,
              globally_unseen=False, reference_level='AI_REVIEWED_SILVER_PENDING',
              prior_quality_failed_preserved=True, new_model_calls=0, optimizer_updates=0)
with (OUT / 'source_selection.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps({'sources':len(rows),'screen':12,'confirm':8,'ids':[r['case_id']+':'+r['source_group'] for r in rows]}))
