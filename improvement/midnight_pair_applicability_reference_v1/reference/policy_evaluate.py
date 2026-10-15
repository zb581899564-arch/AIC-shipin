"""Three preregistered worst-ID policies; two new development comparisons only.

ALL_WINDOW_WORST adopts its already completed exact result. BUDGET_TWO_THIRDS
and PAIR_ONLY only filter that same actual model-selected worst index. No raw
answer, endpoint, candidate, reference label or old result is rewritten.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

from evaluate import checked_decisions
from reference_common import (checked, exact_metrics, frames, merged, metrics, read,
    ref, require, save, serialized, validate_gates)

POLICIES = ('ALL_WINDOW_WORST', 'BUDGET_TWO_THIRDS', 'PAIR_ONLY')


def retained_event_policy(policy, count, actual_worst):
    require(policy in POLICIES and len(actual_worst) <= 1 and (count >= 2 or not actual_worst),
            'Actual successful relative response must name at most one worst, and none for n<2')
    if policy == 'BUDGET_TWO_THIRDS':
        return actual_worst if count >= 3 else []
    if policy == 'PAIR_ONLY':
        return actual_worst if count == 2 else []
    return actual_worst


def assess(cases):
    require(len(cases) == 4, 'Full original four-source denominator required')
    macro_mean = lambda arm, key: sum((case[arm][key] for case in cases), F(0))/4
    macro = {key: {field: dict(exact=str(value), value=float(value)) for field, value in dict(
        baseline=macro_mean('baseline', key), candidate=macro_mean('candidate', key),
        delta=macro_mean('candidate', key)-macro_mean('baseline', key)).items()} for key in ('f1', 'precision', 'recall')}
    gates = dict(full_group=True, macro_F1_not_lower=F(macro['f1']['delta']['exact']) >= 0,
        macro_precision_not_lower=F(macro['precision']['delta']['exact']) >= 0,
        every_source_F1_loss_at_most_001=all(case['candidate']['f1']-case['baseline']['f1'] >= F(-1, 100) for case in cases),
        invalid_decisions_zero=True, full_original_rater_denominator=True,
        real_changed_sources=any(case['removed_native_frames'] > 0 for case in cases),
        no_new_native_frames=all(case['added_native_frames'] == 0 for case in cases))
    return dict(PASS=all(gates.values()), gates=gates, macro=macro,
        cases=[{**case, 'baseline': exact_metrics(case['baseline']), 'candidate': exact_metrics(case['candidate'])} for case in cases])


def evaluate(protocol_path, output, manifest_path=None, decisions_path=None, development_selection=None):
    protocol_ref = ref(protocol_path); protocol = read(checked(protocol_ref)); validate_gates(protocol)
    require(protocol['policies'] == list(POLICIES) and protocol['max_selected_policies'] == 2
        and set(protocol['selection_order']) == set(POLICIES) and len(protocol['selection_order']) == 3,
        'Exactly three discrete policies and a frozen two-policy selection order required')
    source_protocol = read(checked(protocol['source_protocol_ref'])); validate_gates(source_protocol)
    group = 'confirm' if manifest_path else 'dev'
    manifest_ref = ref(manifest_path) if manifest_path else protocol['source_manifest_ref']
    completion_ref = ref(decisions_path) if decisions_path else protocol['source_completion_ref']
    manifest, completion = read(checked(manifest_ref)), read(checked(completion_ref))
    inputs = read(checked(manifest['inputs_ref']))
    require(manifest['group'] == inputs['group'] == group and len(manifest['sources']) == 4,
            'Complete explicit development or first-confirmation source group required')
    prior = read(checked(protocol['prior_all_window_result_ref']))
    require(prior['group'] == 'dev' and prior['bindings']['manifest_ref'] == protocol['source_manifest_ref']
        and prior['bindings']['decisions_ref'] == protocol['source_completion_ref']
        and prior['bindings']['protocol_ref'] == protocol['source_protocol_ref'], 'Exact naturally completed all-window result binding required')
    if group == 'dev':
        require(manifest['protocol_ref'] == inputs['protocol_ref'] == protocol['source_protocol_ref']
            and manifest['exposure_label'] == 'development_previously_exposed'
            and inputs['all_sources_previously_exposed'] is True, 'Only already exposed original development group may select policies')
        active_policies = list(POLICIES)
    else:
        require(decisions_path is not None and development_selection is not None
            and manifest['protocol_ref'] == inputs['protocol_ref'] == protocol_ref, 'First confirmation must bind the newly frozen policy protocol')
        selection = read(checked(ref(development_selection))); dev_result = read(checked(selection['result_ref']))
        require(selection['schema'] == 'MIDNIGHT_DELETE_DEV_SELECTION_V1' and selection['protocol_ref'] == protocol_ref
            and selection['confirm_metrics_examined'] is False and selection['passed_arms'] == dev_result['passed_arms']
            and dev_result['bindings']['protocol_ref'] == protocol_ref, 'Actual frozen passing policy selection required')
        active_policies = selection['selected_policies']
        require(active_policies == ['PAIR_ONLY'] and selection['confirm_metrics_examined_scope'] == 'THIS_NEW_SHORT_COHORT_ONLY'
            and selection['prior_confirm_metrics_examined'] is True and selection['old_confirm_result_unchanged'] is True, 'Only the separately frozen single short-source PAIR cohort may be evaluated')
        require(0 < len(active_policies) <= 2 and len(set(active_policies)) == len(active_policies)
            and set(active_policies) <= set(POLICIES)
            and all(selection['passed_arms'][policy] is True for policy in active_policies), 'Only selected development-passing policies may be confirmed')
        admission = read(checked(manifest['fresh_admission_ref']))
        require(admission['status'] == 'PASS_MIDNIGHT_NEW4_ID_BYTES_NATIVE_ADMISSION'
            and admission['protocol_ref'] == protocol_ref and admission['development_selection_ref'] == ref(development_selection)
            and admission['sources_unexposed_before_registration'] is True
            and admission['quality_metrics_examined_before_freeze'] is False
            and admission['source_names'] == [source['source_name'] for source in manifest['sources']],
            'Actual fresh source/byte/native/input registration required')
    parsed = checked_decisions(inputs, completion, Path(completion_ref['path']).resolve().parent)
    for entry in inputs['entries']:
        retained_event_policy('ALL_WINDOW_WORST', len(entry['candidate_events']), parsed[entry['case_id']]['redundant'])
    names = [source['source_name'] for source in manifest['sources']]
    require(len(set(names)) == 4 and {entry['source_name'] for entry in inputs['entries']} <= set(names),
            'Never omit a source from the complete four-source denominator')
    prior_cases = {case['source_name']: case for case in prior['arms']['redundant']['cases']}
    policy_cases = {policy: [] for policy in active_policies}; prediction_sets = {policy: [] for policy in active_policies}
    for source in manifest['sources']:
        name = source['source_name']; clock = read(checked(source['clock_ref'])); points = list(map(F, clock['original_exact_pts']))
        entries = [entry for entry in inputs['entries'] if entry['source_name'] == name]
        for entry in entries:
            require(entry['source_sha256'] == source['source_sha256']
                and [str(points[i]) for i in entry['source_ordinals']] == entry['exact_pts'], 'Actual native observation/source clock differs')
        baseline = merged([event['selected_interval_exact'] for entry in entries for event in entry['candidate_events']])
        require(serialized(baseline) == source['baseline_spans'], 'Untouched baseline contribution union required')
        old_frames = frames(baseline, points)
        # Actual reference content is opened only for genuinely new policy comparisons.
        reference = read(checked(source['reference_ref'])); raters = reference['annotator_intervals_exact_seconds']
        require(len(raters) == reference['annotator_count'] >= 2, 'Every original reference rater is required')
        average = lambda spans: {key: sum((metrics(spans, rater)[key] for rater in raters), F(0))/len(raters)
            for key in ('f1', 'precision', 'recall')}
        baseline_average = average(baseline)
        if group == 'dev':
            require(all(str(value) == prior_cases[name]['baseline'][key]['exact'] for key, value in baseline_average.items()),
                    'New policy baseline must equal the accepted complete all-window baseline')
        for policy in active_policies:
            retained, deleted = [], []
            for entry in entries:
                count = len(entry['candidate_events']); deleted_indices = retained_event_policy(policy, count, parsed[entry['case_id']]['redundant'])
                for index, event in enumerate(entry['candidate_events']):
                    (deleted if index in deleted_indices else retained).append(event)
            prediction = merged([event['selected_interval_exact'] for event in retained]); new_frames = frames(prediction, points)
            require(new_frames <= old_frames, 'A fixed worst-ID policy cannot add frames or change endpoints')
            prediction_sets[policy].append(dict(source_name=name, source_sha256=source['source_sha256'], native_ordinals=sorted(new_frames)))
            if group == 'dev' and policy == 'ALL_WINDOW_WORST':
                require(serialized(prediction) == prior_cases[name]['candidate_spans'], 'Adopted all-window result differs from actual unchanged worst IDs')
                continue
            policy_cases[policy].append(dict(source_name=name, video_id=source['source_id'], annotator_count=len(raters),
                baseline=baseline_average, candidate=average(prediction), baseline_spans=serialized(baseline), candidate_spans=serialized(prediction),
                baseline_native_frames=len(old_frames), candidate_native_frames=len(new_frames), removed_native_frames=len(old_frames-new_frames),
                added_native_frames=len(new_frames-old_frames), deleted_event_ids=[event['event_id'] for event in deleted],
                retained_event_ids=[event['event_id'] for event in retained], reference_ref=source['reference_ref'], clock_ref=source['clock_ref']))
    policies = {}
    for policy in active_policies:
        if group == 'dev' and policy == 'ALL_WINDOW_WORST':
            value = dict(prior['arms']['redundant'], adopted_prior_result_ref=protocol['prior_all_window_result_ref'],
                successful_quality_comparison_repeated=False)
        else:
            value = assess(policy_cases[policy])
        value['prediction_signature'] = hashlib.sha256(json.dumps(prediction_sets[policy], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        value['prediction_native_sets'] = prediction_sets[policy]
        policies[policy] = value
    passed = {policy: value['PASS'] for policy, value in policies.items()}
    selected, seen_predictions = [], []
    if group == 'dev':
        for policy in protocol['selection_order']:
            if passed[policy] and prediction_sets[policy] not in seen_predictions:
                selected.append(policy); seen_predictions.append(prediction_sets[policy])
                if len(selected) == 2:
                    break
    else:
        selected = active_policies
    result = dict(schema='MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1', group=group,
        status=('TWO_DISTINCT_PASSING_POLICIES_FROZEN_PENDING_FIRST_FRESH_CONFIRMATION' if len(selected) == 2 else
            'INSUFFICIENT_TWO_DISTINCT_PASSING_POLICIES') if group == 'dev' else 'FIRST_FRESH_POLICY_COMPARISON_COMPLETE',
        policies=policies, passed_policies=passed, passed_arms=passed, selected_policies=selected,
        selected_predictions_genuinely_distinct=(len(selected) == 2 and prediction_sets[selected[0]] != prediction_sets[selected[1]]),
        full_source_count=4, bindings=dict(protocol_ref=protocol_ref, manifest_ref=manifest_ref,
            decisions_ref=completion_ref, source_protocol_ref=protocol['source_protocol_ref']),
        all_development_sources_previously_exposed=True, source_model_answers_modified=False,
        ordinary_failed_result_changed=False, old_scientific_failures_changed=False, new_model_calls=0, prior_QA_repeated=0,
        source_all_window_comparison_repeated=False, actual_official_improvement='UNKNOWN', production_admitted=False)
    require(group == 'confirm', 'This independent wrapper cannot rescore development')
    result['status'] = 'FIRST_FRESH_POLICY_COMPARISON_COMPLETE'
    result['comparison_scope'] = 'SUPPLEMENTAL_SHORT_PAIR_APPLICABILITY_COMPARISON_COMPLETE'
    result['bindings']['supplemental_protocol_ref'] = selection['supplemental_protocol_ref']
    result['bindings']['development_selection_ref'] = ref(development_selection)
    result['bindings']['prior_neutral_no_applicability_result_ref'] = selection['prior_fresh_result_ref']
    result['old_neutral_no_applicability_result_unchanged'] = True
    save(output, result)
    if group == 'dev' and selected:
        save(output.with_name(output.stem+'_selection.json'), dict(schema='MIDNIGHT_DELETE_DEV_SELECTION_V1',
            passed_arms=passed, selected_policies=selected, selected_predictions_genuinely_distinct=result['selected_predictions_genuinely_distinct'],
            result_ref=ref(output), protocol_ref=protocol_ref, confirm_metrics_examined=False, production_admitted=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--manifest', type=Path)
    parser.add_argument('--decisions', type=Path); parser.add_argument('--development-selection', type=Path)
    args = parser.parse_args(); result = evaluate(args.protocol, args.output, args.manifest, args.decisions, args.development_selection)
    print(dict(passed=result['passed_policies'], selected=result['selected_policies'], status=result['status']))
    sys.exit(0 if result['selected_policies'] == ['PAIR_ONLY'] and all(result['passed_policies'][p] for p in result['selected_policies']) else 5)
