"""Read-only exact developer window inventory. Never reads model answers or media.

stdout is a compact private aggregate; this process performs no remote writes.
All source groups are opaque in output. Plan validity is not consumer acceptance.
"""
import hashlib, json, socket
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path
from datetime import datetime, timezone

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
P=RUN/'context_advisory_v1/input_01/developer_plan.json'
def sha(b): return hashlib.sha256(b).hexdigest()
def floor64(a):
    n=min(64,len(a))
    return [a[i*(len(a)-1)//(n-1)] for i in range(n)] if n>1 else a[:1]
def key(f): return str(f.numerator)+'/'+str(f.denominator)
d=json.loads(P.read_bytes()); rows=[]; bindings=[]; issues=[]
for j in d['developer_jobs']:
    if len(j['windows'])!=2: continue
    p=Path(d['source_clocks'][j['source_key']]); b=p.read_bytes(); c=json.loads(b)
    assert c['source_sha256']==j['source_key']
    clock=[F(x) for x in c['pts_rational']]
    assert len(clock)==c['n_frames'] and all(x<y for x,y in zip(clock,clock[1:]))
    start,end=F(str(j['clip_start_sec'])),F(str(j['clip_end_sec']))
    mid=(start+end)/2
    assert 30<end-start<=60
    assert start<mid<end and (mid-start)==(end-mid)
    old=[]
    for w in j['windows']:
        expected=w['window']['planned_source_frame_ordinals']
        eligible=list(range(bisect_left(clock,F(str(w['start_sec']))),bisect_left(clock,F(str(w['end_sec'])))))
        actual=floor64(eligible)
        old.append(expected)
        if actual!=expected: issues.append({'record_sha':sha(j['video_id'].encode()),'issue':'EXACT_OLD_PLAN_DIFFERS_FROM_REGISTERED_FLOAT_PLAN'})
    new=[]
    for a,z in ((start,mid),(mid,end)):
        eligible=list(range(bisect_left(clock,a),bisect_left(clock,z)))
        chosen=floor64(eligible)
        assert chosen and len(chosen)==len(set(chosen)) and chosen==sorted(chosen)
        assert all(a<=clock[o]<z for o in chosen)
        new.append(chosen)
    left_eligible=set(range(bisect_left(clock,start),bisect_left(clock,mid)))
    right_eligible=set(range(bisect_left(clock,mid),bisect_left(clock,end)))
    assert not(left_eligible & right_eligible)
    assert left_eligible | right_eligible == set(range(bisect_left(clock,start),bisect_left(clock,end)))
    if end>F(c['physical_endpoint_rational']):
        issues.append({'record_sha':sha(j['video_id'].encode()),'issue':'REGISTERED_CLIP_END_BEYOND_PHYSICAL_ENDPOINT_REQUIRES_EXISTING_EXACT_POLICY'})
    rows.append(dict(record_sha=sha(j['video_id'].encode()),group_sha=sha(j['source_group'].encode()),
        source_sha=j['source_key'],start=key(start),mid=key(mid),end=key(end),
        old_first_seconds=float(F(str(j['windows'][0]['end_sec']))-F(str(j['windows'][0]['start_sec']))),
        old_tail_seconds=float(F(str(j['windows'][1]['end_sec']))-F(str(j['windows'][1]['start_sec']))),
        new_window_seconds=float(mid-start),mid_is_physical_pts=mid in clock,
        old_observations=[len(x) for x in old],new_observations=[len(x) for x in new],
        new_requests_changed=sum(a!=b for a,b in zip(old,new)),
        old_tail_kept=len(set(old[1])&set(new[1])),old_tail_removed=len(set(old[1])-set(new[1])),
        new_right_left_context_observations=sum(clock[o]<F(str(j['windows'][1]['start_sec'])) for o in new[1]),
        old_ordinal_sha=sha(json.dumps(old,separators=(',',':')).encode()),
        proposed_ordinal_sha=sha(json.dumps(new,separators=(',',':')).encode())))
    bindings.append(dict(path=str(p),bytes=len(b),sha256=sha(b)))
result=dict(status='PASS_EXACT_DEVELOPER_METADATA_PLAN_NOT_CONSUMER_OR_QUALITY' if not issues else 'BLOCKED_EXACT_METADATA_POLICY_REVIEW',
    utc=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),plan_path=str(P),plan_sha256=sha(P.read_bytes()),
    records=len(d['developer_jobs']),source_groups=len({j['source_group'] for j in d['developer_jobs']}),
    windows=sum(len(j['windows']) for j in d['developer_jobs']),affected_records=len(rows),
    affected_groups=len({r['group_sha'] for r in rows}),new_changed_requests=sum(r['new_requests_changed'] for r in rows),
    rows=rows,clock_bindings=bindings,issues=issues,
    quality_reference='UNKNOWN_NOT_ESTABLISHED',consumer_fraction_boundary_acceptance='NOT_RUN',
    rgb_processor_tokens='NOT_RUN',old_exact_answer_handoff='NOT_RUN',
    new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0,remote_writes=0,test_predictions_read=False)
print(json.dumps(result,ensure_ascii=False))
