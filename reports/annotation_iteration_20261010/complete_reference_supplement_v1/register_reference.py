"""Append a new immutable denominator registry without overwriting prior decisions."""
import argparse,json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'slot6_silver24_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--prior',required=True);ap.add_argument('--reference',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 prior=Path(a.prior).resolve(strict=True);rp=Path(a.reference).resolve(strict=True);out=Path(a.output).resolve()
 assert prior.parent==ROOT and rp.parent==ROOT and out.parent==ROOT and not out.exists()
 rows=read(prior)['records'];r=read(rp);plan=read(OLD/'source_window_plan.json');jobs={j['window']['window_id']:j for j in plan['jobs']}
 assert len(rows)==24 and set(rows)==set(jobs)
 sys.path.insert(0,str(OLD));from silver_contract import verify_window
 for key,row in rows.items():
  if row.get('reference'):
   assert sha(row['reference']['path'])==row['reference']['sha256'];verify_window(read(row['reference']['path']),jobs[key])
 key=r['window_id'];row=rows[key]
 assert row.get('reference') is None and row.get('status',row.get('state','')).startswith('PENDING'), 'Prior rejection/acceptance cannot be silently replaced'
 verify_window(r,jobs[key])
 row.update(state='QUALIFIED_SUPPLEMENT',status='QUALIFIED_COMPLETE_TRAIN_REFERENCE' if r['training_admitted'] else 'QUALIFIED_FINITE_EVALUATION_REFERENCE',training_admitted=r['training_admitted'],reference=bind(rp))
 qualified=sum(bool(v.get('reference')) for v in rows.values())
 rejected=sum(not v.get('reference') and v.get('status',v.get('state','')).startswith('REJECTED') for v in rows.values())
 result=dict(status='REFERENCE_DENOMINATOR_SNAPSHOT_NOT_BATCH_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),previous_registry=bind(prior),added_reference=bind(rp),
  fixed_denominator=24,qualified_references=qualified,rejected_references=rejected,pending_references=24-qualified-rejected,
  accepted_train_windows=sum(v['training_admitted'] for v in rows.values()),new_optimizer_updates=0,records=rows)
 with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()
