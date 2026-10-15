from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=ROOT/'denominator24_v2.json';rows=read(prior)['records'];p=ROOT/'04_ht5_w02_complete_reference.json';r=read(p)
rows[r['window_id']].update(state='QUALIFIED_SUPPLEMENT',training_admitted=True,reference=dict(path=str(p),sha256=sha(p)))
assert len(rows)==24 and sum(v['training_admitted'] for v in rows.values())==5
v=dict(status='PARTIAL_REFERENCE_SUPPLEMENT_NOT_BATCH_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),previous_registry=dict(path=str(prior),sha256=sha(prior)),fixed_denominator=24,qualified_references=5,pending_references=19,new_optimizer_updates=0,records=rows)
with (ROOT/'denominator24_v3.json').open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(v['status'],v['qualified_references'],v['pending_references'])
