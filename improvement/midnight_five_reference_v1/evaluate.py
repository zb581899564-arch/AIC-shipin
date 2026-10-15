"""First new ordinary/redundant deletion comparison on all original raters.

Only this CPU process opens references. No manual summary omission is treated
as ORDINARY truth. This duration-summary proxy is not the official score.
"""
import argparse
from fractions import Fraction as F
from pathlib import Path
import sys

from reference_common import (ARMS, checked, exact_metrics, frames, merged,
    metrics, read, ref, require, save, serialized, validate_gates, validate_indices)


def checked_decisions(inputs, decisions, decision_directory):
    """Bind each new parsed decision to its actual done and independent QA."""
    expected = {entry['case_id']: entry for entry in inputs['entries']}
    rows = decisions['entries']
    require([row['case_id'] for row in rows] == list(expected) and len(rows) == len(expected),
            'Complete unique new decision denominator and order required')
    require(decisions['status'] == 'COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY'
        and decisions['actual_model_calls'] == len(rows) and decisions['first_input_QA_complete'] is True
        and decisions['first_output_QA_complete'] is True and decisions['reference_labels_in_inference'] is False,
        'Complete new actual inference and first independent input/output QA required')
    terminal = read(checked(decisions['unique_gpu_terminal_ref']))
    require(terminal['status'] == 'completed' and terminal['exit_code'] == 0, 'New GPU must complete naturally')
    result = {}
    for row in rows:
        case = row['case_id']; entry = expected[case]
        dp = checked(row['decision_ref']); done = read(dp); proof = read(checked(row['output_qa_ref']))
        require(dp.is_relative_to(decision_directory), 'Actual new done escaped its new completed stage')
        require(done['case_id'] == case and proof['done_ref'] == row['decision_ref']
            and done['parsed'] == proof['parsed'] and proof['CPU_only'] is True
            and proof['status'] == 'PASS_FIRST_INDEPENDENT_OUTPUT_QA' and proof['new_model_calls'] == 0,
            'Decision differs from independently accepted actual done')
        raw = read(checked(done['raw_ref'])); actual_input = read(checked(done['input_ref']))
        first_qa = read(checked(done['first_input_qa_ref']))
        require(proof['raw_ref'] == done['raw_ref'] and proof['first_input_qa_ref'] == done['first_input_qa_ref']
            and raw['actual_model_call'] is True and raw['input_ref'] == done['input_ref']
            and raw['first_input_qa_ref'] == done['first_input_qa_ref'] and first_qa['input_ref'] == done['input_ref'],
            'Actual input/raw/first QA chain differs')
        for key in ('case_id', 'source_name', 'source_id', 'source_sha256', 'source_ordinals', 'exact_pts',
                    'window_exact', 'candidate_events', 'cache_ref', 'original_first_QA_ref'):
            require(actual_input[key] == row[key] == entry[key], 'Actual new input differs from frozen mapping: '+key)
        result[case] = validate_indices({arm: done['parsed'][arm] for arm in ARMS}, len(entry['candidate_events']))
    return result


