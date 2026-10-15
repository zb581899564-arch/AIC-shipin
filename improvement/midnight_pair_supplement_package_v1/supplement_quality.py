"""Validate the new short-source applicability scope without changing old FAIL.

Only JSON evidence is read through a path/SHA-verifying caller.  No inference,
quality re-evaluation, label selection, or result mutation occurs here.
"""
from package_math import exact, require
from production_evidence import ref_key, same_ref

POLICY = 'PAIR_ONLY'
APPLICATION_POLICY = 'WORST_PAIR_ONLY'
SCOPE = 'SHORT_SOURCE_PAIR_APPLICABILITY_SUPPLEMENT_ONLY'
GATE_KEYS = frozenset(('full_group', 'macro_F1_not_lower', 'macro_precision_not_lower',
    'every_source_F1_loss_at_most_001', 'invalid_decisions_zero',
    'full_original_rater_denominator', 'real_changed_sources', 'no_new_native_frames'))
METRICS = ('f1', 'precision', 'recall')


def policy_result(value, passed):
    require(value['schema'] == 'MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1' and
            value['group'] == 'confirm' and value['status'] == 'FIRST_FRESH_POLICY_COMPARISON_COMPLETE' and
            value['full_source_count'] == 4 and value['source_model_answers_modified'] is False and
            value['old_scientific_failures_changed'] is False and value['passed_policies'][POLICY] is passed,
            'Actual complete unchanged four-source PAIR_ONLY comparison required')
    result = value['policies'][POLICY]
    require(result['PASS'] is passed and set(result['gates']) == GATE_KEYS and len(result['cases']) == 4,
            'Exact original eight gates and full four-source denominator required')
    expected = {key: True for key in GATE_KEYS}
    if not passed:
        expected['real_changed_sources'] = False
    require(result['gates'] == expected, 'Original zero-change failure or supplemental fixed-gate PASS differs')
    for reference in value['bindings'].values():
        ref_key(reference)
    return result


def source_set(manifest, group):
    sources = manifest['sources']
    require(manifest['group'] == group and len(sources) == 4, 'Complete explicit external source cohort required')
    names = {value['source_name'] for value in sources}
    digests = {value['source_sha256'] for value in sources}
    require(len(names) == len(digests) == 4 and all(names) and all(digests), 'Duplicate/missing external source identity')
    return names, digests


def validate_quality(value, original_admission, protocol_ref, protocol, read_ref):
    require(value['status'] == 'PASS' and value['deterministic_deletion_policy'] == APPLICATION_POLICY and
            value['actual_model_parsed_unchanged'] is True and value['independent_confirmation'] is True and
            value['test_labels_used'] is False and value['old_result_unchanged'] is True and
            value['policy_and_gates_unchanged'] is True and value['supplemental_scope_only'] is True and
            value['reference_scope_kind'] == SCOPE and isinstance(value['reference_scope'], str) and value['reference_scope'],
            'New PASS must be limited to the unchanged short-source pair applicability supplement')
    same_ref(value['frozen_rule_ref'], protocol_ref, 'Supplement must use the original publication protocol')
    require(protocol['deletion_application_policy']['REDUNDANT'] == APPLICATION_POLICY,
            'Original frozen WORST_PAIR_ONLY application changed')
    original_ref, supplemental_ref = value['original_nonapplicable_confirmation_ref'], value['supplemental_confirmation_ref']
    require(ref_key(original_ref) != ref_key(supplemental_ref), 'A new reference scope cannot relabel the old confirmation')
    same_ref(value['confirmation_ref'], supplemental_ref, 'Quality confirmation_ref must be the actual new supplemental result')
    original_arm = original_admission['arms']['REDUNDANT']
    require(original_arm['status'] == 'FAILED_FIXED_NEW_CONFIRMATION', 'Original REDUNDANT failure must remain unchanged')
    same_ref(original_arm['confirmation_ref'], original_ref, 'Old nonapplicable result does not match the original failed admission')
    same_ref(original_arm['frozen_rule_ref'], protocol_ref, 'Old failed admission belongs to another frozen application')
    same_ref(original_arm['development_ref'], value['development_ref'], 'Supplement must adopt the same original development result')
    original, supplemental, development = (read_ref(reference) for reference in
        (original_ref, supplemental_ref, value['development_ref']))
    old_pair = policy_result(original, False)
    new_pair = policy_result(supplemental, True)
    require(supplemental['selected_policies'] == [POLICY], 'Only the existing selected PAIR_ONLY policy is eligible here')
    for metric in METRICS:
        require(exact(old_pair['macro'][metric]['delta']['exact']) == 0,
                'The original four-source result was not an exact zero-change comparison')
    for case in old_pair['cases']:
        require(case['removed_native_frames'] == 0 and case['added_native_frames'] == 0 and
                all(exact(case['baseline'][metric]['exact']) == exact(case['candidate'][metric]['exact']) for metric in METRICS),
                'The old result must remain the actual nonapplicable zero-change failure')
    require(all(type(case['removed_native_frames']) is int and case['removed_native_frames'] >= 0 and
                case['added_native_frames'] == 0 for case in new_pair['cases']) and
            any(case['removed_native_frames'] > 0 for case in new_pair['cases']),
            'Supplement must have an actual nonempty deletion application and no added native frames')
    require(development['schema'] == 'MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1' and development['group'] == 'dev' and
            development['passed_policies'][POLICY] is True and development['policies'][POLICY]['PASS'] is True,
            'Original completed development PAIR_ONLY PASS is required without another comparison')
    for result in (original, supplemental, development):
        same_ref(result['bindings']['protocol_ref'], protocol['policy_protocol_ref'],
                 'Policy algorithm and original gate protocol must remain identical')
        for reference in result['bindings'].values():
            read_ref(reference)
    old_sources = source_set(read_ref(original['bindings']['manifest_ref']), 'confirm')
    new_manifest = read_ref(supplemental['bindings']['manifest_ref'])
    new_sources = source_set(new_manifest, 'confirm')
    dev_sources = source_set(read_ref(development['bindings']['manifest_ref']), 'dev')
    require(not (new_sources[0] & (old_sources[0] | dev_sources[0])) and
            not (new_sources[1] & (old_sources[1] | dev_sources[1])),
            'Supplemental four sources must have new identities and bytes')
    registration = value['supplementary_source_registration_ref']
    read_ref(registration)
    return dict(reference_scope=value['reference_scope'], reference_scope_kind=SCOPE,
                supplemental_scope_only=True, old_result_unchanged=True, policy_and_gates_unchanged=True,
                original_nonapplicable_confirmation_ref=original_ref, supplemental_confirmation_ref=supplemental_ref,
                supplementary_source_registration_ref=registration, original_confirmation_status='FAILED_FIXED_NEW_CONFIRMATION')
