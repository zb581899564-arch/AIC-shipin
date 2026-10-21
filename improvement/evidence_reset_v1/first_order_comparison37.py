"""First CPU-only frozen-gradient prediction vs36 actual margin comparison."""
import hashlib,json,math,time
from pathlib import Path

def ref(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def prediction(dot,norm2,alpha,rounding_norm):
 # Descriptive estimate, not an outward-rounded certified interval: the saved
 # rounding norm and these scalar endpoint operations use ordinary FP64.
 err=math.sqrt(norm2['upper'])*rounding_norm
 return dict(value=alpha*dot['value'],estimated_lower=alpha*dot['lower']-err,estimated_upper=alpha*dot['upper']+err,
             estimated_FP32_rounding_projection_error=err,scope='Descriptive FP64 estimate, not certified outward-rounded bounds. Frozen first-order prediction; nonlinear Taylor remainder is unbounded and reported empirically.')

def main():
 n=Path(__file__).resolve().parent;w=n.parent.parent;started=time.monotonic()
 reg=json.loads((n/'registration37.json').read_text());assert reg['code_ref']==ref(__file__)
 def read(rr):
  p=Path(rr['path']).resolve(strict=True);assert p.is_relative_to(w)and ref(p)==rr
  return json.loads(p.read_text())
 q=read(reg['completion36_ref']);review=read(q['review_ref']);old=read(reg['completion35_ref'])
 assert q['unique_ledger']=='PASS'and q['actual_updates']==1
 recipe=read(q['recipe_ref']);step=q['step'];alpha=float.fromhex(recipe['alpha_hex'])
 assert step==review['step']and step['alpha_hex']==recipe['alpha_hex']
 rounding=step['FP32_rounding_residual_norm'];fit=old['fit'];process={r['sid']:r['stats']for r in old['process']}
 rows=[]
 for row in review['rows']:
  if row['role']!='process' or row['forced_B']:continue
  arms={}
  for arm in ['real','shifted']:
   pred=prediction(process[row['sid']][arm+'_dot'],process[row['sid']][arm+'_norm2'],alpha,rounding)
   actual=row['arms'][arm]['actual_fixed_pair_margin_gain']
   arms[arm]=dict(prediction=pred,actual_fixed_pair_margin_gain=actual,actual_minus_linear_prediction=actual-pred['value'])
  rows.append(dict(sid=row['sid'],arms=arms))
 assert {r['sid']for r in rows}=={'S02','S06','S08'}
 fit_pred=prediction(fit['aggregate64_dot_stored'],fit['aggregate64_norm2'],alpha,rounding)
 fit_actual=math.fsum(r['arms']['real']['actual_fixed_pair_margin_gain']for r in review['rows']if r['role']=='fit')/4
 assert math.isclose(fit_pred['value'],recipe['fit_active_loss'],rel_tol=1e-12,abs_tol=1e-12)
 process_macro={arm:dict(predicted=math.fsum(r['arms'][arm]['prediction']['value']for r in rows)/4,
     estimated_lower=math.fsum(r['arms'][arm]['prediction']['estimated_lower']for r in rows)/4,
     estimated_upper=math.fsum(r['arms'][arm]['prediction']['estimated_upper']for r in rows)/4,
     actual=math.fsum(r['arms'][arm]['actual_fixed_pair_margin_gain']for r in rows)/4)for arm in ['real','shifted']}
 out=dict(status='COMPLETE_FIRST_CPU_LINEAR_PREDICTION_ACTUAL_MARGIN_COMPARISON37',completion36_ref=reg['completion36_ref'],completion35_ref=reg['completion35_ref'],
     fit=dict(prediction=fit_pred,actual_mean_margin_gain=fit_actual,actual_minus_linear=fit_actual-fit_pred['value']),process_macro=process_macro,process_rows=rows,
     forced_B_S23='Zero margin change, retained in fixedfour source denominator.',scope='No new gradients/scores/updates or scientificgate modification; margin gain is not MAP/summaryF1/official jointscore.',
     CPU_seconds=time.monotonic()-started,new_forwards=0,new_backwards=0,new_updates=0,new_ZIP=0,official_submissions=0)
 with(n/'completion37.json').open('x')as f:json.dump(out,f,indent=2,allow_nan=False)
 print(json.dumps(dict(completion_ref=ref(n/'completion37.json'),receipt={k:v for k,v in out.items()if k!='process_rows'})))

if __name__=='__main__':main()
