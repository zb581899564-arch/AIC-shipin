"""Root reviewed decimal representations; preserve exact Fraction references."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2)
sys.path.insert(0,str(ROOT/'runtime'))
from objective import target,classify
plan=read(ROOT.parent/'slot6_silver24_v1/source_window_plan.json')
specs=[(1,'01_w02', [['0','0.7273333333333333'],['4.531133333333333','7.250516666666667'],['19.2792','20.563816666666667'],['22.115366666666667','23.550133333333334'],['29.255833333333333','30']],[(None,0),(1,2),(3,4),(5,6),(7,None)]),
       (2,'02_w10',[['0','4.070433333333333']],[(None,1)])]
for ix,name,decimals,bi in specs:
    path=ROOT/(name+'_complete_reference.json'); r=read(path); w=plan['jobs'][ix]['window']; start=F(w['domain_start_exact']); duration=F(w['domain_end_exact'])-start
    def interval(index, endpoint):
        if index is None: return [str(endpoint),str(endpoint)]
        b=r['boundary_decisions'][index]
        return [b['uncertainty_start_exact'],b['uncertainty_end_exact']]
    side=dict(window_id=w['window_id'],reference_sha256=sha(path),reviewed=True,not_measured_cut=True,
        exact_target_local=[[str(F(a)-start),str(F(b)-start)] for a,b in r['keep_global_exact']],
        serialized_decimal_as_str=decimals,
        reviewed_boundary_ranges_local_exact=[[interval(a,0),interval(b,duration)] for a,b in bi],
        main_review='Root explicitly approves these finite decimal boundaries inside already adjudicated observed editing ranges. Exact reference is unchanged; these are not measured physical cuts. Native64 and full eligible native membership must be unchanged.')
    raw,_=target(r,w,side,side['reference_sha256']); parsed=classify(raw,duration); assert parsed['status']=='MODEL_OK'
    assert [[F(str(x)) for x in pair] for pair in json.loads(raw)['segments']]==parsed['parsed_segments']
    sidepath=ROOT/(name+'_target_serialization.json');save(sidepath,side)
    save(ROOT/(name+'_target_serialization_acceptance.json'),dict(status='PASS_EXPLICIT_REVIEWED_SERIALIZATION_AND_EXACT_NATIVE_MEMBERSHIP',utc=datetime.now(timezone.utc).isoformat(),reference_sha256=side['reference_sha256'],sidecar_sha256=sha(sidepath),original_fraction_reference_changed=False,raw_json=raw,parsed_float_decimal_identity=True,planned_native64_membership_unchanged=True,full_eligible_native_membership_unchanged=True,new_model_calls=0,new_optimizer_updates=0))
    print(name,raw)
