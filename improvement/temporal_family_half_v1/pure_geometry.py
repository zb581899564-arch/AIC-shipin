"""New fixed-alpha geometry cases only; no source, proof, ZIP or model input."""


def run(half, full_candidate):
    def event(old=('10', '20'), window=('0', '40'), physical='40'):
        return dict(event_id='E', source_id='S', original_interval_exact=list(old),
                    original_window_exact=list(window), physical_end_exact=physical)

    def endpoint(side, original, new=None, pivot=None, native_moved=True):
        if new is None:
            return dict(event_id='E', side=side, original_endpoint_exact=original,
                        endpoint_exact=original, applied_decision='KEEP')
        return dict(event_id='E', side=side, original_endpoint_exact=original,
                    endpoint_exact=new, applied_decision='REFINE',
                    native_cut_actually_moved=native_moved,
                    original_native_cut_endpoint_exact=pivot if pivot is not None else original,
                    native_endpoint_exact=new if native_moved else (pivot if pivot is not None else original))

    verify={'E': {'event_id': 'E', 'decision': 'DROP'}}
    def apply(ev, start, end, arm):
        return half.candidate(ev, {'E.start':start, 'E.end':end}, verify, arm, full_candidate)

    base=event()
    out=apply(base,endpoint('start','10','18','12'),endpoint('end','20'),'HALF_START')
    assert out['refined_interval_exact']==['14','20'] and out['event_removed'] is False
    assert out['selected_interval_exact']==['53/4','83/4'] and out['original_length_padding_eligible'] is True
    conflict=apply(base,endpoint('start','10','21'),endpoint('end','20','19'),'HALF_BOTH')
    assert conflict['pair_conflict_preserved_original'] is True and conflict['refined_interval_exact']==['10','20']
    assert apply(base,endpoint('start','10','21'),endpoint('end','20','19'),'HALF_START')['refined_interval_exact']==['10','20']
    assert apply(base,endpoint('start','10','21'),endpoint('end','20','19'),'HALF_END')['refined_interval_exact']==['10','39/2']
    old_hi='7500000000000001/250000000000000'
    ev=event(('10',old_hi),('0',old_hi),'30')
    outside=apply(ev,endpoint('start','10','12'),endpoint('end',old_hi,'30'),'HALF_BOTH')
    assert outside['halfpoint_outside_physical_domain_preserved_whole_original_event'] is True
    assert outside['refined_interval_exact']==['10',old_hi]
    assert apply(ev,endpoint('start','10'),endpoint('end',old_hi),'HALF_BOTH')['refined_interval_exact']==['10',old_hi]
    zero=apply(base,endpoint('start','10','10','12',False),endpoint('end','20'),'HALF_START')
    assert zero['refined_interval_exact']==['10','20'] and not zero['half_applied_sides']['start']
    bad=endpoint('start','10');bad['applied_decision']='MODEL_FAILURE'
    try:
        apply(base,bad,endpoint('end','20'),'HALF_BOTH')
    except ValueError:
        pass
    else:
        raise AssertionError('A bad accepted output must fail, never become half UNKNOWN')
    return dict(status='PASS_NEW_HALF_EXACT_RECIPE_GEOMETRY_ONLY_NOT_QUALITY',
                checks=['recipe_delta_not_native_pivot_delta','original_length_fixed_padding',
                        'corresponding_full_conflict_precedes_half','single_arm_conflict_not_wrongly_inherited',
                        'out_of_physical_half_rolls_back_whole_event','old_KEEP_hi_may_exceed_new_physical',
                        'zero_native_preserves_recipe','invalid_result_fails','VERIFY_DROP_not_applied'],
                synthetic_only=True, actual_source_reads=0, actual_model_calls=0, actual_package_calls=0)
