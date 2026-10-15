import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/reliable_reference_20261012_v1'
sel=json.loads((OUT/'supplement_review_selection.json').read_text())['rows']
train=[json.loads(l) for l in (ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/data_audit/teacher_semantics_train_dev.jsonl').read_text().splitlines() if json.loads(l)['split']=='train']
groups={r['source_group'] for r in train};meta=json.loads((ROOT/'reports/boundary_refinement_20261012_v1/input_01/metadata.json').read_text())['records']
hashes={r['source_sha256'] for r in meta}
intersection=sorted(groups&{r['source_group'] for r in sel})
sha_intersection=sorted(hashes&{r['source_key'] for r in sel})
result=dict(status='PASS_KNOWN_SOURCE_SEPARATION' if not intersection and not sha_intersection else 'FAIL_SOURCE_OVERLAP',sources=len(sel),teacher_train_records=len(train),train_source_group_intersection=intersection,official_records=len(meta),official_distinct_sha=len(hashes),official_sha_intersection=sha_intersection,semantic_reencoded_separation_proven=False,previously_exposed_development=True)
with (OUT/'supplement_source_separation_audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result));assert result['status']=='PASS_KNOWN_SOURCE_SEPARATION'
