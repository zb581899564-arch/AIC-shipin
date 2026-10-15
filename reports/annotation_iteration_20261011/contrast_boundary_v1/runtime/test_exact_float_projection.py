"""Exact native metadata tests only: no decoder, processor, model or GPU."""
import argparse
import copy
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys
from native_runtime import validate_plan, native_ranges


def rejected(call):
    try:call()
    except ValueError:return
    raise AssertionError('incorrect float projection admitted')


def synthetic_quarter():
    # Source length100/3 -> quarter end25/3 and length25/3, with native300
    # frames/s. A denominator3 cannot be represented by finite decimal text.
    a,b=F(0),F(25,3);points=[F(i,300) for i in range(2500)]
    ids=[i*(len(points)-1)//63 for i in range(64)]
    return dict(domain_start_exact=str(a),domain_end_exact=str(b),eligible_exact_pts=list(map(str,points)),
        planned_exact_pts=[str(points[i]) for i in ids],planned_actual_pts_sec=[float(points[i]) for i in ids],
        planned_source_frame_ordinals=ids,eligible_source_frame_count=len(points),source_total_frames=10000,
        window_pts_start_sec=float(a),window_pts_end_exclusive_sec=float(b),window_duration_sec=float(b-a))


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',default=str(Path(__file__).resolve().parent.parent/'source_window_plan_v1.json'))
    args=p.parse_args();path=Path(args.plan).resolve(strict=True);original=path.read_bytes()
    plan=json.loads(original.decode('utf-8-sig'));jobs=plan['jobs']
    assert len(jobs)==len({j['window']['window_id'] for j in jobs})==96
    counts={role:sum(j['role']==role for j in jobs) for role in ('train','process_dev','locked_evaluation')}
    assert counts==dict(train=64,process_dev=16,locked_evaluation=16)
    legacy_rejected=[];nondecimal=[];native_membership_checked=0
    for j in jobs:
        w=j['window'];snapshot=copy.deepcopy(w);a,b,points=validate_plan(w)
        if F(str(w['window_pts_start_sec']))!=a or F(str(w['window_pts_end_exclusive_sec']))!=b:
            legacy_rejected.append(w['window_id'])
        for value in (a,b):
            denominator=value.denominator
            for prime in (2,5):
                while denominator%prime==0:denominator//=prime
            if denominator!=1:nondecimal.append(w['window_id']);break
        # Independent ordered membership oracle over every exact eligible PTS.
        for local_start,local_end in ((F(0),b-a),((b-a)/3,2*(b-a)/3)):
            wanted=[i for i,t in enumerate(points) if a+local_start<=t<a+local_end]
            assert wanted
            assert native_ranges([[local_start,local_end]],w)==[[wanted[0],wanted[-1]+1]]
            native_membership_checked+=1
        assert w==snapshot
    assert len(legacy_rejected)==35
    sample=next(j['window'] for j in jobs if j['window']['window_id']=='91IHQYk1IQM:CONTRASTQ:0')
    assert F(sample['domain_end_exact'])==F(3314311,120000)
    assert sample['window_pts_end_exclusive_sec']==float(F(3314311,120000))
    assert F(str(sample['window_pts_end_exclusive_sec']))!=F(3314311,120000)
    w=synthetic_quarter();assert F(str(w['window_pts_end_exclusive_sec']))!=F(w['domain_end_exact'])
    validate_plan(w)
    for field in ('window_pts_start_sec','window_pts_end_exclusive_sec','window_duration_sec'):
        broken=copy.deepcopy(w);broken[field]=math.nextafter(broken[field],math.inf)
        rejected(lambda:validate_plan(broken))
    broken=copy.deepcopy(w);broken['planned_actual_pts_sec'][1]=math.nextafter(broken['planned_actual_pts_sec'][1],math.inf)
    rejected(lambda:validate_plan(broken))
    broken=copy.deepcopy(w);broken['planned_exact_pts'][1]=str(F(broken['planned_exact_pts'][1])+F(1,10**15))
    rejected(lambda:validate_plan(broken))
    assert path.read_bytes()==original
    assert not any(name in sys.modules for name in ('torch','transformers','av','numpy','peft'))
    print(json.dumps(dict(status='PASS_EXACT_FRACTION_TO_FLOAT_PROJECTION_METADATA_ONLY',
        plan=dict(path=str(path),sha256=hashlib.sha256(original).hexdigest()),metadata_windows_verified=96,
        old_decimal_roundtrip_false_rejections_reproduced=len(legacy_rejected),old_rejected_window_ids=legacy_rejected,
        non_finite_decimal_domain_windows=len(set(nondecimal)),exact_native_membership_oracle_cases=native_membership_checked,
        synthetic_non_finite_decimal_quarter_tested=True,wrong_float_nextafter_rejected=True,
        exact_domains_and_sample_pts_changed=False,model_calls=0,decoder_calls=0,processor_calls=0,
        actual_runtime_encode_decode_verified=False)))


if __name__=='__main__':main()
