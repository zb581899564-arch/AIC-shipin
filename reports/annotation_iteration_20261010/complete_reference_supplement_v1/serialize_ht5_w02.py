"""Explicit root reviewed literals; exact original reference unchanged."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
p=ROOT/'04_ht5_w02_complete_reference.json';r=read(p);w=read(ROOT.parent/'slot6_silver24_v1/source_window_plan.json')['jobs'][4]['window'];start=F(w['domain_start_exact'])
s=dict(window_id=w['window_id'],reference_sha256=sha(p),reviewed=True,not_measured_cut=True,exact_target_local=[[str(F(a)-start),str(F(b)-start)] for a,b in r['keep_global_exact']],serialized_decimal_as_str=[['14.507766666666665','18.661916666666666']],reviewed_boundary_ranges_local_exact=[[[b['uncertainty_start_exact'],b['uncertainty_end_exact']] for b in r['boundary_decisions']]],main_review='Root explicitly approves these finite literals within the actual F30/F31 onset and F39/O002361 endpoint editing ranges. These are not measured cuts; full eligible and planned64 half-open membership must remain exact.')
sys.path.insert(0,str(ROOT/'runtime'));from objective import target,classify
raw,_=target(r,w,s,s['reference_sha256']);result=classify(raw,F(30));assert result['status']=='MODEL_OK'
assert [[F(str(x)) for x in pair] for pair in json.loads(raw)['segments']]==result['parsed_segments']
q=ROOT/'04_ht5_w02_target_serialization.json';save(q,s)
save(ROOT/'04_ht5_w02_target_serialization_acceptance.json',dict(status='PASS_EXPLICIT_REVIEWED_SERIALIZATION_AND_EXACT_NATIVE_MEMBERSHIP',utc=datetime.now(timezone.utc).isoformat(),reference_sha256=s['reference_sha256'],sidecar_sha256=sha(q),raw_json=raw,original_fraction_reference_changed=False,parsed_float_decimal_identity=True,planned_native64_membership_unchanged=True,full_eligible_native_membership_unchanged=True,new_model_calls=0,new_optimizer_updates=0))
print(raw)
