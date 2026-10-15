"""Serialize an explicitly adjudicated root review; never generate semantic labels."""
import argparse,json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'slot6_silver24_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--main-review',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 mp=Path(a.main_review).resolve(strict=True);out=Path(a.output).resolve();assert mp.parent==ROOT and out.parent==ROOT and not out.exists()
 m=read(mp);assert m['status']=='ROOT_FINAL_COMPLETE_FINITE_EDITORIAL_REFERENCE_ADJUDICATED'
 assert m['root_semantic_adjudication_complete'] is True and m['candidate_prediction_exposure_before_freeze'] is False
 plan=read(OLD/'source_window_plan.json');job=next(j for j in plan['jobs'] if j['window']['window_id']==m['window_id'])
 w=job['window'];start=F(w['domain_start_exact']);end=F(w['domain_end_exact']);duration=end-start
 def globalize(rows):
  result=[]
  for pair in rows:
   lo,hi=map(F,pair);assert F(0)<=lo<hi<=duration;result.append([str(start+lo),str(start+hi)])
  return result
 evidence=dict(m['evidence']);assert 'final_main_review' not in evidence
 for name,b in evidence.items():assert set(b)=={'path','sha256'} and sha(b['path'])==b['sha256']
 evidence['final_main_review']=bind(mp)
 admitted=m['training_admitted'];assert type(admitted) is bool and (not admitted or job['role']=='train')
 record=dict(window_id=w['window_id'],source_sha256=w['source_sha256'],reference_kind='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD',
   keep_global_exact=globalize(m['keep_local_exact']),no_global_exact=globalize(m['no_local_exact']),unknown_global_exact=globalize(m['unknown_local_exact']),
   evidence=evidence,main_review_assertions=m['main_review_assertions'],boundary_decisions=m['boundary_decisions'],events=m['events'],
   consequential_unknowns=m['consequential_unknowns'],explicit_no_highlight=m['explicit_no_highlight'],
   all_target_boundaries_adjudicated=m['all_target_boundaries_adjudicated'],student_observable_complete_target=m['student_observable_complete_target'],
   training_admitted=admitted,reason=m['reference_scope_and_reason'],
   supplement_provenance=dict(protocol=bind(ROOT/'PROTOCOL.md'),erratum=bind(ROOT/'PROTOCOL_ERRATUM_W11_AND_BUDGET.md'),new_optimizer_updates=0))
 sys.path.insert(0,str(OLD));from silver_contract import verify_window
 verified=verify_window(record,job)
 with out.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 receipt=out.with_name(out.stem+'_acceptance.json')
 with receipt.open('x',encoding='utf-8') as f:json.dump(dict(status='PASS_BOUND_COMPLETE_FINITE_REFERENCE_NOT_BATCH_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),reference=bind(out),verified=verified,new_optimizer_updates=0),f,ensure_ascii=False,indent=2,default=str)
 print(json.dumps(dict(reference=bind(out),verified=verified,batch_training_admitted=False),ensure_ascii=False,default=str))
if __name__=='__main__':main()
