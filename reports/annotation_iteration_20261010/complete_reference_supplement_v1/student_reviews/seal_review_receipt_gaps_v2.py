import json,sys,hashlib
from pathlib import Path
from fractions import Fraction
from seal_review import seal,ROOT
job_index=int(sys.argv[1]);pp=Path(sys.argv[2]);p=json.loads(pp.read_text('utf-8-sig'))
jobs=json.loads((ROOT/'slot6_silver24_v1/observations/jobs.json').read_text('utf-8-sig'))['jobs']
rp=Path(jobs[job_index])/'student_views/receipt.json';r=json.loads(rp.read_text('utf-8-sig'))
requests=p['judgment'].pop('boundary_requests',[])
assert not p['judgment'].get('boundary_gaps')
gaps=[]
for req in requests:
 a,b=req['slots']; fa=r['frames'][a];fb=r['frames'][b]
 assert fa['frame_id']==f'F{a:02d}' and fb['frame_id']==f'F{b:02d}' and b>a
 t0=Fraction(fa['global_seconds_exact']);t1=Fraction(fb['global_seconds_exact']);g=t1-t0
 gaps.append(dict(req,frame_ids=[fa['frame_id'],fb['frame_id']],global_seconds_exact=[str(t0),str(t1)],gap_seconds_exact=str(g),gap_seconds_float=float(g),gap_at_most_half_second=g<=Fraction(1,2),qualification='TIME_THRESHOLD_MET_BUT_SEMANTIC_LIMITS_APPLY' if g<=Fraction(1,2) else 'UNKNOWN_GAP_EXCEEDS_HALF_SECOND'))
for gap in gaps:
 a,b=gap['slots'];assert Fraction(gap['gap_seconds_exact'])==Fraction(r['frames'][b]['global_seconds_exact'])-Fraction(r['frames'][a]['global_seconds_exact'])
p['judgment']['boundary_gaps']=gaps
p['judgment']['boundary_machine_verification']={'all_endpoint_times_from_receipt':True,'all_gaps_computed_with_Fraction':True,'all_gap_fields_rechecked_before_seal':True,'receipt_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'semantic_verification_not_implied':True}
# Preserve the original observation payload; computed-only sibling is independently reviewable.
cp=pp.with_name(pp.stem+'.computed_boundaries.json');assert not cp.exists()
cp.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf-8')
seal(job_index,p)
print(json.dumps({'generated_gap_evidence':gaps},ensure_ascii=False))

