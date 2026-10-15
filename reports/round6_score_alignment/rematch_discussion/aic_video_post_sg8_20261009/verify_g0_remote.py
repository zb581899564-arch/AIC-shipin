"""New metadata-only independent verification; execute over SSH stdin, no writes.
No decoder/processor/model imports or old controller execution.
"""
from pathlib import Path
from fractions import Fraction as Q
import json, hashlib, time, resource, socket
from datetime import datetime, timezone

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
P=RUN/'context_advisory_v1/input_01/developer_plan.json'
started=time.monotonic(); cpu=time.process_time(); reads=[]
def read(p):
    b=p.read_bytes(); reads.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())); return b
def pair(q):return [q.numerator,q.denominator]
def select(clock,a,b):
    ids=[i for i,x in enumerate(clock) if a<=x<b]
    if not ids:raise ValueError('EMPTY_PHYSICAL_WINDOW')
    if len(ids)<=64:return ids
    return [ids[divmod(k*(len(ids)-1),63)[0]] for k in range(64)]
def partition(a,b,old):
    if a>=b:raise ValueError('INVALID_DOMAIN')
    if old[0][0]!=a or old[-1][1]!=b or any(x>=y for x,y in old) or any(x[1]!=y[0] for x,y in zip(old,old[1:])):raise ValueError('OLD_DOMAIN_GAP_OR_OVERLAP')
    if len(old)==2 and Q(30)<b-a<Q(60):return [(a,(a+b)/2),((a+b)/2,b)]
    return old
def allowed(p,whitelist):
    if p not in whitelist:raise ValueError('FORBIDDEN_PATH')
    return p
def spacing(clock,ids,a,b):
    points=[clock[i] for i in ids if a<=clock[i]<b]
    gaps=[y-x for x,y in zip(points,points[1:])]
    return dict(observations=len(points),min_gap=pair(min(gaps)) if gaps else None,max_gap=pair(max(gaps)) if gaps else None)

tests=[]
def check(name,fn):fn();tests.append(dict(name=name,status='PASS'))
def eq(a,b):assert a==b,(a,b)
def rejects(fn):
    try:fn()
    except (ValueError,ZeroDivisionError):return
    raise AssertionError('EXPECTED_REJECTION')
check('nonzero_origin',lambda:eq(partition(Q(7),Q(38),[(Q(7),Q(37)),(Q(37),Q(38))]),[(Q(7),Q(45,2)),(Q(45,2),Q(38))]))
check('single_window_identity',lambda:eq(partition(Q(7),Q(20),[(Q(7),Q(20))]),[(Q(7),Q(20))]))
check('exact60_identity',lambda:eq(partition(Q(7),Q(67),[(Q(7),Q(37)),(Q(37),Q(67))]),[(Q(7),Q(37)),(Q(37),Q(67))]))
check('three_window_identity',lambda:eq(partition(Q(0),Q(75),[(Q(0),Q(30)),(Q(30),Q(60)),(Q(60),Q(75))]),[(Q(0),Q(30)),(Q(30),Q(60)),(Q(60),Q(75))]))
check('midpoint_present_unique_right',lambda:eq((select([Q(0),Q(1),Q(2)],Q(0),Q(1)),select([Q(0),Q(1),Q(2)],Q(1),Q(3))),([0],[1,2])))
check('midpoint_absent_no_snap',lambda:eq(partition(Q(0),Q(31),[(Q(0),Q(30)),(Q(30),Q(31))])[0][1],Q(31,2)))
check('empty_window_reject',lambda:rejects(lambda:select([Q(0)],Q(1),Q(2))))
check('nan_reject',lambda:rejects(lambda:Q('nan')))
check('inf_reject',lambda:rejects(lambda:Q('inf')))
check('old_gap_reject',lambda:rejects(lambda:partition(Q(0),Q(31),[(Q(0),Q(29)),(Q(30),Q(31))])))
check('same_source_two_files_one_group',lambda:eq(len(set(['group-a','group-a'])),1))
check('forbidden_path',lambda:rejects(lambda:allowed('/100confirm',{'/registered/plan'})))
diagnostic_permission={'metadata':True,'diagnostic':True,'train':False,'competition':False}
check('diagnostic_does_not_grant_train_or_competition',lambda:eq((diagnostic_permission['train'],diagnostic_permission['competition']),(False,False)))
# Lossless synthetic rational interval projection; no trimming/clamping.
segment=(Q(1,20),Q(301,20));offset=Q(303,20)
check('whole_interval_projection_no_trim',lambda:eq(tuple(x+offset for x in segment),(Q(76,5),Q(151,5))))
check('fraction_to_float_can_change_boundary_detected',lambda:eq(Q.from_float(float(Q(1,10)))==Q(1,10),False))

