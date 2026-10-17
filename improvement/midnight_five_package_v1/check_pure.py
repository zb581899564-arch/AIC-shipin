"""Small arithmetic checks only; no production files or packaging are read."""
from copy import deepcopy
from package_math import (SKIP_DROP, SKIP_NO64, combine, validate_deletion_policy_map,
                          validate_parsed)


def rejected(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError('Expected engineering rejection')


def main():
    clocks = {'0': dict(normalized_exact_pts=[str(value) for value in range(128)], physical_end_exact='128',
                        source_sha256='a' * 64)}
    events = {
        'e0': dict(source_id='0', original_interval_exact=['0', '20'], selected_interval_exact=['0', '20'], decision='KEEP'),
        'e1': dict(source_id='0', original_interval_exact=['10', '30'], selected_interval_exact=['10', '30'], decision='UNKNOWN'),
    }
    entry = dict(case_id='case0', source_id='0', source_sha256='a' * 64,
                 source_ordinals=list(range(64)), exact_pts=[str(value) for value in range(64)],
                 window_exact=['0', '64'], window_native_end_exact='64', window_native_end_ordinal=64,
                 candidate_events=[dict(event_id=key, **{name: value for name, value in event.items() if name != 'source_id'})
                                   for key, event in events.items()],
                 parsed=dict(ordinary=[0], redundant=[1], action=[30, 40], reaction=[60, 64], information=[10, 20]))
    baseline = {('0', frame) for frame in range(30)}
    result = combine([entry], baseline, clocks, events)
    assert result['ORDINARY']['selected_keys'] == {('0', frame) for frame in range(10, 30)}
    assert result['REDUNDANT']['selected_keys'] == {('0', frame) for frame in range(20)}
    assert result['ACTION']['selected_keys'] == {('0', frame) for frame in range(40)}
    assert result['REACTION']['selected_keys'] == baseline | {('0', frame) for frame in range(60, 64)}
    assert result['INFORMATION']['selected_keys'] == baseline
    assert result['REACTION']['added_interval_witnesses'][0]['native_interval'] == [60, 64]
    guard = deepcopy(entry); guard['parsed']['ordinary'] = [0, 1]
    guarded = combine([guard], baseline, clocks, events)['ORDINARY']
    assert guarded['selected_keys'] == baseline and guarded['empty_source_format_guard'] == ['0']
    invalid = deepcopy(entry); invalid['exact_pts'][7] = '8'
    rejected(lambda: combine([invalid], baseline, clocks, events))
    invalid = deepcopy(entry); invalid['window_native_end_ordinal'] = 65
    rejected(lambda: combine([invalid], baseline, clocks, events))
    # Different source bytes can share all frame ordinals, PTS and candidate
    # intervals.  Such a model answer must never be applied to this video.
    invalid = deepcopy(entry); invalid['source_sha256'] = 'b' * 64
    rejected(lambda: combine([invalid], baseline, clocks, events))
    invalid = deepcopy(entry); del invalid['source_sha256']
    rejected(lambda: combine([invalid], baseline, clocks, events))
    invalid_clocks = deepcopy(clocks); del invalid_clocks['0']['source_sha256']
    rejected(lambda: combine([entry], baseline, invalid_clocks, events))
    for invalid_sha in ('', 'g' * 64, None):
        invalid, invalid_clocks = deepcopy(entry), deepcopy(clocks)
        invalid['source_sha256'] = invalid_clocks['0']['source_sha256'] = invalid_sha
        rejected(lambda: combine([invalid], baseline, invalid_clocks, events))
    invalid = deepcopy(entry); invalid['parsed']['action'] = [[30, 40]]
    rejected(lambda: combine([invalid], baseline, clocks, events))
    invalid = deepcopy(entry); invalid['parsed']['action'] = [30, 65]
    rejected(lambda: combine([invalid], baseline, clocks, events))
    invalid = deepcopy(entry); invalid['candidate_events'] = invalid['candidate_events'][:1]
    invalid['parsed']['redundant'] = []
    rejected(lambda: combine([invalid], baseline, clocks, events))
    rejected(lambda: combine([entry], baseline | {('0', 31)}, clocks, events))
    rejected(lambda: validate_parsed(dict(entry['parsed'], ordinary=[True]), 2))
    # Real calls retain their original denominator.  The old short UNKNOWN is
    # preserved without parsed output; a DROP from the same case contributes 0.
    extended = deepcopy(events)
    extended['short'] = dict(source_id='0', original_case_id='short_case', old_structural_no64=True,
                             original_interval_exact=['70', '75'], selected_interval_exact=['70', '75'], decision='UNKNOWN')
    extended['dropped'] = dict(source_id='0', original_case_id='case0', old_structural_no64=False,
                               original_interval_exact=['100', '110'], selected_interval_exact=None, decision='DROP')
    def skipped(key, reason):
        value = extended[key]
        return dict(case_id=value['original_case_id'], source_id='0', reason=reason,
                    candidate_events=[dict(event_id=key, **{name: value[name] for name in
                        ('original_interval_exact', 'selected_interval_exact', 'decision')})],
                    old_decision_ref=dict(path='/frozen/verification.json', sha256='a' * 64))
    skips = [skipped('short', SKIP_NO64), skipped('dropped', SKIP_DROP)]
    extended_baseline = baseline | {('0', frame) for frame in range(70, 75)}
    preserved = combine([entry], extended_baseline, clocks, extended, skips)
    assert {('0', frame) for frame in range(70, 75)} <= preserved['ORDINARY']['selected_keys']
    assert preserved['ACTION']['selected_keys'] == extended_baseline | {('0', frame) for frame in range(30, 40)}
    assert len(preserved['ACTION']['structural_skips']) == 2
    assert all(value['new_model_calls'] == 0 and value['fabricated_parsed'] is False
               for value in preserved['ACTION']['structural_skips'])
    invalid = deepcopy(skips); invalid[0]['parsed'] = entry['parsed']
    rejected(lambda: combine([entry], extended_baseline, clocks, extended, invalid))
    invalid = deepcopy(extended); invalid['short']['old_structural_no64'] = False
    rejected(lambda: combine([entry], extended_baseline, clocks, invalid, skips))
    invalid = deepcopy(skips); invalid[0]['reason'] = SKIP_DROP
    rejected(lambda: combine([entry], extended_baseline, clocks, extended, invalid))
    invalid = deepcopy(skips); invalid[0]['case_id'] = 'case0'
    rejected(lambda: combine([entry], extended_baseline, clocks, extended, invalid))
    rejected(lambda: combine([entry], extended_baseline, clocks, extended, skips[:1]))
    rejected(lambda: combine([entry], extended_baseline, clocks, extended, skips + [skips[0]]))
    raw_snapshot = deepcopy(entry['parsed'])
    policies = dict(ORDINARY='WORST_ALL', REDUNDANT='WORST_FRACTION_1_3')
    derived = combine([entry], baseline, clocks, events, deletion_policy_map=policies)
    # Both deterministic arms consume the actual redundant index 1.  They do
    # not re-label the actual ordinary index 0 as another model answer.
    assert derived['ORDINARY']['selected_keys'] == result['REDUNDANT']['selected_keys']
    assert derived['REDUNDANT']['selected_keys'] == baseline
    assert derived['ORDINARY']['removed_event_ids'] == ['e1']
    assert derived['ORDINARY']['actual_model_parsed_unchanged'] is True
    assert derived['ORDINARY']['deterministic_deletion_policy'] == 'WORST_ALL'
    assert entry['parsed'] == raw_snapshot
    for arm in ('ACTION', 'REACTION', 'INFORMATION'):
        assert derived[arm] == result[arm]
        assert 'deterministic_deletion_policy' not in derived[arm]
    for count in (1, 2, 3, 4):
        many_events, many_entry = {}, deepcopy(entry)
        for index in range(count):
            bounds = [str(index * 10), str(index * 10 + 5)]
            many_events[str(index)] = dict(source_id='0', original_interval_exact=bounds,
                                           selected_interval_exact=bounds, decision='KEEP')
        many_entry['candidate_events'] = [dict(event_id=key, **{name: value for name, value in event.items() if name != 'source_id'})
                                          for key, event in many_events.items()]
        many_entry['parsed']['ordinary'] = [0]
        many_entry['parsed']['redundant'] = [count - 1]
        before = {('0', frame) for index in range(count) for frame in range(index * 10, index * 10 + 5)}
        for policy, apply in (('WORST_ALL', count >= 2), ('WORST_FRACTION_1_3', count >= 3), ('WORST_PAIR_ONLY', count == 2)):
            mapping = dict(ORDINARY=policy, REDUNDANT='WORST_ALL')
            applied = combine([many_entry], before, clocks, many_events, deletion_policy_map=mapping)['ORDINARY']
            assert applied['removed_event_ids'] == ([str(count - 1)] if apply else [])
            assert applied['selected_keys'] == (before - {('0', frame) for frame in range((count - 1) * 10, (count - 1) * 10 + 5)} if apply else before)
    for bad in ({'ORDINARY': 'WORST_ALL'}, dict(ORDINARY='DIRECT_PARSED_ORDINARY', REDUNDANT='WORST_ALL'),
                dict(ORDINARY='WORST_ALL', REDUNDANT='WORST_ALL', ACTION='WORST_ALL'), ['WORST_ALL']):
        rejected(lambda bad=bad: validate_deletion_policy_map(bad))
    invalid = deepcopy(entry); invalid['parsed']['redundant'] = [0, 1]
    rejected(lambda: combine([invalid], baseline, clocks, events, deletion_policy_map=policies))
    assert combine([entry], baseline, clocks, events)['ORDINARY']['deterministic_deletion_policy'] == 'DIRECT_PARSED_ORDINARY'
    print('PASS_PURE_SOURCE_BYTES_UNION_ENDPOINT64_STRUCTURAL_SKIPS_AND_FROZEN_DELETION_POLICIES')


if __name__ == '__main__':
    main()
