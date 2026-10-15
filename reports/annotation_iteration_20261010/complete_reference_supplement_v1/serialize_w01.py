"""Explicit root-reviewed finite-decimal mapping; original exact reference stays intact."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
r=read(ROOT/'00_w01_complete_reference.json');b=r['boundary_decisions']
w=read(ROOT.parent/'slot6_silver24_v1/source_window_plan.json')['jobs'][0]['window']
exact=[[str(F(x)-30) for x in pair] for pair in r['keep_global_exact']]
def interval(i):return [b[i]['uncertainty_start_exact'],b[i]['uncertainty_end_exact']]
side=dict(window_id=w['window_id'],reference_sha256=sha(ROOT/'00_w01_complete_reference.json'),reviewed=True,not_measured_cut=True,
 exact_target_local=exact,serialized_decimal_as_str=[['0','2.6326'],['17.8478','24.020633333333333'],['27.3573','30']],
 reviewed_boundary_ranges_local_exact=[[['0','0'],interval(0)],[interval(1),interval(3)],[interval(4),['30','30']]],
 main_review='Explicitly review serialized end24.020633333333333 within original F50/F51 range. Difference from exact720619/30000 is declared, not a recovered or measured cut. All native membership and original reference SHA must remain exact.')
sys.path.insert(0,str(ROOT/'runtime'))
from objective import target,classify
raw,_=target(r,w,side,side['reference_sha256']);parsed=classify(raw,F(30));assert parsed['status']=='MODEL_OK'
# Validate exact float-parser identity in addition to Decimal/source selection.
plain=json.loads(raw)
assert [[F(str(x)) for x in pair] for pair in plain['segments']]==parsed['parsed_segments']
save(ROOT/'00_w01_target_serialization.json',side)
save(ROOT/'w01_target_serialization_acceptance.json',dict(status='PASS_EXPLICIT_REVIEWED_SERIALIZATION_AND_EXACT_NATIVE_MEMBERSHIP',utc=datetime.now(timezone.utc).isoformat(),
 reference_sha256=side['reference_sha256'],sidecar_sha256=sha(ROOT/'00_w01_target_serialization.json'),
 original_fraction_reference_changed=False,raw_json=raw,parsed_float_decimal_identity=True,planned_native64_membership_unchanged=True,full_eligible_native_membership_unchanged=True,
 new_model_calls=0,new_optimizer_updates=0))
print(raw)