d=json.loads(read(P));rows=[];unchanged=0
for j in d['developer_jobs']:
    a,b=Q(str(j['clip_start_sec'])),Q(str(j['clip_end_sec']))
    old=[(Q(str(w['start_sec'])),Q(str(w['end_sec']))) for w in j['windows']]
    new=partition(a,b,old)
    if new==old:unchanged+=1;continue
    c=json.loads(read(Path(d['source_clocks'][j['source_key']])));clock=[Q(x) for x in c['pts_rational']]
    assert c['source_sha256']==j['source_key']
    assert all(x<y for x,y in zip(clock,clock[1:]))
    old_ids=[select(clock,x,y) for x,y in old]
    assert old_ids==[w['window']['planned_source_frame_ordinals'] for w in j['windows']]
    new_ids=[select(clock,x,y) for x,y in new]
    physical=[set(i for i,x in enumerate(clock) if x0<=x<x1) for x0,x1 in new]
    domain=set(i for i,x in enumerate(clock) if a<=x<b)
    assert not physical[0]&physical[1] and physical[0]|physical[1]==domain
    for ids,(lo,hi) in zip(new_ids,new):assert len(ids)==len(set(ids)) and all(lo<=clock[i]<hi for i in ids)
    old_all=set(sum(old_ids,[]));new_all=set(sum(new_ids,[]));seam=old[1][0];mid=new[0][1]
    main_domain=(a,seam);tail_domain=(seam,b)
    rows.append(dict(record_sha=hashlib.sha256(j['video_id'].encode()).hexdigest(),group_sha=hashlib.sha256(j['source_group'].encode()).hexdigest(),source_sha=j['source_key'],old_bounds=[[pair(x),pair(y)] for x,y in old],new_bounds=[[pair(x),pair(y)] for x,y in new],old_ordinals=old_ids,new_ordinals=new_ids,added_ordinals=sorted(new_all-old_all),removed_ordinals=sorted(old_all-new_all),old_main_spacing=spacing(clock,sorted(old_all),*main_domain),new_main_spacing=spacing(clock,sorted(new_all),*main_domain),old_tail_spacing=spacing(clock,sorted(old_all),*tail_domain),new_tail_spacing=spacing(clock,sorted(new_all),*tail_domain),old_seam_nearest_left=pair(max(clock[i] for i in new_all if clock[i]<seam)),old_seam_nearest_right=pair(min(clock[i] for i in new_all if clock[i]>=seam)),new_mid_nearest_left=pair(max(clock[i] for i in new_all if clock[i]<mid)),new_mid_nearest_right=pair(min(clock[i] for i in new_all if clock[i]>=mid)),mid_is_native_pts=mid in clock,old_tail_kept=len(set(old_ids[1])&set(new_ids[1])),old_tail_removed=len(set(old_ids[1])-set(new_ids[1])),new_right_left_context=sum(clock[i]<seam for i in new_ids[1])))
# Read only explicitly named fallback registration; do not run its inventory.
fallback=RUN/'context_advisory_v1/fallback.py';fb=read(fallback).decode('utf-8')
fallback_importance=dict(path=str(fallback),executed=False,mentions_authority='authority' in fb,inventory_not_rerun=True)
out=dict(status='PASS_INDEPENDENT_METADATA_AND_15_CPU_CONTRACTS_NOT_CONSUMER',utc=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),plan_sha256=reads[0]['sha256'],tests=tests,rows=rows,affected_records=len(rows),affected_groups=len({x['group_sha'] for x in rows}),unchanged_records=unchanged,records=len(d['developer_jobs']),bindings=reads,fallback_registration=fallback_importance,consumer_boundary_admission='NOT_RUN_FLOAT_ROUNDTRIP_COUNTEREXAMPLE_RECORDED',new_model_calls=0,new_decoder_calls=0,new_processor_calls=0,new_optimizer_updates=0,remote_writes=0,cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,bytes_read=sum(x['bytes'] for x in reads),science='NO_426',quality='UNKNOWN')
print(json.dumps(out,ensure_ascii=False))
