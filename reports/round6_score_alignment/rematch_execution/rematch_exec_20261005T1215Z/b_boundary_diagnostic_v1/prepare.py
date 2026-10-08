"""Prepare exact 16 event/shift plans and independently assigned weak references."""
import bdiag_common as c


def main():
    cad, ex, student, old, teacher, boundary = c.helpers()
    ex.verify()
    stop = c.read(c.CAD / 'scientific_stop.json')
    hand = c.read(c.CAD / 'fallback_b_diagnostic_handoff.json')
    require = c.require
    require(stop['C']['status'] == 'STOP_C_PRODUCTION_INVESTMENT', 'C did not stop under its frozen rule')
    require(hand['denominator'] == hand['requested_events'] == 16 and hand['new_32B_calls'] == 0, 'exact fallback16')
    source_plan = c.read(c.CAD / 'input_01/developer_plan.json')
    sources = ex.source_tables(source_plan)
    jobs = {j['video_id']: j for j in source_plan['developer_jobs']}
    events = []
    for seed in hand['events']:
        require(c.sha(seed['original_B0_done']) == seed['original_B0_done_sha256'], 'original B seed bytes')
        done = c.read(seed['original_B0_done'])
        for p, digest in done['bound_files'].items():
            require(c.sha(p) == digest, 'original B bound byte changed')
        require(done['arm'] == 'B0' and done['output_valid'], 'seed was not original successful B0')
        source = sources[seed['source_key']]
        require(source['source_path'] == seed['source_path'] and c.sha(source['source_path']) == seed['source_key'], 'non-test source identity')
        candidate = seed['raw_source_event_seconds']
        variants = [{'name': 'original', 'window': seed['original_window']}]
        for i, (a,b) in enumerate(seed['shifted_context_source_seconds']):
            require(0 <= a < b <= source['raw_end_exclusive_sec'] and a <= candidate[0] < candidate[1] <= b, 'unmodified shifted window/candidate domain')
            w = student.window_from_pts(source['source_path'], seed['source_key'], source['pts'], a,b,
                seed['event_key']+':SHIFT:'+str(i), width=source['width'], height=source['height'])
            variants.append({'name': 'shift'+str(i), 'window': w})
        # Assign before any new teacher answer. Exactly one overlapping
        # external positive interval is an independent weak direction reference.
        # Missing/ambiguous overlap never becomes a negative or invented target.
        job = jobs[seed['video_id']]
        refs = [[job['clip_start_sec']+a, job['clip_start_sec']+b] for a,b in job['weak_reference']]
        matches = [r for r in refs if c.overlap(r,candidate) > 0]
        ref = matches[0] if len(matches) == 1 else None
        events.append({**seed, 'variants': variants, 'weak_direction_reference': ref,
            'weak_reference_status': 'ONE_PREREGISTERED_EXTERNAL_OVERLAP' if ref else 'UNKNOWN_MISSING_OR_AMBIGUOUS',
            'weak_reference_coverage': 'UNKNOWN', 'reference_is_not_human_truth': True})
    require(len({e['source_group'] for e in events}) == 16, 'fallback source groups changed')
    admission = c.read(c.RUN / 'teacher_student_autopilot_v13/teacher_admission.json')
    # Existing pinned model/runtime recipe is reused; runtime PID/log fields
    # are supplied by the new owned session, never borrowed as live evidence.
    for key in ('server_pid','server_log','server_url','server_port'):
        admission.pop(key, None)
    c.save(c.HERE / 'input_01/plan.json', {'events': events, 'event_denominator':16,
        'variant_denominator':sum(len(e['variants']) for e in events),
        'original_handoff_sha256':c.sha(c.CAD/'fallback_b_diagnostic_handoff.json'),
        'selection_has_no_new_label_or_direction_filter':True,'new_model_calls':0})
    c.save(c.HERE / 'input_01/teacher_recipe.json', admission)
    c.save(c.HERE / 'prepared.json', {'status':'PASS_EXACT_NONTEST_B_BOUNDARY_PLAN_NO_MODEL_CALLS',
        'utc':c.utc(),'events':16,'variants':sum(len(e['variants']) for e in events),'optimizer_updates':0})
    print('PASS_EXACT_NONTEST_B_BOUNDARY_PLAN_NO_MODEL_CALLS', flush=True)


if __name__ == '__main__': main()
