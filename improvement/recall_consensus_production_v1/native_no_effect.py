"""Pure native-output equivalence proof for the frozen two-view consensus.

No media, model, labels, files, prediction selection or production admission.
The caller must bind the actual immutable baseline, complete clock and this
code before using a witness. Omitted calls have no answer or input/output QA.
Only final native-frame additions are equivalent, not continuous-time metrics.
"""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json


def require(value, reason):
    if not value:
        raise ValueError(reason)


def exact(value):
    require(type(value) in (str, int, F), 'Exact rational seconds required')
    return F(value)


def full_grid(end):
    end=exact(end)
    require(end>0, 'Positive original measured physical endpoint required')
    if end<=15:
        return {(F(0),end)}
    views=set();start=F(0)
    while start+15<=end:
        views.add((start,start+15));start+=F(15,2)
    views.add((end-15,end))
    return views


def plan_native_effect(points, physical_end, baseline_frames, views):
    """Keep every view covering any possible new two-support native point.

    U={i not in B: at least two COMPLETE original-grid windows contain pts[i]}.
    For every u in U, all its covering views are retained. Outside U a native
    point is already in B or cannot have two actual KEEP votes in the full
    grid. Thus B union K2 is unchanged for every legal per-view KEEP subset.
    Coverage is computed once on the full grid, never after dropping views.
    """
    pts=list(map(exact,points));end=exact(physical_end)
    require(pts and 0<=pts[0] and pts[-1]<end and all(a<b for a,b in zip(pts,pts[1:])),
            'Complete strict native source clock and original physical end required')
    original=list(baseline_frames)
    require(all(type(i) is int and 0<=i<len(pts) for i in original) and len(set(original))==len(original),
            'Unique in-domain protected native ordinals required')
    baseline=set(original);geometries={};ids=set();delta=[0]*(len(pts)+1)
    for view in views:
        key=view['view_id'];lo=exact(view['start_exact']);hi=exact(view['end_exact'])
        require(isinstance(key,str) and key and key not in ids and (lo,hi) not in geometries,
                'Unique original view ID and rational geometry required; aliases cannot add votes')
        require(0<=lo<hi<=end,'Original view escaped its source')
        first,stop=bisect_left(pts,lo),bisect_left(pts,hi)
        geometries[(lo,hi)]=(key,first,stop);ids.add(key)
        delta[first]+=1;delta[stop]-=1
    require(set(geometries)==full_grid(end),'Every distinct original 15/7.5/tail window is required')
    coverage=[];active=0;possible=[]
    for ordinal in range(len(pts)):
        active+=delta[ordinal];coverage.append(active)
        if ordinal not in baseline and active>=2:possible.append(ordinal)
    require(active+delta[-1]==0,'Unclosed complete-grid native coverage')
    payload=dict(points=[str(p) for p in pts],physical_end_exact=str(end),baseline_ordinals=sorted(baseline),
                 geometries=[[str(lo),str(hi),key] for (lo,hi),(key,_,_) in sorted(geometries.items())])
    identity=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    execute=[];omitted=[]
    for (lo,hi),(key,first,stop) in sorted(geometries.items()):
        a,b=bisect_left(possible,first),bisect_left(possible,stop)
        if a<b:
            execute.append(key)
        else:
            omitted.append(dict(view_id=key,start_exact=str(lo),end_exact=str(hi),first_native_ordinal=first,
                stop_native_ordinal=stop,possible_new_two_support_native_frames=0,
                protected_or_insufficient_full_grid_support_for_every_native_frame=True,
                mathematical_witness_identity=identity,model_answer=None,actual_model_calls=0,
                input_or_output_QA_claimed=False))
    return dict(schema='CONSENSUS2_NATIVE_NO_EFFECT_PLAN_V1',
        status='MATHEMATICAL_FINAL_NATIVE_OUTPUT_EQUIVALENCE_NOT_EXECUTION_OR_QUALITY',
        identity=identity,source_native_frames=len(pts),baseline_native_frames=len(baseline),full_grid_views=len(geometries),
        fixed_support_count=2,potential_new_native_ordinals=possible,required_view_ids=execute,omitted=omitted,
        complete_full_grid_coverage=coverage,continuous_time_metric_equivalence_claimed=False,
        invariant='FOR_ALL_LEGAL_PER_VIEW_KEEP_SUBSETS__B_UNION_K2_FULL_EQUALS_B_UNION_K2_RETAINED',
        original_baseline_frames_and_boxes_preserved_by_later_frozen_merge='REQUIRED',
        model_calls=0,media_decodes=0,vision_processor_calls=0,quality_pass_claimed=False,
        production_admitted=False)