def evaluate(manifest_path, decisions_path, output):
    manifest, decisions = read(manifest_path), read(decisions_path)
    require(manifest['schema'] == 'MIDNIGHT_DELETE_REFERENCE_V1' and manifest['group'] in ('dev', 'confirm'),
            'Explicit independent deletion-only reference manifest required')
    protocol = read(checked(manifest['protocol_ref'])); gates = validate_gates(protocol)
    inputs = read(checked(manifest['inputs_ref']))
    require(inputs['schema'] == 'MIDNIGHT_DELETE_INPUT_ENTRIES_V1' and inputs['group'] == manifest['group']
        and inputs['protocol_ref'] == manifest['protocol_ref'], 'Frozen new protocol/input/decision binding differs')
    if manifest['group'] == 'dev':
        eligible_arms = set(ARMS)
        require(inputs['all_sources_previously_exposed'] is True
            and manifest['exposure_label'] == 'development_previously_exposed', 'Exposed sources are development only')
    else:
        admission = read(checked(manifest['fresh_admission_ref']))
        require(admission['status'] == 'PASS_MIDNIGHT_NEW4_ID_BYTES_NATIVE_ADMISSION'
            and admission['sources_unexposed_before_registration'] is True
            and admission['quality_metrics_examined_before_freeze'] is False
            and admission['protocol_ref'] == manifest['protocol_ref']
            and admission['source_names'] == [source['source_name'] for source in manifest['sources']],
            'Fresh independently admitted IDs, bytes, clocks and frozen development required')
        selection = read(checked(admission['development_selection_ref']))
        eligible_arms = set(admission['admitted_arms'])
        require(selection['protocol_ref'] == manifest['protocol_ref'] and selection['confirm_metrics_examined'] is False
            and eligible_arms and eligible_arms <= set(ARMS)
            and all(selection['passed_arms'].get(arm) is True for arm in eligible_arms),
            'Only an arm with actual frozen development PASS may run first fresh confirmation')
    parsed = checked_decisions(inputs, decisions, decisions_path.resolve().parent)
    names = [source['source_name'] for source in manifest['sources']]
    require(len(names) == len(set(names)) == gates['full_group_denominator'] == 4
        and {entry['source_name'] for entry in inputs['entries']} == set(names), 'Full four-source denominator required')
    cases_by_arm = {arm: [] for arm in ARMS}
    for source in manifest['sources']:
        name = source['source_name']; clock = read(checked(source['clock_ref']))
        reference = read(checked(source['reference_ref']))
        points = list(map(F, clock['original_exact_pts']))
        require(points and points == sorted(set(points)), 'Complete monotone native source clock required')
        raters = reference['annotator_intervals_exact_seconds']
        require(len(raters) == reference['annotator_count'] >= 2, 'Every original reference rater required')
        entries = [entry for entry in inputs['entries'] if entry['source_name'] == name]
        for entry in entries:
            require(entry['source_sha256'] == source['source_sha256']
                and [str(points[i]) for i in entry['source_ordinals']] == entry['exact_pts'],
                'Actual input observation/reference native clock differs')
        baseline = merged([event['selected_interval_exact'] for entry in entries for event in entry['candidate_events']])
        require(serialized(baseline) == source['baseline_spans'], 'Protected baseline union differs')
        old_frames = frames(baseline, points)
        baseline_raters = [metrics(baseline, rater) for rater in raters]
        baseline_average = {key: sum((value[key] for value in baseline_raters), F(0))/len(raters)
            for key in ('f1', 'precision', 'recall')}
        for arm in ARMS:
            if arm not in eligible_arms:
                continue
            retained, deleted = [], []
            for entry in entries:
                for index, event in enumerate(entry['candidate_events']):
                    require(F(event['selected_interval_exact'][0]) < F(event['selected_interval_exact'][1]),
                            'Untouched original baseline contribution required')
                    (deleted if index in parsed[entry['case_id']][arm] else retained).append(event)
            prediction = merged([event['selected_interval_exact'] for event in retained])
            new_frames = frames(prediction, points)
            require(new_frames <= old_frames, 'A deletion-only arm cannot introduce any new native frame')
            averages = {key: sum((metrics(prediction, rater)[key] for rater in raters), F(0))/len(raters)
                for key in ('f1', 'precision', 'recall')}
            cases_by_arm[arm].append(dict(source_name=name, video_id=source['source_id'], annotator_count=len(raters),
                baseline=baseline_average, candidate=averages, baseline_spans=serialized(baseline), candidate_spans=serialized(prediction),
                baseline_native_frames=len(old_frames), candidate_native_frames=len(new_frames),
                removed_native_frames=len(old_frames-new_frames), added_native_frames=len(new_frames-old_frames),
                deleted_event_ids=[event['event_id'] for event in deleted], retained_event_ids=[event['event_id'] for event in retained],
                reference_ref=source['reference_ref'], clock_ref=source['clock_ref']))
    arms = {}
    for arm, cases in cases_by_arm.items():
        if arm not in eligible_arms:
            arms[arm] = dict(status='NOT_ADMITTED_DEVELOPMENT_FAILED_OR_NOT_SELECTED', PASS=False,
                gates={}, macro={}, cases=[], skipped_without_reference_metric=True)
            continue
        average = lambda which, key: sum((case[which][key] for case in cases), F(0))/4
        macro = {key: dict(baseline=average('baseline', key), candidate=average('candidate', key),
            delta=average('candidate', key)-average('baseline', key)) for key in ('f1', 'precision', 'recall')}
        conditions = dict(full_group=True, macro_F1_not_lower=macro['f1']['delta'] >= 0,
            macro_precision_not_lower=macro['precision']['delta'] >= 0,
            every_source_F1_loss_at_most_001=all(case['candidate']['f1']-case['baseline']['f1'] >= F(-1, 100) for case in cases),
            invalid_decisions_zero=True, full_original_rater_denominator=True,
            real_changed_sources=sum(case['removed_native_frames'] > 0 for case in cases) >= 1,
            no_new_native_frames=all(case['added_native_frames'] == 0 for case in cases))
        passed = all(conditions.values())
        arms[arm] = dict(status=('PASS_DEV_PENDING_FIRST_FRESH_CONFIRMATION' if manifest['group'] == 'dev' else
            'PASS_FIRST_FRESH_CONFIRMATION_PENDING_FIXED_FACTS') if passed else 'STOP_'+manifest['group'].upper()+'_REJECTED',
            PASS=passed, gates=conditions, macro={key: {field: dict(exact=str(value), value=float(value))
                for field, value in values.items()} for key, values in macro.items()},
            cases=[{**case, 'baseline': exact_metrics(case['baseline']), 'candidate': exact_metrics(case['candidate'])} for case in cases])
    result = dict(schema='MIDNIGHT_DELETE_COMPARISON_V1', group=manifest['group'], arms=arms,
        passed_arms={arm: value['PASS'] for arm, value in arms.items()}, full_source_count=4,
        bindings=dict(manifest_ref=ref(manifest_path), decisions_ref=ref(decisions_path), protocol_ref=manifest['protocol_ref']),
        exposure_label=manifest['exposure_label'], recall_not_an_absolute_non_degradation_gate=True,
        reference_scope='EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NOT_ORDINARY_OR_DENSE_HIGHLIGHT_GOLD',
        actual_official_improvement='UNKNOWN', old_scientific_failures_changed=False,
        new_model_calls=0, old_QA_repeated=0, production_admitted=False)
    save(output, result)
    if manifest['group'] == 'dev' and any(result['passed_arms'].values()):
        save(output.with_name(output.stem+'_selection.json'), dict(schema='MIDNIGHT_DELETE_DEV_SELECTION_V1',
            passed_arms=result['passed_arms'], result_ref=ref(output), protocol_ref=manifest['protocol_ref'],
            confirm_metrics_examined=False, production_admitted=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.manifest, args.decisions, args.output)
    print({arm: data['PASS'] for arm, data in result['arms'].items()})
    sys.exit(0 if any(result['passed_arms'].values()) else 5)
