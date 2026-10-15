"""Append new four-reference snapshot, retaining all fixed 24 rows and v1."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=read(ROOT/'denominator24_v1.json')
for stem in ['00_w01','01_w02','02_w10','03_w11']:
    p=ROOT/(stem+'_complete_reference.json');r=read(p);row=rows[r['window_id']]
    row.update(state='QUALIFIED_SUPPLEMENT',training_admitted=r['training_admitted'],reference=dict(path=str(p),sha256=sha(p)))
assert len(rows)==24 and sum(x['training_admitted'] for x in rows.values())==4
out=dict(status='PARTIAL_REFERENCE_SUPPLEMENT_NOT_BATCH_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),previous_registry=dict(path=str(ROOT/'denominator24_v1.json'),sha256=sha(ROOT/'denominator24_v1.json')),fixed_denominator=24,qualified_references=4,pending_references=20,new_optimizer_updates=0,records=rows)
with (ROOT/'denominator24_v2.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(out['status'],out['qualified_references'],out['pending_references'])
