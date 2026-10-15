"""Full four-source eight-gate proxy comparison; never called by GPU inference."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import positive_io as io
import positive_metrics as m
from positive_runtime import accepted, base, completed


def validate_export_binding(req, event, receipt, done, proof, first_input_qa_ref):
    """Pure exact equality gate after caller has checked each immutable file ref."""
    io.require(receipt['case_id'] == done['case_id'] == proof['case_id'] == req['request_id'] and
        done['status'] == 'PASS_POSITIVE_DECISION_NOT_QUALITY' and
        proof['status'] == 'PASS_INDEPENDENT_POSITIVE_OUTPUT_TOKEN_GRAMMAR_PARSER_NATIVE_QA' and
        done['group'] == proof['group'] == req['group'] and
        proof['done_ref'] == receipt['done_ref'] and proof['raw_ref'] == done['raw_ref'] and
        proof['first_input_QA_completion_ref'] == first_input_qa_ref and
        event['decision_result'] == done['decision_result'] == proof['decision_result'] and
        event['original_native_range'] == proof['original_native_range'] and
        event['source_name'] == req['source_name'] and event['source_sha256'] == req['source_sha256'] and
        event['event_id'] == req['event_id'] == done['decision_result']['event_id'] and
        event['old_event_id'] == req['old_event_id'] == done['decision_result']['old_event_id'] and
        event['original_case_id'] == req['original_case_id'] and
        event['original_segment_index'] == req['original_segment_index'] and
        done['decision_result']['request_id'] == req['request_id'] and
        done['input_evidence'] == req['input_evidence'],
        'Export must exactly match checked actual GPU done and first output-QA proof')


def assess(cases, gates):
    io.require(len(cases) == 4, 'Complete frozen four-source denominator required')
    macro = lambda arm, key: sum((case[arm][key] for case in cases), F(0))/4
    delta = {key: macro('augmented', key)-macro('baseline', key) for key in ('f1', 'recall', 'precision')}
    conditions = dict(full_group=True,
        macro_F1_not_lower=delta['f1'] >= F(gates['macro_paired_all_rater_duration_F1_delta_min']),
        macro_recall_gain=delta['recall'] >= F(gates['macro_all_rater_recall_delta_min']),
        every_source_loss_within_gate=all(case['augmented']['f1']-case['baseline']['f1'] >= F(gates['per_source_F1_delta_min']) for case in cases),
        macro_precision_not_lower=delta['precision'] >= F(gates['macro_all_rater_precision_delta_min']),
        all_rater_recall_retained=all(case['all_rater_recall_preserved'] for case in cases),
        all_baseline_native_frames_retained=all(case['baseline_native_frames_preserved'] for case in cases),
        real_changed_sources=sum(case['added_native_frames'] > 0 for case in cases) >= gates['minimum_sources_with_real_new_native_frames'])
    return conditions, {key: dict(baseline=float(macro('baseline', key)), baseline_exact=str(macro('baseline', key)),
        augmented=float(macro('augmented', key)), augmented_exact=str(macro('augmented', key)),
        delta=float(delta[key]), delta_exact=str(delta[key])) for key in delta}


def evaluate(root, group):
    io.host(cpu=True)
    reg, protocol, reg_path = io.registration(root, group)
    _, gate, gate_path, values = accepted(root, group)
    adopted = io.adopted(root, group, reg)
    export_path = base(root, group)/'verification_export.json'; export = io.read(export_path)
    io.require(export['status'] == io.EXPORT_STATUS and export['group'] == group and
        export['model_parameters'] == io.c.MODEL_PARAMETERS and export['new_additions_require_explicit_KEEP'] is True and
        export['UNKNOWN_does_not_add'] is True, 'Complete new execution and output-only QA export required')
    qa_path = io.checked_ref(export['output_QA_completion_ref']); qa = io.read(qa_path)
    io.require(qa['status'] == io.REPLAY_STATUS and qa['calls'] == len(values) == len(export['events']) == len(qa['proofs']) and
        qa['CPU_only'] is True and qa['CUDA_initialized'] is False and qa['input_token_reencodes'] == 0,
        'Entire independent output-only QA required')
    gpu_complete = None
    if values:
        _, resource_sha = io.terminal(gate)
        gpu_complete = completed(root, group, reg, gate, gate_path, values)
        io.require(qa['resource_terminal_sha256'] == resource_sha and
            qa['gpu_completion_ref'] == io.ref(base(root, group)/'gpu_01/completion.json'), 'Actual new GPU/QA natural terminal differs')
    else:
        io.require(export.get('zero_model_calls') is True and not (base(root, group)/'gpu_01').exists(),
                   'Genuine zero-candidate export may never use an actual model job')
    by_old = {req['old_event_id']: req for _, req, _ in values}
    io.require(len(by_old) == len(values) and len({e['old_event_id'] for e in export['events']}) == len(values) and
        {e['old_event_id'] for e in export['events']} == set(by_old), 'Every complete new output is required once')
    io.require([row['case_id'] for row in qa['proofs']] == [entry['case_id'] for entry, _, _ in values] and
        qa['first_input_QA_completion_ref'] == gate['first_input_QA_ref'],
        'Output-QA complete unique input order/binding differs')
    outputs = {}
    for receipt, qa_row in zip(gpu_complete['entries'] if gpu_complete else [], qa['proofs']):
        done = io.read(io.checked_ref(receipt['done_ref']))
        proof = io.read(io.checked_ref(qa_row['proof_ref']))
        io.checked_ref(done['raw_ref']); io.checked_ref(done['request_ref'])
        io.require(qa_row['case_id'] == receipt['case_id'] and receipt['case_id'] not in outputs,
                   'Duplicate/foreign actual GPU/output-QA case')
        outputs[receipt['case_id']] = (receipt, done, proof)
    new_by_source = {name: [] for name in adopted['source_names']}
    for event in export['events']:
        req = by_old[event['old_event_id']]; result = event['decision_result']
        io.require(req['request_id'] in outputs, 'Export event has no checked actual GPU/QA case')
        receipt, done, proof = outputs[req['request_id']]
        validate_export_binding(req, event, receipt, done, proof, gate['first_input_QA_ref'])
        io.require(event['original_interval_exact'] == req['original_interval_exact'] == result['original_interval_exact'] and
            event['source_name'] == req['source_name'] and result['successful_model_call_required'] is True and
            result['decision'] in io.c.DECISIONS and result['eligible_for_new_addition'] == (result['decision'] == 'KEEP') and
            result['baseline_deletion_authorized'] is False and result['boundaries_changed'] is False,
            'Only explicit new KEEP can add the complete untouched original candidate')
        if result['decision'] == 'KEEP':
            new_by_source[req['source_name']].append(req['original_interval_exact'])
    references, reference_refs = {}, []
    cohorts = reg['adopted_source_groups'][group]
    if isinstance(cohorts, dict):
        cohorts = [cohorts]
    for cohort in cohorts:
        ref_path = io.checked_ref(cohort['reference_completion']); reference_refs.append(io.ref(ref_path))
        receipt = io.read(ref_path)
        if set(receipt) == {'path', 'sha256'}:
            ref_path = io.checked_ref(receipt); reference_refs.append(io.ref(ref_path)); receipt = io.read(ref_path)
        io.require(receipt['group'] == cohort['prior_group'] and len(receipt['accepted']) == len(cohort['source_names']),
                   'Complete original four-source accepted reference receipt required')
        for row in receipt['accepted']:
            io.require(row['video_id'] in cohort['source_names'] and row['video_id'] not in references,
                       'Duplicate/foreign reference source')
            references[row['video_id']] = row
    io.require(set(references) == set(adopted['source_names']) and len(references) == 4, 'Every original reference source required')
    inputs = {case: value['meta'] for case, value in adopted['inputs'].items()}
    cases = []
    for name in adopted['source_names']:
        row = references[name]
        reference_path = io.checked(row['reference_path'], row['reference_sha256'])
        clock_path = io.checked(row['clock_path'], row['clock_sha256'])
        reference, clock = io.read(reference_path), io.read(clock_path)
        old_events = [e for e in adopted['events'] if e['source_name'] == name]
        baseline = m.baseline_prediction(old_events, inputs)
        novel = m.merged(new_by_source[name]); augmented = m.merged(baseline+novel)
        raters = reference['annotator_intervals_exact_seconds']
        io.require(len(raters) == reference['annotator_count'] >= 2, 'All original reference reviewers required')
        paired = [(m.metrics(baseline, r), m.metrics(augmented, r)) for r in raters]
        average = lambda arm: {key: sum((value[arm][key] for value in paired), F(0))/len(paired) for key in ('f1', 'recall', 'precision')}
        pts = list(map(F, clock['original_exact_pts']))
        source_metas = [value for value in inputs.values() if value['source_name'] == name]
        io.require(all(meta['all_source_exact_pts'] == clock['original_exact_pts'] for meta in source_metas),
                   'Original exact reference/native input clocks differ')
        old_frames, new_frames = m.frames(baseline, pts), m.frames(augmented, pts)
        cases.append(dict(video_id=name, baseline=average(0), augmented=average(1),
            all_rater_recall_preserved=all(b['recall'] >= a['recall'] for a, b in paired),
            baseline_native_frames_preserved=old_frames <= new_frames,
            baseline_selected_frames=len(old_frames), augmented_selected_frames=len(new_frames),
            added_native_frames=len(new_frames-old_frames), annotator_count=len(raters),
            baseline_spans=[[str(a), str(b)] for a, b in baseline],
            augmented_spans=[[str(a), str(b)] for a, b in augmented],
            new_positive_KEEP_spans=[[str(a), str(b)] for a, b in novel],
            reference_ref=io.ref(reference_path), clock_ref=io.ref(clock_path)))
    conditions, macro = assess(cases, protocol['quality_gates'])
    io.require(tuple(conditions) == io.CONDITIONS, 'All eight original quality gates required')
    passed = all(conditions.values())
    out = root/group/'comparison_01'; out.mkdir(exist_ok=False)
    serialized = [{**case, **{arm: {key: dict(exact=str(value), value=float(value))
        for key, value in case[arm].items()} for arm in ('baseline', 'augmented')}} for case in cases]
    status = ('PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION' if group == 'dev' else
              'PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40') if passed else 'STOP_ROLE_FRESH_CONFIRM_REJECTED'
    io.save(out/'result.json', dict(status=status, group=group, utc=io.utc(), conditions=conditions,
        macro=macro, cases=serialized, candidate=protocol['candidate'],
        bindings=dict(protocol_ref=reg['protocol_ref'], registration_ref=io.ref(reg_path),
            verification_export_ref=io.ref(export_path), reference_completion_refs=reference_refs,
            first_input_QA_ref=gate['first_input_QA_ref'], output_QA_completion_ref=io.ref(qa_path)),
        source_metrics_exposed_first_time=group == 'confirm', proxy_is_not_highlight_or_ORDINARY_gold=True,
        actual_online_improvement='UNKNOWN', old_failed_gates_changed=False, production_admitted=False,
        no_fixed40_426_or_package_started=True))
    if passed and group == 'dev':
        io.save(root/'dev/selection_before_confirmation.json', dict(status='PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION',
            utc=io.utc(), protocol_sha256=reg['protocol_ref']['sha256'], result_ref=io.ref(out/'result.json'),
            code_files=io.code_files(), candidate=protocol['candidate'], confirm_metrics_examined=False,
            fresh_confirmation_requires_separate_registration=True, production_admitted=False))
    print(json.dumps(dict(status=status, conditions=conditions, macro=macro)), flush=True)
    return 0 if passed else 5


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=('dev', 'confirm'), required=True)
    args = parser.parse_args()
    import os
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.exit(evaluate(io.root_path(args.root), args.group))
