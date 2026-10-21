"""Fixed native-cardinality content ranking; no labels, cutoff or fill rules."""
import math


def select_fixed_budget(native_count,baseline,scored_blocks,available_ordinals=None):
    """Reassign only modeled available frames; preserve original count exactly.

    Blocks are half-open native ordinal ranges and must be disjoint. Frames
    outside them (including short tails and missing observations) remain as
    selected by the original baseline. Equal scores prefer that baseline.
    """
    if not isinstance(native_count,int) or native_count<=0:
        raise ValueError('Actual positive native frame count required')
    baseline=set(baseline)
    if any(type(i) is not int or not 0<=i<native_count for i in baseline):
        raise ValueError('Baseline native ordinal is invalid')
    available=set(range(native_count)) if available_ordinals is None else set(available_ordinals)
    if any(type(i) is not int or not 0<=i<native_count for i in available):
        raise ValueError('Available native domain is invalid')
    scores={};seen=set()
    for row in scored_blocks:
        lo=row['start_ordinal'];hi=row['stop_ordinal'];score=float(row['score'])
        if type(lo) is not int or type(hi) is not int or not 0<=lo<hi<=native_count or not math.isfinite(score):
            raise ValueError('Invalid real block bounds or finite ranking score')
        domain=set(range(lo,hi))
        if seen&domain:raise ValueError('Overlapping modeled blocks would double-count frames')
        seen.update(domain)
        for i in domain&available:scores[i]=score
    # Original baseline outside the candidate domain is immutable.
    domain=set(scores);budget=len(baseline&domain)
    ordered=sorted(domain,key=lambda i:(-scores[i],i not in baseline,i))
    selected=(baseline-domain)|set(ordered[:budget])
    if len(selected)!=len(baseline) or (selected-domain)!=(baseline-domain):
        raise AssertionError('Source native-cardinality or immutable outside-domain range changed')
    return sorted(selected),dict(native_count=native_count,modeled_available_frames=len(domain),
        fixed_inside_budget=budget,baseline_count=len(baseline),selected_count=len(selected),
        added=len(selected-baseline),removed=len(baseline-selected),unknown_filled=False)
