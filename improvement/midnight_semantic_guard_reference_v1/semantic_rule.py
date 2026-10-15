"""Single fixed ordinal-semantic guard; no reference, model, or network access."""
from bisect import bisect_left
from fractions import Fraction as F
from reference_common import frames, require

POLICY = 'SEMANTIC_GUARD'
FIELDS = ('ordinary', 'redundant', 'action', 'reaction', 'information')
RULE = dict(candidate='ACTUAL_PARSED_REDUNDANT_SINGLE_WEAKEST_ONLY_IF_N_GE2',
    positive_fields=['action','reaction','information'], positive_field_empty='NO_CUE',
    proposal_mapping='HALF_OPEN_NATIVE_ORDINAL_RANGE_SOURCE_ORDINAL_A_TO_SOURCE_ORDINAL_B_WITH_B64_WINDOW_NATIVE_END',
    overlap='AT_LEAST_ONE_NATIVE_ORDINAL_WITH_WEAK_SELECTED_INTERVAL_EXACT',
    guarded_action='KEEP_WHOLE_ORIGINAL_WEAK_CANDIDATE', unguarded_action='DELETE_WHOLE_ORIGINAL_WEAK_CANDIDATE',
    endpoints='UNCHANGED_ORIGINAL_SELECTED_INTERVAL_EXACT',duplicate_event_ids='ENGINEERING_FAILURE', new_frames=False, threshold_scan=False)

def validate_full(parsed, count):
    require(isinstance(parsed,dict) and list(parsed) == list(FIELDS), 'Exact original five-field order required')
    for key in FIELDS[:2]:
        value = parsed[key]
        require(isinstance(value,list) and all(type(i) is int and 0 <= i < count for i in value)
            and value == sorted(set(value)), 'Actual candidate decision indices invalid')
    require(len(parsed['ordinary']) == max(0,count-1) and len(parsed['redundant']) == (1 if count>1 else 0)
        and set(parsed['redundant']) <= set(parsed['ordinary']), 'Original relative rank grammar must remain valid')
    for key in FIELDS[2:]:
        value = parsed[key]
        require(value == [] or isinstance(value,list) and len(value)==2 and all(type(i) is int for i in value)
            and 0 <= value[0] < value[1] <= 64, 'Actual positive native64 proposal invalid: '+key)
    return parsed

def decide(entry, parsed, points):
    """Compare only actual native frame sets; preserve a guarded event in full."""
    count = len(entry['candidate_events']);validate_full(parsed,count)
    ordinals = entry['source_ordinals'];pts = entry['exact_pts'];window = list(map(F,entry['window_exact']))
    require(len(ordinals)==len(pts)==64 and ordinals==sorted(set(ordinals))
        and all(type(i) is int and 0 <= i < len(points) for i in ordinals)
        and [str(points[i]) for i in ordinals]==pts and window[0] < window[1], 'Complete original native64 binding required')
    end = entry['window_native_end_ordinal']
    require(type(end) is int and end==bisect_left(points,window[1]) and ordinals[-1]<end<=len(points)
        and F(entry['window_native_end_exact'])==window[1]
        and all(window[0] <= points[i] < window[1] for i in ordinals), 'Exact original window end/native ordinal binding required')
    positive, cues = set(), []
    for field in FIELDS[2:]:
        value = parsed[field]
        if not value:
            continue
        a,b = value;lo=ordinals[a];hi=ordinals[b] if b<64 else end
        a_exact=pts[a];b_exact=pts[b] if b<64 else entry['window_native_end_exact']
        mapped=set(range(lo,hi))
        require(mapped==frames([[a_exact,b_exact]],points) and lo<hi, 'Native64 ordinal/exact-time mapping must agree')
        positive.update(mapped)
        cues.append(dict(field=field,sample_interval=value,native_ordinal_interval=[lo,hi],exact_interval=[a_exact,b_exact],native_frames=len(mapped)))
    worst = parsed['redundant']
    weak_frames=set();event_id=None
    if worst:
        event=entry['candidate_events'][worst[0]];event_id=event['event_id']
        lo,hi=map(F,event['selected_interval_exact'])
        require(window[0]<=lo<hi<=window[1], 'Original selected candidate contribution escaped its window')
        weak_frames=frames([event['selected_interval_exact']],points)
    intersection=positive & weak_frames;guarded=bool(worst and intersection)
    return dict(delete_indices=[] if guarded else worst,unprotected_worst_indices=worst,
        guarded=guarded,weak_event_id=event_id,weak_selected_native_frames=len(weak_frames),
        positive_cues=cues,positive_union_native_frames=len(positive),positive_weak_intersection_native_frames=len(intersection))
